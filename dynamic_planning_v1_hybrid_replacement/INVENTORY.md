# File Inventory - Dynamic Planning V1

## SQL Files (Keep - Used by V2)

### Database Tables
- `supabase/dynamic-planning/001_task_library.sql` - Task library table
- `supabase/dynamic-planning/002_task_rotation_state.sql` - Rotation tracking
- `supabase/dynamic-planning/003_user_preference_profile.sql` - User learning phases
- `supabase/dynamic-planning/004_task_feedback_complete.sql` - Comprehensive feedback
- `supabase/dynamic-planning/005_user_preference_summary.sql` - Aggregated preferences

**Status**: ✅ KEEP - These tables are used by V2

## Python Services (Partial Keep)

### Core Services (KEEP)
- `services/dynamic_personalization/task_library_service.py` - Task selection from library
- `services/dynamic_personalization/feedback_analyzer_service.py` - Feedback analysis
- `services/dynamic_personalization/adaptive_task_selector.py` - Adaptive selection with learning
- `services/dynamic_personalization/learning_phase_manager.py` - Phase transitions

**Status**: ✅ KEEP - Core functionality needed for V2

### Hybrid-Specific Services (ARCHIVE/MODIFY)
- `services/dynamic_personalization/dynamic_task_selector.py` - Hybrid replacement logic
- `services/dynamic_personalization/dynamic_plan_generator.py` - Standalone plan generation

**Status**: ⚠️ MODIFY - Will be refactored for V2 pre-seeding approach

## Configuration (KEEP)
- `config/dynamic_personalization_config.py` - Feature flags and settings

**Status**: ✅ KEEP - Will update flags for V2

## Documentation Files (ARCHIVE)

### Implementation Docs
- `DYNAMIC_HYBRID_IMPLEMENTATION_PLAN.md` - V1 implementation plan
- `FINAL_DUAL_MODE_SETUP.md` - Database dual-mode setup
- `DEVELOPMENT_VS_PRODUCTION_GUIDE.md` - Environment guide
- `MVP_QUICK_START.md` - MVP testing guide
- `TEST_FAILURE_ANALYSIS.md` - Test failure documentation

**Status**: 📦 ARCHIVE - Historical reference for V1

## Integration Points (MODIFY)

### API Gateway
- `services/api_gateway/openai_main.py` (lines 1368-1416) - Hybrid replacement logic

**Status**: ⚠️ MODIFY - Remove hybrid replacement, add pre-seeding

## Test Files (KEEP/UPDATE)

### Test Scripts
- `testing/test_realistic_user_journey_v2.py` - End-to-end testing
- `testing/test_hybrid_mvp_e2e.py` - Hybrid MVP testing
- `testing/test_task_library_access.py` - Task library access tests

**Status**: ⚠️ UPDATE - Modify for V2 approach

## Schema Fixes Applied (Session Work)

### Changes Made During Session
1. Fixed `plan_items` INSERT schema (removed `dynamic_metadata`, `is_dynamic`)
2. Added `source`, `category`, `subcategory`, `variation_group` columns
3. Fixed foreign key constraint understanding
4. Dual-mode database setup (REST API for dev, PostgreSQL for prod)

**Status**: ✅ COMPLETE - Schema now matches production table
