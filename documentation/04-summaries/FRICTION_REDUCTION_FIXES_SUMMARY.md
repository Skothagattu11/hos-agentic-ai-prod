# Friction-Reduction System Fixes Summary

## Date: 2025-10-30

## Issues Found & Fixed

### 1. ✅ JSON Parser Missing Category Field
**Problem:** AI was generating tasks with categories, but JSON parser wasn't extracting them to plan_items table.

**Files Fixed:**
- `services/parsers/json_parser.py` (lines 134, 172)

**Fix:** Added `category=task_data.get('category')` to ExtractedTask creation (both nested and old format)

**Result:** Categories now correctly saved to plan_items table

---

### 2. ✅ TaskPreseeder Using Wrong Field Names
**Problem:** FeedbackService returns `low_friction_categories` but TaskPreseeder was looking for old `exclude_categories` and `enjoyed_categories` fields.

**Files Fixed:**
- `services/dynamic_personalization/task_preseeder.py` (lines 175-179, 519-523)

**Fix:**
- Added new friction fields to selection_stats: `low_friction_categories`, `medium_friction_categories`, `high_friction_categories`, `friction_analysis`
- Updated `_empty_response()` to include new fields

**Result:** Friction data now flows from FeedbackService → TaskPreseeder → AI Prompt

---

### 3. ✅ Category Prioritization Logic (Exclusion → Friction-Reduction)
**Problem:** TaskPreseeder was excluding high-friction categories instead of keeping them with lower priority.

**Files Fixed:**
- `services/dynamic_personalization/task_preseeder.py` (lines 297-354)

**Fix:** Rewrote `_prioritize_categories_with_checkin()`:
- REMOVED exclusion logic (no categories excluded)
- ADDED friction-based scoring:
  - Low friction: 0.8 (high priority)
  - Medium friction: 0.5 (medium priority)
  - High friction: 0.3 (lower priority, will be simplified by AI)
- All categories included for balanced health

**Result:** High-friction categories now included in task selection (to be simplified by AI)

---

## Complete Data Flow (After Fixes)

```
1. User completes tasks
   ↓
2. task_checkins table stores: experience_rating (1-5), continue_preference (yes/maybe/no)
   ↓
3. FeedbackService.get_latest_checkin_feedback()
   - Calculates friction scores per category
   - Returns: low_friction_categories, high_friction_categories, friction_analysis
   ↓
4. TaskPreseeder.select_tasks_for_plan()
   - Receives friction data from FeedbackService
   - Passes to AI prompt via selection_stats
   ↓
5. AI Prompt (openai_main.py lines 4876-4987)
   - Receives: low_friction_categories, high_friction_categories
   - Applies Atomic Habits principles
   - SIMPLIFIES high-friction tasks (micro-habits)
   - Uses low-friction as anchors
   ↓
6. AI generates plan with categories
   ↓
7. JSON Parser extracts tasks WITH categories
   ↓
8. plan_items table populated with category field
   ↓
9. Test validation passes ✅
```

---

## Verification Steps

Run this test to verify the complete flow:

```bash
# 1. Clean old check-ins (optional)
python fix_old_checkins.py  # Choose option 1 (UPDATE)

# 2. Run full feedback test
python run_feedback_test.py

# 3. Diagnostic (should show categories in all plans)
python diagnose_adaptive_flow.py
```

Expected results:
- ✅ Plan 1: Has nutrition tasks
- ✅ Plan 2: Has more movement tasks (adapted to positive feedback)
- ✅ Plan 3: Has nutrition tasks (SIMPLIFIED, not excluded)
- ✅ Friction scores correctly calculated
- ✅ AI prompt receives friction data

---

## Key Philosophy Change

**OLD (Exclusion-based):**
- "User hates nutrition → Remove nutrition tasks"
- Result: Imbalanced health, no habit building

**NEW (Friction-reduction):**
- "User struggles with nutrition → Simplify nutrition tasks"
- Result: Balanced health, sustainable habits via Atomic Habits principles

---

## Atomic Habits Integration

The AI prompt now uses these principles for high-friction tasks:

1. **Make it Obvious**: Environmental cues (e.g., "Place shake ingredients on counter")
2. **Make it Easy**: Micro-habits (e.g., "Track macros" → "Take photo of meal")
3. **Make it Attractive**: Habit stacking (e.g., "Protein shake after workout")
4. **Make it Satisfying**: Immediate feedback (e.g., "Check off each meal")

---

## Files Modified

1. `services/parsers/json_parser.py` - Category extraction
2. `services/dynamic_personalization/task_preseeder.py` - Friction data flow and prioritization
3. `supabase/user-engagement/006_add_simplified_feedback_columns.sql` - Database schema
4. `services/feedback_service.py` - Simplified 2-question feedback (already completed)

---

## Testing

**Diagnostic Script:**
```bash
python diagnose_adaptive_flow.py
```

Shows:
- Raw AI output (categories generated)
- Extracted plan_items (categories saved)
- Check-ins (feedback patterns)
- Friction analysis by category
- Validation (Plan 3 has all categories)

---

## Status: ✅ COMPLETE

All friction-reduction system components are now connected and functional.
