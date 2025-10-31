# FeedbackAnalyzerService - Data Flow & Logic
**Date:** 2025-10-28

---

## Executive Summary

**FeedbackAnalyzerService** analyzes user feedback from existing engagement tables (not separate feedback tables). It uses SQL views to combine data from `plan_items` and `task_checkins` for intelligent task selection.

**Key Insight:** No separate feedback storage needed - it reads from the existing user engagement system!

---

## Core Tables & Views

### Base Tables (Already Exist)

#### 1. `plan_items` (User's Daily Plans)
**Purpose:** Stores all tasks in user's daily plan

**Columns Used by Feedback System:**
```sql
id UUID                          -- Primary key
profile_id TEXT                  -- User ID
title TEXT                       -- Task name
task_type VARCHAR(50)            -- wellness, nutrition, exercise, etc.
estimated_duration_minutes INT   -- Task duration
priority_level VARCHAR(10)       -- high, medium, low
scheduled_time TIME              -- When task is scheduled
category VARCHAR(50)             -- NEW: hydration, movement, nutrition, etc.
subcategory VARCHAR(50)          -- NEW: Finer categorization
task_library_id UUID             -- NEW: Links to task_library (NULL for AI tasks)
source VARCHAR(20)               -- NEW: 'ai', 'library', 'hybrid'
variation_group VARCHAR(100)     -- NEW: For task rotation (e.g., hydration_variations)
```

**How it's populated:**
- AI generates plan → Tasks extracted → Inserted into `plan_items`
- Each task gets `source='ai'` initially
- **Option B will set `source='library'` for pre-selected tasks**

---

#### 2. `task_checkins` (User Feedback on Tasks)
**Purpose:** Stores user feedback when they complete/skip tasks

**Columns:**
```sql
id UUID                          -- Primary key
profile_id TEXT                  -- User ID
plan_item_id UUID                -- Links to plan_items.id
analysis_result_id UUID          -- Links to holistic_analysis_results
completion_status VARCHAR(20)    -- 'completed', 'partial', 'skipped'
satisfaction_rating INT          -- 1-5 rating (NULL if not rated)
planned_date DATE                -- When task was planned
completed_at TIMESTAMP           -- When user completed/skipped it
user_notes TEXT                  -- Optional user comment
user_mode VARCHAR(20)            -- NEW: Energy mode at task time (low/medium/high)
user_archetype VARCHAR(50)       -- NEW: Active archetype (foundation_builder, etc.)
day_of_week INTEGER              -- NEW: 0=Sunday, 6=Saturday
```

**How it's populated:**
- User completes/skips task in app → App calls engagement endpoint
- Feedback stored in `task_checkins`
- **This is the primary source of user feedback!**

---

### SQL Views (Auto-Generated from Tables)

#### 1. `task_feedback_complete` (Complete Feedback with Task Details)
**Purpose:** Joins `task_checkins` + `plan_items` for easy querying

**Created by:**
```sql
CREATE OR REPLACE VIEW task_feedback_complete AS
SELECT
    tc.id as checkin_id,
    tc.profile_id,
    tc.plan_item_id,
    tc.completion_status,
    tc.satisfaction_rating,
    tc.planned_date,
    tc.completed_at,
    tc.user_notes,
    tc.user_mode,
    tc.user_archetype,
    tc.day_of_week,
    -- FROM plan_items:
    pi.task_library_id,
    pi.title as task_name,
    pi.task_type,
    pi.category,
    pi.subcategory,
    pi.variation_group,
    pi.source,
    pi.scheduled_time,
    pi.estimated_duration_minutes,
    pi.priority_level
FROM task_checkins tc
JOIN plan_items pi ON tc.plan_item_id = pi.id;
```

**What it provides:**
- Single view with both feedback AND task details
- Used by FeedbackAnalyzerService for all queries
- Example row:
  ```json
  {
    "checkin_id": "uuid",
    "profile_id": "user123",
    "task_name": "Morning Lemon Water",
    "category": "hydration",
    "task_library_id": "uuid",  // NULL if AI-generated
    "completion_status": "completed",
    "satisfaction_rating": 5,
    "source": "library",  // or "ai"
    "user_mode": "medium",
    "user_archetype": "foundation_builder"
  }
  ```

---

#### 2. `user_preference_summary` (Aggregated User Stats by Category)
**Purpose:** Aggregate statistics per user per category

**Created by:**
```sql
CREATE OR REPLACE VIEW user_preference_summary AS
SELECT
    pi.profile_id,
    pi.category,
    COUNT(*) as tasks_seen,
    COUNT(CASE WHEN tc.completion_status = 'completed' THEN 1 END) as tasks_completed,
    ROUND(tasks_completed::NUMERIC / NULLIF(COUNT(*), 0), 3) as completion_rate,
    ROUND(AVG(tc.satisfaction_rating), 2) as avg_satisfaction,
    COUNT(DISTINCT pi.task_library_id) as unique_library_tasks,
    MAX(tc.completed_at) as last_activity
FROM plan_items pi
LEFT JOIN task_checkins tc ON pi.id = tc.plan_item_id
WHERE pi.category IS NOT NULL
GROUP BY pi.profile_id, pi.category;
```

**What it provides:**
- Per-category performance metrics
- Example row:
  ```json
  {
    "profile_id": "user123",
    "category": "hydration",
    "tasks_seen": 15,
    "tasks_completed": 12,
    "completion_rate": 0.800,
    "avg_satisfaction": 4.5,
    "unique_library_tasks": 3,
    "last_activity": "2025-10-28T10:30:00Z"
  }
  ```

---

#### 3. `library_task_performance` (Task-Level Performance)
**Purpose:** Performance metrics for each library task

**Created by:**
```sql
CREATE OR REPLACE VIEW library_task_performance AS
SELECT
    pi.task_library_id,
    pi.title,
    pi.category,
    COUNT(*) as total_assignments,
    COUNT(CASE WHEN tc.completion_status = 'completed' THEN 1 END) as completed_count,
    ROUND(AVG(tc.satisfaction_rating), 2) as avg_satisfaction,
    MAX(tc.completed_at) as last_completed
FROM plan_items pi
LEFT JOIN task_checkins tc ON pi.id = tc.plan_item_id
WHERE pi.task_library_id IS NOT NULL
GROUP BY pi.task_library_id, pi.title, pi.category;
```

**What it provides:**
- How well each library task performs across all users
- Example row:
  ```json
  {
    "task_library_id": "uuid",
    "title": "Morning Lemon Water",
    "category": "hydration",
    "total_assignments": 50,
    "completed_count": 42,
    "avg_satisfaction": 4.7,
    "last_completed": "2025-10-28T08:00:00Z"
  }
  ```

---

## FeedbackAnalyzerService Methods

### Method 1: `get_user_feedback(user_id, days, category)`
**Purpose:** Get raw feedback records for a user

**SQL:**
```sql
SELECT * FROM task_feedback_complete
WHERE profile_id = $1
  AND planned_date >= NOW() - INTERVAL '30 days'
  AND category = $2  -- optional
ORDER BY planned_date DESC
```

**Returns:**
```python
[
    {
        'checkin_id': 'uuid',
        'task_name': 'Morning Lemon Water',
        'category': 'hydration',
        'completion_status': 'completed',
        'satisfaction_rating': 5,
        'task_library_id': 'uuid',  # or None
        'source': 'library',  # or 'ai'
        ...
    },
    ...
]
```

**Use case:** Get all feedback for analysis

---

### Method 2: `get_user_preferences(user_id)`
**Purpose:** Get aggregated preferences and determine learning phase

**SQL:**
```sql
SELECT * FROM user_preference_summary
WHERE profile_id = $1
ORDER BY avg_satisfaction DESC NULLS LAST, tasks_completed DESC
```

**Logic:**
1. Queries `user_preference_summary` view
2. Calculates total completion rate across all categories
3. Determines learning phase:
   - **Discovery:** <50 tasks seen
   - **Establishment:** 50-199 tasks seen
   - **Mastery:** ≥200 tasks seen
4. Builds category affinity dict

**Returns:**
```python
{
    'user_id': 'user123',
    'total_tasks_completed': 45,
    'total_tasks_seen': 60,
    'avg_completion_rate': 0.75,
    'avg_satisfaction_rating': 4.2,
    'current_learning_phase': 'discovery',  # or 'establishment', 'mastery'
    'category_affinity': {
        'hydration': 0.90,  # 90% completion rate
        'movement': 0.70,
        'nutrition': 0.65
    },
    'categories': [...]  # Detailed breakdown
}
```

**Use case:** AdaptiveTaskSelector uses this to determine selection strategy

---

### Method 3: `get_user_favorites(user_id, category, min_rating, min_completions)`
**Purpose:** Get user's favorite tasks (high-rated, frequently completed)

**SQL:**
```sql
SELECT
    task_library_id,
    task_name,
    category,
    COUNT(*) as completion_count,
    AVG(satisfaction_rating) as avg_rating
FROM task_feedback_complete
WHERE profile_id = $1
  AND task_library_id IS NOT NULL  -- Only library tasks
  AND completion_status = 'completed'
  AND satisfaction_rating >= 4  -- High-rated only
GROUP BY task_library_id, task_name, category
HAVING COUNT(*) >= 2  -- Completed at least 2 times
ORDER BY avg_rating DESC, completion_count DESC
```

**Returns:**
```python
[
    {
        'task_library_id': 'uuid',
        'task_name': 'Morning Lemon Water',
        'category': 'hydration',
        'completion_count': 8,
        'avg_rating': 4.88,
        'source': 'library'
    },
    ...
]
```

**Use case:** Select proven tasks for establishment/mastery phases

---

### Method 4: `get_category_performance(user_id, days)`
**Purpose:** Get performance breakdown by category

**SQL:**
```sql
SELECT
    category,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as completed,
    AVG(satisfaction_rating) as avg_satisfaction
FROM task_feedback_complete
WHERE profile_id = $1
  AND planned_date >= NOW() - INTERVAL '30 days'
GROUP BY category
```

**Returns:**
```python
{
    'hydration': {
        'total_tasks': 15,
        'completed': 12,
        'completion_rate': 0.80,
        'avg_satisfaction': 4.5
    },
    'movement': {
        'total_tasks': 20,
        'completed': 14,
        'completion_rate': 0.70,
        'avg_satisfaction': 3.8
    }
}
```

**Use case:** Understand which categories user engages with most

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1. AI generates plan
                              ▼
                    ┌──────────────────┐
                    │   plan_items     │
                    │  (Daily tasks)   │
                    │                  │
                    │ - task_library_id│ ← Links to library
                    │ - source         │ ← 'ai' or 'library'
                    │ - category       │
                    │ - title          │
                    └──────────────────┘
                              │
                              │ 2. User completes/skips task
                              ▼
                    ┌──────────────────┐
                    │  task_checkins   │
                    │   (Feedback)     │
                    │                  │
                    │ - completion_status
                    │ - satisfaction_rating
                    │ - user_mode      │
                    │ - user_archetype │
                    └──────────────────┘
                              │
                              │ 3. Views join the data
                              ▼
        ┌───────────────────────────────────────────────┐
        │                 SQL VIEWS                      │
        ├───────────────────────────────────────────────┤
        │                                               │
        │  task_feedback_complete                      │
        │  (Combines plan_items + task_checkins)       │
        │  ↓                                            │
        │  Used by: get_user_feedback(),               │
        │          get_user_favorites(),               │
        │          get_category_performance()          │
        │                                               │
        │  user_preference_summary                     │
        │  (Aggregates by category)                    │
        │  ↓                                            │
        │  Used by: get_user_preferences()             │
        │          (determines learning phase)          │
        │                                               │
        │  library_task_performance                    │
        │  (Aggregates by task_library_id)             │
        │  ↓                                            │
        │  Used by: get_library_task_performance()     │
        │                                               │
        └───────────────────────────────────────────────┘
                              │
                              │ 4. FeedbackAnalyzerService queries views
                              ▼
                    ┌──────────────────┐
                    │ AdaptiveTask     │
                    │ Selector         │
                    │                  │
                    │ Uses feedback to │
                    │ select best tasks│
                    └──────────────────┘
                              │
                              │ 5. TaskPreseeder uses AdaptiveTaskSelector
                              ▼
                    ┌──────────────────┐
                    │ TaskPreseeder    │
                    │ (Option B)       │
                    │                  │
                    │ Selects 5-8 tasks│
                    │ for AI prompt    │
                    └──────────────────┘
```

---

## Learning Phase Logic

**Determined by:** Total tasks seen (from `user_preference_summary`)

```python
def _determine_learning_phase(self, total_tasks: int) -> str:
    if total_tasks < 50:
        return "discovery"      # Week 1-2: Explore variety
    elif total_tasks < 200:
        return "establishment"  # Week 3-8: Build consistency
    else:
        return "mastery"        # Week 9+: Optimize personalization
```

**How it's used:**
- **Discovery:** AdaptiveTaskSelector picks 80% untried, 20% tried
- **Establishment:** 70% favorites, 30% exploration
- **Mastery:** 85% proven, 15% novelty

---

## Key Insights

### 1. No Separate Feedback Tables
✅ **Uses existing engagement system** (`task_checkins`)
- No duplication
- Single source of truth
- Existing app already collects this data

### 2. Views Do the Heavy Lifting
✅ **SQL views combine data automatically**
- `task_feedback_complete` joins tables
- `user_preference_summary` aggregates stats
- No manual aggregation needed in Python

### 3. Flexible Querying
✅ **Can filter by:**
- Category (hydration, movement, etc.)
- Date range (last 7/30/90 days)
- Task source (library vs AI)
- Satisfaction rating (≥4 for favorites)
- Completion status (completed, partial, skipped)

### 4. Real-Time Analysis
✅ **Always up-to-date**
- Views automatically reflect latest feedback
- No cache invalidation needed
- Query anytime for current state

---

## Example User Journey

**Day 1:**
```
1. AI generates 12 tasks → Inserted into plan_items (source='ai')
2. User completes 8 tasks → Feedback saved to task_checkins
3. task_feedback_complete view shows: 8 completed tasks
4. user_preference_summary shows: tasks_seen=12, learning_phase='discovery'
```

**Day 2:**
```
5. TaskPreseeder checks feedback count: 8 tasks (≥3 required) ✓
6. FeedbackAnalyzerService.get_user_preferences() returns learning_phase='discovery'
7. AdaptiveTaskSelector selects 5 library tasks (80% untried)
8. AI receives pre-selected tasks + generates plan
9. Plan extracted → 5 tasks marked source='library', 7 tasks source='ai'
```

**Day 30:**
```
10. User has completed 60 tasks total
11. learning_phase transitions to 'establishment'
12. AdaptiveTaskSelector now picks 70% favorites, 30% exploration
13. High-rated library tasks (4-5 stars) prioritized
```

---

## Summary

**FeedbackAnalyzerService is smart and efficient:**

✅ **No duplicate data** - Uses existing `task_checkins` table
✅ **SQL views do aggregation** - Fast, automatic, always fresh
✅ **Flexible querying** - Filter by category, rating, date, etc.
✅ **Learning phase logic** - Adapts strategy based on user experience
✅ **Ready for Option B** - All infrastructure exists!

**Tables involved:**
1. `plan_items` (tasks)
2. `task_checkins` (feedback)
3. `task_feedback_complete` (view)
4. `user_preference_summary` (view)
5. `library_task_performance` (view)

**Next step for Option B:** Create TaskPreseeder that uses FeedbackAnalyzerService + AdaptiveTaskSelector!
