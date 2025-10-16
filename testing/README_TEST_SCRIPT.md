# Routine Generation Test Script

## Quick Start

```bash
# 1. Make sure server is running
python start_openai.py

# 2. In another terminal, run the test
python testing/test_routine_generation_flow.py
```

## What It Does

Tests the complete routine generation flow exactly as a real user would:

1. **Health Check** - Verifies API server is running at localhost:8002
2. **Request Payload** - Prepares routine generation request with your user ID and archetype
3. **API Call** - Calls POST /api/user/{user_id}/routine/generate (with force_refresh=true)
4. **Analyses Extraction** - Extracts behavior + circadian analyses from response
5. **Sahha Verification** - Verifies Sahha direct integration was used
6. **Quality Analysis** - Analyzes completeness and quality of generated routine
7. **Summary Report** - Generates comprehensive test summary

## Output Logs

All inputs and outputs are saved to: `logs/test_runs/YYYYMMDD_HHMMSS_*`

Files created:
- `01_health_check.json` - API health status
- `02_request_payload.json` - Request sent to API
- `03_api_response.json` - Full API response (complete data)
- `04_behavior_analysis.json` - Behavior analysis output (o3 model)
- `05_circadian_analysis.json` - Circadian analysis output (o3 model)
- `06_routine_plan.json` - Generated routine plan (combined)
- `07_generation_metadata.json` - Metadata (timestamps, models, data sources)
- `08_sahha_verification.json` - Sahha integration verification
- `09_quality_report.json` - Routine quality metrics
- `10_SUMMARY.json` - Test summary report

## Configuration

Edit these variables in the test script:

```python
TEST_USER_ID = "6241b25a-c2de-49fe-9476-1ada99ffe5ca"  # Your user ID
TEST_ARCHETYPE = "Peak Performer"  # Your archetype
API_BASE_URL = "http://localhost:8002"  # API server URL
```

## Expected Duration

- **API Call**: 60-180 seconds
  - Sahha data fetch: 5-15 seconds (parallel for biomarkers + scores)
  - Behavior analysis (o3): 20-60 seconds
  - Circadian analysis (o3): 20-60 seconds
  - Routine generation: 10-30 seconds

## What Gets Tested

✅ **API Connectivity** - Server is running and responding
✅ **Authentication** - API key validation working
✅ **Sahha Integration** - Direct Sahha fetch with watermarks
✅ **o3 Model Usage** - Both analyses using o3 model
✅ **Parallel Execution** - Behavior + circadian run in parallel
✅ **Data Quality** - Sufficient biomarkers/scores fetched
✅ **Analysis Completeness** - All required sections present
✅ **Routine Quality** - Personalized, archetype-specific output

## Troubleshooting

### "API Server NOT REACHABLE"
```bash
# Start the server first
python start_openai.py
```

### "AUTHENTICATION FAILED"
Check that API key is correct: `hosa_flutter_app_2024`

### "Rate Limited"
Wait 60 seconds before retrying

### "Timeout after 300s"
- Check Sahha API is responding
- Check OpenAI API is responding
- Increase timeout in script if needed

### "Sahha integration not verified"
1. Check environment variables:
   ```bash
   SAHHA_CLIENT_ID=your_client_id
   SAHHA_CLIENT_SECRET=your_client_secret
   USE_SAHHA_DIRECT=true
   ```
2. Check Sahha credentials are valid
3. Check user has data in Sahha

## Example Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║            ROUTINE GENERATION FLOW TEST - Real User Simulation              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Test Run ID: 20251016_143022
Logs Directory: logs/test_runs
User ID: 6241b25a-c2de-49fe-9476-1ada99ffe5ca
Archetype: Peak Performer

================================================================================
  STEP 1: API Server Health Check
================================================================================

✅ API Server: Running at http://localhost:8002
✅ Status: healthy
📝 Logged to: logs/test_runs/20251016_143022_01_health_check.json

...

================================================================================
  FINAL VERDICT
================================================================================

✅ TEST PASSED!

The complete flow is working:
  1. ✅ API endpoint responding
  2. ✅ Sahha integration active
  3. ✅ o3 model analyses completed
  4. ✅ Routine generated successfully

Review logs at: logs/test_runs/20251016_143022_*
```

## Review Raw Data

All raw inputs/outputs are in JSON format for easy inspection:

```bash
# View behavior analysis output
cat logs/test_runs/20251016_143022_04_behavior_analysis.json

# View circadian analysis output
cat logs/test_runs/20251016_143022_05_circadian_analysis.json

# View final routine plan
cat logs/test_runs/20251016_143022_06_routine_plan.json

# View complete API response
cat logs/test_runs/20251016_143022_03_api_response.json
```

## Next Steps

After successful test:
1. Review logs to verify o3 model outputs
2. Check behavior analysis contains all required sections
3. Check circadian analysis contains energy zones
4. Verify routine plan is personalized for archetype
5. Confirm Sahha data was used (not just Supabase fallback)
