"""
Anchoring Coordinator - Phase 2

Orchestrates the complete anchoring workflow:
1. Fetch calendar events
2. Find available time gaps
3. Score task-slot combinations
4. Assign tasks to optimal slots

This is the main entry point for anchoring functionality.
"""

import logging
from typing import List, Optional
from datetime import date

from .calendar_integration_service import (
    get_calendar_integration_service,
    CalendarEvent,
    CalendarFetchResult
)
from .calendar_gap_finder import get_gap_finder, AvailableSlot
from .basic_scorer_service import (
    get_basic_scorer_service,
    TaskToAnchor,
    TaskSlotScore
)
from .hybrid_scorer_service import (
    get_hybrid_scorer_service,
    HybridTaskSlotScore
)
from .greedy_assignment_service import (
    get_greedy_assignment_service,
    AssignmentResult
)

logger = logging.getLogger(__name__)


# ============================================================================
# Anchoring Coordinator
# ============================================================================

class AnchoringCoordinator:
    """
    Coordinates the complete calendar anchoring workflow

    This service ties together all anchoring components and provides
    a simple interface for anchoring tasks to calendar slots.

    Usage:
        coordinator = AnchoringCoordinator()
        result = await coordinator.anchor_tasks(
            user_id="user_123",
            tasks=task_list,
            target_date=date.today(),
            use_mock_calendar=True
        )
    """

    def __init__(self, use_ai_scoring: bool = False):
        """
        Initialize coordinator with all required services

        Args:
            use_ai_scoring: Whether to use AI-enhanced scoring (default: False for speed)
        """
        self.calendar_service = get_calendar_integration_service()
        self.gap_finder = get_gap_finder()
        self.use_ai_scoring = use_ai_scoring

        # Choose scorer based on AI flag
        if use_ai_scoring:
            self.scorer = get_hybrid_scorer_service(use_ai=True)
            self.assigner = get_greedy_assignment_service()
            logger.info("[ANCHORING-COORDINATOR] Initialized with AI-enhanced scoring")
        else:
            self.basic_scorer = get_basic_scorer_service()
            self.assigner = get_greedy_assignment_service()
            logger.info("[ANCHORING-COORDINATOR] Initialized with algorithmic-only scoring")

    async def anchor_tasks(
        self,
        user_id: str,
        tasks: List[TaskToAnchor],
        target_date: date,
        supabase_token: Optional[str] = None,
        use_mock_calendar: bool = False,
        mock_profile: str = "realistic_day",
        min_gap_minutes: int = 15
    ) -> AssignmentResult:
        """
        Anchor tasks to calendar gaps

        Args:
            user_id: User's profile ID
            tasks: List of tasks to anchor
            target_date: Date to anchor tasks for
            supabase_token: Optional Supabase JWT token for auth
            use_mock_calendar: Whether to use mock calendar data
            mock_profile: Mock calendar profile to use
            min_gap_minutes: Minimum gap size to consider

        Returns:
            AssignmentResult with all anchored tasks
        """
        logger.info(
            f"[ANCHORING-COORDINATOR] Starting anchoring for {len(tasks)} tasks "
            f"on {target_date}"
        )

        # Step 1: Fetch calendar events
        logger.info("[ANCHORING-COORDINATOR] Step 1: Fetching calendar events")
        calendar_result = await self.calendar_service.fetch_calendar_events(
            user_id=user_id,
            target_date=target_date,
            supabase_token=supabase_token,
            use_mock_data=use_mock_calendar,
            mock_profile=mock_profile
        )

        if not calendar_result.success:
            logger.error(
                f"[ANCHORING-COORDINATOR] Failed to fetch calendar events: "
                f"{calendar_result.error_message}"
            )
            # Continue with empty calendar
            calendar_events = []
        else:
            calendar_events = calendar_result.events
            logger.info(
                f"[ANCHORING-COORDINATOR] Fetched {len(calendar_events)} calendar events"
            )

        # Step 2: Find available time gaps
        logger.info("[ANCHORING-COORDINATOR] Step 2: Finding available time gaps")
        gaps = self.gap_finder.find_gaps(
            calendar_events=calendar_events,
            target_date=target_date,
            min_gap_minutes=min_gap_minutes
        )

        logger.info(
            f"[ANCHORING-COORDINATOR] Found {len(gaps)} available time gaps "
            f"({sum(g.duration_minutes for g in gaps)} total minutes)"
        )

        # Step 3: Score all task-slot combinations
        logger.info(f"[ANCHORING-COORDINATOR] Step 3: Scoring task-slot combinations "
                   f"({'AI-enhanced' if self.use_ai_scoring else 'algorithmic-only'})")

        if self.use_ai_scoring:
            # Use hybrid scorer (algorithmic + AI)
            scores = await self.scorer.score_all_combinations(
                tasks, gaps, calendar_events, optimize_ai_calls=True
            )
        else:
            # Use basic scorer (algorithmic only)
            scores = self.basic_scorer.score_all_combinations(tasks, gaps)

        logger.info(
            f"[ANCHORING-COORDINATOR] Scored {len(scores)} combinations "
            f"(avg score: {sum(s.total_score for s in scores) / len(scores):.1f})"
            if scores else "[ANCHORING-COORDINATOR] No valid combinations found"
        )

        # Step 4: Assign tasks to slots using greedy algorithm
        logger.info("[ANCHORING-COORDINATOR] Step 4: Assigning tasks to slots")
        result = self.assigner.assign_tasks(tasks, gaps, scores)

        logger.info(
            f"[ANCHORING-COORDINATOR] ✅ Anchoring complete: "
            f"{result.tasks_anchored} tasks anchored, "
            f"{result.tasks_rescheduled} rescheduled, "
            f"average confidence: {result.average_confidence:.2f}"
        )

        return result


# ============================================================================
# Singleton Instance
# ============================================================================

_coordinator_instance: Optional[AnchoringCoordinator] = None


def get_anchoring_coordinator(use_ai_scoring: bool = False) -> AnchoringCoordinator:
    """
    Get singleton instance of AnchoringCoordinator

    Args:
        use_ai_scoring: Whether to use AI-enhanced scoring

    Returns:
        AnchoringCoordinator instance
    """
    global _coordinator_instance

    if _coordinator_instance is None:
        _coordinator_instance = AnchoringCoordinator(use_ai_scoring=use_ai_scoring)

    return _coordinator_instance
