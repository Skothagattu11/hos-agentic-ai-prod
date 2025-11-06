"""
Hybrid Scorer Service - Phase 4

Combines algorithmic and AI-based scoring for optimal task-slot matching.

Scoring Architecture:
- BasicScorer: 15 points (algorithmic - duration, time window, priority)
- AIScorer: 33 points (semantic - context, dependencies, energy)
- Total: 48 points (hybrid approach)

This provides both the speed of algorithmic scoring and the intelligence of AI.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .basic_scorer_service import (
    BasicScorerService,
    TaskToAnchor,
    get_basic_scorer_service
)
from .ai_scorer_service import (
    AIScorerService,
    get_ai_scorer_service
)
from .calendar_gap_finder import AvailableSlot
from .calendar_integration_service import CalendarEvent

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class HybridTaskSlotScore:
    """
    Combined score for a specific (task, slot) combination
    """
    task_id: str
    slot_id: str
    total_score: float  # 0-48 points (15 algorithmic + 33 AI)
    algorithmic_score: float  # 0-15 points
    ai_score: float  # 0-33 points
    scoring_breakdown: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "slot_id": self.slot_id,
            "total_score": self.total_score,
            "algorithmic_score": self.algorithmic_score,
            "ai_score": self.ai_score,
            "scoring_breakdown": self.scoring_breakdown
        }


# ============================================================================
# Hybrid Scorer Service
# ============================================================================

class HybridScorerService:
    """
    Hybrid scorer combining algorithmic and AI-based scoring

    Provides the best of both worlds:
    - Fast, consistent algorithmic scoring (15 points)
    - Intelligent, context-aware AI scoring (33 points)

    Usage:
        scorer = HybridScorerService()
        scores = await scorer.score_all_combinations(tasks, slots, calendar_events)
    """

    def __init__(
        self,
        basic_scorer: Optional[BasicScorerService] = None,
        ai_scorer: Optional[AIScorerService] = None,
        use_ai: bool = True
    ):
        """
        Initialize hybrid scorer service

        Args:
            basic_scorer: Optional BasicScorerService instance
            ai_scorer: Optional AIScorerService instance
            use_ai: Whether to use AI scoring (fallback to algorithmic if False)
        """
        self.basic_scorer = basic_scorer or get_basic_scorer_service()
        self.ai_scorer = ai_scorer or (get_ai_scorer_service() if use_ai else None)
        self.use_ai = use_ai

        if self.use_ai and self.ai_scorer:
            logger.info("[HYBRID-SCORER] Initialized with AI-enhanced scoring (48 points max)")
        else:
            logger.info("[HYBRID-SCORER] Initialized with algorithmic-only scoring (15 points max)")

    async def score_task_slot(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> HybridTaskSlotScore:
        """
        Score how well a task fits a specific time slot using hybrid approach

        Args:
            task: Task to anchor
            slot: Available time slot
            calendar_context: Optional surrounding calendar events

        Returns:
            HybridTaskSlotScore combining algorithmic + AI scoring
        """
        # Step 1: Get algorithmic score (always computed)
        basic_score_obj = self.basic_scorer.score_task_slot(task, slot)
        algorithmic_score = basic_score_obj.total_score

        # Step 2: Get AI score (if enabled)
        ai_score = 0.0
        ai_breakdown = {}

        if self.use_ai and self.ai_scorer:
            try:
                ai_score_obj = await self.ai_scorer.score_task_slot(
                    task, slot, calendar_context
                )
                ai_score = ai_score_obj.total_score
                ai_breakdown = {
                    "task_context": ai_score_obj.task_context_score,
                    "dependency_flow": ai_score_obj.dependency_score,
                    "energy_focus": ai_score_obj.energy_score,
                    "reasoning": ai_score_obj.reasoning,
                    "model": ai_score_obj.model_used
                }
            except Exception as e:
                logger.warning(
                    f"[HYBRID-SCORER] AI scoring failed for task {task.id}, "
                    f"using algorithmic only: {str(e)}"
                )
                # Use neutral AI score if AI fails
                ai_score = 16.5  # Middle of 0-33 range

        # Step 3: Combine scores
        total_score = algorithmic_score + ai_score

        # Build comprehensive breakdown
        scoring_breakdown = {
            "algorithm_version": "hybrid_v1.0",
            "max_possible_score": 48.0 if self.use_ai else 15.0,
            "algorithmic": {
                "score": algorithmic_score,
                "max": 15.0,
                "duration_fit": basic_score_obj.duration_fit_score,
                "time_window_match": basic_score_obj.time_window_score,
                "priority_alignment": basic_score_obj.priority_score
            },
            "ai": ai_breakdown if self.use_ai else None
        }

        return HybridTaskSlotScore(
            task_id=task.id,
            slot_id=slot.slot_id,
            total_score=total_score,
            algorithmic_score=algorithmic_score,
            ai_score=ai_score,
            scoring_breakdown=scoring_breakdown
        )

    async def score_all_combinations(
        self,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        calendar_context: Optional[List[CalendarEvent]] = None,
        optimize_ai_calls: bool = True
    ) -> List[HybridTaskSlotScore]:
        """
        Score all possible (task, slot) combinations using hybrid approach

        Args:
            tasks: List of tasks to anchor
            slots: List of available slots
            calendar_context: Optional calendar events for AI context
            optimize_ai_calls: If True, only use AI for ambiguous cases

        Returns:
            List of HybridTaskSlotScore objects sorted by score (descending)
        """
        logger.info(
            f"[HYBRID-SCORER] Scoring {len(tasks)} tasks across {len(slots)} slots"
        )

        # Step 1: Get all algorithmic scores first (fast)
        basic_scores = self.basic_scorer.score_all_combinations(tasks, slots)

        # Step 2: Decide which combinations need AI scoring
        if self.use_ai and self.ai_scorer:
            if optimize_ai_calls:
                # Only use AI for top candidates or ambiguous cases
                # (saves on API costs)
                combinations_to_score_with_ai = self._select_ai_candidates(
                    basic_scores, tasks, slots
                )
                logger.info(
                    f"[HYBRID-SCORER] Using AI for {len(combinations_to_score_with_ai)} "
                    f"combinations (optimized from {len(basic_scores)})"
                )
            else:
                # Score all combinations with AI
                combinations_to_score_with_ai = [
                    (tasks[i // len(slots)], slots[i % len(slots)])
                    for i in range(len(basic_scores))
                ]
                logger.info(
                    f"[HYBRID-SCORER] Using AI for all {len(combinations_to_score_with_ai)} combinations"
                )

            # Get AI scores for selected combinations (score each directly)
            ai_scores_list = []
            print(f"   🤖 AI Scoring: {len(combinations_to_score_with_ai)} combinations (top 3 per task)")
            for idx, (task, slot) in enumerate(combinations_to_score_with_ai, 1):
                print(f"   🔄 [{idx}/{len(combinations_to_score_with_ai)}] AI scoring '{task.title[:30]}...' at {slot.start_time.strftime('%I:%M %p')}", flush=True)
                score = await self.ai_scorer.score_task_slot(task, slot, calendar_context)
                ai_scores_list.append(score)
            print(f"   ✅ AI Scoring complete!")

            # Create AI score lookup
            ai_scores_map = {
                (score.task_id, score.slot_id): score
                for score in ai_scores_list
            }
        else:
            ai_scores_map = {}

        # Step 3: Combine scores
        hybrid_scores = []

        for basic_score in basic_scores:
            key = (basic_score.task_id, basic_score.slot_id)

            # Get AI score if available
            ai_score_obj = ai_scores_map.get(key)
            ai_score = ai_score_obj.total_score if ai_score_obj else 16.5  # Neutral if not scored

            # Build combined score
            total_score = basic_score.total_score + ai_score

            scoring_breakdown = {
                "algorithm_version": "hybrid_v1.0",
                "max_possible_score": 48.0 if self.use_ai else 15.0,
                "algorithmic": {
                    "score": basic_score.total_score,
                    "max": 15.0,
                    "duration_fit": basic_score.duration_fit_score,
                    "time_window_match": basic_score.time_window_score,
                    "priority_alignment": basic_score.priority_score
                },
                "ai": ai_score_obj.to_dict() if ai_score_obj else None
            }

            hybrid_scores.append(HybridTaskSlotScore(
                task_id=basic_score.task_id,
                slot_id=basic_score.slot_id,
                total_score=total_score,
                algorithmic_score=basic_score.total_score,
                ai_score=ai_score,
                scoring_breakdown=scoring_breakdown
            ))

        # Sort by total score (highest first)
        hybrid_scores.sort(key=lambda x: x.total_score, reverse=True)

        logger.info(
            f"[HYBRID-SCORER] Scored {len(hybrid_scores)} combinations "
            f"(avg score: {sum(s.total_score for s in hybrid_scores) / len(hybrid_scores):.1f})"
            if hybrid_scores else "[HYBRID-SCORER] No valid combinations found"
        )

        return hybrid_scores

    def _select_ai_candidates(
        self,
        basic_scores: List,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        top_n_per_task: int = 3
    ) -> List[tuple]:
        """
        Select which combinations need AI scoring (cost optimization)

        Strategy: Only use AI for top N candidates per task, or ambiguous cases

        Args:
            basic_scores: List of basic scores
            tasks: List of tasks
            slots: List of slots
            top_n_per_task: How many top slots to score with AI per task

        Returns:
            List of (task, slot) tuples to score with AI
        """
        # Group scores by task
        scores_by_task = {}
        for score in basic_scores:
            if score.task_id not in scores_by_task:
                scores_by_task[score.task_id] = []
            scores_by_task[score.task_id].append(score)

        # Select top N per task
        candidates = []
        task_map = {t.id: t for t in tasks}
        slot_map = {s.slot_id: s for s in slots}

        for task_id, task_scores in scores_by_task.items():
            # Sort by score
            task_scores.sort(key=lambda x: x.total_score, reverse=True)

            # Take top N
            for score in task_scores[:top_n_per_task]:
                task = task_map.get(score.task_id)
                slot = slot_map.get(score.slot_id)
                if task and slot:
                    candidates.append((task, slot))

        return candidates


# ============================================================================
# Singleton Instance
# ============================================================================

_hybrid_scorer_instance: Optional[HybridScorerService] = None


def get_hybrid_scorer_service(use_ai: bool = True) -> HybridScorerService:
    """
    Get singleton instance of HybridScorerService

    Args:
        use_ai: Whether to enable AI-enhanced scoring

    Returns:
        HybridScorerService instance
    """
    global _hybrid_scorer_instance

    if _hybrid_scorer_instance is None:
        _hybrid_scorer_instance = HybridScorerService(use_ai=use_ai)

    return _hybrid_scorer_instance
