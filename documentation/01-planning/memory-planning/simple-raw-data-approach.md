# Simple Raw Data Approach for AI Context Generation

## Overview

Instead of complex API integrations and pre-processed summaries, use **raw engagement data** directly with AI to generate context. This approach is simpler, more flexible, and more effective.

## Philosophy

**Let AI do what AI does best**: Analyze raw data and find patterns we didn't think of, rather than forcing it to work with our pre-conceived data processing.

## Current vs Simplified Approach

### ❌ Current Complex Approach
```python
# Multiple API calls with pre-processed data
engagement_summary = await get_engagement_context(user_id)
calendar_stats = await get_calendar_workflow_stats(user_id)
timing_patterns = await get_timing_analysis(user_id)
satisfaction_trends = await get_satisfaction_analysis(user_id)
# ... 5+ API calls with complex processing
```

### ✅ New Simple Approach
```python
# 3 simple raw data queries
raw_data = await get_raw_engagement_data(user_id)
context = await ai_analyze_engagement(raw_data)
await store_context(user_id, context, raw_data)
```

## Raw Data Requirements

We need exactly **3 simple data sources**:

### 1. Calendar Items (What was planned)
```sql
SELECT
    plan_item_id,
    title,
    task_type,
    time_block,
    scheduled_time,
    estimated_duration_minutes,
    selection_timestamp
FROM calendar_selections cs
JOIN plan_items pi ON cs.plan_item_id = pi.id
WHERE profile_id = ?
AND selection_timestamp >= ?
ORDER BY selection_timestamp DESC
```

**Purpose**: Shows what user chose to put on their calendar from AI recommendations

### 2. Check-in Data (What actually happened)
```sql
SELECT
    plan_item_id,
    completion_status,
    satisfaction_rating,
    planned_date,
    completed_at,
    user_notes
FROM task_checkins
WHERE profile_id = ?
AND planned_date >= ?
ORDER BY planned_date DESC
```

**Purpose**: Shows what user actually did and how they felt about it

### 3. Daily Journals (Holistic feedback)
```sql
SELECT
    journal_date,
    energy_level,
    mood_rating,
    sleep_quality,
    stress_level,
    what_went_well,
    what_was_challenging,
    tomorrow_intentions
FROM daily_journals
WHERE profile_id = ?
AND journal_date >= ?
ORDER BY journal_date DESC
```

**Purpose**: Shows overall patterns and qualitative insights

## Implementation Structure

### Service Architecture

```python
class SimpleEngagementDataService:
    """Fetch raw engagement data for AI analysis"""

    async def get_raw_engagement_data(self, user_id: str, days: int = 30) -> dict:
        """Get all raw engagement data for AI analysis"""

        # 1. Get calendar selections (what was planned)
        calendar_items = await self._get_calendar_selections_raw(user_id, days)

        # 2. Get check-ins (what actually happened)
        checkin_data = await self._get_task_checkins_raw(user_id, days)

        # 3. Get journals (holistic feedback)
        journal_data = await self._get_daily_journals_raw(user_id, days=14)

        return {
            "calendar_selections": calendar_items,
            "task_checkins": checkin_data,
            "daily_journals": journal_data,
            "data_period": {
                "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "days_analyzed": days
            }
        }

    async def _get_calendar_selections_raw(self, user_id: str, days: int) -> List[dict]:
        """Get raw calendar selection data"""
        # Direct database query - no processing
        pass

    async def _get_task_checkins_raw(self, user_id: str, days: int) -> List[dict]:
        """Get raw check-in data"""
        # Direct database query - no processing
        pass

    async def _get_daily_journals_raw(self, user_id: str, days: int) -> List[dict]:
        """Get raw journal data"""
        # Direct database query - no processing
        pass
```

### AI Context Generator

```python
class AIEngagementAnalyzer:
    """Use AI to analyze raw engagement data"""

    async def generate_context(self, raw_data: dict) -> str:
        """Generate context from raw engagement data"""

        prompt = f"""
        Analyze this user's engagement data and create a concise context summary:

        CALENDAR SELECTIONS (What they planned - last 30 days):
        {json.dumps(raw_data['calendar_selections'], indent=2)}

        TASK CHECK-INS (What they actually did - last 30 days):
        {json.dumps(raw_data['task_checkins'], indent=2)}

        DAILY JOURNALS (How they felt - last 14 days):
        {json.dumps(raw_data['daily_journals'], indent=2)}

        Create a focused context summary covering:
        1. What types of tasks work best vs struggle with
        2. Best engagement times and patterns
        3. Satisfaction patterns and preferences
        4. Recent behavioral changes or trends
        5. Key insights for personalizing next analysis

        Focus on actionable insights for behavior and circadian analysis.
        Keep it concise and specific to this user's patterns.
        """

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )

        return response.choices[0].message.content
```

### Integration with Context Service

```python
class AIContextGeneratorService:
    """Enhanced context generation with engagement data"""

    async def generate_user_context(self, user_id: str) -> str:
        """Generate complete user context including engagement data"""

        # 1. Get engagement data
        engagement_service = SimpleEngagementDataService()
        engagement_data = await engagement_service.get_raw_engagement_data(user_id)

        # 2. Get other data sources (plans, health data, etc.)
        last_plans = await self._get_last_plans(user_id, limit=3)
        previous_context = await self._get_last_context(user_id)

        # 3. Generate comprehensive context
        context_prompt = f"""
        Create user context for personalized health analysis:

        PREVIOUS PLANS (last 3):
        {last_plans}

        ENGAGEMENT DATA:
        {engagement_data}

        PREVIOUS CONTEXT:
        {previous_context or "None"}

        Create comprehensive context covering:
        1. What worked vs what didn't from previous plans
        2. User engagement patterns and preferences
        3. Timing and satisfaction patterns
        4. Recent changes in behavior or preferences
        5. Key insights for next behavior and circadian analysis
        6. What to avoid based on past struggles

        Keep it actionable and focused.
        """

        # 4. AI generates complete context
        context_summary = await self._call_ai_for_context(context_prompt)

        # 5. Store context with source data
        await self._store_context(user_id, context_summary, {
            'engagement_data': engagement_data,
            'plans_analyzed': last_plans,
            'generation_method': 'ai_raw_data'
        })

        return context_summary
```

## Data Structure Examples

### Raw Calendar Selections
```json
[
  {
    "plan_item_id": "abc123",
    "title": "Morning HRV Check",
    "task_type": "wellness",
    "time_block": "Morning Wake-up",
    "scheduled_time": "06:00:00",
    "estimated_duration_minutes": 3,
    "selection_timestamp": "2024-01-15T08:00:00Z"
  }
]
```

### Raw Check-in Data
```json
[
  {
    "plan_item_id": "abc123",
    "completion_status": "completed",
    "satisfaction_rating": 4,
    "planned_date": "2024-01-15",
    "completed_at": "2024-01-15T06:05:00Z",
    "user_notes": "Felt good, HRV was high"
  }
]
```

### Raw Journal Data
```json
[
  {
    "journal_date": "2024-01-15",
    "energy_level": 4,
    "mood_rating": 4,
    "sleep_quality": 3,
    "stress_level": 2,
    "what_went_well": "Morning routine was smooth",
    "what_was_challenging": "Afternoon energy dip",
    "tomorrow_intentions": "Try 10min walk after lunch"
  }
]
```

## Integration Points

### With Behavior Analysis
```python
# In behavior analysis endpoint
context_service = AIContextGeneratorService()
enhanced_prompt = await context_service.enhance_analysis_prompt(
    base_behavior_prompt, user_id
)
```

### With Circadian Analysis
```python
# In circadian analysis endpoint
context_service = AIContextGeneratorService()
enhanced_prompt = await context_service.enhance_analysis_prompt(
    base_circadian_prompt, user_id
)
```

## Database Schema Updates

### Simple Context Storage
```sql
-- Enhanced context table
ALTER TABLE user_analysis_context
ADD COLUMN engagement_data_included BOOLEAN DEFAULT FALSE,
ADD COLUMN data_period_days INTEGER DEFAULT 30,
ADD COLUMN generation_method VARCHAR(50) DEFAULT 'ai_raw_data';
```

### Indexes for Performance
```sql
-- Optimized indexes for raw data queries
CREATE INDEX idx_calendar_selections_user_date
ON calendar_selections (profile_id, selection_timestamp DESC);

CREATE INDEX idx_task_checkins_user_date
ON task_checkins (profile_id, planned_date DESC);

CREATE INDEX idx_daily_journals_user_date
ON daily_journals (profile_id, journal_date DESC);
```

## Performance Considerations

### Data Volume (Typical User)
- **Calendar selections**: 5-10 items per analysis
- **Task check-ins**: 20-50 per month
- **Daily journals**: 14 entries per analysis

**Total**: ~100 records max = Very manageable for AI

### Query Performance
- Direct table queries (no complex JOINs)
- Indexed by user_id and date
- Small result sets
- Fast response times

## Benefits of This Approach

### 1. Simplicity
- **3 simple queries** instead of complex API orchestration
- **No pre-processing** required
- **Direct database access** - no API overhead

### 2. Flexibility
- **AI finds patterns** we didn't anticipate
- **Adapts to new data** automatically
- **No hardcoded logic** to maintain

### 3. Effectiveness
- **Complete data picture** - AI sees everything
- **Better insights** from raw patterns
- **Continuously improving** with more data

### 4. Maintainability
- **Single data flow** - easy to debug
- **No complex transformations** to break
- **Future-proof** for new engagement features

## Implementation Timeline

### Phase 1: Core Data Service (Week 1)
1. Create `SimpleEngagementDataService`
2. Implement 3 raw data queries
3. Test data retrieval and formatting

### Phase 2: AI Integration (Week 1)
1. Create `AIEngagementAnalyzer`
2. Develop context generation prompts
3. Test AI analysis quality

### Phase 3: Context Service Integration (Week 1)
1. Enhance `AIContextGeneratorService`
2. Integrate engagement data into context generation
3. Update context storage

### Phase 4: Analysis Enhancement (Week 2)
1. Integrate with behavior analysis
2. Integrate with circadian analysis
3. Test improved personalization

## Success Metrics

1. **Context Quality**: Better insights about user patterns
2. **Analysis Personalization**: More relevant recommendations
3. **System Simplicity**: Fewer API calls and complexity
4. **User Satisfaction**: Better adherence to personalized plans

## Conclusion

This raw data approach leverages the strength of both systems:
- **Existing APIs** provide rich, clean engagement data
- **AI analysis** finds patterns and creates actionable context
- **Simple integration** reduces complexity and maintenance

The result is a more effective, maintainable, and future-proof system for personalized health analysis.