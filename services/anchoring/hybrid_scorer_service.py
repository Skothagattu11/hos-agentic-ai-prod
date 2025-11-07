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
from .gemini_scorer_service import (
    GeminiAIScorerService,
    get_gemini_scorer_service
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
        use_ai: bool = True,
        use_gemini: bool = True,
        gemini_model: str = "gemini-2.5-flash"
    ):
        """
        Initialize hybrid scorer service

        Args:
            basic_scorer: Optional BasicScorerService instance
            ai_scorer: Optional AIScorerService instance (overrides use_gemini if provided)
            use_ai: Whether to use AI scoring (fallback to algorithmic if False)
            use_gemini: Whether to use Gemini (faster) or OpenAI (default: True)
            gemini_model: Which Gemini model to use
                - "gemini-2.5-flash" (recommended): 40s, good quality
                - "gemini-2.5-flash-lite" (fastest): 8.5s, acceptable quality
        """
        self.basic_scorer = basic_scorer or get_basic_scorer_service()

        # If ai_scorer is explicitly provided, use it (backwards compatibility)
        if ai_scorer is not None:
            self.ai_scorer = ai_scorer
            logger.info("[HYBRID-SCORER] Using provided AI scorer")
        elif use_ai:
            # Use Gemini by default (2-11x faster than OpenAI)
            if use_gemini:
                self.ai_scorer = get_gemini_scorer_service(model=gemini_model)
                logger.info(f"[HYBRID-SCORER] Using Gemini AI scorer ({gemini_model})")
            else:
                self.ai_scorer = get_ai_scorer_service()
                logger.info("[HYBRID-SCORER] Using OpenAI scorer")
        else:
            self.ai_scorer = None

        self.use_ai = use_ai

        if self.use_ai and self.ai_scorer:
            model_name = getattr(self.ai_scorer, 'model_name', getattr(self.ai_scorer, 'model', 'unknown'))
            logger.info(f"[HYBRID-SCORER] Initialized with AI-enhanced scoring (48 points max, model: {model_name})")
        else:
            logger.info("[HYBRID-SCORER] Initialized with algorithmic-only scoring (15 points max)")

    def _apply_semantic_validation(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        base_score: float
    ) -> float:
        """
        Apply semantic validation rules to penalize inappropriate task-slot combinations

        Rules:
        - Sleep/meditation/wind-down tasks should be evening (after 8 PM)
        - Morning routine tasks should be early (before 10 AM)
        - Exercise should be during appropriate energy times
        - Meal planning around meal times

        Args:
            task: Task being scored
            slot: Slot being scored
            base_score: Current score before semantic penalty

        Returns:
            Adjusted score with semantic penalty applied
        """
        from datetime import time as dt_time

        penalty = 0.0
        task_lower = task.title.lower()
        slot_hour = slot.start_time.hour

        # Rule 1: Sleep/wind-down/meditation tasks should be evening (after 8 PM)
        sleep_keywords = ['sleep', 'meditation', 'wind down', 'bedtime', 'night', 'evening routine']
        is_sleep_task = any(keyword in task_lower for keyword in sleep_keywords)
        if is_sleep_task and slot_hour < 20:  # Before 8 PM
            # Heavy penalty for sleep tasks in afternoon/morning
            penalty = 8.0 if slot_hour < 17 else 5.0  # More penalty earlier in day
            logger.debug(f"[SEMANTIC-VALIDATION] Sleep task '{task.title}' at {slot_hour}:00 - penalty: {penalty}")

        # Rule 2: Morning routine tasks should be early (before 10 AM)
        morning_keywords = ['morning', 'breakfast', 'wake up', 'sunrise']
        is_morning_task = any(keyword in task_lower for keyword in morning_keywords)
        if is_morning_task and slot_hour >= 10:
            # Penalty increases with how late it is
            penalty = min(6.0, (slot_hour - 10) * 1.5)
            logger.debug(f"[SEMANTIC-VALIDATION] Morning task '{task.title}' at {slot_hour}:00 - penalty: {penalty}")

        # Rule 3: High-energy exercise should not be late evening
        exercise_keywords = ['workout', 'exercise', 'training', 'cardio', 'hiit', 'strength']
        is_exercise_task = any(keyword in task_lower for keyword in exercise_keywords)
        if is_exercise_task and slot_hour >= 21:  # After 9 PM
            penalty = 4.0
            logger.debug(f"[SEMANTIC-VALIDATION] Exercise task '{task.title}' at {slot_hour}:00 - penalty: {penalty}")

        # Rule 4: Energy zone preference violations (if specified)
        if task.energy_zone_preference:
            zone_lower = task.energy_zone_preference.lower()
            if 'evening' in zone_lower or 'wind_down' in zone_lower:
                # Evening tasks should be after 6 PM
                if slot_hour < 18:
                    penalty = max(penalty, 6.0)
                    logger.debug(f"[SEMANTIC-VALIDATION] Evening zone task '{task.title}' at {slot_hour}:00 - penalty: 6.0")
            elif 'morning' in zone_lower or 'peak' in zone_lower:
                # Morning/peak tasks should be before 12 PM
                if slot_hour >= 12:
                    penalty = max(penalty, 4.0)
                    logger.debug(f"[SEMANTIC-VALIDATION] Morning/peak zone task '{task.title}' at {slot_hour}:00 - penalty: 4.0")

        # Apply penalty (subtract from base score, never go negative)
        adjusted_score = max(0.0, base_score - penalty)

        if penalty > 0:
            logger.info(
                f"[SEMANTIC-VALIDATION] Task '{task.title}' at {slot.start_time.strftime('%H:%M')} "
                f"- semantic penalty: {penalty:.1f} (score: {base_score:.1f} → {adjusted_score:.1f})"
            )

        return adjusted_score

    def _enforce_energy_zone_constraints(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        base_score: float
    ) -> float:
        """
        Enforce energy zone preferences as hard constraints with heavy penalties

        Energy Zone Time Mappings:
        - morning_energy: 6 AM - 10 AM
        - peak_energy/peak_focus: 9 AM - 2 PM
        - afternoon: 12 PM - 6 PM
        - evening_wind_down: 6 PM - 11 PM

        Args:
            task: Task being scored
            slot: Slot being scored
            base_score: Current score before energy zone penalty

        Returns:
            Adjusted score with heavy penalty if energy zone doesn't match
        """
        if not task.energy_zone_preference:
            return base_score  # No preference specified

        zone_lower = task.energy_zone_preference.lower()
        slot_hour = slot.start_time.hour

        # Define strict energy zone time windows
        energy_zones = {
            'morning': (6, 10),
            'peak': (9, 14),
            'afternoon': (12, 18),
            'evening': (18, 23),
            'wind_down': (18, 23)
        }

        # Find matching zone
        zone_match = None
        for zone_name, (start_hour, end_hour) in energy_zones.items():
            if zone_name in zone_lower:
                zone_match = (start_hour, end_hour)
                break

        if zone_match:
            start_hour, end_hour = zone_match
            if not (start_hour <= slot_hour < end_hour):
                # Heavy penalty for energy zone violations (15 points = entire algorithmic score)
                # This effectively makes energy zone a hard constraint
                penalty = 15.0
                logger.warning(
                    f"[ENERGY-ZONE-VIOLATION] Task '{task.title}' (zone: {task.energy_zone_preference}) "
                    f"at {slot.start_time.strftime('%H:%M')} violates energy zone "
                    f"(expected: {start_hour}:00-{end_hour}:00) - penalty: {penalty}"
                )
                adjusted_score = max(0.0, base_score - penalty)
                return adjusted_score

        return base_score

    def _is_semantically_valid(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot
    ) -> bool:
        """
        Check if a task-slot combination is semantically valid (hard constraints)

        Some task-slot combinations are fundamentally inappropriate and should
        be filtered out entirely rather than just penalized.

        Hard constraints:
        - Sleep/meditation/wind-down tasks MUST be in evening (after 6 PM)
        - Morning routine tasks MUST be before 11 AM

        Args:
            task: Task being checked
            slot: Slot being checked

        Returns:
            True if combination is valid, False if it should be filtered out
        """
        task_lower = task.title.lower()
        slot_hour = slot.start_time.hour

        # HARD CONSTRAINT 1: Sleep/meditation/wind-down tasks MUST be evening (after 6 PM)
        sleep_keywords = ['sleep', 'meditation', 'wind down', 'bedtime', 'night', 'evening routine']
        is_sleep_task = any(keyword in task_lower for keyword in sleep_keywords)
        if is_sleep_task and slot_hour < 18:  # Before 6 PM
            logger.warning(
                f"[SEMANTIC-FILTER] BLOCKED: Sleep task '{task.title}' cannot be placed at "
                f"{slot.start_time.strftime('%H:%M')} (must be after 6 PM)"
            )
            return False

        # HARD CONSTRAINT 2: Morning routine tasks MUST be before 11 AM
        morning_keywords = ['morning', 'breakfast', 'wake up', 'sunrise']
        is_morning_task = any(keyword in task_lower for keyword in morning_keywords)
        if is_morning_task and slot_hour >= 11:
            logger.warning(
                f"[SEMANTIC-FILTER] BLOCKED: Morning task '{task.title}' cannot be placed at "
                f"{slot.start_time.strftime('%H:%M')} (must be before 11 AM)"
            )
            return False

        return True

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

        # Step 1.5: Apply semantic validation (penalize inappropriate placements)
        algorithmic_score = self._apply_semantic_validation(task, slot, algorithmic_score)

        # Step 1.6: Enforce energy zone constraints as hard constraints
        algorithmic_score = self._enforce_energy_zone_constraints(task, slot, algorithmic_score)

        # Step 2: Get AI score (if enabled)
        ai_score = 0.0
        ai_breakdown = {}

        if self.use_ai and self.ai_scorer:
            try:
                logger.debug(f"[AI-SCORING] Calling AI scorer for task '{task.title}' at {slot.start_time.strftime('%H:%M')}")
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
                logger.info(
                    f"[AI-SCORING] Task '{task.title}' at {slot.start_time.strftime('%H:%M')} - "
                    f"AI score: {ai_score:.1f}/33.0 (context: {ai_score_obj.task_context_score:.1f}, "
                    f"flow: {ai_score_obj.dependency_score:.1f}, energy: {ai_score_obj.energy_score:.1f})"
                )
            except Exception as e:
                logger.warning(
                    f"[HYBRID-SCORER] AI scoring failed for task {task.id}, "
                    f"using algorithmic only: {str(e)}"
                )
                # Use neutral AI score if AI fails
                ai_score = 16.5  # Middle of 0-33 range

        # Step 3: Combine scores
        total_score = algorithmic_score + ai_score

        # Log final score combination
        if self.use_ai and ai_score > 0:
            logger.info(
                f"[HYBRID-SCORER] Task '{task.title}' at {slot.start_time.strftime('%H:%M')} - "
                f"TOTAL: {total_score:.1f}/48.0 (Algo: {algorithmic_score:.1f}/15.0 + AI: {ai_score:.1f}/33.0)"
            )
        else:
            logger.debug(
                f"[HYBRID-SCORER] Task '{task.title}' at {slot.start_time.strftime('%H:%M')} - "
                f"TOTAL: {total_score:.1f}/15.0 (algorithmic-only mode)"
            )

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
        from datetime import datetime
        start_total = datetime.now()

        logger.info(
            f"[HYBRID-SCORER] Scoring {len(tasks)} tasks across {len(slots)} slots"
        )
        print(f"\n   [HYBRID-SCORER] Starting hybrid scoring...")

        # Step 0.5: Filter out semantically invalid combinations (hard constraints)
        print(f"   [STEP 0] Applying semantic hard constraints...")
        valid_combinations = []
        invalid_count = 0
        for task in tasks:
            for slot in slots:
                if self._is_semantically_valid(task, slot):
                    valid_combinations.append((task, slot))
                else:
                    invalid_count += 1

        if invalid_count > 0:
            print(f"   [FILTER] Blocked {invalid_count} semantically invalid combinations")
            logger.info(f"[HYBRID-SCORER] Filtered out {invalid_count} invalid combinations")

        # Update tasks/slots to only include valid combinations
        # Create filtered task and slot lists for scoring
        valid_task_slot_pairs = valid_combinations

        # Step 1: Get all algorithmic scores first (fast) - only for valid combinations
        print(f"   [STEP 1] Algorithmic scoring...")
        start_algo = datetime.now()

        # Score only valid combinations
        basic_scores = []
        for task, slot in valid_task_slot_pairs:
            basic_score = self.basic_scorer.score_task_slot(task, slot)
            basic_scores.append(basic_score)

        end_algo = datetime.now()
        algo_time = (end_algo - start_algo).total_seconds()
        print(f"   [TIMING] Algorithmic scoring: {algo_time:.2f}s ({len(basic_scores)} combinations)")

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
                # Score all VALID combinations with AI
                combinations_to_score_with_ai = valid_task_slot_pairs
                logger.info(
                    f"[HYBRID-SCORER] Using AI for all {len(combinations_to_score_with_ai)} valid combinations"
                )

            # Get AI scores using BATCH scoring (Option 2 - single API call)
            print(f"   [STEP 2] AI Batch Scoring: {len(combinations_to_score_with_ai)} combinations...")
            start_ai = datetime.now()
            ai_scores_list = await self.ai_scorer.score_batch(
                combinations_to_score_with_ai,
                calendar_context
            )
            end_ai = datetime.now()
            ai_time = (end_ai - start_ai).total_seconds()
            print(f"   [TIMING] AI batch scoring: {ai_time:.2f}s")

            # Create AI score lookup
            ai_scores_map = {
                (score.task_id, score.slot_id): score
                for score in ai_scores_list
            }
        else:
            ai_scores_map = {}
            ai_time = 0

        # Step 3: Combine scores
        print(f"   [STEP 3] Combining {len(basic_scores)} algorithmic + AI scores...")
        start_combine = datetime.now()
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

        end_combine = datetime.now()
        combine_time = (end_combine - start_combine).total_seconds()
        print(f"   [TIMING] Score combination: {combine_time:.2f}s")

        # Total time summary
        end_total = datetime.now()
        total_time = (end_total - start_total).total_seconds()

        print(f"\n   [HYBRID-SCORER TIMING SUMMARY]")
        print(f"   • Algorithmic:     {algo_time:.2f}s ({algo_time/total_time*100:.1f}%)")
        print(f"   • AI Batch:        {ai_time:.2f}s ({ai_time/total_time*100:.1f}%)")
        print(f"   • Combining:       {combine_time:.2f}s ({combine_time/total_time*100:.1f}%)")
        print(f"   • TOTAL:           {total_time:.2f}s")

        logger.info(
            f"[HYBRID-SCORER] Scored {len(hybrid_scores)} combinations in {total_time:.2f}s "
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


def get_hybrid_scorer_service(
    use_ai: bool = True,
    use_gemini: bool = True,
    gemini_model: Optional[str] = None
) -> HybridScorerService:
    """
    Get singleton instance of HybridScorerService

    Args:
        use_ai: Whether to enable AI-enhanced scoring
        use_gemini: Whether to use Gemini (faster, 2-11x) or OpenAI (default: True)
        gemini_model: Which Gemini model to use (defaults to GEMINI_MODEL env var or "gemini-2.5-flash")
            - "gemini-2.5-flash" (recommended): 40s, good quality balance
            - "gemini-2.5-flash-lite" (fastest): 8.5s, acceptable quality

    Returns:
        HybridScorerService instance configured with Gemini by default
    """
    global _hybrid_scorer_instance

    if _hybrid_scorer_instance is None:
        # Read model from environment if not provided
        if gemini_model is None:
            import os
            gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

        _hybrid_scorer_instance = HybridScorerService(
            use_ai=use_ai,
            use_gemini=use_gemini,
            gemini_model=gemini_model
        )

    return _hybrid_scorer_instance
