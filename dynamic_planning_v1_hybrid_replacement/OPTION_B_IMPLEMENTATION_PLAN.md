# Option B: Feedback-Driven Pre-Seeding Implementation Plan

## Executive Summary

**Approach**: Select tasks from library based on user feedback → Feed to AI → AI creates schedule with those tasks

**Benefits**:
- ✅ Cleaner architecture (AI focuses on scheduling, library provides content)
- ✅ Feedback-first (tasks selected based on completion/satisfaction)
- ✅ Progressive enhancement (Day 1 pure AI, Day 2+ library tasks)
- ✅ Single plan generation path (no post-processing)

---

## Current State (What We Have)

### Working Components ✅
1. **Task Library** (`task_library` table) - 50+ vetted tasks
2. **Feedback Collection** (`task_checkins`, `task_feedback_complete` tables)
3. **Adaptive Task Selector** - Selects tasks based on user history
4. **Learning Phase Manager** - Tracks discovery → establishment → mastery
5. **Circadian Analysis** - Identifies optimal time blocks

### Broken Components ❌
1. **Hybrid Replacement** - Fails with schema/parsing errors
2. **Standalone Dynamic Generator** - Foreign key constraint violations

---

## Architecture Comparison

### V1 (Hybrid Replacement) - DEPRECATED
```
AI generates full plan (12 tasks)
  ↓
Parse AI output JSON
  ↓
Replace 5 tasks with library tasks
  ↓
Re-save modified plan
  ↓
Extract to plan_items
```

**Issues**: Complex, fragile, error-prone

### V2 (Feedback-Driven Pre-seeding) - NEW
```
Day 1: Pure AI plan (cold start)
  ↓
User completes tasks → Feedback collected
  ↓
Day 2+: Adaptive selector picks 5-8 library tasks
  ↓
AI receives: "Schedule these specific tasks in optimal time blocks"
  ↓
AI returns structured plan with YOUR tasks
  ↓
Extract to plan_items (single path, clean)
```

**Benefits**: Simple, robust, feedback-driven

---

## Phase 1: Preparation & Cleanup (1-2 hours)

### 1.1 Archive V1 Implementation
```bash
# Already created:
# - archive/dynamic_planning_v1_hybrid_replacement/README.md
# - archive/dynamic_planning_v1_hybrid_replacement/INVENTORY.md

# Archive documentation files
mkdir -p archive/dynamic_planning_v1_hybrid_replacement/docs
mv DYNAMIC_HYBRID_IMPLEMENTATION_PLAN.md archive/dynamic_planning_v1_hybrid_replacement/docs/
mv TEST_FAILURE_ANALYSIS.md archive/dynamic_planning_v1_hybrid_replacement/docs/
mv FINAL_DUAL_MODE_SETUP.md archive/dynamic_planning_v1_hybrid_replacement/docs/
```

**Status**: ✅ DONE (this session)

### 1.2 Update Configuration
**File**: `config/dynamic_personalization_config.py`

**Changes**:
```python
# Add new flag
ENABLE_FEEDBACK_PRESEEDING = os.getenv('ENABLE_FEEDBACK_PRESEEDING', 'true').lower() == 'true'

# Deprecate old flag
ENABLE_HYBRID_REPLACEMENT = False  # Deprecated - Use ENABLE_FEEDBACK_PRESEEDING

# Add configuration for pre-seeding
PRESEEDING_MIN_TASKS = 5  # Minimum library tasks to include
PRESEEDING_MAX_TASKS = 8  # Maximum library tasks to include
PRESEEDING_MIN_FEEDBACK = 3  # Minimum feedback items before pre-seeding
```

**Outcome**: Feature flag for V2 approach

---

## Phase 2: Pre-Generation Task Selection (3-4 hours)

### 2.1 Create Task Pre-Selector Service

**New File**: `services/dynamic_personalization/task_preseeder.py`

**Purpose**: Select library tasks BEFORE AI generation based on feedback

**Key Methods**:
```python
class TaskPreseeder:
    async def select_tasks_for_plan(
        self,
        user_id: str,
        archetype: str,
        mode: str,
        plan_date: datetime
    ) -> Dict:
        """
        Select 5-8 tasks from library based on:
        1. User feedback (completion rate, satisfaction)
        2. Learning phase (discovery/establishment/mastery)
        3. Task rotation (avoid recently used)
        4. Archetype + mode fit

        Returns:
            {
                'preselected_tasks': [
                    {
                        'task_library_id': 'uuid',
                        'category': 'hydration',
                        'name': 'Morning Lemon Water',
                        'description': '...',
                        'duration_minutes': 5,
                        'time_preference': 'morning',
                        'selection_reason': 'High satisfaction (4.5/5)',
                        'source': 'library'
                    },
                    ...
                ],
                'selection_stats': {
                    'total_selected': 5,
                    'from_feedback': 3,
                    'from_discovery': 2,
                    'categories_covered': ['hydration', 'movement', ...]
                },
                'has_sufficient_feedback': True  # If >= 3 feedback items
            }
        """
```

**Implementation Notes**:
- Reuse `AdaptiveTaskSelector` for core logic
- Add feedback-scoring algorithm
- Prioritize tasks with:
  - High completion rate (>80%)
  - High satisfaction (≥4/5)
  - Moderate difficulty (avoid too hard/too easy)

**Testing**:
```bash
python testing/test_task_preseeder.py
```

---

## Phase 3: AI Prompt Enhancement (2-3 hours)

### 3.1 Modify Routine Generation Prompt

**File**: `shared_libs/utils/system_prompts.py` or relevant prompt file

**Current Prompt** (simplified):
```
Generate a daily routine for {archetype} with {mode} energy.
Create time blocks with appropriate tasks.
```

**New Prompt** (with pre-seeding):
```
Generate a daily routine for {archetype} with {mode} energy.

IMPORTANT: You must include the following pre-selected tasks in your plan:
{preselected_tasks_json}

These tasks have been selected based on user feedback and preferences.
Your job is to:
1. Schedule these tasks in optimal time blocks based on circadian analysis
2. Add 4-7 additional tasks to complete the routine
3. Ensure smooth transitions between activities
4. Respect time preferences (e.g., "morning", "evening")

Pre-selected tasks to include:
[
  {
    "name": "Morning Lemon Water",
    "duration": 5,
    "time_preference": "morning",
    "reason": "User loves this (5/5 satisfaction)"
  },
  ...
]

Output format: JSON with time_blocks containing all tasks
```

**Key Changes**:
- Explicitly list pre-selected tasks
- Instruct AI to schedule them appropriately
- AI fills gaps with additional tasks
- Clear structure for mixing library + AI tasks

---

## Phase 4: Integration in API Gateway (3-4 hours)

### 4.1 Modify Routine Generation Endpoint

**File**: `services/api_gateway/openai_main.py`

**Current Flow**:
```python
# Line ~1200-1400
async def generate_routine_plan(...):
    # Generate AI plan
    routine_plan = await ai_generation_service.generate_routine(...)

    # [LINES 1368-1416] Hybrid replacement (REMOVE THIS)

    # Extract plan
    await plan_extraction_service.extract_plan(...)
```

**New Flow**:
```python
async def generate_routine_plan(...):
    # NEW: Check if user has sufficient feedback for pre-seeding
    if config.is_feedback_preseeding_enabled():
        preseeder = TaskPreseeder()
        await preseeder.initialize()

        preseeding_result = await preseeder.select_tasks_for_plan(
            user_id=user_id,
            archetype=archetype,
            mode=mode,
            plan_date=plan_date
        )

        await preseeder.close()

        if preseeding_result['has_sufficient_feedback']:
            print(f"[INFO] [PRESEED] Selected {len(preseeding_result['preselected_tasks'])} library tasks")

            # Enhance AI context with pre-selected tasks
            enhanced_context = _build_enhanced_context(
                context=original_context,
                preselected_tasks=preseeding_result['preselected_tasks']
            )
        else:
            print(f"[INFO] [PRESEED] Insufficient feedback - using pure AI generation")
            enhanced_context = original_context
    else:
        enhanced_context = original_context

    # Generate AI plan (with enhanced context if pre-seeding enabled)
    routine_plan = await ai_generation_service.generate_routine(
        context=enhanced_context,
        ...
    )

    # REMOVE: Lines 1368-1416 (hybrid replacement logic)

    # Extract plan (single path, clean)
    await plan_extraction_service.extract_plan(...)

    return routine_plan
```

**Testing**:
- Cold start (Day 1): Should see `[PRESEED] Insufficient feedback`
- Warm start (Day 2+): Should see `[PRESEED] Selected 5 library tasks`

---

## Phase 5: Plan Extraction Enhancement (1-2 hours)

### 5.1 Update Plan Extraction Logic

**File**: `services/plan_extraction_service.py`

**Current Behavior**: All tasks marked as `source='ai'`

**New Behavior**: Detect library tasks from AI response

**Implementation**:
```python
def _extract_task_from_ai_plan(self, task_dict):
    """
    Extract task and detect if it's from library.

    Check if task name/description matches a library task exactly.
    If so, populate task_library_id and source='library'.
    Otherwise, source='ai'.
    """
    task_name = task_dict.get('title')

    # Check if this task name matches a library task
    library_match = await self.db.fetchrow(
        "SELECT id, variation_group FROM task_library WHERE name = $1",
        task_name
    )

    if library_match:
        return {
            'source': 'library',
            'task_library_id': library_match['id'],
            'variation_group': library_match['variation_group'],
            ...
        }
    else:
        return {
            'source': 'ai',
            'task_library_id': None,
            'variation_group': None,
            ...
        }
```

**Outcome**: `plan_items` table correctly shows `source='library'` for pre-selected tasks

---

## Phase 6: Testing & Validation (2-3 hours)

### 6.1 Create Comprehensive Test Suite

**New File**: `testing/test_feedback_preseeding_e2e.py`

**Test Scenarios**:

#### Test 1: Cold Start (No Feedback)
```python
async def test_cold_start_pure_ai():
    """
    Day 1: User has no feedback
    Expected: Pure AI plan, all tasks source='ai'
    """
    plan = await generate_routine_plan(
        user_id='new_user_001',
        archetype='foundation_builder',
        mode='brain_power'
    )

    assert plan['source'] == 'ai'
    assert all(task['source'] == 'ai' for task in plan['tasks'])
```

#### Test 2: Warm Start (With Feedback)
```python
async def test_warm_start_with_feedback():
    """
    Day 2+: User has completed 5+ tasks with feedback
    Expected: Mixed plan (5-8 library + AI tasks)
    """
    # Setup: Create feedback for user
    await create_mock_feedback(
        user_id='existing_user_001',
        completed_tasks=[
            {'task': 'Morning Lemon Water', 'satisfaction': 5},
            {'task': 'Quick Stretch', 'satisfaction': 4},
            ...
        ]
    )

    plan = await generate_routine_plan(
        user_id='existing_user_001',
        archetype='foundation_builder',
        mode='brain_power'
    )

    library_tasks = [t for t in plan['tasks'] if t['source'] == 'library']
    assert len(library_tasks) >= 5, "Should have at least 5 library tasks"
    assert len(library_tasks) <= 8, "Should have at most 8 library tasks"
```

#### Test 3: Task Rotation
```python
async def test_task_rotation_prevents_duplicates():
    """
    Day 3: User shouldn't see same tasks as Day 2
    Expected: Different library tasks selected
    """
    day2_plan = await generate_routine_plan(user_id='user', date=date(2025, 10, 28))
    day3_plan = await generate_routine_plan(user_id='user', date=date(2025, 10, 29))

    day2_library_ids = {t['task_library_id'] for t in day2_plan['tasks'] if t['source'] == 'library'}
    day3_library_ids = {t['task_library_id'] for t in day3_plan['tasks'] if t['source'] == 'library'}

    overlap = day2_library_ids & day3_library_ids
    assert len(overlap) <= 2, "Should have maximum 2 overlapping tasks"
```

### 6.2 Integration Testing

**Test Flow**:
1. Create new user → Generate Day 1 plan (pure AI)
2. Complete 5 tasks with high satisfaction → Record feedback
3. Generate Day 2 plan (should include 5+ library tasks)
4. Verify `plan_items` table shows correct `source` values
5. Verify app displays library tasks correctly

**Success Criteria**:
- ✅ Day 1: 100% AI tasks
- ✅ Day 2+: 40-60% library tasks (5-8 out of 12)
- ✅ No errors in plan extraction
- ✅ Correct `source` attribution in database

---

## Phase 7: Monitoring & Rollout (Ongoing)

### 7.1 Add Logging & Metrics

**New Logs**:
```
[INFO] [PRESEED] Analyzing feedback for user {user_id}
[INFO] [PRESEED] Found {count} high-satisfaction tasks
[INFO] [PRESEED] Selected {count} library tasks: {task_names}
[INFO] [PRESEED] Insufficient feedback ({count}/3) - using pure AI
[OK] [PRESEED] Pre-seeding successful: {library_count} library + {ai_count} AI tasks
```

**Metrics to Track**:
- Feedback collection rate (% of tasks with feedback)
- Pre-seeding activation rate (% of plans using library tasks)
- Library task replacement rate (% of tasks from library)
- User satisfaction by source (library vs AI tasks)

### 7.2 Gradual Rollout

**Week 1**: Test with 1-2 users
- Monitor logs for errors
- Verify task selection quality
- Collect user feedback

**Week 2**: Expand to 10-20 users
- Compare satisfaction: library tasks vs AI tasks
- Fine-tune selection algorithm

**Week 3+**: Full rollout
- Enable `ENABLE_FEEDBACK_PRESEEDING=true` in production

---

## Phase 8: Cleanup & Documentation (1-2 hours)

### 8.1 Remove Deprecated Code

**Files to Modify**:
```python
# services/api_gateway/openai_main.py
# DELETE lines 1368-1416 (hybrid replacement logic)

# services/dynamic_personalization/dynamic_task_selector.py
# DEPRECATE replace_ai_tasks_with_library() method

# services/dynamic_personalization/dynamic_plan_generator.py
# KEEP for potential direct library-only plans in future
# But mark persist_plan_to_database() as DEPRECATED
```

### 8.2 Update Documentation

**Create**:
- `FEEDBACK_PRESEEDING_GUIDE.md` - How it works
- `MIGRATION_V1_TO_V2.md` - Migration notes

**Update**:
- `README.md` - Add V2 architecture diagram
- `MVP_QUICK_START.md` - Update testing instructions

---

## Success Metrics

### Technical Metrics
- ✅ 0 foreign key constraint errors
- ✅ 0 schema mismatch errors
- ✅ Single plan generation path (no post-processing)
- ✅ >95% successful plan extractions

### User Experience Metrics
- ✅ 40-60% library task replacement rate (Day 2+)
- ✅ ≥4.0/5 average satisfaction for library tasks
- ✅ <2 duplicate tasks within 48 hours
- ✅ ≥80% task completion rate

### Business Metrics
- ✅ Reduced AI costs (fewer tokens for task generation)
- ✅ Increased user engagement (familiar tasks + novelty)
- ✅ Better feedback loop (clear cause-effect)

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| 0. Organize Existing Work | 30 mins | ✅ DONE |
| 1. Preparation & Cleanup | 1-2 hours | 🟡 IN PROGRESS |
| 2. Task Pre-Selector | 3-4 hours | ⏳ PENDING |
| 3. AI Prompt Enhancement | 2-3 hours | ⏳ PENDING |
| 4. API Gateway Integration | 3-4 hours | ⏳ PENDING |
| 5. Plan Extraction Enhancement | 1-2 hours | ⏳ PENDING |
| 6. Testing & Validation | 2-3 hours | ⏳ PENDING |
| 7. Monitoring & Rollout | Ongoing | ⏳ PENDING |
| 8. Cleanup & Documentation | 1-2 hours | ⏳ PENDING |

**Total Estimated Time**: 13-21 hours (2-3 days of focused work)

---

## Risk Mitigation

### Risk 1: AI Doesn't Follow Instructions
**Issue**: AI ignores pre-selected tasks and generates its own

**Mitigation**:
- Use strict JSON schema in prompt
- Validate AI response includes all pre-selected tasks
- Fallback to pure AI if validation fails

### Risk 2: Insufficient Task Library Coverage
**Issue**: Library has only 50 tasks, may not cover all scenarios

**Mitigation**:
- Continue using AI for gap filling
- Monitor categories with low library coverage
- Prioritize expanding task library

### Risk 3: Poor Task Selection Quality
**Issue**: Pre-selected tasks don't fit user's needs

**Mitigation**:
- Start conservatively (5 tasks, not 8)
- Monitor user feedback specifically for library tasks
- Allow manual override in app

---

## Next Steps

**Immediate** (Today):
1. ✅ Create this implementation plan
2. ⏳ Review and approve approach
3. ⏳ Begin Phase 2 (Task Pre-Selector)

**This Week**:
1. Complete Phases 2-5 (core implementation)
2. Run comprehensive tests
3. Fix any bugs

**Next Week**:
1. Test with real users
2. Monitor metrics
3. Iterate based on feedback

---

## Questions & Decisions Needed

1. **Minimum feedback threshold**: Start with 3 or 5 completed tasks?
   - **Recommendation**: 3 (faster activation)

2. **Library task ratio**: 5-8 out of 12 tasks (40-60%)?
   - **Recommendation**: Start with 5 (40%), increase gradually

3. **Pure AI fallback**: Keep generating pure AI plans if pre-seeding fails?
   - **Recommendation**: Yes, always fallback to working system

4. **Feedback quality filter**: Require satisfaction rating ≥3?
   - **Recommendation**: Yes, exclude low-satisfaction tasks

---

**Ready to proceed?** Let me know if you approve this plan and I'll start with Phase 2!
