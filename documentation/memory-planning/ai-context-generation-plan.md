# AI-Powered Context Generation Plan

## Overview

Replace the complex 4-layer memory system with a simple, AI-powered context generation approach that leverages existing APIs to create focused, actionable context for personalized health analysis.

## Strategy

**Core Concept**: Use AI to analyze engagement data, calendar check-ins, and previous plans to generate a concise context summary that improves the personalization of behavior and circadian analysis.

## Architecture

### Data Flow
```
Existing APIs → AI Context Generator → Simple Storage → Enhanced Analysis
    ↓                    ↓                   ↓              ↓
Engagement APIs     AI analyzes &       Store in        Use for next
Calendar APIs       summarizes         simple table     analysis
Last 3 plans        Creates context
```

### Key Components

1. **Data Sources** (existing APIs)
   - Engagement APIs
   - Calendar check-in APIs
   - Previous plan history (last 3 plans)

2. **AI Context Generator Service**
   - Analyzes all data sources
   - Creates focused context summary
   - Stores results for future use

3. **Simple Storage**
   - Single context table
   - One record per user per day
   - Iterative context building

4. **Enhanced Analysis**
   - Behavior analysis with context
   - Circadian analysis with context
   - Personalized recommendations

## Database Schema

```sql
CREATE TABLE user_analysis_context (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    context_summary TEXT NOT NULL,  -- AI-generated summary
    source_data JSONB,              -- Raw data used to generate context
    plans_analyzed JSONB,           -- Which plans were included
    engagement_period TEXT,         -- Date range analyzed
    created_at TIMESTAMP DEFAULT NOW(),

    -- Simple constraints
    UNIQUE(user_id, created_at::date)  -- One context per user per day
);
```

## Service Implementation

### AIContextGeneratorService

```python
class AIContextGeneratorService:
    """Uses AI to create simple, focused context from existing APIs"""

    async def generate_user_context(self, user_id: str) -> str:
        """Single method that does everything"""

        # 1. Gather from existing APIs
        engagement_data = await self._get_engagement_data(user_id)
        calendar_data = await self._get_calendar_checkins(user_id)
        last_plans = await self._get_last_plans(user_id, limit=3)
        previous_context = await self._get_last_context(user_id)

        # 2. Let AI analyze and create context
        context_prompt = f"""
        Analyze this user's health data and create a concise context summary for personalized analysis:

        ENGAGEMENT DATA (last 30 days):
        {engagement_data}

        CALENDAR CHECK-INS (last 14 days):
        {calendar_data}

        PREVIOUS PLANS (last 3):
        {last_plans}

        PREVIOUS CONTEXT:
        {previous_context or "None"}

        Create a focused summary covering:
        1. What worked vs what didn't work from previous plans
        2. Current engagement patterns and adherence
        3. Recent sleep/circadian changes
        4. Key insights for next analysis
        5. What to avoid based on past failures

        Keep it concise and actionable for behavior and circadian analysis.
        """

        # 3. AI generates the context
        context_summary = await self._call_ai_for_context(context_prompt)

        # 4. Store in simple table
        await self._store_context(user_id, context_summary, {
            'engagement_data': engagement_data,
            'calendar_data': calendar_data,
            'plans_analyzed': last_plans
        })

        return context_summary

    async def enhance_analysis_prompt(self, base_prompt: str, user_id: str) -> str:
        """Add user context to analysis prompts"""
        context = await self._get_last_context(user_id)

        if context:
            return f"""
            {base_prompt}

            USER CONTEXT FROM PREVIOUS ANALYSIS:
            {context}

            Use this context to personalize your analysis and avoid repeating failed strategies.
            """

        return base_prompt

    # Helper methods
    async def _get_engagement_data(self, user_id: str):
        """Get engagement data from existing APIs"""
        # Call engagement APIs
        pass

    async def _get_calendar_checkins(self, user_id: str):
        """Get calendar check-in data from existing APIs"""
        # Call calendar APIs
        pass

    async def _get_last_plans(self, user_id: str, limit: int = 3):
        """Get last N plans from analysis results"""
        # Query holistic_analysis_results table
        pass

    async def _get_last_context(self, user_id: str):
        """Get most recent context for this user"""
        # Query user_analysis_context table
        pass

    async def _call_ai_for_context(self, prompt: str) -> str:
        """Use AI to generate context summary"""
        # Call OpenAI API
        pass

    async def _store_context(self, user_id: str, summary: str, source_data: dict):
        """Store generated context in database"""
        # Insert into user_analysis_context table
        pass
```

## Integration Points

### Behavior Analysis Enhancement
```python
# In behavior analysis endpoint
context_service = AIContextGeneratorService()
enhanced_prompt = await context_service.enhance_analysis_prompt(
    base_behavior_prompt, user_id
)
# Use enhanced_prompt for analysis
```

### Circadian Analysis Enhancement
```python
# In circadian analysis endpoint
context_service = AIContextGeneratorService()
enhanced_prompt = await context_service.enhance_analysis_prompt(
    base_circadian_prompt, user_id
)
# Use enhanced_prompt for analysis
```

## Implementation Phases

### Phase 1: Core Implementation
1. **Create simple context table**
   - Add migration for `user_analysis_context`
   - Set up indexes and constraints

2. **Build AIContextGeneratorService**
   - Core service structure
   - AI prompt engineering
   - Database operations

3. **Integrate with existing APIs**
   - Connect to engagement APIs
   - Connect to calendar check-in APIs
   - Query existing plan data

4. **Test AI context generation**
   - Validate context quality
   - Refine AI prompts
   - Test with sample users

### Phase 2: Analysis Integration
1. **Add context enhancement to behavior analysis**
   - Modify behavior analysis endpoint
   - Test improved personalization
   - Compare results with/without context

2. **Add context enhancement to circadian analysis**
   - Modify circadian analysis endpoint
   - Test sleep pattern personalization
   - Validate circadian insights

3. **End-to-end testing**
   - Test complete workflow
   - Validate context persistence
   - Monitor analysis quality improvements

### Phase 3: Optimization
1. **Refine AI prompts based on results**
   - Analyze context effectiveness
   - Improve prompt specificity
   - Optimize for different user types

2. **Add context refresh triggers**
   - Refresh after significant health changes
   - Time-based refresh logic
   - Event-driven updates

3. **Monitor and improve**
   - Track context quality metrics
   - Monitor analysis improvements
   - User feedback integration

## Benefits

### 1. Simplicity
- **One table** instead of 4 memory layers
- **One service** with clear responsibilities
- **Clear data flow** that's easy to understand and debug

### 2. Intelligence
- **AI-powered analysis** handles complex pattern recognition
- **Adaptive context** that improves over time
- **Personalized insights** based on actual user data

### 3. Practicality
- **Uses existing APIs** - no new data collection needed
- **Leverages current infrastructure** - builds on what's already working
- **Immediate value** - improves analysis quality from day one

### 4. Effectiveness
- **Focused context** for behavior and circadian analysis
- **Avoids failed strategies** based on past experience
- **Iterative improvement** - each analysis gets better context

### 5. Maintainability
- **Single source of truth** for user context
- **Simple debugging** - easy to see what context was used
- **Extensible design** - easy to add new data sources

## Success Metrics

1. **Context Quality**
   - Relevance of generated context
   - Accuracy of insights about what worked/failed
   - Usefulness for analysis personalization

2. **Analysis Improvement**
   - Better recommendation personalization
   - Reduced repetition of failed strategies
   - Improved user satisfaction with plans

3. **System Performance**
   - Context generation speed
   - Database query efficiency
   - API integration reliability

## Migration Strategy

### From Current Memory System
1. **Parallel implementation** - build new system alongside current
2. **Gradual migration** - test with subset of users first
3. **Data preservation** - keep existing memory data as backup
4. **Progressive rollout** - migrate users in phases

### Risk Mitigation
1. **Fallback mechanism** - use basic analysis if context generation fails
2. **Context validation** - ensure AI-generated context is reasonable
3. **Performance monitoring** - track impact on analysis speed
4. **User feedback loop** - monitor analysis quality changes

## Conclusion

This AI-powered context generation approach provides a much simpler, more effective alternative to the complex 4-layer memory system. By leveraging existing APIs and AI intelligence, it delivers personalized context that directly improves behavior and circadian analysis quality while maintaining simplicity and maintainability.

The key insight is to let AI do what it does best (pattern recognition and summarization) while keeping the overall architecture simple and focused on the actual goal: better personalized health analysis.