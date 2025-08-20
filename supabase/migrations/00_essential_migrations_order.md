# Essential Database Migrations Order

## Migration Files to Apply (in order):

### 1. Core Tables & Features
1. **create_holistic_insights_table.sql** - Creates insights storage table
2. **update_holistic_insights_table.sql** - Updates insights table structure
3. **fix_insights_rls_policy.sql** - Sets up Row Level Security for insights

### 2. Archetype-Specific Tracking
4. **create_archetype_analysis_tracking.sql** - Creates archetype tracking table
5. **populate_archetype_analysis_tracking.sql** - Populates initial tracking data

### 3. Analysis Storage Fixes
6. **fix_analysis_storage_duplicates.sql** - Adds analysis_trigger column and fixes constraints

## Files Removed (Superseded/Redundant):
- ❌ add_duplicate_prevention_constraints.sql (superseded by fix_analysis_storage_duplicates.sql)
- ❌ fix_duplicate_prevention_constraints.sql (superseded)
- ❌ fix_duplicate_prevention_v2.sql (superseded)
- ❌ fix_archetype_aware_constraint.sql (superseded by fix_analysis_storage_duplicates.sql)
- ❌ fix_multiple_threshold_analyses.sql (handled by timestamp in code)

## Current Migration Status:
- ✅ Insights table: Applied
- ✅ Archetype tracking: Applied
- ⚠️ Analysis trigger constraint: Needs to be applied (fix_analysis_storage_duplicates.sql)

## To Apply Remaining Migration:
Run in Supabase SQL Editor:
```sql
-- Check current constraint
SELECT conname, pg_get_constraintdef(c.oid) 
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'holistic_analysis_results' AND c.contype = 'u';

-- If constraint name is not 'unique_analysis_per_user_type_date_archetype_trigger'
-- or if analysis_trigger column doesn't exist, apply:
-- supabase/migrations/fix_analysis_storage_duplicates.sql
```