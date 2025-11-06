"""
AI Scorer Service - Phase 4

Implements LLM-based scoring for task-slot combinations.
This is the AI layer of the hybrid scoring system (algorithmic + AI).

Scoring Components (0-33 points total):
1. Task Context (0-12 points): Does task description match slot timing?
2. Dependency & Flow (0-11 points): Does this task naturally follow previous events?
3. Energy & Focus (0-10 points): Does user's energy level match task demands?

Total Possible Score: 33 points (AI portion)
Combined with BasicScorer (15 points) = 48 points total
"""

import os
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import time, datetime
from dataclasses import dataclass

from openai import AsyncOpenAI

from .basic_scorer_service import TaskToAnchor
from .calendar_gap_finder import AvailableSlot
from .calendar_integration_service import CalendarEvent

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AITaskSlotScore:
    """
    AI-based score for a specific (task, slot) combination
    """
    task_id: str
    slot_id: str
    total_score: float  # 0-33 points
    task_context_score: float  # 0-12 points
    dependency_score: float  # 0-11 points
    energy_score: float  # 0-10 points
    reasoning: str
    model_used: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "slot_id": self.slot_id,
            "total_score": self.total_score,
            "scoring_breakdown": {
                "task_context": self.task_context_score,
                "dependency_flow": self.dependency_score,
                "energy_focus": self.energy_score
            },
            "reasoning": self.reasoning,
            "model": self.model_used
        }


# ============================================================================
# AI Scorer Service
# ============================================================================

class AIScorerService:
    """
    LLM-based scorer for task-slot combinations

    Implements phase 4 AI scoring (semantic understanding):
    - Task context and semantic matching
    - Dependency analysis and flow
    - Energy level alignment

    Usage:
        scorer = AIScorerService()
        score = await scorer.score_task_slot(task, slot, calendar_context)
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3
    ):
        """
        Initialize AI scorer service

        Args:
            openai_api_key: OpenAI API key (default: from env)
            model: OpenAI model to use
            temperature: Lower = more consistent, higher = more creative
        """
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment or passed to constructor")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

        logger.info(f"[AI-SCORER] Initialized with model: {model}")

    async def score_task_slot(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> AITaskSlotScore:
        """
        Score how well a task fits a specific time slot using AI

        Args:
            task: Task to anchor
            slot: Available time slot
            calendar_context: Optional surrounding calendar events for context

        Returns:
            AITaskSlotScore with LLM-based scoring (0-33 points)
        """
        try:
            # Build prompt with context
            prompt = self._build_scoring_prompt(task, slot, calendar_context)

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at calendar optimization and task scheduling. Score task-slot combinations based on semantic understanding, dependencies, and energy alignment."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)

            # Create score object
            return AITaskSlotScore(
                task_id=task.id,
                slot_id=slot.slot_id,
                total_score=float(result.get("total_score", 0)),
                task_context_score=float(result.get("task_context_score", 0)),
                dependency_score=float(result.get("dependency_score", 0)),
                energy_score=float(result.get("energy_score", 0)),
                reasoning=result.get("reasoning", ""),
                model_used=self.model
            )

        except Exception as e:
            logger.error(f"[AI-SCORER] Error scoring task {task.id} in slot {slot.slot_id}: {str(e)}")

            # Return default neutral score on error
            return AITaskSlotScore(
                task_id=task.id,
                slot_id=slot.slot_id,
                total_score=16.5,  # Middle of 0-33 range
                task_context_score=6.0,
                dependency_score=5.5,
                energy_score=5.0,
                reasoning="Error during AI scoring - using neutral fallback",
                model_used=self.model
            )

    async def score_all_combinations(
        self,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        calendar_context: Optional[List[CalendarEvent]] = None,
        score_top_n: Optional[int] = None
    ) -> List[AITaskSlotScore]:
        """
        Score multiple task-slot combinations using AI

        Args:
            tasks: List of tasks to anchor
            slots: List of available slots
            calendar_context: Optional calendar events for context
            score_top_n: Optional limit - only score top N combinations (cost optimization)

        Returns:
            List of AITaskSlotScore objects
        """
        scores = []

        # Generate all valid combinations
        combinations = []
        for task in tasks:
            for slot in slots:
                if task.estimated_duration_minutes <= slot.duration_minutes:
                    combinations.append((task, slot))

        # Optionally limit combinations to reduce API costs
        if score_top_n and len(combinations) > score_top_n:
            logger.info(f"[AI-SCORER] Limiting to top {score_top_n} combinations (cost optimization)")
            combinations = combinations[:score_top_n]

        logger.info(f"[AI-SCORER] Scoring {len(combinations)} task-slot combinations with AI")
        print(f"   🤖 AI Scoring: {len(combinations)} combinations to score (this may take 30-60 seconds)...")

        # Score each combination
        for idx, (task, slot) in enumerate(combinations, 1):
            logger.info(f"[AI-SCORER] Progress: {idx}/{len(combinations)} - Scoring task '{task.title}' in slot {slot.start_time.strftime('%I:%M %p')}")
            print(f"   🔄 [{idx}/{len(combinations)}] Scoring '{task.title[:30]}...' at {slot.start_time.strftime('%I:%M %p')}", flush=True)
            score = await self.score_task_slot(task, slot, calendar_context)
            scores.append(score)

        print(f"   ✅ AI Scoring complete! Scored {len(scores)} combinations.")
        return scores

    def _build_scoring_prompt(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> str:
        """
        Build detailed prompt for LLM scoring

        Args:
            task: Task to score
            slot: Slot to score
            calendar_context: Optional surrounding events

        Returns:
            Formatted prompt string
        """
        # Format task info
        task_info = f"""
Task to Schedule:
- Title: {task.title}
- Description: {task.description or "No description"}
- Category: {task.category}
- Priority: {task.priority_level}
- Duration: {task.estimated_duration_minutes} minutes
- Original scheduled time: {task.scheduled_time.strftime('%I:%M %p') if task.scheduled_time else 'Not set'}
- Time block preference: {task.time_block or "Any"}
- Energy zone preference: {task.energy_zone_preference or "Any"}
"""

        # Format slot info
        slot_info = f"""
Available Time Slot:
- Time: {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}
- Duration: {slot.duration_minutes} minutes
- Gap type: {slot.gap_type.value}
- Gap size: {slot.gap_size.value}
"""

        # Add calendar context if available
        context_info = ""
        if calendar_context:
            context_info = "\nSurrounding Calendar Events:\n"
            for event in calendar_context[:5]:  # Show max 5 events
                context_info += f"- {event.title}: {event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}\n"

        # Build full prompt
        prompt = f"""
Score this task-slot combination from 0-33 points based on semantic understanding.

{task_info}

{slot_info}

{context_info}

Score the following aspects:

1. Task Context (0-12 points):
   - Does the task description semantically match this time of day?
   - Is this the right energy level for this specific task?
   - Does the task need uninterrupted time? Is this slot suitable?
   - Consider: Focus requirements, cognitive load, task complexity

2. Dependency & Flow (0-11 points):
   - Does this task naturally follow the previous calendar events?
   - Is there helpful mental context from prior tasks?
   - Does this create good momentum and logical flow?
   - Consider: Context switching cost, task sequencing, natural progression

3. Energy & Focus (0-10 points):
   - Does the user's typical energy level at this time match task demands?
   - Is this peak/maintenance/recovery time appropriate for this task?
   - Will the user be fresh or fatigued at this time?
   - Consider: Circadian rhythm, post-meeting energy, time of day patterns

Return ONLY valid JSON with this exact structure:
{{
  "total_score": <sum of all three scores, 0-33>,
  "task_context_score": <0-12>,
  "dependency_score": <0-11>,
  "energy_score": <0-10>,
  "reasoning": "<brief explanation of the scoring in 1-2 sentences>"
}}

Be precise and consider the holistic fit of this task in this specific time slot.
"""

        return prompt


# ============================================================================
# Singleton Instance
# ============================================================================

_ai_scorer_instance: Optional[AIScorerService] = None


def get_ai_scorer_service() -> AIScorerService:
    """
    Get singleton instance of AIScorerService

    Returns:
        AIScorerService instance
    """
    global _ai_scorer_instance

    if _ai_scorer_instance is None:
        _ai_scorer_instance = AIScorerService()

    return _ai_scorer_instance
