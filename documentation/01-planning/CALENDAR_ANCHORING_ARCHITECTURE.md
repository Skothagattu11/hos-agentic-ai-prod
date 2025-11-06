# CALENDAR ANCHORING SYSTEM - ARCHITECTURE & IMPLEMENTATION PLAN

**Document Version**: 2.0
**Date**: November 6, 2025
**Status**: Design Specification (Updated with Existing Feedback Integration)
**Dependencies**:
- well-planned-api (Google Calendar integration)
- hos-agentic-ai-prod (AI plan generation + plan_items table)
- Existing feedback system (task_checkins, time_blocks tables)
- Friction-reduction system (Phase 5.0 compatibility required)

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Integration Points](#integration-points)
5. [Anchoring Algorithm Design](#anchoring-algorithm-design)
6. [Database Schema Changes](#database-schema-changes)
7. [API Design](#api-design)
8. [Mock Data Testing Strategy](#mock-data-testing-strategy)
9. [Implementation Phases](#implementation-phases)
10. [Error Handling & Edge Cases](#error-handling--edge-cases)

---

## OVERVIEW

### Problem Statement

Currently, HolisticOS generates AI-powered wellness plans with suggested task times (e.g., "Morning Stretch at 6:20 AM"), but these tasks exist in isolation without considering the user's actual calendar events (meetings, appointments, commitments).

**The Gap**:
- Plans stored in `plan_items` table have `scheduled_time` fields
- Google Calendar events exist in well-planned-api
- **No connection** between AI-generated tasks and real calendar events
- Tasks may conflict with meetings or be scheduled at unrealistic times

### Existing Feedback System (Foundation)

**IMPORTANT**: HolisticOS already has a sophisticated feedback system that we will integrate with:

1. **task_checkins** table captures:
   - `satisfaction_rating` (1-5 scale)
   - `completion_status` ('completed', 'partial', 'skipped')
   - `actual_completion_time` (when user actually checked in)
   - `planned_time` (when task was scheduled)
   - Links to `plan_item_id` and `analysis_result_id`

2. **time_blocks** table provides:
   - `block_title` (e.g., "Morning Foundation", "Peak Performance Block")
   - `time_range` (e.g., "6:00-7:00 AM")
   - `purpose` and `why_it_matters` context
   - Links plan_items to time-of-day categories

3. **Friction-reduction system** (Phase 5.0):
   - Analyzes feedback to detect friction patterns
   - Simplifies high-friction tasks (never excludes)
   - Uses Atomic Habits principles
   - **MUST NOT BE BROKEN** by calendar anchoring

**Integration Strategy**: Calendar anchoring will USE this existing feedback data to make intelligent placement decisions, while respecting the friction-reduction system's adaptations.

### Critical Compatibility Requirements

**🚨 NON-NEGOTIABLE**: Calendar anchoring MUST NOT break existing systems:

1. **Friction-Reduction System (Phase 5.0)**:
   - FeedbackService already analyzes task_checkins for friction patterns
   - Calendar anchoring will READ same data (task_checkins)
   - Calendar anchoring will NOT modify friction-reduction logic
   - Both systems will co-exist independently
   - Anchoring happens AFTER plan generation (AI already applied friction-reduction)

2. **Data Flow Separation**:
   ```
   Plan Generation → Friction-Reduction → AI generates plan → Plan Extraction → Calendar Anchoring
        (Phase 5.0)        (Phase 5.0)     (Existing)      (Existing)        (NEW - Phase 1-4)
   ```

3. **Database Operations**:
   - Anchoring only UPDATES `plan_items` (scheduled_time, anchoring_metadata)
   - Anchoring never MODIFIES task_checkins or time_blocks tables
   - Anchoring never DELETES or EXCLUDES tasks
   - Anchoring reads feedback data but doesn't interpret "friction" (FeedbackService owns that)

### Solution: Calendar Anchoring System

An **intelligent anchoring service** that:
1. Fetches user's Google Calendar events via well-planned-api
2. Loads AI-generated tasks from `plan_items` table (filtered by `analysis_result_id`)
3. Finds available time gaps in the calendar
4. Anchors tasks to optimal slots using hybrid algorithm (algorithmic + AI reasoning)
5. Updates `plan_items` with anchored times and metadata
6. Supports testing with mock calendar data (no Google connection required)

**Key Principles**:
- **Non-Destructive**: Never modifies Google Calendar (read-only integration)
- **User Control**: User reviews and approves anchored times before committing
- **Testable**: Works with mock calendar data for development/testing
- **Adaptive**: Uses AI to understand context (e.g., "don't place workout before important meeting")
- **Atomic Habits**: Applies habit stacking principles (anchor tasks to existing routines)

---

## SYSTEM ARCHITECTURE

### High-Level Components

```
┌──────────────────────────────────────────────────────────────┐
│  HolisticOS Architecture for Calendar Anchoring              │
└──────────────────────────────────────────────────────────────┘

Component 1: WELL-PLANNED-API (Port 8003)
├── Google Calendar OAuth Integration
├── Fetch Calendar Events API
├── Returns event data: id, title, start_time, end_time, etc.
└── Handles authentication and rate limiting

Component 2: HOS-AGENTIC-AI-PROD (Port 8002)
├── AI Plan Generation (existing)
│   └── Creates plan_items with scheduled_time suggestions
├── NEW: Calendar Anchoring Service
│   ├── Fetches calendar events from well-planned-api
│   ├── Finds available time gaps
│   ├── Runs hybrid anchoring algorithm
│   └── Updates plan_items with anchored times
└── NEW: Mock Calendar Data Generator
    └── Creates realistic mock events for testing

Component 3: DATABASE (Supabase PostgreSQL)
├── plan_items table (source of tasks to anchor)
├── time_blocks table (grouping context)
├── holistic_analysis_results table (plan metadata)
└── NEW: calendar_anchoring_results table (anchoring metadata)
```

### Service Layer Separation

```
┌─────────────────────────────────────────────────────────────┐
│  SERVICE LAYERS                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: EXTERNAL CALENDAR SERVICE (well-planned-api)     │
│  ├── Responsibility: Fetch Google Calendar events          │
│  ├── Input: user_id, date_range                           │
│  └── Output: List[CalendarEvent] JSON                      │
│                                                             │
│  Layer 2: CALENDAR INTEGRATION SERVICE (hos-agentic)       │
│  ├── Responsibility: Call well-planned-api                 │
│  ├── Input: user_id, start_date, end_date                 │
│  ├── Handles: API errors, fallback to mock data           │
│  └── Output: StandardizedCalendarEvents                    │
│                                                             │
│  Layer 3: CALENDAR GAP FINDER (hos-agentic)               │
│  ├── Responsibility: Find available time slots             │
│  ├── Input: CalendarEvents + time constraints             │
│  ├── Algorithm: Detect gaps between events                │
│  └── Output: List[AvailableSlot]                          │
│                                                             │
│  Layer 4: TASK LOADER (hos-agentic)                       │
│  ├── Responsibility: Load plan_items to anchor            │
│  ├── Input: analysis_result_id (UUID)                     │
│  ├── Query: Filter plan_items by analysis_result_id       │
│  └── Output: List[PlanItemToAnchor]                       │
│                                                             │
│  Layer 5: PATTERN ANALYZER (AI-powered + existing data)   │
│  ├── Responsibility: Analyze user completion patterns     │
│  ├── Input: task_checkins table (satisfaction, timing)   │
│  ├── Query: Load last 30 days of check-ins per category  │
│  ├── Analyze: satisfaction_rating, actual_completion_time│
│  ├── AI: OpenAI GPT-4 analyzes patterns                  │
│  └── Output: UserPatterns (optimal windows, categories)  │
│                                                             │
│  Layer 6: HABIT STACKING ENGINE (AI-powered)              │
│  ├── Responsibility: Apply Atomic Habits principles       │
│  ├── Input: Tasks + Available slots + Existing routines  │
│  ├── AI: OpenAI GPT-4o-mini for quick habit decisions    │
│  └── Output: Habit-stacked task placements               │
│                                                             │
│  Layer 7: INTELLIGENT SCORER (AI-powered)                  │
│  ├── Responsibility: Score task-slot combinations         │
│  ├── Input: Tasks + Slots + Patterns + Goals             │
│  ├── Scoring: Energy zones, patterns, habit stacks       │
│  └── Output: Ranked list of optimal placements           │
│                                                             │
│  Layer 8: ANCHORING COORDINATOR (orchestrator)            │
│  ├── Responsibility: Orchestrate entire anchoring flow    │
│  ├── Calls: All above services in sequence               │
│  ├── Writes: Updates plan_items.scheduled_time           │
│  └── Output: AnchoredPlan with metadata                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## DATA FLOW

### Complete Anchoring Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: TRIGGER ANCHORING                                   │
└──────────────────────────────────────────────────────────────┘

User Action:
- User generates new plan (POST /api/user/{user_id}/routine/generate)
- OR user requests re-anchoring (POST /api/anchoring/anchor-plan)

Input Parameters:
- user_id: "user_sarah_123"
- analysis_result_id: "uuid-of-generated-plan"
- target_date: "2025-11-06"
- use_mock_data: false (default)

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 2: FETCH CALENDAR EVENTS                               │
└──────────────────────────────────────────────────────────────┘

CalendarIntegrationService:
├── IF use_mock_data == true:
│   └── Load mock events from MockCalendarGenerator
├── ELSE:
│   ├── Call well-planned-api:
│   │   GET http://localhost:8003/api/calendars/google/{user_id}/events
│   │   ?time_min=2025-11-06T00:00:00Z
│   │   &time_max=2025-11-06T23:59:59Z
│   ├── Handle errors:
│   │   ├── No OAuth connection → Fallback to mock data
│   │   ├── Network timeout → Retry once, then mock data
│   │   └── Empty calendar → Return empty list (valid state)
│   └── Standardize format:
│       └── Convert well-planned-api format → Internal CalendarEvent model

Output Example:
{
  "calendar_events": [
    {
      "id": "gcal_event_001",
      "title": "Team Standup",
      "start_time": "2025-11-06T09:30:00Z",
      "end_time": "2025-11-06T10:00:00Z",
      "status": "confirmed",
      "meeting_link": "https://meet.google.com/abc",
      "attendees": [{"email": "colleague@company.com"}]
    },
    {
      "id": "gcal_event_002",
      "title": "Client Strategy Call",
      "start_time": "2025-11-06T14:00:00Z",
      "end_time": "2025-11-06T15:00:00Z",
      "status": "confirmed",
      "attendees": [{"email": "client@company.com"}]
    }
  ],
  "total_events": 2,
  "date": "2025-11-06"
}

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 3: FIND AVAILABLE TIME GAPS                            │
└──────────────────────────────────────────────────────────────┘

CalendarGapFinder:
├── Input: CalendarEvents + TimeConstraints
├── Algorithm:
│   ├── Sort events by start_time
│   ├── Detect gaps between consecutive events
│   ├── Filter gaps < min_duration (default: 15 min)
│   ├── Exclude user sleep hours (default: 10 PM - 6 AM)
│   └── Label gaps by size: small (15-30m), medium (30-60m), large (60m+)
└── Output: List of AvailableSlot objects

Output Example:
{
  "available_slots": [
    {
      "slot_id": "slot_001",
      "start_time": "06:00:00",
      "end_time": "09:30:00",
      "duration_minutes": 210,
      "gap_type": "morning_start",
      "before_event": null,
      "after_event": "Team Standup"
    },
    {
      "slot_id": "slot_002",
      "start_time": "10:00:00",
      "end_time": "14:00:00",
      "duration_minutes": 240,
      "gap_type": "between_events",
      "before_event": "Team Standup",
      "after_event": "Client Strategy Call"
    },
    {
      "slot_id": "slot_003",
      "start_time": "15:00:00",
      "end_time": "22:00:00",
      "duration_minutes": 420,
      "gap_type": "evening_end",
      "before_event": "Client Strategy Call",
      "after_event": null
    }
  ],
  "total_available_minutes": 870
}

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 4: LOAD PLAN ITEMS TO ANCHOR                           │
└──────────────────────────────────────────────────────────────┘

TaskLoader:
├── Query Database:
│   SELECT * FROM plan_items
│   WHERE analysis_result_id = '{uuid}'
│   AND plan_date = '2025-11-06'
│   ORDER BY scheduled_time ASC
├── Join with time_blocks for context
└── Output: List of PlanItemToAnchor objects

Output Example:
{
  "plan_items": [
    {
      "id": "uuid-task-001",
      "title": "Morning Hydration",
      "description": "Drink full glass of water to rehydrate",
      "category": "hydration",
      "priority_level": "high",
      "scheduled_time": "08:45:00",  // AI-suggested time
      "scheduled_end_time": "08:50:00",
      "estimated_duration_minutes": 5,
      "time_block": "Morning Block",
      "energy_zone_preference": "peak"
    },
    {
      "id": "uuid-task-002",
      "title": "Morning Stretch",
      "category": "movement",
      "priority_level": "medium",
      "scheduled_time": "09:00:00",
      "scheduled_end_time": "09:15:00",
      "estimated_duration_minutes": 15,
      "energy_zone_preference": "peak"
    },
    // ... 8 more tasks
  ],
  "total_tasks": 10,
  "analysis_result_id": "uuid-of-plan"
}

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 5: PATTERN ANALYSIS (Using Existing Feedback Data)    │
└──────────────────────────────────────────────────────────────┘

PatternAnalyzer (AI-Powered + Database):
├── QUERY task_checkins table:
│   SELECT
│     pi.category,
│     pi.time_block_id,
│     tb.block_title,
│     tb.time_range,
│     tc.satisfaction_rating,
│     tc.completion_status,
│     tc.actual_completion_time,
│     tc.planned_time,
│     EXTRACT(HOUR FROM tc.actual_completion_time) as check_in_hour
│   FROM task_checkins tc
│   JOIN plan_items pi ON tc.plan_item_id = pi.id
│   JOIN time_blocks tb ON pi.time_block_id = tb.id
│   WHERE tc.profile_id = $1
│     AND tc.created_at > NOW() - INTERVAL '30 days'
│   ORDER BY tc.created_at DESC
├── ANALYZE patterns:
│   ├── Calculate completion rates by time_block (Morning, Afternoon, Evening)
│   ├── Calculate average satisfaction_rating by category
│   ├── Identify preferred check-in times (actual_completion_time patterns)
│   ├── Detect timing drift (planned_time vs actual_completion_time)
│   └── Find high-satisfaction time windows (satisfaction_rating >= 4)
├── IF sufficient data (>50 check-ins):
│   └── Call OpenAI GPT-4 to extract insights:
│       Prompt: "Analyze completion patterns from check-in data..."
│       Response: UserPatterns object with recommendations
├── ELSE:
│   └── Use default patterns (no historical data)
└── Output: UserPatterns

Output Example:
{
  "user_patterns": {
    "time_block_analysis": {
      "Morning Foundation (6:00-9:00 AM)": {
        "completion_rate": 0.87,
        "avg_satisfaction": 4.3,
        "check_in_count": 42,
        "preferred_check_in_hour": 7  // Users check in at 7 AM most often
      },
      "Peak Performance (9:00-12:00 PM)": {
        "completion_rate": 0.65,
        "avg_satisfaction": 3.8,
        "check_in_count": 28
      },
      "Evening Wind Down (6:00-9:00 PM)": {
        "completion_rate": 0.45,
        "avg_satisfaction": 3.2,
        "check_in_count": 18
      }
    },
    "category_insights": {
      "hydration": {"completion_rate": 0.92, "avg_satisfaction": 4.5},
      "movement": {"completion_rate": 0.78, "avg_satisfaction": 4.1},
      "nutrition": {"completion_rate": 0.45, "avg_satisfaction": 3.0}
    },
    "timing_drift_analysis": {
      "average_drift_minutes": 15,  // Users check in 15 min after planned time
      "categories_with_drift": ["nutrition", "stress_management"]
    },
    "optimal_windows": [
      {"start": "06:00", "end": "09:00", "reason": "87% completion + 4.3/5 satisfaction"}
    ],
    "friction_integration": {
      "high_friction_categories": ["nutrition", "stress_management"],
      "low_friction_categories": ["hydration", "movement"],
      "note": "Integrated with Phase 5.0 friction-reduction system"
    }
  }
}

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 6: HYBRID ANCHORING ALGORITHM                          │
└──────────────────────────────────────────────────────────────┘

AnchoringCoordinator orchestrates 3 sub-services:

6A. HABIT STACKING ENGINE (AI-Powered)
├── For each available_slot:
│   ├── Identify nearby calendar events (within 30 min)
│   ├── Check for existing routines in UserPatterns
│   ├── Call OpenAI GPT-4o-mini:
│   │   Prompt: "Which task should stack after 'Team Standup'?"
│   │   Response: Habit stack recommendation
│   └── Add habit_stack_bonus to slot scoring
└── Output: Slots with habit stacking metadata

6B. INTELLIGENT SCORER (Hybrid: Algorithmic + AI)
├── For each (task, slot) combination:
│   ├── Algorithmic Scoring (fast):
│   │   ├── Duration fit: +0-2 points
│   │   ├── Time window match: +0-10 points
│   │   └── Priority alignment: +0-3 points
│   ├── AI Scoring (contextual):
│   │   ├── Pattern-based: +0-10 points (from UserPatterns)
│   │   ├── Habit stacking: +0-10 points (from HabitStackingEngine)
│   │   ├── Goal alignment: +0-8 points (e.g., weight loss goal)
│   │   └── Meeting context: +0-5 points (e.g., don't place workout before important call)
│   └── Total Score: Sum of all components (max 48 points)
└── Output: Scored list of (task, slot) pairs

6C. OPTIMAL ASSIGNMENT
├── Sort all (task, slot) pairs by score (descending)
├── Greedy assignment algorithm:
│   ├── Assign highest-scored task to best slot
│   ├── Mark slot as "used" (adjust available time)
│   ├── Re-score remaining tasks (some slots now partial)
│   └── Repeat until all tasks assigned
└── Output: Final anchored task list

Output Example:
{
  "anchored_tasks": [
    {
      "task_id": "uuid-task-002",
      "original_time": "09:00:00",
      "anchored_time": "06:20:00",  // ✅ ANCHORED
      "anchored_end_time": "06:35:00",
      "slot_id": "slot_001",
      "confidence_score": 45,  // Out of 48
      "anchoring_metadata": {
        "habit_stack": {
          "anchor": "Morning coffee at 6:10 AM",
          "phrase": "After coffee, do 15-min stretch",
          "reliability": 0.98
        },
        "scoring_breakdown": {
          "duration_fit": 2,
          "pattern_score": 10,
          "habit_bonus": 10,
          "goal_alignment": 8,
          "meeting_context": 4,
          "time_window_match": 10,
          "priority_alignment": 1
        },
        "reasoning": "Morning coffee (98% reliability) is strongest anchor. User's morning window has 85% completion rate. Movement category improved by placing in peak zone."
      }
    },
    {
      "task_id": "uuid-task-001",
      "original_time": "08:45:00",
      "anchored_time": "07:20:00",
      "anchored_end_time": "07:25:00",
      "slot_id": "slot_001",
      "confidence_score": 40,
      "anchoring_metadata": {
        "habit_stack": {
          "anchor": "Breakfast at 6:45 AM",
          "phrase": "Right after breakfast, drink water"
        }
      }
    }
    // ... 8 more anchored tasks
  ],
  "anchoring_summary": {
    "tasks_anchored": 10,
    "tasks_rescheduled": 7,
    "average_confidence": 0.88,
    "conflicts_detected": 0
  }
}

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 7: UPDATE DATABASE                                     │
└──────────────────────────────────────────────────────────────┘

Database Update Service:
├── BEGIN TRANSACTION
├── For each anchored_task:
│   ├── UPDATE plan_items SET
│   │   scheduled_time = anchored_time,
│   │   scheduled_end_time = anchored_end_time,
│   │   anchoring_metadata = JSON(metadata),
│   │   is_anchored = true,
│   │   anchored_at = NOW()
│   │   WHERE id = task_id
├── INSERT INTO calendar_anchoring_results:
│   ├── analysis_result_id
│   ├── user_id
│   ├── target_date
│   ├── anchoring_summary (JSON)
│   ├── total_tasks_anchored
│   └── created_at
├── COMMIT TRANSACTION
└── Output: Success confirmation

↓

┌──────────────────────────────────────────────────────────────┐
│  STEP 8: RETURN TO CLIENT                                    │
└──────────────────────────────────────────────────────────────┘

API Response:
{
  "success": true,
  "message": "Plan successfully anchored to calendar",
  "anchoring_id": "uuid-anchoring-result",
  "summary": {
    "tasks_total": 10,
    "tasks_anchored": 10,
    "tasks_rescheduled": 7,
    "tasks_kept_original_time": 3,
    "average_confidence": 0.88,
    "calendar_conflicts": 0
  },
  "anchored_plan": {
    "analysis_result_id": "uuid-of-plan",
    "date": "2025-11-06",
    "tasks": [/* anchored tasks with metadata */]
  }
}
```

---

## INTEGRATION POINTS

### 1. Well-Planned-API Integration

**Service Name**: `CalendarIntegrationService`
**Location**: `hos-agentic-ai-prod/services/integrations/calendar_integration_service.py`

#### Methods

**`fetch_calendar_events(user_id, start_date, end_date)`**
- **Purpose**: Fetch Google Calendar events from well-planned-api
- **API Call**: `GET http://localhost:8003/api/calendars/google/{user_id}/events`
- **Query Parameters**:
  - `time_min`: ISO 8601 datetime (start_date at 00:00:00)
  - `time_max`: ISO 8601 datetime (end_date at 23:59:59)
- **Headers**: `Authorization: Bearer {token}` (if authentication required)
- **Response Format** (from well-planned-api):
  ```json
  {
    "success": true,
    "events": [
      {
        "id": "event_id_123",
        "title": "Team Meeting",
        "start_time": "2025-11-06T14:00:00Z",
        "end_time": "2025-11-06T15:00:00Z",
        "location": "Conference Room A",
        "meeting_link": "https://meet.google.com/abc",
        "attendees": [{"email": "user@example.com"}],
        "status": "confirmed"
      }
    ]
  }
  ```
- **Error Handling**:
  - 404 (No OAuth tokens) → Log warning, return empty list
  - Network timeout → Retry once, then fallback to mock data
  - 500 (Server error) → Log error, return empty list
- **Output**: Standardized `List[CalendarEvent]` objects

**`check_calendar_connection(user_id)`**
- **Purpose**: Verify user has connected Google Calendar
- **API Call**: `GET http://localhost:8003/api/auth/google/status/{user_id}`
- **Response**: `{"connected": true/false}`
- **Use Case**: Before anchoring, check if calendar available

---

### 2. Database Integration

**Service Name**: `TaskLoaderService`
**Location**: `hos-agentic-ai-prod/services/anchoring/task_loader_service.py`

#### Methods

**`load_plan_items_to_anchor(analysis_result_id, plan_date)`**
- **Purpose**: Load unanchored tasks from database
- **Query**:
  ```sql
  SELECT
    pi.*,
    tb.block_title,
    tb.time_range,
    tb.purpose
  FROM plan_items pi
  LEFT JOIN time_blocks tb ON pi.time_block_id = tb.id
  WHERE pi.analysis_result_id = $1
    AND pi.plan_date = $2
    AND pi.is_trackable = true
  ORDER BY pi.scheduled_time ASC
  ```
- **Output**: `List[PlanItemToAnchor]` with time block context

**`update_anchored_times(anchored_tasks)`**
- **Purpose**: Batch update plan_items with anchored times
- **Query**:
  ```sql
  UPDATE plan_items SET
    scheduled_time = $1,
    scheduled_end_time = $2,
    anchoring_metadata = $3,
    is_anchored = true,
    anchored_at = NOW(),
    updated_at = NOW()
  WHERE id = $4
  ```
- **Batch Size**: 50 tasks per batch (prevents lock timeout)

---

### 3. AI Service Integration

**Service Name**: `OpenAIAnchoringService`
**Location**: `hos-agentic-ai-prod/services/anchoring/ai_anchoring_service.py`

#### Methods

**`analyze_user_patterns(user_id, historical_checkins)`**
- **Purpose**: AI analyzes completion patterns
- **Model**: GPT-4 (needs strong reasoning)
- **Prompt**: See PATTERN ANALYZER in data flow
- **Cost**: ~$0.01 per user
- **Caching**: Cache results for 24 hours (patterns don't change fast)

**`recommend_habit_stack(task, available_slots, existing_routines)`**
- **Purpose**: AI suggests habit stacking opportunities
- **Model**: GPT-4o-mini (faster, cheaper for quick decisions)
- **Prompt**: See HABIT STACKING ENGINE in data flow
- **Cost**: ~$0.002 per task (10 tasks = $0.02)

**`score_meeting_context(task, nearby_meetings)`**
- **Purpose**: AI understands meeting importance and timing
- **Model**: GPT-4o-mini
- **Example**: "Don't place workout before important client call"
- **Cost**: ~$0.001 per task-meeting pair

---

## ANCHORING ALGORITHM DESIGN

### Hybrid Approach: Algorithmic + AI

```
┌──────────────────────────────────────────────────────────────┐
│  ANCHORING ALGORITHM ARCHITECTURE                            │
└──────────────────────────────────────────────────────────────┘

Phase 1: ALGORITHMIC PREPARATION (Fast - 100ms)
├── Find time gaps
├── Basic duration matching
├── Filter incompatible slots (too small, wrong time of day)
└── Generate all possible (task, slot) combinations

Phase 2: AI ENHANCEMENT (Intelligent - 2-3 seconds)
├── Pattern analysis (historical data)
├── Habit stacking recommendations (Atomic Habits principles)
├── Meeting context scoring (importance + timing)
└── Goal alignment scoring

Phase 3: OPTIMAL ASSIGNMENT (Fast - 50ms)
├── Combine algorithmic + AI scores
├── Greedy assignment algorithm
├── Conflict resolution
└── Generate final placements
```

### Scoring Formula

**For each (task, slot) pair**:

```
Total Score = Base Score + Pattern Score + Habit Score + Goal Score + Context Score

Base Score (Algorithmic - 0 to 15 points):
├── Duration Fit: 0-2 points
│   ├── Perfect fit (slot == task duration): +2
│   ├── Close fit (slot within 20% of duration): +1
│   └── Poor fit: +0
├── Time Window Match: 0-10 points
│   ├── Task prefers "morning", slot is 6-9 AM: +10
│   ├── Task prefers "peak", slot is peak energy zone: +10
│   ├── Task prefers "evening", slot is 6-9 PM: +8
│   └── Mismatch: +0
└── Priority Alignment: 0-3 points
    ├── High-priority task in peak energy slot: +3
    ├── Medium-priority in maintenance slot: +2
    └── Low-priority in recovery slot: +1

Pattern Score (AI - 0 to 10 points - FROM task_checkins DATA):
├── Historical Completion Rate (from task_checkins.completion_status):
│   ├── Time block completion rate ≥ 90%: +10
│   ├── Time block completion rate 70-89%: +7
│   ├── Time block completion rate 50-69%: +5
│   ├── Time block completion rate 30-49%: +3
│   └── Time block completion rate <30%: +0 (avoid this window)
├── Satisfaction Score (from task_checkins.satisfaction_rating):
│   ├── Avg satisfaction ≥ 4.0: +3 bonus
│   ├── Avg satisfaction 3.5-3.9: +2 bonus
│   └── Avg satisfaction <3.5: +0
└── Timing Drift Awareness (from actual_completion_time vs planned_time):
    └── If slot accounts for typical drift: +2 bonus

Habit Score (AI - 0 to 10 points):
├── Habit Stacking Available:
│   ├── Strong anchor (95%+ reliability): +10
│   ├── Good anchor (80-95% reliability): +7
│   ├── Weak anchor (60-80% reliability): +4
│   └── No anchor: +0
└── Atomic Habits Principles:
    ├── Make it Obvious: +2
    ├── Make it Easy: +2
    ├── Make it Attractive: +2
    └── Make it Satisfying: +2

Goal Score (AI - 0 to 8 points):
├── Primary Goal Alignment:
│   ├── Task directly supports goal: +8
│   ├── Task indirectly supports goal: +5
│   └── Task neutral to goal: +0
└── Multi-Goal Bonus:
    └── Task supports 2+ goals: +3 extra

Context Score (AI - 0 to 5 points):
├── Meeting Proximity:
│   ├── After meeting, before important meeting: -3 (e.g., workout before client call)
│   ├── After meeting, energizing task: +5 (e.g., walk after long meeting)
│   ├── Before meeting, prep task: +3 (e.g., hydration before presentation)
│   └── No nearby meetings: +0
└── Calendar Event Type:
    ├── After recurring event (reliable): +2
    └── Before one-off event: +0

Maximum Possible Score: 48 points
```

### Assignment Algorithm

**Greedy Approach with Backtracking**:

```
1. Generate all (task, slot) pairs
2. Score each pair (see formula above)
3. Sort pairs by score (descending)
4. FOR each task (in order of total score sum):
   a. Select highest-scored available slot
   b. Assign task to slot
   c. Update slot availability (reduce available time)
   d. IF slot now too small for remaining tasks:
      - Mark slot as "full"
   e. Re-score remaining tasks (slots changed)
5. IF any tasks unassigned:
   - Use fallback: place at original AI-suggested time
   - Flag as "low confidence" placement
6. Return all assigned tasks
```

**Why Greedy Works**:
- High-scored tasks get priority (important + high-success tasks first)
- Slot availability dynamically updates (prevents conflicts)
- Re-scoring after each assignment (adapts to changing landscape)
- Fallback ensures all tasks get placed (never fail)

---

## DATABASE SCHEMA CHANGES

### New Table: `calendar_anchoring_results`

**Purpose**: Store metadata about anchoring operations

```sql
CREATE TABLE calendar_anchoring_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_result_id UUID NOT NULL REFERENCES holistic_analysis_results(id),
    profile_id TEXT NOT NULL,
    target_date DATE NOT NULL,

    -- Calendar data used
    calendar_events_count INTEGER,
    calendar_provider VARCHAR(50),  -- 'google', 'mock', 'none'

    -- Anchoring results
    total_tasks INTEGER,
    tasks_anchored INTEGER,
    tasks_rescheduled INTEGER,
    tasks_kept_original_time INTEGER,
    average_confidence_score FLOAT,

    -- Summary metadata (JSONB)
    anchoring_summary JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processing_time_ms INTEGER,

    CONSTRAINT unique_anchoring_per_plan UNIQUE(analysis_result_id, target_date)
);

CREATE INDEX idx_anchoring_results_profile ON calendar_anchoring_results(profile_id);
CREATE INDEX idx_anchoring_results_date ON calendar_anchoring_results(target_date);
```

**`anchoring_summary` JSONB Structure**:
```json
{
  "calendar_gaps_found": 8,
  "total_available_minutes": 870,
  "algorithm_version": "hybrid_v1.0",
  "ai_models_used": ["gpt-4", "gpt-4o-mini"],
  "pattern_analysis_used": true,
  "habit_stacking_applied": 7,
  "conflicts_detected": 0,
  "fallback_placements": 1
}
```

---

### Modify Table: `plan_items`

**Add New Columns**:

```sql
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS is_anchored BOOLEAN DEFAULT false;
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS anchored_at TIMESTAMPTZ;
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS anchoring_metadata JSONB;
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS confidence_score FLOAT;

CREATE INDEX idx_plan_items_anchored ON plan_items(is_anchored);
```

**`anchoring_metadata` JSONB Structure**:
```json
{
  "original_time": "09:00:00",
  "anchored_time": "06:20:00",
  "time_adjustment_minutes": -160,
  "slot_id": "slot_001",
  "habit_stack": {
    "anchor_event": "Morning coffee",
    "anchor_time": "06:10:00",
    "reliability": 0.98,
    "phrase": "After coffee, do 15-min stretch"
  },
  "scoring_breakdown": {
    "base_score": 15,
    "pattern_score": 10,
    "habit_score": 10,
    "goal_score": 8,
    "context_score": 2,
    "total": 45
  },
  "ai_reasoning": "Excellent placement. Morning coffee (98% reliability) is strongest anchor...",
  "calendar_gap_used": {
    "gap_start": "06:00:00",
    "gap_end": "09:30:00",
    "gap_type": "morning_start"
  }
}
```

---

## API DESIGN

### New Endpoints

#### 1. Anchor Plan to Calendar

```
POST /api/anchoring/anchor-plan
```

**Request Body**:
```json
{
  "user_id": "user_sarah_123",
  "analysis_result_id": "uuid-of-generated-plan",
  "target_date": "2025-11-06",
  "options": {
    "use_mock_calendar": false,
    "force_reanchor": false,
    "enable_pattern_analysis": true,
    "enable_habit_stacking": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "anchoring_id": "uuid-anchoring-result",
  "message": "Plan successfully anchored",
  "summary": {
    "tasks_total": 10,
    "tasks_anchored": 10,
    "tasks_rescheduled": 7,
    "average_confidence": 0.88,
    "calendar_conflicts": 0
  },
  "anchored_plan_url": "/api/anchoring/results/{anchoring_id}"
}
```

**Status Codes**:
- 200: Success
- 400: Invalid analysis_result_id or date
- 404: No plan items found for analysis_result_id
- 500: Anchoring algorithm failure

---

#### 2. Get Anchoring Results

```
GET /api/anchoring/results/{anchoring_id}
```

**Response**:
```json
{
  "anchoring_id": "uuid",
  "analysis_result_id": "uuid-of-plan",
  "target_date": "2025-11-06",
  "anchored_tasks": [
    {
      "task_id": "uuid-task-001",
      "title": "Morning Stretch",
      "original_time": "09:00:00",
      "anchored_time": "06:20:00",
      "confidence_score": 0.94,
      "habit_stack": {
        "anchor": "Morning coffee at 6:10 AM",
        "phrase": "After coffee, do 15-min stretch"
      },
      "reasoning": "Morning coffee (98% reliability) is strongest anchor..."
    }
    // ... more tasks
  ],
  "summary": {/* anchoring summary */},
  "created_at": "2025-11-05T21:00:00Z"
}
```

---

#### 3. Get Calendar Events (Proxy to well-planned-api)

```
GET /api/anchoring/calendar-events/{user_id}
```

**Query Parameters**:
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `use_mock`: boolean (default: false)

**Purpose**: Allow frontend to preview calendar before anchoring

**Response**: Standardized calendar events format

---

#### 4. Simulate Anchoring (Preview Mode)

```
POST /api/anchoring/simulate
```

**Purpose**: Run anchoring algorithm WITHOUT updating database (preview only)

**Request**: Same as `/anchor-plan`

**Response**: Same format but includes `"simulation": true` flag

**Use Case**: User wants to see proposed changes before committing

---

## MOCK DATA TESTING STRATEGY

### Mock Calendar Generator

**Service Name**: `MockCalendarGenerator`
**Location**: `hos-agentic-ai-prod/services/testing/mock_calendar_generator.py`

#### Purpose

Generate realistic mock calendar data that mimics well-planned-api response format, enabling:
1. Development without Google Calendar connection
2. Automated testing of anchoring algorithm
3. Reproducible test scenarios

#### Mock Data Profiles

**Profile 1: Corporate Parent (Sarah)**
```python
{
  "profile_name": "corporate_parent_sarah",
  "events": [
    {
      "id": "mock_event_001",
      "title": "Wake up routine",
      "start_time": "06:00:00",
      "end_time": "06:45:00",
      "recurring": true,
      "reliability": 0.95
    },
    {
      "id": "mock_event_002",
      "title": "Breakfast with family",
      "start_time": "06:45:00",
      "end_time": "07:15:00",
      "recurring": true,
      "reliability": 0.90
    },
    {
      "id": "mock_event_003",
      "title": "Kids school drop-off",
      "start_time": "07:30:00",
      "end_time": "08:15:00",
      "recurring": true
    },
    {
      "id": "mock_event_004",
      "title": "Team Standup",
      "start_time": "09:30:00",
      "end_time": "10:00:00",
      "meeting_link": "https://meet.google.com/mock",
      "attendees": [{"email": "colleague@company.com"}]
    },
    {
      "id": "mock_event_005",
      "title": "Client Strategy Call",
      "start_time": "14:00:00",
      "end_time": "15:00:00",
      "meeting_link": "https://meet.google.com/mock2",
      "attendees": [{"email": "client@company.com"}]
    },
    {
      "id": "mock_event_006",
      "title": "Lunch break",
      "start_time": "12:30:00",
      "end_time": "13:15:00",
      "recurring": true
    },
    {
      "id": "mock_event_007",
      "title": "Kids pickup",
      "start_time": "17:30:00",
      "end_time": "18:00:00",
      "recurring": true
    },
    {
      "id": "mock_event_008",
      "title": "Family dinner",
      "start_time": "18:30:00",
      "end_time": "19:15:00",
      "recurring": true
    }
  ]
}
```

**Profile 2: Hybrid Athlete (Peak Performer)**
```python
{
  "profile_name": "hybrid_athlete_peak",
  "events": [
    {
      "id": "mock_event_101",
      "title": "Morning Run",
      "start_time": "05:30:00",
      "end_time": "06:30:00",
      "recurring": true
    },
    {
      "id": "mock_event_102",
      "title": "Gym Session",
      "start_time": "18:00:00",
      "end_time": "19:30:00",
      "recurring": true
    },
    {
      "id": "mock_event_103",
      "title": "Work Block",
      "start_time": "09:00:00",
      "end_time": "17:00:00"
    }
  ]
}
```

**Profile 3: Empty Calendar (Foundation Builder)**
```python
{
  "profile_name": "empty_calendar",
  "events": []
}
```

**Profile 4: Overscheduled (Stressed Professional)**
```python
{
  "profile_name": "overscheduled",
  "events": [
    # 12 meetings from 8 AM to 6 PM (very few gaps)
  ]
}
```

#### Usage

**In Code**:
```python
# Load mock profile
mock_generator = MockCalendarGenerator()
mock_events = mock_generator.generate_profile("corporate_parent_sarah", date="2025-11-06")

# Or generate random profile
random_events = mock_generator.generate_random_day(
    num_events=8,
    work_hours_start="09:00",
    work_hours_end="17:00"
)
```

**In API Request**:
```json
{
  "user_id": "test_user",
  "analysis_result_id": "uuid",
  "target_date": "2025-11-06",
  "options": {
    "use_mock_calendar": true,
    "mock_profile": "corporate_parent_sarah"
  }
}
```

#### Mock Response Format

**Exactly Matches well-planned-api Format**:
```json
{
  "success": true,
  "events": [
    {
      "id": "mock_event_001",
      "title": "Team Standup",
      "description": "",
      "start_time": "2025-11-06T09:30:00Z",
      "end_time": "2025-11-06T10:00:00Z",
      "location": "",
      "meeting_link": "https://meet.google.com/mock",
      "meeting_provider": "google_meet",
      "attendees": [{"email": "colleague@company.com", "name": "John Doe"}],
      "status": "confirmed"
    }
  ],
  "count": 8,
  "_mock_data": true
}
```

---

### Testing Scenarios

#### Test Case 1: Basic Anchoring (Happy Path)

**Inputs**:
- Mock Profile: `corporate_parent_sarah` (8 calendar events)
- Plan: 10 tasks (generated from AI)
- Target Date: 2025-11-06

**Expected Outputs**:
- All 10 tasks anchored successfully
- 7+ tasks rescheduled (moved from AI suggestions)
- 8+ available time slots identified
- Average confidence score > 0.80
- Zero conflicts with calendar events

**Validation**:
- No task overlaps with calendar events
- All tasks have `is_anchored = true`
- All tasks have `anchoring_metadata` populated
- Database `calendar_anchoring_results` has 1 new row

---

#### Test Case 2: Empty Calendar

**Inputs**:
- Mock Profile: `empty_calendar` (0 events)
- Plan: 10 tasks
- Target Date: 2025-11-06

**Expected Outputs**:
- All 10 tasks keep original AI-suggested times (no rescheduling needed)
- 1 large available slot (6 AM - 10 PM)
- Average confidence score > 0.70 (lower due to no habit stacking)
- Algorithm completes in <1 second (no AI calls needed)

---

#### Test Case 3: Overscheduled Day

**Inputs**:
- Mock Profile: `overscheduled` (12 meetings, few gaps)
- Plan: 10 tasks (total 120 minutes)
- Target Date: 2025-11-06

**Expected Outputs**:
- 8-10 tasks anchored (some may fail to find slots)
- Tasks placed in small gaps (15-30 minute slots)
- Average confidence score < 0.70 (suboptimal placements)
- Warning: "Limited time available, some tasks may not fit ideally"

**Fallback Behavior**:
- If task doesn't fit any gap, place at original time with warning
- Flag as "potential conflict" in metadata

---

#### Test Case 4: Pattern Analysis Integration

**Inputs**:
- Mock Profile: `corporate_parent_sarah`
- Plan: 10 tasks
- User has 30 days of check-in history (mocked)
- Historical patterns show: morning 85%, evening 40%

**Expected Outputs**:
- 7+ tasks moved to morning window (6-9 AM)
- 0-2 tasks in evening window (avoid low-compliance time)
- Habit stacking applied to 5+ tasks
- Average confidence score > 0.85

---

#### Test Case 5: Habit Stacking

**Inputs**:
- Mock Profile: `corporate_parent_sarah`
- Plan includes: "Morning Hydration" task
- Calendar has: "Breakfast at 6:45 AM" (recurring, reliable)

**Expected Outputs**:
- "Morning Hydration" anchored at 7:20 AM (right after breakfast)
- `anchoring_metadata.habit_stack` contains:
  ```json
  {
    "anchor_event": "Breakfast with family",
    "anchor_time": "06:45:00",
    "phrase": "Right after breakfast, drink full glass of water",
    "reliability": 0.90
  }
  ```
- Habit score = 10 (strong anchor)

---

### Test Suite Structure

```
/testing/anchoring/
├── test_calendar_integration.py
│   ├── test_fetch_calendar_events_from_well_planned_api()
│   ├── test_mock_calendar_generator()
│   └── test_calendar_connection_fallback()
├── test_calendar_gap_finder.py
│   ├── test_find_gaps_corporate_parent()
│   ├── test_find_gaps_empty_calendar()
│   └── test_find_gaps_overscheduled()
├── test_anchoring_algorithm.py
│   ├── test_basic_anchoring_happy_path()
│   ├── test_anchoring_with_pattern_analysis()
│   ├── test_anchoring_with_habit_stacking()
│   └── test_anchoring_scoring_formula()
├── test_database_updates.py
│   ├── test_update_plan_items_with_anchored_times()
│   ├── test_create_anchoring_results_record()
│   └── test_transaction_rollback_on_error()
└── test_api_endpoints.py
    ├── test_anchor_plan_endpoint()
    ├── test_get_anchoring_results_endpoint()
    └── test_simulate_anchoring_endpoint()
```

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1)

**Goal**: Basic infrastructure without AI

**Tasks**:
1. Create `CalendarIntegrationService`
   - Implement `fetch_calendar_events()` with well-planned-api integration
   - Implement fallback to mock data
   - Handle authentication errors
2. Create `MockCalendarGenerator`
   - Implement 4 mock profiles
   - Match well-planned-api response format exactly
3. Create `CalendarGapFinder`
   - Implement basic gap detection algorithm
   - Handle edge cases (no gaps, very small gaps)
4. Create `TaskLoaderService`
   - Query plan_items by analysis_result_id
   - Include time_blocks context
5. Create database migration
   - Add `calendar_anchoring_results` table
   - Add columns to `plan_items` (is_anchored, anchoring_metadata, etc.)

**Deliverables**:
- Services can fetch calendar events (real or mock)
- Services can identify time gaps
- Services can load plan_items
- Database schema updated

**Testing**:
- Unit tests for each service
- Integration test: fetch mock calendar → find gaps → load tasks

---

### Phase 2: Algorithmic Anchoring (Week 2)

**Goal**: Working anchoring without AI (pure algorithm)

**Tasks**:
1. Create `BasicScorerService`
   - Implement scoring formula (algorithmic portion only)
   - Duration fit, time window match, priority alignment
2. Create `GreedyAssignmentService`
   - Implement greedy assignment algorithm
   - Handle slot availability updates
   - Implement fallback for unassigned tasks
3. Create `AnchoringCoordinator`
   - Orchestrate: load tasks → find gaps → score → assign
   - Update database with anchored times
   - Create anchoring_results record
4. Create API endpoint: `POST /api/anchoring/anchor-plan`
   - Wire up all services
   - Return anchoring results
5. Create API endpoint: `GET /api/anchoring/results/{anchoring_id}`

**Deliverables**:
- End-to-end anchoring flow (algorithmic only)
- API endpoints functional
- Database updates working

**Testing**:
- Test Case 1 (Happy Path) passes
- Test Case 2 (Empty Calendar) passes
- Test Case 3 (Overscheduled) passes

---

### Phase 3: AI Enhancement (Week 3)

**Goal**: Add AI-powered scoring (patterns, habit stacking, context)

**Tasks**:
1. Create `PatternAnalyzerService`
   - Load historical check-ins
   - Call OpenAI GPT-4 for pattern analysis
   - Cache results (24 hours)
2. Create `HabitStackingEngine`
   - Identify nearby calendar events
   - Call OpenAI GPT-4o-mini for habit stack recommendations
   - Apply Atomic Habits 4 Laws
3. Create `MeetingContextScorer`
   - Analyze meeting importance (attendees, duration, title keywords)
   - Call OpenAI GPT-4o-mini for context scoring
4. Update `AnchoringCoordinator`
   - Integrate AI services
   - Combine algorithmic + AI scores
5. Update API endpoint options:
   - `enable_pattern_analysis`: boolean
   - `enable_habit_stacking`: boolean

**Deliverables**:
- AI services integrated
- Hybrid scoring working
- Pattern analysis functional

**Testing**:
- Test Case 4 (Pattern Analysis) passes
- Test Case 5 (Habit Stacking) passes
- Verify AI API costs < $0.05 per anchoring

---

### Phase 4: Testing & Refinement (Week 4)

**Goal**: Production-ready quality

**Tasks**:
1. Comprehensive test suite
   - All 5 test cases pass
   - Edge case coverage (empty plan, single task, etc.)
   - Performance tests (< 5 seconds per anchoring)
2. Error handling improvements
   - Network failures
   - AI API failures
   - Database transaction rollbacks
3. Logging & monitoring
   - Structured logs for debugging
   - Metrics: success rate, average confidence, processing time
4. Documentation
   - API documentation
   - Service documentation
   - Usage examples
5. Frontend preview (optional)
   - Show calendar events + proposed anchoring
   - User approves before committing

**Deliverables**:
- 95%+ test coverage
- Production-ready error handling
- Complete documentation

**Testing**:
- Load testing (100 concurrent anchoring requests)
- Stress testing (1000 tasks, 50 calendar events)
- Failure recovery testing (API downtime scenarios)

---

## ERROR HANDLING & EDGE CASES

### Error Scenarios

#### 1. Well-Planned-API Unavailable

**Scenario**: Network timeout or service down

**Handling**:
```python
try:
    events = await calendar_service.fetch_calendar_events(user_id, date)
except NetworkError:
    logger.warning("well-planned-api unavailable, using mock data")
    events = mock_generator.generate_profile("corporate_parent_sarah", date)
except AuthenticationError:
    logger.info("User has not connected Google Calendar")
    events = []  # Proceed with empty calendar
```

**User Impact**: Minimal (fallback to mock data or empty calendar)

---

#### 2. No Plan Items Found

**Scenario**: Invalid `analysis_result_id` or no tasks in database

**Handling**:
```python
plan_items = await task_loader.load_plan_items(analysis_result_id)
if not plan_items:
    raise HTTPException(
        status_code=404,
        detail="No plan items found for analysis_result_id"
    )
```

**User Impact**: API returns 404, frontend shows error message

---

#### 3. AI API Failure

**Scenario**: OpenAI API timeout or rate limit

**Handling**:
```python
try:
    patterns = await ai_service.analyze_patterns(user_id)
except OpenAIError:
    logger.warning("AI pattern analysis failed, using defaults")
    patterns = UserPatterns(default_values)
    # Continue with algorithmic scoring only
```

**User Impact**: Anchoring still completes (fallback to algorithmic only)

---

#### 4. No Available Time Slots

**Scenario**: Calendar fully booked, no gaps for tasks

**Handling**:
```python
available_slots = gap_finder.find_gaps(calendar_events)
if not available_slots:
    logger.warning("No available time slots, using original times")
    # Place tasks at AI-suggested times (may conflict)
    # Flag in metadata: "conflict_warning": true
```

**User Impact**: Tasks placed at original times with conflict warning

---

#### 5. Database Transaction Failure

**Scenario**: Constraint violation or connection loss during update

**Handling**:
```python
async with db_transaction():
    try:
        await update_plan_items(anchored_tasks)
        await create_anchoring_result(summary)
        await commit()
    except DatabaseError:
        await rollback()
        logger.error("Database update failed, rolling back")
        raise HTTPException(500, "Anchoring failed, please retry")
```

**User Impact**: API returns 500, no partial updates (atomic operation)

---

### Edge Cases

#### Edge Case 1: Single Task

**Scenario**: Plan has only 1 task

**Handling**: Algorithm still runs (finds best slot for single task)

**Expected**: Completes in <1 second

---

#### Edge Case 2: Tasks Longer Than Gaps

**Scenario**: Task needs 60 min, largest gap is 45 min

**Handling**:
- Split task into multiple slots (if splittable)
- OR place at original time with warning
- Flag in metadata: `"placement_quality": "suboptimal"`

---

#### Edge Case 3: Duplicate Analysis Result ID

**Scenario**: User triggers anchoring twice for same plan

**Handling**:
- Check `force_reanchor` flag
- If false: return existing anchoring result
- If true: re-run algorithm, overwrite old result

---

#### Edge Case 4: Future Date Without Calendar

**Scenario**: User requests anchoring for date 7 days ahead (no calendar events yet)

**Handling**:
- Proceed with empty calendar
- Flag in metadata: `"calendar_data_incomplete": true`
- User can re-anchor later when calendar populated

---

## NEXT STEPS

### Immediate Actions

1. **Review this design document** with team
2. **Approve architecture** and approach
3. **Set up project structure** in hos-agentic-ai-prod
4. **Create GitHub issues** for each phase
5. **Assign developers** to phases
6. **Start Phase 1** (Foundation)

### Success Criteria

**MVP (End of Phase 2)**:
- [ ] Can fetch calendar events from well-planned-api
- [ ] Can generate mock calendar data
- [ ] Can find available time gaps
- [ ] Can anchor tasks using algorithmic scoring
- [ ] API endpoint returns anchored plan
- [ ] Database updates successfully

**Full Release (End of Phase 4)**:
- [ ] AI pattern analysis working
- [ ] Habit stacking functional
- [ ] 95%+ test coverage
- [ ] <5 seconds per anchoring operation
- [ ] <$0.05 AI cost per anchoring
- [ ] Production documentation complete

---

**END OF DESIGN DOCUMENT**

*Next: Begin Phase 1 implementation*
