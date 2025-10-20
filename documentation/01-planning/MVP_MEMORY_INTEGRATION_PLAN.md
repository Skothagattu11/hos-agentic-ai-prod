# MVP Memory Integration Plan
## Unified Memory Service for Behavior, Circadian, and Engagement Learning

## Overview

This plan implements a **simple but effective** memory system that enables continuous learning and adaptation across behavior analysis, circadian rhythm optimization, and user engagement patterns. The focus is on **MVP functionality** that works immediately while building toward more sophisticated learning.

## Current System Analysis

### **Existing Data Sources**
```json
{
  "behavior_analysis": {
    "table": "holistic_analysis_results",
    "data": "behavioral_patterns, recommendations, archetype_effectiveness"
  },
  "engagement_metrics": {
    "tables": ["task_checkins", "calendar_selections"],
    "data": "completion_rates, satisfaction_ratings, calendar_adoption"
  },
  "health_biomarkers": {
    "source": "user_data_service",
    "data": "sleep_patterns, hrv, activity, recovery_scores"
  },
  "memory_system": {
    "tables": ["holistic_shortterm_memory", "holistic_longterm_memory", "holistic_meta_memory"],
    "status": "partially_implemented"
  }
}
```

## MVP Memory Integration Architecture

### **Phase 1: Core Memory Methods (Week 1)**

#### **1. Enhanced HolisticMemoryService**

Add these key methods to `services/agents/memory/holistic_memory_service.py`:

```python
class HolisticMemoryService:

    # ======== BEHAVIOR MEMORY ========

    async def get_behavior_context(self, user_id: str, archetype: str = None) -> Dict[str, Any]:
        """Get behavioral context for continuity"""
        return {
            "last_analysis": await self._get_last_behavior_analysis(user_id, archetype),
            "successful_strategies": await self._get_successful_behavior_strategies(user_id),
            "engagement_patterns": await self._get_engagement_behavior_patterns(user_id),
            "adaptation_history": await self._get_behavior_adaptations(user_id)
        }

    async def store_behavior_learning(self, user_id: str, analysis_result: Dict,
                                   engagement_data: Dict, effectiveness_score: float) -> bool:
        """Store behavioral learning with engagement correlation"""

    # ======== CIRCADIAN MEMORY ========

    async def get_circadian_context(self, user_id: str) -> Dict[str, Any]:
        """Get circadian rhythm context for energy optimization"""
        return {
            "energy_patterns": await self._get_energy_pattern_history(user_id),
            "schedule_effectiveness": await self._get_schedule_performance(user_id),
            "biomarker_trends": await self._get_circadian_biomarker_patterns(user_id),
            "timing_preferences": await self._get_proven_timing_patterns(user_id)
        }

    async def store_circadian_learning(self, user_id: str, energy_analysis: Dict,
                                     schedule_performance: Dict, biomarker_correlation: Dict) -> bool:
        """Store circadian learning with performance correlation"""

    # ======== ENGAGEMENT MEMORY ========

    async def get_engagement_context(self, user_id: str) -> Dict[str, Any]:
        """Get engagement patterns for plan optimization"""
        return {
            "completion_patterns": await self._get_completion_patterns(user_id),
            "calendar_adoption": await self._get_calendar_adoption_patterns(user_id),
            "satisfaction_trends": await self._get_satisfaction_patterns(user_id),
            "timing_preferences": await self._get_engagement_timing_patterns(user_id)
        }

    # ======== UNIFIED CONTEXT ========

    async def get_unified_context(self, user_id: str, archetype: str = None) -> Dict[str, Any]:
        """Get comprehensive context for plan generation"""
        behavior_context = await self.get_behavior_context(user_id, archetype)
        circadian_context = await self.get_circadian_context(user_id)
        engagement_context = await self.get_engagement_context(user_id)

        return {
            "behavior_memory": behavior_context,
            "circadian_memory": circadian_context,
            "engagement_memory": engagement_context,
            "cross_correlations": await self._analyze_cross_correlations(
                behavior_context, circadian_context, engagement_context
            ),
            "retrieved_at": datetime.now().isoformat()
        }
```

#### **2. Memory-Aware Behavior Agent**

Update `services/agents/behavior/main.py`:

```python
async def _get_memory_context(self, user_id: str) -> dict:
    """Get actual behavioral context from memory service"""
    memory_service = HolisticMemoryService()

    # Get behavior-specific memory
    behavior_context = await memory_service.get_behavior_context(user_id, self.archetype)

    # Get engagement patterns to understand what works
    engagement_context = await memory_service.get_engagement_context(user_id)

    return {
        "previous_analysis": behavior_context.get("last_analysis", {}),
        "successful_strategies": behavior_context.get("successful_strategies", []),
        "engagement_patterns": engagement_context.get("completion_patterns", {}),
        "calendar_adoption": engagement_context.get("calendar_adoption", {}),
        "satisfaction_trends": engagement_context.get("satisfaction_trends", {}),
        "retrieved_at": datetime.now().isoformat()
    }
```

#### **3. Memory-Aware Circadian-Energy Agent**

Create `services/agents/circadian_energy/main.py`:

```python
class CircadianEnergyAgent(BaseAgent):

    async def _get_memory_context(self, user_id: str) -> dict:
        """Get circadian and engagement memory for energy optimization"""
        memory_service = HolisticMemoryService()

        circadian_context = await memory_service.get_circadian_context(user_id)
        engagement_context = await memory_service.get_engagement_context(user_id)

        return {
            "energy_patterns": circadian_context.get("energy_patterns", {}),
            "schedule_effectiveness": circadian_context.get("schedule_effectiveness", {}),
            "timing_preferences": circadian_context.get("timing_preferences", {}),
            "engagement_timing": engagement_context.get("timing_preferences", {}),
            "biomarker_trends": circadian_context.get("biomarker_trends", {}),
            "retrieved_at": datetime.now().isoformat()
        }
```

### **Phase 2: Engagement Data Integration (Week 2)**

#### **4. Engagement Memory Collectors**

```python
class EngagementMemoryCollector:
    """Collects and aggregates engagement data for memory storage"""

    async def collect_completion_patterns(self, user_id: str, days: int = 30) -> Dict:
        """Analyze task completion patterns from task_checkins table"""
        completion_data = await self._get_task_checkins(user_id, days)

        return {
            "overall_completion_rate": self._calculate_completion_rate(completion_data),
            "completion_by_time": self._analyze_completion_timing(completion_data),
            "completion_by_task_type": self._analyze_completion_by_type(completion_data),
            "satisfaction_correlation": self._correlate_completion_satisfaction(completion_data),
            "streak_patterns": self._analyze_streak_patterns(completion_data)
        }

    async def collect_calendar_adoption_patterns(self, user_id: str, days: int = 30) -> Dict:
        """Analyze calendar adoption from calendar_selections table"""
        calendar_data = await self._get_calendar_selections(user_id, days)

        return {
            "selection_rate": self._calculate_selection_rate(calendar_data),
            "selection_preferences": self._analyze_selection_preferences(calendar_data),
            "timing_patterns": self._analyze_calendar_timing(calendar_data),
            "follow_through_rate": await self._calculate_follow_through(user_id, calendar_data)
        }

    async def _get_task_checkins(self, user_id: str, days: int) -> List[Dict]:
        """Fetch task checkin data"""
        # Implementation fetches from task_checkins table

    async def _get_calendar_selections(self, user_id: str, days: int) -> List[Dict]:
        """Fetch calendar selection data"""
        # Implementation fetches from calendar_selections table
```

### **Phase 3: Cross-Agent Memory Integration (Week 3)**

#### **5. Unified Plan Generation with Memory**

Update routine and nutrition agents to use unified memory:

```python
# In services/agents/routine/main.py and services/agents/nutrition/main.py

async def _generate_plan_with_memory(self, user_id: str, archetype: str) -> Dict:
    """Generate plans using unified memory context"""
    memory_service = HolisticMemoryService()

    # Get comprehensive context
    unified_context = await memory_service.get_unified_context(user_id, archetype)

    # Extract key insights for plan generation
    plan_context = {
        "behavior_insights": {
            "successful_strategies": unified_context["behavior_memory"]["successful_strategies"],
            "archetype_effectiveness": unified_context["behavior_memory"]["last_analysis"]
        },
        "circadian_insights": {
            "energy_patterns": unified_context["circadian_memory"]["energy_patterns"],
            "optimal_timing": unified_context["circadian_memory"]["timing_preferences"]
        },
        "engagement_insights": {
            "completion_patterns": unified_context["engagement_memory"]["completion_patterns"],
            "calendar_preferences": unified_context["engagement_memory"]["calendar_adoption"],
            "satisfaction_drivers": unified_context["engagement_memory"]["satisfaction_trends"]
        },
        "cross_correlations": unified_context["cross_correlations"]
    }

    # Generate plan with memory-informed context
    return await self._create_memory_informed_plan(plan_context)
```

## Implementation Strategy

### **Week 1: Foundation**
```python
# Implement core memory methods
1. Add behavior_context methods to HolisticMemoryService
2. Update behavior agent _get_memory_context() to use real data
3. Create basic circadian memory structure
4. Test with existing behavior analysis endpoint

# Expected Outcome: Behavior agent knows about previous analysis
```

### **Week 2: Engagement Integration**
```python
# Connect engagement data to memory
1. Create EngagementMemoryCollector class
2. Implement completion and calendar pattern analysis
3. Store engagement patterns in shortterm/longterm memory
4. Test engagement memory retrieval

# Expected Outcome: System understands what users actually do vs. plan
```

### **Week 3: Cross-Agent Learning**
```python
# Unify memory across agents
1. Implement get_unified_context() method
2. Update plan generation agents to use unified memory
3. Implement cross-correlation analysis
4. Test complete memory-informed plan generation

# Expected Outcome: Plans improve based on behavior + circadian + engagement learning
```

## Memory Storage Schema

### **Enhanced Memory Tables**

```sql
-- Add engagement-specific memory categories to existing tables

-- holistic_shortterm_memory additions
INSERT INTO holistic_shortterm_memory (user_id, memory_category, content, confidence_score, source_agent)
VALUES
('user123', 'completion_patterns', '{"completion_rate": 0.73, "best_times": ["09:00", "15:00"]}', 0.85, 'engagement_collector'),
('user123', 'calendar_adoption', '{"selection_rate": 0.62, "follow_through": 0.78}', 0.82, 'engagement_collector');

-- holistic_longterm_memory additions
INSERT INTO holistic_longterm_memory (user_id, memory_category, content, confidence_score)
VALUES
('user123', 'behavior_effectiveness', '{"archetype": "Foundation Builder", "success_rate": 0.68}', 0.79),
('user123', 'circadian_patterns', '{"peak_hours": ["09:00-11:00"], "energy_dips": ["14:00-15:00"]}', 0.84);

-- holistic_meta_memory enhancements
-- Track learning effectiveness across agents
```

### **Memory Quality Metrics**

```python
class MemoryQualityTracker:
    """Track memory quality and learning effectiveness"""

    async def calculate_memory_quality(self, user_id: str) -> float:
        """Calculate overall memory quality score (0.0-1.0)"""
        scores = {
            "behavior_memory_quality": await self._assess_behavior_memory(user_id),
            "circadian_memory_quality": await self._assess_circadian_memory(user_id),
            "engagement_memory_quality": await self._assess_engagement_memory(user_id),
            "cross_correlation_quality": await self._assess_correlations(user_id)
        }

        return sum(scores.values()) / len(scores)

    async def get_learning_trends(self, user_id: str) -> Dict:
        """Track how well the system is learning about the user"""
        return {
            "improvement_rate": await self._calculate_improvement_rate(user_id),
            "prediction_accuracy": await self._calculate_prediction_accuracy(user_id),
            "adaptation_speed": await self._calculate_adaptation_speed(user_id)
        }
```

## Expected Outcomes

### **Immediate Benefits (Week 1)**
- Behavior agent remembers previous analysis and recommendations
- No more "starting from scratch" each analysis
- Continuity in behavioral insights and strategies

### **Short-term Benefits (Week 2-3)**
- Plans informed by actual user engagement patterns
- Recommendations based on what users actually complete
- Calendar adoption preferences influence plan structure
- Timing recommendations based on actual completion patterns

### **Medium-term Benefits (Month 1-2)**
- Cross-agent learning improves plan quality
- Circadian recommendations align with engagement patterns
- Behavioral strategies adapted based on completion rates
- Personalization becomes increasingly accurate

### **Key Success Metrics**
```python
{
  "memory_quality_score": "> 0.7 (good quality memory)",
  "plan_effectiveness": "+ 25% improvement in completion rates",
  "user_satisfaction": "+ 30% improvement in satisfaction ratings",
  "system_learning": "Demonstrable improvement over 30-day periods",
  "cross_agent_correlation": "Behavior + circadian + engagement insights align"
}
```

## Technical Implementation Notes

### **Database Integration**
- **Reuse existing tables**: `holistic_shortterm_memory`, `holistic_longterm_memory`, `task_checkins`, `calendar_selections`
- **Minimal schema changes**: Add memory categories, no new tables needed
- **Backward compatible**: Existing memory service functionality preserved

### **Performance Considerations**
- **Lazy loading**: Memory context only fetched when needed
- **Caching**: Cache unified context for session duration
- **Aggregation**: Pre-compute engagement patterns, don't calculate real-time

### **Error Handling**
- **Graceful degradation**: If memory unavailable, use default context
- **Confidence scoring**: Lower confidence for incomplete memory data
- **Fallback patterns**: Default to archetype patterns when memory insufficient

This MVP plan provides **immediate value** while building the foundation for sophisticated multi-agent learning and continuous adaptation.