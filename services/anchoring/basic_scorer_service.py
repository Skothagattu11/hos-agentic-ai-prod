"""
Basic Scorer Service - Phase 2

Implements algorithmic scoring for task-slot combinations.
This is the first part of the hybrid scoring system (algorithmic + AI).

Scoring Components:
1. Duration Fit (0-2 points): How well task duration fits the available slot
2. Time Window Match (0-10 points): Whether task prefers this time of day
3. Priority Alignment (0-3 points): High-priority tasks in peak slots

Total Possible Score: 15 points (algorithmic portion only)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import time, datetime
from dataclasses import dataclass
from enum import Enum

from .calendar_gap_finder import AvailableSlot

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class TimeWindowPreference(str, Enum):
    """Time of day preferences for tasks"""
    MORNING = "morning"  # 6 AM - 9 AM
    PEAK = "peak"  # 9 AM - 12 PM
    MIDDAY = "midday"  # 12 PM - 2 PM
    AFTERNOON = "afternoon"  # 2 PM - 5 PM
    EVENING = "evening"  # 5 PM - 9 PM
    ANY = "any"


class PriorityLevel(str, Enum):
    """Task priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskToAnchor:
    """
    Task that needs to be anchored to calendar

    Loaded from plan_items table with relevant metadata
    """
    id: str
    title: str
    description: Optional[str]
    category: str
    priority_level: str
    scheduled_time: time
    scheduled_end_time: time
    estimated_duration_minutes: int
    time_block: Optional[str] = None
    energy_zone_preference: Optional[str] = None

    def get_priority(self) -> PriorityLevel:
        """Convert string priority to enum"""
        try:
            return PriorityLevel(self.priority_level.lower())
        except:
            return PriorityLevel.MEDIUM

    def get_time_preference(self) -> TimeWindowPreference:
        """Infer time preference from energy_zone or time_block"""
        if self.energy_zone_preference:
            zone = self.energy_zone_preference.lower()
            if 'peak' in zone or 'focus' in zone:
                return TimeWindowPreference.PEAK
            elif 'recovery' in zone or 'wind' in zone:
                return TimeWindowPreference.EVENING

        if self.time_block:
            block = self.time_block.lower()
            if 'morning' in block:
                return TimeWindowPreference.MORNING
            elif 'afternoon' in block:
                return TimeWindowPreference.AFTERNOON
            elif 'evening' in block:
                return TimeWindowPreference.EVENING
            elif 'peak' in block:
                return TimeWindowPreference.PEAK

        # Default: use scheduled_time to infer
        hour = self.scheduled_time.hour
        if 6 <= hour < 9:
            return TimeWindowPreference.MORNING
        elif 9 <= hour < 12:
            return TimeWindowPreference.PEAK
        elif 12 <= hour < 14:
            return TimeWindowPreference.MIDDAY
        elif 14 <= hour < 17:
            return TimeWindowPreference.AFTERNOON
        elif 17 <= hour < 21:
            return TimeWindowPreference.EVENING
        else:
            return TimeWindowPreference.ANY


@dataclass
class TaskSlotScore:
    """
    Score for a specific (task, slot) combination
    """
    task_id: str
    slot_id: str
    total_score: float
    duration_fit_score: float
    time_window_score: float
    priority_score: float
    scoring_breakdown: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "slot_id": self.slot_id,
            "total_score": self.total_score,
            "scoring_breakdown": {
                "duration_fit": self.duration_fit_score,
                "time_window_match": self.time_window_score,
                "priority_alignment": self.priority_score
            }
        }


# ============================================================================
# Basic Scorer Service
# ============================================================================

class BasicScorerService:
    """
    Algorithmic scorer for task-slot combinations

    Implements phase 2 scoring (no AI, pure algorithm):
    - Duration fit
    - Time window preferences
    - Priority alignment

    Usage:
        scorer = BasicScorerService()
        score = scorer.score_task_slot(task, slot)
    """

    def __init__(self):
        """Initialize scorer service"""
        self.max_duration_fit_score = 2.0
        self.max_time_window_score = 10.0
        self.max_priority_score = 3.0

    def score_task_slot(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot
    ) -> TaskSlotScore:
        """
        Score how well a task fits a specific time slot

        Args:
            task: Task to anchor
            slot: Available time slot

        Returns:
            TaskSlotScore with algorithmic scoring only
        """
        # Component 1: Duration Fit (0-2 points)
        duration_fit = self._score_duration_fit(
            task.estimated_duration_minutes,
            slot.duration_minutes
        )

        # Component 2: Time Window Match (0-10 points)
        time_window = self._score_time_window_match(
            task.get_time_preference(),
            slot
        )

        # Component 3: Priority Alignment (0-3 points)
        priority = self._score_priority_alignment(
            task.get_priority(),
            slot
        )

        # Calculate total
        total = duration_fit + time_window + priority

        # Create score object
        return TaskSlotScore(
            task_id=task.id,
            slot_id=slot.slot_id,
            total_score=total,
            duration_fit_score=duration_fit,
            time_window_score=time_window,
            priority_score=priority,
            scoring_breakdown={
                "algorithm_version": "basic_v1.0",
                "max_possible_score": 15.0,
                "duration_fit": {
                    "score": duration_fit,
                    "task_duration": task.estimated_duration_minutes,
                    "slot_duration": slot.duration_minutes
                },
                "time_window": {
                    "score": time_window,
                    "preferred_window": task.get_time_preference().value,
                    "slot_window": self._classify_slot_time_window(slot)
                },
                "priority": {
                    "score": priority,
                    "task_priority": task.get_priority().value
                }
            }
        )

    def score_all_combinations(
        self,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot]
    ) -> List[TaskSlotScore]:
        """
        Score all possible (task, slot) combinations

        Args:
            tasks: List of tasks to anchor
            slots: List of available slots

        Returns:
            List of TaskSlotScore objects sorted by score (descending)
        """
        scores = []

        for task in tasks:
            for slot in slots:
                # Only score if task can fit in slot
                if task.estimated_duration_minutes <= slot.duration_minutes:
                    score = self.score_task_slot(task, slot)
                    scores.append(score)

        # Sort by total score (highest first)
        scores.sort(key=lambda x: x.total_score, reverse=True)

        logger.info(
            f"[BASIC-SCORER] Scored {len(scores)} combinations "
            f"for {len(tasks)} tasks and {len(slots)} slots"
        )

        return scores

    # ========================================================================
    # Scoring Components
    # ========================================================================

    def _score_duration_fit(
        self,
        task_duration: int,
        slot_duration: int
    ) -> float:
        """
        Score how well task duration fits the slot

        Args:
            task_duration: Task duration in minutes
            slot_duration: Slot duration in minutes

        Returns:
            Score from 0 to 2
        """
        if task_duration > slot_duration:
            return 0.0  # Task doesn't fit

        # Calculate utilization percentage
        utilization = task_duration / slot_duration

        # Perfect fit: task uses 80-100% of slot
        if 0.8 <= utilization <= 1.0:
            return 2.0

        # Close fit: task uses 60-80% of slot
        elif 0.6 <= utilization < 0.8:
            return 1.5

        # Good fit: task uses 40-60% of slot
        elif 0.4 <= utilization < 0.6:
            return 1.0

        # Poor fit: task uses less than 40% of slot (lots of wasted space)
        else:
            return 0.5

    def _score_time_window_match(
        self,
        task_preference: TimeWindowPreference,
        slot: AvailableSlot
    ) -> float:
        """
        Score how well slot time matches task's preferred time window

        Args:
            task_preference: Task's preferred time of day
            slot: Available time slot

        Returns:
            Score from 0 to 10
        """
        slot_window = self._classify_slot_time_window(slot)

        # Task has no preference - any time is fine
        if task_preference == TimeWindowPreference.ANY:
            return 5.0

        # Exact match: preferred window matches slot window
        if task_preference.value == slot_window:
            return 10.0

        # Adjacent match: preferred window is adjacent to slot window
        adjacent_matches = {
            TimeWindowPreference.MORNING: [TimeWindowPreference.PEAK],
            TimeWindowPreference.PEAK: [TimeWindowPreference.MORNING, TimeWindowPreference.MIDDAY],
            TimeWindowPreference.MIDDAY: [TimeWindowPreference.PEAK, TimeWindowPreference.AFTERNOON],
            TimeWindowPreference.AFTERNOON: [TimeWindowPreference.MIDDAY, TimeWindowPreference.EVENING],
            TimeWindowPreference.EVENING: [TimeWindowPreference.AFTERNOON]
        }

        if slot_window in [w.value for w in adjacent_matches.get(task_preference, [])]:
            return 6.0

        # No match: different time of day
        return 2.0

    def _score_priority_alignment(
        self,
        task_priority: PriorityLevel,
        slot: AvailableSlot
    ) -> float:
        """
        Score priority alignment (high-priority tasks in peak slots)

        Args:
            task_priority: Task priority level
            slot: Available time slot

        Returns:
            Score from 0 to 3
        """
        slot_window = self._classify_slot_time_window(slot)

        # High-priority task in peak energy slot
        if task_priority == PriorityLevel.HIGH and slot_window == "peak":
            return 3.0

        # High-priority task in morning slot (also good)
        if task_priority == PriorityLevel.HIGH and slot_window == "morning":
            return 2.5

        # Medium-priority task in midday/afternoon (maintenance)
        if task_priority == PriorityLevel.MEDIUM and slot_window in ["midday", "afternoon"]:
            return 2.0

        # Low-priority task in evening (recovery)
        if task_priority == PriorityLevel.LOW and slot_window == "evening":
            return 1.5

        # Any match is better than nothing
        return 1.0

    def _classify_slot_time_window(self, slot: AvailableSlot) -> str:
        """
        Classify what time window a slot belongs to

        Args:
            slot: Available time slot

        Returns:
            Time window classification
        """
        start_hour = slot.start_time.hour

        if 6 <= start_hour < 9:
            return "morning"
        elif 9 <= start_hour < 12:
            return "peak"
        elif 12 <= start_hour < 14:
            return "midday"
        elif 14 <= start_hour < 17:
            return "afternoon"
        elif 17 <= start_hour < 21:
            return "evening"
        else:
            return "any"


# ============================================================================
# Singleton Instance
# ============================================================================

_scorer_service_instance: Optional[BasicScorerService] = None


def get_basic_scorer_service() -> BasicScorerService:
    """
    Get singleton instance of BasicScorerService

    Returns:
        BasicScorerService instance
    """
    global _scorer_service_instance

    if _scorer_service_instance is None:
        _scorer_service_instance = BasicScorerService()

    return _scorer_service_instance
