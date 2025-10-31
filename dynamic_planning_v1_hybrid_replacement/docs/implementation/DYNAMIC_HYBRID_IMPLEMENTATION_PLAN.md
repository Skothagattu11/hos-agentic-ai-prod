# Dynamic Hybrid Architecture - Implementation Plan

## Executive Summary

This document provides a detailed, phased implementation plan for integrating the Dynamic Task Selection system with the existing AI Routine Agent. The implementation preserves the current AI-based flow as a fallback and introduces a feature-switched hybrid approach that reduces costs by 75% while improving personalization.

**Key Objectives:**
- Zero breaking changes to existing flow
- Feature-switched gradual rollout
- AI strategic layer + Dynamic tactical layer
- Feedback-driven learning for both systems
- Mode support with brain_power as default
- Configurable shuffle frequency

**Timeline:** 4-6 weeks (phased rollout)

---

## Phase 1: Foundation Setup (Week 1)

### 1.1 Prerequisites Verification

**Goal:** Ensure all infrastructure is in place before building new features.

**Tasks:**

1. **Verify Database Tables**
   ```bash
   # Check all tables exist
   cd /mnt/c/dev_skoth/hos/hos-agentic-ai-prod
   python -c "
   import asyncio
   from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
   from dotenv import load_dotenv
   import os

   async def verify():
       load_dotenv()
       adapter = SupabaseAsyncPGAdapter(
           supabase_url=os.getenv('SUPABASE_URL'),
           supabase_key=os.getenv('SUPABASE_SERVICE_KEY')
       )
       await adapter.connect()

       tables = [
           'task_library',
           'user_task_feedback',
           'user_preference_profile',
           'task_rotation_state',
           'plan_items'
       ]

       for table in tables:
           result = await adapter.fetch(f'SELECT COUNT(*) as count FROM {table}')
           print(f'✓ {table}: {result[0][\"count\"]} records')

       await adapter.close()

   asyncio.run(verify())
   "
   ```

2. **Verify Task Library Seeding**
   ```bash
   # Run seeding script if not already done
   python services/seeding/task_library_seed.py

   # Expected output: [OK] Successfully seeded 50 tasks
   ```

3. **Verify Dynamic Services**
   ```bash
   # Run comprehensive test suite
   python testing/test_dynamic_personalization.py

   # Expected: 10/10 tests passing
   ```

4. **Fix Circadian Analysis (CRITICAL)**

   **Current Issue:** Circadian analysis is broken, preventing personalized time blocks.

   **File:** `services/agents/memory/episodic_memory_manager.py` or `services/agents/behavior/circadian_analyzer.py`

   **Action Required:**
   - Locate circadian analysis code
   - Fix any broken API calls or calculations
   - Verify wake/sleep time extraction from user data
   - Test with real user data

   **Test Command:**
   ```bash
   # Create test script
   # File: testing/test_circadian_analysis.py
   ```

   **Expected Output:** Personalized wake time (e.g., 7:00 AM), sleep time (e.g., 11:00 PM)

**Acceptance Criteria:**
- ✅ All 5 database tables verified with row counts
- ✅ 50 tasks in task_library
- ✅ 10/10 dynamic personalization tests passing
- ✅ Circadian analysis returns personalized times for test user

---

## Phase 2: Dynamic Task Selector Service (Week 2)

### 2.1 Create Dynamic Task Selector

**Goal:** Build the core service that replaces AI tasks with library selections.

**File:** `services/dynamic_personalization/dynamic_task_selector.py`

**Implementation:**

```python
"""
Dynamic Task Selector
======================

Purpose: Replace AI-generated tasks with task library selections
Layer: Tactical selection within AI-generated time blocks

Features:
- Extract task requirements from AI blocks
- Query task library with filters (archetype, mode, category)
- Score tasks based on preferences and feedback
- Handle fallback to AI tasks
- Track selection metadata
"""

from typing import List, Dict, Optional
from datetime import datetime

from services.dynamic_personalization.task_library_service import TaskLibraryService
from services.dynamic_personalization.feedback_analyzer_service import FeedbackAnalyzerService
from services.dynamic_personalization.adaptive_task_selector import AdaptiveTaskSelector
from services.dynamic_personalization.category_mapper import CategoryMapper
from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
from shared_libs.utils.logger import get_logger

logger = get_logger(__name__)


class DynamicTaskSelector:
    """Selects library tasks to replace AI-generated tasks."""

    def __init__(self, db_adapter: Optional[SupabaseAsyncPGAdapter] = None):
        """Initialize DynamicTaskSelector.

        Args:
            db_adapter: Database adapter (creates new if None)
        """
        self.db = db_adapter or SupabaseAsyncPGAdapter()
        self.task_library = TaskLibraryService(db_adapter=self.db)
        self.feedback_service = FeedbackAnalyzerService(db_adapter=self.db)
        self.adaptive_selector = AdaptiveTaskSelector(db_adapter=self.db)
        self.category_mapper = CategoryMapper()
        self._initialized = False

    async def initialize(self):
        """Initialize all services."""
        if not self._initialized:
            await self.db.connect()
            await self.task_library.initialize()
            await self.feedback_service.initialize()
            await self.adaptive_selector.initialize()
            self._initialized = True
            logger.info("DynamicTaskSelector initialized")

    async def close(self):
        """Close all services."""
        if self._initialized:
            await self.adaptive_selector.close()
            await self.feedback_service.close()
            await self.task_library.close()
            await self.db.close()
            self._initialized = False
            logger.info("DynamicTaskSelector closed")

    async def replace_ai_tasks_with_library(
        self,
        user_id: str,
        ai_plan: Dict,
        archetype: str,
        mode: str = "brain_power"
    ) -> Dict:
        """Replace AI-generated tasks with library selections.

        Args:
            user_id: User ID
            ai_plan: AI-generated plan with time_blocks
            archetype: User archetype
            mode: Current mode (brain_power, travel, fasting, productivity, recovery)

        Returns:
            Modified plan with library tasks replacing AI tasks
        """
        try:
            logger.info(f"Replacing AI tasks for user {user_id} (mode={mode})")

            # Extract time blocks from AI plan
            time_blocks = ai_plan.get('time_blocks', [])
            if not time_blocks:
                logger.warning("No time blocks in AI plan - returning as-is")
                return ai_plan

            # Process each time block
            modified_blocks = []
            replacement_stats = {
                'total_tasks': 0,
                'replaced': 0,
                'kept_ai': 0,
                'failed': 0
            }

            for block in time_blocks:
                modified_block = await self._process_time_block(
                    user_id=user_id,
                    block=block,
                    archetype=archetype,
                    mode=mode,
                    stats=replacement_stats
                )
                modified_blocks.append(modified_block)

            # Update plan with modified blocks
            modified_plan = ai_plan.copy()
            modified_plan['time_blocks'] = modified_blocks
            modified_plan['is_dynamic_hybrid'] = True
            modified_plan['replacement_stats'] = replacement_stats

            logger.info(
                f"Task replacement complete: {replacement_stats['replaced']}/{replacement_stats['total_tasks']} "
                f"replaced with library tasks"
            )

            return modified_plan

        except Exception as e:
            logger.error(f"Error replacing AI tasks: {e}")
            # Return original AI plan as fallback
            return ai_plan

    async def _process_time_block(
        self,
        user_id: str,
        block: Dict,
        archetype: str,
        mode: str,
        stats: Dict
    ) -> Dict:
        """Process a single time block, replacing tasks.

        Args:
            user_id: User ID
            block: Time block with tasks
            archetype: User archetype
            mode: Current mode
            stats: Replacement statistics dict (mutated)

        Returns:
            Modified time block
        """
        tasks = block.get('tasks', [])
        modified_tasks = []

        for task in tasks:
            stats['total_tasks'] += 1

            try:
                # Extract task requirements
                requirement = self._extract_task_requirement(task, block)

                # Map to library category
                library_category = self.category_mapper.map_ai_task_to_category(
                    task_title=task.get('title', ''),
                    task_type=task.get('task_type', ''),
                    block_zone=block.get('zone_type', 'maintenance')
                )

                if not library_category:
                    logger.debug(f"No category mapping for task '{task.get('title')}' - keeping AI task")
                    modified_tasks.append(self._mark_as_ai_task(task))
                    stats['kept_ai'] += 1
                    continue

                # Select library task
                library_task = await self.adaptive_selector.select_tasks_for_block(
                    user_id=user_id,
                    category=library_category,
                    archetype=archetype,
                    mode=mode,
                    time_of_day=self._map_block_to_time_of_day(block),
                    count=1
                )

                if library_task and len(library_task) > 0:
                    # Replace with library task
                    replaced_task = self._create_replaced_task(
                        original_task=task,
                        library_task=library_task[0],
                        requirement=requirement
                    )
                    modified_tasks.append(replaced_task)
                    stats['replaced'] += 1
                    logger.debug(f"Replaced '{task.get('title')}' with '{library_task[0]['name']}'")
                else:
                    # No suitable library task - keep AI task
                    logger.debug(f"No library task found for '{task.get('title')}' - keeping AI task")
                    modified_tasks.append(self._mark_as_ai_task(task))
                    stats['kept_ai'] += 1

            except Exception as e:
                logger.error(f"Error processing task '{task.get('title')}': {e}")
                modified_tasks.append(self._mark_as_ai_task(task))
                stats['failed'] += 1

        # Return modified block
        modified_block = block.copy()
        modified_block['tasks'] = modified_tasks
        return modified_block

    def _extract_task_requirement(self, task: Dict, block: Dict) -> Dict:
        """Extract task requirements from AI task and block context.

        Args:
            task: AI-generated task
            block: Time block context

        Returns:
            Task requirement dictionary
        """
        return {
            'category': task.get('task_type', 'wellness'),
            'duration': self._parse_duration(task),
            'time_of_day': self._map_block_to_time_of_day(block),
            'zone_type': block.get('zone_type', 'maintenance'),
            'priority': task.get('priority', 'medium')
        }

    def _parse_duration(self, task: Dict) -> int:
        """Parse duration from task times.

        Args:
            task: Task with start_time and end_time

        Returns:
            Duration in minutes
        """
        try:
            from datetime import datetime
            start = datetime.strptime(task['start_time'], '%H:%M')
            end = datetime.strptime(task['end_time'], '%H:%M')
            duration = (end - start).seconds // 60
            return duration
        except:
            return 15  # Default 15 minutes

    def _map_block_to_time_of_day(self, block: Dict) -> str:
        """Map time block to time_of_day preference.

        Args:
            block: Time block with name

        Returns:
            Time of day (morning/afternoon/evening/any)
        """
        block_name = block.get('name', '').lower()

        if 'morning' in block_name:
            return 'morning'
        elif 'peak' in block_name or 'mid' in block_name:
            return 'afternoon'
        elif 'evening' in block_name or 'wind' in block_name:
            return 'evening'
        else:
            return 'any'

    def _create_replaced_task(
        self,
        original_task: Dict,
        library_task: Dict,
        requirement: Dict
    ) -> Dict:
        """Create replacement task preserving AI timing.

        Args:
            original_task: Original AI task
            library_task: Selected library task
            requirement: Extracted requirements

        Returns:
            Replacement task with library content and AI timing
        """
        return {
            'title': library_task['name'],
            'description': library_task['description'],
            'start_time': original_task['start_time'],
            'end_time': original_task['end_time'],
            'task_type': library_task['category'],
            'priority': original_task.get('priority', 'medium'),

            # Dynamic metadata
            'is_dynamic': True,
            'task_library_id': library_task['id'],
            'variation_group': library_task.get('variation_group'),
            'replaced_ai_task': original_task['title'],
            'selection_score': library_task.get('selection_score'),
            'archetype_fit': library_task.get('archetype_fit'),
            'mode_fit': library_task.get('mode_fit')
        }

    def _mark_as_ai_task(self, task: Dict) -> Dict:
        """Mark task as AI-generated (not replaced).

        Args:
            task: AI task

        Returns:
            Task with is_dynamic=False
        """
        marked_task = task.copy()
        marked_task['is_dynamic'] = False
        marked_task['task_library_id'] = None
        return marked_task
```

**Testing:**

Create test file: `testing/test_dynamic_task_selector.py`

```python
"""Test Dynamic Task Selector"""

import asyncio
import os
from dotenv import load_dotenv
from services.dynamic_personalization.dynamic_task_selector import DynamicTaskSelector

# Load environment
load_dotenv()

# Test user
TEST_USER_ID = "a57f70b4-d0a4-4aef-b721-a4b526f64869"
TEST_ARCHETYPE = "peak_performer"

# Sample AI plan
SAMPLE_AI_PLAN = {
    "time_blocks": [
        {
            "name": "Morning Activation",
            "start_time": "07:00",
            "end_time": "09:00",
            "zone_type": "maintenance",
            "tasks": [
                {
                    "title": "Morning Hydration",
                    "description": "Drink 16oz water",
                    "start_time": "07:00",
                    "end_time": "07:05",
                    "task_type": "hydration",
                    "priority": "high"
                },
                {
                    "title": "Light Movement",
                    "description": "10 min stretching",
                    "start_time": "07:15",
                    "end_time": "07:25",
                    "task_type": "movement",
                    "priority": "medium"
                }
            ]
        }
    ]
}

async def test_task_replacement():
    """Test replacing AI tasks with library tasks."""

    selector = DynamicTaskSelector()
    await selector.initialize()

    try:
        # Replace tasks
        modified_plan = await selector.replace_ai_tasks_with_library(
            user_id=TEST_USER_ID,
            ai_plan=SAMPLE_AI_PLAN,
            archetype=TEST_ARCHETYPE,
            mode="brain_power"
        )

        # Print results
        print("\n" + "="*60)
        print("DYNAMIC TASK REPLACEMENT TEST")
        print("="*60)

        stats = modified_plan.get('replacement_stats', {})
        print(f"\nReplacement Stats:")
        print(f"  Total tasks: {stats.get('total_tasks', 0)}")
        print(f"  Replaced: {stats.get('replaced', 0)}")
        print(f"  Kept AI: {stats.get('kept_ai', 0)}")
        print(f"  Failed: {stats.get('failed', 0)}")

        # Show replaced tasks
        print(f"\nModified Time Blocks:")
        for block in modified_plan['time_blocks']:
            print(f"\n  Block: {block['name']}")
            for task in block['tasks']:
                task_source = "LIBRARY" if task.get('is_dynamic') else "AI"
                print(f"    [{task_source}] {task['title']} ({task['start_time']}-{task['end_time']})")
                if task.get('replaced_ai_task'):
                    print(f"         (replaced: {task['replaced_ai_task']})")

        print("\n" + "="*60)
        print("✓ Test completed successfully")
        print("="*60 + "\n")

    finally:
        await selector.close()

if __name__ == "__main__":
    asyncio.run(test_task_replacement())
```

**Run Test:**
```bash
python testing/test_dynamic_task_selector.py

# Expected output:
# Replacement Stats:
#   Total tasks: 2
#   Replaced: 2
#   Kept AI: 0
#   Failed: 0
```

**Acceptance Criteria:**
- ✅ Service successfully replaces AI tasks with library tasks
- ✅ Original timing preserved (start_time, end_time)
- ✅ Replacement stats tracked correctly
- ✅ Fallback to AI tasks when no library match

---

## Phase 3: Category Mapping Service (Week 2)

### 3.1 Create Category Mapper

**Goal:** Map AI task titles to task library categories with fuzzy matching.

**File:** `services/dynamic_personalization/category_mapper.py`

**Implementation:**

```python
"""
Category Mapper
================

Purpose: Map AI-generated task titles to task library categories
Pattern: Rule-based + fuzzy matching

Features:
- Keyword-based category detection
- Fuzzy string matching for variations
- Zone type consideration
- Fallback category logic
"""

from typing import Optional, Dict
import re
from shared_libs.utils.logger import get_logger

logger = get_logger(__name__)


class CategoryMapper:
    """Maps AI tasks to task library categories."""

    # Category keyword patterns
    CATEGORY_PATTERNS = {
        'hydration': [
            r'\bwater\b', r'\bhydrat', r'\bdrink', r'\bfluid', r'\bh2o\b',
            r'\belixir\b', r'\belectrolyte'
        ],
        'movement': [
            r'\bexercise\b', r'\bworkout\b', r'\bstretch', r'\byoga\b',
            r'\bwalk', r'\brun', r'\bjog', r'\bcardio\b', r'\bmovement\b',
            r'\bphysical', r'\bactive', r'\bmobility\b', r'\bpilates\b'
        ],
        'nutrition': [
            r'\bmeal\b', r'\beat', r'\bfood\b', r'\bnutrit', r'\bsnack\b',
            r'\bbreakfast\b', r'\blunch\b', r'\bdinner\b', r'\bprotein\b',
            r'\bveggie', r'\bfruit\b', r'\bsupplement'
        ],
        'wellness': [
            r'\bmeditat', r'\bmindful', r'\bbreath', r'\brelax',
            r'\bstress', r'\bcalm', r'\bzenith\b', r'\bpeace\b',
            r'\bjournal', r'\bgratitude\b', r'\bwellness\b', r'\bself-care\b'
        ],
        'recovery': [
            r'\bsleep\b', r'\brest\b', r'\brecover', r'\bmassage\b',
            r'\bbath\b', r'\bwind down\b', r'\bunwind\b', r'\bnap\b',
            r'\bfoam roll', r'\bice bath\b', r'\bsauna\b'
        ],
        'work': [
            r'\bwork\b', r'\btask\b', r'\bproject\b', r'\bmeeting\b',
            r'\bfocus\b', r'\bproductiv', r'\bdeep work\b', r'\bbrain dump\b',
            r'\bplan', r'\borganize\b'
        ]
    }

    # Zone type to category hints
    ZONE_CATEGORY_HINTS = {
        'peak': ['work', 'movement', 'nutrition'],
        'maintenance': ['hydration', 'wellness', 'nutrition'],
        'recovery': ['recovery', 'wellness', 'hydration']
    }

    def map_ai_task_to_category(
        self,
        task_title: str,
        task_type: str = "",
        block_zone: str = "maintenance"
    ) -> Optional[str]:
        """Map AI task to library category.

        Args:
            task_title: AI-generated task title
            task_type: Task type from AI (if available)
            block_zone: Time block zone type

        Returns:
            Category name or None if no match
        """
        # Normalize title
        title_lower = task_title.lower()

        # First: Check if task_type directly matches a category
        if task_type and task_type.lower() in self.CATEGORY_PATTERNS:
            logger.debug(f"Direct task_type match: '{task_title}' → {task_type}")
            return task_type.lower()

        # Second: Pattern matching on title
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    logger.debug(f"Pattern match: '{task_title}' → {category} (pattern: {pattern})")
                    return category

        # Third: Use zone hints if no pattern match
        hint_categories = self.ZONE_CATEGORY_HINTS.get(block_zone, [])
        if hint_categories:
            logger.debug(f"Zone hint fallback: '{task_title}' → {hint_categories[0]} (zone: {block_zone})")
            return hint_categories[0]

        # No match found
        logger.warning(f"No category mapping for: '{task_title}' (type: {task_type}, zone: {block_zone})")
        return None

    def get_category_for_ai_task_type(self, ai_task_type: str) -> Optional[str]:
        """Direct mapping from AI task_type to library category.

        Args:
            ai_task_type: Task type from AI

        Returns:
            Category name or None
        """
        # Direct mappings
        type_mappings = {
            'hydration': 'hydration',
            'movement': 'movement',
            'nutrition': 'nutrition',
            'wellness': 'wellness',
            'recovery': 'recovery',
            'work': 'work',
            'exercise': 'movement',
            'meal': 'nutrition',
            'mindfulness': 'wellness',
            'rest': 'recovery'
        }

        return type_mappings.get(ai_task_type.lower())
```

**Testing:**

Add to `testing/test_dynamic_task_selector.py`:

```python
def test_category_mapping():
    """Test category mapper."""
    from services.dynamic_personalization.category_mapper import CategoryMapper

    mapper = CategoryMapper()

    test_cases = [
        ("Morning Hydration", "hydration", "maintenance", "hydration"),
        ("Light Movement", "movement", "maintenance", "movement"),
        ("Brain Dump", "work", "peak", "work"),
        ("Meditation Break", "wellness", "recovery", "wellness"),
        ("Protein Snack", "nutrition", "maintenance", "nutrition"),
        ("Evening Wind Down", "recovery", "recovery", "recovery"),
        ("Unknown Task", "", "maintenance", None)  # Should return None or fallback
    ]

    print("\n" + "="*60)
    print("CATEGORY MAPPING TEST")
    print("="*60)

    for title, task_type, zone, expected in test_cases:
        result = mapper.map_ai_task_to_category(title, task_type, zone)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{title}' → {result} (expected: {expected})")

    print("="*60 + "\n")

# Run in test file
if __name__ == "__main__":
    test_category_mapping()
    # asyncio.run(test_task_replacement())
```

**Acceptance Criteria:**
- ✅ All common AI task titles map to correct categories
- ✅ Fallback logic works for unknown tasks
- ✅ Zone hints provide sensible defaults

---

## Phase 4: Feature Switch Integration (Week 3)

### 4.1 Add Feature Flags

**File:** `config/dynamic_personalization_config.py`

**Add new configuration:**

```python
class DynamicPersonalizationConfig:
    """Configuration for dynamic personalization features."""

    def __init__(self):
        # Existing flags
        self.ENABLE_DYNAMIC_PLANS = os.getenv("ENABLE_DYNAMIC_PLANS", "false").lower() == "true"
        self.ADAPTIVE_LEARNING_ENABLED = os.getenv("ADAPTIVE_LEARNING_ENABLED", "false").lower() == "true"

        # NEW: Master switch for hybrid system
        self.ENABLE_DYNAMIC_TASK_SELECTION = os.getenv("ENABLE_DYNAMIC_TASK_SELECTION", "false").lower() == "true"

        # NEW: Shuffle frequency control
        self.SHUFFLE_FREQUENCY = os.getenv("SHUFFLE_FREQUENCY", "weekly")  # weekly, daily, every_plan, on_pattern, manual

        # Rotation threshold
        self.rotation_threshold_hours = int(os.getenv("ROTATION_THRESHOLD_HOURS", "48"))

        # Mode defaults
        self.DEFAULT_MODE = os.getenv("DEFAULT_MODE", "brain_power")

    def is_enabled(self) -> bool:
        """Check if any dynamic personalization is enabled."""
        return self.ENABLE_DYNAMIC_PLANS or self.ENABLE_DYNAMIC_TASK_SELECTION

    def is_hybrid_enabled(self) -> bool:
        """Check if hybrid AI + Dynamic is enabled."""
        return self.ENABLE_DYNAMIC_TASK_SELECTION

    def should_shuffle_plan(self, user_id: str, last_shuffle_date: Optional[str]) -> bool:
        """Determine if time blocks should be regenerated by AI.

        Args:
            user_id: User ID
            last_shuffle_date: ISO date of last shuffle

        Returns:
            True if should regenerate AI time blocks
        """
        from datetime import datetime, timedelta

        if self.SHUFFLE_FREQUENCY == "every_plan":
            return True

        if self.SHUFFLE_FREQUENCY == "manual":
            return False

        if not last_shuffle_date:
            return True  # First time

        try:
            last_shuffle = datetime.fromisoformat(last_shuffle_date)
            days_since = (datetime.now() - last_shuffle).days

            if self.SHUFFLE_FREQUENCY == "daily":
                return days_since >= 1
            elif self.SHUFFLE_FREQUENCY == "weekly":
                return days_since >= 7
            elif self.SHUFFLE_FREQUENCY == "on_pattern":
                # Check for pattern changes (simplified - expand later)
                return days_since >= 3

        except ValueError:
            return True

        return False
```

**Update .env file:**

```bash
# Add to .env
ENABLE_DYNAMIC_TASK_SELECTION=false  # Set to true to enable hybrid system
SHUFFLE_FREQUENCY=weekly  # How often AI regenerates time blocks
DEFAULT_MODE=brain_power  # Default mode if not specified
```

### 4.2 Modify Routine API Endpoint

**File:** `services/api_gateway/openai_main.py`

**Locate the `/api/user/{user_id}/routine/generate` endpoint and modify:**

```python
@app.post("/api/user/{user_id}/routine/generate", response_model=RoutinePlanResponse)
async def generate_routine_plan(user_id: str, request: PlanGenerationRequest):
    """Generate personalized routine plan with HYBRID AI + DYNAMIC support."""

    try:
        # ... existing validation and archetype logic ...

        # NEW: Get mode with default
        from config.dynamic_personalization_config import get_config as get_dynamic_config
        dynamic_config = get_dynamic_config()

        mode = request.preferences.get('mode', dynamic_config.DEFAULT_MODE) if request.preferences else dynamic_config.DEFAULT_MODE

        print(f"🎯 [MODE] Using mode: {mode}")

        # Parse plan_date if provided
        plan_date_obj = None
        if request.plan_date:
            try:
                from datetime import datetime as dt
                plan_date_obj = dt.strptime(request.plan_date, "%Y-%m-%d")
                print(f"📅 [PLAN_DATE] Using specified date: {request.plan_date}")
            except ValueError:
                print(f"⚠️ [PLAN_DATE] Invalid date format: {request.plan_date}")
                plan_date_obj = None

        # NEW: Check if hybrid system is enabled
        if dynamic_config.is_hybrid_enabled():
            print(f"🔀 [HYBRID] Dynamic task selection enabled - using hybrid flow")

            try:
                # Check if we need to shuffle (regenerate AI time blocks)
                last_shuffle = await _get_last_shuffle_date(user_id)
                should_shuffle = dynamic_config.should_shuffle_plan(user_id, last_shuffle)

                if should_shuffle:
                    print(f"🔄 [SHUFFLE] Regenerating AI time blocks (last shuffle: {last_shuffle})")

                    # Generate AI time blocks (existing flow)
                    ai_plan = await _generate_ai_routine_plan(
                        user_id=user_id,
                        archetype=archetype,
                        preferences=request.preferences,
                        timezone=request.timezone,
                        mode=mode
                    )

                    # Save shuffle date
                    await _save_shuffle_date(user_id)

                else:
                    print(f"🔁 [REUSE] Reusing existing AI time blocks (last shuffle: {last_shuffle})")

                    # Load cached AI plan structure
                    ai_plan = await _load_cached_ai_plan(user_id)

                    if not ai_plan:
                        print(f"⚠️ [CACHE_MISS] No cached plan found - generating new one")
                        ai_plan = await _generate_ai_routine_plan(
                            user_id=user_id,
                            archetype=archetype,
                            preferences=request.preferences,
                            timezone=request.timezone,
                            mode=mode
                        )
                        await _save_shuffle_date(user_id)

                # NEW: Replace AI tasks with library selections
                from services.dynamic_personalization.dynamic_task_selector import DynamicTaskSelector

                selector = DynamicTaskSelector()
                await selector.initialize()

                try:
                    hybrid_plan = await selector.replace_ai_tasks_with_library(
                        user_id=user_id,
                        ai_plan=ai_plan,
                        archetype=archetype,
                        mode=mode
                    )

                    # Log replacement stats
                    stats = hybrid_plan.get('replacement_stats', {})
                    print(f"✅ [HYBRID] Replaced {stats.get('replaced', 0)}/{stats.get('total_tasks', 0)} tasks with library selections")

                    # Return hybrid plan
                    return RoutinePlanResponse(
                        success=True,
                        message=f"Hybrid plan generated successfully (mode: {mode})",
                        data={
                            "plan": hybrid_plan,
                            "archetype": archetype,
                            "mode": mode,
                            "is_hybrid": True,
                            "replacement_stats": stats
                        }
                    )

                finally:
                    await selector.close()

            except Exception as hybrid_error:
                print(f"❌ [HYBRID_ERROR] Hybrid generation failed: {hybrid_error}")
                print(f"   Falling back to full AI generation...")
                # Fall through to AI generation below

        # FALLBACK: Full AI generation (existing flow - unchanged)
        print(f"🤖 [AI_GENERATION] Using full AI-based plan generation")

        ai_plan = await _generate_ai_routine_plan(
            user_id=user_id,
            archetype=archetype,
            preferences=request.preferences,
            timezone=request.timezone,
            mode=mode
        )

        return RoutinePlanResponse(
            success=True,
            message=f"AI plan generated successfully (mode: {mode})",
            data={
                "plan": ai_plan,
                "archetype": archetype,
                "mode": mode,
                "is_hybrid": False
            }
        )

    except Exception as e:
        logger.error(f"Error generating routine plan for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# NEW: Helper functions

async def _get_last_shuffle_date(user_id: str) -> Optional[str]:
    """Get last shuffle date for user."""
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        db = SupabaseAsyncPGAdapter()
        await db.connect()

        query = """
            SELECT last_shuffle_date
            FROM user_preference_profile
            WHERE user_id = $1
        """
        result = await db.fetchrow(query, user_id)
        await db.close()

        if result:
            return result.get('last_shuffle_date')

    except Exception as e:
        logger.error(f"Error fetching last shuffle date: {e}")

    return None


async def _save_shuffle_date(user_id: str):
    """Save current date as last shuffle date."""
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        from datetime import datetime

        db = SupabaseAsyncPGAdapter()
        await db.connect()

        query = """
            UPDATE user_preference_profile
            SET last_shuffle_date = $1
            WHERE user_id = $2
        """
        await db.execute(query, datetime.now().isoformat(), user_id)
        await db.close()

    except Exception as e:
        logger.error(f"Error saving shuffle date: {e}")


async def _load_cached_ai_plan(user_id: str) -> Optional[Dict]:
    """Load cached AI plan structure for user."""
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        db = SupabaseAsyncPGAdapter()
        await db.connect()

        # Query last AI plan structure
        query = """
            SELECT cached_ai_plan
            FROM user_preference_profile
            WHERE user_id = $1
        """
        result = await db.fetchrow(query, user_id)
        await db.close()

        if result and result.get('cached_ai_plan'):
            return result['cached_ai_plan']

    except Exception as e:
        logger.error(f"Error loading cached AI plan: {e}")

    return None


async def _generate_ai_routine_plan(
    user_id: str,
    archetype: str,
    preferences: Optional[Dict],
    timezone: Optional[str],
    mode: str
) -> Dict:
    """Generate AI routine plan (existing logic - extract to function)."""

    # ... existing AI generation code ...
    # This is the current plan generation logic - no changes needed
    # Just extract it into this function for reusability

    pass  # Replace with actual implementation
```

**Add database migration for caching:**

**File:** `supabase/migrations/006_add_plan_caching.sql`

```sql
-- Add columns for plan caching and shuffle tracking
ALTER TABLE user_preference_profile
ADD COLUMN IF NOT EXISTS last_shuffle_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS cached_ai_plan JSONB;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_user_pref_shuffle_date
ON user_preference_profile(user_id, last_shuffle_date);
```

**Acceptance Criteria:**
- ✅ Feature switch controls which flow is used
- ✅ Hybrid flow: AI generates time blocks, Dynamic replaces tasks
- ✅ Full AI flow preserved as fallback (no breaking changes)
- ✅ Mode parameter supported with brain_power as default
- ✅ Shuffle frequency controls AI regeneration
- ✅ Replacement stats logged

---

## Phase 5: Mode Support Implementation (Week 3)

### 5.1 Add Mode Constraints to Task Library

**File:** `services/dynamic_personalization/task_library_service.py`

**Modify `get_tasks_for_category` to support mode filtering:**

```python
async def get_tasks_for_category(
    self,
    category: str,
    archetype: str,
    mode: str = "medium",  # Changed from energy mode to operation mode
    exclude_recently_used: Optional[List[str]] = None,
    time_of_day: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """Get tasks for category with archetype, mode, and rotation filters.

    Args:
        category: Task category
        archetype: User archetype
        mode: Operation mode (brain_power, travel, fasting, productivity, recovery)
        exclude_recently_used: List of variation_group values to exclude
        time_of_day: Time preference (morning/afternoon/evening/any)
        limit: Max tasks to return

    Returns:
        List of matching tasks with scores
    """
    try:
        # Build mode constraints
        mode_constraints = self._build_mode_constraints(mode)

        # Build query with mode filtering
        query = f"""
            SELECT
                tl.*,
                CASE
                    WHEN '{archetype}' = ANY(tl.archetype_fit) THEN 1.0
                    ELSE 0.5
                END as archetype_score,
                CASE
                    WHEN '{mode}' = tl.preferred_mode THEN 1.5
                    WHEN '{mode}' = ANY(tl.compatible_modes) THEN 1.0
                    ELSE 0.3
                END as mode_score
            FROM task_library tl
            WHERE tl.category = $1
              AND tl.is_active = true
              {mode_constraints}
              {"AND tl.variation_group NOT IN (" + ",".join([f"${i+2}" for i in range(len(exclude_recently_used))]) + ")" if exclude_recently_used else ""}
              {f"AND (tl.time_of_day_preference = '{time_of_day}' OR tl.time_of_day_preference = 'any')" if time_of_day and time_of_day != 'any' else ""}
            ORDER BY
                (archetype_score + mode_score) DESC,
                RANDOM()
            LIMIT ${len(exclude_recently_used) + 2 if exclude_recently_used else 2}
        """

        params = [category]
        if exclude_recently_used:
            params.extend(exclude_recently_used)
        params.append(limit)

        results = await self.db.fetch(query, *params)

        if not results:
            logger.warning(f"No tasks found for category={category}, mode={mode}")
            return []

        return [dict(row) for row in results]

    except Exception as e:
        logger.error(f"Error getting tasks for category {category}: {e}")
        return []

def _build_mode_constraints(self, mode: str) -> str:
    """Build SQL constraints based on mode.

    Args:
        mode: Operation mode

    Returns:
        SQL WHERE clause fragment
    """
    mode_rules = {
        'brain_power': "AND tl.intensity_level IN ('light', 'moderate')",  # No intense physical
        'travel': "AND tl.requires_equipment = false",  # Portable tasks only
        'fasting': "AND tl.energy_requirement IN ('low', 'moderate')",  # Energy preservation
        'productivity': "AND tl.category NOT IN ('movement', 'recovery')",  # Focus on work/wellness
        'recovery': "AND tl.category IN ('recovery', 'wellness', 'hydration')"  # Rest-focused
    }

    return mode_rules.get(mode, "")  # No constraints for unknown modes
```

**Add mode fields to task library seed:**

**File:** `services/seeding/task_library_seed.py`

**Add mode metadata to each task:**

```python
# Example task with mode metadata
{
    'name': 'Light Morning Stretch',
    'category': 'movement',
    # ... other fields ...
    'preferred_mode': 'brain_power',  # NEW
    'compatible_modes': ['brain_power', 'productivity', 'recovery'],  # NEW
    'requires_equipment': False,  # NEW
    'intensity_level': 'light',  # NEW: light, moderate, intense
    'energy_requirement': 'low'  # NEW: low, moderate, high
}
```

**Database migration:**

**File:** `supabase/migrations/007_add_mode_support.sql`

```sql
-- Add mode support columns to task_library
ALTER TABLE task_library
ADD COLUMN IF NOT EXISTS preferred_mode VARCHAR(50),
ADD COLUMN IF NOT EXISTS compatible_modes TEXT[],
ADD COLUMN IF NOT EXISTS requires_equipment BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS intensity_level VARCHAR(20),
ADD COLUMN IF NOT EXISTS energy_requirement VARCHAR(20);

-- Create index for mode filtering
CREATE INDEX IF NOT EXISTS idx_task_library_mode
ON task_library(category, preferred_mode, requires_equipment);
```

**Acceptance Criteria:**
- ✅ Mode constraints filter tasks appropriately
- ✅ brain_power mode avoids intense workouts
- ✅ travel mode only selects portable tasks
- ✅ fasting mode prioritizes low-energy tasks
- ✅ productivity mode focuses on work/wellness
- ✅ recovery mode emphasizes rest

---

## Phase 6: E2E Testing (Week 4)

### 6.1 Create Multi-Day Journey Test

**File:** `testing/test_hybrid_system_journey.py`

**Implementation:**

```python
"""
Multi-Day User Journey Test for Hybrid System
===============================================

Simulates Flutter app behavior over multiple days:
1. Generate hybrid plans (AI structure + Dynamic tasks)
2. Record task feedback (completions, ratings)
3. Verify preference evolution
4. Test mode switching
5. Validate shuffle frequency
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List

# Load environment
load_dotenv()

# Test configuration
TEST_USER_ID = "a57f70b4-d0a4-4aef-b721-a4b526f64869"
TEST_ARCHETYPE = "peak_performer"
TEST_DAYS = 7  # Simulate 7 days
TEST_MODE = "brain_power"

async def simulate_multi_day_journey():
    """Simulate user journey over multiple days."""

    print("\n" + "="*80)
    print("HYBRID SYSTEM MULTI-DAY JOURNEY TEST")
    print("="*80)
    print(f"\nTest Configuration:")
    print(f"  User ID: {TEST_USER_ID}")
    print(f"  Archetype: {TEST_ARCHETYPE}")
    print(f"  Mode: {TEST_MODE}")
    print(f"  Days: {TEST_DAYS}")
    print(f"  Shuffle Frequency: {os.getenv('SHUFFLE_FREQUENCY', 'weekly')}")
    print("="*80 + "\n")

    from services.dynamic_personalization.dynamic_task_selector import DynamicTaskSelector
    from services.dynamic_personalization.feedback_analyzer_service import FeedbackAnalyzerService

    selector = DynamicTaskSelector()
    feedback_service = FeedbackAnalyzerService()

    await selector.initialize()
    await feedback_service.initialize()

    try:
        # Simulate each day
        for day in range(1, TEST_DAYS + 1):
            plan_date = datetime.now() + timedelta(days=day-1)

            print(f"\n{'─'*80}")
            print(f"DAY {day}: {plan_date.strftime('%Y-%m-%d %A')}")
            print(f"{'─'*80}")

            # Generate hybrid plan
            plan = await _generate_hybrid_plan_for_day(
                user_id=TEST_USER_ID,
                archetype=TEST_ARCHETYPE,
                mode=TEST_MODE,
                plan_date=plan_date,
                selector=selector
            )

            if not plan:
                print(f"  ✗ Failed to generate plan for day {day}")
                continue

            # Display plan
            stats = plan.get('replacement_stats', {})
            print(f"\n  Plan Generated:")
            print(f"    Total tasks: {stats.get('total_tasks', 0)}")
            print(f"    Library tasks: {stats.get('replaced', 0)}")
            print(f"    AI tasks: {stats.get('kept_ai', 0)}")

            # Simulate user completing tasks with feedback
            completed_tasks = await _simulate_task_completion(
                user_id=TEST_USER_ID,
                plan=plan,
                day=day,
                feedback_service=feedback_service
            )

            print(f"\n  User Activity:")
            print(f"    Completed: {completed_tasks['completed']}/{completed_tasks['total']}")
            print(f"    Avg Satisfaction: {completed_tasks['avg_satisfaction']:.1f}/5.0")

            # Show preference evolution (every 3 days)
            if day % 3 == 0:
                await _show_preference_evolution(
                    user_id=TEST_USER_ID,
                    day=day,
                    feedback_service=feedback_service
                )

            # Simulate mode change on day 4
            if day == 4:
                TEST_MODE = "productivity"
                print(f"\n  🔄 Mode changed to: {TEST_MODE}")

        # Final summary
        print(f"\n{'═'*80}")
        print("JOURNEY SUMMARY")
        print(f"{'═'*80}")

        await _show_final_summary(
            user_id=TEST_USER_ID,
            feedback_service=feedback_service
        )

    finally:
        await selector.close()
        await feedback_service.close()


async def _generate_hybrid_plan_for_day(
    user_id: str,
    archetype: str,
    mode: str,
    plan_date: datetime,
    selector: 'DynamicTaskSelector'
) -> Dict:
    """Generate hybrid plan for a specific day."""

    # Sample AI plan structure (in real system, this comes from AI agent)
    ai_plan = {
        "time_blocks": [
            {
                "name": "Morning Activation",
                "start_time": "07:00",
                "end_time": "09:00",
                "zone_type": "maintenance",
                "tasks": [
                    {
                        "title": "Morning Hydration",
                        "description": "Drink water",
                        "start_time": "07:00",
                        "end_time": "07:05",
                        "task_type": "hydration",
                        "priority": "high"
                    },
                    {
                        "title": "Light Movement",
                        "description": "Stretching",
                        "start_time": "07:15",
                        "end_time": "07:30",
                        "task_type": "movement",
                        "priority": "medium"
                    }
                ]
            },
            {
                "name": "Peak Energy Block",
                "start_time": "09:00",
                "end_time": "12:00",
                "zone_type": "peak",
                "tasks": [
                    {
                        "title": "Deep Work Session",
                        "description": "Focus work",
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "task_type": "work",
                        "priority": "high"
                    },
                    {
                        "title": "Protein Snack",
                        "description": "Nutrition break",
                        "start_time": "11:00",
                        "end_time": "11:15",
                        "task_type": "nutrition",
                        "priority": "medium"
                    }
                ]
            }
        ]
    }

    # Replace with library tasks
    hybrid_plan = await selector.replace_ai_tasks_with_library(
        user_id=user_id,
        ai_plan=ai_plan,
        archetype=archetype,
        mode=mode
    )

    return hybrid_plan


async def _simulate_task_completion(
    user_id: str,
    plan: Dict,
    day: int,
    feedback_service: 'FeedbackAnalyzerService'
) -> Dict:
    """Simulate user completing tasks with varying satisfaction."""

    import random

    total_tasks = 0
    completed_tasks = 0
    satisfaction_sum = 0

    for block in plan.get('time_blocks', []):
        for task in block.get('tasks', []):
            total_tasks += 1

            # 70% completion rate (increases over days as preferences learned)
            completion_rate = 0.7 + (day * 0.03)
            completed = random.random() < completion_rate

            if completed:
                completed_tasks += 1

                # Satisfaction: Library tasks generally higher than AI tasks
                if task.get('is_dynamic'):
                    satisfaction = random.randint(3, 5)  # Library tasks: 3-5
                else:
                    satisfaction = random.randint(2, 4)  # AI tasks: 2-4

                satisfaction_sum += satisfaction

                # Record feedback
                await feedback_service.record_task_feedback(
                    user_id=user_id,
                    task_library_id=task.get('task_library_id'),
                    task_name=task.get('title'),
                    category=task.get('task_type'),
                    completed=True,
                    satisfaction_rating=satisfaction,
                    completion_timing='on_time',
                    feedback_text=None,
                    skip_reason=None
                )

    avg_satisfaction = satisfaction_sum / completed_tasks if completed_tasks > 0 else 0

    return {
        'total': total_tasks,
        'completed': completed_tasks,
        'avg_satisfaction': avg_satisfaction
    }


async def _show_preference_evolution(
    user_id: str,
    day: int,
    feedback_service: 'FeedbackAnalyzerService'
):
    """Show how preferences have evolved."""

    profile = await feedback_service.get_user_preferences(user_id)

    if profile:
        print(f"\n  📊 Preference Evolution (Day {day}):")

        category_affinity = profile.get('category_affinity', {})
        if category_affinity:
            top_categories = sorted(category_affinity.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"    Top Categories: {', '.join([f'{cat} ({score:.2f})' for cat, score in top_categories])}")

        print(f"    Consistency Score: {profile.get('consistency_score', 0):.2f}")
        print(f"    Variety Seeking: {profile.get('variety_seeking_score', 0):.2f}")
        print(f"    Learning Phase: {profile.get('current_learning_phase', 'discovery')}")


async def _show_final_summary(
    user_id: str,
    feedback_service: 'FeedbackAnalyzerService'
):
    """Show final journey summary."""

    # Get total feedback count
    query = """
        SELECT
            COUNT(*) as total_feedback,
            SUM(CASE WHEN completed THEN 1 ELSE 0 END) as total_completed,
            AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating ELSE 0 END) as avg_satisfaction,
            COUNT(DISTINCT category) as categories_tried
        FROM user_task_feedback
        WHERE user_id = $1
    """

    from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
    db = SupabaseAsyncPGAdapter()
    await db.connect()

    result = await db.fetchrow(query, user_id)
    await db.close()

    if result:
        print(f"\n  Total Feedback Records: {result['total_feedback']}")
        print(f"  Total Completed Tasks: {result['total_completed']}")
        print(f"  Average Satisfaction: {result['avg_satisfaction']:.2f}/5.0")
        print(f"  Categories Tried: {result['categories_tried']}")

    # Get final preferences
    profile = await feedback_service.get_user_preferences(user_id)

    if profile:
        print(f"\n  Final Learning State:")
        print(f"    Phase: {profile.get('current_learning_phase', 'unknown')}")
        print(f"    Consistency: {profile.get('consistency_score', 0):.2f}")
        print(f"    Variety Seeking: {profile.get('variety_seeking_score', 0):.2f}")

        category_affinity = profile.get('category_affinity', {})
        if category_affinity:
            print(f"\n  Category Preferences:")
            for cat, score in sorted(category_affinity.items(), key=lambda x: x[1], reverse=True):
                print(f"    {cat}: {score:.2f}")

    print(f"\n{'═'*80}")
    print("✓ Journey test completed successfully")
    print(f"{'═'*80}\n")


if __name__ == "__main__":
    asyncio.run(simulate_multi_day_journey())
```

**Run Test:**
```bash
# Enable hybrid system
export ENABLE_DYNAMIC_TASK_SELECTION=true
export SHUFFLE_FREQUENCY=weekly

# Run journey test
python testing/test_hybrid_system_journey.py

# Expected output:
# - 7 days of plan generation
# - Task completion simulation
# - Preference evolution tracking
# - Learning phase transitions
# - Final summary with insights
```

**Acceptance Criteria:**
- ✅ Plans generated for all 7 days
- ✅ Task replacement stats show library usage
- ✅ Feedback recorded correctly
- ✅ Preferences evolve over time
- ✅ Learning phase transitions occur
- ✅ Mode switching works correctly

---

## Phase 7: Gradual Rollout Strategy (Week 4)

### 7.1 Alpha Testing (Single User)

**Duration:** 3-5 days

**Steps:**

1. **Enable for Test User**
   ```bash
   # In .env
   ENABLE_DYNAMIC_TASK_SELECTION=true
   SHUFFLE_FREQUENCY=weekly
   DEFAULT_MODE=brain_power
   ```

2. **Monitor Logs**
   ```bash
   # Watch for errors in real-time
   tail -f logs/app.log | grep -E "(HYBRID|DYNAMIC|ERROR)"
   ```

3. **Verify Metrics**
   - API response time < 2 seconds
   - Task replacement rate > 70%
   - User completion rate similar to AI baseline
   - No error rate increase

4. **User Feedback**
   - Task quality subjective rating
   - Variety perception
   - Relevance to archetype/mode

**Success Criteria:**
- ✅ Zero crashes
- ✅ API latency acceptable
- ✅ User satisfaction maintained or improved
- ✅ Cost savings confirmed (check OpenAI usage)

### 7.2 Beta Testing (10% of Users)

**Duration:** 1-2 weeks

**Steps:**

1. **User Segmentation**

   Add user-level feature flag:

   **File:** `services/api_gateway/openai_main.py`

   ```python
   async def _is_user_in_beta(user_id: str) -> bool:
       """Check if user is in beta group for hybrid system."""

       # Option 1: Percentage-based rollout
       import hashlib
       hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
       return (hash_value % 100) < 10  # 10% of users

       # Option 2: Explicit allowlist (commented out)
       # BETA_USERS = os.getenv("BETA_USERS", "").split(",")
       # return user_id in BETA_USERS

   # In generate_routine_plan endpoint:
   if dynamic_config.is_hybrid_enabled() and await _is_user_in_beta(user_id):
       # Use hybrid flow
       ...
   ```

2. **A/B Comparison Dashboard**

   Track metrics for hybrid vs AI-only users:
   - Plan generation time
   - Task completion rate
   - User satisfaction ratings
   - Skip reasons
   - Cost per plan

3. **Monitoring**
   ```bash
   # Daily metrics check
   python testing/monitor_hybrid_performance.py
   ```

**Success Criteria:**
- ✅ Hybrid users have ≥ AI-only users completion rate
- ✅ 75% cost reduction confirmed
- ✅ No significant quality degradation
- ✅ Positive or neutral user feedback

### 7.3 Production Rollout (100% of Users)

**Duration:** Gradual over 1 week

**Steps:**

1. **Staged Rollout**
   - Day 1: 25% of users
   - Day 3: 50% of users
   - Day 5: 75% of users
   - Day 7: 100% of users

2. **Rollback Plan**
   ```bash
   # If issues arise, immediately disable
   export ENABLE_DYNAMIC_TASK_SELECTION=false

   # Restart service
   # No code deployment needed - just env var change
   ```

3. **Post-Rollout Monitoring** (2 weeks)
   - Daily metrics review
   - User support ticket volume
   - API error rate
   - Database performance

**Success Criteria:**
- ✅ No increase in support tickets
- ✅ API uptime maintained (99.9%)
- ✅ Cost savings realized
- ✅ User retention stable

---

## Phase 8: Post-Launch Optimization (Ongoing)

### 8.1 Feedback Loop Refinement

**Month 1-2 Focus:**

1. **Tune Learning Phase Thresholds**
   - Analyze actual user progression
   - Adjust Discovery → Establishment transition
   - Optimize Establishment → Mastery criteria

2. **Expand Task Library**
   - Add tasks based on user skip reasons
   - Fill gaps in coverage (modes, archetypes)
   - Target 100+ tasks by end of Month 2

3. **Improve Category Mapping**
   - Analyze AI tasks that fail to map
   - Add new patterns to CategoryMapper
   - Increase replacement rate to 90%+

### 8.2 AI Strategic Layer Optimization

**Month 2-3 Focus:**

1. **Fix Circadian Analysis** (CRITICAL)
   - Personalize time blocks based on sleep/wake
   - Test with diverse user schedules
   - Validate timing accuracy

2. **Feedback to AI Prompts**
   - Analyze which time block structures work best
   - Update system prompts based on patterns
   - Reduce shuffle frequency needs

3. **Mode-Specific AI Prompts**
   - Create specialized prompts per mode
   - Optimize block structure for travel, fasting, etc.
   - Validate mode effectiveness

### 8.3 Advanced Features

**Month 3+ Roadmap:**

1. **Context-Aware Selection**
   - Weather-based task adaptation
   - Calendar event integration
   - Location-aware suggestions

2. **Social Features**
   - Task recommendations from similar users
   - Community-contributed tasks
   - Archetype-specific leaderboards

3. **AI Enhancement**
   - GPT-4 → GPT-5 migration
   - Multimodal input (images, voice)
   - Real-time adaptation during day

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Verify all 5 database tables exist
- [ ] Run task library seeding (50 tasks)
- [ ] Confirm 10/10 dynamic tests passing
- [ ] Fix circadian analysis service
- [ ] Test with user `a57f70b4-d0a4-4aef-b721-a4b526f64869`

### Week 2: Core Services
- [ ] Create `dynamic_task_selector.py`
- [ ] Create `category_mapper.py`
- [ ] Test task replacement with sample AI plan
- [ ] Verify replacement stats tracking
- [ ] Test fallback to AI tasks

### Week 3: Integration
- [ ] Add feature flags to config
- [ ] Modify routine API endpoint
- [ ] Add shuffle frequency logic
- [ ] Add mode support to task library
- [ ] Run migration 006 (caching) and 007 (modes)
- [ ] Test with ENABLE_DYNAMIC_TASK_SELECTION=false (verify no breaking changes)
- [ ] Test with ENABLE_DYNAMIC_TASK_SELECTION=true (hybrid flow)

### Week 4: Testing & Rollout
- [ ] Create multi-day journey test
- [ ] Run 7-day simulation successfully
- [ ] Alpha test with single user (3-5 days)
- [ ] Beta test with 10% users (1-2 weeks)
- [ ] Production rollout (gradual over 1 week)
- [ ] Monitor metrics daily

### Ongoing
- [ ] Tune learning phase thresholds
- [ ] Expand task library to 100+ tasks
- [ ] Improve category mapping accuracy
- [ ] Optimize AI strategic layer
- [ ] Add advanced features

---

## Risk Mitigation

### Risk 1: Task Library Coverage Gaps

**Risk:** User gets AI tasks due to no library matches

**Mitigation:**
- Start with comprehensive 50-task seed
- Monitor replacement rate daily
- Add tasks proactively based on gaps
- Target: 80%+ replacement rate

### Risk 2: Quality Degradation

**Risk:** Library tasks less relevant than AI tasks

**Mitigation:**
- A/B test hybrid vs AI-only users
- Track completion rate and satisfaction
- Rollback if metrics decline >10%
- Iterate on task scoring algorithm

### Risk 3: Performance Impact

**Risk:** Dynamic selection adds latency

**Mitigation:**
- Profile and optimize database queries
- Add caching for frequently accessed tasks
- Set API timeout at 3 seconds
- Monitor P95 latency

### Risk 4: Feature Flag Bugs

**Risk:** Switch doesn't work, breaks existing flow

**Mitigation:**
- Comprehensive testing with switch OFF first
- Test all user flows before enabling
- Keep AI flow completely unchanged
- Rollback via env var (no deployment)

### Risk 5: Circadian Analysis Still Broken

**Risk:** Personalized timing doesn't work

**Mitigation:**
- Use fixed time blocks as fallback
- Test with multiple user schedules
- Document known limitations
- Plan fix in Phase 1 (critical)

---

## Success Metrics

### Cost Metrics
- **Target:** 75% reduction in plan generation cost
- **Baseline:** $0.084/plan (all AI)
- **Goal:** $0.02/plan (AI structure + Dynamic tasks)

### Quality Metrics
- **Completion Rate:** ≥ current AI baseline
- **Satisfaction:** ≥ current AI baseline
- **Variety Score:** Improved (measured by unique tasks per week)

### Technical Metrics
- **API Latency:** < 2 seconds P95
- **Task Replacement Rate:** > 80%
- **Error Rate:** < 1%
- **Uptime:** > 99.9%

### User Engagement
- **Retention:** No decline
- **Daily Active Users:** Stable or improved
- **Plan Completion:** Improved (due to better personalization)

---

## Support and Troubleshooting

### Common Issues

**Issue 1: No library tasks returned**

```bash
# Check task library count
python -c "
import asyncio
from services.dynamic_personalization.task_library_service import TaskLibraryService

async def check():
    service = TaskLibraryService()
    await service.initialize()
    counts = await service.get_task_count_by_category()
    print(counts)
    await service.close()

asyncio.run(check())
"

# If empty, re-run seeding
python services/seeding/task_library_seed.py
```

**Issue 2: Feature switch not working**

```bash
# Verify env var is set
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'ENABLE_DYNAMIC_TASK_SELECTION={os.getenv(\"ENABLE_DYNAMIC_TASK_SELECTION\")}'

# Expected: true
```

**Issue 3: High API latency**

```bash
# Profile slow queries
# Add timing logs to adapter.py

# Check database connection pool
# Increase pool size if needed
```

**Issue 4: Low replacement rate**

```bash
# Check category mapper accuracy
python testing/test_dynamic_task_selector.py

# Review unmapped AI tasks in logs
grep "No category mapping" logs/app.log
```

---

## Conclusion

This phased implementation plan provides a structured approach to integrating the Dynamic Hybrid Architecture while preserving the existing AI flow as a safety net. The feature-switched design allows for gradual rollout, easy rollback, and iterative improvement based on real-world feedback.

**Key Success Factors:**
1. Zero breaking changes to existing flow
2. Comprehensive testing at each phase
3. Gradual rollout with clear success criteria
4. Continuous monitoring and optimization
5. User feedback integration

**Timeline Summary:**
- Week 1: Foundation setup
- Week 2: Core services implementation
- Week 3: Integration and mode support
- Week 4: Testing and gradual rollout
- Ongoing: Optimization and feature expansion

By following this plan, the hybrid system can be safely deployed to production while maintaining high quality, reducing costs, and improving personalization over time.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Next Review:** After Week 4 (Production Rollout Complete)
