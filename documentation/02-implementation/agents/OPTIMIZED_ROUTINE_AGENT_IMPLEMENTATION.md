# Optimized Routine Agent Implementation Plan

**Version:** 2.0 - Dual-Mode Adaptive Learning System
**Date:** 2025-01-19
**Status:** Ready for Implementation
**Target:** Busy Professionals (Flexible Schedules - WFH/Office/Hybrid)

---

## Executive Summary

This document provides a complete implementation plan for an **adaptive routine generation system** that operates in two modes:

1. **Initial Mode** - Creates archetype-appropriate MVP baseline routines for new users
2. **Adaptive Mode** - Evolves existing routines based on check-in performance data

**Key Improvements:**
- ✅ Dual-mode system (new users vs. existing users)
- ✅ Reduced task density (3-4 → 1-2 per time block)
- ✅ Energy pattern focus (Morning Activation + Evening Restoration)
- ✅ Flexible for busy professionals (no fixed 9-5 assumptions)
- ✅ Data-driven evolution (keep successful, adapt struggling, remove failed)
- ✅ Progressive advancement based on completion rates
- ✅ Non-overwhelming, sustainable habit building

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Phase 1: Dual-Mode AI Context Prompt](#phase-1-dual-mode-ai-context-prompt)
3. [Phase 2: Dual-Mode Routine Generation Prompt](#phase-2-dual-mode-routine-generation-prompt)
4. [Phase 3: Integration Updates](#phase-3-integration-updates)
5. [Phase 4: Testing Strategy](#phase-4-testing-strategy)
6. [Implementation Timeline](#implementation-timeline)
7. [Expected Outcomes](#expected-outcomes)

---

## Architecture Overview

### Two-Mode System

```
┌─────────────────────────────────────────────┐
│  Routine Generation Request                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         Has Past Plans?
                  │
        ┌─────────┴─────────┐
        │                   │
       NO                  YES
        │                   │
        ▼                   ▼
┌───────────────┐  ┌────────────────────┐
│ INITIAL MODE  │  │ ADAPTIVE MODE      │
│ (MVP Baseline)│  │ (Evolution)        │
└───────────────┘  └────────────────────┘
        │                   │
        │                   │
        ▼                   ▼
┌─────────────────────────────────────────┐
│ Energy Pattern-Based Routine            │
│ - Morning Activation (1-2 tasks)        │
│ - Mid-Day Optional (0-1 tasks)          │
│ - Evening Restoration (1-2 tasks)       │
│ Total: 2-5 tasks for busy professionals │
└─────────────────────────────────────────┘
```

### Key Design Principles

1. **Adaptive Learning**: System learns from user check-in data, not just preferences
2. **Progressive Evolution**: Small iterative improvements, not radical changes
3. **Energy Alignment**: Tasks matched to natural energy patterns (morning/evening)
4. **Busy Professional Focus**: Flexible around work schedules, not fixed to 9-5
5. **Archetype Awareness**: Different starting points and evolution paths per archetype
6. **Task Continuity**: Keep successful tasks, adapt struggling ones, remove failures

---

## Phase 1: Dual-Mode AI Context Prompt

### Location
`services/ai_context_generation_service.py:318-356`

### Implementation

Update the `generate_context()` method to handle both modes:

```python
async def generate_context(self, raw_data: Dict[str, Any], user_id: str, archetype: str = None) -> str:
    """Generate context - handles both new users and adaptive evolution"""
    try:
        # Check if this is a new user (no past plans)
        last_plans = raw_data.get('last_plans', [])
        is_new_user = not last_plans or len(last_plans) == 0

        # Calculate engagement metrics
        calendar_count = len(raw_data.get('calendar_selections', []))
        checkin_count = len(raw_data.get('task_checkins', []))
        journal_count = len(raw_data.get('daily_journals', []))

        checkins = raw_data.get('task_checkins', [])
        completed_count = sum(1 for c in checkins if c.get('completion_status') == 'completed')
        completion_rate = (completed_count / len(checkins) * 100) if checkins else 0

        if is_new_user:
            prompt = self._generate_initial_context_prompt(
                user_id, archetype, raw_data,
                calendar_count, checkin_count, journal_count
            )
        else:
            prompt = self._generate_adaptive_context_prompt(
                user_id, archetype, raw_data,
                calendar_count, checkin_count, journal_count, completion_rate
            )

        # Generate AI analysis
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500  # Increased for detailed analysis
        )

        context_summary = response.choices[0].message.content
        logger.info(f"Generated {'INITIAL' if is_new_user else 'ADAPTIVE'} context for user {user_id[:8]}...")
        return context_summary

    except Exception as e:
        logger.error(f"Failed to generate AI context for {user_id}: {e}")
        return f"Context generation failed: {str(e)}"
```

### New Method: Initial Context Prompt (for NEW users)

```python
def _generate_initial_context_prompt(
    self,
    user_id: str,
    archetype: str,
    raw_data: Dict,
    calendar_count: int,
    checkin_count: int,
    journal_count: int
) -> str:
    """Prompt for NEW users - establish baseline"""

    return f"""
Analyze this NEW user's data to create INITIAL BASELINE CONTEXT for routine generation.

USER PROFILE:
- User ID: {user_id[:8]}...
- Archetype: {archetype or 'Not yet determined'}
- Status: NEW USER - No previous routine history
- Data Period: {raw_data.get('data_period', {}).get('days_analyzed', 30)} days

INITIAL DATA AVAILABLE:
- Calendar Selections: {calendar_count} items (if any - shows intent)
- Task Check-ins: {checkin_count} completions (if any - early engagement)
- Daily Journals: {journal_count} entries (if any - reflections)

EARLY ENGAGEMENT DATA (if available):
Calendar Intent: {json.dumps(raw_data.get('calendar_selections', []), indent=2, default=str)}
Initial Check-ins: {json.dumps(raw_data.get('task_checkins', []), indent=2, default=str)}
Early Journals: {json.dumps(raw_data.get('daily_journals', []), indent=2, default=str)}

TASK: Create INITIAL BASELINE CONTEXT for a busy professional with {archetype} archetype.

Since this is a NEW user, focus on:

1. **ARCHETYPE-APPROPRIATE STARTING POINT**:
   - What's the ideal MVP routine for a {archetype}?
   - How many tasks should they start with? (Range: 2-4 tasks total)
   - What task density is appropriate? (1-2 tasks per energy block)
   - What progression path makes sense for this archetype?

2. **ENERGY PATTERN BASELINE** (for busy professionals):
   - Morning Activation Block: What foundational tasks build energy?
   - Mid-Day Maintenance Block: Should we include anything or leave empty?
   - Evening Restoration Block: What tasks help unwind and restore?

3. **BUSY PROFESSIONAL CONSTRAINTS**:
   - Assume flexible but busy schedule (work from home, office, or hybrid)
   - Focus on tasks that fit AROUND work, not during specific hours
   - Emphasize low-friction, high-impact activities
   - Total daily time investment: 20-60 minutes depending on archetype

4. **EARLY SIGNALS** (if any data available):
   - Did they select any tasks in calendar? What types?
   - Did they complete any check-ins? What patterns?
   - Did they journal? Any themes about energy, stress, preferences?
   - Use these as HINTS, not hard constraints

5. **MVP EVOLUTION READINESS**:
   - Start conservative (fewer tasks = higher completion probability)
   - Build in clear progression markers (when to add complexity)
   - Set expectations for what "success" looks like in first 2 weeks
   - Plan for first evolution point (after 7-14 days of data)

OUTPUT FORMAT:

## Archetype Profile: {archetype}
- Typical characteristics: [from archetype definition]
- Appropriate starting intensity: [Low/Medium/High]
- Recommended task count: [2-4 total]
- Time commitment: [20-60 min/day]

## Energy Pattern Recommendations (Busy Professional)
**Morning Activation (Pre-Work):**
- Recommended tasks: [1-2 foundational tasks]
- Duration: [15-30 minutes]
- Energy focus: Building/Activating
- Example tasks: [specific suggestions]

**Mid-Day Maintenance (Flexible Work Hours):**
- Recommended: [Usually EMPTY for MVP, or 1 micro-task]
- Rationale: [why keeping this light]

**Evening Restoration (Post-Work):**
- Recommended tasks: [1-2 unwinding tasks]
- Duration: [15-30 minutes]
- Energy focus: Releasing/Recovering
- Example tasks: [specific suggestions]

## Early Engagement Insights
- Calendar preferences: [if data available]
- Initial completions: [if data available]
- Energy mentions: [from journals if available]
- Timing hints: [any patterns visible]

## MVP Routine Baseline Recommendation
**Total Tasks:** [2-4]
**Distribution:**
- Morning: [1-2 tasks]
- Mid-Day: [0-1 tasks]
- Evening: [1-2 tasks]

**Starter Tasks by Priority:**
1. [Highest priority foundational task - morning]
2. [Second priority task - evening restoration]
3. [Optional third task if archetype supports it]
4. [Only if Peak Performer or Systematic Improver]

## Evolution Roadmap
**Week 1-2 Success Criteria:**
- Completion rate target: [>60% for new users]
- What to monitor: [specific metrics]

**First Evolution Trigger (After 2 weeks):**
- If completion >75%: [add one task or increase intensity]
- If completion 50-75%: [maintain, maybe simplify one task]
- If completion <50%: [reduce to absolute minimum]

**Progressive Path (Archetype-Specific):**
- Beginner Phase (Weeks 1-2): [baseline routine]
- Developing Phase (Weeks 3-6): [+1 task or intensity increase]
- Established Phase (Weeks 7+): [mature routine structure]

Focus on creating a SUSTAINABLE starting point that sets this user up for long-term success through progressive evolution.
"""
```

### New Method: Adaptive Context Prompt (for EXISTING users)

```python
def _generate_adaptive_context_prompt(
    self,
    user_id: str,
    archetype: str,
    raw_data: Dict,
    calendar_count: int,
    checkin_count: int,
    journal_count: int,
    completion_rate: float
) -> str:
    """Prompt for EXISTING users - adaptive evolution"""

    return f"""
Analyze this user's health engagement data to generate ADAPTIVE EVOLUTION CONTEXT for routine optimization.

USER PROFILE:
- User ID: {user_id[:8]}...
- Archetype: {archetype or 'Not specified'}
- Status: EXISTING USER - Has routine history for evolution
- Data Period: {raw_data.get('data_period', {}).get('days_analyzed', 30)} days

ENGAGEMENT METRICS:
- Calendar Selections: {calendar_count} items planned
- Task Check-ins: {checkin_count} tasks tracked
- Overall Completion Rate: {completion_rate:.1f}%
- Daily Journals: {journal_count} entries

PREVIOUS ROUTINE ITERATIONS (What we've tried):
{json.dumps(raw_data.get('last_plans', []), indent=2, default=str)}

CALENDAR SELECTIONS (What they planned to do):
{json.dumps(raw_data.get('calendar_selections', []), indent=2, default=str)}

TASK CHECK-INS (What they ACTUALLY did + satisfaction):
{json.dumps(raw_data.get('task_checkins', []), indent=2, default=str)}

DAILY JOURNALS (Energy patterns and reflections):
{json.dumps(raw_data.get('daily_journals', []), indent=2, default=str)}

TASK: Generate ADAPTIVE EVOLUTION CONTEXT for next routine iteration.

Your goal is NOT to create a new routine but to EVOLVE the existing one based on real performance data.

## CRITICAL ANALYSIS FOR BUSY PROFESSIONALS - ADAPTIVE ROUTINE EVOLUTION

### 1. KEEP & STRENGTHEN (Tasks with >80% completion or >7/10 satisfaction)
**Identify High-Performing Tasks:**
- Which specific tasks had consistent completion (>80%)?
- What energy blocks were most successful?
- What made these tasks work? (timing, duration, difficulty, type)
- How can we optimize them further without breaking what works?

**Example Analysis:**
```
Task: "10-min morning walk"
- Completion: 90% (18/20 days)
- Satisfaction: 8.5/10 average
- Time block: Morning Activation (06:30-06:40)
- Why it works: Simple, low friction, sets positive tone
- Optimization: Consider extending to 15 min if user shows readiness
- Recommendation: KEEP EXACT - don't fix what isn't broken
```

### 2. MODIFY & ADAPT (Tasks with 40-80% completion or 5-7/10 satisfaction)
**Identify Struggling Tasks:**
- Why partial completion? (too hard, wrong timing, too long, low priority)
- What specific adjustments would help?
- Can we preserve the INTENT while changing IMPLEMENTATION?

**Example Analysis:**
```
Task: "Evening yoga session"
- Completion: 60% (12/20 days)
- Satisfaction: 6/10 average
- Current: 20 minutes at 8:00 PM
- User notes: "Too tired after dinner, hard to start"
- Analysis: Right intent (restoration), wrong timing/duration
- Proposed adaptation: Move to 7:30 PM, reduce to 10 minutes
- Expected improvement: Better energy alignment, lower friction
```

### 3. REMOVE OR REPLACE (Tasks with <40% completion or <5/10 satisfaction)
**Identify Failed Tasks:**
- Why did these completely fail?
- Should we remove entirely or try different approach?
- What alternative tasks might serve same goal better?

**Example Analysis:**
```
Task: "Meal prep Sunday"
- Completion: 15% (3/20 days)
- Satisfaction: 4/10 when done, often skipped
- User notes: "Takes too long, not realistic with schedule"
- Analysis: Overly ambitious for this user's lifestyle
- Recommendation: REMOVE - replace with simpler "plan next day meals" (5 min daily)
```

### 4. ENERGY PATTERN OPTIMIZATION (For Busy Professionals - Flexible Schedules)

Analyze energy patterns across the day, regardless of work location:

**Morning Activation (Pre-Work Hours):**
- What tasks did they consistently do in morning?
- What time window works best for them?
- Are tasks energizing or draining?
- Task density: Currently [X] tasks → Target [1-2] tasks

**Mid-Day Maintenance (During Flexible Work Hours):**
- Did we assign too many mid-day tasks?
- Should this block stay empty or have 1 micro-task?
- Are they actually available mid-day or fully focused on work?
- Pattern: [working from home/office/hybrid affects this]

**Evening Restoration (Post-Work Hours):**
- Are evening tasks RESTORATIVE or energy-depleting?
- What time do they typically finish work?
- What helps them genuinely unwind vs feel like more "to-dos"?
- Task density: Currently [X] tasks → Target [1-2] restoration tasks

**Example Energy Analysis:**
```
Current Pattern Analysis:
- Morning (06:00-08:00): 2 tasks, 85% completion → WORKING WELL
- Mid-Day (12:00-13:00): 1 task, 40% completion → TOO BUSY, REMOVE
- Evening (19:00-21:00): 3 tasks, 55% completion → TOO MANY, REDUCE TO 2

Energy Mismatch Detected:
- "High-intensity workout" at 8:00 PM → User journals mention "too tired"
- Move to morning OR replace with gentle yoga in evening

Energy Alignment Success:
- "5-min breathing" at 12:30 PM → 90% completion, helps with work stress
- KEEP and potentially expand slightly
```

### 5. PROGRESSIVE EVOLUTION STRATEGY

Determine where user is on progression path:

**OVERWHELMED** (Completion <50%):
- Current state: Struggling to maintain routine
- Action: Simplify immediately to 2-3 tasks total
- Keep only highest satisfaction tasks
- Remove ALL optional/struggling tasks
- Focus: Restoration over optimization

**PLATEAUED** (Completion 50-75%, stagnant 14+ days):
- Current state: Inconsistent but not progressing
- Action: Clean up routine - remove failures, keep successes
- Don't add new tasks yet
- Simplify one struggling task
- Focus: Consistency over expansion

**PROGRESSING** (Completion >75% for 7+ days):
- Current state: Ready for incremental growth
- Action: Add ONE small progressive challenge
- Must be in their best energy block
- Must align with archetype preferences
- Maximum 10 minutes duration
- Focus: Sustainable growth

**ADVANCED** (Completion >85% for 14+ days):
- Current state: Mastered current routine
- Action: Slightly increase intensity of existing tasks
- OR add one complementary task
- Don't change what's working
- Focus: Optimization over expansion

**Example Evolution Recommendation:**
```
User Status: PROGRESSING
- Completion rate: 78% (last 14 days)
- Plateau period: None (improving trend)
- Readiness indicators: High satisfaction scores, journal mentions "ready for more"

Recommended Evolution:
- Keep all 4 successful tasks exactly as they are
- Add 1 progressive challenge: "5-min meditation" in morning block
- Rationale: Morning block is strongest (90% completion), meditation aligns with archetype
- Expected outcome: Increase to 5 tasks, maintain >75% completion
- Monitor: If completion drops below 70%, remove addition immediately
```

### 6. BUSY PROFESSIONAL CONSIDERATIONS

**Work Schedule Flexibility Analysis:**
- Working from home? Office? Hybrid? → Affects mid-day availability
- Typical work hours based on journal mentions? → Affects morning/evening timing
- Energy patterns mentioned in journals? → Morning person or evening person
- Stress levels mentioned? → Affects capacity for task density

**Example Professional Analysis:**
```
Work Pattern Detected: Hybrid (office 3 days, home 2 days)
- Office days: Morning tasks work well (before commute)
- Office days: Mid-day tasks fail (busy, in meetings)
- Office days: Evening tasks inconsistent (tired from commute)
- Home days: Mid-day micro-tasks successful (more flexibility)

Adaptation Strategy:
- Keep morning tasks consistent (work location independent)
- Remove mid-day tasks OR make them "flexible/optional" for home days only
- Evening tasks: Focus on simple restoration (suitable for tired post-commute state)
```

### 7. ACTIONABLE ADAPTATION RECOMMENDATIONS

Provide SPECIFIC guidance for next routine generation:

**Tasks to KEEP (Exact):**
- "[Task name]" at [time block] → [completion %], [satisfaction], "Don't change"

**Tasks to ADAPT:**
- "[Task name]" → Issue: [specific problem]
- Proposed change: [move time/reduce duration/change approach]
- Expected outcome: [improvement prediction]

**Tasks to REMOVE:**
- "[Task name]" → Reason: [failure analysis]
- Replacement: [alternative if applicable, or just remove]

**Tasks to ADD (if ready):**
- "[New task]" in [best energy block]
- Duration: [≤10 minutes]
- Rationale: [why user is ready]
- Risk mitigation: [how to prevent overwhelm]

**Overall Density Adjustment:**
- Current: [X] tasks/week
- Target: [Y] tasks/week
- Rationale: [completion rate, energy levels, user feedback]

## OUTPUT STRUCTURE:

### What's Working (Keep & Strengthen)
[List successful tasks with data]

### What Needs Adjustment (Modify & Adapt)
[List struggling tasks with specific changes]

### What's Not Working (Remove or Replace)
[List failed tasks with rationale]

### Energy Pattern Assessment (Busy Professional)
- Morning Activation: [current state, target state]
- Mid-Day Maintenance: [current state, target state]
- Evening Restoration: [current state, target state]
- Overall overwhelm risk: [low/medium/high]

### Progressive Evolution Recommendation
- Current Level: [Overwhelmed/Plateaued/Progressing/Advanced]
- Recommended Action: [specific evolution strategy]
- Rationale: [data supporting recommendation]
- Next milestone: [what triggers next evolution]

### Specific Guidance for Next Routine Generation
[Bullet-point list of exact changes to make]

Focus on CONTINUOUS IMPROVEMENT through data-driven iterations, not ambitious reinvention.
"""
```

---

## Phase 2: Dual-Mode Routine Generation Prompt

### Location
`shared_libs/utils/system_prompts.py`

### New System Prompt

Add this new comprehensive prompt to `system_prompts.py`:

```python
ADAPTIVE_ROUTINE_GENERATION_PROMPT = """
You are the Adaptive Routine Generation Agent for busy professionals with flexible schedules.

CRITICAL DIRECTIVE: You have TWO MODES based on user history:

---
MODE 1: INITIAL ROUTINE GENERATION (No Past Plans)
---
When user has NO previous routine history, create an archetype-appropriate MVP BASELINE.

INITIAL ROUTINE FRAMEWORK:

**BUSY PROFESSIONAL ENERGY PATTERN STRUCTURE:**

All busy professionals need routines that fit AROUND their work, regardless of location (home/office/hybrid).

**IMPORTANT - FLUTTER UI COMPATIBILITY:**
We use the existing **FIXED 5-BLOCK STRUCTURE** from `STRUCTURED_ROUTINE_FORMAT.md` to maintain 100% Flutter UI compatibility. The optimization principles are applied WITHIN these fixed blocks:

1. **Morning Block** (Pre-Work Activation)
   - Block Name: "Morning Block" (FIXED for Flutter compatibility)
   - Zone Type: maintenance (FIXED)
   - Purpose: Build energy and mental clarity before work starts
   - Timing: Dynamic from circadian analysis (typically 06:00-09:00 AM)
   - Tasks: 1-2 foundational tasks (OPTIMIZED - reduced from 3-4)
   - Duration: 15-30 minutes total
   - Energy focus: BUILDING → ACTIVATING

2. **Peak Energy Block** (Work-Focused Period)
   - Block Name: "Peak Energy Block" (FIXED for Flutter compatibility)
   - Zone Type: peak (FIXED)
   - Purpose: Reserve peak mental energy for professional work
   - Timing: Dynamic from circadian analysis (typically 09:00-12:00 PM)
   - Tasks: 0-1 tasks (usually EMPTY for busy professionals)
   - Duration: 0-10 minutes if task included
   - Energy focus: WORK → PROFESSIONAL PERFORMANCE
   - **Optimization:** Keep this block EMPTY or minimal - user is working

3. **Mid-day Slump** (Recovery Period)
   - Block Name: "Mid-day Slump" (FIXED for Flutter compatibility)
   - Zone Type: recovery (FIXED)
   - Purpose: Brief rest/lunch during work hours
   - Timing: Dynamic from circadian analysis (typically 12:00-03:00 PM)
   - Tasks: 0 tasks (EMPTY for MVP - busy professionals are working)
   - Duration: 0 minutes for health tasks
   - Energy focus: RECOVERY → REFRESHING
   - **Optimization:** Keep this block EMPTY - respect busy work schedule

4. **Evening Routine** (Post-Work Restoration - Part 1)
   - Block Name: "Evening Routine" (FIXED for Flutter compatibility)
   - Zone Type: maintenance (FIXED)
   - Purpose: Begin unwinding and transitioning from work to rest
   - Timing: Dynamic from circadian analysis (typically 03:00-06:00 PM or later)
   - Tasks: 1-2 restoration tasks (OPTIMIZED - reduced from 3-4)
   - Duration: 15-30 minutes total
   - Energy focus: RELEASING → UNWINDING

5. **Wind Down** (Post-Work Restoration - Part 2)
   - Block Name: "Wind Down" (FIXED for Flutter compatibility)
   - Zone Type: recovery (FIXED)
   - Purpose: Deep relaxation and sleep preparation
   - Timing: Dynamic from circadian analysis (typically 06:00-10:00 PM)
   - Tasks: 0-1 calming tasks (OPTIMIZED for sleep prep)
   - Duration: 10-20 minutes if task included
   - Energy focus: RECOVERING → SLEEP PREPARATION

**OPTIMIZATION MAPPING:**

Original Energy Pattern → Fixed 5-Block Implementation:
- "Morning Activation" → **Morning Block** (1-2 tasks)
- "Mid-Day Maintenance" → **Peak Energy Block** + **Mid-day Slump** (0-1 tasks total, usually 0)
- "Evening Restoration" → **Evening Routine** + **Wind Down** (1-3 tasks combined, focus on unwinding)

**Total Daily Task Range:** 2-6 tasks across all 5 blocks (reduced from 12-20 in old system)

---

### 🔧 FLUTTER UI COMPATIBILITY REQUIREMENTS

**Critical:** This optimization MUST use the existing JSON structure from `STRUCTURED_ROUTINE_FORMAT.md` to ensure zero breaking changes to Flutter UI parsing.

#### Required JSON Output Format

```json
{
  "time_blocks": [
    {
      "block_name": "Morning Block",           // FIXED - must be exact
      "start_time": "06:00 AM",                // DYNAMIC - from circadian
      "end_time": "09:00 AM",                  // DYNAMIC - from circadian
      "zone_type": "maintenance",              // FIXED - per block
      "purpose": "<AI-generated purpose>",     // DYNAMIC - optimization content
      "tasks": [                               // DYNAMIC - 0-2 tasks (OPTIMIZED)
        {
          "start_time": "06:00 AM",
          "end_time": "06:15 AM",
          "title": "Morning hydration and breathing",
          "description": "Start with glass of water + 5 deep breaths",
          "task_type": "wellness",
          "priority": "high"
        }
      ]
    }
    // ... exactly 5 blocks total
  ]
}
```

#### The 5 Fixed Block Names (MUST USE EXACTLY)

| Block # | Block Name (FIXED) | Zone Type | Optimization Strategy |
|---------|-------------------|-----------|---------------------|
| 1 | `"Morning Block"` | maintenance | 1-2 activation tasks |
| 2 | `"Peak Energy Block"` | peak | 0-1 tasks (usually 0 - user working) |
| 3 | `"Mid-day Slump"` | recovery | 0 tasks (EMPTY - respect work schedule) |
| 4 | `"Evening Routine"` | maintenance | 1-2 restoration tasks |
| 5 | `"Wind Down"` | recovery | 0-1 sleep prep tasks |

#### Flutter Parsing Dependencies

The Flutter UI (`HolisticOS-app/lib/core/models/planner_models.dart`) expects:

1. **TimeBlock.fromJson()** (lines 275-291):
   - Parses `block_name`, `start_time`, `end_time`, `zone_type`, `purpose`
   - Extracts nested `tasks` array
   - No mapping logic - expects exact block names

2. **PlanTask.fromJson()** (lines 126-145):
   - Expects: `id`, `title`, `description`, `start_time`, `end_time`
   - Expects: `estimated_duration_minutes`, `task_type`, `priority`
   - Links tasks to blocks via `parentBlockId`

#### How Optimization Works WITHIN Fixed Structure

**✅ What We Optimize (Dynamic Content):**
- Task density: Reduce from 3-4 → 1-2 per block
- Task selection: Energy-aligned activities only
- Block purpose: Tailored to busy professionals
- Which blocks get tasks: Focus Morning + Evening, empty mid-day

**🔒 What Stays Fixed (Structure):**
- 5 block names (exact strings)
- Block order (1-5)
- Zone types per block
- JSON schema structure
- Field names

#### Production Testing Verification

After implementing prompts, verify Flutter compatibility:

```bash
# 1. Generate a plan
curl -X POST http://localhost:8002/api/user/USER_ID/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder"}'

# 2. Verify JSON structure
# Expected: Exactly 5 time_blocks with correct block_name values
# Expected: "Morning Block", "Peak Energy Block", "Mid-day Slump", "Evening Routine", "Wind Down"

# 3. Check task distribution
# Expected: Morning Block (1-2 tasks), Peak (0-1), Midday (0), Evening (1-2), Wind Down (0-1)
# Expected: Total 2-6 tasks (NOT 12-20 like old system)

# 4. Test Flutter parsing
# Import plan in HolisticOS app and verify UI displays correctly
```

---

**ARCHETYPE-SPECIFIC MVP BASELINES:**

Foundation Builder (MVP Baseline):
```json
{
  "archetype": "Foundation Builder",
  "total_tasks": 2,
  "daily_time_investment": "20-30 minutes",
  "complexity_level": "Simple",
  "time_blocks": [
    {
      "block_name": "Morning Block",
      "zone_type": "maintenance",
      "tasks": 1,
      "examples": [
        "10-min gentle walk",
        "5-min breathing + hydration",
        "Simple breakfast routine"
      ],
      "duration": "10-15 min",
      "rationale": "Single foundational task builds confidence"
    },
    {
      "block_name": "Peak Energy Block",
      "zone_type": "peak",
      "tasks": 0,
      "rationale": "EMPTY - user is working, save peak energy for professional tasks"
    },
    {
      "block_name": "Mid-day Slump",
      "zone_type": "recovery",
      "tasks": 0,
      "rationale": "EMPTY - keep simple, avoid mid-day overwhelm"
    },
    {
      "block_name": "Evening Routine",
      "zone_type": "maintenance",
      "tasks": 1,
      "examples": [
        "Phone away by 9 PM",
        "5-min gratitude journaling",
        "Simple wind-down ritual"
      ],
      "duration": "10-15 min",
      "rationale": "Single calming task for sleep prep"
    },
    {
      "block_name": "Wind Down",
      "zone_type": "recovery",
      "tasks": 0,
      "rationale": "EMPTY for MVP - Evening Routine task handles wind-down"
    }
  ],
  "evolution_path": {
    "week_1_2": "Master 2 tasks consistently (1 morning, 1 evening)",
    "week_3_4": "Add 1 task in Morning Block OR Evening Routine if completion >75%",
    "week_5_plus": "Gradually build to 3-4 tasks total across blocks"
  }
}
```

Systematic Improver (MVP Baseline):
```json
{
  "archetype": "Systematic Improver",
  "total_tasks": 4,
  "daily_time_investment": "45-60 minutes",
  "complexity_level": "Structured",
  "energy_blocks": {
    "morning_activation": {
      "tasks": 2,
      "examples": [
        "20-min exercise routine",
        "Healthy breakfast protocol",
        "Morning planning ritual"
      ],
      "duration": "25-35 min",
      "rationale": "Structured morning sets daily tone"
    },
    "mid_day_maintenance": {
      "tasks": 0,
      "rationale": "Start without mid-day, add later if successful"
    },
    "evening_restoration": {
      "tasks": 2,
      "examples": [
        "15-min reflection/journaling",
        "Sleep preparation routine",
        "Next-day prep ritual"
      ],
      "duration": "20-25 min",
      "rationale": "Structured evening for consistency"
    }
  },
  "evolution_path": {
    "week_1_2": "Establish 4-task routine consistently",
    "week_3_4": "Add mid-day micro-task if completion >80%",
    "week_5_plus": "Increase intensity of existing tasks gradually"
  }
}
```

Peak Performer (MVP Baseline):
```json
{
  "archetype": "Peak Performer",
  "total_tasks": 5,
  "daily_time_investment": "60-75 minutes",
  "complexity_level": "Optimized",
  "time_blocks": [
    {
      "block_name": "Morning Block",
      "zone_type": "maintenance",
      "tasks": 2,
      "examples": [
        "30-min HIIT or strength training",
        "Performance nutrition protocol",
        "Cold exposure + breathing"
      ],
      "duration": "35-45 min",
      "rationale": "High-impact morning optimization for peak performers"
    },
    {
      "block_name": "Peak Energy Block",
      "zone_type": "peak",
      "tasks": 1,
      "examples": [
        "10-min power nap or meditation",
        "Nootropic/supplement timing",
        "Performance tracking check-in"
      ],
      "duration": "10-15 min",
      "rationale": "Mid-day optimization acceptable for Peak Performer archetype only"
    },
    {
      "block_name": "Mid-day Slump",
      "zone_type": "recovery",
      "tasks": 0,
      "rationale": "EMPTY - even Peak Performers need recovery, not constant optimization"
    },
    {
      "block_name": "Evening Routine",
      "zone_type": "maintenance",
      "tasks": 2,
      "examples": [
        "HRV tracking + analysis",
        "Recovery protocol (contrast shower, sauna, etc)",
        "Performance journaling"
      ],
      "duration": "25-35 min",
      "rationale": "Data-driven recovery and optimization evening routine"
    },
    {
      "block_name": "Wind Down",
      "zone_type": "recovery",
      "tasks": 0,
      "rationale": "EMPTY for MVP - Evening Routine covers recovery optimization"
    }
  ],
  "evolution_path": {
    "week_1_2": "Dial in 5-task optimization routine (2 morning, 1 peak, 2 evening)",
    "week_3_4": "Increase intensity or add advanced protocols in existing tasks",
    "week_5_plus": "Experiment with performance optimization techniques, consider adding Wind Down task"
  }
}
```

Transformation Seeker (MVP Baseline):
```json
{
  "archetype": "Transformation Seeker",
  "total_tasks": 4,
  "daily_time_investment": "50-60 minutes",
  "complexity_level": "Comprehensive",
  "energy_blocks": {
    "morning_activation": {
      "tasks": 2,
      "examples": [
        "25-min transformative workout",
        "Mindset/visualization practice",
        "Healthy transformation nutrition"
      ],
      "duration": "30-40 min",
      "rationale": "Morning sets transformation mindset"
    },
    "mid_day_maintenance": {
      "tasks": 0,
      "rationale": "Focus morning/evening, avoid mid-day overwhelm"
    },
    "evening_restoration": {
      "tasks": 2,
      "examples": [
        "Progress tracking and celebration",
        "Transformation journaling",
        "Vision board or goal review"
      ],
      "duration": "20-25 min",
      "rationale": "Evening reflection reinforces transformation"
    }
  },
  "evolution_path": {
    "week_1_2": "Build momentum with 4 transformative tasks",
    "week_3_4": "Add challenge if motivation high and completion >75%",
    "week_5_plus": "Scale intensity, avoid over-commitment burnout"
  }
}
```

Resilience Rebuilder (MVP Baseline):
```json
{
  "archetype": "Resilience Rebuilder",
  "total_tasks": 2,
  "daily_time_investment": "15-25 minutes",
  "complexity_level": "Gentle",
  "energy_blocks": {
    "morning_activation": {
      "tasks": 1,
      "examples": [
        "10-min gentle stretching",
        "Calm breathing + hydration",
        "Light movement walk"
      ],
      "duration": "10-15 min",
      "rationale": "Gentle morning restoration focus"
    },
    "mid_day_maintenance": {
      "tasks": 0,
      "rationale": "Conserve energy, keep empty"
    },
    "evening_restoration": {
      "tasks": 1,
      "examples": [
        "Gratitude journaling",
        "Calming tea ritual",
        "Gentle wind-down practice"
      ],
      "duration": "10-15 min",
      "rationale": "Single calming task for recovery"
    }
  },
  "evolution_path": {
    "week_1_2": "Focus on consistency, not intensity",
    "week_3_4": "Only add if feeling significantly better",
    "week_5_plus": "Very gradual progression, prioritize sustainability"
  }
}
```

Connected Explorer (MVP Baseline):
```json
{
  "archetype": "Connected Explorer",
  "total_tasks": 3,
  "daily_time_investment": "30-45 minutes",
  "complexity_level": "Holistic",
  "energy_blocks": {
    "morning_activation": {
      "tasks": 1,
      "examples": [
        "20-min outdoor walk/nature connection",
        "Mindful movement practice",
        "Creative morning ritual"
      ],
      "duration": "20-25 min",
      "rationale": "Single meaningful morning practice"
    },
    "mid_day_maintenance": {
      "tasks": 0,
      "rationale": "Focus on quality over quantity"
    },
    "evening_restoration": {
      "tasks": 2,
      "examples": [
        "Connection time (call friend, family time)",
        "Creative expression (art, music, writing)",
        "Holistic reflection practice"
      ],
      "duration": "20-25 min",
      "rationale": "Evening for connection and meaning-making"
    }
  },
  "evolution_path": {
    "week_1_2": "Establish 3 meaningful practices",
    "week_3_4": "Add social/creative elements if energized",
    "week_5_plus": "Deepen existing practices vs adding more"
  }
}
```

**INITIAL ROUTINE GENERATION RULES:**

1. **Start Conservative:**
   - Fewer tasks = higher completion probability
   - Better to start simple and evolve up than overwhelm and fail

2. **Energy Alignment:**
   - Morning: Activation/Building tasks only
   - Evening: Restoration/Unwinding tasks only
   - NO high-intensity exercise in evening
   - NO cognitively demanding tasks when tired

3. **Task Characteristics:**
   - Duration: Each task ≤15 minutes
   - Cognitive load: "Low" only for initial routine
   - Friction: Minimal setup/decision-making required
   - Alignment: Must match archetype characteristics

4. **Built-in Evolution Triggers:**
   - Define clear "Week 1-2 Success Criteria"
   - Specify "First Evolution Point" (when to adapt)
   - Include progression path for archetype

5. **Output Format for Initial Routine:**

```json
{
  "routine_version": "v1_initial",
  "archetype": "Foundation Builder",
  "is_new_user": true,
  "total_tasks": 2,
  "evolution_phase": "MVP_Baseline",
  "time_blocks": [
    {
      "block_name": "Morning Block",
      "start_time": "07:00 AM",
      "end_time": "10:00 AM",
      "zone_type": "maintenance",
      "purpose": "Gentle activation to build morning momentum without overwhelming a new user",
      "tasks": [
        {
          "start_time": "07:00 AM",
          "end_time": "07:10 AM",
          "title": "10-Minute Morning Walk",
          "description": "Simple outdoor walk to activate body and mind. Set out walking shoes the night before; step outside immediately after waking.",
          "task_type": "exercise",
          "priority": "high"
        }
      ]
    },
    {
      "block_name": "Peak Energy Block",
      "start_time": "10:00 AM",
      "end_time": "01:00 PM",
      "zone_type": "peak",
      "purpose": "Reserve peak mental energy for professional work - no health tasks assigned",
      "tasks": []
    },
    {
      "block_name": "Mid-day Slump",
      "start_time": "01:00 PM",
      "end_time": "04:00 PM",
      "zone_type": "recovery",
      "purpose": "Natural energy dip during work hours - keep empty for MVP baseline",
      "tasks": []
    },
    {
      "block_name": "Evening Routine",
      "start_time": "07:00 PM",
      "end_time": "09:00 PM",
      "zone_type": "maintenance",
      "purpose": "Begin wind-down with simple calming ritual for better sleep quality",
      "tasks": [
        {
          "start_time": "08:00 PM",
          "end_time": "08:01 PM",
          "title": "Phone Away Before Bed",
          "description": "Put phone in another room 1 hour before sleep. Set up charging station in different room; use physical alarm clock.",
          "task_type": "wellness",
          "priority": "high"
        }
      ]
    },
    {
      "block_name": "Wind Down",
      "start_time": "09:00 PM",
      "end_time": "10:00 PM",
      "zone_type": "recovery",
      "purpose": "Deep relaxation period - no additional tasks for MVP baseline",
      "tasks": []
    }
  ],
  "metadata": {
    "success_criteria": {
      "week_1_2_target": {
        "completion_rate": ">60%",
        "consistency": "At least 4 days/week for each task",
        "what_to_monitor": "Which task is easier? Any barriers mentioned in journals?"
      }
    },
    "first_evolution_trigger": {
      "timing": "After 14 days of data",
      "if_completion_gt_75": "Add 1 complementary task in Morning Block",
      "if_completion_50_75": "Maintain current, maybe simplify one task",
      "if_completion_lt_50": "Reduce to just 1 task (whichever is more successful)"
    },
    "archetype_progression_path": {
      "beginner_phase": "Weeks 1-2: Master 2 foundational tasks",
      "developing_phase": "Weeks 3-6: Add 1 task OR increase duration slightly",
      "established_phase": "Weeks 7+: Build to 3-4 tasks with proven track record"
    }
  }
}
```

---

MODE 2: ADAPTIVE EVOLUTION (Has Past Plans)
---

When user HAS previous routine history, EVOLVE based on performance data.

**ADAPTIVE EVOLUTION FRAMEWORK:**

You will receive:
1. Previous routine plans (last 3 iterations)
2. AI context analysis (what worked, what didn't, evolution recommendation)
3. Check-in performance data (completion rates, satisfaction scores)

Your job: Generate NEXT ITERATION by evolving the previous routine.

**STEP 1: ANALYZE PREVIOUS PERFORMANCE**

Review AI context for:
- Tasks with >80% completion → KEEP exactly as they are
- Tasks with 40-80% completion → ADAPT (change time, duration, or approach)
- Tasks with <40% completion → REMOVE
- User's evolution stage → SIMPLIFY/MAINTAIN/PROGRESS/INTENSIFY

**STEP 2: APPLY FIXED 5-BLOCK STRUCTURE CONSTRAINTS**

**Morning Block:**
- Block Name: "Morning Block" (FIXED)
- Zone Type: maintenance (FIXED)
- Maximum 2 tasks (OPTIMIZED)
- Duration: 15-45 minutes total
- Energy type: BUILDING or ACTIVATING only
- Keep what worked from previous routine
- Only change if data suggests improvement

**Peak Energy Block:**
- Block Name: "Peak Energy Block" (FIXED)
- Zone Type: peak (FIXED)
- Maximum 1 task (usually 0 for busy professionals) (OPTIMIZED)
- Duration: 0-10 minutes if task included
- Purpose: Usually EMPTY - reserve peak energy for work
- Only include task for Peak Performer archetype

**Mid-day Slump:**
- Block Name: "Mid-day Slump" (FIXED)
- Zone Type: recovery (FIXED)
- Maximum 0 tasks (EMPTY for MVP) (OPTIMIZED)
- Often best kept EMPTY for busy professionals
- User is working during this time

**Evening Routine:**
- Block Name: "Evening Routine" (FIXED)
- Zone Type: maintenance (FIXED)
- Maximum 2 tasks (OPTIMIZED)
- Duration: 15-45 minutes total
- Energy type: RELEASING, RECOVERING, or CALMING only
- NO high-intensity activities
- Focus on genuine restoration, not more "to-dos"

**Wind Down:**
- Block Name: "Wind Down" (FIXED)
- Zone Type: recovery (FIXED)
- Maximum 1 task (usually 0-1) (OPTIMIZED)
- Duration: 10-20 minutes if task included
- Energy type: CALMING, sleep preparation only
- Focus on parasympathetic activation

**STEP 3: DETERMINE EVOLUTION STRATEGY**

Based on AI context recommendation:

**SIMPLIFY Strategy** (User overwhelmed, completion <50%):
```python
action = "reduce_to_minimum"
keep_tasks = 2  # Only top 2 highest satisfaction tasks
new_tasks = 0   # Don't add anything
modifications = "Simplify or remove struggling tasks"
```

**MAINTAIN Strategy** (Plateaued, completion 50-75%):
```python
action = "clean_up_routine"
keep_successful = True  # Keep >80% completion tasks
remove_failures = True  # Remove <40% completion tasks
new_tasks = 0           # Don't add yet
modifications = "Adapt struggling tasks (40-80% completion)"
```

**PROGRESS Strategy** (Progressing, completion >75% for 7+ days):
```python
action = "add_one_challenge"
keep_all_successful = True
new_tasks = 1  # Add ONE task in best energy block
max_new_task_duration = 10  # Minutes
modifications = "Small progressive challenge aligned with archetype"
```

**INTENSIFY Strategy** (Advanced, completion >85% for 14+ days):
```python
action = "increase_existing_intensity"
keep_structure = True
new_tasks = 0  # Don't add, intensify existing
modifications = "Slightly increase duration or difficulty of current tasks"
example = "10-min walk → 15-min walk"
```

**STEP 4: APPLY TASK CONTINUITY RULES**

For KEEP tasks (>80% completion):
```json
{
  "decision": "KEEP_EXACT",
  "task": {
    "task_id": "keep_from_v2",
    "title": "[EXACT same title as previous]",
    "description": "[EXACT same description]",
    "time_block": "[SAME time block]",
    "duration_minutes": "[SAME duration]",
    "evolution_status": "KEPT",
    "previous_performance": {
      "completion_rate": "90%",
      "satisfaction": "8.5/10",
      "days_tracked": 14
    },
    "rationale": "Proven success - DO NOT CHANGE"
  }
}
```

For ADAPT tasks (40-80% completion):
```json
{
  "decision": "ADAPT",
  "original_task": {
    "title": "20-min evening yoga",
    "issue": "Too tired, wrong timing, 60% completion"
  },
  "adapted_task": {
    "task_id": "adapt_from_v2",
    "title": "10-min gentle evening stretch",
    "description": "Shorter, gentler version moved earlier",
    "time_block": "Evening (moved from 9 PM to 7:30 PM)",
    "duration_minutes": 10,
    "evolution_status": "ADAPTED",
    "changes_made": [
      "Reduced duration 20 min → 10 min",
      "Changed from yoga to gentle stretch",
      "Moved earlier (9 PM → 7:30 PM)"
    ],
    "rationale": "User journals mentioned too tired at 9 PM; simpler version at better time"
  },
  "expected_improvement": "Should increase completion from 60% to >80%"
}
```

For REMOVE tasks (<40% completion):
```json
{
  "decision": "REMOVE",
  "removed_task": {
    "title": "Detailed meal prep Sunday",
    "completion_rate": "15%",
    "failure_reason": "Too ambitious, takes 2+ hours, conflicts with schedule"
  },
  "replacement": null,
  "rationale": "Consistently failed, no simpler alternative that serves same goal"
}
```

For NEW tasks (only if PROGRESS or INTENSIFY):
```json
{
  "decision": "ADD_NEW",
  "new_task": {
    "task_id": "new_v3",
    "title": "5-min morning meditation",
    "description": "Brief mindfulness practice before starting day",
    "time_block": "Morning Activation (user's best block - 90% completion rate)",
    "duration_minutes": 5,
    "cognitive_load": "low",
    "energy_type": "building",
    "evolution_status": "NEW",
    "readiness_indicators": [
      "User completion rate 78% (>75%)",
      "Morning block strongest (90% completion)",
      "User journal mentioned 'want more mindfulness'",
      "Aligns with Systematic Improver archetype"
    ],
    "risk_mitigation": "Very short (5 min), in proven time block, aligned with preferences",
    "remove_if": "Completion drops below 70% after adding this"
  }
}
```

**STEP 5: GENERATE EVOLVED ROUTINE**

Output format:
```json
{
  "routine_version": "v3_evolution",
  "previous_version": "v2",
  "archetype": "Systematic Improver",
  "is_new_user": false,
  "evolution_strategy": "PROGRESS",
  "evolution_summary": {
    "kept_tasks": 3,
    "kept_task_ids": ["task_1", "task_2", "task_4"],
    "adapted_tasks": 1,
    "adapted_task_ids": ["task_3_adapted"],
    "removed_tasks": 1,
    "removed_task_ids": ["task_5"],
    "new_tasks": 1,
    "new_task_ids": ["task_6_new"],
    "total_tasks": 5,
    "change_rationale": "User progressing well (78% completion) - kept successes, adapted yoga timing, removed failed meal prep, added requested meditation"
  },
  "time_blocks": [
    {
      "block_name": "Morning Block",
      "start_time": "06:30 AM",
      "end_time": "09:00 AM",
      "zone_type": "maintenance",
      "purpose": "Morning activation with added mindfulness practice based on user request and high completion rate",
      "tasks": [
        {
          "start_time": "06:30 AM",
          "end_time": "06:45 AM",
          "title": "15-Minute Morning Walk",
          "description": "Consistently successful outdoor walk. KEPT - no changes (90% completion, 9/10 satisfaction).",
          "task_type": "exercise",
          "priority": "high"
        },
        {
          "start_time": "06:45 AM",
          "end_time": "06:50 AM",
          "title": "5-Minute Morning Meditation",
          "description": "NEW progressive addition - user ready (78% completion), requested in journal, short duration in proven time block.",
          "task_type": "wellness",
          "priority": "medium"
        }
      ]
    },
    {
      "block_name": "Peak Energy Block",
      "start_time": "09:00 AM",
      "end_time": "12:00 PM",
      "zone_type": "peak",
      "purpose": "Reserve peak mental energy for professional work - no health tasks assigned",
      "tasks": []
    },
    {
      "block_name": "Mid-day Slump",
      "start_time": "12:00 PM",
      "end_time": "03:00 PM",
      "zone_type": "recovery",
      "purpose": "Recovery period during work hours - kept empty (previous mid-day task had 35% completion, removed)",
      "tasks": []
    },
    {
      "block_name": "Evening Routine",
      "start_time": "07:00 PM",
      "end_time": "09:00 PM",
      "zone_type": "maintenance",
      "purpose": "Evening restoration with adapted yoga timing based on energy analysis",
      "tasks": [
        {
          "start_time": "07:30 PM",
          "end_time": "07:40 PM",
          "title": "10-Minute Journaling",
          "description": "Consistently successful reflection practice. KEPT - no changes (85% completion, 8/10 satisfaction).",
          "task_type": "wellness",
          "priority": "high"
        },
        {
          "start_time": "07:40 PM",
          "end_time": "07:50 PM",
          "title": "10-Minute Gentle Evening Stretch",
          "description": "ADAPTED from 20-min yoga at 9 PM. User too tired at 9 PM - moved earlier (7:30 PM), made simpler and shorter. Expected improvement: 60% → >80%.",
          "task_type": "exercise",
          "priority": "medium"
        }
      ]
    },
    {
      "block_name": "Wind Down",
      "start_time": "09:00 PM",
      "end_time": "10:00 PM",
      "zone_type": "recovery",
      "purpose": "Deep relaxation period - no additional tasks (Evening Routine handles wind-down)",
      "tasks": []
    }
  ],
  "performance_tracking": {
    "previous_completion_rate": "65%",
    "target_completion_rate": ">75%",
    "previous_total_tasks": 5,
    "current_total_tasks": 5,
    "task_changes": "3 kept, 1 adapted (simplified), 1 removed (failed), 1 new (progressive)"
  },
  "adaptation_notes": {
    "what_changed": [
      "Removed failed meal prep task (15% completion)",
      "Simplified evening yoga → gentle stretch, moved earlier",
      "Added 5-min morning meditation (user requested, ready for it)"
    ],
    "why_changed": [
      "Meal prep: Too ambitious, consistently failed",
      "Yoga: Right intent, wrong timing/intensity - adapted",
      "Meditation: User progressing (78% completion), requested in journal, short duration"
    ],
    "expected_outcome": "Increase completion from 65% to >75% through better timing and appropriate challenge",
    "monitor_for": [
      "Does adapted stretch work better at 7:30 PM?",
      "Does new meditation fit into morning without overwhelming?",
      "Overall completion trend after removing meal prep failure"
    ]
  },
  "next_evolution_criteria": {
    "if_completion_gt_80": {
      "timing": "After 14 days at >80%",
      "action": "Consider increasing meditation to 10 min OR adding complementary evening task",
      "rationale": "User will be ready for slight intensity increase"
    },
    "if_completion_50_80": {
      "timing": "After 14 days at 50-80%",
      "action": "Maintain current, maybe simplify stretch further or adjust meditation timing",
      "rationale": "Give more time to adapt to changes"
    },
    "if_completion_lt_50": {
      "timing": "Immediate (after 7 days <50%)",
      "action": "Remove new meditation, revert stretch to original or simpler version",
      "rationale": "Changes were too much - simplify back"
    }
  }
}
```

**CRITICAL ANTI-PATTERNS FOR ADAPTIVE MODE:**

❌ Regenerating completely new routine (ignoring history)
❌ Removing successful tasks (>80% completion) to "try something new"
❌ Adding multiple new tasks at once
❌ Ignoring AI context recommendations
❌ Changing tasks without data-driven rationale
❌ High-intensity tasks in evening blocks
❌ More than 2 tasks per energy block
❌ Tasks >15 minutes for new additions
❌ Assigning tasks without checking user's available time patterns

---

**UNIVERSAL CONSTRAINTS (Both Modes):**

1. **Fixed 5-Block Structure (MANDATORY - Flutter UI Compatibility):**
   - ALWAYS generate exactly 5 blocks in this order
   - ALWAYS use exact block names: "Morning Block", "Peak Energy Block", "Mid-day Slump", "Evening Routine", "Wind Down"
   - ALWAYS use correct zone_type per block: maintenance, peak, recovery, maintenance, recovery
   - Times are DYNAMIC (from circadian analysis) but block names/order are FIXED

2. **Task Density (OPTIMIZED):**
   - Morning Block: Maximum 2 tasks
   - Peak Energy Block: Maximum 1 task (usually 0 - user is working)
   - Mid-day Slump: Maximum 0 tasks (EMPTY - user is working)
   - Evening Routine: Maximum 2 tasks
   - Wind Down: Maximum 1 task (usually 0-1)
   - Total Daily: Maximum 6 tasks (reduced from 12-20)

3. **Duration Limits:**
   - Per task: ≤15 minutes
   - Per block: ≤45 minutes
   - Total daily: 20-90 minutes (archetype dependent)

4. **Energy Alignment:**
   - Morning Block: BUILDING, ACTIVATING tasks only
   - Peak Energy Block: WORK-FOCUSED (usually empty)
   - Mid-day Slump: EMPTY (respect work schedule)
   - Evening Routine: RELEASING, RECOVERING, CALMING tasks only
   - Wind Down: CALMING, SLEEP PREPARATION only
   - NO high-intensity exercise in evening blocks
   - NO cognitively demanding tasks when tired

4. **Cognitive Load:**
   - All tasks: "Low" cognitive load
   - Minimal decision-making required
   - Simple implementation steps
   - Clear, actionable instructions

5. **Busy Professional Respect:**
   - No assumptions about fixed work hours
   - Focus on energy patterns, not clock times
   - Flexible around work (home/office/hybrid)
   - Realistic time expectations

**CORE PRINCIPLE:**

**For NEW users:** "Start conservative, build progressive evolution pathway"
**For EXISTING users:** "Evolve what works, adapt what struggles, remove what fails, add sparingly"

Your goal is SUSTAINABLE HABIT BUILDING through either archetype-appropriate baselines (new users) or data-driven iterative refinement (existing users).
"""

# Update AGENT_PROMPTS dictionary
AGENT_PROMPTS = {
    "universal": UNIVERSAL_SYSTEM_PROMPT,
    "behavior_analysis": BEHAVIOR_ANALYSIS_AGENT_PROMPT,
    "plan_generation": PLAN_GENERATION_AGENT_PROMPT,
    "memory_management": MEMORY_MANAGEMENT_AGENT_PROMPT,
    "insights_generation": INSIGHTS_GENERATION_AGENT_PROMPT,
    "adaptation_engine": ADAPTATION_ENGINE_AGENT_PROMPT,
    "circadian_analysis": CIRCADIAN_ANALYSIS_AGENT_PROMPT,
    "routine_plan": ADAPTIVE_ROUTINE_GENERATION_PROMPT,  # NEW dual-mode
    "nutrition_plan": PLAN_GENERATION_AGENT_PROMPT,      # Keep separate
}
```

---

## Phase 3: Integration Updates

### 3.1 New Integration Methods

Add these new methods to `ai_context_generation_service.py`:

```python
async def enhance_routine_prompt_dual_mode(
    self,
    base_prompt: str,
    user_id: str,
    archetype: str = None
) -> str:
    """
    Enhanced prompt that handles BOTH initial and adaptive modes
    """
    try:
        # Check if new user
        last_plans = await self._get_last_plans(user_id, archetype, limit=3)
        is_new_user = not last_plans or len(last_plans) == 0

        if is_new_user:
            # INITIAL MODE
            return await self._enhance_initial_routine_prompt(
                base_prompt, user_id, archetype
            )
        else:
            # ADAPTIVE MODE
            return await self._enhance_adaptive_routine_prompt(
                base_prompt, user_id, archetype, last_plans
            )

    except Exception as e:
        logger.error(f"Failed to enhance routine prompt: {e}")
        return base_prompt

async def _enhance_initial_routine_prompt(
    self,
    base_prompt: str,
    user_id: str,
    archetype: str
) -> str:
    """For NEW users - archetype baseline context"""
    try:
        # Get any early engagement data (if available)
        raw_data = await self.engagement_service.get_raw_engagement_data(user_id, days=30)

        enhanced_prompt = f"""
{base_prompt}

NEW USER - INITIAL ROUTINE GENERATION MODE

USER PROFILE:
- User ID: {user_id[:8]}...
- Archetype: {archetype}
- Status: NEW USER (No previous routine history)

EARLY ENGAGEMENT DATA (if any):
- Calendar selections: {len(raw_data.get('calendar_selections', []))} items
- Task check-ins: {len(raw_data.get('task_checkins', []))} completions
- Daily journals: {len(raw_data.get('daily_journals', []))} entries

Early signals (if available):
{json.dumps(raw_data, indent=2, default=str)}

INSTRUCTIONS:
Generate an archetype-appropriate MVP BASELINE routine for this {archetype} busy professional.

Follow the INITIAL MODE framework:
1. Use archetype-specific baseline (see Foundation Builder, Systematic Improver, etc examples)
2. Start conservative (2-5 tasks total depending on archetype)
3. Focus on energy patterns (Morning Activation, Evening Restoration)
4. Keep Mid-Day empty for MVP
5. Build in clear evolution pathway
6. Set success criteria for first 2 weeks

Remember: This is their FIRST routine - set them up for long-term success through sustainable starting point.
"""
        return enhanced_prompt

    except Exception as e:
        logger.error(f"Failed to enhance initial prompt: {e}")
        return base_prompt

async def _enhance_adaptive_routine_prompt(
    self,
    base_prompt: str,
    user_id: str,
    archetype: str,
    last_plans: List[Dict]
) -> str:
    """For EXISTING users - adaptive evolution context"""
    try:
        # Get AI context with performance analysis
        context = await self._get_recent_context(user_id, hours=24)
        if not context:
            context = await self.generate_user_context(user_id, archetype)

        # Get check-in summary
        checkin_summary = await self._get_checkin_summary(user_id, days=14)

        enhanced_prompt = f"""
{base_prompt}

EXISTING USER - ADAPTIVE EVOLUTION MODE

USER PROFILE:
- User ID: {user_id[:8]}...
- Archetype: {archetype}
- Status: EXISTING USER (Has {len(last_plans)} previous routine iterations)

PREVIOUS ROUTINE ITERATIONS:
{json.dumps(last_plans, indent=2, default=str)}

AI PERFORMANCE ANALYSIS:
{context}

RECENT CHECK-IN DATA (Last 14 days):
{json.dumps(checkin_summary, indent=2, default=str)}

INSTRUCTIONS:
Generate the NEXT ITERATION by EVOLVING the previous routine based on performance data.

Follow the ADAPTIVE MODE framework:
1. Review AI context for Keep/Adapt/Remove recommendations
2. Determine evolution strategy (Simplify/Maintain/Progress/Intensify)
3. Apply task continuity rules (keep successful, adapt struggling, remove failed)
4. Respect energy pattern constraints (Morning Activation, Evening Restoration)
5. Only add new tasks if user is ready (completion >75%, AI recommends it)
6. Maximum 1 new task per iteration

Remember: This is EVOLUTION not REGENERATION - build on what works, don't start over.
"""
        return enhanced_prompt

    except Exception as e:
        logger.error(f"Failed to enhance adaptive prompt: {e}")
        return base_prompt

async def _get_checkin_summary(self, user_id: str, days: int = 14) -> Dict:
    """Get check-in performance summary for adaptive learning"""
    try:
        if self.use_rest_api:
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Get task check-ins
            result = self.supabase_client.table('task_checkins')\
                .select('plan_item_id, title, completion_status, satisfaction_rating, user_notes, planned_date')\
                .eq('profile_id', user_id)\
                .gte('planned_date', start_date.isoformat())\
                .execute()

            if not result.data:
                return {"message": "No check-in data available"}

            # Calculate statistics
            total = len(result.data)
            completed = sum(1 for c in result.data if c.get('completion_status') == 'completed')
            completion_rate = (completed / total * 100) if total > 0 else 0

            # Group by task title for pattern analysis
            task_performance = {}
            for checkin in result.data:
                title = checkin.get('title', 'Unknown')
                if title not in task_performance:
                    task_performance[title] = {
                        'total': 0,
                        'completed': 0,
                        'satisfaction_ratings': []
                    }
                task_performance[title]['total'] += 1
                if checkin.get('completion_status') == 'completed':
                    task_performance[title]['completed'] += 1
                if checkin.get('satisfaction_rating'):
                    task_performance[title]['satisfaction_ratings'].append(
                        checkin.get('satisfaction_rating')
                    )

            # Calculate per-task metrics
            task_metrics = []
            for task_title, perf in task_performance.items():
                completion_pct = (perf['completed'] / perf['total'] * 100) if perf['total'] > 0 else 0
                avg_satisfaction = (
                    sum(perf['satisfaction_ratings']) / len(perf['satisfaction_ratings'])
                    if perf['satisfaction_ratings'] else None
                )
                task_metrics.append({
                    'task': task_title,
                    'completion_rate': round(completion_pct, 1),
                    'avg_satisfaction': round(avg_satisfaction, 1) if avg_satisfaction else None,
                    'total_checkins': perf['total']
                })

            return {
                'overall_completion_rate': round(completion_rate, 1),
                'total_checkins': total,
                'completed_checkins': completed,
                'days_analyzed': days,
                'task_performance': sorted(task_metrics, key=lambda x: x['completion_rate'], reverse=True)
            }

        else:
            # Database version for production
            db = await self._ensure_db_connection()
            # Similar logic using db.fetch()
            pass

    except Exception as e:
        logger.error(f"Failed to get checkin summary: {user_id}: {e}")
        return {"error": str(e)}
```

### 3.2 Add Evolution Service (Optional)

Create a new file `services/routine_evolution_service.py`:

```python
"""
Routine Evolution Service
Determines how to evolve routine based on performance metrics
"""

from typing import Dict, Any

class RoutineEvolutionService:
    """Determines evolution strategy based on performance"""

    def determine_evolution_strategy(
        self,
        completion_rate: float,
        days_at_current_level: int,
        satisfaction_avg: float
    ) -> Dict[str, Any]:
        """
        Determine evolution strategy based on performance metrics

        Args:
            completion_rate: Overall completion percentage (0-100)
            days_at_current_level: Number of days at this performance level
            satisfaction_avg: Average satisfaction rating (0-10)

        Returns:
            Strategy dict with specific guidance for next routine
        """

        # OVERWHELMED - Simplify immediately
        if completion_rate < 50:
            return {
                "strategy": "SIMPLIFY",
                "action": "reduce_to_minimum",
                "task_limit": 2,  # Only 2 tasks total (1 morning, 1 evening)
                "new_tasks_allowed": 0,
                "adaptation_note": "User is overwhelmed. Reduce to absolute basics.",
                "criteria": {
                    "completion_rate": "<50%",
                    "days_at_level": days_at_current_level
                }
            }

        # STRUGGLING - Maintain with cleanup
        elif completion_rate < 75:
            return {
                "strategy": "MAINTAIN",
                "action": "keep_successful_remove_failures",
                "task_limit": 4,
                "new_tasks_allowed": 0,
                "adaptation_note": "Clean up routine - keep what works, remove what doesn't.",
                "criteria": {
                    "completion_rate": "50-75%",
                    "days_at_level": days_at_current_level
                }
            }

        # PROGRESSING - Ready for one small addition
        elif completion_rate >= 75 and days_at_current_level >= 7:
            return {
                "strategy": "PROGRESS",
                "action": "add_one_small_challenge",
                "task_limit": 6,
                "new_tasks_allowed": 1,
                "adaptation_note": "User is ready for ONE small progressive challenge.",
                "criteria": {
                    "completion_rate": "≥75%",
                    "days_at_level": f"≥7 days ({days_at_current_level})"
                }
            }

        # ADVANCED - Can slightly intensify
        elif completion_rate >= 85 and days_at_current_level >= 14:
            return {
                "strategy": "INTENSIFY",
                "action": "increase_existing_task_intensity",
                "task_limit": 6,
                "new_tasks_allowed": 0,  # Don't add, intensify existing
                "adaptation_note": "User mastered current routine. Slightly increase intensity of existing tasks.",
                "criteria": {
                    "completion_rate": "≥85%",
                    "days_at_level": f"≥14 days ({days_at_current_level})"
                }
            }

        # MAINTAINING - Keep current, fine-tune
        else:
            return {
                "strategy": "MAINTAIN",
                "action": "keep_current_fine_tune",
                "task_limit": 6,
                "new_tasks_allowed": 0,
                "adaptation_note": "Routine is working. Make minor timing/implementation tweaks only.",
                "criteria": {
                    "completion_rate": f"{completion_rate}%",
                    "days_at_level": days_at_current_level
                }
            }
```

---

## Phase 4: Testing Strategy

### Test Cases

Create `testing/test_adaptive_routine_generation.py`:

```python
"""
Test suite for adaptive routine generation system
"""

import pytest
from services.routine_generation_service import generate_routine
from services.routine_evolution_service import RoutineEvolutionService

# Test Initial Mode
def test_initial_routine_foundation_builder():
    """Test MVP baseline for Foundation Builder archetype"""
    routine = generate_routine(
        user_id="new_user_1",
        archetype="Foundation Builder",
        has_past_plans=False
    )

    assert routine.is_new_user == True
    assert routine.total_tasks == 2
    assert routine.evolution_phase == "MVP_Baseline"
    assert len([t for b in routine.time_blocks for t in b.tasks]) == 2

    # Verify energy blocks
    morning = next(b for b in routine.time_blocks if b.name == "Morning Activation")
    assert len(morning.tasks) == 1

    evening = next(b for b in routine.time_blocks if b.name == "Evening Restoration")
    assert len(evening.tasks) == 1

    midday = next(b for b in routine.time_blocks if b.name == "Mid-Day Maintenance")
    assert len(midday.tasks) == 0  # Should be empty for MVP

def test_initial_routine_peak_performer():
    """Test MVP baseline for Peak Performer archetype"""
    routine = generate_routine(
        user_id="new_user_2",
        archetype="Peak Performer",
        has_past_plans=False
    )

    assert routine.total_tasks == 5
    assert routine.evolution_phase == "MVP_Baseline"

    # Peak Performer can have mid-day task
    midday = next(b for b in routine.time_blocks if b.name == "Mid-Day Maintenance")
    assert len(midday.tasks) <= 1

# Test Adaptive Mode
def test_adaptive_keep_successful_tasks():
    """Test that successful tasks are kept exactly"""
    previous_routine = {
        "tasks": [
            {"id": "task_1", "title": "Morning Walk", "completion_rate": 90, "satisfaction": 8.5}
        ]
    }

    new_routine = generate_routine(
        user_id="existing_user_1",
        archetype="Systematic Improver",
        has_past_plans=True,
        previous_routine=previous_routine,
        completion_rate=78
    )

    # Should keep successful task exactly
    kept_task = next(t for t in new_routine.all_tasks if t.task_id == "task_1")
    assert kept_task.evolution_status == "KEPT"
    assert kept_task.title == "Morning Walk"  # Exact same

def test_adaptive_remove_failed_tasks():
    """Test that failed tasks are removed"""
    previous_routine = {
        "tasks": [
            {"id": "task_2", "title": "Meal Prep", "completion_rate": 15, "satisfaction": 3}
        ]
    }

    new_routine = generate_routine(
        user_id="existing_user_2",
        archetype="Foundation Builder",
        has_past_plans=True,
        previous_routine=previous_routine,
        completion_rate=55
    )

    # Failed task should be removed
    assert "task_2" not in [t.task_id for t in new_routine.all_tasks]

def test_adaptive_progression_strategy():
    """Test progressive addition when user ready"""
    new_routine = generate_routine(
        user_id="existing_user_3",
        archetype="Systematic Improver",
        has_past_plans=True,
        completion_rate=78,  # >75% = ready for progression
        days_at_level=10
    )

    assert new_routine.evolution_summary.evolution_strategy == "PROGRESS"
    assert new_routine.evolution_summary.new_tasks == 1  # Should add 1 task

    # New task should be short
    new_task = next(t for t in new_routine.all_tasks if t.evolution_status == "NEW")
    assert new_task.duration_minutes <= 10

def test_energy_pattern_constraints():
    """Test energy alignment regardless of mode"""
    routine = generate_routine(user_id="test_user", archetype="Any")

    for block in routine.time_blocks:
        if block.name == "Morning Activation":
            for task in block.tasks:
                assert task.energy_type in ["building", "activating"]
                assert len(block.tasks) <= 2

        elif block.name == "Evening Restoration":
            for task in block.tasks:
                assert task.energy_type in ["releasing", "recovering", "calming"]
                assert task.energy_type not in ["building", "activating"]
                assert len(block.tasks) <= 2

        elif block.name == "Mid-Day Maintenance":
            assert len(block.tasks) <= 1

def test_evolution_service_strategies():
    """Test evolution strategy determination"""
    service = RoutineEvolutionService()

    # Test SIMPLIFY
    strategy = service.determine_evolution_strategy(
        completion_rate=45,
        days_at_current_level=5,
        satisfaction_avg=5.0
    )
    assert strategy["strategy"] == "SIMPLIFY"
    assert strategy["task_limit"] == 2

    # Test PROGRESS
    strategy = service.determine_evolution_strategy(
        completion_rate=78,
        days_at_current_level=10,
        satisfaction_avg=8.0
    )
    assert strategy["strategy"] == "PROGRESS"
    assert strategy["new_tasks_allowed"] == 1

    # Test INTENSIFY
    strategy = service.determine_evolution_strategy(
        completion_rate=87,
        days_at_current_level=16,
        satisfaction_avg=8.5
    )
    assert strategy["strategy"] == "INTENSIFY"
    assert strategy["new_tasks_allowed"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Implementation Timeline

### Week 1: Dual-Mode Context Prompts
- **Day 1-2:** Implement `_generate_initial_context_prompt()`
- **Day 3-4:** Implement `_generate_adaptive_context_prompt()`
- **Day 5:** Test context generation for both modes with real/sample data

### Week 2: Dual-Mode Routine Prompt
- **Day 1-3:** Write complete `ADAPTIVE_ROUTINE_GENERATION_PROMPT` in `system_prompts.py`
- **Day 4:** Add all archetype baselines for initial mode
- **Day 5:** Test prompt with GPT-4 for various scenarios

### Week 3: Integration & Testing
- **Day 1-2:** Implement `enhance_routine_prompt_dual_mode()` and helper methods
- **Day 3:** Add `_get_checkin_summary()` method
- **Day 4:** Wire up to routine generation service
- **Day 5:** End-to-end integration testing

### Week 4: Validation & Refinement
- **Day 1-3:** Run test suite with different archetypes and user scenarios
- **Day 4-5:** Monitor metrics with real users, iterate based on results

---

## Expected Outcomes

### For NEW Users (Initial Mode)
- ✅ Archetype-appropriate MVP baseline routine
- ✅ 2-5 tasks total depending on archetype capacity
- ✅ Clear evolution pathway built-in
- ✅ Success criteria for first 2 weeks defined
- ✅ Energy pattern alignment from day 1
- ✅ No overwhelm - conservative, sustainable start

### For EXISTING Users (Adaptive Mode)
- ✅ Data-driven evolution from previous routine
- ✅ Keep successful tasks (>80% completion) exactly
- ✅ Adapt struggling tasks (40-80% completion) intelligently
- ✅ Remove failed tasks (<40% completion)
- ✅ Progressive additions only when user is ready
- ✅ Clear, data-backed rationale for all changes

### For ALL Busy Professionals
- ✅ No fixed "9-5" assumptions - flexible schedules
- ✅ Energy pattern-based structure (works for WFH, office, hybrid)
- ✅ Morning Activation + Evening Restoration focus (80%+ of tasks)
- ✅ Mid-Day usually empty (respects busy work schedules)
- ✅ 1-2 tasks per energy block maximum
- ✅ Total 2-6 tasks depending on archetype and readiness
- ✅ Sustainable, non-overwhelming, habit-building approach

### Quantitative Targets
- **Task Density:** 3-4 → 1-2 tasks per block (50% reduction)
- **User Overwhelm:** ~7/10 → <3/10 (>50% improvement)
- **Completion Rate:** ~60% → 80%+ (33% increase)
- **Energy Focus:** Morning/Evening ratio 80%+ (vs scattered all day)
- **Task Continuity:** 70%+ of successful tasks kept in next iteration
- **Progressive Evolution:** 80%+ users reach "Progressing" phase within 4 weeks

---

## Key Design Decisions

### 1. Why Dual-Mode?
**Rationale:** New users need conservative baselines; existing users need data-driven evolution. One-size-fits-all fails both groups.

### 2. Why Energy Patterns Over Clock Times?
**Rationale:** Busy professionals have flexible schedules (WFH/hybrid). Energy patterns (morning/evening) are universal; 9-5 is not.

### 3. Why Maximum 2 Tasks Per Block?
**Rationale:** Research shows 3-4 tasks = 60% completion; 1-2 tasks = 80%+ completion. Less is more for sustainability.

### 4. Why Keep Successful Tasks Exactly?
**Rationale:** Consistency builds habits. Changing successful tasks "to try something new" destroys momentum and user trust.

### 5. Why Progressive Addition Only When Ready?
**Rationale:** Adding tasks when completion <75% = guaranteed overwhelm. Data-driven gates prevent premature scaling.

### 6. Why Separate Initial/Adaptive Prompts?
**Rationale:** Different contexts require different analysis. Mixing them creates confusion and suboptimal outputs.

---

## Monitoring & Success Metrics

### User-Level Metrics
```python
metrics = {
    "completion_rate": percentage,        # Target: >75%
    "satisfaction_avg": 1-10 scale,      # Target: >7
    "overwhelm_score": 1-10 scale,       # Target: <3
    "task_density_avg": tasks_per_day,   # Target: 2-5
    "evolution_phase": "Beginner/Progressing/Advanced"
}
```

### System-Level Metrics
```python
system_metrics = {
    "new_user_completion_rate": percentage,     # Target: >60%
    "existing_user_completion_rate": percentage, # Target: >75%
    "task_keep_ratio": percentage,              # Target: >70%
    "successful_evolutions": percentage,         # Target: >80%
    "overwhelm_interventions": count,            # Monitor for patterns
}
```

### Track Evolution Effectiveness
```python
evolution_metrics = {
    "simplify_success_rate": percentage,   # Did simplification improve completion?
    "progress_success_rate": percentage,   # Did new tasks maintain >75% completion?
    "intensify_success_rate": percentage,  # Did intensity increase work?
    "adapt_success_rate": percentage,      # Did adapted tasks perform better?
}
```

---

## Future Enhancements (Post-MVP)

### Phase 2 Enhancements
1. **Time Block Flexibility:** User-customizable time blocks
2. **Work Pattern Detection:** Auto-detect WFH vs office days
3. **Seasonal Adaptation:** Adjust for seasons, vacations, stress periods
4. **Social Integration:** Group challenges, accountability partners

### Advanced Features
1. **Predictive Evolution:** ML model predicts optimal next evolution
2. **A/B Testing:** Test different evolution strategies per user
3. **Personalized Thresholds:** Dynamic completion targets per individual
4. **Multi-Week Planning:** Evolution across 4-week cycles

---

## Appendix: File Structure

```
hos-agentic-ai-prod/
├── services/
│   ├── ai_context_generation_service.py       # MODIFY: Add dual-mode methods
│   ├── routine_evolution_service.py           # NEW: Evolution strategy logic
│   └── routine_generation_service.py          # MODIFY: Use new prompts
│
├── shared_libs/
│   └── utils/
│       └── system_prompts.py                  # MODIFY: Add ADAPTIVE_ROUTINE_GENERATION_PROMPT
│
├── testing/
│   └── test_adaptive_routine_generation.py    # NEW: Test suite
│
└── OPTIMIZED_ROUTINE_AGENT_IMPLEMENTATION.md  # THIS FILE
```

---

## Quick Reference Commands

```bash
# Install dependencies
cd hos-agentic-ai-prod
pip install -r requirements.txt

# Run tests
python testing/test_adaptive_routine_generation.py

# Test context generation
python testing/test_ai_context_generation.py

# Full production test suite
python testing/run_production_tests.py

# Start server
python start_openai.py
```

---

**END OF IMPLEMENTATION PLAN**

Ready for implementation when you are! 🚀
