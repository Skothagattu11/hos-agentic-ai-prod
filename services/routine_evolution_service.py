#!/usr/bin/env python3
"""
Routine Evolution Service

Determines evolution strategy based on performance metrics for adaptive routine generation.
This service is part of the optimized dual-mode routine generation system.

Created: 2025-01-19
Status: NEW - Parallel implementation (does not modify existing routine generation)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RoutineEvolutionService:
    """
    Determines evolution strategy based on user performance metrics.

    This service helps the adaptive routine generation system decide how to evolve
    a user's routine based on their completion rates and consistency.

    Evolution Strategies:
    - SIMPLIFY: Reduce task count when user is overwhelmed (<50% completion)
    - MAINTAIN: Keep successful tasks, remove failures (50-75% completion)
    - PROGRESS: Add one new challenge (>75% completion for 7+ days)
    - INTENSIFY: Increase existing task intensity (>85% for 14+ days)
    """

    def determine_evolution_strategy(
        self,
        completion_rate: float,
        days_at_current_level: int,
        satisfaction_avg: float = None
    ) -> Dict[str, Any]:
        """
        Determine evolution strategy based on performance metrics.

        Args:
            completion_rate: Overall completion percentage (0-100)
            days_at_current_level: Number of days at this performance level
            satisfaction_avg: Average satisfaction rating (0-10), optional

        Returns:
            Strategy dict with specific guidance for next routine iteration
        """
        logger.debug(f"Determining evolution strategy: completion={completion_rate}%, days={days_at_current_level}, satisfaction={satisfaction_avg}")

        # OVERWHELMED - Simplify immediately
        if completion_rate < 50:
            return {
                "strategy": "SIMPLIFY",
                "action": "reduce_to_minimum",
                "task_limit": 2,  # Only 2 tasks total (1 morning, 1 evening)
                "new_tasks_allowed": 0,
                "modification_guidance": "Keep only highest satisfaction tasks",
                "adaptation_note": "User is overwhelmed. Reduce to absolute basics.",
                "criteria": {
                    "completion_rate": f"<50% (current: {completion_rate:.1f}%)",
                    "days_at_level": days_at_current_level
                },
                "rationale": "Completion rate below 50% indicates user is struggling. Simplify immediately to build confidence.",
                "expected_outcome": "Increase completion to >60% through reduced cognitive load"
            }

        # STRUGGLING - Maintain with cleanup
        elif completion_rate < 75:
            return {
                "strategy": "MAINTAIN",
                "action": "keep_successful_remove_failures",
                "task_limit": 4,
                "new_tasks_allowed": 0,
                "modification_guidance": "Clean up routine - keep what works, remove what doesn't",
                "adaptation_note": "Clean up routine - keep successes, remove failures, adapt struggling tasks.",
                "criteria": {
                    "completion_rate": f"50-75% (current: {completion_rate:.1f}%)",
                    "days_at_level": days_at_current_level
                },
                "rationale": "User is plateaued. Focus on consistency before adding complexity.",
                "expected_outcome": "Stabilize completion at >75% through routine optimization",
                "specific_actions": [
                    "Keep tasks with >80% completion (exact copy)",
                    "Adapt tasks with 40-80% completion (change timing/duration/approach)",
                    "Remove tasks with <40% completion",
                    "Don't add new tasks yet"
                ]
            }

        # PROGRESSING - Ready for one small addition
        elif completion_rate >= 75 and days_at_current_level >= 7:
            return {
                "strategy": "PROGRESS",
                "action": "add_one_small_challenge",
                "task_limit": 6,
                "new_tasks_allowed": 1,
                "modification_guidance": "Add ONE small progressive challenge in best energy block",
                "adaptation_note": "User is ready for ONE small progressive challenge.",
                "criteria": {
                    "completion_rate": f"≥75% (current: {completion_rate:.1f}%)",
                    "days_at_level": f"≥7 days (current: {days_at_current_level})"
                },
                "rationale": "User has demonstrated consistency. Ready for incremental growth.",
                "expected_outcome": "Maintain >70% completion while adding sustainable challenge",
                "new_task_constraints": {
                    "max_duration_minutes": 10,
                    "placement": "In user's best-performing energy block",
                    "complexity": "Low cognitive load only",
                    "alignment": "Must match archetype preferences"
                },
                "specific_actions": [
                    "Keep all successful tasks (>80% completion) exactly",
                    "Adapt any struggling tasks (40-80%)",
                    "Remove any failed tasks (<40%)",
                    "Add ONE new task (≤10 minutes) in proven time block"
                ]
            }

        # ADVANCED - Can slightly intensify
        elif completion_rate >= 85 and days_at_current_level >= 14:
            return {
                "strategy": "INTENSIFY",
                "action": "increase_existing_task_intensity",
                "task_limit": 6,
                "new_tasks_allowed": 0,  # Don't add, intensify existing
                "modification_guidance": "Slightly increase intensity of existing tasks",
                "adaptation_note": "User mastered current routine. Slightly increase intensity of existing tasks.",
                "criteria": {
                    "completion_rate": f"≥85% (current: {completion_rate:.1f}%)",
                    "days_at_level": f"≥14 days (current: {days_at_current_level})"
                },
                "rationale": "User has mastered current routine. Increase intensity without adding complexity.",
                "expected_outcome": "Sustainable progression through gradual intensity increase",
                "intensification_examples": [
                    "10-min walk → 15-min walk",
                    "5-min meditation → 10-min meditation",
                    "Gentle stretch → Active yoga",
                    "Journaling → Structured reflection with prompts"
                ],
                "specific_actions": [
                    "Keep all successful tasks (don't remove any)",
                    "Slightly increase duration (5-10 minutes more)",
                    "OR increase difficulty (same duration, higher intensity)",
                    "Don't add new tasks - optimize existing ones"
                ]
            }

        # MAINTAINING - Keep current, fine-tune
        else:
            return {
                "strategy": "MAINTAIN",
                "action": "keep_current_fine_tune",
                "task_limit": 6,
                "new_tasks_allowed": 0,
                "modification_guidance": "Routine is working. Make minor timing/implementation tweaks only.",
                "adaptation_note": "Routine is working well. Make minor optimizations only.",
                "criteria": {
                    "completion_rate": f"{completion_rate:.1f}%",
                    "days_at_level": days_at_current_level
                },
                "rationale": "User is performing well but not yet ready for next evolution phase.",
                "expected_outcome": "Maintain current performance while building consistency",
                "specific_actions": [
                    "Keep successful tasks (>80% completion) exactly",
                    "Fine-tune timing of tasks if needed",
                    "Minor adjustments to task descriptions/tips",
                    "Build consistency before adding complexity"
                ]
            }

    def analyze_task_performance(
        self,
        task_checkins: list
    ) -> Dict[str, Any]:
        """
        Analyze individual task performance from check-in data.

        Args:
            task_checkins: List of task check-in records with completion_status, satisfaction_rating

        Returns:
            Dict with per-task performance metrics
        """
        if not task_checkins:
            return {}

        task_performance = {}

        for checkin in task_checkins:
            task_title = checkin.get('title', 'Unknown')
            completion_status = checkin.get('completion_status')
            satisfaction = checkin.get('satisfaction_rating')

            if task_title not in task_performance:
                task_performance[task_title] = {
                    'total_checkins': 0,
                    'completed': 0,
                    'skipped': 0,
                    'satisfaction_ratings': []
                }

            task_performance[task_title]['total_checkins'] += 1

            if completion_status == 'completed':
                task_performance[task_title]['completed'] += 1
            elif completion_status == 'skipped':
                task_performance[task_title]['skipped'] += 1

            if satisfaction:
                task_performance[task_title]['satisfaction_ratings'].append(satisfaction)

        # Calculate metrics for each task
        task_metrics = {}
        for task_title, data in task_performance.items():
            completion_rate = (data['completed'] / data['total_checkins'] * 100) if data['total_checkins'] > 0 else 0
            avg_satisfaction = (
                sum(data['satisfaction_ratings']) / len(data['satisfaction_ratings'])
                if data['satisfaction_ratings'] else None
            )

            # Determine action
            if completion_rate >= 80:
                action = "KEEP"
                reason = "High completion rate - keep exactly as is"
            elif completion_rate >= 40:
                action = "ADAPT"
                reason = "Moderate completion - adapt timing/duration/approach"
            else:
                action = "REMOVE"
                reason = "Low completion - remove from routine"

            task_metrics[task_title] = {
                'completion_rate': round(completion_rate, 1),
                'avg_satisfaction': round(avg_satisfaction, 1) if avg_satisfaction else None,
                'total_checkins': data['total_checkins'],
                'action': action,
                'reason': reason
            }

        return task_metrics

    def get_archetype_task_limit(self, archetype: str, evolution_strategy: str) -> int:
        """
        Get recommended task limit based on archetype and evolution strategy.

        Args:
            archetype: User archetype (Foundation Builder, Peak Performer, etc.)
            evolution_strategy: Current evolution strategy (SIMPLIFY, MAINTAIN, PROGRESS, INTENSIFY)

        Returns:
            Recommended maximum number of tasks
        """
        # Base task limits per archetype (for initial/normal state)
        archetype_limits = {
            "Foundation Builder": 2,
            "Resilience Rebuilder": 2,
            "Connected Explorer": 3,
            "Systematic Improver": 4,
            "Transformation Seeker": 4,
            "Peak Performer": 5
        }

        base_limit = archetype_limits.get(archetype, 3)

        # Adjust based on evolution strategy
        if evolution_strategy == "SIMPLIFY":
            return 2  # Always reduce to 2 tasks when overwhelmed
        elif evolution_strategy == "MAINTAIN":
            return base_limit  # Maintain archetype baseline
        elif evolution_strategy == "PROGRESS":
            return min(base_limit + 1, 6)  # Add one task, max 6
        elif evolution_strategy == "INTENSIFY":
            return base_limit  # Don't add tasks, intensify existing
        else:
            return base_limit


# Singleton instance for easy import
evolution_service = RoutineEvolutionService()

__all__ = ['RoutineEvolutionService', 'evolution_service']
