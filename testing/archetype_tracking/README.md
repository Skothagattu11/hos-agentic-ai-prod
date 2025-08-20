# Archetype-Specific Analysis Tracking Tests

This folder contains test scripts for the archetype-specific analysis tracking system implemented in August 2025.

## System Overview

The archetype tracking system allows each user-archetype combination to maintain independent `last_analysis_at` timestamps. This ensures:
- New archetypes get comprehensive 7-day data windows
- Returning to previous archetypes uses incremental data since that archetype's last analysis
- Each archetype builds its own analysis history

## Database Schema

- **Table**: `archetype_analysis_tracking`
- **Key Fields**: `user_id`, `archetype`, `last_analysis_at`, `analysis_count`
- **Unique Constraint**: `(user_id, archetype)`

## Test Files

### 🎯 Primary Tests

- **`test_archetype_tracking_modern_api.py`** - **MAIN TEST**
  - Comprehensive end-to-end test using modern API endpoints
  - Tests archetype switching patterns and timing differences
  - Validates archetype-specific incremental vs baseline behavior
  - **Use this for primary validation**

### 🔧 Development Tests

- **`test_archetype_direct.py`**
  - Direct service-level testing of ArchetypeAnalysisTracker
  - Tests database operations (get/update timestamps)
  - Useful for debugging service logic

- **`test_archetype_logic_minimal.py`**
  - Minimal unit tests for archetype tracking logic
  - Tests fallback mechanisms and error handling

- **`test_archetype_switching.py`**
  - Legacy test for general archetype switching
  - May be outdated after new tracking implementation

## Prerequisites

1. **Database Migration**: Apply the schema migration first:
   ```bash
   # Apply the create table migration
   psql $DATABASE_URL < supabase/migrations/create_archetype_analysis_tracking.sql
   
   # Populate with existing data
   psql $DATABASE_URL < supabase/migrations/populate_archetype_analysis_tracking.sql
   ```

2. **Server Running**: Start the API server:
   ```bash
   python start_openai.py
   # OR
   uvicorn services.api_gateway.openai_main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Running Tests

### Main Test (Recommended)
```bash
cd testing/archetype_tracking
python test_archetype_tracking_modern_api.py
```

### All Tests
```bash
cd testing/archetype_tracking
for test in test_*.py; do
    echo "Running $test..."
    python "$test"
    echo ""
done
```

## Expected Results

### Success Indicators
- **Similar baseline times**: First analysis for any archetype takes ~7-30 seconds
- **Incremental speedup**: Return to previous archetype is 50-80% faster
- **Database tracking**: Records appear in `archetype_analysis_tracking` table

### Debugging Queries
```sql
-- View tracking records for test user
SELECT * FROM archetype_analysis_tracking 
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- Check analysis distribution
SELECT archetype, COUNT(*) FROM holistic_analysis_results 
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2' 
GROUP BY archetype;
```

## Implementation Details

The archetype tracking system integrates with:
- **OnDemandAnalysisService**: Uses archetype timestamps for analysis decisions
- **HolisticMemoryService**: Updates tracking when storing behavior analysis results
- **ArchetypeAnalysisTracker**: MVP service handling database operations

## Troubleshooting

- **No tracking records**: Check database migration was applied
- **All analyses take same time**: OnDemandAnalysisService not using archetype tracker
- **Import errors**: Verify ArchetypeAnalysisTracker service is properly integrated
- **Test user not found**: System creates tracking records automatically on first analysis