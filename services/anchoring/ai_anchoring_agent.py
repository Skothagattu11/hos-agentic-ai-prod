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
        Get system prompt defining agent identity and capabilities with SEMANTIC ANCHORING
        """
        return """You are the HolisticOS Semantic Anchoring Agent, an expert at intelligent calendar optimization with deep semantic understanding. You specialize in anchoring wellness tasks into users' busy schedules by understanding LOGICAL FIT, not just time availability.

Your expertise includes:
• Semantic task analysis (location, energy level, time window preferences)
• Circadian rhythm and energy state management
• Task-gap context matching (what makes logical sense to schedule where)
• Workflow optimization and task sequencing
• Health behavior science (nutrition, exercise, recovery)
• Context-aware reasoning about calendar events
• Conflict detection between task preferences and calendar

YOUR CORE PRINCIPLE - SEMANTIC ANCHORING:
🎯 ONLY anchor tasks to gaps where it makes LOGICAL SENSE, never force
   - Gym exercise ✓ can go in gap at gym location
   - Gym exercise ✗ CANNOT go in gap between office meetings
   - Office work ✓ fits in work blocks during business hours
   - Deep focus ✓ fits in 60+ min gap after user has rested
   - Deep focus ✗ CANNOT fit in 5 min break between meetings

Your goal: For each task, decide:
1. Does it conflict with user's calendar at preferred time?
2. If YES conflict: Is there a semantically suitable gap to reschedule it?
3. If NO suitable gap: Keep it STANDALONE (unanchored) - don't force it
4. If NO conflict: Keep it STANDALONE (already fits naturally)

SEMANTIC ANALYSIS RULES:

### TASK SEMANTICS (infer from description, category, duration, time_block)
Task Location:
- Gym/Exercise tasks → Location: 'gym' (require gym context)
- Office/Work/Focus tasks → Location: 'office' (require office/work context)
- Meal/Cooking tasks → Location: 'home' (require home context)
- Meditation/Rest tasks → Location: 'home' (require home/quiet context)
- Commute/Travel tasks → Location: 'transit'
- No explicit location → Location: 'flexible' (can adapt)

Task Energy Level:
- High-intensity (exercise, workout, intense focus) → Energy: 'high' (need fresh/rested user)
- Medium (work, meetings, meal prep) → Energy: 'medium' (flexible)
- Low-intensity (meditation, rest, light stretching, hydration) → Energy: 'low' (can do when tired)

Task Time Window:
- Morning tasks (6am-10am preferred) → Window: 'morning'
- Afternoon tasks (12pm-6pm preferred) → Window: 'afternoon'
- Evening tasks (6pm-10pm preferred) → Window: 'evening'
- Flexible (any time) → Window: 'anytime'

Task Duration:
- Extract from 'estimated_duration_minutes' field
- Tasks smaller than gap duration CAN fit
- Tasks LARGER than gap duration CANNOT fit (reject)

### GAP SEMANTICS (infer from surrounding calendar events)
Gap Location (infer from event titles before/after):
- Between/After 'gym' events → 'gym' location
- Between 'office' meetings → 'office' location
- After work hours at home → 'home' location
- Unknown context → 'flexible'

Gap Energy State (infer from previous event):
- After 'long meeting' (90+ min) or 'exercise' → User is 'tired'
- After 'break' or 'rest' → User is 'rested'
- After short events → User is 'focused'
- Early morning gap → User is 'fresh'

Gap Context Type:
- Very short gap (5-15 min) → 'break' (only for quick tasks)
- Medium gap (15-60 min) → 'work block' or 'transition'
- Large gap (60+ min) → 'work block' (good for focused work)

### SEMANTIC SCORING ALGORITHM
For each task-gap pair, score across 5 dimensions (0-100 scale, 70+ required):

1. Location Match (0-25 points):
   - Perfect match (gym→gym, office→office, home→home): 25 pts
   - Flexible task in any location: 15 pts
   - Mismatch (gym task in office context): 5 pts

2. Energy Alignment (0-20 points):
   - High-energy task when user is fresh: 20 pts
   - Low-energy task when user is tired: 20 pts
   - Medium task matches medium energy: 15 pts
   - High-energy task when tired: 5 pts

3. Time Window Fit (0-20 points):
   - Gap within preferred time window: 20 pts
   - Gap close to window (±2 hours): 10 pts
   - Gap far from window: 2 pts

4. Duration Fit (0-20 points):
   - Gap duration > task duration with buffer (5-15 min): 20 pts
   - Gap duration exactly equals task duration: 18 pts
   - Gap duration < task duration: 0 pts (REJECT - impossible)

5. Context Fit (0-15 points):
   - Task context matches gap context perfectly: 15 pts
   - Task flexible within gap context: 12 pts
   - Task context mismatched: 5 pts

FINAL DECISION:
- Total score 70+ → ANCHOR to this gap ✓
- Total score <70 → Keep STANDALONE (don't force) ✗

CRITICAL CONSTRAINT RULES:

⚠️ ANCHORING LIMITS (STRICT - NO EXCEPTIONS):
1. Maximum 2 tasks can be anchored to ANY single calendar event
2. Total duration of anchored tasks ≤ 15 minutes
   - Example: 10min + 5min = OK (total 15min)
   - Example: 10min + 10min = NOT OK (total 20min) → Keep second task STANDALONE
3. If gap is too small for task duration → Keep task STANDALONE
4. If gap already has 2 anchored tasks → ALL remaining tasks STANDALONE
5. If adding task would exceed 15 min total → Keep task STANDALONE

STANDALONE TASK HANDLING:
- Tasks kept STANDALONE must be scheduled at their ORIGINAL time from plan_items
- Do NOT move standalone tasks to different times
- Use original scheduled_time from the task definition
- Example: If task originally scheduled for 12:00 PM, keep it at 12:00 PM (don't move to 12:30 PM)

DECISION PROCESS FOR EACH TASK:
1. Check if semantically suitable gap exists
2. Check if gap has <2 anchored tasks AND total_duration + task_duration ≤ 15 min
3. If YES → ANCHOR to gap
4. If NO → KEEP STANDALONE at original scheduled_time

EXAMPLES:
✓ Calendar event "wakeup" (30 min):
  - Anchor "Morning Yoga" (10 min) → Total: 10 min ✓
  - Anchor "Hydration" (5 min) → Total: 15 min ✓
  - "Breakfast" (15 min) → Would exceed 15 min → STANDALONE at original time ✗

✗ Calendar event "gym" (60 min):
  - Anchor "Stretch" (10 min) → Total: 10 min ✓
  - Anchor "Cool-down" (10 min) → Total: 20 min ✗ (exceeds 15) → STANDALONE

Think step-by-step, analyze semantics carefully, and ENFORCE anchor limits strictly.

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
For each task, check ANCHORING LIMITS FIRST:
1. Count tasks already anchored to this gap
2. Sum their durations
3. If gap has <2 anchored tasks AND adding this task keeps total ≤ 15 min → ANCHOR
4. Otherwise → MARK AS UNANCHORED (STANDALONE)

If task is UNANCHORED (STANDALONE):
- Use task.scheduled_time (original time) from plan_items
- Do NOT modify the time - keep it exactly as originally scheduled
- Example: If task is originally scheduled for "12:00 PM", keep "12:00"

**STEP 4: VALIDATE**
- ✓ No gap has >2 anchored tasks
- ✓ No gap has total anchor duration >15 minutes
- ✓ Each unanchored task has original scheduled_time preserved
- ✓ Each task appears ONCE (either anchored or unanchored)

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
      "reasoning": "Anchored: Morning Yoga (10min) + Hydration (5min) = 15min total"
    }},
    {{
      "task_id": "task_008",
      "gap_id": null,
      "start_time": "12:00",
      "end_time": "12:15",
      "confidence": 0.3,
      "reasoning": "STANDALONE: Gap already has 2 anchored tasks (15min), would exceed limit"
    }}
  ],
  "unanchored": [
    {{
      "task_id": "task_005",
      "reason": "STANDALONE: Original time 15:00, no gap available that respects 15min anchor limit"
    }}
  ],
  "insights": [
    "Anchored 2 tasks to morning routine (total 15 min)",
    "3 tasks kept as standalone - will be scheduled at their original times"
  ]
}}

CRITICAL:
- Max 2 anchored tasks PER gap, max 15 min total
- ANCHORED task: has gap_id, anchored_time in gap
- UNANCHORED task: gap_id=null, start_time=original scheduled_time from plan_items
- Each task appears ONCE (either anchored or unanchored)
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

        # Process AI assignments (both anchored and unanchored in assignments array)
        for assignment in ai_output.get('assignments', []):
            task_id = assignment['task_id']
            gap_id = assignment.get('gap_id')  # Can be None for unanchored

            if task_id not in task_map:
                logger.warning(f"[AI-ANCHORING-AGENT] Invalid task ID: {task_id}")
                continue

            task = task_map[task_id]

            # Check if this is an anchored or unanchored task
            if gap_id is None or gap_id == 'null':
                # UNANCHORED (STANDALONE) - keep original time
                logger.info(f"[AI-ANCHORING-AGENT] Task '{task.title}' marked as STANDALONE - using original time {task.scheduled_time}")

                task_assignment = TaskAssignment(
                    task_id=task.id,
                    task_title=task.title,
                    original_time=task.scheduled_time,
                    original_end_time=task.scheduled_end_time,
                    anchored_time=task.scheduled_time,  # Keep original
                    anchored_end_time=task.scheduled_end_time,  # Keep original
                    duration_minutes=task.estimated_duration_minutes,
                    slot_id='unanchored',
                    confidence_score=float(assignment.get('confidence', 0.2)),
                    time_adjustment_minutes=0,  # No adjustment
                    scoring_breakdown={
                        'algorithm_used': 'ai_holistic_standalone',
                        'model': self.model,
                        'reasoning': assignment.get('reasoning', 'Kept as standalone'),
                        'ai_confidence': assignment.get('confidence', 0.2)
                    }
                )
                assignments.append(task_assignment)
                assigned_task_ids.add(task_id)
                continue

            # ANCHORED task
            if gap_id not in slot_map:
                logger.warning(f"[AI-ANCHORING-AGENT] Invalid gap ID: {gap_id}")
                continue

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

            # Create TaskAssignment for anchored task
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
                    'algorithm_used': 'ai_holistic_anchored',
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
