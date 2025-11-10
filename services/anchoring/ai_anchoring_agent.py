"""
AI-Only Anchoring Agent - Holistic Approach

This agent handles the entire anchoring process using AI reasoning
instead of algorithmic scoring + ILP optimization.

Key Features:
- Holistic decision-making (sees all tasks + slots at once)
- Semantic understanding of task descriptions
- Context-aware reasoning about calendar events
- Natural language explanations for decisions
- Output compatible with existing AssignmentResult format

Architecture:
    [Tasks + Slots + Context]
            ↓
    [AI Agent - GPT-4o]
        • Understands task semantics
        • Reasons about workflows
        • Considers user preferences
        • Makes assignment decisions
            ↓
    [AssignmentResult] (same format as greedy_assignment_service)
"""

import logging
import json
import re
from typing import List, Optional, Dict, Any
from datetime import time, datetime, timedelta, date
from dataclasses import dataclass

import google.generativeai as genai

from .basic_scorer_service import TaskToAnchor
from .calendar_gap_finder import AvailableSlot
from .calendar_integration_service import CalendarEvent
from .greedy_assignment_service import TaskAssignment, AssignmentResult

logger = logging.getLogger(__name__)


# ============================================================================
# AI Anchoring Agent
# ============================================================================

class AIAnchoringAgent:
    """
    AI-powered anchoring agent using Google Gemini Flash

    This agent replaces the traditional scorer + optimizer pipeline with
    end-to-end AI reasoning that considers all context holistically.

    Performance:
    - Gemini Flash:      2-3s, ~$0.005 per request
    - 2x faster than OpenAI GPT-4o
    - 2-4x cheaper than OpenAI

    Usage:
        agent = AIAnchoringAgent(model="gemini-2.0-flash-exp")
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.2
    ):
        """
        Initialize AI anchoring agent with Gemini

        Args:
            model: Gemini model name (default: gemini-2.0-flash-exp)
            api_key: Gemini API key (auto-detects from env if None)
            temperature: Lower = more deterministic (0.2 recommended)
        """
        import os
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment")

        genai.configure(api_key=api_key)
        self.model = model or "gemini-2.0-flash-exp"
        self.gemini_model = genai.GenerativeModel(self.model)
        self.temperature = temperature

        logger.info(f"[AI-ANCHORING] Initialized with Gemini: {self.model}")

    async def anchor_tasks(
        self,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        calendar_events: List[CalendarEvent],
        user_profile: Optional[Dict[str, Any]] = None,
        target_date: Optional[date] = None
    ) -> AssignmentResult:
        """
        Anchor tasks to slots using AI holistic reasoning

        Args:
            tasks: Tasks to anchor
            slots: Available time slots
            calendar_events: Full calendar context
            user_profile: User behavioral patterns, preferences, chronotype
            target_date: Target date for anchoring

        Returns:
            AssignmentResult (compatible with existing format)
        """
        logger.info(
            f"[AI-ANCHORING-AGENT] Starting holistic anchoring for "
            f"{len(tasks)} tasks across {len(slots)} gaps"
        )

        try:
            # Build comprehensive prompt with all context
            prompt = self._build_anchoring_prompt(
                tasks, slots, calendar_events, user_profile, target_date
            )

            # Call Gemini for holistic reasoning
            logger.info(f"[AI-ANCHORING] Calling Gemini {self.model} for anchoring decisions")

            ai_output = await self._call_gemini(prompt)

            logger.info(f"[AI-ANCHORING] Gemini response received, parsing assignments")

            # Validate and convert to AssignmentResult format
            result = self._convert_to_assignment_result(
                ai_output, tasks, slots, calendar_events
            )

            logger.info(
                f"[AI-ANCHORING-AGENT] ✅ Anchoring complete: "
                f"{result.tasks_anchored}/{result.total_tasks} tasks anchored, "
                f"confidence: {result.average_confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"[AI-ANCHORING-AGENT] Error during anchoring: {str(e)}")
            # Return fallback result (all tasks at original times)
            return self._create_fallback_result(tasks)

    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API and return parsed JSON"""
        # Combine system prompt and user prompt for Gemini
        full_prompt = f"{self._get_system_prompt()}\n\n{prompt}"

        # Call Gemini (synchronous API, but we're in async context)
        response = self.gemini_model.generate_content(full_prompt)
        response_text = response.text

        # Extract JSON from markdown code blocks if present
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

        return json.loads(response_text)

    def _get_system_prompt(self) -> str:
        """
        Get system prompt defining agent identity and capabilities
        """
        return """You are the HolisticOS Anchoring Agent, an expert at calendar optimization and task scheduling. You specialize in anchoring wellness tasks into users' busy schedules by deeply understanding context, preferences, and behavioral patterns.

Your expertise includes:
• Circadian rhythm and energy management
• Task semantics and cognitive load understanding
• Workflow optimization and task sequencing
• Stress patterns and mental state transitions
• Health behavior science (nutrition, exercise, recovery)
• Context-aware reasoning about calendar events

Your goal: Find the optimal placement for each task that:
1. Respects calendar constraints (no conflicts, capacity limits)
2. Honors user preferences stated in task descriptions
3. Creates natural workflows and routines
4. Maximizes user satisfaction and task adherence
5. Considers both immediate fit and long-term sustainability

Think step-by-step, reason about trade-offs, and provide clear explanations for your decisions.

CRITICAL CONSTRAINT RULES:
- Each task can be assigned to AT MOST ONE gap
- Gap capacity MUST NOT be exceeded (sum of task durations ≤ gap duration)
- High-priority tasks SHOULD be anchored (low priority can be unanchored if needed)
- Tasks can be placed sequentially within the same gap
- Unanchored tasks should keep their original time as fallback

Always output valid JSON matching the specified structure."""

    def _build_anchoring_prompt(
        self,
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        calendar_events: List[CalendarEvent],
        user_profile: Optional[Dict[str, Any]],
        target_date: Optional[date]
    ) -> str:
        """
        Build comprehensive prompt with all anchoring context
        """
        # Format user profile
        profile_section = ""
        if user_profile:
            chronotype = user_profile.get('chronotype', 'Unknown')
            peak_energy = user_profile.get('peak_energy_window', 'Unknown')
            patterns = user_profile.get('behavioral_patterns', {})

            profile_section = f"""
## User Profile
Chronotype: {chronotype}
Peak Energy Window: {peak_energy}
Behavioral Patterns:
- Focus work completion rate: {patterns.get('focus_completion_rate', 'N/A')}
- Exercise preference: {patterns.get('exercise_preference', 'Flexible')}
- Stress response: {patterns.get('stress_patterns', 'N/A')}
"""

        # Format target date
        date_section = ""
        if target_date:
            date_section = f"""
## Today's Context
Date: {target_date.strftime('%Y-%m-%d')}
Day of Week: {target_date.strftime('%A')}
"""

        # Format calendar events
        events_section = "## Calendar Events (Immovable)\n"
        if calendar_events:
            for idx, event in enumerate(calendar_events, 1):
                events_section += f"""
Event {idx}:
  - Title: "{event.title}"
  - Time: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')} ({event.duration_minutes} min)
  - Type: {getattr(event, 'event_type', 'meeting')}
"""
            events_section += f"\nTotal calendar events: {len(calendar_events)}\n"
        else:
            events_section += "No calendar events - full day available\n"

        # Format available gaps
        gaps_section = "## Available Time Gaps\n"
        total_available = 0
        for idx, slot in enumerate(slots, 1):
            total_available += slot.duration_minutes
            gaps_section += f"""
Gap {idx}:
  - ID: {slot.slot_id}
  - Time: {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')} ({slot.duration_minutes} min)
  - Position: {slot.gap_type.value}
  - Before Event: {slot.before_event_title or 'None'}
  - After Event: {slot.after_event_title or 'None'}
"""
        gaps_section += f"\nTotal gaps: {len(slots)}\nTotal available time: {total_available} minutes\n"

        # Format tasks
        tasks_section = "## Tasks to Anchor\n"
        total_duration = 0
        for idx, task in enumerate(tasks, 1):
            total_duration += task.estimated_duration_minutes
            tasks_section += f"""
Task {idx}:
  - ID: {task.id}
  - Title: "{task.title}"
  - Description: "{task.description or 'No description'}"
  - Category: {task.category}
  - Duration: {task.estimated_duration_minutes} minutes
  - Priority: {task.priority_level}
  - Preferred Time: {task.scheduled_time.strftime('%H:%M')}
  - Time Block: {task.time_block or 'Any'}
  - Energy Zone: {task.energy_zone_preference or 'Any'}
"""
        tasks_section += f"\nTotal tasks: {len(tasks)}\nTotal duration: {total_duration} minutes\n"

        # Build complete prompt
        prompt = f"""# ANCHORING REQUEST

{profile_section}
{date_section}
{events_section}
{gaps_section}
{tasks_section}

## Your Task

Analyze all tasks, gaps, and context holistically. For each task, decide:
1. Which gap to assign it to (or mark as unanchored)
2. Exact start time within that gap
3. Brief reasoning for this decision

Think through this step-by-step:

**STEP 1: ANALYZE CONTEXT**
- Identify high-stakes events that create stress/anxiety
- Map user's energy curve across the day
- Note explicit preferences in task descriptions
- Identify potential workflows (tasks that should be sequential)

**STEP 2: CONSIDER WORKFLOWS**
- Can tasks be grouped in same gap (morning routine, evening routine)?
- Do any tasks naturally follow others (workout → protein shake)?
- Are there synergies (meal prep before dinner time)?

**STEP 3: MAKE ASSIGNMENTS**
For each task, assign to optimal gap considering:
- Energy match (task demand vs time of day)
- Timing preference (user's stated preference)
- Context fit (events before/after this gap)
- Workflow optimization (creates good daily flow)
- Constraint satisfaction (fits in gap capacity)

**STEP 4: VALIDATE**
- Check no gap is over-capacity
- Verify high-priority tasks are anchored
- Ensure no overlaps within same gap

## Output Format (JSON)

Return ONLY valid JSON with this EXACT structure:

{{
  "assignments": [
    {{
      "task_id": "task_001",
      "gap_id": "gap_1",
      "start_time": "06:00",
      "end_time": "06:05",
      "confidence": 0.95,
      "reasoning": "Brief explanation why this gap is optimal..."
    }}
  ],
  "unanchored": [
    {{
      "task_id": "task_008",
      "reason": "No suitable gap - all slots at capacity"
    }}
  ],
  "insights": [
    "Created morning wellness routine with 3 sequential tasks",
    "Positioned focus work after coffee break for clarity"
  ]
}}

CRITICAL:
- Ensure gap capacities are not exceeded
- Each task appears ONCE (either in assignments or unanchored)
- All task_ids and gap_ids must match the input exactly
- Times must be in HH:MM format
"""

        return prompt

    def _convert_to_assignment_result(
        self,
        ai_output: Dict[str, Any],
        tasks: List[TaskToAnchor],
        slots: List[AvailableSlot],
        calendar_events: List[CalendarEvent]
    ) -> AssignmentResult:
        """
        Convert AI JSON output to AssignmentResult format

        This ensures backward compatibility with existing API
        """
        task_map = {task.id: task for task in tasks}
        slot_map = {slot.slot_id: slot for slot in slots}

        assignments = []
        assigned_task_ids = set()

        # Process AI assignments
        for assignment in ai_output.get('assignments', []):
            task_id = assignment['task_id']
            gap_id = assignment['gap_id']

            if task_id not in task_map or gap_id not in slot_map:
                logger.warning(f"[AI-ANCHORING-AGENT] Invalid task/gap ID: {task_id}/{gap_id}")
                continue

            task = task_map[task_id]
            slot = slot_map[gap_id]

            # Parse AI-provided times
            start_time_str = assignment['start_time']
            end_time_str = assignment['end_time']

            try:
                anchored_time = datetime.strptime(start_time_str, '%H:%M').time()
                anchored_end_time = datetime.strptime(end_time_str, '%H:%M').time()
            except:
                # Fallback: use task's scheduled time
                anchored_time = task.scheduled_time
                anchored_end_time = task.scheduled_end_time

            # Calculate time adjustment
            original_dt = datetime.combine(datetime.today(), task.scheduled_time)
            anchored_dt = datetime.combine(datetime.today(), anchored_time)
            time_diff = (anchored_dt - original_dt).total_seconds() / 60

            # Create TaskAssignment
            task_assignment = TaskAssignment(
                task_id=task.id,
                task_title=task.title,
                original_time=task.scheduled_time,
                original_end_time=task.scheduled_end_time,
                anchored_time=anchored_time,
                anchored_end_time=anchored_end_time,
                duration_minutes=task.estimated_duration_minutes,
                slot_id=gap_id,
                confidence_score=float(assignment.get('confidence', 0.9)),
                time_adjustment_minutes=int(time_diff),
                scoring_breakdown={
                    'algorithm_used': 'ai_holistic',
                    'model': self.model,
                    'reasoning': assignment.get('reasoning', ''),
                    'ai_confidence': assignment.get('confidence', 0.9)
                }
            )

            assignments.append(task_assignment)
            assigned_task_ids.add(task_id)

        # Handle unanchored tasks from AI
        unanchored_task_ids = []
        for unanchored in ai_output.get('unanchored', []):
            task_id = unanchored['task_id']
            if task_id in task_map and task_id not in assigned_task_ids:
                task = task_map[task_id]

                # Create fallback assignment at original time
                fallback = TaskAssignment(
                    task_id=task.id,
                    task_title=task.title,
                    original_time=task.scheduled_time,
                    original_end_time=task.scheduled_end_time,
                    anchored_time=task.scheduled_time,
                    anchored_end_time=task.scheduled_end_time,
                    duration_minutes=task.estimated_duration_minutes,
                    slot_id='unanchored',
                    confidence_score=0.3,
                    time_adjustment_minutes=0,
                    scoring_breakdown={
                        'algorithm_used': 'ai_holistic',
                        'unanchored_reason': unanchored.get('reason', 'AI could not find suitable gap')
                    }
                )

                assignments.append(fallback)
                unanchored_task_ids.append(task_id)
                assigned_task_ids.add(task_id)

        # Handle tasks AI missed (shouldn't happen, but safety check)
        for task in tasks:
            if task.id not in assigned_task_ids:
                logger.warning(f"[AI-ANCHORING-AGENT] AI missed task {task.id}, using fallback")
                fallback = TaskAssignment(
                    task_id=task.id,
                    task_title=task.title,
                    original_time=task.scheduled_time,
                    original_end_time=task.scheduled_end_time,
                    anchored_time=task.scheduled_time,
                    anchored_end_time=task.scheduled_end_time,
                    duration_minutes=task.estimated_duration_minutes,
                    slot_id='unanchored',
                    confidence_score=0.2,
                    time_adjustment_minutes=0,
                    scoring_breakdown={
                        'algorithm_used': 'ai_holistic',
                        'unanchored_reason': 'AI did not process this task'
                    }
                )
                assignments.append(fallback)
                unanchored_task_ids.append(task.id)

        # Calculate summary statistics
        tasks_rescheduled = sum(1 for a in assignments if a.time_adjustment_minutes != 0)
        tasks_kept_original = len(tasks) - tasks_rescheduled

        valid_assignments = [a for a in assignments if a.slot_id != 'unanchored']
        avg_confidence = (
            sum(a.confidence_score for a in valid_assignments) / len(valid_assignments)
            if valid_assignments else 0.0
        )

        return AssignmentResult(
            assignments=assignments,
            total_tasks=len(tasks),
            tasks_anchored=len(valid_assignments),
            tasks_rescheduled=tasks_rescheduled,
            tasks_kept_original_time=tasks_kept_original,
            average_confidence=avg_confidence,
            unassigned_tasks=unanchored_task_ids
        )

    def _create_fallback_result(self, tasks: List[TaskToAnchor]) -> AssignmentResult:
        """
        Create fallback result if AI fails

        All tasks keep original times
        """
        logger.warning("[AI-ANCHORING-AGENT] Creating fallback result (AI failed)")

        assignments = []
        for task in tasks:
            fallback = TaskAssignment(
                task_id=task.id,
                task_title=task.title,
                original_time=task.scheduled_time,
                original_end_time=task.scheduled_end_time,
                anchored_time=task.scheduled_time,
                anchored_end_time=task.scheduled_end_time,
                duration_minutes=task.estimated_duration_minutes,
                slot_id='fallback_error',
                confidence_score=0.5,
                time_adjustment_minutes=0,
                scoring_breakdown={
                    'algorithm_used': 'fallback',
                    'reason': 'AI agent error - kept original times'
                }
            )
            assignments.append(fallback)

        return AssignmentResult(
            assignments=assignments,
            total_tasks=len(tasks),
            tasks_anchored=0,
            tasks_rescheduled=0,
            tasks_kept_original_time=len(tasks),
            average_confidence=0.5,
            unassigned_tasks=[]
        )


# ============================================================================
# Singleton Instance
# ============================================================================

_ai_agent_instance: Optional[AIAnchoringAgent] = None


def get_ai_anchoring_agent(model: Optional[str] = None) -> AIAnchoringAgent:
    """
    Get singleton instance of AIAnchoringAgent (Gemini only)

    Args:
        model: Gemini model name (default: gemini-2.0-flash-exp)

    Returns:
        AIAnchoringAgent instance

    Example:
        # Use default Gemini model (recommended)
        agent = get_ai_anchoring_agent()

        # Use specific Gemini model
        agent = get_ai_anchoring_agent(model="gemini-2.0-flash-thinking-exp-01-21")
    """
    global _ai_agent_instance

    if _ai_agent_instance is None:
        _ai_agent_instance = AIAnchoringAgent(model=model)

    return _ai_agent_instance
