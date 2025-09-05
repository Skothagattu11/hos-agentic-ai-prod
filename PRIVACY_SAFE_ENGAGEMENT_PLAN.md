# Privacy-Safe Engagement Data Integration Plan

## Overview
This document outlines the implementation plan for integrating engagement data into the AI agent context while ensuring no internal IDs are exposed to the AI model. The approach uses single JOIN queries for efficiency and passes raw behavioral data to the O3 model for analysis.

## Current Issues
1. **ID Exposure in Biomarkers/Scores**: Currently exposing internal IDs in `user_data_service.py`
2. **Memory Data**: Likely includes IDs that shouldn't be exposed to AI
3. **Engagement Data**: Needs unified JOIN endpoint to avoid exposing plan_item_id, analysis_result_id, etc.

## Implementation Plan

### Phase 1: Create Unified Engagement Context API (No IDs)

#### 1.1 New Engagement Context Endpoint
**File**: `services/api_gateway/engagement_endpoints.py`

```python
@router.get("/engagement-context/{profile_id}")
async def get_engagement_context(
    profile_id: str,
    days: int = Query(7, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase)
):
    """
    Returns complete engagement picture without exposing any IDs.
    Uses efficient JOIN query to combine plan items with check-ins.
    
    Returns:
    - Planned tasks with titles, descriptions, time blocks
    - Completion status and satisfaction ratings
    - Timing patterns (planned vs actual)
    - NO system IDs exposed
    """
    # SQL JOIN query combining:
    # - plan_items (title, description, scheduled_time, time_block)
    # - task_checkins (completion_status, satisfaction_rating, planned_date)
    # - holistic_analysis_results (analysis_date for context)
```

**Expected Output Structure**:
```json
{
    "engagement_summary": {
        "total_planned": 25,
        "completed": 18,
        "partial": 3,
        "skipped": 4,
        "completion_rate": 0.72
    },
    "timing_patterns": {
        "average_delay_minutes": 15,
        "on_time_percentage": 0.65,
        "preferred_completion_times": ["07:00", "19:00"]
    },
    "recent_tasks": [
        {
            "title": "Morning meditation",
            "time_block": "morning_routine",
            "planned_time": "06:00",
            "actual_completion": "06:15",
            "status": "completed",
            "satisfaction": 4
        }
    ],
    "satisfaction_trends": {
        "average_rating": 3.8,
        "trending": "improving"
    }
}
```

### Phase 2: Remove IDs from Existing Data Fetching

#### 2.1 Clean Scores Data
**File**: `services/user_data_service.py` (lines 136-163)

**Before**:
```python
score_data = {
    'id': str(row['id']),  # REMOVE THIS
    'profile_id': row['profile_id'],  # REMOVE THIS
    'type': row['type'],
    'score': float(row['score']),
    ...
}
```

**After**:
```python
score_data = {
    'type': row['type'],
    'score': float(row['score']),
    'date': row['score_date_time'],
    'state': row['data'].get('state') if row['data'] else None,
    'factors': row['data'].get('factors') if row['data'] else []
}
```

#### 2.2 Clean Biomarkers Data
**File**: `services/user_data_service.py` (lines 184-210)

**Before**:
```python
biomarker_data = {
    'id': str(row['id']),  # REMOVE THIS
    'profile_id': row['profile_id'],  # REMOVE THIS
    ...
}
```

**After**:
```python
biomarker_data = {
    'category': row['category'],
    'type': row['type'],
    'data': row['data'] if isinstance(row['data'], dict) else {},
    'start_date': row['start_date_time'],
    'end_date': row['end_date_time']
}
```

#### 2.3 Clean Archetypes Data
**File**: `services/user_data_service.py` (lines 238-268)

**Before**:
```python
archetype_data = {
    'id': str(row['id']),  # REMOVE THIS
    'profile_id': row['profile_id'],  # REMOVE THIS
    ...
}
```

**After**:
```python
archetype_data = {
    'name': row['name'],
    'periodicity': row['periodicity'],
    'value': row['value'],
    'data': row['data'] if isinstance(row['data'], dict) else {},
    'start_date': row['start_date_time'],
    'end_date': row['end_date_time']
}
```

#### 2.4 Add Engagement Data Method
**File**: `services/user_data_service.py`

```python
async def fetch_engagement_context(self, user_id: str, days: int = 7) -> dict:
    """
    Fetch engagement data using the new privacy-safe endpoint.
    No IDs exposed, only behavioral patterns.
    """
    try:
        # Use the API client to call engagement context endpoint
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8002')
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_base_url}/api/v1/engagement/engagement-context/{user_id}",
                params={'days': days}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to fetch engagement context: {response.status}")
                    return {}
    except Exception as e:
        logger.error(f"Error fetching engagement context: {e}")
        return {}
```

### Phase 3: Clean Memory Context

#### 3.1 Update Memory Service
**File**: `services/agents/memory/holistic_memory_service.py`

Ensure `get_memory_context()` returns clean data:
```python
def clean_memory_for_ai(memory_data: dict) -> dict:
    """Remove all IDs from memory context before sending to AI"""
    cleaned = {}
    
    if 'past_analyses' in memory_data:
        cleaned['past_analyses'] = [
            {
                'analysis_type': a.get('analysis_type'),
                'created_at': a.get('created_at'),
                'key_insights': a.get('key_insights'),
                # NO analysis_result_id
            }
            for a in memory_data['past_analyses']
        ]
    
    if 'past_plans' in memory_data:
        cleaned['past_plans'] = [
            {
                'plan_type': p.get('plan_type'),
                'created_date': p.get('created_date'),
                'plan_content': p.get('plan_content'),
                # NO plan_id
            }
            for p in memory_data['past_plans']
        ]
    
    return cleaned
```

### Phase 4: Integrate Engagement into AI Context

#### 4.1 Update format_health_data_for_ai()
**File**: `services/api_gateway/openai_main.py` (line 1815)

```python
async def format_health_data_for_ai(user_context) -> str:
    """Format health tracking data for AI analysis - with engagement patterns"""
    try:
        # Existing health data formatting...
        
        # NEW: Add engagement patterns section
        if hasattr(user_context, 'engagement_data') and user_context.engagement_data:
            data_summary.append("\nENGAGEMENT PATTERNS:")
            
            eng = user_context.engagement_data
            if 'engagement_summary' in eng:
                summary = eng['engagement_summary']
                data_summary.append(f"  • Plan adherence: {summary.get('completion_rate', 0):.1%}")
                data_summary.append(f"  • Tasks completed: {summary.get('completed', 0)}/{summary.get('total_planned', 0)}")
            
            if 'timing_patterns' in eng:
                timing = eng['timing_patterns']
                data_summary.append(f"  • Average delay: {timing.get('average_delay_minutes', 0)} minutes")
                data_summary.append(f"  • On-time rate: {timing.get('on_time_percentage', 0):.1%}")
            
            if 'recent_tasks' in eng and eng['recent_tasks']:
                data_summary.append(f"  • Recent completions: {len(eng['recent_tasks'])} tasks tracked")
                # Sample of recent task performance
                for task in eng['recent_tasks'][:3]:
                    data_summary.append(f"    - {task['title']}: {task['status']} (satisfaction: {task.get('satisfaction', 'N/A')})")
        
        return "\n".join(data_summary)
```

#### 4.2 Update prepare_behavior_agent_data()
**File**: `services/api_gateway/openai_main.py` (line 1644)

```python
async def prepare_behavior_agent_data(user_context, user_context_summary: str) -> dict:
    """Prepare comprehensive data for behavior analysis agent (o3)"""
    try:
        behavior_data = {
            "comprehensive_health_context": user_context_summary,
            "detailed_metrics": {
                # Remove ID fields from existing data
                "data_quality": {
                    "level": user_context.data_quality.quality_level,
                    "completeness": user_context.data_quality.completeness_score,
                    "scores_count": user_context.data_quality.scores_count,
                    "biomarkers_count": user_context.data_quality.biomarkers_count,
                },
                # ... existing fields ...
            },
            # NEW: Add engagement patterns
            "engagement_patterns": {},
            "analysis_focus": "comprehensive_behavior_pattern_analysis_with_engagement"
        }
        
        # Add engagement data if available
        if hasattr(user_context, 'engagement_data') and user_context.engagement_data:
            behavior_data["engagement_patterns"] = {
                "plan_adherence": user_context.engagement_data.get('engagement_summary', {}),
                "timing_analysis": user_context.engagement_data.get('timing_patterns', {}),
                "recent_performance": user_context.engagement_data.get('recent_tasks', [])[:10],
                "satisfaction_trends": user_context.engagement_data.get('satisfaction_trends', {})
            }
        
        return behavior_data
```

### Phase 5: Update Main Analysis Flow

#### 5.1 Modify get_user_health_data()
**File**: `services/user_data_service.py`

```python
async def get_user_health_data(self, user_id: str, days: int = None) -> UserHealthContext:
    """Main entry point - fetch complete user health data with engagement"""
    # ... existing code ...
    
    # Fetch engagement context alongside health data
    tasks = [
        self.fetch_user_scores(user_id, days),
        self.fetch_user_biomarkers(user_id, days),
        self.fetch_user_archetypes(user_id),
        self.fetch_engagement_context(user_id, days)  # NEW
    ]
    
    db_scores, db_biomarkers, db_archetypes, engagement_data = await asyncio.gather(*tasks)
    
    # Create result with engagement data
    result = create_health_context_from_raw_data(
        user_id=user_id,
        raw_scores=raw_scores,
        raw_biomarkers=raw_biomarkers,
        raw_archetypes=raw_archetypes,
        engagement_data=engagement_data,  # NEW
        days=days
    )
```

### Phase 6: Testing & Validation

#### 6.1 Create Test Script
**File**: `testing/test_privacy_safe_integration.py`

```python
import asyncio
import json
from services.user_data_service import UserDataService
from services.api_gateway.openai_main import format_health_data_for_ai

async def test_no_ids_exposed():
    """Verify no IDs are sent to AI model"""
    service = UserDataService()
    
    # Test user
    test_user_id = "test_user_123"
    
    # Fetch all context data
    user_context = await service.get_user_health_data(test_user_id, days=7)
    
    # Convert to JSON to check for ID fields
    context_json = json.dumps(user_context.__dict__, default=str)
    
    # Assert no ID fields present
    assert '"id"' not in context_json.lower()
    assert '"_id"' not in context_json.lower()
    assert 'profile_id' not in context_json.lower()
    assert 'analysis_result_id' not in context_json.lower()
    assert 'plan_item_id' not in context_json.lower()
    
    print("✅ No IDs exposed in user context")
    
    # Check formatted AI context
    ai_context = await format_health_data_for_ai(user_context)
    assert 'id' not in ai_context.lower()
    
    print("✅ No IDs in formatted AI context")

async def test_engagement_integration():
    """Test engagement data flows correctly"""
    service = UserDataService()
    
    # Test user with engagement data
    test_user_id = "test_user_with_tasks"
    
    # Fetch context with engagement
    user_context = await service.get_user_health_data(test_user_id, days=7)
    
    # Verify engagement data present
    assert hasattr(user_context, 'engagement_data')
    assert 'engagement_summary' in user_context.engagement_data
    assert 'timing_patterns' in user_context.engagement_data
    
    # Check AI context includes engagement
    ai_context = await format_health_data_for_ai(user_context)
    assert 'ENGAGEMENT PATTERNS' in ai_context
    assert 'Plan adherence' in ai_context
    
    print("✅ Engagement data successfully integrated")

if __name__ == "__main__":
    asyncio.run(test_no_ids_exposed())
    asyncio.run(test_engagement_integration())
```

## Implementation Timeline

### Day 1: Create Engagement Context Endpoint
- Implement `/engagement-context/{profile_id}` endpoint
- Write efficient JOIN query
- Test with sample data

### Day 2: Clean Existing Data Fetching
- Remove IDs from scores fetching
- Remove IDs from biomarkers fetching
- Remove IDs from archetypes fetching
- Add engagement fetching method

### Day 3: Clean Memory Context
- Update memory service to remove IDs
- Test memory context is clean

### Day 4: Integrate into AI Context
- Update `format_health_data_for_ai()`
- Update `prepare_behavior_agent_data()`
- Ensure engagement flows through

### Day 5: Update Main Flow & Test
- Update main analysis flow
- Run comprehensive tests
- Validate end-to-end

## Success Criteria

1. **Zero ID Exposure**: No internal IDs in AI context
2. **Engagement Integration**: AI receives plan adherence data
3. **Performance**: JOIN queries complete in <500ms
4. **Backward Compatibility**: Existing endpoints continue working
5. **AI Analysis**: Model successfully analyzes engagement patterns

## Key Design Decisions

1. **Single JOIN Query**: More efficient than multiple API calls
2. **Raw Data to AI**: No pre-processing, let O3 analyze
3. **Privacy First**: IDs never leave the backend
4. **MVP Approach**: Simple, working solution before optimization

## Notes for Implementation

- All ID removal should be done at the data fetching layer
- Engagement context should be optional (graceful fallback if unavailable)
- Memory context cleaning should not break existing functionality
- Test with real user data to ensure patterns are meaningful

## Files to Modify

1. `/services/api_gateway/engagement_endpoints.py` - Add new endpoint
2. `/services/user_data_service.py` - Remove IDs, add engagement
3. `/services/agents/memory/holistic_memory_service.py` - Clean memory
4. `/services/api_gateway/openai_main.py` - Update AI context formatting
5. `/testing/test_privacy_safe_integration.py` - New test file

## Expected Benefits

1. **Privacy**: No risk of ID leakage to AI models
2. **Context**: AI gets full picture of user engagement
3. **Adaptation**: Plans can evolve based on actual behavior
4. **Simplicity**: Raw data approach reduces complexity
5. **Performance**: Single JOIN more efficient than multiple queries