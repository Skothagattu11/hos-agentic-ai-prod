# 🚀 HolisticOS Dynamic Personalization Implementation Plan
## Production-Grade, Phased Rollout Strategy

**Document Version:** 1.0
**Created:** 2025-10-24
**Owner:** CTO/Lead Engineer
**Goal:** Dynamic personalization without breaking existing system
**Approach:** Incremental, backwards-compatible, data-driven

---

## 📊 CURRENT STATE ASSESSMENT

### Existing Flutter App Capabilities ✅

```
hos_app/
├── Daily Journal (feedback collection) ✅
├── Task Completion Tracking ✅
├── Streak System ✅
├── Insights Display ✅
└── Calendar Integration ✅
```

### Existing Backend Infrastructure ✅

```
hos-agentic-ai-prod/
├── BehaviorAnalysisService ✅
├── CircadianAnalysisService ✅
├── RoutineGenerationService ✅
├── InsightsExtractionService ✅
└── OnDemandAnalysisService (50-item threshold) ✅
```

### Existing Database Schema ✅

```sql
-- Already exists
holistic_analysis_results  -- Stores AI analysis outputs
plan_items                 -- Individual tasks from plans
time_blocks               -- Time block structure
holistic_insights         -- Extracted insights
```

---

## 🎯 MVP SCOPE: "Intelligent Variety Engine"

### Core MVP Features (Phase 1)

**What User Gets:**
1. ✅ Task variety (no more repetitive plans)
2. ✅ Pattern-based adaptation (system learns from completions)
3. ✅ Weekly personalization summary
4. ✅ Mode-aware plan adjustments

**What User DOESN'T Get (Post-MVP):**
- ❌ Advanced gamification
- ❌ Social features
- ❌ Seasonal/weather integration
- ❌ Predictive scheduling

**Business Value:**
- 30-40% increase in task completion rates
- Higher user retention (personalized = sticky)
- Clear differentiation from competitors

---

## 🏗️ ARCHITECTURE OVERVIEW

### System Components

```
Flutter App (hos_app)
    ↓ (existing API calls)
RoutineApiService
    ↓ (new endpoints)
hos-agentic-ai-prod (Port 8002)
    ↓
[NEW] DynamicPlanGenerator
    ├─ TaskLibraryService (new)
    ├─ UserPreferenceEngine (new)
    ├─ FeedbackAnalyzer (new)
    └─ RoutineGenerationService (modified)
    ↓
Database (Supabase PostgreSQL)
    ├─ task_library (new table)
    ├─ user_task_feedback (new table)
    ├─ user_preference_profile (new table)
    └─ plan_items (existing, modified)
```

### Design Principles

1. **Backwards Compatibility:** Existing API contracts remain unchanged
2. **Feature Flags:** All new features toggle-able via environment variables
3. **Graceful Degradation:** System falls back to static plans if dynamic fails
4. **Zero Breaking Changes:** Existing users unaffected during rollout
5. **Incremental Data Migration:** No big-bang migrations

---

## 📅 PHASED IMPLEMENTATION PLAN

---

## **PHASE 1: FOUNDATION (Week 1-2)**
### Goal: Build task variety without breaking existing system

### Backend Work

#### 1.1 Database Schema (Day 1-2)

**New Tables:**

```sql
-- Task Library: Master list of all possible tasks
CREATE TABLE task_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL, -- 'hydration', 'movement', 'nutrition', 'wellness', 'recovery', 'work', 'focus'
    subcategory VARCHAR(50), -- 'outdoor', 'indoor', 'yoga', 'cardio', etc.
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    duration_minutes INT NOT NULL,
    difficulty VARCHAR(20) CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),

    -- Archetype compatibility (0.0 - 1.0 fit score)
    archetype_fit JSONB NOT NULL DEFAULT '{
        "Foundation Builder": 0.5,
        "Transformation Seeker": 0.5,
        "Peak Performer": 0.5,
        "Systematic Improver": 0.5,
        "Resilience Rebuilder": 0.5,
        "Connected Explorer": 0.5
    }',

    -- Mode compatibility
    mode_fit JSONB NOT NULL DEFAULT '{
        "high": 0.5,
        "medium": 0.5,
        "low": 0.5
    }',

    -- Task properties
    tags JSONB DEFAULT '[]', -- ['outdoor', 'social', 'quiet', 'energizing']
    variation_group VARCHAR(100), -- Groups related tasks (e.g., 'morning_hydration')

    -- Metadata
    time_of_day_preference VARCHAR(20), -- 'morning', 'afternoon', 'evening', 'any'
    equipment_needed JSONB DEFAULT '[]', -- ['yoga mat', 'weights']

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_task_library_category ON task_library(category);
CREATE INDEX idx_task_library_difficulty ON task_library(difficulty);
CREATE INDEX idx_task_library_variation_group ON task_library(variation_group);


-- User Task Feedback: Track every interaction
CREATE TABLE user_task_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    task_library_id UUID REFERENCES task_library(id),
    plan_item_id UUID, -- Links to existing plan_items table

    -- Scheduled vs actual
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,

    -- Completion tracking
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_early_minutes INT, -- negative if late

    -- Explicit feedback (optional)
    satisfaction_rating INT CHECK (satisfaction_rating BETWEEN 1 AND 5),
    user_notes TEXT,

    -- Implicit feedback
    skipped BOOLEAN DEFAULT FALSE,
    skip_reason VARCHAR(50), -- 'too_hard', 'no_time', 'not_interested', 'forgot'
    modified_by_user BOOLEAN DEFAULT FALSE, -- Did they edit the task?

    -- Context
    mode_at_time VARCHAR(20), -- 'high', 'medium', 'low'
    weather VARCHAR(50), -- Future: weather API integration

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_task_feedback_user_id ON user_task_feedback(user_id);
CREATE INDEX idx_user_task_feedback_scheduled_date ON user_task_feedback(scheduled_date);
CREATE INDEX idx_user_task_feedback_completed ON user_task_feedback(completed);


-- User Preference Profile: Learned preferences
CREATE TABLE user_preference_profile (
    user_id UUID PRIMARY KEY,
    archetype VARCHAR(50) NOT NULL,

    -- Learned preferences (0.0 - 1.0 affinity scores)
    category_affinity JSONB DEFAULT '{
        "hydration": 0.5,
        "movement": 0.5,
        "nutrition": 0.5,
        "wellness": 0.5,
        "recovery": 0.5,
        "work": 0.5,
        "focus": 0.5
    }',

    subcategory_affinity JSONB DEFAULT '{}', -- e.g., {"outdoor": 0.85, "yoga": 0.3}

    -- Behavioral patterns
    time_of_day_performance JSONB DEFAULT '{
        "morning": 0.5,
        "afternoon": 0.5,
        "evening": 0.5
    }',

    complexity_tolerance FLOAT DEFAULT 0.5, -- 0 = prefers simple, 1 = handles complex
    variety_seeking_score FLOAT DEFAULT 0.5, -- 0 = routine-lover, 1 = explorer

    -- Current state
    current_mode VARCHAR(20) DEFAULT 'medium',
    learning_phase VARCHAR(20) DEFAULT 'discovery', -- 'discovery', 'establishment', 'mastery'

    -- Statistics
    total_tasks_completed INT DEFAULT 0,
    total_tasks_scheduled INT DEFAULT 0,
    completion_rate FLOAT DEFAULT 0.0,
    longest_streak INT DEFAULT 0,
    current_streak INT DEFAULT 0,

    -- Discovery phase tracking
    unique_tasks_tried INT DEFAULT 0,
    discovery_start_date DATE,

    -- Metadata
    profile_confidence FLOAT DEFAULT 0.0, -- 0-1, how confident we are in preferences
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_preference_profile_archetype ON user_preference_profile(archetype);
CREATE INDEX idx_user_preference_profile_learning_phase ON user_preference_profile(learning_phase);


-- Task Rotation State: Prevent repetition
CREATE TABLE task_rotation_state (
    user_id UUID NOT NULL,
    variation_group VARCHAR(100) NOT NULL,
    last_used_date DATE NOT NULL,
    task_library_id UUID REFERENCES task_library(id),
    times_used INT DEFAULT 1,

    PRIMARY KEY (user_id, variation_group),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_task_rotation_state_user_id ON task_rotation_state(user_id);
```

**Modification to Existing Table:**

```sql
-- Add to existing plan_items table
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS task_library_id UUID REFERENCES task_library(id);
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS variation_group VARCHAR(100);
ALTER TABLE plan_items ADD COLUMN IF NOT EXISTS is_dynamic BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_plan_items_task_library_id ON plan_items(task_library_id);
```

#### 1.2 Seed Task Library (Day 2-3)

**File:** `services/seeding/task_library_seed.py`

```python
# Sample seed data structure
TASK_LIBRARY_SEED = [
    # HYDRATION CATEGORY
    {
        "category": "hydration",
        "subcategory": "water",
        "name": "Morning Lemon Water",
        "description": "Start your day with warm water and fresh lemon to boost metabolism and hydration",
        "duration_minutes": 5,
        "difficulty": "beginner",
        "archetype_fit": {
            "Foundation Builder": 0.9,
            "Transformation Seeker": 0.8,
            "Peak Performer": 0.7,
            "Systematic Improver": 0.9,
            "Resilience Rebuilder": 0.8,
            "Connected Explorer": 0.7
        },
        "mode_fit": {"high": 0.8, "medium": 0.9, "low": 0.9},
        "tags": ["quick", "energizing", "simple"],
        "variation_group": "morning_hydration",
        "time_of_day_preference": "morning"
    },
    {
        "category": "hydration",
        "subcategory": "tea",
        "name": "Green Tea Morning Ritual",
        "description": "Enjoy antioxidant-rich green tea to gently wake up your system",
        "duration_minutes": 10,
        "difficulty": "beginner",
        "archetype_fit": {
            "Foundation Builder": 0.7,
            "Transformation Seeker": 0.8,
            "Peak Performer": 0.9,
            "Systematic Improver": 0.8,
            "Resilience Rebuilder": 0.9,
            "Connected Explorer": 0.8
        },
        "mode_fit": {"high": 0.6, "medium": 0.9, "low": 0.9},
        "tags": ["calming", "ritualistic"],
        "variation_group": "morning_hydration",
        "time_of_day_preference": "morning"
    },

    # MOVEMENT CATEGORY
    {
        "category": "movement",
        "subcategory": "outdoor",
        "name": "Neighborhood Morning Walk",
        "description": "15-minute walk around your neighborhood to get sunlight and movement",
        "duration_minutes": 15,
        "difficulty": "beginner",
        "archetype_fit": {
            "Foundation Builder": 0.9,
            "Transformation Seeker": 0.7,
            "Peak Performer": 0.6,
            "Systematic Improver": 0.8,
            "Resilience Rebuilder": 0.9,
            "Connected Explorer": 0.9
        },
        "mode_fit": {"high": 0.7, "medium": 0.9, "low": 0.8},
        "tags": ["outdoor", "cardio-light", "sunlight"],
        "variation_group": "morning_movement",
        "time_of_day_preference": "morning"
    },
    {
        "category": "movement",
        "subcategory": "yoga",
        "name": "Gentle Morning Yoga Flow",
        "description": "15-minute beginner-friendly yoga sequence to wake up your body",
        "duration_minutes": 15,
        "difficulty": "beginner",
        "archetype_fit": {
            "Foundation Builder": 0.8,
            "Transformation Seeker": 0.8,
            "Peak Performer": 0.5,
            "Systematic Improver": 0.9,
            "Resilience Rebuilder": 0.9,
            "Connected Explorer": 0.8
        },
        "mode_fit": {"high": 0.5, "medium": 0.8, "low": 0.9},
        "tags": ["indoor", "flexibility", "mindful"],
        "variation_group": "morning_movement",
        "time_of_day_preference": "morning"
    },
    {
        "category": "movement",
        "subcategory": "strength",
        "name": "Quick Bodyweight Circuit",
        "description": "10-minute bodyweight exercises: squats, push-ups, planks",
        "duration_minutes": 10,
        "difficulty": "intermediate",
        "archetype_fit": {
            "Foundation Builder": 0.5,
            "Transformation Seeker": 0.9,
            "Peak Performer": 0.9,
            "Systematic Improver": 0.7,
            "Resilience Rebuilder": 0.4,
            "Connected Explorer": 0.7
        },
        "mode_fit": {"high": 0.9, "medium": 0.7, "low": 0.3},
        "tags": ["indoor", "strength", "energizing"],
        "variation_group": "morning_movement",
        "time_of_day_preference": "morning"
    },

    # Add 40-50 more tasks covering all categories...
]
```

**Seeding Script:**

```python
# services/seeding/seed_task_library.py

import asyncio
from shared_libs.supabase_client import get_supabase_client

async def seed_task_library():
    """Seed task library with initial variations"""
    supabase = get_supabase_client()

    # Check if already seeded
    result = supabase.table('task_library').select('id').limit(1).execute()
    if result.data:
        print("Task library already seeded")
        return

    # Insert seed data
    for task in TASK_LIBRARY_SEED:
        supabase.table('task_library').insert(task).execute()

    print(f"Seeded {len(TASK_LIBRARY_SEED)} tasks")

if __name__ == "__main__":
    asyncio.run(seed_task_library())
```

**Run:**
```bash
cd hos-agentic-ai-prod
python services/seeding/seed_task_library.py
```

#### 1.3 TaskLibraryService (Day 3-4)

**File:** `services/task_library_service.py`

```python
from typing import List, Dict, Optional
from shared_libs.supabase_client import get_supabase_client
import random

class TaskLibraryService:
    """Manages task selection from library based on user preferences"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def get_tasks_for_category(
        self,
        category: str,
        archetype: str,
        mode: str = "medium",
        exclude_recently_used: Optional[List[str]] = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Get suitable tasks for a category with variety

        Args:
            category: Task category (e.g., 'hydration', 'movement')
            archetype: User archetype
            mode: Current mode ('high', 'medium', 'low')
            exclude_recently_used: List of variation_group to exclude
            limit: Number of tasks to return
        """

        # Query task library
        query = self.supabase.table('task_library').select('*').eq('category', category).eq('is_active', True)

        result = query.execute()
        tasks = result.data

        if not tasks:
            return []

        # Score each task
        scored_tasks = []
        for task in tasks:
            # Skip recently used tasks
            if exclude_recently_used and task['variation_group'] in exclude_recently_used:
                continue

            # Calculate fitness score
            archetype_fit = task.get('archetype_fit', {}).get(archetype, 0.5)
            mode_fit = task.get('mode_fit', {}).get(mode, 0.5)

            # Combined score (weighted)
            score = (archetype_fit * 0.7) + (mode_fit * 0.3)

            scored_tasks.append({
                **task,
                'fitness_score': score
            })

        # Sort by score and add randomness
        scored_tasks.sort(key=lambda x: x['fitness_score'] + random.uniform(0, 0.1), reverse=True)

        return scored_tasks[:limit]

    async def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Get specific task by ID"""
        result = self.supabase.table('task_library').select('*').eq('id', task_id).single().execute()
        return result.data if result.data else None

    async def get_recently_used_variation_groups(
        self,
        user_id: str,
        days: int = 2
    ) -> List[str]:
        """Get variation groups used in last N days to avoid repetition"""
        result = self.supabase.table('task_rotation_state')\
            .select('variation_group')\
            .eq('user_id', user_id)\
            .gte('last_used_date', f"NOW() - INTERVAL '{days} days'")\
            .execute()

        return [row['variation_group'] for row in result.data]

    async def record_task_usage(
        self,
        user_id: str,
        task_library_id: str,
        variation_group: str
    ):
        """Record that a task was used to prevent immediate repetition"""
        self.supabase.table('task_rotation_state').upsert({
            'user_id': user_id,
            'task_library_id': task_library_id,
            'variation_group': variation_group,
            'last_used_date': 'NOW()',
            'times_used': 1  # Increment logic handled by DB trigger
        }).execute()
```

#### 1.4 FeedbackAnalyzer Service (Day 4-5)

**File:** `services/feedback_analyzer_service.py`

```python
from typing import Dict, Optional
from datetime import datetime, timedelta
from shared_libs.supabase_client import get_supabase_client

class FeedbackAnalyzerService:
    """Analyzes user task feedback to update preferences"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def record_task_feedback(
        self,
        user_id: str,
        plan_item_id: str,
        completed: bool,
        completed_at: Optional[datetime] = None,
        satisfaction_rating: Optional[int] = None,
        skip_reason: Optional[str] = None,
        user_notes: Optional[str] = None
    ):
        """Record user feedback for a task"""

        # Get plan item details
        plan_item = self.supabase.table('plan_items').select('*').eq('id', plan_item_id).single().execute()

        if not plan_item.data:
            return

        task_library_id = plan_item.data.get('task_library_id')
        scheduled_date = plan_item.data.get('scheduled_date')
        scheduled_time = plan_item.data.get('scheduled_time')

        # Calculate early/late minutes
        completed_early_minutes = None
        if completed and completed_at and scheduled_time:
            scheduled_dt = datetime.combine(scheduled_date, scheduled_time)
            delta = (scheduled_dt - completed_at).total_seconds() / 60
            completed_early_minutes = int(delta)

        # Insert feedback
        feedback_data = {
            'user_id': user_id,
            'task_library_id': task_library_id,
            'plan_item_id': plan_item_id,
            'scheduled_date': scheduled_date,
            'scheduled_time': scheduled_time,
            'completed': completed,
            'completed_at': completed_at,
            'completed_early_minutes': completed_early_minutes,
            'satisfaction_rating': satisfaction_rating,
            'skipped': not completed,
            'skip_reason': skip_reason,
            'user_notes': user_notes
        }

        self.supabase.table('user_task_feedback').insert(feedback_data).execute()

        # Trigger preference update (async)
        await self.update_user_preferences(user_id)

    async def update_user_preferences(self, user_id: str):
        """Recalculate user preferences based on feedback history"""

        # Get feedback from last 14 days
        cutoff_date = datetime.now() - timedelta(days=14)

        feedback_result = self.supabase.table('user_task_feedback')\
            .select('*, task_library:task_library_id(*)')\
            .eq('user_id', user_id)\
            .gte('scheduled_date', cutoff_date.date())\
            .execute()

        feedbacks = feedback_result.data

        if not feedbacks:
            return

        # Calculate category affinity
        category_stats = {}
        subcategory_stats = {}

        for fb in feedbacks:
            task = fb.get('task_library')
            if not task:
                continue

            category = task['category']
            subcategory = task.get('subcategory')

            # Track completions per category
            if category not in category_stats:
                category_stats[category] = {'completed': 0, 'total': 0}

            category_stats[category]['total'] += 1
            if fb['completed']:
                category_stats[category]['completed'] += 1

            # Track subcategory
            if subcategory:
                if subcategory not in subcategory_stats:
                    subcategory_stats[subcategory] = {'completed': 0, 'total': 0}
                subcategory_stats[subcategory]['total'] += 1
                if fb['completed']:
                    subcategory_stats[subcategory]['completed'] += 1

        # Calculate affinity scores (completion rate)
        category_affinity = {
            cat: stats['completed'] / stats['total']
            for cat, stats in category_stats.items()
        }

        subcategory_affinity = {
            subcat: stats['completed'] / stats['total']
            for subcat, stats in subcategory_stats.items()
        }

        # Calculate completion rate
        total_completed = sum(1 for fb in feedbacks if fb['completed'])
        completion_rate = total_completed / len(feedbacks)

        # Calculate complexity tolerance (do they complete harder tasks?)
        completed_difficulties = [
            fb['task_library']['difficulty']
            for fb in feedbacks
            if fb['completed'] and fb.get('task_library')
        ]

        complexity_score = 0.5  # default
        if completed_difficulties:
            advanced_count = completed_difficulties.count('advanced')
            complexity_score = min(1.0, 0.3 + (advanced_count / len(completed_difficulties)))

        # Calculate variety seeking (do they try new tasks?)
        unique_tasks = len(set(fb['task_library_id'] for fb in feedbacks if fb.get('task_library_id')))
        variety_seeking_score = min(1.0, unique_tasks / 20)  # 20+ unique tasks = max variety

        # Update profile
        self.supabase.table('user_preference_profile').upsert({
            'user_id': user_id,
            'category_affinity': category_affinity,
            'subcategory_affinity': subcategory_affinity,
            'completion_rate': completion_rate,
            'complexity_tolerance': complexity_score,
            'variety_seeking_score': variety_seeking_score,
            'total_tasks_completed': total_completed,
            'total_tasks_scheduled': len(feedbacks),
            'unique_tasks_tried': unique_tasks,
            'profile_confidence': min(1.0, len(feedbacks) / 50),  # Confidence builds with data
            'last_analyzed_at': datetime.now(),
            'updated_at': datetime.now()
        }).execute()

    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user preference profile"""
        result = self.supabase.table('user_preference_profile').select('*').eq('user_id', user_id).single().execute()
        return result.data if result.data else None
```

#### 1.5 Modified RoutineGenerationService (Day 5-7)

**File:** `services/routine_generation_service.py` (modified)

```python
from services.task_library_service import TaskLibraryService
from services.feedback_analyzer_service import FeedbackAnalyzerService

class RoutineGenerationService:
    """
    MODIFIED: Now generates dynamic plans using task library
    BACKWARDS COMPATIBLE: Falls back to AI generation if dynamic fails
    """

    def __init__(self):
        self.task_library = TaskLibraryService()
        self.feedback_analyzer = FeedbackAnalyzerService()
        # ... existing initialization

    async def generate_routine(
        self,
        user_id: str,
        archetype: str,
        preferences: Dict,
        use_dynamic: bool = True  # FEATURE FLAG
    ) -> Dict:
        """
        Generate routine plan with dynamic task selection

        Args:
            user_id: User ID
            archetype: User archetype
            preferences: User preferences (wake time, etc.)
            use_dynamic: If True, use dynamic task library. If False, use AI generation (fallback)
        """

        # FEATURE FLAG CHECK
        if not use_dynamic:
            return await self._generate_static_plan(user_id, archetype, preferences)

        try:
            # Try dynamic generation
            return await self._generate_dynamic_plan(user_id, archetype, preferences)
        except Exception as e:
            print(f"Dynamic plan generation failed: {e}. Falling back to static.")
            return await self._generate_static_plan(user_id, archetype, preferences)

    async def _generate_dynamic_plan(
        self,
        user_id: str,
        archetype: str,
        preferences: Dict
    ) -> Dict:
        """Generate plan using task library (NEW)"""

        # Get user preference profile
        user_profile = await self.feedback_analyzer.get_user_profile(user_id)

        mode = user_profile.get('current_mode', 'medium') if user_profile else 'medium'
        learning_phase = user_profile.get('learning_phase', 'discovery') if user_profile else 'discovery'

        # Get recently used tasks to avoid repetition
        recently_used = await self.task_library.get_recently_used_variation_groups(user_id, days=2)

        # Build time blocks with varied tasks
        time_blocks = []

        # Morning Block
        morning_tasks = []

        # Hydration task (1 variation)
        hydration_tasks = await self.task_library.get_tasks_for_category(
            category='hydration',
            archetype=archetype,
            mode=mode,
            exclude_recently_used=recently_used,
            limit=1
        )
        if hydration_tasks:
            morning_tasks.append(self._format_task_for_plan(hydration_tasks[0], '06:30 AM'))

        # Movement task (1 variation)
        movement_tasks = await self.task_library.get_tasks_for_category(
            category='movement',
            archetype=archetype,
            mode=mode,
            exclude_recently_used=recently_used,
            limit=1
        )
        if movement_tasks:
            morning_tasks.append(self._format_task_for_plan(movement_tasks[0], '06:45 AM'))

        # Nutrition task (1 variation)
        nutrition_tasks = await self.task_library.get_tasks_for_category(
            category='nutrition',
            archetype=archetype,
            mode=mode,
            exclude_recently_used=recently_used,
            limit=1
        )
        if nutrition_tasks:
            morning_tasks.append(self._format_task_for_plan(nutrition_tasks[0], '07:30 AM'))

        time_blocks.append({
            'block_name': 'Morning Block',
            'start_time': '06:00 AM',
            'end_time': '09:00 AM',
            'zone_type': 'maintenance',
            'purpose': 'Start your day with energizing activities',
            'tasks': morning_tasks
        })

        # ... Similar for other blocks (Peak Energy, Midday, Evening, Wind Down)

        # Record task usage for rotation tracking
        for block in time_blocks:
            for task in block['tasks']:
                if task.get('task_library_id'):
                    await self.task_library.record_task_usage(
                        user_id=user_id,
                        task_library_id=task['task_library_id'],
                        variation_group=task.get('variation_group')
                    )

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'system': 'HolisticOS',
            'content': {
                'time_blocks': time_blocks
            },
            'archetype': archetype,
            'plan_type': 'dynamic_routine',
            'model_used': 'task_library_v1',
            'readiness_mode': mode
        }

    async def _generate_static_plan(self, user_id: str, archetype: str, preferences: Dict) -> Dict:
        """Original AI-based generation (FALLBACK)"""
        # ... existing implementation unchanged
        pass

    def _format_task_for_plan(self, task: Dict, start_time: str) -> Dict:
        """Format task from library into plan task structure"""
        return {
            'task_library_id': task['id'],
            'variation_group': task['variation_group'],
            'start_time': start_time,
            'end_time': self._calculate_end_time(start_time, task['duration_minutes']),
            'title': task['name'],
            'description': task['description'],
            'task_type': task['category'],
            'priority': self._determine_priority(task),
            'estimated_duration_minutes': task['duration_minutes']
        }
```

---

### Frontend Work (Day 6-7)

#### 1.6 Task Completion API Integration

**File:** `hos_app/lib/core/services/task_feedback_service.dart` (NEW)

```dart
import 'package:dio/dio.dart';
import '../config/app_config.dart';

class TaskFeedbackService {
  final Dio _dio;

  TaskFeedbackService() : _dio = Dio(BaseOptions(
    baseUrl: AppConfig.routineApiBaseUrl,
    headers: {'X-API-Key': AppConfig.apiKey},
  ));

  /// Record task completion with optional feedback
  Future<void> recordTaskCompletion({
    required String userId,
    required String planItemId,
    required bool completed,
    DateTime? completedAt,
    int? satisfactionRating, // 1-5 stars
    String? skipReason,
    String? userNotes,
  }) async {
    try {
      await _dio.post(
        '/api/v1/feedback/task',
        data: {
          'user_id': userId,
          'plan_item_id': planItemId,
          'completed': completed,
          'completed_at': completedAt?.toIso8601String(),
          'satisfaction_rating': satisfactionRating,
          'skip_reason': skipReason,
          'user_notes': userNotes,
        },
      );
    } catch (e) {
      print('Error recording task feedback: $e');
      // Fail silently - don't block user
    }
  }

  /// Get user preference profile
  Future<Map<String, dynamic>?> getUserProfile(String userId) async {
    try {
      final response = await _dio.get('/api/v1/feedback/profile/$userId');
      return response.data;
    } catch (e) {
      print('Error fetching user profile: $e');
      return null;
    }
  }
}
```

#### 1.7 Backend API Endpoint (NEW)

**File:** `services/api_gateway/feedback_endpoints.py` (NEW)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from services.feedback_analyzer_service import FeedbackAnalyzerService

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])
feedback_service = FeedbackAnalyzerService()

class TaskFeedbackRequest(BaseModel):
    user_id: str
    plan_item_id: str
    completed: bool
    completed_at: Optional[datetime] = None
    satisfaction_rating: Optional[int] = None
    skip_reason: Optional[str] = None
    user_notes: Optional[str] = None

@router.post("/task")
async def record_task_feedback(request: TaskFeedbackRequest):
    """Record user feedback for a task"""
    try:
        await feedback_service.record_task_feedback(
            user_id=request.user_id,
            plan_item_id=request.plan_item_id,
            completed=request.completed,
            completed_at=request.completed_at,
            satisfaction_rating=request.satisfaction_rating,
            skip_reason=request.skip_reason,
            user_notes=request.user_notes
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user preference profile"""
    profile = await feedback_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
```

**Register router in `openai_main.py`:**

```python
from services.api_gateway.feedback_endpoints import router as feedback_router
app.include_router(feedback_router)
```

#### 1.8 Flutter UI Enhancement (Existing Journal Integration)

**File:** `hos_app/lib/presentation/screens/planner/active_plan_dashboard.dart` (MODIFY)

```dart
// Add to existing task completion handler
Future<void> _handleTaskCompletion(PlanTask task, bool completed) async {
  // Existing completion logic...

  // NEW: Record feedback
  final taskFeedbackService = getIt<TaskFeedbackService>();

  await taskFeedbackService.recordTaskCompletion(
    userId: currentUserId,
    planItemId: task.id,
    completed: completed,
    completedAt: completed ? DateTime.now() : null,
  );

  // Trigger UI update...
}

// Add optional satisfaction rating after task completion
Future<void> _showSatisfactionRating(PlanTask task) async {
  // Show only if user completed task and it's their first time
  if (!task.isFirstCompletion) return;

  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('How was it?'),
      content: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          for (int i = 1; i <= 5; i++)
            IconButton(
              icon: Icon(Icons.star, color: Colors.amber),
              onPressed: () {
                taskFeedbackService.recordTaskCompletion(
                  userId: currentUserId,
                  planItemId: task.id,
                  completed: true,
                  satisfactionRating: i,
                );
                Navigator.pop(context);
              },
            ),
        ],
      ),
    ),
  );
}
```

---

### Testing & Deployment (Day 7)

#### 1.9 Feature Flag Configuration

**File:** `.env`

```env
# Feature Flags
ENABLE_DYNAMIC_PLANS=true  # Toggle dynamic plan generation
TASK_LIBRARY_VERSION=v1
FEEDBACK_COLLECTION_ENABLED=true
```

#### 1.10 Testing Checklist

```bash
# Backend Tests
cd hos-agentic-ai-prod

# 1. Test task library seeding
python services/seeding/seed_task_library.py

# 2. Test task selection
python testing/test_task_library_service.py

# 3. Test feedback recording
python testing/test_feedback_analyzer.py

# 4. Test dynamic plan generation
python testing/test_dynamic_routine.py

# 5. Test backward compatibility (feature flag off)
ENABLE_DYNAMIC_PLANS=false python testing/test_routine_generation.py
```

```dart
// Flutter Tests
cd hos_app

// 1. Test task feedback service
flutter test test/services/task_feedback_service_test.dart

// 2. Test UI integration
flutter test test/screens/active_plan_dashboard_test.dart

// 3. Integration test
flutter drive --target=test_driver/task_completion_flow.dart
```

#### 1.11 Monitoring Setup

**Add to existing monitoring:**

```python
# shared_libs/monitoring/metrics.py

from prometheus_client import Counter, Histogram

# New metrics
dynamic_plan_generated = Counter('dynamic_plans_generated_total', 'Dynamic plans generated')
task_feedback_recorded = Counter('task_feedback_recorded_total', 'Task feedback recorded')
task_library_selection_time = Histogram('task_library_selection_seconds', 'Task selection latency')
```

---

## **PHASE 1 DELIVERABLES SUMMARY**

### What Gets Released (Week 2 End)

**User-Facing:**
- ✅ Task variety (no more repetitive morning hydration)
- ✅ Different tasks each day from same category
- ✅ Seamless experience (no UI changes visible)

**Backend:**
- ✅ Task library with 50+ task variations
- ✅ Dynamic plan generation service
- ✅ Feedback collection infrastructure
- ✅ User preference tracking (silent)

**Safety:**
- ✅ Feature flag controlled
- ✅ Automatic fallback to AI generation
- ✅ Backwards compatible
- ✅ No breaking changes

### Success Metrics (Week 3-4)

Monitor these in production:
- Dynamic plan generation success rate: >95%
- Task variety achieved: 80% of users see 3+ different hydration tasks in 7 days
- API latency: <500ms for plan generation
- Feedback collection rate: >20% of tasks get implicit feedback

---

**END OF PHASE 1**

Phase 2 implementation continues in next section...
