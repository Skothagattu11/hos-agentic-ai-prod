"""
Adaptive Task Selector
=======================

Purpose: Intelligent task selection based on learning phases
Phase: 2 - Adaptive Learning

Learning Phases:
- Discovery (Week 1): 80% untried tasks, 20% tried - Maximum exploration
- Establishment (Week 2-3): 70% favorites, 30% exploration - Build consistency
- Mastery (Week 4+): 85% proven, 15% novelty - Optimized personalization

Features:
- Phase-aware selection strategies
- Preference-based scoring
- Completion pattern analysis
- Smooth phase transitions
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from services.dynamic_personalization.task_library_service import TaskLibraryService
from services.dynamic_personalization.feedback_analyzer_service import FeedbackAnalyzerService
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
import logging

logger = logging.getLogger(__name__)


class AdaptiveTaskSelector:
    """Selects tasks adaptively based on user's learning phase and preferences."""

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
        """Initialize AdaptiveTaskSelector.

        Args:
            db_adapter: Database adapter (creates new if None)
        """
        self.db = db_adapter or SupabaseAsyncPGAdapter()
        self.task_library = TaskLibraryService(db_adapter=self.db)
        self.feedback_service = FeedbackAnalyzerService(db_adapter=self.db)
        self._initialized = False

    async def initialize(self):
        """Initialize services."""
        if not self._initialized:
            await self.db.connect()
            await self.task_library.initialize()
            await self.feedback_service.initialize()
            self._initialized = True
            logger.info("AdaptiveTaskSelector initialized")

    async def close(self):
        """Close services."""
        if self._initialized:
            await self.feedback_service.close()
            await self.task_library.close()
            await self.db.close()
            self._initialized = False
            logger.info("AdaptiveTaskSelector closed")

    async def select_tasks_for_block(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str = "medium",
        time_of_day: Optional[str] = None,
        count: int = 1
    ) -> List[Dict]:
        """Select tasks for a time block using adaptive strategy.

        Args:
            user_id: User ID
            category: Task category
            archetype: User archetype
            mode: Energy mode (high/medium/low)
            time_of_day: Preferred time (morning/afternoon/evening/any)
            count: Number of tasks to select

        Returns:
            List of selected tasks with scores
        """
        try:
            # Get user preferences and learning phase
            profile = await self.feedback_service.get_user_preferences(user_id)

            if not profile:
                # New user - use discovery phase
                logger.info(f"New user {user_id} - using discovery phase")
                return await self._discovery_phase_selection(
                    user_id, category, archetype, mode, time_of_day, count
                )

            # Determine learning phase
            learning_phase = profile.get('current_learning_phase', 'discovery')

            logger.info(f"User {user_id} in {learning_phase} phase - selecting {count} tasks for {category}")

            # Route to appropriate strategy
            if learning_phase == 'discovery':
                return await self._discovery_phase_selection(
                    user_id, category, archetype, mode, time_of_day, count
                )
            elif learning_phase == 'establishment':
                return await self._establishment_phase_selection(
                    user_id, category, archetype, mode, time_of_day, count, profile
                )
            elif learning_phase == 'mastery':
                return await self._mastery_phase_selection(
                    user_id, category, archetype, mode, time_of_day, count, profile
                )
            else:
                # Default to discovery if unknown phase
                logger.warning(f"Unknown learning phase '{learning_phase}' for user {user_id} - defaulting to discovery")
                return await self._discovery_phase_selection(
                    user_id, category, archetype, mode, time_of_day, count
                )

        except Exception as e:
            logger.error(f"Error in adaptive task selection for user {user_id}: {e}")
            # Fallback to basic task library selection
            excluded = await self.task_library.get_recently_used_variation_groups(user_id)
            return await self.task_library.get_tasks_for_category(
                category=category,
                archetype=archetype,
                mode=mode,
                exclude_recently_used=excluded,
                time_of_day=time_of_day,
                limit=count
            )

    async def _discovery_phase_selection(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        time_of_day: Optional[str],
        count: int
    ) -> List[Dict]:
        """Discovery phase: Maximum variety, 80% untried tasks.

        Goal: Test 3-5 variations per category in first week.

        Args:
            user_id: User ID
            category: Task category
            archetype: User archetype
            mode: Energy mode
            time_of_day: Time preference
            count: Number of tasks

        Returns:
            List of mostly untried tasks
        """
        # Get tasks user has tried
        tried_tasks = await self._get_tried_task_ids(user_id, category)

        # Get recently used variation groups (exclude from this session)
        excluded_groups = await self.task_library.get_recently_used_variation_groups(user_id, hours_threshold=24)

        # Fetch all available tasks for category
        all_tasks = await self.task_library.get_tasks_for_category(
            category=category,
            archetype=archetype,
            mode=mode,
            exclude_recently_used=excluded_groups,
            time_of_day=time_of_day,
            limit=20  # Get more candidates
        )

        # Split into untried and tried
        untried_tasks = [t for t in all_tasks if t['id'] not in tried_tasks]
        tried_tasks_list = [t for t in all_tasks if t['id'] in tried_tasks]

        # Select 80% untried, 20% tried
        untried_count = int(count * 0.8)
        tried_count = count - untried_count

        selected = []
        selected.extend(untried_tasks[:untried_count])
        selected.extend(tried_tasks_list[:tried_count])

        # Fill remaining if not enough
        if len(selected) < count:
            remaining = [t for t in all_tasks if t not in selected]
            selected.extend(remaining[:count - len(selected)])

        logger.info(f"Discovery phase: Selected {len(untried_tasks[:untried_count])} untried, {len(tried_tasks_list[:tried_count])} tried")

        return selected[:count]

    async def _establishment_phase_selection(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        time_of_day: Optional[str],
        count: int,
        profile: Dict
    ) -> List[Dict]:
        """Establishment phase: 70% favorites, 30% exploration.

        Goal: Build consistency with proven tasks while maintaining novelty.

        Args:
            user_id: User ID
            category: Task category
            archetype: User archetype
            mode: Energy mode
            time_of_day: Time preference
            count: Number of tasks
            profile: User preference profile

        Returns:
            List of mostly favorite tasks
        """
        # Get category affinity from profile
        category_affinity = profile.get('category_affinity', {})
        current_affinity = category_affinity.get(category, 0.5)

        # Get user's task history for this category
        task_history = await self._get_task_history(user_id, category, limit=50)

        # Score tasks by completion + satisfaction
        favorite_task_ids = self._identify_favorite_tasks(task_history, threshold=0.7)

        # Get recently used variation groups
        excluded_groups = await self.task_library.get_recently_used_variation_groups(user_id, hours_threshold=48)

        # Fetch all available tasks
        all_tasks = await self.task_library.get_tasks_for_category(
            category=category,
            archetype=archetype,
            mode=mode,
            exclude_recently_used=excluded_groups,
            time_of_day=time_of_day,
            limit=20
        )

        # Split into favorites and exploration
        favorite_tasks = [t for t in all_tasks if t['id'] in favorite_task_ids]
        exploration_tasks = [t for t in all_tasks if t['id'] not in favorite_task_ids]

        # Select 70% favorites, 30% exploration
        favorite_count = int(count * 0.7)
        exploration_count = count - favorite_count

        selected = []
        selected.extend(favorite_tasks[:favorite_count])
        selected.extend(exploration_tasks[:exploration_count])

        # Fill remaining
        if len(selected) < count:
            remaining = [t for t in all_tasks if t not in selected]
            selected.extend(remaining[:count - len(selected)])

        logger.info(f"Establishment phase: Selected {len(favorite_tasks[:favorite_count])} favorites, {len(exploration_tasks[:exploration_count])} exploration")

        return selected[:count]

    async def _mastery_phase_selection(
        self,
        user_id: str,
        category: str,
        archetype: str,
        mode: str,
        time_of_day: Optional[str],
        count: int,
        profile: Dict
    ) -> List[Dict]:
        """Mastery phase: 85% proven, 15% novelty.

        Goal: Highly personalized plans with occasional new experiences.

        Args:
            user_id: User ID
            category: Task category
            archetype: User archetype
            mode: Energy mode
            time_of_day: Time preference
            count: Number of tasks
            profile: User preference profile

        Returns:
            List of highly personalized tasks
        """
        # Get user's task history
        task_history = await self._get_task_history(user_id, category, limit=100)

        # Identify top proven tasks (completion rate >80% + high satisfaction)
        proven_task_ids = self._identify_favorite_tasks(task_history, threshold=0.8)

        # Get recently used variation groups
        excluded_groups = await self.task_library.get_recently_used_variation_groups(user_id, hours_threshold=72)

        # Fetch all available tasks
        all_tasks = await self.task_library.get_tasks_for_category(
            category=category,
            archetype=archetype,
            mode=mode,
            exclude_recently_used=excluded_groups,
            time_of_day=time_of_day,
            limit=20
        )

        # Split into proven and novelty
        proven_tasks = [t for t in all_tasks if t['id'] in proven_task_ids]
        novelty_tasks = [t for t in all_tasks if t['id'] not in proven_task_ids]

        # Select 85% proven, 15% novelty
        proven_count = int(count * 0.85)
        novelty_count = count - proven_count

        selected = []
        selected.extend(proven_tasks[:proven_count])
        selected.extend(novelty_tasks[:novelty_count])

        # Fill remaining
        if len(selected) < count:
            remaining = [t for t in all_tasks if t not in selected]
            selected.extend(remaining[:count - len(selected)])

        logger.info(f"Mastery phase: Selected {len(proven_tasks[:proven_count])} proven, {len(novelty_tasks[:novelty_count])} novelty")

        return selected[:count]

    async def _get_tried_task_ids(self, user_id: str, category: str) -> set:
        """Get set of task IDs user has tried in this category.

        Args:
            user_id: User ID (profile_id)
            category: Task category

        Returns:
            Set of task_library_id strings
        """
        # Query task_feedback_complete view (uses existing task_checkins + plan_items)
        query = """
            SELECT task_library_id
            FROM task_feedback_complete
            WHERE profile_id = $1
              AND category = $2
              AND task_library_id IS NOT NULL
        """

        results = await self.db.fetch(query, user_id, category)
        return {row['task_library_id'] for row in results if row.get('task_library_id')}

    async def _get_task_history(self, user_id: str, category: str, limit: int = 50) -> List[Dict]:
        """Get user's task history for a category.

        Args:
            user_id: User ID (profile_id)
            category: Task category
            limit: Max records to fetch

        Returns:
            List of feedback records
        """
        # Query task_feedback_complete view (uses existing task_checkins + plan_items)
        query = """
            SELECT
                task_library_id,
                task_name,
                completion_status,
                satisfaction_rating,
                planned_date,
                completed_at
            FROM task_feedback_complete
            WHERE profile_id = $1
              AND category = $2
              AND task_library_id IS NOT NULL
            ORDER BY completed_at DESC
            LIMIT $3
        """

        results = await self.db.fetch(query, user_id, category, limit)
        # Convert completion_status to completed boolean for compatibility
        processed = []
        for row in results:
            record = dict(row)
            record['completed'] = record['completion_status'] == 'completed'
            record['created_at'] = record['completed_at']  # For compatibility
            processed.append(record)
        return processed

    def _identify_favorite_tasks(self, task_history: List[Dict], threshold: float = 0.7) -> set:
        """Identify favorite tasks based on completion and satisfaction.

        Score = (completion_rate * 0.7) + (avg_satisfaction/5.0 * 0.3)

        Args:
            task_history: List of feedback records
            threshold: Minimum score to be considered favorite

        Returns:
            Set of task_library_id strings
        """
        task_stats = {}

        for record in task_history:
            task_id = record['task_library_id']
            if not task_id:
                continue

            if task_id not in task_stats:
                task_stats[task_id] = {
                    'total': 0,
                    'completed': 0,
                    'satisfaction_sum': 0,
                    'satisfaction_count': 0
                }

            task_stats[task_id]['total'] += 1
            if record['completed']:
                task_stats[task_id]['completed'] += 1

            if record['satisfaction_rating']:
                task_stats[task_id]['satisfaction_sum'] += record['satisfaction_rating']
                task_stats[task_id]['satisfaction_count'] += 1

        # Calculate scores
        favorites = set()
        for task_id, stats in task_stats.items():
            if stats['total'] < 2:  # Need at least 2 data points
                continue

            completion_rate = stats['completed'] / stats['total']

            if stats['satisfaction_count'] > 0:
                avg_satisfaction = stats['satisfaction_sum'] / stats['satisfaction_count']
                satisfaction_score = avg_satisfaction / 5.0
                final_score = (completion_rate * 0.7) + (satisfaction_score * 0.3)
            else:
                final_score = completion_rate

            if final_score >= threshold:
                favorites.add(task_id)

        logger.debug(f"Identified {len(favorites)} favorite tasks (threshold={threshold})")

        return favorites
