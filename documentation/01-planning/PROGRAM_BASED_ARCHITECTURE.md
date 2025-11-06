# PROGRAM-BASED WELLNESS COACHING ARCHITECTURE

**Document Version**: 1.0
**Date**: November 6, 2025
**Status**: Product Design Specification
**Author**: Product Design Session

---

## TABLE OF CONTENTS

1. [Product Vision](#product-vision)
2. [Goal-Based Program Catalog](#goal-based-program-catalog)
3. [Onboarding Flow](#onboarding-flow)
4. [Nightly Auto-Generation System](#nightly-auto-generation-system)
5. [User Experience: Daily Cycle](#user-experience-daily-cycle)
6. [Adaptive Learning Mechanism](#adaptive-learning-mechanism)
7. [Progress Tracking](#progress-tracking)
8. [User Value Proposition](#user-value-proposition)
9. [Key Features Summary](#key-features-summary)
10. [Success Metrics](#success-metrics)
11. [Edge Cases & Handling](#edge-cases--handling)
12. [Technical Architecture](#technical-architecture)

---

## PRODUCT VISION

### The Shift

**❌ OLD MODEL (What We DON'T Want)**
- User manually generates plan each day
- Disconnected daily tasks with no continuity
- No progression tracking over time
- Ad-hoc wellness approach
- Decision fatigue every morning

**✅ NEW MODEL (What We DO Want)**
- User commits to a **structured program** (21-60 days)
- System automatically generates tomorrow's plan every night at 9 PM
- Plans build on yesterday's performance (adaptive learning)
- Structured wellness journey with clear outcomes
- Zero planning effort from user

### Core Concept

HolisticOS is a **program-based coaching system** that:
- Offers goal-specific programs (Weight Loss, Marathon Training, 75 Hard, etc.)
- Auto-generates daily plans every night based on performance + calendar
- Anchors tasks to user's calendar with intelligent habit stacking
- Adapts difficulty based on completion rates and feedback
- Guides users through multi-week transformations with clear milestones

---

## GOAL-BASED PROGRAM CATALOG

### Program Categories

Users select ONE program to start. Each program has:
- **Goal**: Clear outcome (lose 15 lbs, run a marathon, etc.)
- **Duration**: 21-60 days
- **Archetype**: Coaching style (Peak Performer, Transformation Seeker, etc.)
- **Daily Tasks**: 8-12 tasks per day, auto-generated
- **Progression Phases**: 6 phases from baseline to independence

---

### 🎯 WEIGHT MANAGEMENT

#### Sustainable Weight Loss
- **Duration**: 30-60 days
- **Goal**: Lose 10-20 lbs through habit formation
- **Approach**: Progressive nutrition changes, enjoyable movement, sleep optimization
- **Recommended Archetype**: Transformation Seeker
- **Daily Tasks**: 8-10 (nutrition focus: 40%, movement: 30%, mindfulness: 20%, hydration: 10%)

#### Healthy Weight Gain
- **Duration**: 45-60 days
- **Goal**: Build muscle + increase calories sustainably
- **Approach**: Calorie surplus, strength training, protein focus
- **Recommended Archetype**: Systematic Improver
- **Daily Tasks**: 9-11 (nutrition focus: 50%, movement: 35%, recovery: 15%)

#### Maintenance Mode
- **Duration**: Ongoing (no end date)
- **Goal**: Sustain current weight + fitness level
- **Approach**: Balanced lifestyle, minimal friction
- **Recommended Archetype**: Foundation Builder
- **Daily Tasks**: 6-8 (balanced across all categories)

---

### 🏃 FITNESS CHALLENGES

#### 75 Hard
- **Duration**: 75 days (fixed)
- **Goal**: Complete Andy Frisella's mental toughness program
- **Requirements**: 2 workouts/day (1 outdoor), gallon of water, diet compliance, 10 pages reading, daily photo
- **Recommended Archetype**: Peak Performer
- **Daily Tasks**: 12 (strict compliance tracking)
- **Special**: No rest days, no alcohol, no cheat meals

#### Marathon Training
- **Duration**: 90-120 days
- **Goal**: Complete 26.2 miles
- **Approach**: Progressive running program (Couch to Marathon)
- **Recommended Archetype**: Peak Performer or Systematic Improver
- **Daily Tasks**: 7-9 (running: 40%, cross-training: 20%, nutrition: 25%, recovery: 15%)
- **Phases**: Base Building (4 weeks) → Build Up (8 weeks) → Peak (4 weeks) → Taper (2 weeks)

#### Strength Building
- **Duration**: 60 days
- **Goal**: Progressive overload for muscle gain
- **Approach**: Structured lifting program (4-day split)
- **Recommended Archetype**: Peak Performer
- **Daily Tasks**: 8-10 (strength training: 50%, nutrition: 30%, recovery: 20%)

#### Couch to 5K
- **Duration**: 60 days
- **Goal**: Run 3.1 miles without stopping
- **Approach**: Walk/run intervals → continuous running
- **Recommended Archetype**: Foundation Builder or Transformation Seeker
- **Daily Tasks**: 6-8 (running: 40%, recovery: 30%, hydration: 20%, nutrition: 10%)

---

### 🌴 LIFESTYLE TRANSFORMATIONS

#### Beach Body Prep
- **Duration**: 30-45 days
- **Goal**: Pre-vacation fitness + nutrition optimization
- **Approach**: Balanced training, calorie deficit, aesthetic focus
- **Recommended Archetype**: Transformation Seeker
- **Daily Tasks**: 9-11 (movement: 40%, nutrition: 40%, mindfulness: 20%)

#### Summer Wellness
- **Duration**: 60 days
- **Goal**: Outdoor activity focus, lighter meals, energy optimization
- **Approach**: Seasonal adaptation (outdoor workouts, fresh produce, vitamin D)
- **Recommended Archetype**: Connected Explorer
- **Daily Tasks**: 8-10 (outdoor movement: 50%, seasonal nutrition: 30%, hydration: 20%)

#### Winter Wellness
- **Duration**: 60 days
- **Goal**: Indoor workouts, immune support, seasonal affective disorder prevention
- **Approach**: Indoor activity, comfort food optimization, light therapy
- **Recommended Archetype**: Resilience Rebuilder
- **Daily Tasks**: 7-9 (indoor movement: 40%, immune nutrition: 30%, mood support: 30%)

#### Post-Injury Recovery
- **Duration**: 30-90 days (depends on injury)
- **Goal**: Rehabilitation protocol adherence
- **Approach**: Physical therapy exercises, gentle progression, pain management
- **Recommended Archetype**: Foundation Builder
- **Daily Tasks**: 6-8 (rehab exercises: 50%, nutrition: 25%, rest: 25%)

---

### 🧘 MENTAL WELLNESS

#### Stress Reset
- **Duration**: 30 days
- **Goal**: Reduce stress, improve resilience
- **Approach**: Meditation, breathwork, sleep optimization, boundary setting
- **Recommended Archetype**: Resilience Rebuilder
- **Daily Tasks**: 7-9 (mindfulness: 50%, sleep: 30%, movement: 20%)

#### Burnout Recovery
- **Duration**: 45 days
- **Goal**: Energy restoration, work-life balance
- **Approach**: Reduced intensity, restorative practices, boundary reinforcement
- **Recommended Archetype**: Foundation Builder
- **Daily Tasks**: 6-7 (recovery: 40%, gentle movement: 30%, nutrition: 30%)

#### Sleep Optimization
- **Duration**: 21 days
- **Goal**: Improve sleep quality and duration
- **Approach**: Sleep hygiene, circadian alignment, evening routine mastery
- **Recommended Archetype**: Systematic Improver
- **Daily Tasks**: 7-8 (evening routine: 40%, daytime habits: 35%, environment: 25%)

---

### 🎓 HABIT FOUNDATIONS

#### Wellness Foundations
- **Duration**: 21 days
- **Goal**: Build 5 core wellness habits
- **Focus**: Hydration, movement, nutrition, mindfulness, sleep
- **Recommended Archetype**: Foundation Builder
- **Daily Tasks**: 5-6 (one per habit category, kept simple)

#### Morning Routine Mastery
- **Duration**: 30 days
- **Goal**: Perfect your AM ritual for peak performance
- **Approach**: Habit stacking, time-blocking, consistency building
- **Recommended Archetype**: Peak Performer or Systematic Improver
- **Daily Tasks**: 4-6 (all morning-focused, 6-9 AM window)

#### Energy Optimization
- **Duration**: 45 days
- **Goal**: Align with circadian rhythm for maximum energy
- **Approach**: Chronotype analysis, peak performance timing, energy management
- **Recommended Archetype**: Systematic Improver
- **Daily Tasks**: 8-10 (time-optimized based on energy zones)

---

## ONBOARDING FLOW

### Screen Flow

```
Welcome Screen
    ↓
Goal Selection (5 categories)
    ↓
Program Selection (3-5 programs per category)
    ↓
Archetype Selection (6 archetypes, with recommendation)
    ↓
Duration Selection (21/30/45/60 days)
    ↓
Quick Preferences (4-5 questions)
    ↓
Calendar Connection (Google/Apple, optional)
    ↓
Wearable Connection (Sahha/HealthKit, optional)
    ↓
Program Confirmation
    ↓
Setup Complete
```

### Screen 1: Welcome
- **Purpose**: Set expectations
- **Content**: Brief intro to program-based approach
- **CTA**: "Let's Get Started"

### Screen 2: Goal Selection
- **Purpose**: Identify primary objective
- **Options**: 5 categories (Weight Management, Fitness Challenges, Lifestyle, Mental Wellness, Habit Foundations)
- **Visual**: Icon grid with descriptions

### Screen 3: Program Selection
- **Purpose**: Choose specific program
- **Content**: Cards showing duration, goals, daily task count, outcomes
- **Features**:
  - Program preview (sample day)
  - Success stories (social proof)
  - Difficulty indicator

### Screen 4: Archetype Selection
- **Purpose**: Personalize coaching style
- **Options**: 6 archetypes with personality descriptions
- **Recommendation**: AI suggests best match based on goal
- **Features**: Quiz option ("Help me choose")

### Screen 5: Duration Selection
- **Purpose**: Commitment level
- **Options**: 21/30/45/60 days (varies by program)
- **Recommendation**: Science-backed optimal duration highlighted
- **Visual**: Timeline showing phases

### Screen 6: Quick Preferences
- **Purpose**: Gather baseline info
- **Questions**:
  1. Wake time (picker)
  2. Sleep time (picker)
  3. Work hours (picker)
  4. Dietary restrictions (multi-select)
  5. Current activity level (1-5 scale)

### Screen 7: Calendar Connection
- **Purpose**: Enable auto-anchoring
- **Options**:
  - Google Calendar
  - Apple Calendar
  - Skip for now
- **Benefits Listed**:
  - No scheduling conflicts
  - Tasks placed at optimal times
  - Habit stacking with existing routines
- **Privacy Note**: Read-only access, we never write events

### Screen 8: Wearable Connection
- **Purpose**: Enable data-driven adaptation
- **Options**:
  - iOS: HealthKit (pulls from all connected devices)
  - Android: Health Connect
  - Skip for now
- **Benefits Listed**:
  - Plans adapt to your recovery scores
  - Task difficulty matches your energy
  - Avoid overtraining

### Screen 9: Program Confirmation
- **Purpose**: Final review before commitment
- **Content**:
  - Program name
  - Archetype
  - Duration
  - Start date (tomorrow)
  - End date (calculated)
- **Expectations Set**:
  - Daily plan at 9 PM
  - Tasks auto-placed in calendar
  - Adapts based on progress
  - Push notifications

### Screen 10: Setup Complete
- **Purpose**: Excitement + preparation
- **Content**:
  - Success message
  - "First plan ready tonight at 9 PM"
  - Reminder to check calendar tomorrow
- **CTAs**:
  - Explore the app
  - View program details
  - Invite friends

---

## NIGHTLY AUTO-GENERATION SYSTEM

### Trigger Configuration

**Time**: 9:00 PM user's local timezone
**Frequency**: Every night for program duration
**Technology**: Cron job or scheduled function (e.g., AWS EventBridge, Render Cron)

### Pipeline Stages

#### STAGE 1: User Context Loading (500ms)

**Inputs Loaded**:
```python
{
    "user_id": "user_sarah_123",
    "program": {
        "type": "Sustainable Weight Loss",
        "archetype": "Transformation Seeker",
        "duration_days": 45,
        "current_day": 15,
        "phase": "Consistency Building"
    },
    "today_performance": {
        "date": "2025-11-05",
        "tasks_completed": 7,
        "tasks_total": 10,
        "completion_rate": 0.70
    },
    "historical_checkins": [...],  // Last 14 days
    "wearable_data": {
        "readiness_score": 68,
        "sleep_quality": 75,
        "hrv": 52,
        "activity_load": 73
    },
    "tomorrow_calendar": [...]  // Google Calendar events for Nov 6
}
```

#### STAGE 2: Progress Analysis (1 second)

**AI Analyzes**:
- Today's completion rate vs 7-day average
- Category-level performance (hydration: 95%, movement: 60%, etc.)
- Friction patterns (evening tasks skipped 80%)
- Readiness/recovery trends (declining vs improving)

**Outputs**:
```python
{
    "overall_trend": "improving",  // 60% → 70% this week
    "struggling_categories": ["movement", "mindfulness"],
    "successful_categories": ["hydration", "nutrition"],
    "friction_patterns": {
        "evening_fatigue": {
            "detected": true,
            "skip_rate": 0.75,
            "recommendation": "Move tasks earlier or simplify"
        }
    },
    "readiness_status": "medium",  // 68/100
    "adaptation_needed": true
}
```

#### STAGE 3: AI Plan Generation (2 seconds)

**GPT-4 Prompt**:
```
Generate Day 16 wellness plan for:

Program: Sustainable Weight Loss (Day 16/45)
Archetype: Transformation Seeker
Phase: Consistency Building

Today's Performance:
- Overall: 70% (7/10 tasks completed)
- Hydration: 95% (excellent)
- Movement: 40% (struggling)
- Evening tasks: 25% (major friction)

User Context:
- Readiness: 68/100 (medium energy)
- Sleep: 6.5 hrs (target: 7.5 hrs)
- Work schedule: 9 AM - 5 PM
- Parent of 2 kids (6, 8)

Apply Adaptive Adjustments:
1. Simplify movement tasks (40% completion → reduce difficulty)
2. Move evening tasks earlier (before 8 PM fatigue cliff)
3. Keep successful hydration tasks stable (95% working)
4. Gradual increase: 10 → 9 tasks (capacity available at 70%)

Generate 9 tasks with:
- Specific times (will be anchored later)
- Atomic Habits principles
- Progressive difficulty (Week 3 standards)
- Category balance

Return JSON format.
```

**AI Response**:
```json
{
    "day_number": 16,
    "phase": "Consistency Building",
    "total_tasks": 9,
    "focus": "Simplify movement, strengthen morning routine",
    "tasks": [
        {
            "task_id": "task_016_001",
            "title": "Morning Hydration",
            "category": "hydration",
            "duration_minutes": 5,
            "priority": "high",
            "time_block_preference": "morning",
            "energy_zone": "peak"
        },
        // ... 8 more tasks
    ],
    "daily_theme": "Consistency through simplification",
    "motivation_message": "You've built a strong foundation. Today we're refining what works and easing what doesn't."
}
```

#### STAGE 4: Calendar Anchoring (1 second)

**Process**:
1. **Load Tomorrow's Calendar**: Fetch Google Calendar events for Nov 6
2. **Find Available Gaps**: CalendarGapFinder identifies 8 time slots
3. **Analyze Patterns**: PatternAnalyzer uses historical data (morning: 85% completion)
4. **Apply Habit Stacking**: HabitStackingEngine creates 9 habit stack cues
5. **Score Slots**: IntelligentScorer ranks each task-slot combination
6. **Assign Times**: Each task gets specific scheduled_time

**Output**:
```json
{
    "anchored_tasks": [
        {
            "task_id": "task_016_001",
            "title": "Morning Hydration",
            "scheduled_time": "06:25 AM",
            "scheduled_end_time": "06:30 AM",
            "habit_stack": {
                "anchor": "Breakfast with family at 6:45 AM",
                "phrase": "Right after breakfast, drink full glass of water",
                "cue": "Leave breakfast table → Grab water bottle"
            },
            "compliance_prediction": 0.95,
            "ai_reasoning": "User has 93% hydration completion. Breakfast is 90% reliable anchor."
        }
        // ... 8 more anchored tasks
    ]
}
```

#### STAGE 5: Delivery (500ms)

**Actions**:
1. **Save to Database**: Store anchored plan in `daily_plans` table
2. **Send Push Notification**: "Tomorrow's plan is ready! Day 16/45"
3. **Update Dashboard**: User sees preview when opening app
4. **Log Event**: Analytics tracking for generation success

**Push Notification Payload**:
```json
{
    "title": "Tomorrow's Plan is Ready!",
    "body": "Day 16 of 45 • 9 tasks scheduled",
    "data": {
        "plan_id": "plan_nov6_2025",
        "day_number": 16,
        "total_tasks": 9
    },
    "action": "open_plan_preview"
}
```

---

### Pipeline Performance

| Stage | Duration | Cost | Critical? |
|-------|----------|------|-----------|
| Context Loading | 500ms | $0 | Yes |
| Progress Analysis | 1s | $0.005 | Yes |
| AI Plan Generation | 2s | $0.02 | Yes |
| Calendar Anchoring | 1s | $0.01 | Yes |
| Delivery | 500ms | $0 | Yes |
| **TOTAL** | **5s** | **$0.035** | - |

**At Scale**:
- 10,000 users = 50,000 seconds = ~14 hours compute time
- Cost: $350/night for 10K users
- Solution: Batch processing (stagger by timezone, process in parallel)

---

## USER EXPERIENCE: DAILY CYCLE

### Night Before (9:00 PM)

#### User Receives Push Notification
```
🔔 HolisticOS

Tomorrow's plan is ready!

Day 15 of 45 • 8 tasks scheduled
Tap to preview
```

#### User Opens App → Preview Screen
```
┌─────────────────────────────────────────┐
│  ✨ Day 15 Ready                        │
│  Wednesday, Nov 6                       │
│                                         │
│  Your wellness tasks are anchored to   │
│  your calendar and ready to go.        │
│                                         │
│  📊 Program Progress: 31% (14/45 days) │
│  🎯 This Week's Focus: Consistency     │
│                                         │
│  MORNING ROUTINE (6:00 - 7:30 AM)     │
│  ☀️ 06:20  Morning Stretch (15 min)   │
│  💧 07:20  Hydration (5 min)           │
│                                         │
│  WORK DAY (10:00 AM - 1:30 PM)        │
│  💧 10:15  Water break (5 min)         │
│  🥗 12:30  Nutritious lunch (30 min)   │
│  🚶 01:15  Post-lunch walk (10 min)    │
│                                         │
│  EVENING (6:00 - 8:45 PM)             │
│  🍽️ 06:00  Dinner prep (30 min)       │
│  🧘 07:30  Gentle stretch (15 min)     │
│  📵 08:30  Digital sunset (15 min)     │
│                                         │
│  [ View Full Details ]                 │
│  [ Check Calendar ]                    │
└─────────────────────────────────────────┘
```

**User Reviews → Goes to Bed Prepared**

---

### Morning (6:00 AM)

#### User Checks Google Calendar
```
Wednesday, Nov 6
─────────────────────────────────────
06:00  Wake up routine (personal)
06:20  ⭐ Morning Stretch - HolisticOS
06:45  Breakfast with family
07:20  ⭐ Morning Hydration - HolisticOS
07:30  Kids school drop-off
08:15  Commute to office
09:30  Team Standup (work)
10:15  ⭐ Water break - HolisticOS
...
```

**User Sees**: "Perfect, my wellness tasks are already in my calendar!"

---

### During Day (6:20 AM - Task Time)

#### Pre-Task Reminder (5 min before)
```
🔔 HolisticOS • 6:15 AM

☀️ Morning Stretch in 5 minutes

After you finish your coffee,
take 15 min to stretch.

[ I'm Ready ]  [ Snooze 10min ]
```

#### Post-Task Check-In (Right after completion)
```
Did you complete Morning Stretch?

[ ✅ Yes ]  [ ⏭️ Skipped ]  [ 🕐 Later ]

↓ (If Yes)

How did it feel?
[ 😊 Enjoyed it ]  [ 😐 Neutral ]  [ 😞 Didn't enjoy ]

Would you do this again tomorrow?
[ ✅ Yes ]  [ 🤔 Maybe ]  [ ❌ No ]

Satisfaction (1-5):
⭐⭐⭐⭐⭐

[ Submit ]
```

**This Feedback → Feeds Tonight's Generation**

---

### Evening (9:00 PM - Daily Summary)

#### Summary Before Next Plan
```
┌─────────────────────────────────────────┐
│  Day 15 Complete! 🎉                    │
│                                         │
│  Today's Performance:                   │
│  7/8 tasks completed (88%)  ↑           │
│                                         │
│  ✅ Morning Stretch                     │
│  ✅ Morning Hydration                   │
│  ✅ Water break                         │
│  ✅ Nutritious lunch                    │
│  ✅ Post-lunch walk                     │
│  ✅ Dinner prep                         │
│  ✅ Gentle stretch                      │
│  ⏭️ Digital sunset (skipped)            │
│                                         │
│  💡 Insight: You've completed 90% of   │
│     morning tasks but only 40% of      │
│     evening tasks. Tomorrow's plan     │
│     will adjust for this.              │
│                                         │
│  🔔 Day 16 plan generating now...      │
│     You'll be notified when ready.     │
│                                         │
│  [ View Progress ]  [ Done ]           │
└─────────────────────────────────────────┘
```

**Cycle Repeats: Day 16 plan generated → User notified → Preview → Next day execution**

---

## ADAPTIVE LEARNING MECHANISM

### Learning Principles

1. **Performance-Based Difficulty**: High completion → increase difficulty, Low completion → decrease difficulty
2. **Category-Level Adaptation**: Adjust struggling categories independently
3. **Time-Based Adjustment**: Move tasks to high-compliance windows
4. **Friction Reduction**: Apply Atomic Habits principles to resistant tasks
5. **Progressive Challenge**: Gradual increase over program duration

---

### Example: 3-Day Evolution

#### Day 14 Performance
```
Completed: 6/10 (60%)

✅ Morning hydration
✅ Breakfast
❌ Morning workout (too hard)
✅ Mid-morning water
❌ Lunchtime yoga (no time)
✅ Nutritious lunch
✅ Afternoon walk
❌ Evening meal prep (too tired)
❌ Evening meditation (too tired)
✅ Digital sunset

Analysis:
- Morning: 3/4 = 75% ✅
- Midday: 2/4 = 50% ⚠️
- Evening: 1/3 = 33% ❌
- Movement: 0/2 = 0% (struggling)
```

#### Day 15 Adjustments
```
AI Adaptations:

1. Morning Workout → Morning Stretch (15 min)
   Reason: Workout too intense, user skipped
   Fix: Simplify (Atomic Habits: Make it Easy)

2. Lunchtime Yoga → Post-Lunch Walk (10 min)
   Reason: 30-min yoga unrealistic during work
   Fix: Reduce duration, increase success likelihood

3. Evening Meditation → Moved to 8:30 PM (from 9:15 PM)
   Reason: Evening fatigue after 9 PM
   Fix: Move earlier

4. Evening Meal Prep → Removed
   Reason: 80% skip rate for evening nutrition tasks
   Fix: Replace with morning prep task

Volume: 10 → 8 tasks (reduced)
```

#### Day 15 Performance
```
Completed: 7/8 (88%) ↑

✅ Morning hydration
✅ Breakfast
✅ Morning stretch (enjoyed!)
✅ Mid-morning water
✅ Nutritious lunch
✅ Post-lunch walk
✅ Evening stretch
❌ Digital sunset (forgot)

Analysis:
- Overall: 88% (up from 60%) ✅
- Movement: 2/2 = 100% (fixed by simplification)
- Digital sunset: Still struggling (needs better cue)
```

#### Day 16 Adjustments
```
AI Adaptations:

1. Keep Simplified Movement
   Reason: Stretch working, workout wasn't
   Action: Maintain current difficulty

2. Strengthen Digital Sunset Cue
   Reason: User forgets (no natural trigger)
   Fix: Stack after "Kids bedtime" (8 PM)
   New phrase: "After kids asleep → screens off"

3. Add Back Evening Task (Gradual)
   Reason: User at 88% (capacity available)
   Action: Add light meal prep (10 min, not 30 min)

Volume: 8 → 9 tasks
```

---

### Progression Phases (45-Day Program)

#### Week 1 (Days 1-7): BASELINE ESTABLISHMENT
**Goal**: Establish patterns, identify struggles
**Volume**: 10 tasks/day
**Adjustments**: Minimal (let user adapt)
**Focus**: Data collection

#### Week 2 (Days 8-14): SIMPLIFICATION
**Goal**: Reduce friction in struggling areas
**Volume**: 8 tasks/day (reduced)
**Adjustments**: Replace hard tasks with easier versions
**Example**:
- "30-min workout" → "15-min walk"
- "Track macros" → "Take photo of meals"
- "Evening yoga" → "5-min breathing"

#### Week 3 (Days 15-21): CONSISTENCY BUILDING
**Goal**: Lock in habits through repetition
**Volume**: 8-9 tasks/day
**Adjustments**: Keep successful tasks stable
**Focus**: Habit stacking strengthens, minimal changes

#### Week 4-5 (Days 22-35): PROGRESSIVE CHALLENGE
**Goal**: Gradually increase difficulty
**Volume**: 9-10 tasks/day
**Adjustments**: Slightly harder versions of mastered tasks
**Example**:
- "15-min walk" → "20-min walk"
- "Photo meals" → "Log 3 meals"
- "5-min breathing" → "10-min meditation"

#### Week 6+ (Days 36-45): OPTIMIZATION
**Goal**: Fine-tune for maximum performance
**Volume**: 10-11 tasks/day
**Adjustments**: Add new categories, increase complexity
**Focus**: Prepare for program completion, reduce hand-holding

---

## PROGRESS TRACKING

### Dashboard Views

#### Program Overview
```
┌─────────────────────────────────────────┐
│  📋 Sustainable Weight Loss             │
│  🌱 Transformation Seeker               │
│                                         │
│  ══════════════════ 33% (Day 15/45)    │
│                                         │
│  🎯 Current Phase:                      │
│     Week 3 - Consistency Building      │
│                                         │
│  📈 Your Progress:                      │
│  ┌─────────────────────────────────┐  │
│  │  Overall Completion: 78%         │  │
│  │  ████████████████░░░░░░░░       │  │
│  │                                  │  │
│  │  Hydration:      95% ✅          │  │
│  │  Nutrition:      82% ✅          │  │
│  │  Movement:       65% 🟡          │  │
│  │  Mindfulness:    48% ⚠️          │  │
│  │                                  │  │
│  │  Current Streak: 5 days 🔥      │  │
│  │  Best Streak:    7 days          │  │
│  └─────────────────────────────────┘  │
│                                         │
│  📊 Weekly Trend                        │
│  ┌─────────────────────────────────┐  │
│  │   90%│              ●            │  │
│  │   80%│        ●  ●     ●         │  │
│  │   70%│     ●           ●         │  │
│  │   60%│  ●                        │  │
│  │      └─────────────────────────  │  │
│  │       M  T  W  T  F  S  S       │  │
│  └─────────────────────────────────┘  │
│                                         │
│  💡 AI Insights:                        │
│  "You're crushing morning routines     │
│  (90% completion)! Evening tasks need  │
│  work. Tomorrow's plan places tasks    │
│  earlier to beat fatigue."             │
│                                         │
│  [ View Today's Plan ]                 │
│  [ View Tomorrow's Preview ]           │
│  [ See Full History ]                  │
└─────────────────────────────────────────┘
```

---

## USER VALUE PROPOSITION

### 7 Core Benefits

#### 1. Zero Planning Effort
**Old Way**: User must remember to generate plan each day
**New Way**: Plan appears automatically at 9 PM
**Benefit**: "I never have to think about what wellness tasks to do. It's just... handled."

#### 2. Intelligent Adaptation
**Scenario**: User struggles with evening tasks (30% completion)
**System Response**: Plans adjust automatically (move tasks earlier, reduce count)
**Benefit**: "The app learned I'm too tired at 9 PM and fixed it without me asking."

#### 3. Calendar Integration is Invisible
**Experience**: Connect calendar once → tasks appear automatically
**Benefit**: "My wellness routine fits my chaotic schedule. No conflicts, no stress."

#### 4. Habit Formation by Design
**Week 1**: Task placed at 6:20 AM (after coffee)
**Week 3**: Habit solidifies (automatic cue)
**Week 4**: No notification needed (routine established)
**Benefit**: "I don't even think about stretching anymore. I just do it after coffee."

#### 5. Commitment & Accountability
**Structure**: 45-day program with clear start/end
**Tracking**: Daily progress, streaks, milestones
**Benefit**: "I signed up for 45 days. I'm on Day 32. I'm seeing this through."

#### 6. Wearable-Driven Adaptation
**Data**: Readiness score drops from 75 → 55
**Response**: Next day plan reduces intensity automatically
**Benefit**: "The app knows when I need to take it easy based on my WHOOP data."

#### 7. Clear Progression
**Phases**: 6 phases from baseline to independence
**Milestones**: Week 3 = Consistency, Week 5 = Challenge
**Benefit**: "I can see my transformation happening in stages, not just random tasks."

---

## KEY FEATURES SUMMARY

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Goal-Based Programs** | 15+ structured journeys (21-60 days) | Clear commitment with defined outcomes |
| **Archetype Selection** | 6 coaching styles (personality-based) | Personalized approach that fits personality |
| **Nightly Auto-Generation** | System generates plan at 9 PM daily | Zero planning effort, wake up ready |
| **Calendar Auto-Anchoring** | Tasks placed in Google Calendar with habit stacking | No scheduling conflicts, optimal timing |
| **Adaptive Learning** | Plans evolve based on performance (struggling → easier, mastering → harder) | System learns from you, not generic |
| **Atomic Habits Integration** | Every task designed with 4 Laws | High compliance through behavioral science |
| **Push Notifications** | Timely reminders + plan ready alerts | Never miss a task, stay on track |
| **Progress Tracking** | Daily/weekly rates, streaks, categories | Visible progress motivates consistency |
| **Phase-Based Progression** | 6 phases over program duration | Structured journey with milestones |
| **Wearable Integration** | Sahha API for recovery/readiness scores | Tasks match physical capacity |
| **Pattern Recognition** | AI identifies time-of-day compliance | Optimal task placement |
| **Friction Detection** | AI detects struggling categories | Automatic difficulty adjustment |
| **Habit Stacking Engine** | Links tasks to existing routines | Higher completion through cues |
| **Meeting Context Awareness** | Avoids placing tasks before important meetings | Respects calendar priorities |
| **Multi-Day Planning** | Can preview next 3 days | Reduces uncertainty |

---

## SUCCESS METRICS

### Daily Metrics
- Today's completion rate: X/Y tasks (Z%)
- Tasks completed on time vs late
- Current streak: N days
- Category breakdown (which performed well/poorly)

### Weekly Metrics
- Average completion: X% this week (↑Y% from last week)
- Category trends (improving/declining)
- Habit stack success rates
- Time-of-day performance (morning vs evening)

### Program Metrics
- Overall progress: Day X/Y (Z%)
- Total tasks completed: X/Y
- Goal progress (e.g., weight: -4.2 lbs of -12 lbs target)
- Compliance trend: Start X% → Current Y%
- Phase completion (Baseline ✅, Simplification ✅, etc.)

### Outcome Metrics (End of Program)
- Final completion rate
- Goal achievement (yes/no + degree)
- Habits solidified (X habits with 80%+ consistency)
- Best streak achieved
- Total time invested

---

## EDGE CASES & HANDLING

### Calendar Changes Mid-Day

**Scenario**: User's 2 PM meeting moved to 1 PM (conflicts with post-lunch walk)

**Solution**:
- **NOT real-time** (no on-the-fly adaptation per requirement)
- App shows notification: "⚠️ Calendar conflict detected. Tomorrow's plan will adjust."
- Tonight at 9 PM, system regenerates with updated calendar
- Day 16 plan avoids that time slot

**Alternative** (Future Enhancement):
- Manual task rescheduling within app
- User drags task to different time
- System saves override

---

### Multiple Skipped Days

**Scenario**: User completes 0 tasks on Days 18, 19, 20

**System Response**:
- Day 21 plan drastically simplifies (10 → 5 tasks)
- Tasks become micro-habits (2-min versions)
- Notification: "We noticed you've been struggling. Let's reset with easier tasks."
- User options:
  - Continue with simplified plan
  - Pause program (resume later)
  - Restart from Day 1

---

### Perfect Performance Streak

**Scenario**: User completes 100% for 10 days straight

**System Response**:
- Gradually increase difficulty
- Add new categories (e.g., strength training)
- Increase durations (15-min → 25-min)
- Notification: "You're on fire! 🔥 Ready for the next level?"
- User can decline challenge

---

### Program Completion

**End-of-Program Flow**:
```
┌─────────────────────────────────────────┐
│  🎉 Program Complete!                   │
│                                         │
│  Sustainable Weight Loss                │
│  45 days • Transformation Seeker        │
│                                         │
│  Your Results:                          │
│  📈 Overall Completion: 82%             │
│  ⚖️  Weight Lost: 11.3 lbs             │
│  🔥 Best Streak: 14 days                │
│  ✅ Total Tasks: 342/415                │
│                                         │
│  💪 Habits You Built:                   │
│  • Morning stretch (95% consistency)   │
│  • Daily hydration (98% consistency)   │
│  • Post-lunch walks (87% consistency)  │
│                                         │
│  What's Next?                           │
│                                         │
│  [ Start New Program ]                  │
│  [ Continue Maintenance Mode ]          │
│  [ Export Your Data ]                   │
│  [ Share Your Success ]                 │
└─────────────────────────────────────────┘
```

**Options**:
1. Start New Program → Choose new goal (Marathon, 75 Hard, etc.)
2. Maintenance Mode → Simpler daily plans to maintain habits
3. Export Data → CSV/PDF of 45-day journey
4. Share Success → Social sharing with stats

---

### User Pauses Program

**Scenario**: User needs to pause (vacation, illness, etc.)

**Options**:
- Pause for 3 days (auto-resume)
- Pause for 1 week (auto-resume)
- Pause indefinitely (manual resume)

**On Resume**:
- System asks: "Restart from beginning?" or "Continue from Day X?"
- If continue: Plan difficulty resets slightly (accounts for break)

---

### Wearable Disconnection

**Scenario**: User's WHOOP battery died, no data for 2 days

**Fallback**:
- System generates plan without readiness data
- Uses historical averages
- Notification: "No wearable data today. Using your typical patterns."

---

## TECHNICAL ARCHITECTURE

### Database Schema

#### Programs Table
```sql
CREATE TABLE programs (
    program_id UUID PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    duration_days INTEGER,
    description TEXT,
    recommended_archetype VARCHAR(50),
    daily_task_count_min INTEGER,
    daily_task_count_max INTEGER,
    created_at TIMESTAMP
);
```

#### User Programs Table
```sql
CREATE TABLE user_programs (
    user_program_id UUID PRIMARY KEY,
    user_id UUID,
    program_id UUID,
    archetype VARCHAR(50),
    start_date DATE,
    end_date DATE,
    current_day INTEGER,
    status VARCHAR(20),  -- active, paused, completed
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (program_id) REFERENCES programs(program_id)
);
```

#### Daily Plans Table
```sql
CREATE TABLE daily_plans (
    daily_plan_id UUID PRIMARY KEY,
    user_program_id UUID,
    day_number INTEGER,
    date DATE,
    phase VARCHAR(50),
    total_tasks INTEGER,
    generated_at TIMESTAMP,
    FOREIGN KEY (user_program_id) REFERENCES user_programs(user_program_id)
);
```

#### Plan Tasks Table
```sql
CREATE TABLE plan_tasks (
    task_id UUID PRIMARY KEY,
    daily_plan_id UUID,
    title VARCHAR(200),
    description TEXT,
    category VARCHAR(50),
    priority VARCHAR(20),
    duration_minutes INTEGER,
    scheduled_time TIME,
    scheduled_end_time TIME,
    habit_stack_phrase TEXT,
    habit_stack_anchor TEXT,
    compliance_prediction FLOAT,
    ai_reasoning TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (daily_plan_id) REFERENCES daily_plans(daily_plan_id)
);
```

#### Task Check-Ins Table
```sql
CREATE TABLE task_checkins (
    checkin_id UUID PRIMARY KEY,
    task_id UUID,
    user_id UUID,
    completed BOOLEAN,
    completed_at TIMESTAMP,
    enjoyed BOOLEAN,
    satisfaction_rating INTEGER,  -- 1-5
    continue_preference VARCHAR(10),  -- yes, no, maybe
    timing_feedback VARCHAR(20),  -- early, perfect, late
    notes TEXT,
    FOREIGN KEY (task_id) REFERENCES plan_tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

### API Endpoints

#### Program Management
```
GET  /api/programs                     # List all available programs
GET  /api/programs/{program_id}        # Get program details
POST /api/user-programs                # Start a new program
GET  /api/user-programs/{user_id}      # Get user's active program
PUT  /api/user-programs/{id}/pause     # Pause program
PUT  /api/user-programs/{id}/resume    # Resume program
```

#### Daily Plan Generation
```
POST /api/daily-plans/generate         # Manual trigger (admin/testing)
GET  /api/daily-plans/{user_id}/today  # Get today's plan
GET  /api/daily-plans/{user_id}/tomorrow  # Preview tomorrow
GET  /api/daily-plans/{user_id}/history   # Past plans
```

#### Task Management
```
GET  /api/tasks/{daily_plan_id}        # Get tasks for a plan
POST /api/tasks/{task_id}/checkin      # Log task completion
PUT  /api/tasks/{task_id}/reschedule   # User manual reschedule
```

#### Progress Tracking
```
GET  /api/progress/{user_id}/overview  # Dashboard metrics
GET  /api/progress/{user_id}/weekly    # Weekly breakdown
GET  /api/progress/{user_id}/categories  # Category performance
```

---

### Cron Job Configuration

**Nightly Generation Job**:
```yaml
# render.yaml (Render Cron Job)
services:
  - type: cron
    name: nightly-plan-generator
    plan: starter
    schedule: "0 21 * * *"  # 9 PM UTC (adjust per timezone)
    dockerCommand: python scripts/nightly_plan_generator.py
```

**Batch Processing Strategy**:
```python
# scripts/nightly_plan_generator.py

async def generate_plans_for_all_users():
    """
    Process users in batches by timezone
    """
    timezones = get_all_user_timezones()

    for tz in timezones:
        if is_9pm_in_timezone(tz):
            users = get_users_in_timezone(tz, status='active_program')

            # Process in batches of 100
            for batch in chunk_users(users, size=100):
                await asyncio.gather(*[
                    generate_plan_for_user(user)
                    for user in batch
                ])
```

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation (Weeks 1-2)
- [ ] Database schema implementation
- [ ] Program catalog setup (5 initial programs)
- [ ] Basic onboarding flow
- [ ] Manual plan generation (no nightly job yet)

### Phase 2: Auto-Generation (Weeks 3-4)
- [ ] Nightly cron job setup
- [ ] AI plan generation pipeline
- [ ] Push notification system
- [ ] Calendar anchoring (algorithmic only)

### Phase 3: Adaptive Learning (Weeks 5-6)
- [ ] Pattern analysis AI
- [ ] Habit stacking engine
- [ ] Friction detection
- [ ] Difficulty adjustment logic

### Phase 4: Polish (Weeks 7-8)
- [ ] Progress tracking dashboard
- [ ] AI insights generation
- [ ] Program completion flow
- [ ] Edge case handling

---

## NEXT STEPS

1. **Validate Product Vision**: Ensure this aligns with target user needs
2. **Prioritize Features**: Determine MVP scope (which features ship first?)
3. **Design Database Schema**: Implement program + daily plan tables
4. **Build Onboarding Flow**: UI/UX for program selection
5. **Develop Plan Generation Pipeline**: Core AI generation logic
6. **Implement Calendar Anchoring**: Hybrid algorithmic + AI system
7. **Setup Cron Jobs**: Nightly auto-generation infrastructure
8. **Beta Testing**: Test with 10-50 users for 21 days

---

**END OF DOCUMENT**

*This is a living document. Update as product evolves.*
