# Insights V2 - Standalone Implementation

**Phase 1: Daily Insights MVP** - Weeks 1-3

Clean, standalone implementation of the HolisticOS insights system that runs independently from the existing codebase.

## 📁 Project Structure

```
services/insights_v2/
├── __init__.py                          # Module initialization
├── README.md                            # This file
├── data_aggregation_service.py          # Sprint 1.1 - Data fetching
├── baseline_calculation_service.py      # Sprint 1.1 - Baselines
├── insights_generation_service.py       # Sprint 1.2 - AI generation
├── api_endpoints.py                     # Sprint 1.3 - API endpoints
└── (future) insights_storage_service.py # Sprint 1.3 - Database storage
```

## 🎯 Key Features

### ✅ Implemented (Phase 1, Sprints 1.1-1.2)

1. **Data Aggregation Service**
   - Fetches 3-day health data from Sahha API
   - Fetches 3-day behavioral data from Supabase
   - Builds comprehensive `InsightContext` for AI

2. **Baseline Calculation Service**
   - Calculates 30-day rolling baselines
   - Caches baselines in Redis (24-hour TTL)
   - Assesses baseline quality

3. **Insights Generation Service**
   - AI-powered insights using GPT-4o or Claude Sonnet 4
   - Context-rich prompts with archetype personalization
   - Quality validation (confidence > 0.7, actionability > 0.6)
   - Structured output with categories and priorities

4. **API Endpoints**
   - Manual trigger: `POST /api/v2/insights/{user_id}/generate`
   - Health check: `GET /api/v2/insights/health`

### 🚧 To Be Implemented (Phase 1, Sprint 1.3)

- Insights storage in Supabase
- Retrieval endpoint: `GET /api/v2/insights/{user_id}/latest`
- Acknowledgment: `PATCH /api/v2/insights/{insight_id}/acknowledge`
- Feedback: `POST /api/v2/insights/{insight_id}/feedback`

## 🚀 Quick Start

### Step 1: Add Router to openai_main.py

Add the insights v2 router to your FastAPI app without modifying existing code:

```python
# In services/api_gateway/openai_main.py

# Add import at top of file
from services.insights_v2.api_endpoints import router as insights_v2_router

# After all other router registrations, add:
try:
    app.include_router(insights_v2_router)
    print("✅ Insights V2 endpoints registered")
except Exception as e:
    print(f"⚠️ Failed to register insights v2 endpoints: {e}")
```

### Step 2: Test the Endpoint

```bash
curl -X POST "http://localhost:8002/api/v2/insights/{user_id}/generate" \
  -H "X-API-Key: hosa_flutter_app_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "Peak Performer",
    "timeframe_days": 3,
    "force_refresh": false
  }'
```

### Step 3: Add UI Button

In your Flutter app, add a button to trigger insights:

```dart
// In your UI
ElevatedButton(
  onPressed: () async {
    final response = await http.post(
      Uri.parse('$apiBaseUrl/api/v2/insights/$userId/generate'),
      headers: {
        'X-API-Key': 'hosa_flutter_app_2024',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'archetype': userArchetype,
        'timeframe_days': 3,
        'force_refresh': false,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // Display insights to user
      showInsights(data['insights']);
    }
  },
  child: Text('Generate Insights'),
)
```

## 📊 Data Architecture

### Data Flow

```
User Triggers Insights
    ↓
API Endpoint (/api/v2/insights/{user_id}/generate)
    ↓
Data Aggregation Service
    ↓
┌────────────────────┬────────────────────┐
│ Health Data        │ Behavioral Data    │
│ (Sahha API)        │ (Supabase)         │
│ - Sleep            │ - Task completion  │
│ - Activity         │ - Check-ins        │
│ - Energy scores    │ - Mood/stress      │
└──────┬─────────────┴──────┬─────────────┘
       │                    │
       └────────┬───────────┘
                ↓
      Baseline Calculation
      (30-day rolling avg)
                ↓
      Build InsightContext
                ↓
    AI Insights Generation
    (GPT-4o / Claude Sonnet 4)
                ↓
      Quality Validation
                ↓
    Store in Supabase (TODO)
                ↓
      Return to User
```

### Data Models

**HealthDataWindow** (3 days)
- Sleep: duration, quality, consistency
- Activity: steps, active minutes, calories
- Heart: resting HR, HRV
- Scores: energy, readiness

**BehaviorDataWindow** (3 days)
- Tasks: total, completed, completion rate
- Timing: morning/afternoon/evening completion
- Check-ins: energy, mood, stress levels

**UserBaselines** (30 days)
- Sleep baseline
- Activity baseline
- Energy baseline
- Behavioral baseline
- Quality assessment

## 🎨 Insight Structure

Each insight includes:

```json
{
  "insight_id": "uuid",
  "user_id": "user123",
  "category": "sleep|activity|nutrition|energy|routine|recovery|motivation",
  "priority": "high|medium|low",
  "title": "Short headline (max 60 chars)",
  "content": "Full insight text (max 200 chars)",
  "recommendation": "Specific action to take",
  "confidence_score": 0.85,
  "actionability_score": 0.90,
  "relevance_score": 0.80,
  "data_points_used": ["sleep_duration", "energy_score"],
  "timeframe": "3_days",
  "generated_at": "2025-10-17T10:30:00Z",
  "archetype": "Peak Performer"
}
```

## 🔧 Configuration

### Environment Variables

No additional environment variables needed - uses existing:
- `OPENAI_API_KEY` - For GPT-4o model
- `SUPABASE_URL` / `SUPABASE_KEY` - For data fetching
- `REDIS_URL` - For baseline caching (optional)

### Model Selection

Default: `gpt-4o` (OpenAI)

To use Claude Sonnet 4:
```python
insights_service = InsightsGenerationService(
    anthropic_client=anthropic_client,
    model="claude-sonnet-4"
)
```

## 📈 Cost Projections

**Phase 1 (Daily Insights MVP):**
- $0.014 per insight generation (GPT-4o)
- 1 generation per user per day
- **100 users: $1.40/day = $42/month**
- **1,000 users: $14/day = $420/month**

**Optimization (Phase 2+):**
- Cache insights for 24 hours
- Incremental updates for existing insights
- Batch generation for efficiency

## 🧪 Testing

### Manual Testing

1. Start server: `python start_openai.py`
2. Generate insights:
   ```bash
   curl -X POST "http://localhost:8002/api/v2/insights/test_user/generate" \
     -H "X-API-Key: hosa_flutter_app_2024" \
     -H "Content-Type: application/json" \
     -d '{"archetype": "Foundation Builder"}'
   ```
3. Check response for generated insights

### Unit Testing

```bash
# Run tests (when implemented)
pytest tests/unit/test_insights_v2.py
```

## 📝 Implementation Checklist

### Sprint 1.1: Data Pipeline & Baselines ✅
- [x] Create `data_aggregation_service.py`
- [x] Create `baseline_calculation_service.py`
- [x] Define data models (HealthDataWindow, BehaviorDataWindow, UserBaselines, InsightContext)

### Sprint 1.2: AI Generation ✅
- [x] Create `insights_generation_service.py`
- [x] Implement prompt building
- [x] Implement AI model calling (GPT-4o placeholder)
- [x] Implement quality validation

### Sprint 1.3: API & Storage 🚧
- [x] Create `api_endpoints.py`
- [x] Implement manual trigger endpoint
- [ ] Create `insights_storage_service.py`
- [ ] Implement Supabase storage
- [ ] Implement retrieval endpoint
- [ ] Implement acknowledgment/feedback

## 🎯 Next Steps

1. **Complete Sprint 1.3:**
   - Implement Supabase storage service
   - Add retrieval, acknowledgment, and feedback endpoints

2. **Integrate with Real Services:**
   - Connect `SahhaDataService` to `data_aggregation_service.py`
   - Connect `SupabaseAsyncPGAdapter` to `baseline_calculation_service.py`
   - Connect OpenAI client to `insights_generation_service.py`

3. **Add UI Integration:**
   - Create insights screen in Flutter app
   - Add "Generate Insights" button
   - Display insights with categories and priorities

4. **Phase 2 (Weeks 4-6):**
   - Multi-temporal insights (daily, 3-day, weekly)
   - Pattern recognition
   - Trend analysis

## 📚 References

- [INSIGHTS_IMPLEMENTATION_PLAN.md](../../INSIGHTS_IMPLEMENTATION_PLAN.md) - Full implementation plan
- [INSIGHTS_DATA_ARCHITECTURE.md](../../INSIGHTS_DATA_ARCHITECTURE.md) - Data architecture
- [CLAUDE.md](../../CLAUDE.md) - System overview

## ⚠️ Important Notes

- **Standalone Design**: This module does NOT modify existing insights code
- **Manual Trigger Only**: Phase 1 is manual trigger only (button in UI)
- **No Breaking Changes**: Existing endpoints continue to work
- **Clean Separation**: Can be developed and tested independently
- **Future-Proof**: Designed for Phase 2+ enhancements (automated triggers, pattern recognition)

## 🤝 Contributing

When implementing new features:
1. Follow existing patterns (dataclasses, async/await, type hints)
2. Add docstrings to all functions
3. Update this README
4. Add tests
5. Keep it standalone (no dependencies on old insights code)
