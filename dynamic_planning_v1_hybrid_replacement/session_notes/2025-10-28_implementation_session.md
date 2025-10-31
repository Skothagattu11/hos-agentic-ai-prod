# Implementation Session Notes - October 28, 2025

## Session Overview

**Duration**: ~4 hours
**Goal**: Implement and test dynamic task selection (hybrid replacement approach)
**Outcome**: Archived V1, pivoting to V2 (feedback-driven pre-seeding)

---

## Timeline

### Hour 1: Understanding the System
- Reviewed existing dynamic planning code
- Analyzed `dynamic_plan_generator.py` and `task_library_service.py`
- Understood dual-mode database architecture (REST API vs PostgreSQL)

### Hour 2: First Test Attempt
- Ran `test_realistic_user_journey_v2.py`
- Encountered multiple schema errors:
  - `dynamic_metadata` column doesn't exist
  - Wrong column names (`user_id` → `profile_id`, `name` → `title`)
  - Missing required fields (`scheduled_end_time`, `plan_date`)

### Hour 3: Schema Fixes & Re-testing
- Fixed `dynamic_plan_generator.py` INSERT statement to match actual schema
- Discovered foreign key constraint issue:
  - `analysis_result_id` must exist in `holistic_analysis_results` table
  - V1 approach creates standalone plans without AI analysis entry
- Task rotation system too aggressive (filtered out ALL tasks after first use)

### Hour 4: Architecture Decision
- Realized V1 (hybrid replacement) is overly complex
- User suggested better approach: pre-seed tasks to AI
- Created comprehensive V2 implementation plan
- Organized and archived all V1 documentation

---

## Key Discoveries

### 1. Database Schema Reality
**Expected** (from old docs):
```sql
CREATE TABLE plan_items (
    id UUID,
    user_id TEXT,
    name TEXT,
    ...
    is_dynamic BOOLEAN,
    dynamic_metadata JSONB
)
```

**Actual** (production table):
```sql
CREATE TABLE plan_items (
    id UUID,
    profile_id TEXT,  -- NOT user_id
    title TEXT,  -- NOT name
    ...
    source TEXT,  -- 'ai' or 'library'
    task_library_id UUID,
    variation_group TEXT,
    -- NO is_dynamic column
    -- NO dynamic_metadata column
)
```

**Lesson**: Always verify schema with actual database, not documentation

### 2. Foreign Key Constraint
`plan_items.analysis_result_id` has FK constraint to `holistic_analysis_results.id`

**V1 Problem**: Dynamic generator creates random UUID, tries to insert without creating parent entry

**V2 Solution**: AI creates `holistic_analysis_results` entry first, then extraction uses that ID

### 3. System Flow Misunderstanding
**What we thought**:
```
Dynamic Generator → Standalone plan → Direct to plan_items
```

**What actually happens**:
```
AI generates plan → Stores in holistic_analysis_results
  ↓
Plan extraction service → Parses JSON → Inserts to plan_items
  ↓
Hybrid replacement tries to modify → Fails
```

### 4. Task Rotation Over-Filtering
**Problem**: After first plan uses 5 tasks, second plan excludes ALL variation groups

**Cause**: Library has 50 tasks but only ~7 variation groups (e.g., `hydration_variations`)

**Impact**: After using one task from a group, entire group excluded for 48 hours

**V2 Solution**: Will implement safety check: if ALL tasks filtered, use them anyway

---

## Code Changes Made

### 1. Fixed `dynamic_plan_generator.py` (Lines 300-355)
**Before**:
```python
INSERT INTO plan_items (
    id, analysis_result_id, profile_id, item_id, time_block, title, description,
    scheduled_time, estimated_duration_minutes, task_type,
    task_library_id, variation_group, is_dynamic, dynamic_metadata
)
VALUES ($1, $2, ..., $14)
```

**After**:
```python
INSERT INTO plan_items (
    id, analysis_result_id, profile_id, item_id, time_block, title, description,
    scheduled_time, scheduled_end_time, estimated_duration_minutes, task_type,
    task_library_id, source, category, subcategory, variation_group,
    plan_date, is_trackable, priority_level, time_block_order, task_order_in_block
)
VALUES ($1, $2, ..., $21)
```

**Changes**:
- Removed: `is_dynamic`, `dynamic_metadata`
- Added: `scheduled_end_time`, `source='library'`, `category`, `plan_date`, etc.
- Fixed: Column name mappings

### 2. Verified `task_library_service.py` (Lines 76-311)
**Already correct**: Dual-mode fetching (development vs production)

**No changes needed**: REST API workarounds already in place

### 3. Verified `shared_libs/supabase_client/adapter.py` (Line 40)
**Already correct**: Using `SUPABASE_SERVICE_KEY` for RLS bypass

**No changes needed**: Service key properly configured

---

## Errors Encountered & Fixed

### Error 1: Schema Mismatch - `dynamic_metadata`
```
Could not find the 'dynamic_metadata' column of 'plan_items' in the schema cache
```
**Fix**: Removed `dynamic_metadata` from INSERT

### Error 2: Schema Mismatch - Column Names
```
Column 'user_id' doesn't exist (should be 'profile_id')
Column 'name' doesn't exist (should be 'title')
```
**Fix**: Updated all column names to match production schema

### Error 3: Foreign Key Constraint
```
insert or update on table "plan_items" violates foreign key constraint "fk_plan_items_analysis_result"
Key (analysis_result_id)=(1264ffff...) is not present in table "holistic_analysis_results"
```
**Fix**: Realized V1 architecture is flawed, pivoted to V2

### Error 4: Task Over-Filtering
```
[DEVELOPMENT] Fetched 7 tasks for category 'hydration'
[DEVELOPMENT] Filtered 7 tasks with excluded variation_groups
[DEVELOPMENT] Fetched 0 tasks for category 'hydration'
```
**Fix**: Documented for V2, will implement safety check

---

## Architecture Decision

### Why V1 Failed
1. **Too complex**: Generate → Parse → Replace → Re-save → Extract
2. **Fragile dependencies**: Requires AI output format to stay consistent
3. **Schema gymnastics**: Standalone plans don't fit existing infrastructure
4. **Poor error handling**: Foreign key violations, schema mismatches

### Why V2 is Better
1. **Simpler flow**: Select → Feed to AI → Extract (one path)
2. **Robust**: AI just schedules pre-selected tasks
3. **Fits infrastructure**: Uses existing `holistic_analysis_results` pattern
4. **Feedback-first**: Task selection based on user completion/satisfaction

### User's Brilliant Insight
> "Initial plan can be purely AI, then from next plan upon check-in and feedback from daily journal, we select items from task_library and feed the routine builder agent to frame a routine using the tasks provided and align them into time blocks using circadian analysis."

**This is perfect because**:
- Day 1: Pure AI (cold start, no feedback yet)
- Day 2+: Pre-selected tasks based on feedback
- AI does what it's good at: scheduling and structure
- Library does what it's good at: vetted, proven content
- Natural progression from generic to personalized

---

## What We Kept

### Database Tables ✅
- `task_library` - 50+ vetted tasks
- `task_rotation_state` - Rotation tracking
- `user_preference_profile` - Learning phases
- `task_feedback_complete` - Comprehensive feedback
- `user_preference_summary` - Aggregated preferences

### Core Services ✅
- `TaskLibraryService` - Task selection
- `FeedbackAnalyzerService` - Feedback analysis
- `AdaptiveTaskSelector` - Adaptive selection with learning
- `LearningPhaseManager` - Phase transitions
- `dynamic_personalization_config` - Configuration management

### Infrastructure ✅
- Dual-mode database (REST API for dev, PostgreSQL for prod)
- Feature flags system
- Test infrastructure

---

## What We Archived

### Documentation 📦
All moved to `archive/dynamic_planning_v1_hybrid_replacement/docs/`:
- Implementation plans (6 files)
- Architecture docs (2 files)
- Testing guides (6 files)
- Deployment guides (3 files)

### Code (To Be Modified) ⚠️
- `services/api_gateway/openai_main.py` (lines 1368-1416) - Remove hybrid replacement
- `services/dynamic_personalization/dynamic_task_selector.py` - Deprecate replacement method
- `services/dynamic_personalization/dynamic_plan_generator.py` - Keep for future, but mark as WIP

---

## Next Steps (V2 Implementation)

### Phase 1: Preparation (1-2 hours)
- [x] Archive V1 documentation
- [x] Create V2 implementation plan
- [ ] Update configuration flags

### Phase 2: Core Implementation (8-10 hours)
- [ ] Create `TaskPreseeder` service
- [ ] Enhance AI prompts with pre-selected tasks
- [ ] Modify API gateway integration
- [ ] Update plan extraction logic

### Phase 3: Testing (2-3 hours)
- [ ] Test cold start (Day 1, pure AI)
- [ ] Test warm start (Day 2+, with feedback)
- [ ] Test task rotation
- [ ] End-to-end validation

### Phase 4: Rollout (Ongoing)
- [ ] Monitor metrics
- [ ] Collect user feedback
- [ ] Iterate and improve

**Total Estimated Time**: 13-21 hours (2-3 focused days)

---

## Lessons Learned

1. **Verify schema first**: Don't trust documentation, query the actual database
2. **Understand constraints**: Foreign keys and relationships matter
3. **Follow the flow**: Understand how existing system works before adding complexity
4. **Simple is better**: Pre-seeding > Post-processing
5. **User insight is valuable**: The person using the system often has the best ideas

---

## Open Questions for V2

1. **Minimum feedback threshold**: 3 or 5 completed tasks?
2. **Library task ratio**: How many of 12 tasks should be from library? (40-60%?)
3. **Fallback strategy**: Always fallback to pure AI if pre-seeding fails?
4. **Quality filter**: Require satisfaction ≥3 for task selection?

**Decisions**: See `OPTION_B_IMPLEMENTATION_PLAN.md` for recommendations

---

## References

- V2 Implementation Plan: `../../OPTION_B_IMPLEMENTATION_PLAN.md`
- Archive Index: `../ARCHIVE_INDEX.md`
- File Inventory: `../INVENTORY.md`

---

**Session Completed**: 2025-10-28
**Status**: V1 archived, V2 ready to implement
**Next Action**: Review V2 plan and begin Phase 2
