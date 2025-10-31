"""
FeedbackService - Check-in Feedback Aggregation
Purpose: Fetch and aggregate user's daily check-in feedback for plan personalization

Features:
- Retrieves yesterday's task check-ins with preferences
- Aggregates feedback by category (continue, enjoyed, exclude)
- Identifies timing adjustments needed
- Formats data for TaskPreseeder consumption
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

load_dotenv()

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Aggregates user check-in feedback for plan personalization.

    Uses:
    - task_checkins table: continue_preference, enjoyed, timing_feedback
    - plan_items table: category, task metadata
    """

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
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
            logger.info("[FeedbackService] Initialized successfully")

    async def close(self):
        """Close database connection."""
        if self._initialized:
            await self.db.close()
            self._initialized = False
            logger.info("[FeedbackService] Closed successfully")

    async def get_latest_checkin_feedback(
        self,
        user_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Fetch and aggregate recent check-in feedback.

        Args:
            user_id: User profile ID
            days_back: Number of days to look back (default: 7)

        Returns:
            {
                'has_feedback': bool,
                'continue_categories': List[str],
                'enjoyed_categories': List[str],
                'exclude_categories': List[str],
                'timing_adjustments': Dict[str, str],
                'category_scores': Dict[str, float],
                'feedback_count': int,
                'date_range': {'start': str, 'end': str}
            }
        """
        try:
            if not self._initialized:
                await self.initialize()

            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            logger.info(f"[FeedbackService] Fetching feedback for user {user_id} from {start_date} to {end_date}")

            # Use direct Supabase REST API to fetch check-ins with plan_items joined
            # Supabase foreign key syntax: table!inner(fields) means JOIN
            result = self.supabase.table('task_checkins').select(
                'continue_preference, experience_rating, planned_date, plan_items!inner(category, title)'
            ).eq('profile_id', user_id).gte(
                'planned_date', start_date.isoformat()
            ).lte(
                'planned_date', end_date.isoformat()
            ).not_.is_('experience_rating', 'null').not_.is_(
                'continue_preference', 'null'
            ).order('planned_date', desc=True).execute()

            # Transform to match expected format
            results = []
            for row in result.data:
                plan_item = row.get('plan_items', {})
                results.append({
                    'category': plan_item.get('category'),
                    'task_title': plan_item.get('title'),
                    'continue_preference': row['continue_preference'],
                    'experience_rating': row['experience_rating'],
                    'planned_date': row['planned_date']
                })

            if not results:
                logger.info(f"[FeedbackService] No feedback found for user {user_id}")
                return self._empty_feedback_response(start_date, end_date)

            # Aggregate feedback
            feedback = self._aggregate_feedback(results)
            feedback['date_range'] = {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }

            logger.info(f"[FeedbackService] Aggregated {len(results)} check-ins for user {user_id}")
            logger.info(f"[FeedbackService] Categories to continue: {feedback['continue_categories']}")
            logger.info(f"[FeedbackService] Categories to exclude: {feedback['exclude_categories']}")

            return feedback

        except Exception as e:
            logger.error(f"[FeedbackService] Error fetching feedback: {e}", exc_info=True)
            return self._empty_feedback_response(
                datetime.now().date() - timedelta(days=days_back),
                datetime.now().date()
            )

    def _aggregate_feedback(self, checkins: List[Dict]) -> Dict[str, Any]:
        """
        SIMPLIFIED: Aggregate feedback using only 2 questions per task.

        Question 1: experience_rating (1-5) - "How did this go?"
        Question 2: continue_preference (yes/maybe/no) - "Keep this task?"

        Friction Matrix:
        ┌─────────────┬──────────┬───────────┬──────────┐
        │ Rating      │ Keep=Yes │ Keep=Maybe│ Keep=No  │
        ├─────────────┼──────────┼───────────┼──────────┤
        │ 5 (Love it) │ 0.0 ✅   │ 0.2 😊    │ 0.4 😐   │
        │ 4 (Good)    │ 0.1 ✅   │ 0.3 😊    │ 0.5 😐   │
        │ 3 (OK)      │ 0.3 😊   │ 0.5 😐    │ 0.7 ⚠️   │
        │ 2 (Meh)     │ 0.5 😐   │ 0.7 ⚠️    │ 0.85 🔥  │
        │ 1 (Hate it) │ 0.7 ⚠️   │ 0.85 🔥   │ 1.0 🔥   │
        └─────────────┴──────────┴───────────┴──────────┘

        Args:
            checkins: List of check-in records with feedback

        Returns:
            Aggregated feedback dictionary with friction analysis
        """
        low_friction_categories = []
        medium_friction_categories = []
        high_friction_categories = []

        category_scores = {}
        friction_analysis = {}

        # Track counts per category
        category_counts = {}

        for checkin in checkins:
            category = checkin['category']
            if not category:
                continue

            # Initialize category tracking
            if category not in category_counts:
                category_counts[category] = {
                    'total': 0,
                    'experience_sum': 0,
                    'continue_yes': 0,
                    'continue_maybe': 0,
                    'continue_no': 0
                }

            counts = category_counts[category]
            counts['total'] += 1

            # Track experience rating (1-5)
            experience = checkin.get('experience_rating', 3)  # Default to 3 if missing
            counts['experience_sum'] += experience

            # Track continue preference
            continue_pref = checkin.get('continue_preference', 'maybe').lower()
            if continue_pref == 'yes':
                counts['continue_yes'] += 1
            elif continue_pref == 'no':
                counts['continue_no'] += 1
            else:
                counts['continue_maybe'] += 1

        # Calculate friction levels per category
        for category, counts in category_counts.items():
            if counts['total'] == 0:
                continue

            # Calculate average experience rating
            avg_experience = counts['experience_sum'] / counts['total']

            # Calculate continuation rates
            yes_rate = counts['continue_yes'] / counts['total']
            maybe_rate = counts['continue_maybe'] / counts['total']
            no_rate = counts['continue_no'] / counts['total']

            # SIMPLIFIED FRICTION FORMULA:
            # Base friction from experience (inverted): (5 - rating) / 4
            # 5 → 0.0, 4 → 0.25, 3 → 0.5, 2 → 0.75, 1 → 1.0
            experience_friction = (5 - avg_experience) / 4.0

            # Continuation friction: no=0.8, maybe=0.4, yes=0.0
            continuation_friction = (no_rate * 0.8) + (maybe_rate * 0.4)

            # Combined friction (60% experience, 40% continuation)
            friction_score = (experience_friction * 0.6) + (continuation_friction * 0.4)
            friction_score = min(1.0, max(0.0, friction_score))

            category_scores[category] = 1.0 - friction_score

            # Categorize by friction level
            if friction_score <= 0.3:
                low_friction_categories.append(category)
                adaptation_strategy = 'leverage_as_anchor'
            elif friction_score <= 0.6:
                medium_friction_categories.append(category)
                adaptation_strategy = 'maintain_current'
            else:
                high_friction_categories.append(category)
                adaptation_strategy = 'simplify_approach'

            # Store detailed friction analysis
            friction_analysis[category] = {
                'friction_score': round(friction_score, 2),
                'success_score': round(1.0 - friction_score, 2),
                'strategy': adaptation_strategy,
                'avg_experience_rating': round(avg_experience, 1),
                'continue_yes_rate': round(yes_rate, 2),
                'continue_maybe_rate': round(maybe_rate, 2),
                'continue_no_rate': round(no_rate, 2),
                'total_attempts': counts['total']
            }

        # DEBUG: Log friction categorization results
        logger.info(f"[FRICTION-DEBUG] Low friction categories (≤0.3): {low_friction_categories}")
        logger.info(f"[FRICTION-DEBUG] Medium friction categories (0.3-0.6): {medium_friction_categories}")
        logger.info(f"[FRICTION-DEBUG] High friction categories (>0.6): {high_friction_categories}")
        logger.info(f"[FRICTION-DEBUG] Detailed analysis: {friction_analysis}")

        return {
            'has_feedback': len(checkins) > 0,
            'low_friction_categories': low_friction_categories,
            'medium_friction_categories': medium_friction_categories,
            'high_friction_categories': high_friction_categories,
            'friction_analysis': friction_analysis,
            # Backward compatibility
            'continue_categories': low_friction_categories,
            'enjoyed_categories': low_friction_categories,
            'exclude_categories': [],
            'timing_adjustments': {},  # Removed timing complexity
            'category_scores': category_scores,
            'feedback_count': len(checkins)
        }

    def _empty_feedback_response(self, start_date, end_date) -> Dict[str, Any]:
        """Return empty feedback response when no data available."""
        return {
            'has_feedback': False,
            'continue_categories': [],
            'enjoyed_categories': [],
            'exclude_categories': [],
            'timing_adjustments': {},
            'category_scores': {},
            'feedback_count': 0,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }

    async def get_category_preferences(self, user_id: str) -> Dict[str, float]:
        """
        Get simplified category preference scores (0.0 to 1.0).

        Returns:
            {'hydration': 0.8, 'movement': 0.6, 'nutrition': 0.3}
        """
        feedback = await self.get_latest_checkin_feedback(user_id)
        return feedback.get('category_scores', {})

    async def should_exclude_category(self, user_id: str, category: str) -> bool:
        """
        Check if a category should be excluded from plan.

        Args:
            user_id: User profile ID
            category: Task category to check

        Returns:
            True if category should be excluded
        """
        feedback = await self.get_latest_checkin_feedback(user_id)
        return category in feedback.get('exclude_categories', [])


# Singleton instance
_feedback_service = None


def get_feedback_service() -> FeedbackService:
    """Get singleton FeedbackService instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
