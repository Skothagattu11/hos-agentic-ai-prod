# HolisticOS MVP System Flow & Testing Guide

## System Architecture Overview

HolisticOS is a multi-agent AI system for personalized health optimization. The system follows this flow:

```
User Request → OnDemand Analysis → Behavior Analysis → Memory Storage → Plan Generation → Insights Extraction
```

## Expected User Journey

### 1. **Initial Analysis (First Time User)**
When a user makes their first request:
- **Trigger**: Routine or Nutrition generation endpoint
- **OnDemandAnalysisService** detects no prior analysis
- **Decision**: `FRESH_ANALYSIS` mode
- **Actions**:
  1. Fetch all user health data from Supabase
  2. Run behavior analysis via OpenAI GPT-4
  3. Store analysis in `holistic_analysis_results` table
  4. Update all 4 memory layers (working, short-term, long-term, meta)
  5. Generate requested plan (routine/nutrition)
  6. Extract insights from analysis

### 2. **Follow-up Analysis (Returning User)**
When user returns with new data:
- **Trigger**: Subsequent routine/nutrition requests
- **OnDemandAnalysisService** checks data threshold (50 points)
- **Decision**: Based on new data count
  - If ≥50 new points: `FRESH_ANALYSIS`
  - If <50 new points: `MEMORY_ENHANCED_CACHE`
- **Actions**:
  1. Fetch only incremental data since last analysis
  2. Either run fresh analysis or use cached with memory enhancement
  3. Update memory layers with new patterns
  4. Generate updated plans
  5. Extract progressive insights

## Critical System Components

### 1. **OnDemandAnalysisService** (`services/ondemand_analysis_service.py`)
- Controls when to run fresh vs cached analysis
- 50-item threshold for triggering fresh analysis
- Tracks analysis timestamps in `profiles.last_analysis_at`

### 2. **Memory System** (`services/agents/memory/`)
- **4 Layers**: Working, Short-term, Long-term, Meta
- Each layer stores different aspects of user behavior
- Memory enhances prompts for better personalization

### 3. **Supabase Adapter** (`shared_libs/supabase_client/adapter.py`)
- Translates SQL queries to REST API calls
- **KNOWN ISSUE**: Complex WHERE clauses with OR/AND fail
- **FIXED**: Simplified queries to use single conditions

### 4. **Insights Service** (`services/insights_extraction_service.py`)
- Automatically extracts insights after analysis
- Stores in `holistic_insights` table with deduplication
- Provides actionable recommendations

## Database Schema Key Tables

### `holistic_analysis_results`
Stores all analysis outputs:
- `user_id`: User identifier
- `analysis_type`: behavior_analysis, routine_plan, nutrition_plan
- `analysis_result`: JSON with full analysis
- `archetype`: User's wellness archetype
- `created_at`: Timestamp of analysis

### `holistic_insights`
Stores extracted insights:
- `user_id`: User identifier
- `insight_type`: Category of insight
- `insight_title`: Brief title
- `insight_content`: Detailed recommendation
- `priority`: 1-10 importance scale
- `actionability_score`: How actionable (0-1)

### Memory Tables
- `holistic_working_memory`: Current session context
- `holistic_shortterm_memory`: Recent interactions
- `holistic_longterm_memory`: Established patterns
- `holistic_meta_memory`: Learning velocity and adaptation

## Testing the System

### Prerequisites
1. Start the server: `python start_openai.py`
2. Ensure database is accessible
3. Have valid OpenAI API key in `.env`

### Test Scripts

#### 1. **Simple User Journey** (`test_scripts/test_user_journey_simple.py`)
```bash
# Interactive test with prompts
python test_scripts/test_user_journey_simple.py

# Quick automated test
python test_scripts/test_user_journey_simple.py --quick
```

**What it tests:**
- Routine generation (triggers behavior analysis)
- Insights extraction
- Nutrition generation (uses shared analysis)
- Follow-up cycles with memory

#### 2. **Debug Flow Test** (`test_debug_flow.py`)
```bash
python test_debug_flow.py
```

**What it tests:**
- Database state before/after
- Analysis storage verification
- Insights generation
- Memory layer updates
- Log file creation

### Expected Outputs

#### Successful Initial Analysis:
```
🏃 ROUTINE GENERATION
⏳ Generating routine plan...
   Will create behavior analysis if needed...
✅ Routine generated successfully!
   • Analysis Type: initial
   • Memory Quality: sparse
   • Used Cached Behavior: False
```

#### Log Files Created:
- `logs/output_1.txt` - Complete analysis output
- `logs/input_1.txt` - Input data sent to OpenAI
- `logs/insights_1.txt` - Extracted insights
- `logs/agent_handoffs/2_behavior_analysis_*.txt` - Agent communication

### Common Issues & Solutions

#### Issue 1: No Data in holistic_analysis_results
**Symptom**: Analysis runs but nothing stored in database
**Cause**: SQL query parsing error with complex WHERE clauses
**Solution**: Applied - Simplified queries to use date comparisons

#### Issue 2: Log File Numbering
**Symptom**: First analysis creates file "2" instead of "1"
**Cause**: Counter increments before checking if analysis exists
**Solution**: Check analysis existence before incrementing counter

#### Issue 3: No Insights Generated
**Symptom**: Analysis completes but no insights created
**Cause**: Insights service not finding stored analysis results
**Solution**: Ensure analysis is stored before insights extraction

#### Issue 4: Race Conditions
**Symptom**: "212 new data points" detected as "0"
**Cause**: Timestamps updated during data fetch process
**Solution**: Use consistent timestamp throughout analysis

## API Endpoints

### Core Endpoints
```
POST /api/user/{user_id}/routine/generate   # Generate routine plan
POST /api/user/{user_id}/nutrition/generate # Generate nutrition plan
POST /api/user/{user_id}/behavior/analyze   # Standalone behavior analysis
POST /api/v1/insights/generate              # Generate insights
GET  /api/v1/insights/{user_id}            # Retrieve user insights
```

### System Status
```
GET  /api/health                           # Health check
GET  /api/scheduler/status                 # Analysis scheduler status
```

## Development Workflow

### 1. Making Changes
- Always test with `test_debug_flow.py` first
- Check database state before and after
- Verify log files are created correctly

### 2. Debugging Tips
- Enable debug logging in services
- Check Supabase adapter query translations
- Monitor memory table updates
- Verify insights extraction

### 3. Performance Optimization
- Cache behavior analysis for <50 data points
- Use incremental data fetching
- Batch memory updates
- Deduplicate insights by content hash

## Architecture Principles

1. **On-Demand Processing**: Analysis only when needed, not scheduled
2. **Memory-Enhanced**: All responses leverage historical context
3. **Threshold-Based**: Smart decisions based on data availability
4. **Fail-Safe**: Graceful degradation when components fail
5. **Transparent**: Comprehensive logging for debugging

## Next Steps for Production

1. **Fix Supabase Adapter**: Properly handle complex SQL queries
2. **Add Monitoring**: Track analysis success rates
3. **Optimize Thresholds**: Tune based on user behavior
4. **Cache Management**: Implement Redis for better performance
5. **Error Recovery**: Add retry logic for transient failures

---

## Quick Troubleshooting Checklist

- [ ] Server running on port 8001?
- [ ] Database accessible?
- [ ] OpenAI API key valid?
- [ ] User exists in profiles table?
- [ ] RLS policies allow insertions?
- [ ] Memory tables have proper indexes?
- [ ] Insights service imported correctly?
- [ ] Log directory writable?

## Support

For issues, check:
1. Server logs in terminal
2. Analysis logs in `logs/` directory
3. Database state with `test_debug_flow.py`
4. Network tab for API responses