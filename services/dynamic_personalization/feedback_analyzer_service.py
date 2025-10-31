"""
Feedback Analyzer Service
==========================

Purpose: Analyze user feedback from existing task_checkins table for adaptive learning
Phase: 1 - Foundation (Updated to use existing engagement system)

Features:
- Query task_checkins for feedback data (no longer records - uses engagement endpoint)
- Calculate category/subcategory affinity scores from actual user data
- Get user preference profiles from task_feedback_complete view
- Track completion patterns from real engagement data
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
import logging

logger = logging.getLogger(__name__)


class FeedbackAnalyzerService:
    """Analyzes user feedback from existing task_checkins table."""

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
        """Initialize FeedbackAnalyzerService.

        Args:
            db_adapter: Database adapter (creates new if None)
        """
        self.db = db_adapter or SupabaseAsyncPGAdapter()
        self._initialized = False

    async def initialize(self):
        """Initialize database connection."""
        if not self._initialized:
            await self.db.connect()
            self._initialized = True
            logger.info("FeedbackAnalyzerService initialized (using existing task_checkins)")

    async def close(self):
        """Close database connection."""
        if self._initialized:
            await self.db.close()
            self._initialized = False

    async def get_user_feedback(
        self,
        user_id: str,
        days: int = 30,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Get user feedback from task_checkins.

        Args:
            user_id: User ID (profile_id)
            days: Number of days to look back
            category: Optional category filter

        Returns:
            List of feedback records with task details
        """
        try:
            # Use the task_feedback_complete view for easy querying
            query = """
                SELECT
                    checkin_id,
                    profile_id,
                    task_library_id,
                    task_name,
                    category,
                    subcategory,
                    variation_group,
                    completion_status,
                    satisfaction_rating,
                    planned_date,
                    completed_at,
                    user_notes,
                    user_mode,
                    user_archetype,
                    day_of_week,
                    source,
                    task_type,
                    priority_level
                FROM task_feedback_complete
                WHERE profile_id = $1
                  AND planned_date >= NOW() - INTERVAL '%s days'
            """ % days

            params = [user_id]

            if category:
                query += " AND category = $2"
                params.append(category)

            query += " ORDER BY planned_date DESC"

            results = await self.db.fetch(query, *params)

            logger.info(f"Retrieved {len(results)} feedback records for user {user_id[:8]}...")
            return results

        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return []

    async def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preference summary from view.

        Args:
            user_id: User ID (profile_id)

        Returns:
            User preference summary by category
        """
        try:
            query = """
                SELECT
                    profile_id,
                    category,
                    tasks_seen,
                    tasks_completed,
                    completion_rate,
                    avg_satisfaction,
                    unique_library_tasks,
                    last_activity
                FROM user_preference_summary
                WHERE profile_id = $1
                ORDER BY avg_satisfaction DESC NULLS LAST, tasks_completed DESC
            """

            results = await self.db.fetch(query, user_id)

            if not results:
                return None

            # Calculate aggregate metrics
            total_tasks_seen = sum(r['tasks_seen'] or 0 for r in results)
            total_tasks_completed = sum(r['tasks_completed'] or 0 for r in results)

            overall_completion_rate = (
                total_tasks_completed / total_tasks_seen
                if total_tasks_seen > 0 else 0
            )

            # Calculate average satisfaction across all categories
            satisfaction_values = [
                r['avg_satisfaction']
                for r in results
                if r['avg_satisfaction'] is not None
            ]
            avg_satisfaction_rating = (
                sum(satisfaction_values) / len(satisfaction_values)
                if satisfaction_values else None
            )

            # Determine learning phase based on total tasks
            learning_phase = self._determine_learning_phase(total_tasks_seen)

            # Build category affinity dict
            category_affinity = {}
            for row in results:
                if row['category']:
                    category_affinity[row['category']] = float(row['completion_rate'] or 0)

            return {
                'user_id': user_id,
                'profile_id': user_id,
                'total_tasks_completed': total_tasks_completed,
                'total_tasks_seen': total_tasks_seen,
                'avg_completion_rate': float(overall_completion_rate),
                'avg_satisfaction_rating': float(avg_satisfaction_rating) if avg_satisfaction_rating else None,
                'current_learning_phase': learning_phase,
                'category_affinity': category_affinity,
                'categories': results,  # Detailed breakdown by category
                'last_feedback_at': max((r['last_activity'] for r in results if r['last_activity']), default=None)
            }

        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None

    async def get_user_favorites(
        self,
        user_id: str,
        category: Optional[str] = None,
        min_rating: int = 4,
        min_completions: int = 2,
        limit: int = 10
    ) -> List[Dict]:
        """Get user's favorite tasks based on feedback.

        Args:
            user_id: User ID (profile_id)
            category: Optional category filter
            min_rating: Minimum satisfaction rating (default 4)
            min_completions: Minimum times completed (default 2)
            limit: Maximum results to return

        Returns:
            List of favorite tasks with metrics
        """
        try:
            query = """
                SELECT
                    task_library_id,
                    task_name,
                    category,
                    subcategory,
                    variation_group,
                    COUNT(*) as completion_count,
                    ROUND(AVG(satisfaction_rating), 2) as avg_rating,
                    MAX(completed_at) as last_completed,
                    source
                FROM task_feedback_complete
                WHERE profile_id = $1
                  AND task_library_id IS NOT NULL
                  AND completion_status = 'completed'
                  AND satisfaction_rating >= $2
            """

            params = [user_id, min_rating]

            if category:
                query += " AND category = $%d" % (len(params) + 1)
                params.append(category)

            query += """
                GROUP BY task_library_id, task_name, category, subcategory, variation_group, source
                HAVING COUNT(*) >= $%d
                ORDER BY avg_rating DESC, completion_count DESC
                LIMIT $%d
            """ % (len(params) + 1, len(params) + 2)

            params.extend([min_completions, limit])

            results = await self.db.fetch(query, *params)

            logger.info(f"Found {len(results)} favorite tasks for user {user_id[:8]}...")
            return results

        except Exception as e:
            logger.error(f"Error getting user favorites: {e}")
            return []

    async def get_category_performance(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Dict]:
        """Get performance metrics by category.

        Args:
            user_id: User ID (profile_id)
            days: Days to analyze

        Returns:
            Dict of category -> metrics
        """
        try:
            query = """
                SELECT
                    category,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN completion_status = 'partial' THEN 1 END) as partial,
                    COUNT(CASE WHEN completion_status = 'skipped' THEN 1 END) as skipped,
                    ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) as avg_satisfaction,
                    COUNT(DISTINCT task_library_id) as unique_library_tasks
                FROM task_feedback_complete
                WHERE profile_id = $1
                  AND planned_date >= NOW() - INTERVAL '%s days'
                  AND category IS NOT NULL
                GROUP BY category
                ORDER BY completed DESC
            """ % days

            results = await self.db.fetch(query, user_id)

            performance = {}
            for row in results:
                category = row['category']
                completion_rate = (
                    row['completed'] / row['total_tasks']
                    if row['total_tasks'] > 0 else 0
                )

                performance[category] = {
                    'total_tasks': row['total_tasks'],
                    'completed': row['completed'],
                    'partial': row['partial'],
                    'skipped': row['skipped'],
                    'completion_rate': float(completion_rate),
                    'avg_satisfaction': float(row['avg_satisfaction']) if row['avg_satisfaction'] else None,
                    'unique_library_tasks': row['unique_library_tasks']
                }

            return performance

        except Exception as e:
            logger.error(f"Error getting category performance: {e}")
            return {}

    def _determine_learning_phase(self, total_tasks: int) -> str:
        """Determine learning phase based on task count.

        Args:
            total_tasks: Total tasks seen

        Returns:
            Learning phase name
        """
        if total_tasks < 50:
            return "discovery"
        elif total_tasks < 200:
            return "establishment"
        else:
            return "mastery"

    async def get_library_task_performance(
        self,
        task_library_id: Optional[str] = None,
        category: Optional[str] = None,
        min_assignments: int = 1
    ) -> List[Dict]:
        """Get performance metrics for library tasks.

        Args:
            task_library_id: Optional specific task filter
            category: Optional category filter
            min_assignments: Minimum assignments to include

        Returns:
            List of task performance metrics
        """
        try:
            query = """
                SELECT * FROM library_task_performance
                WHERE total_assignments >= $1
            """

            params = [min_assignments]

            if task_library_id:
                query += " AND task_library_id = $%d" % (len(params) + 1)
                params.append(task_library_id)

            if category:
                query += " AND category = $%d" % (len(params) + 1)
                params.append(category)

            query += " ORDER BY avg_satisfaction DESC NULLS LAST, completed_count DESC"

            results = await self.db.fetch(query, *params)
            return results

        except Exception as e:
            logger.error(f"Error getting library task performance: {e}")
            return []
