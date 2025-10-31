# Dynamic Planning V1 - Hybrid Replacement (Archived)

## Status: Archived - Replaced by V2 (Feedback-Driven Pre-seeding)

This folder contains the V1 implementation of dynamic task selection using a "hybrid replacement" approach where AI-generated tasks were replaced post-generation with library tasks.

## Why Archived

**V1 Approach Issues:**
- Complex: AI generates plan → Parse → Replace tasks → Re-save
- Fragile: Depends on AI output format staying consistent
- Error-prone: Foreign key constraints, schema mismatches
- Less feedback-driven: Replacement happened after plan generation

**V2 Approach Benefits:**
- Cleaner: Select tasks → Feed to AI → AI schedules them
- Simpler: No post-processing, no replacement logic
- Feedback-first: Task selection based on user preferences/completion
- Better AI usage: AI focuses on scheduling, not content

## Timeline

- **Created**: Session on 2025-10-28
- **Archived**: 2025-10-28 (same session)
- **Replaced by**: V2 Feedback-Driven Pre-seeding approach

## Contents

See `INVENTORY.md` for complete file listing.

## Migration Notes

V2 keeps:
- ✅ Task library (`task_library` table)
- ✅ Task rotation tracking (`task_rotation_state` table)
- ✅ Feedback analysis (`FeedbackAnalyzerService`)
- ✅ Adaptive task selection (`AdaptiveTaskSelector`)
- ✅ Learning phases (`LearningPhaseManager`)

V2 removes:
- ❌ Hybrid replacement logic (openai_main.py lines 1368-1416)
- ❌ `DynamicTaskSelector.replace_ai_tasks_with_library()`
- ❌ `DynamicPlanGenerator.persist_plan_to_database()` (separate INSERT path)

V2 adds:
- ✅ Pre-generation task selection
- ✅ AI prompt enhancement with selected tasks
- ✅ Single unified plan generation path

## Reference

If you need to understand how hybrid replacement worked, see:
- `services/dynamic_personalization/dynamic_task_selector.py`
- `services/api_gateway/openai_main.py` (lines 1368-1416)
- `IMPLEMENTATION_NOTES.md`
