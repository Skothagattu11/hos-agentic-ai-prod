# Holistic Integration API Endpoints

## Overview

These endpoints provide read-only access to holistic analysis data for the conversational AI service (holistic-ai). The endpoints are designed to support plan-scoped conversations where users can interact with their generated plans through natural language.

## Implementation Files

- **`api/holistic_integration.py`** - FastAPI router with all endpoint implementations
- **`services/api_gateway/openai_main.py`** - Router registration (lines 261-270)
- **`testing/test_holistic_integration_endpoints.py`** - Comprehensive test suite
- **`testing/quick_test_holistic.py`** - Quick validation script

## Endpoints

### 1. Get Analysis Result by ID
```
GET /api/v1/analysis-results/{analysis_result_id}
```

Returns complete analysis result (routine_plan, circadian_analysis, or behavior_analysis).

**Example:**
```bash
curl http://localhost:8002/api/v1/analysis-results/7f785ff5-d785-4013-8c6a-bbd0802f3eed
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "7f785ff5-d785-4013-8c6a-bbd0802f3eed",
    "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
    "analysis_type": "routine_plan",
    "archetype": "Foundation Builder",
    "analysis_result": {...},
    "created_at": "2025-09-30T16:50:22.705642+00:00",
    "analysis_date": "2025-09-30",
    "confidence_score": 0.0
  }
}
```

### 2. Get Behavior Analysis
```
GET /api/v1/users/{user_id}/behavior-analysis
GET /api/v1/users/{user_id}/behavior-analysis?date=2025-09-30
```

Returns behavioral signature, archetype, goals, barriers, and recommendations.

**Example:**
```bash
curl http://localhost:8002/api/v1/users/35pDPUIfAoRl2Y700bFkxPKYjjf2/behavior-analysis
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "a8b23056-4c7d-45e7-aef0-a2b36e9b64f3",
    "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
    "archetype": "Foundation Builder",
    "behavioral_signature": {
      "signature": "User shows strong adherence to simple, time-bounded routines...",
      "confidence": 0.83
    },
    "primary_goal": {
      "goal": "Establish a sustainable daily structure...",
      "timeline": "8-12 weeks",
      "success_metrics": "≥85% completion rate..."
    },
    "readiness_level": "Medium",
    "recommendations": [...]
  }
}
```

### 3. Get Circadian Analysis (includes Energy Zones)
```
GET /api/v1/users/{user_id}/circadian-analysis
GET /api/v1/users/{user_id}/circadian-analysis?date=2025-09-30
```

Returns chronotype, energy zones, sleep schedule, and timing recommendations.

**Example:**
```bash
curl http://localhost:8002/api/v1/users/35pDPUIfAoRl2Y700bFkxPKYjjf2/circadian-analysis
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "95316845-1cbf-451e-a195-b81cb63801e3",
    "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
    "archetype": "Foundation Builder",
    "chronotype_assessment": {
      "primary_chronotype_classification": "Intermediate",
      "confidence_score": 0.85
    },
    "energy_zone_analysis": {
      "peak_energy_window": "10:00 AM - 2:00 PM",
      "low_energy_window": "4:00 PM - 6:00 PM",
      "maintenance_energy_window": "8:00 AM - 10:00 AM and 2:00 PM - 4:00 PM"
    },
    "schedule_recommendations": {
      "optimal_wake_time": "6:30 AM - 7:00 AM",
      "optimal_sleep_time": "10:00 PM - 11:00 PM",
      "workout_timing": "Mid-morning to early afternoon",
      "cognitive_task_timing": "Schedule high-focus tasks during peak energy window"
    }
  }
}
```

### 4. Get Context Memory
```
GET /api/v1/users/{user_id}/context-memory
```

Returns engagement patterns, satisfaction trends, and optimization opportunities.

**Example:**
```bash
curl http://localhost:8002/api/v1/users/35pDPUIfAoRl2Y700bFkxPKYjjf2/context-memory
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "1b4a9c8c-fd10-4a22-81be-b1190c457cff",
    "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
    "context_summary": "### Context Summary...\n1. **Engagement Patterns**:...",
    "source_data": {
      "checkin_count": 7,
      "journal_count": 1,
      "calendar_count": 15
    },
    "archetype": "Foundation Builder",
    "data_period_days": 30
  }
}
```

### 5. List Analysis Results
```
GET /api/v1/users/{user_id}/analysis-results
GET /api/v1/users/{user_id}/analysis-results?analysis_type=routine_plan&limit=10
```

Returns list of available analyses (for date picker).

**Example:**
```bash
curl "http://localhost:8002/api/v1/users/35pDPUIfAoRl2Y700bFkxPKYjjf2/analysis-results?limit=5"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
    "count": 3,
    "analyses": [
      {
        "id": "7f785ff5-d785-4013-8c6a-bbd0802f3eed",
        "analysis_type": "routine_plan",
        "archetype": "Foundation Builder",
        "analysis_date": "2025-09-30",
        "created_at": "2025-09-30T16:50:22.705642+00:00"
      },
      ...
    ]
  }
}
```

### 6. Get Full Context (Mega Endpoint - Optional)
```
GET /api/v1/analysis-results/{analysis_result_id}/full-context
```

Returns everything in one call: plan + behavior + circadian + memory + plan_items.

**Example:**
```bash
curl http://localhost:8002/api/v1/analysis-results/7f785ff5-d785-4013-8c6a-bbd0802f3eed/full-context
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "7f785ff5-d785-4013-8c6a-bbd0802f3eed",
    "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
    "analysis_type": "routine_plan",
    "archetype": "Foundation Builder",
    "primary_analysis": {...},
    "behavior_analysis": {...},
    "circadian_analysis": {...},
    "context_memory": {...},
    "plan_items": [...]
  }
}
```

### 7. Health Check
```
GET /api/v1/holistic-integration/health
```

Verifies service and database connectivity.

**Example:**
```bash
curl http://localhost:8002/api/v1/holistic-integration/health
```

## Database Tables Used

### holistic_analysis_results
Main table storing all analysis types:
- `routine_plan` - Daily routine plans
- `circadian_analysis` - Chronotype and energy zones
- `behavior_analysis` - Behavioral signatures and archetypes

### holistic_memory_analysis_context
Engagement patterns and context memory.

### plan_items
Individual tasks extracted from routine plans (linked by `analysis_result_id`).

## Testing

### Comprehensive Test Suite
```bash
cd /mnt/c/dev_skoth/well-planned/hos-agentic-ai-prod
python testing/test_holistic_integration_endpoints.py
```

Features:
- Tests all 7 endpoints
- Validates response structure
- Tests error handling
- Pretty-printed output with colors
- Full JSON logging

### Quick Validation
```bash
python testing/quick_test_holistic.py
```

Simple curl-like tests for rapid verification.

## Integration with holistic-ai Service

These endpoints are designed to be called by the holistic-ai conversational service:

1. **Date Picker**: Use `/users/{user_id}/analysis-results` to populate date picker
2. **Context Loading**: When user selects a date, call `/analysis-results/{id}/full-context`
3. **Conversation Context**: Use behavior, circadian, and memory data to inform responses
4. **Item Drilling**: Use `plan_items` to support specific task questions

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message here"
}
```

Status codes:
- `200` - Success
- `404` - Resource not found
- `422` - Validation error
- `500` - Internal server error

## Notes

- All endpoints are **read-only** (GET requests only)
- No authentication required (service-to-service trust)
- Uses DatabasePool for connection pooling
- All JSON parsing is handled automatically
- Timestamps are returned in ISO format
- UUIDs are converted to strings for JSON compatibility

## Future Enhancements

1. Add service-to-service authentication (Bearer tokens)
2. Add request rate limiting
3. Add response caching for frequently accessed data
4. Add pagination for large result sets
5. Add filtering/sorting options to list endpoints
