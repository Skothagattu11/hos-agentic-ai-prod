"""
Gemini AI Scorer Service - High-Speed Alternative to OpenAI

Implements the same interface as AIScorerService but uses Google Gemini models.

Performance Benefits:
- gemini-2.5-flash: 40s (2.3x faster than OpenAI)
- gemini-2.5-flash-lite: 8.5s (11x faster than OpenAI!)

Scoring Components (0-33 points total):
1. Task Context (0-12 points): Does task description match slot timing?
2. Dependency & Flow (0-11 points): Does this task naturally follow previous events?
3. Energy & Focus (0-10 points): Does user's energy level match task demands?
"""

import os
import logging
import json
import re
from typing import List, Optional
from datetime import datetime

import google.generativeai as genai

from .basic_scorer_service import TaskToAnchor
from .calendar_gap_finder import AvailableSlot
from .calendar_integration_service import CalendarEvent
from .ai_scorer_service import AITaskSlotScore

logger = logging.getLogger(__name__)


class GeminiAIScorerService:
    """
    Gemini-based scorer for task-slot combinations

    Drop-in replacement for AIScorerService with 2-11x faster performance.

    Usage:
        scorer = GeminiAIScorerService(model="gemini-2.5-flash")
        score = await scorer.score_task_slot(task, slot, calendar_context)
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.3
    ):
        """
        Initialize Gemini AI scorer service

        Args:
            gemini_api_key: Gemini API key (default: from env GEMINI_API_KEY)
            model: Gemini model to use
                - "gemini-2.5-flash" (recommended): 40s, good quality
                - "gemini-2.5-flash-lite" (fastest): 8.5s, acceptable quality
            temperature: Lower = more consistent, higher = more creative
        """
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment or passed to constructor")

        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature

        logger.info(f"[GEMINI-SCORER] Initialized with model: {model}")

    async def score_task_slot(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> AITaskSlotScore:
        """
        Score how well a task fits a specific time slot using Gemini AI

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

            # Call Gemini API
            response = self.model.generate_content(prompt)

            # Parse response
            response_text = response.text

            # Extract JSON from markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            # Clean and extract JSON
            response_text = response_text.strip()
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)

            # Remove comments
            response_text = re.sub(r'//.*', '', response_text)

            # Parse JSON
            result = json.loads(response_text)

            # Extract scores
            return AITaskSlotScore(
                task_id=task.id,
                slot_id=slot.slot_id,
                total_score=float(result.get('total_score', 0)),
                task_context_score=float(result.get('task_context_score', 0)),
                dependency_score=float(result.get('dependency_score', 0)),
                energy_score=float(result.get('energy_score', 0)),
                reasoning=result.get('reasoning', ''),
                model_used=self.model_name
            )

        except Exception as e:
            logger.error(f"[GEMINI-SCORER] Error scoring task {task.id} in slot {slot.slot_id}: {str(e)}")
            # Return neutral score on error
            return AITaskSlotScore(
                task_id=task.id,
                slot_id=slot.slot_id,
                total_score=16.5,  # Middle of 0-33 range
                task_context_score=6.0,
                dependency_score=5.5,
                energy_score=5.0,
                reasoning=f"Error during scoring: {str(e)}",
                model_used=self.model_name
            )

    async def score_batch(
        self,
        combinations: List[tuple],
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> List[AITaskSlotScore]:
        """
        Score multiple task-slot combinations in a SINGLE batch API call

        This is the key performance optimization - instead of 24 API calls,
        we make just 1 call scoring all combinations at once.

        Performance:
            - 24 combinations: 40s (gemini-2.5-flash) or 8.5s (gemini-2.5-flash-lite)
            - vs 90+ seconds for OpenAI

        Args:
            combinations: List of (task, slot) tuples
            calendar_context: Optional calendar events for context

        Returns:
            List of AITaskSlotScore objects
        """
        from datetime import datetime
        start_total = datetime.now()

        logger.info(f"[GEMINI-SCORER] Batch scoring {len(combinations)} combinations with {self.model_name}")
        print(f"   [BATCH] AI Scoring: {len(combinations)} combinations in one call...")

        try:
            # Build batch prompt
            start_prompt = datetime.now()
            prompt = self._build_batch_scoring_prompt(combinations, calendar_context)
            end_prompt = datetime.now()
            prompt_time = (end_prompt - start_prompt).total_seconds()
            print(f"   [TIMING] Prompt building: {prompt_time:.2f}s")

            # Single API call for all combinations
            print(f"   [API] Calling Gemini API ({self.model_name})...")
            start_api = datetime.now()
            response = self.model.generate_content(prompt)
            end_api = datetime.now()
            api_time = (end_api - start_api).total_seconds()
            print(f"   [TIMING] API call: {api_time:.2f}s")

            # Parse batch response
            print(f"   [PARSE] Parsing {len(combinations)} scores from response...")
            start_parse = datetime.now()

            response_text = response.text

            # Extract JSON from markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            # Clean JSON
            response_text = response_text.strip()
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            response_text = re.sub(r'//.*', '', response_text)

            # Parse JSON
            result = json.loads(response_text)
            scores_data = result.get("scores", [])

            # Convert to AITaskSlotScore objects
            scores = []
            for score_data in scores_data:
                scores.append(AITaskSlotScore(
                    task_id=score_data.get('task_id', ''),
                    slot_id=score_data.get('slot_id', ''),
                    total_score=float(score_data.get('total_score', 0)),
                    task_context_score=float(score_data.get('task_context_score', 0)),
                    dependency_score=float(score_data.get('dependency_score', 0)),
                    energy_score=float(score_data.get('energy_score', 0)),
                    reasoning=score_data.get('reasoning', ''),
                    model_used=self.model_name
                ))

            end_parse = datetime.now()
            parse_time = (end_parse - start_parse).total_seconds()
            print(f"   [TIMING] Response parsing: {parse_time:.2f}s")
            print(f"   [OK] Batch scoring complete! Scored {len(scores)} combinations in single call.")

            # Timing summary
            end_total = datetime.now()
            total_time = (end_total - start_total).total_seconds()

            print(f"\n   [TIMING SUMMARY]")
            print(f"   • Prompt building: {prompt_time:.2f}s ({prompt_time/total_time*100:.1f}%)")
            print(f"   • API call:        {api_time:.2f}s ({api_time/total_time*100:.1f}%)")
            print(f"   • Response parse:  {parse_time:.2f}s ({parse_time/total_time*100:.1f}%)")
            print(f"   • TOTAL:           {total_time:.2f}s")

            logger.info(
                f"[GEMINI-SCORER] Batch scored {len(scores)} combinations in {total_time:.2f}s "
                f"(avg: {total_time/len(scores):.2f}s per combination)"
            )

            return scores

        except Exception as e:
            logger.error(f"[GEMINI-SCORER] Batch scoring failed: {str(e)}")
            # Return neutral scores for all combinations
            return [
                AITaskSlotScore(
                    task_id=task.id,
                    slot_id=slot.slot_id,
                    total_score=16.5,
                    task_context_score=6.0,
                    dependency_score=5.5,
                    energy_score=5.0,
                    reasoning=f"Batch scoring error: {str(e)}",
                    model_used=self.model_name
                )
                for task, slot in combinations
            ]

    def _build_scoring_prompt(
        self,
        task: TaskToAnchor,
        slot: AvailableSlot,
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> str:
        """Build the prompt for scoring a single task-slot combination"""

        context_str = ""
        if calendar_context:
            context_str = "\n\nCalendar Context:\n"
            for event in calendar_context:
                context_str += f"- {event.title} at {event.start_time}\n"

        prompt = f"""Score how well this health task fits this time slot.

Task: {task.title}
Description: {task.description}
Duration: {task.estimated_duration_minutes} minutes
Category: {task.category}
Priority: {task.priority_level}

Time Slot:
Start: {slot.start_time.strftime('%I:%M %p')}
End: {slot.end_time.strftime('%I:%M %p')}
Duration: {slot.duration_minutes} minutes
{context_str}

Score these aspects (return JSON):
1. task_context_score (0-12): Does the task match this time of day?
2. dependency_score (0-11): Does this create good momentum/flow?
3. energy_score (0-10): Does energy level match task demands?

Return ONLY valid JSON:
{{
  "task_id": "{task.id}",
  "slot_id": "{slot.slot_id}",
  "total_score": <0-33>,
  "task_context_score": <0-12>,
  "dependency_score": <0-11>,
  "energy_score": <0-10>,
  "reasoning": "<brief explanation>"
}}"""

        return prompt

    def _build_batch_scoring_prompt(
        self,
        combinations: List[tuple],
        calendar_context: Optional[List[CalendarEvent]] = None
    ) -> str:
        """Build the prompt for scoring multiple task-slot combinations in one call"""

        prompt = f"""Score {len(combinations)} task-slot combinations and return results as a JSON array.

For EACH combination, score these aspects:
1. Task Context (0-12 points): Does the task match this time of day?
2. Dependency & Flow (0-11 points): Does this create good momentum?
3. Energy & Focus (0-10 points): Does energy level match demands?

Combinations:
"""

        for idx, (task, slot) in enumerate(combinations, 1):
            prompt += f"""
{idx}. Task: {task.title} ({task.estimated_duration_minutes}min)
   Slot: {slot.start_time.strftime('%I:%M %p')}-{slot.end_time.strftime('%I:%M %p')}
   task_id: "{task.id}", slot_id: "{slot.slot_id}"
"""

        prompt += f"""
Return ONLY valid JSON with this structure:
{{
  "scores": [
    {{
      "task_id": "<task_id>",
      "slot_id": "<slot_id>",
      "total_score": <0-33>,
      "task_context_score": <0-12>,
      "dependency_score": <0-11>,
      "energy_score": <0-10>,
      "reasoning": "<brief explanation>"
    }},
    ... (repeat for all {len(combinations)} combinations)
  ]
}}"""

        return prompt


# ============================================================================
# Singleton Instance
# ============================================================================

_gemini_scorer_instance: Optional[GeminiAIScorerService] = None


def get_gemini_scorer_service(model: str = "gemini-2.5-flash") -> GeminiAIScorerService:
    """
    Get singleton instance of GeminiAIScorerService

    Args:
        model: Gemini model to use
            - "gemini-2.5-flash" (recommended): 40s, good quality balance
            - "gemini-2.5-flash-lite" (fastest): 8.5s, acceptable quality

    Returns:
        GeminiAIScorerService instance
    """
    global _gemini_scorer_instance

    if _gemini_scorer_instance is None:
        _gemini_scorer_instance = GeminiAIScorerService(model=model)

    return _gemini_scorer_instance
