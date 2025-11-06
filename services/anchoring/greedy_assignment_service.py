"""
Greedy Assignment Service - Phase 2

Implements greedy algorithm to assign tasks to optimal time slots.
Uses scores from BasicScorerService to make assignment decisions.

Algorithm:
1. Sort all (task, slot) combinations by score (descending)
2. For each task (highest-scored first):
   - Assign to best available slot
   - Update slot availability (reduce available time)
   - Re-score remaining tasks if needed
3. Return all assignments
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import time, datetime, timedelta
from dataclasses import dataclass
from copy import deepcopy

from .basic_scorer_service import TaskToAnchor, TaskSlotScore
from .calendar_gap_finder import AvailableSlot

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TaskAssignment:
    """
    Final assignment of a task to a specific time slot
    """
    task_id: str
    task_title: str
    original_time: time
    original_end_time: time
    anchored_time: time
    anchored_end_time: time
    duration_minutes: int
    slot_id: str
    confidence_score: float
    time_adjustment_minutes: int
    scoring_breakdown: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_title": self.task_title,
            "original_time": self.original_time.strftime("%H:%M:%S"),
            "original_end_time": self.original_end_time.strftime("%H:%M:%S"),
            "anchored_time": self.anchored_time.strftime("%H:%M:%S"),
            "anchored_end_time": self.anchored_end_time.strftime("%H:%M:%S"),
            "duration_minutes": self.duration_minutes,
            "slot_id": self.slot_id,
            "confidence_score": self.confidence_score,
            "time_adjustment_minutes": self.time_adjustment_minutes,
            "scoring_breakdown": self.scoring_breakdown,
            "was_rescheduled": self.time_adjustment_minutes != 0
        }


@dataclass
class AssignmentResult:
    """
    Result of greedy assignment algorithm
    """
    assignments: List[TaskAssignment]
    total_tasks: int
    tasks_anchored: int
    tasks_rescheduled: int
    tasks_kept_original_time: int
    average_confidence: float
    unassigned_tasks: List[str]  # Task IDs that couldn't be assigned

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "assignments": [a.to_dict() for a in self.assignments],
            "summary": {
                "total_tasks": self.total_tasks,
                "tasks_anchored": self.tasks_anchored,
                "tasks_rescheduled": self.tasks_rescheduled,
                "tasks_kept_original_time": self.tasks_kept_original_time,
                "average_confidence": self.average_confidence,
                "unassigned_count": len(self.unassigned_tasks)
            },
            "unassigned_tasks": self.unassigned_tasks
        }


# ============================================================================
# Greedy Assignment Service
# ============================================================================

class GreedyAssignmentService:
    """
    Greedy algorithm for assigning tasks to time slots

    Uses scores from BasicScorerService to make optimal assignments.
    Handles slot availability updates and conflict resolution.

    Usage:
        assigner = GreedyAssignmentService()
        result = assigner.assign_tasks(tasks, slots, scores)
    """

    def __init__(self):
        """Initialize assignment service"""
        pass

    def assign_tasks(
        self,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        scores: List[TaskSlotScore]
    ) -> AssignmentResult:
        """
        Assign tasks to slots using greedy algorithm

        Args:
            tasks: List of tasks to anchor
            slots: List of available time slots
            scores: Pre-computed scores for all (task, slot) combinations

        Returns:
            AssignmentResult with all assignments
        """
        logger.info(
            f"[GREEDY-ASSIGNMENT] Starting assignment for {len(tasks)} tasks "
            f"across {len(slots)} slots"
        )

        # Create working copies
        available_slots = {slot.slot_id: deepcopy(slot) for slot in slots}
        task_map = {task.id: task for task in tasks}
        assigned_tasks = set()
        assignments = []

        # Sort scores by total score (highest first)
        sorted_scores = sorted(scores, key=lambda x: x.total_score, reverse=True)

        # Greedy assignment
        for score in sorted_scores:
            task_id = score.task_id
            slot_id = score.slot_id

            # Skip if task already assigned
            if task_id in assigned_tasks:
                continue

            # Skip if slot no longer available
            if slot_id not in available_slots:
                continue

            task = task_map[task_id]
            slot = available_slots[slot_id]

            # Check if task still fits in slot (slot may have been partially used)
            if task.estimated_duration_minutes > slot.duration_minutes:
                continue

            # Assign task to slot
            assignment = self._create_assignment(task, slot, score)
            assignments.append(assignment)
            assigned_tasks.add(task_id)

            logger.info(
                f"[GREEDY-ASSIGNMENT] Assigned '{task.title}' to slot {slot_id} "
                f"(score: {score.total_score:.1f})"
            )

            # Update slot availability
            self._update_slot_availability(
                available_slots,
                slot_id,
                task.estimated_duration_minutes,
                assignment.anchored_end_time
            )

        # Handle unassigned tasks (fallback to original times)
        unassigned_task_ids = []
        for task in tasks:
            if task.id not in assigned_tasks:
                logger.warning(
                    f"[GREEDY-ASSIGNMENT] Task '{task.title}' could not be assigned, "
                    f"using original time"
                )
                # Keep original time as fallback
                assignment = self._create_fallback_assignment(task)
                assignments.append(assignment)
                unassigned_task_ids.append(task.id)

        # Calculate summary statistics
        result = self._create_result(assignments, len(tasks), unassigned_task_ids)

        logger.info(
            f"[GREEDY-ASSIGNMENT] Completed: {result.tasks_anchored} tasks anchored, "
            f"{result.tasks_rescheduled} rescheduled, "
            f"average confidence: {result.average_confidence:.2f}"
        )

        return result

    def _create_assignment(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        score: TaskSlotScore
    ) -> TaskAssignment:
        """
        Create task assignment for a successfully anchored task

        Args:
            task: Task being assigned
            slot: Slot it's being assigned to
            score: Score object with scoring details

        Returns:
            TaskAssignment object
        """
        # Calculate anchored time (start of slot)
        anchored_time = slot.start_time

        # Calculate anchored end time
        anchored_datetime = datetime.combine(datetime.today(), anchored_time)
        anchored_end_datetime = anchored_datetime + timedelta(minutes=task.estimated_duration_minutes)
        anchored_end_time = anchored_end_datetime.time()

        # Calculate time adjustment
        original_datetime = datetime.combine(datetime.today(), task.scheduled_time)
        anchored_datetime_full = datetime.combine(datetime.today(), anchored_time)
        time_diff = (anchored_datetime_full - original_datetime).total_seconds() / 60

        # Normalize confidence score (0-15 points → 0-1.0 scale)
        confidence = score.total_score / 15.0

        return TaskAssignment(
            task_id=task.id,
            task_title=task.title,
            original_time=task.scheduled_time,
            original_end_time=task.scheduled_end_time,
            anchored_time=anchored_time,
            anchored_end_time=anchored_end_time,
            duration_minutes=task.estimated_duration_minutes,
            slot_id=slot.slot_id,
            confidence_score=confidence,
            time_adjustment_minutes=int(time_diff),
            scoring_breakdown=score.scoring_breakdown
        )

    def _create_fallback_assignment(self, task: TaskToAnchor) -> TaskAssignment:
        """
        Create fallback assignment for unassigned task (keeps original time)

        Args:
            task: Task that couldn't be assigned

        Returns:
            TaskAssignment with original time
        """
        return TaskAssignment(
            task_id=task.id,
            task_title=task.title,
            original_time=task.scheduled_time,
            original_end_time=task.scheduled_end_time,
            anchored_time=task.scheduled_time,
            anchored_end_time=task.scheduled_end_time,
            duration_minutes=task.estimated_duration_minutes,
            slot_id="fallback_original_time",
            confidence_score=0.5,  # Low confidence for fallback
            time_adjustment_minutes=0,
            scoring_breakdown={
                "fallback": True,
                "reason": "No suitable slot found, kept original time"
            }
        )

    def _update_slot_availability(
        self,
        available_slots: Dict[str, AvailableSlot],
        slot_id: str,
        task_duration: int,
        task_end_time: time
    ):
        """
        Update slot availability after assigning a task

        Args:
            available_slots: Dictionary of available slots (modified in place)
            slot_id: ID of slot being updated
            task_duration: Duration of task that was assigned
            task_end_time: End time of assigned task
        """
        slot = available_slots[slot_id]

        # Calculate remaining time in slot
        remaining_minutes = slot.duration_minutes - task_duration

        # If slot has < 15 minutes left, mark as full (remove from available)
        if remaining_minutes < 15:
            del available_slots[slot_id]
            logger.debug(f"[GREEDY-ASSIGNMENT] Slot {slot_id} is now full (removed)")
        else:
            # Update slot to start after the assigned task
            slot.start_time = task_end_time
            slot.duration_minutes = remaining_minutes
            logger.debug(
                f"[GREEDY-ASSIGNMENT] Slot {slot_id} updated: "
                f"now starts at {task_end_time}, {remaining_minutes} min remaining"
            )

    def _create_result(
        self,
        assignments: List[TaskAssignment],
        total_tasks: int,
        unassigned_task_ids: List[str]
    ) -> AssignmentResult:
        """
        Create final assignment result with summary statistics

        Args:
            assignments: List of all assignments
            total_tasks: Total number of tasks
            unassigned_task_ids: List of task IDs that couldn't be assigned

        Returns:
            AssignmentResult object
        """
        tasks_rescheduled = sum(
            1 for a in assignments if a.time_adjustment_minutes != 0
        )
        tasks_kept_original = total_tasks - tasks_rescheduled

        # Calculate average confidence (excluding fallback assignments)
        valid_assignments = [a for a in assignments if a.slot_id != "fallback_original_time"]
        avg_confidence = (
            sum(a.confidence_score for a in valid_assignments) / len(valid_assignments)
            if valid_assignments else 0.0
        )

        return AssignmentResult(
            assignments=assignments,
            total_tasks=total_tasks,
            tasks_anchored=len(assignments),
            tasks_rescheduled=tasks_rescheduled,
            tasks_kept_original_time=tasks_kept_original,
            average_confidence=avg_confidence,
            unassigned_tasks=unassigned_task_ids
        )


# ============================================================================
# Singleton Instance
# ============================================================================

_assignment_service_instance: Optional[GreedyAssignmentService] = None


def get_greedy_assignment_service() -> GreedyAssignmentService:
    """
    Get singleton instance of GreedyAssignmentService

    Returns:
        GreedyAssignmentService instance
    """
    global _assignment_service_instance

    if _assignment_service_instance is None:
        _assignment_service_instance = GreedyAssignmentService()

    return _assignment_service_instance
