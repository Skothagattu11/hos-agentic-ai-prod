"""
Task Library Service
====================

Purpose: Select tasks from task_library based on archetype, mode, and rotation state
Phase: 1 - Foundation

Features:
- Category-based task selection
- Archetype fit scoring (70% weight)
- Mode fit scoring (30% weight)
- Rotation prevention (excludes recently used tasks)
- Randomization for variety
"""

import os
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class TaskLibraryService:
    """Manages task selection from the task library."""

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
        """Initialize TaskLibraryService.

        Args:
            db_adapter: Database adapter (creates new if None)
        """
        self.db = db_adapter or SupabaseAsyncPGAdapter()
        self._initialized = False

        # Direct Supabase client for simple queries (avoid adapter complexity)
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )

    async def initialize(self):
        """Initialize database connection."""
        if not self._initialized:
            await self.db.connect()
            self._initialized = True
            logger.info("TaskLibraryService initialized")

    async def close(self):
        """Close database connection."""
        if self._initialized:
            await self.db.close()
            self._initialized = False
            logger.info("TaskLibraryService closed")

    async def get_tasks_for_category(
        self,
        category: str,
        archetype: str,
        mode: str = "medium",
        exclude_recently_used: Optional[List[str]] = None,
        time_of_day: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict]:
        """Get scored and sorted tasks for a category.

        Args:
            category: Task category (hydration, movement, nutrition, etc.)
            archetype: User archetype (foundation_builder, peak_performer, etc.)
            mode: User energy mode (high, medium, low)
            exclude_recently_used: List of variation_groups to exclude
            time_of_day: Preferred time of day (morning, afternoon, evening, any)
            limit: Number of tasks to return

        Returns:
            List of task dictionaries with scores
        """
        try:
            # Check if we're using connection pool (production) or REST API (development)
            use_production_mode = os.getenv('ENVIRONMENT', 'development').lower() == 'production'

            if use_production_mode and self.db.use_connection_pool:
                # PRODUCTION MODE: Use complex query with OR conditions (full SQL support)
                tasks = await self._fetch_tasks_production_mode(
                    category, exclude_recently_used, time_of_day
                )
            else:
                # DEVELOPMENT MODE: Use multiple simple queries (REST API compatible)
                tasks = await self._fetch_tasks_development_mode(
                    category, exclude_recently_used, time_of_day
                )

            if not tasks:
                logger.warning(f"No tasks found for category '{category}'")
                return []

            # Score tasks
            scored_tasks = []
            for task in tasks:
                score = self._calculate_task_score(
                    task=task,
                    archetype=archetype,
                    mode=mode
                )
                scored_tasks.append({
                    **task,
                    'selection_score': score
                })

            # Sort by score (descending) with randomization for variety
            scored_tasks.sort(key=lambda x: x['selection_score'] + random.uniform(-0.05, 0.05), reverse=True)

            # Return top N tasks
            selected_tasks = scored_tasks[:limit]

            logger.info(
                f"Selected {len(selected_tasks)} tasks for category '{category}' "
                f"(archetype={archetype}, mode={mode})"
            )

            return selected_tasks

        except Exception as e:
            logger.error(f"Error getting tasks for category '{category}': {e}")
            raise

    def _calculate_task_score(self, task: Dict, archetype: str, mode: str) -> float:
        """Calculate selection score for a task.

        Score = (archetype_fit * 0.7) + (mode_fit * 0.3)

        Args:
            task: Task dictionary with archetype_fit and mode_fit
            archetype: User archetype
            mode: User energy mode

        Returns:
            Score between 0.0 and 1.0
        """
        # Get archetype fit score (default 0.5 if not found)
        archetype_fit_scores = task.get('archetype_fit', {})
        archetype_score = archetype_fit_scores.get(archetype, 0.5)

        # Get mode fit score (default 0.5 if not found)
        mode_fit_scores = task.get('mode_fit', {})
        mode_score = mode_fit_scores.get(mode, 0.5)

        # Weighted combination: 70% archetype, 30% mode
        final_score = (archetype_score * 0.7) + (mode_score * 0.3)

        return final_score

    async def get_recently_used_variation_groups(
        self,
        user_id: str,
        hours_threshold: int = 48
    ) -> List[str]:
        """Get variation groups used recently by the user.

        Args:
            user_id: User ID
            hours_threshold: Hours to look back (default 48)

        Returns:
            List of variation_group strings
        """
        try:
            # Note: Removed DISTINCT due to Supabase REST API parsing issues
            # Deduplication happens in Python via set conversion
            query = """
                SELECT variation_group
                FROM task_rotation_state
                WHERE user_id = $1
                  AND last_used_at > NOW() - INTERVAL '%s hours'
                  AND variation_group IS NOT NULL
            """ % hours_threshold

            results = await self.db.fetch(query, user_id)

            # Deduplicate variation groups
            variation_groups = list(set(row['variation_group'] for row in results if row.get('variation_group')))

            logger.debug(
                f"Found {len(variation_groups)} recently used variation groups "
                f"for user {user_id} (threshold={hours_threshold}h)"
            )

            return variation_groups

        except Exception as e:
            logger.error(f"Error getting recently used variation groups for user {user_id}: {e}")
            return []  # Return empty list on error (fail gracefully)

    async def _fetch_tasks_production_mode(
        self,
        category: str,
        exclude_recently_used: Optional[List[str]],
        time_of_day: Optional[str]
    ) -> List[Dict]:
        """Fetch tasks using complex SQL queries (PostgreSQL connection pool).

        Supports OR conditions and array operations.
        """
        query = """
            SELECT
                id,
                category,
                subcategory,
                name,
                description,
                duration_minutes,
                difficulty,
                archetype_fit,
                mode_fit,
                tags,
                variation_group,
                time_of_day_preference
            FROM task_library
            WHERE category = $1
              AND is_active = true
        """
        params = [category]
        param_count = 1

        # Exclude recently used variation groups
        if exclude_recently_used and len(exclude_recently_used) > 0:
            param_count += 1
            query += f" AND (variation_group NOT IN (SELECT unnest(${param_count}::text[])) OR variation_group IS NULL)"
            params.append(exclude_recently_used)

        # Filter by time of day if specified
        if time_of_day:
            param_count += 1
            query += f" AND (time_of_day_preference = ${param_count} OR time_of_day_preference = 'any')"
            params.append(time_of_day)

        tasks = await self.db.fetch(query, *params)
        logger.info(f"[PRODUCTION] Fetched {len(tasks)} tasks for category '{category}' using PostgreSQL")
        return tasks

    async def _fetch_tasks_development_mode(
        self,
        category: str,
        exclude_recently_used: Optional[List[str]],
        time_of_day: Optional[str]
    ) -> List[Dict]:
        """Fetch tasks using direct Supabase REST API (development mode).

        Works around adapter issues by using direct REST API:
        1. Fetching tasks with specific time_of_day
        2. Fetching tasks with time_of_day='any'
        3. Merging and deduplicating in Python
        4. Filtering excluded variation_groups in Python
        """
        all_tasks = []

        # Fields to select
        fields = 'id,category,subcategory,name,description,duration_minutes,difficulty,archetype_fit,mode_fit,tags,variation_group,time_of_day_preference'

        if time_of_day:
            # Query 1: Tasks matching specific time_of_day
            result1 = self.supabase.table('task_library').select(fields).eq(
                'category', category
            ).eq('is_active', True).eq(
                'time_of_day_preference', time_of_day
            ).execute()
            all_tasks.extend(result1.data)

            # Query 2: Tasks with time_of_day='any'
            result2 = self.supabase.table('task_library').select(fields).eq(
                'category', category
            ).eq('is_active', True).eq(
                'time_of_day_preference', 'any'
            ).execute()
            all_tasks.extend(result2.data)
        else:
            # No time filter - fetch all active tasks for category
            result = self.supabase.table('task_library').select(fields).eq(
                'category', category
            ).eq('is_active', True).execute()
            all_tasks.extend(result.data)

        # Deduplicate by task ID
        seen_ids = set()
        unique_tasks = []
        for task in all_tasks:
            task_id = task.get('id')
            if task_id and task_id not in seen_ids:
                seen_ids.add(task_id)
                unique_tasks.append(task)

        # Filter out excluded variation_groups in Python (since REST API can't do complex subqueries)
        if exclude_recently_used and len(exclude_recently_used) > 0:
            filtered_tasks = [
                task for task in unique_tasks
                if task.get('variation_group') is None or task.get('variation_group') not in exclude_recently_used
            ]
            logger.info(
                f"[DEVELOPMENT] Filtered {len(unique_tasks) - len(filtered_tasks)} tasks "
                f"with excluded variation_groups"
            )
            unique_tasks = filtered_tasks

        logger.info(f"[DEVELOPMENT] Fetched {len(unique_tasks)} tasks for category '{category}' using REST API")
        return unique_tasks

    async def record_task_usage(
        self,
        user_id: str,
        task_library_id: str,
        task_name: str,
        category: str,
        variation_group: Optional[str] = None
    ) -> None:
        """Record task usage for rotation tracking.

        Args:
            user_id: User ID
            task_library_id: ID from task_library
            task_name: Task name
            category: Task category
            variation_group: Variation group (if applicable)
        """
        try:
            # Direct INSERT with UPSERT for REST API compatibility
            # REST API cannot call PostgreSQL functions, so we use INSERT with ON CONFLICT
            import uuid
            from datetime import datetime

            query = """
                INSERT INTO task_rotation_state (
                    user_id,
                    variation_group,
                    last_task_library_id,
                    last_task_name,
                    category,
                    last_used_at,
                    usage_count
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, variation_group)
                DO UPDATE SET
                    last_task_library_id = $3,
                    last_task_name = $4,
                    category = $5,
                    last_used_at = $6,
                    usage_count = task_rotation_state.usage_count + 1
            """

            await self.db.execute(
                query,
                user_id,
                variation_group,
                task_library_id,
                task_name,
                category,
                datetime.utcnow(),
                1  # initial usage_count
            )

            logger.debug(
                f"Recorded task usage for user {user_id}: "
                f"{task_name} (variation_group={variation_group})"
            )

        except Exception as e:
            logger.error(f"Error recording task usage for user {user_id}: {e}")
            # Don't raise - this is non-critical tracking

    async def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Get a specific task by ID.

        Args:
            task_id: Task library ID

        Returns:
            Task dictionary or None if not found
        """
        try:
            query = """
                SELECT
                    id,
                    category,
                    subcategory,
                    name,
                    description,
                    duration_minutes,
                    difficulty,
                    archetype_fit,
                    mode_fit,
                    tags,
                    variation_group,
                    time_of_day_preference
                FROM task_library
                WHERE id = $1
                  AND is_active = true
            """

            task = await self.db.fetchrow(query, task_id)

            if task:
                logger.debug(f"Found task by ID: {task['name']}")
            else:
                logger.warning(f"Task not found with ID: {task_id}")

            return task

        except Exception as e:
            logger.error(f"Error getting task by ID {task_id}: {e}")
            return None

    async def get_all_categories(self) -> List[str]:
        """Get all unique categories in task library.

        Returns:
            List of category names
        """
        try:
            # Note: Removed DISTINCT due to Supabase REST API parsing issues
            # Deduplication happens in Python via set conversion
            query = """
                SELECT category
                FROM task_library
                WHERE is_active = true
            """

            results = await self.db.fetch(query)
            # Deduplicate and sort categories
            categories = sorted(set(row['category'] for row in results if row.get('category')))

            logger.debug(f"Found {len(categories)} categories in task library")

            return categories

        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    async def get_task_count_by_category(self) -> Dict[str, int]:
        """Get count of tasks per category.

        Returns:
            Dictionary mapping category name to task count
        """
        try:
            # Note: Supabase REST API doesn't support GROUP BY properly
            # So we fetch all tasks and group in Python
            query = """
                SELECT category
                FROM task_library
                WHERE is_active = true
            """

            results = await self.db.fetch(query)

            # Count categories in Python
            counts = {}
            for row in results:
                category = row['category'] if isinstance(row, dict) else row[0]
                counts[category] = counts.get(category, 0) + 1

            logger.debug(f"Task counts: {counts}")

            return counts

        except Exception as e:
            logger.error(f"Error getting task counts: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
