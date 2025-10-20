# Unified Circadian-Energy Analysis Agent Design

## Overview

This document defines the comprehensive design for a unified Circadian-Energy Analysis Agent that integrates circadian rhythm analysis with energy zone evaluation to provide personalized scheduling recommendations aligned with the user's natural biological patterns.

## Agent Input Specification

### Primary Input Data Structure

```json
{
  "user_profile": {
    "user_id": "string",
    "archetype": "foundation_builder|transformation_seeker|systematic_improver|peak_performer|resilience_rebuilder|connected_explorer",
    "timezone": "America/New_York",
    "preferred_wake_time": "07:00:00",
    "preferred_sleep_time": "23:00:00"
  },
  "raw_biomarker_data": {
    "sahha_biomarkers": {
      "sleep": [
        {
          "id": "sleep_001",
          "createdDateTime": "2024-01-15T08:00:00Z",
          "startDateTime": "2024-01-14T23:30:00Z",
          "endDateTime": "2024-01-15T07:15:00Z",
          "value": 7.75,
          "unit": "hour",
          "type": "sleep_duration",
          "source": "whoop",
          "additionalProperties": {
            "efficiency": 89,
            "deep_sleep_minutes": 156,
            "rem_sleep_minutes": 98,
            "light_sleep_minutes": 211,
            "awake_minutes": 25,
            "sleep_latency_minutes": 8,
            "wake_episodes": 3,
            "hrv_rmssd": 42.3,
            "respiratory_rate": 14.2,
            "skin_temp_celsius": 33.8
          }
        }
      ],
      "activity": [
        {
          "id": "activity_001",
          "createdDateTime": "2024-01-15T20:00:00Z",
          "startDateTime": "2024-01-15T06:00:00Z",
          "endDateTime": "2024-01-15T22:00:00Z",
          "value": 2847,
          "unit": "step",
          "type": "steps",
          "source": "whoop",
          "additionalProperties": {
            "active_calories": 687,
            "total_calories": 2341,
            "distance_km": 2.1,
            "active_minutes": 73,
            "sedentary_minutes": 512,
            "strain_score": 12.4,
            "recovery_score": 78
          }
        }
      ],
      "body_metrics": [
        {
          "id": "body_001",
          "createdDateTime": "2024-01-15T08:00:00Z",
          "value": 42.3,
          "unit": "ms",
          "type": "heart_rate_variability_rmssd",
          "source": "whoop",
          "additionalProperties": {
            "resting_heart_rate": 58,
            "heart_rate_max": 142,
            "heart_rate_avg": 71
          }
        }
      ]
    },
    "historical_patterns": {
      "days_of_data": 14,
      "avg_sleep_duration": 7.2,
      "avg_sleep_efficiency": 84,
      "avg_bedtime": "23:15:00",
      "avg_wake_time": "07:30:00",
      "sleep_consistency_score": 76,
      "energy_patterns": {
        "peak_hours": ["09:00", "10:00", "11:00"],
        "low_hours": ["14:00", "15:00"],
        "recovery_hours": ["20:00", "21:00", "22:00"]
      }
    }
  },
  "behavior_analysis_context": {
    "recent_behavior_patterns": {
      "sleep_quality_trend": "improving",
      "stress_indicators": ["elevated_hrv_variance", "irregular_bedtime"],
      "activity_consistency": 0.73,
      "energy_stability": 0.68
    },
    "lifestyle_factors": {
      "work_schedule": "flexible",
      "exercise_frequency": 4,
      "caffeine_timing": ["07:00", "13:00"],
      "screen_time_evening": 2.5
    }
  }
}
```

## Agent Output Specification

### Primary Output Data Structure

```json
{
  "circadian_analysis": {
    "chronotype_assessment": {
      "primary_type": "moderate_morning_type",
      "confidence_score": 0.84,
      "supporting_evidence": [
        "Natural wake time aligns with 07:30 average",
        "Peak performance window 09:00-11:00",
        "Bedtime preference matches moderate morning pattern"
      ]
    },
    "circadian_rhythm_health": {
      "overall_score": 76,
      "stability_rating": "good",
      "key_indicators": {
        "sleep_timing_consistency": 0.78,
        "light_exposure_alignment": 0.82,
        "meal_timing_optimization": 0.65,
        "activity_rhythm_sync": 0.71
      },
      "disruption_patterns": [
        {
          "type": "social_jetlag",
          "severity": "mild",
          "impact": "15min average weekend shift",
          "recommendation": "Maintain consistent weekend wake time within 30min of weekday schedule"
        }
      ]
    }
  },
  "energy_zone_analysis": {
    "daily_energy_profile": {
      "peak_windows": [
        {
          "time_range": "09:00-11:30",
          "energy_level": 92,
          "confidence": 0.89,
          "optimal_activities": ["complex_cognitive_work", "strategic_planning", "creative_tasks"],
          "biomarker_support": "HRV and recovery scores highest during this window"
        }
      ],
      "productive_windows": [
        {
          "time_range": "13:00-15:30",
          "energy_level": 78,
          "confidence": 0.76,
          "optimal_activities": ["routine_tasks", "administrative_work", "moderate_exercise"],
          "biomarker_support": "Stable heart rate and moderate strain tolerance"
        }
      ],
      "maintenance_windows": [
        {
          "time_range": "16:00-18:00",
          "energy_level": 65,
          "confidence": 0.72,
          "optimal_activities": ["light_exercise", "social_activities", "meal_prep"],
          "biomarker_support": "Declining but stable energy markers"
        }
      ],
      "recovery_windows": [
        {
          "time_range": "20:00-22:30",
          "energy_level": 35,
          "confidence": 0.88,
          "optimal_activities": ["wind_down_routines", "light_stretching", "meditation"],
          "biomarker_support": "HRV preparation for sleep, declining core temp"
        }
      ]
    },
    "weekly_energy_patterns": {
      "monday": {
        "energy_adjustment": -12,
        "recommended_start_delay": "30min",
        "focus": "gentle_buildup"
      },
      "tuesday": {
        "energy_adjustment": +8,
        "recommended_start_delay": "0min",
        "focus": "peak_performance"
      },
      "wednesday": {
        "energy_adjustment": +15,
        "recommended_start_delay": "-15min",
        "focus": "sustained_high"
      },
      "friday": {
        "energy_adjustment": -5,
        "recommended_start_delay": "15min",
        "focus": "variable_adaptive"
      }
    }
  },
  "personalized_schedule_recommendations": {
    "optimal_daily_structure": {
      "wake_window": {
        "ideal_time": "07:15",
        "acceptable_range": "06:45-07:45",
        "light_exposure_protocol": "15min bright light within 30min of waking",
        "morning_routine_duration": "45-60min"
      },
      "peak_performance_block": {
        "time_range": "09:00-11:30",
        "activity_recommendations": [
          {
            "activity_type": "deep_cognitive_work",
            "duration": "90min",
            "intensity": "high",
            "break_pattern": "none - maintain flow state"
          },
          {
            "activity_type": "strategic_planning",
            "duration": "45min",
            "intensity": "high",
            "break_pattern": "5min movement break after"
          }
        ],
        "environmental_optimization": {
          "lighting": "bright_natural_or_5000k",
          "temperature": "68-70F",
          "noise": "minimal_or_focus_music",
          "nutrition": "avoid_heavy_meals_2hrs_prior"
        }
      },
      "afternoon_energy_management": {
        "predicted_dip": "14:00-15:30",
        "mitigation_strategies": [
          {
            "strategy": "power_nap",
            "duration": "10-20min",
            "timing": "13:45-14:05",
            "conditions": "dark_room_cool_temp"
          },
          {
            "strategy": "light_movement",
            "duration": "15min",
            "timing": "14:30",
            "activity": "outdoor_walk_or_stairs"
          }
        ],
        "activity_adjustments": {
          "avoid": ["complex_decision_making", "creative_work"],
          "prefer": ["administrative_tasks", "email_processing", "routine_maintenance"]
        }
      },
      "evening_wind_down": {
        "start_time": "20:30",
        "duration": "2-2.5hrs",
        "light_management": {
          "dim_lights_by": "21:00",
          "blue_light_cutoff": "21:30",
          "darkness_preparation": "22:30"
        },
        "activity_sequence": [
          {
            "time": "20:30-21:00",
            "activity": "gentle_movement",
            "description": "Light stretching or yoga"
          },
          {
            "time": "21:00-21:45",
            "activity": "calm_activities",
            "description": "Reading, journaling, meditation"
          },
          {
            "time": "21:45-22:30",
            "activity": "sleep_preparation",
            "description": "Personal hygiene, bedroom prep, breathing exercises"
          }
        ]
      }
    },
    "weekly_optimization": {
      "monday_protocol": {
        "energy_expectation": "gradual_buildup",
        "schedule_adjustments": {
          "later_start": "+30min",
          "gentler_morning": "extended_warm_up",
          "afternoon_focus": "planning_not_execution"
        }
      },
      "peak_days": {
        "tuesday_wednesday": {
          "energy_expectation": "maximum_capacity",
          "schedule_adjustments": {
            "earlier_start": "-15min",
            "extended_peak_windows": "+30min",
            "challenging_task_scheduling": "front_load_difficult_work"
          }
        }
      },
      "friday_adaptation": {
        "energy_expectation": "variable",
        "schedule_adjustments": {
          "flexible_timing": "real_time_energy_assessment",
          "backup_plans": "low_energy_alternatives_ready",
          "social_integration": "plan_collaborative_work"
        }
      }
    }
  },
  "integration_recommendations": {
    "routine_agent_handoff": {
      "exercise_scheduling": {
        "high_intensity_windows": ["09:30-10:30", "17:00-18:00"],
        "moderate_intensity_windows": ["07:00-08:00", "13:00-14:00"],
        "recovery_only_windows": ["20:00-22:00"],
        "avoid_exercise_windows": ["14:00-15:30", "22:00-06:00"]
      },
      "meal_timing_optimization": {
        "breakfast": {
          "ideal_time": "07:30-08:30",
          "composition": "protein_focused_stable_energy",
          "avoid": "high_sugar_quick_energy"
        },
        "lunch": {
          "ideal_time": "12:00-13:00",
          "composition": "balanced_sustaining",
          "pre_afternoon_energy": "include_complex_carbs"
        },
        "dinner": {
          "ideal_time": "18:00-19:00",
          "composition": "light_digestible",
          "sleep_preparation": "avoid_caffeine_alcohol"
        }
      }
    },
    "behavior_agent_feedback": {
      "habit_timing_optimization": [
        {
          "habit": "morning_hydration",
          "optimal_timing": "within_10min_of_waking",
          "circadian_rationale": "supports_cortisol_awakening_response"
        },
        {
          "habit": "caffeine_consumption",
          "optimal_timing": "90min_after_waking",
          "circadian_rationale": "allows_natural_cortisol_peak_avoids_afternoon_crash"
        }
      ],
      "lifestyle_adjustments": [
        {
          "factor": "screen_time_evening",
          "current_pattern": "2.5hrs_before_bed",
          "recommended_change": "reduce_to_1hr_blue_light_filters",
          "expected_impact": "improved_melatonin_production"
        }
      ]
    }
  },
  "monitoring_and_adaptation": {
    "key_biomarkers_to_track": [
      {
        "metric": "sleep_onset_latency",
        "target_range": "5-15min",
        "adaptation_trigger": "consistently_outside_range_3_days"
      },
      {
        "metric": "morning_hrv_trend",
        "target_trend": "stable_or_improving",
        "adaptation_trigger": "declining_trend_5_days"
      },
      {
        "metric": "afternoon_energy_dip_severity",
        "target_range": "mild_manageable",
        "adaptation_trigger": "severe_impact_on_productivity"
      }
    ],
    "schedule_adaptation_rules": [
      {
        "condition": "sleep_quality_declining",
        "adjustment": "shift_bedtime_earlier_15min_increments",
        "evaluation_period": "1_week"
      },
      {
        "condition": "morning_energy_consistently_low",
        "adjustment": "delay_start_time_adjust_light_exposure",
        "evaluation_period": "3_days"
      }
    ]
  }
}
```

## Implementation Architecture

### Integration into Current HolisticOS 6-Agent System

#### 1. Agent Positioning in Workflow

```
Current Flow:
User Request → API Gateway → On-Demand Analysis → Behavior Agent → Memory Agent → Plan Generation → Adaptation → Insights

Enhanced Flow:
User Request → API Gateway → On-Demand Analysis → Behavior Agent → **CIRCADIAN-ENERGY AGENT** → Memory Agent → Plan Generation (Enhanced) → Adaptation → Insights
```

#### 2. Agent Communication Patterns

```python
# Agent Input Sources
def get_agent_inputs(self, user_id: str, analysis_number: int) -> CircadianEnergyInput:
    return CircadianEnergyInput(
        user_profile=await self.get_user_profile(user_id),
        raw_biomarker_data=await self.user_data_service.get_user_health_data(user_id, analysis_number),
        behavior_analysis_context=await self.get_behavior_context(user_id, analysis_number)
    )

# Agent Output Distribution
def distribute_agent_outputs(self, analysis_result: CircadianEnergyOutput) -> None:
    # To Routine Agent
    await self.routine_agent.receive_circadian_timing(analysis_result.integration_recommendations.routine_agent_handoff)

    # To Behavior Agent (feedback loop)
    await self.behavior_agent.receive_habit_optimization(analysis_result.integration_recommendations.behavior_agent_feedback)

    # To Memory Agent (pattern storage)
    await self.memory_agent.store_circadian_patterns(analysis_result.circadian_analysis)

    # To Plan Generation (schedule optimization)
    await self.plan_generator.receive_energy_zones(analysis_result.energy_zone_analysis)
```

#### 3. Database Schema Extensions

```sql
-- New table for circadian analysis results
CREATE TABLE holistic_circadian_analysis (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    analysis_number INTEGER NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chronotype_assessment JSONB NOT NULL,
    energy_zone_analysis JSONB NOT NULL,
    schedule_recommendations JSONB NOT NULL,
    biomarker_summary JSONB NOT NULL,
    FOREIGN KEY (user_id, analysis_number) REFERENCES holistic_analysis_results(user_id, analysis_number)
);

-- Enhanced analysis results to include circadian data
ALTER TABLE holistic_analysis_results
ADD COLUMN circadian_energy_score INTEGER DEFAULT NULL,
ADD COLUMN optimal_schedule_generated BOOLEAN DEFAULT FALSE;
```

#### 4. Service Layer Integration

```python
# services/agents/circadian_energy/circadian_energy_agent.py
class CircadianEnergyAgent(BaseAgent):
    def __init__(self):
        super().__init__("circadian_energy")
        self.openai_client = OpenAI()
        self.model = "gpt-4-turbo"  # Recommended model for complex analysis

    async def analyze_circadian_energy_patterns(
        self,
        input_data: CircadianEnergyInput
    ) -> CircadianEnergyOutput:
        """
        Main analysis method that processes biomarker data and generates
        comprehensive circadian rhythm and energy zone recommendations
        """
        system_prompt = self._get_system_prompt()
        user_prompt = self._format_analysis_prompt(input_data)

        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent analysis
            max_tokens=4000
        )

        return self._parse_response(response.choices[0].message.content)
```

#### 5. Enhanced Orchestrator Integration

```python
# services/orchestrator/holistic_orchestrator.py - Enhanced workflow
async def run_enhanced_analysis_workflow(self, user_id: str, analysis_number: int):
    """Enhanced workflow with circadian-energy analysis"""

    # Step 1: Behavior Analysis (existing)
    behavior_result = await self.behavior_agent.analyze_behavior_patterns(user_id, analysis_number)

    # Step 2: NEW - Circadian-Energy Analysis
    circadian_input = CircadianEnergyInput(
        user_profile=await self.get_user_profile(user_id),
        raw_biomarker_data=await self.user_data_service.get_user_health_data(user_id, analysis_number),
        behavior_analysis_context=behavior_result.behavior_summary
    )
    circadian_result = await self.circadian_energy_agent.analyze_circadian_energy_patterns(circadian_input)

    # Step 3: Enhanced Plan Generation with Circadian Data
    plan_input = PlanGenerationInput(
        behavior_analysis=behavior_result,
        circadian_energy_analysis=circadian_result,  # NEW INPUT
        user_preferences=await self.get_user_preferences(user_id)
    )

    # Continue with memory, adaptation, insights...
```

## System Prompt Design

### Primary System Prompt

```
You are the Circadian-Energy Analysis Agent, a specialized component of the HolisticOS health optimization system. Your role is to analyze biomarker data and behavioral patterns to provide comprehensive circadian rhythm assessment and energy zone optimization recommendations.

## Core Responsibilities:

1. **Circadian Rhythm Analysis**: Evaluate sleep patterns, timing consistency, and chronotype alignment using biomarker data including sleep metrics, HRV, core temperature patterns, and activity rhythms.

2. **Energy Zone Mapping**: Create personalized daily energy profiles identifying peak, productive, maintenance, and recovery windows based on physiological markers and historical performance patterns.

3. **Schedule Optimization**: Generate specific timing recommendations for activities, meals, exercise, and sleep that align with the user's natural biological rhythms.

4. **Multi-Agent Integration**: Provide structured outputs that enhance routine generation, behavior modification, and adaptive learning across the HolisticOS ecosystem.

## Analysis Framework:

### Chronotype Assessment Protocol:
- Evaluate natural sleep-wake preferences using sleep timing data
- Assess morning/evening performance patterns from activity and cognitive metrics
- Analyze light sensitivity and melatonin production timing indicators
- Consider genetic predispositions and age-related chronotype shifts

### Energy Zone Classification:
- **Peak Zones**: Highest cognitive and physical performance capacity (typically 85-100% energy)
- **Productive Zones**: Sustained high performance for routine tasks (70-84% energy)
- **Maintenance Zones**: Moderate energy suitable for administrative/social tasks (50-69% energy)
- **Recovery Zones**: Low energy requiring rest and restoration focus (0-49% energy)

### Biomarker Integration Priority:
1. Sleep metrics (duration, efficiency, stages, timing)
2. Heart Rate Variability (HRV) patterns and recovery indicators
3. Activity patterns and strain/recovery balance
4. Core body temperature rhythms (if available)
5. Cortisol awakening response indicators
6. Subjective energy self-reports and mood patterns

## Output Requirements:

### Structure and Precision:
- Provide specific time windows (not vague recommendations)
- Include confidence scores for all predictions (0.0-1.0 scale)
- Support recommendations with biomarker evidence
- Quantify expected performance improvements
- Include adaptation rules for schedule refinement

### Integration Focus:
- Generate routine agent handoffs with precise exercise timing windows
- Provide behavior agent feedback for habit timing optimization
- Create memory agent inputs for pattern learning and trend analysis
- Support plan generation with energy-aligned activity scheduling

### Personalization Depth:
- Consider user archetype (Foundation Builder, Peak Performer, etc.) in recommendation style
- Adapt complexity and intensity based on user's optimization maturity
- Account for lifestyle constraints and preferences
- Provide both ideal and practical implementation options

## Analysis Standards:

- Base recommendations on minimum 7-14 days of biomarker data for pattern recognition
- Prioritize sleep quality and consistency as the foundation for all circadian optimization
- Consider individual variation - avoid rigid population-based assumptions
- Provide progressive implementation plans that prevent circadian disruption
- Include monitoring protocols for tracking optimization effectiveness

## Response Format:

Always structure responses as valid JSON matching the CircadianEnergyOutput specification. Include comprehensive rationale for timing recommendations, confidence assessments for all predictions, and specific integration instructions for downstream agents.

Focus on actionable, measurable improvements that align with the user's natural biological rhythms while supporting their health optimization goals within the HolisticOS framework.
```

## Model Recommendations

### Primary Model: GPT-4 Turbo
- **Reasoning**: Complex biomarker analysis and pattern recognition requires advanced reasoning capabilities
- **Token Efficiency**: 4000+ token outputs with structured JSON responses
- **Consistency**: Low temperature (0.1) for reliable analysis patterns
- **Cost Management**: Fits within existing $1-$10 daily cost protection limits

### Fallback Model: GPT-4
- **Use Case**: When GPT-4 Turbo unavailable or for cost optimization
- **Performance**: Slightly reduced pattern recognition but maintains core functionality

### Alternative Consideration: Claude-3-Opus
- **Potential Benefit**: Strong analytical reasoning for complex biomarker interpretation
- **Integration**: Would require API client modification
- **Cost**: Evaluate against OpenAI pricing for production deployment

## Implementation Timeline

### Phase 1: Core Agent Development (Week 1-2)
- Create `CircadianEnergyAgent` class with BaseAgent inheritance
- Implement input/output data models using Pydantic
- Develop system prompt and basic analysis logic
- Add database schema for circadian analysis storage

### Phase 2: Integration Testing (Week 3)
- Integrate agent into orchestrator workflow
- Test with real user biomarker data
- Validate output quality and consistency
- Implement enhanced MVP logging for agent handoffs

### Phase 3: Multi-Agent Enhancement (Week 4)
- Enhance routine agent to consume circadian timing data
- Update behavior agent with habit optimization feedback
- Modify plan generation to incorporate energy zones
- Test complete integrated workflow

### Phase 4: Production Optimization (Week 5-6)
- Implement rate limiting and cost controls
- Add monitoring and alerting for agent performance
- Optimize prompts based on real-world usage patterns
- Deploy to production with gradual user rollout

This design provides a comprehensive foundation for implementing sophisticated circadian rhythm and energy optimization into the existing HolisticOS architecture while maintaining system reliability and user personalization standards.