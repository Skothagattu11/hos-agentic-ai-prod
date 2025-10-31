"""
Learning Phase Manager
======================

Purpose: Manage automatic progression through learning phases
Phase: 2 - Adaptive Learning

Phase Transitions:
- Discovery  Establishment: After 7 days OR 15+ tasks completed
- Establishment  Mastery: After 21 days OR 40+ tasks completed

Features:
- Automatic phase progression based on time and engagement
- Phase transition insights
- Manual phase override capability
- Prevent regression (forward-only progression)
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
import logging

logger = logging.getLogger(__name__)


class LearningPhaseManager:
    """Manages user learning phase progression."""

    # Phase transition criteria
    DISCOVERY_MIN_DAYS = 7
    DISCOVERY_MIN_TASKS = 15

    ESTABLISHMENT_MIN_DAYS = 21  # Total days from start
    ESTABLISHMENT_MIN_TASKS = 40  # Total tasks from start

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
        """Initialize LearningPhaseManager.

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
            logger.info("LearningPhaseManager initialized")

    async def close(self):
        """Close database connection."""
        if self._initialized:
            await self.db.close()
            self._initialized = False
            logger.info("LearningPhaseManager closed")

    async def update_learning_phase(self, user_id: str) -> Tuple[str, bool, Optional[Dict]]:
        """Check and update user's learning phase if criteria met.

        Args:
            user_id: User ID

        Returns:
            Tuple of (current_phase, phase_changed, transition_insight)
        """
        try:
            # Get current profile
            profile = await self._get_profile(user_id)

            if not profile:
                logger.warning(f"No profile found for user {user_id}")
                return ('discovery', False, None)

            current_phase = profile['current_learning_phase']
            phase_started_at = profile['phase_started_at']
            total_tasks_completed = profile['total_tasks_completed']

            # Calculate days in current phase
            days_in_phase = (datetime.now() - phase_started_at).days

            # Check for phase transition
            new_phase, should_transition = self._should_transition_phase(
                current_phase=current_phase,
                days_in_phase=days_in_phase,
                total_tasks_completed=total_tasks_completed
            )

            if should_transition:
                # Update phase in database
                await self._transition_to_phase(user_id, new_phase)

                # Generate transition insight
                insight = self._generate_transition_insight(
                    user_id=user_id,
                    old_phase=current_phase,
                    new_phase=new_phase,
                    days_in_phase=days_in_phase,
                    total_tasks=total_tasks_completed
                )

                logger.info(f"User {user_id} transitioned: {current_phase}  {new_phase}")

                return (new_phase, True, insight)

            return (current_phase, False, None)

        except Exception as e:
            logger.error(f"Error updating learning phase for user {user_id}: {e}")
            return ('discovery', False, None)

    def _should_transition_phase(
        self,
        current_phase: str,
        days_in_phase: int,
        total_tasks_completed: int
    ) -> Tuple[str, bool]:
        """Determine if user should transition to next phase.

        Args:
            current_phase: Current learning phase
            days_in_phase: Days spent in current phase
            total_tasks_completed: Total tasks completed by user

        Returns:
            Tuple of (new_phase, should_transition)
        """
        if current_phase == 'discovery':
            # Transition to establishment if:
            # - 7+ days in discovery OR 15+ tasks completed
            if days_in_phase >= self.DISCOVERY_MIN_DAYS or total_tasks_completed >= self.DISCOVERY_MIN_TASKS:
                return ('establishment', True)

        elif current_phase == 'establishment':
            # Transition to mastery if:
            # - 21+ days since start OR 40+ tasks completed
            if days_in_phase >= self.ESTABLISHMENT_MIN_DAYS or total_tasks_completed >= self.ESTABLISHMENT_MIN_TASKS:
                return ('mastery', True)

        elif current_phase == 'mastery':
            # Already in final phase - no transition
            return ('mastery', False)

        return (current_phase, False)

    async def _transition_to_phase(self, user_id: str, new_phase: str) -> None:
        """Transition user to new learning phase.

        Args:
            user_id: User ID
            new_phase: New phase to transition to
        """
        query = """
            UPDATE user_preference_profile
            SET
                current_learning_phase = $1,
                phase_started_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $2
        """

        await self.db.execute(query, new_phase, user_id)

        logger.info(f"Transitioned user {user_id} to {new_phase} phase")

    def _generate_transition_insight(
        self,
        user_id: str,
        old_phase: str,
        new_phase: str,
        days_in_phase: int,
        total_tasks: int
    ) -> Dict:
        """Generate insight message for phase transition.

        Args:
            user_id: User ID
            old_phase: Previous phase
            new_phase: New phase
            days_in_phase: Days spent in previous phase
            total_tasks: Total tasks completed

        Returns:
            Insight dictionary
        """
        # Phase-specific messages
        messages = {
            'discovery_to_establishment': {
                'title': ' Week 1 Complete!',
                'message': f"You've completed {total_tasks} tasks and we're learning what you love! "
                           f"Your routine is now becoming more personalized based on your preferences.",
                'next_steps': "We'll focus on tasks you enjoy while continuing to explore new options."
            },
            'establishment_to_mastery': {
                'title': ' Personalization Mastery!',
                'message': f"Amazing progress! {total_tasks} tasks completed. "
                           f"Your routine is now highly optimized for your unique preferences and goals.",
                'next_steps': "You'll see your favorite tasks with occasional new experiences for continued growth."
            }
        }

        transition_key = f"{old_phase}_to_{new_phase}"
        insight_data = messages.get(transition_key, {
            'title': 'Phase Transition',
            'message': f'Transitioned from {old_phase} to {new_phase}',
            'next_steps': 'Continue completing tasks to improve personalization.'
        })

        return {
            'user_id': user_id,
            'type': 'phase_transition',
            'old_phase': old_phase,
            'new_phase': new_phase,
            'days_in_previous_phase': days_in_phase,
            'total_tasks_completed': total_tasks,
            **insight_data,
            'created_at': datetime.now().isoformat()
        }

    async def _get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user preference profile.

        Args:
            user_id: User ID

        Returns:
            Profile dictionary or None
        """
        query = """
            SELECT
                current_learning_phase,
                phase_started_at,
                total_tasks_completed,
                total_tasks_seen,
                created_at
            FROM user_preference_profile
            WHERE user_id = $1
        """

        result = await self.db.fetchrow(query, user_id)
        return dict(result) if result else None

    async def manually_set_phase(self, user_id: str, new_phase: str) -> bool:
        """Manually override user's learning phase.

        Use case: Testing, admin override, user preference

        Args:
            user_id: User ID
            new_phase: Phase to set (discovery, establishment, mastery)

        Returns:
            True if successful
        """
        if new_phase not in ['discovery', 'establishment', 'mastery']:
            logger.error(f"Invalid phase: {new_phase}")
            return False

        try:
            await self._transition_to_phase(user_id, new_phase)
            logger.info(f"Manually set user {user_id} to {new_phase} phase")
            return True

        except Exception as e:
            logger.error(f"Error manually setting phase for user {user_id}: {e}")
            return False

    async def get_phase_progress(self, user_id: str) -> Optional[Dict]:
        """Get user's progress within current learning phase.

        Args:
            user_id: User ID

        Returns:
            Progress dictionary with current status and next milestone
        """
        try:
            profile = await self._get_profile(user_id)

            if not profile:
                return None

            current_phase = profile['current_learning_phase']
            phase_started_at = profile['phase_started_at']
            total_tasks = profile['total_tasks_completed']

            days_in_phase = (datetime.now() - phase_started_at).days

            # Calculate progress to next phase
            if current_phase == 'discovery':
                days_remaining = max(0, self.DISCOVERY_MIN_DAYS - days_in_phase)
                tasks_remaining = max(0, self.DISCOVERY_MIN_TASKS - total_tasks)
                next_phase = 'establishment'

            elif current_phase == 'establishment':
                days_remaining = max(0, self.ESTABLISHMENT_MIN_DAYS - days_in_phase)
                tasks_remaining = max(0, self.ESTABLISHMENT_MIN_TASKS - total_tasks)
                next_phase = 'mastery'

            else:  # mastery
                days_remaining = 0
                tasks_remaining = 0
                next_phase = None

            return {
                'user_id': user_id,
                'current_phase': current_phase,
                'days_in_phase': days_in_phase,
                'total_tasks_completed': total_tasks,
                'next_phase': next_phase,
                'days_until_next': days_remaining,
                'tasks_until_next': tasks_remaining,
                'phase_started_at': phase_started_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting phase progress for user {user_id}: {e}")
            return None
