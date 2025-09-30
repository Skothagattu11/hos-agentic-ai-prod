# AI Context Integration Service - Step by Step Example

## 📊 **Step 1: Data Collection**

When `AIContextIntegrationService.prepare_memory_enhanced_context(user_id="35pDPUIfAoRl2Y700bFkxPKYjjf2", archetype="systematic_improver")` is called:

### **1.1 AI Context Generation (Once)**
```python
# Calls: ai_context_service.generate_user_context(user_id, archetype, days=3)
# Input: Raw engagement data from LAST 3 DAYS ONLY
raw_engagement_data = {
    'calendar_selections': [
        {'title': 'Morning workout', 'time_block': '6:00-7:00 AM', 'selection_timestamp': '2024-01-15'},
        {'title': 'Review goals', 'time_block': '8:00-8:30 AM', 'selection_timestamp': '2024-01-14'},
        {'title': 'Afternoon meeting', 'time_block': '2:00-3:00 PM', 'selection_timestamp': '2024-01-13'},
        # Only 3 days of data
    ],
    'task_checkins': [
        {'title': 'Morning workout', 'completion_status': 'completed', 'satisfaction_rating': 4},
        {'title': 'Review goals', 'completion_status': 'completed', 'satisfaction_rating': 5},
        {'title': 'Afternoon meeting', 'completion_status': 'skipped', 'satisfaction_rating': None},
        # Only 3 days of data
    ],
    'daily_journals': [
        {'journal_date': '2024-01-15', 'energy_level': 4, 'mood': 'focused'},
        {'journal_date': '2024-01-14', 'energy_level': 3, 'mood': 'motivated'}
        # Only recent journals
    ]
}

# AI Analysis Result (based on 3 days):
ai_context_summary = """
ENGAGEMENT PATTERNS:
- User consistently completes morning workouts (2/2 attempts) with high satisfaction (avg 4.5/5)
- Prefers early morning time blocks (6-8 AM selections: 2 items)
- Shows systematic approach with goal review sessions
- Completion rate higher for morning activities (100%) vs afternoon tasks (0%)

TIMING PREFERENCES:
- Most successful between 6-9 AM (completion rate: 100% in last 3 days)
- Afternoon productivity dips (2-4 PM completion: 0%)
- Recent pattern shows consistent morning energy

OPTIMIZATION OPPORTUNITIES:
- Schedule demanding tasks in proven 6-9 AM window
- Add structure to afternoon tasks to improve completion
- Build on established morning routine success
"""

# Stored in holistic_memory_analysis_context table:
stored_context = {
    'user_id': '35pDPUIfAoRl2Y700bFkxPKYjjf2',
    'context_summary': ai_context_summary,  # The AI analysis above
    'source_data': {
        'calendar_count': 3,
        'checkin_count': 3,
        'journal_count': 2,
        'data_period': {'days_analyzed': 3, 'start_date': '2024-01-13', 'end_date': '2024-01-15'}
    },
    'archetype': 'systematic_improver',
    'data_period_days': 3,
    'generation_method': 'ai_raw_data'
}
```

### **1.2 Historical Analysis Collection**

```python
# For Behavior Agent - Get last 2 behavior analyses
behavior_analysis_history = [
    {
        'id': 'analysis_123',
        'analysis_type': 'behavior_analysis',
        'archetype': 'systematic_improver',
        'created_at': '2024-01-10',
        'analysis_result': {
            'behavioral_signature': 'Goal-oriented with morning energy peak',
            'recommendations': [
                'Schedule high-priority tasks between 6-9 AM',
                'Use afternoon for routine/administrative tasks',
                'Implement evening wind-down routine'
            ],
            'readiness_level': 7
        }
    },
    {
        'id': 'analysis_456',
        'analysis_type': 'behavior_analysis',
        'archetype': 'systematic_improver',
        'created_at': '2024-01-05',
        'analysis_result': {
            'behavioral_signature': 'Consistent morning performer',
            'recommendations': [
                'Maintain morning workout routine',
                'Add afternoon energy management strategies'
            ],
            'readiness_level': 6
        }
    }
]

# For Circadian Agent - Get last 2 circadian analyses
circadian_analysis_history = [
    {
        'id': 'analysis_789',
        'analysis_type': 'circadian_analysis',
        'archetype': 'systematic_improver',
        'created_at': '2024-01-10',
        'analysis_result': {
            'chronotype_assessment': {
                'primary_type': 'early_bird',
                'confidence_score': 0.85
            },
            'energy_zone_analysis': {
                'peak_windows': ['6:00-9:00 AM'],
                'productive_windows': ['9:00-11:00 AM', '2:00-4:00 PM'],
                'rest_windows': ['1:00-2:00 PM', '8:00-10:00 PM']
            }
        }
    },
    {
        'id': 'analysis_101',
        'analysis_type': 'circadian_analysis',
        'archetype': 'systematic_improver',
        'created_at': '2024-01-05',
        'analysis_result': {
            'chronotype_assessment': {
                'primary_type': 'early_bird',
                'confidence_score': 0.78
            },
            'energy_zone_analysis': {
                'peak_windows': ['6:30-9:30 AM'],
                'productive_windows': ['9:30-11:30 AM']
            }
        }
    }
]
```

# No separate engagement insights - all info is in AI context summary above

## 🧠 **Step 2: What Behavior Agent Receives**

```python
# When BehaviorAnalysisService.analyze(enhanced_context) is called:
enhanced_context_for_behavior = {
    # SAME RAW HEALTH DATA (unchanged)
    'user_context': {
        'sahha_scores': [...],      # Raw health data
        'sahha_biomarkers': [...],  # Raw biomarkers
        'user_id': '35pDPUIfAoRl2Y700bFkxPKYjjf2'
    },

    # SAME ARCHETYPE (unchanged)
    'archetype': 'systematic_improver',

    # NEW: AI CONTEXT + BEHAVIOR-SPECIFIC HISTORY
    'memory_context': {
        # AI Context Summary (engagement analysis from last 3 days)
        'ai_context_summary': """
        ENGAGEMENT PATTERNS:
        - User consistently completes morning workouts (2/2 attempts) with high satisfaction (avg 4.5/5)
        - Prefers early morning time blocks (6-8 AM selections: 2 items)
        - Shows systematic approach with goal review sessions
        - Completion rate higher for morning activities (100%) vs afternoon tasks (0%)

        TIMING PREFERENCES:
        - Most successful between 6-9 AM (completion rate: 100% in last 3 days)
        - Afternoon productivity dips (2-4 PM completion: 0%)
        - Recent pattern shows consistent morning energy

        OPTIMIZATION OPPORTUNITIES:
        - Schedule demanding tasks in proven 6-9 AM window
        - Add structure to afternoon tasks to improve completion
        - Build on established morning routine success
        """,

        # BEHAVIOR-SPECIFIC: Last 2 behavior analyses (from holistic_analysis_results)
        'agent_specific_history': [
            {
                'analysis_date': '2024-01-10',
                'behavioral_signature': 'Goal-oriented with morning energy peak',
                'recommendations': [
                    'Schedule high-priority tasks between 6-9 AM',
                    'Use afternoon for routine/administrative tasks',
                    'Implement evening wind-down routine'
                ],
                'readiness_level': 7
            },
            {
                'analysis_date': '2024-01-05',
                'behavioral_signature': 'Consistent morning performer',
                'recommendations': [
                    'Maintain morning workout routine',
                    'Add afternoon energy management strategies'
                ],
                'readiness_level': 6
            }
        ]

        # REMOVED: engagement_insights (info is in AI context)
        # REMOVED: proven_strategies (agents extract from context + history)
    }
}
```

## 🕐 **Step 3: What Circadian Agent Receives**

```python
# When CircadianAnalysisService.analyze(enhanced_context) is called:
enhanced_context_for_circadian = {
    # SAME RAW HEALTH DATA (unchanged)
    'user_context': {
        'sahha_scores': [...],      # Raw health data
        'sahha_biomarkers': [...],  # Raw biomarkers
        'user_id': '35pDPUIfAoRl2Y700bFkxPKYjjf2'
    },

    # SAME ARCHETYPE (unchanged)
    'archetype': 'systematic_improver',

    # NEW: AI CONTEXT + CIRCADIAN-SPECIFIC HISTORY
    'memory_context': {
        # SAME AI Context Summary (timing focus from last 3 days)
        'ai_context_summary': """
        TIMING PREFERENCES:
        - Most successful between 6-9 AM (completion rate: 100% in last 3 days)
        - Afternoon productivity dips (2-4 PM completion: 0%)
        - Recent pattern shows consistent morning energy

        ENGAGEMENT PATTERNS:
        - Prefers early morning time blocks (6-8 AM selections: 2 items)
        - Shows systematic approach with goal review sessions
        - Completion rate higher for morning activities (100%) vs afternoon tasks (0%)

        OPTIMIZATION OPPORTUNITIES:
        - Schedule demanding tasks in proven 6-9 AM window
        - Add structure to afternoon tasks to improve completion
        - Build on established morning routine success
        """,

        # CIRCADIAN-SPECIFIC: Last 2 circadian analyses (from holistic_analysis_results)
        'agent_specific_history': [
            {
                'analysis_date': '2024-01-10',
                'chronotype_assessment': {
                    'primary_type': 'early_bird',
                    'confidence_score': 0.85
                },
                'energy_zone_analysis': {
                    'peak_windows': ['6:00-9:00 AM'],
                    'productive_windows': ['9:00-11:00 AM', '2:00-4:00 PM'],
                    'rest_windows': ['1:00-2:00 PM', '8:00-10:00 PM']
                }
            },
            {
                'analysis_date': '2024-01-05',
                'chronotype_assessment': {
                    'primary_type': 'early_bird',
                    'confidence_score': 0.78
                },
                'energy_zone_analysis': {
                    'peak_windows': ['6:30-9:30 AM'],
                    'productive_windows': ['9:30-11:30 AM']
                }
            }
        ]

        # REMOVED: engagement_insights (info is in AI context)
        # REMOVED: proven_strategies (agents extract from context + history)
    }
}
```

## 🔄 **Step 4: How This Replaces Memory System**

### **OLD Memory System (Complex)**
```python
# MemoryIntegrationService.prepare_memory_enhanced_context()
old_enhanced_context = {
    'memory_context': {
        'longterm_memory': {
            'behavioral_patterns': {...},    # Complex 4-layer system
            'health_goals': {...},
            'preference_patterns': {...}
        },
        'recent_patterns': [...],            # Short-term memory
        'meta_memory': {...},               # Meta-learning
        'analysis_history': [...]           # Mixed history
    }
}
```

### **NEW AI Context System (Simple & Powerful)**
```python
# AIContextIntegrationService.prepare_memory_enhanced_context()
new_enhanced_context = {
    'memory_context': {
        'ai_context_summary': "Rich AI analysis...",     # Replaces 4-layer memory
        'agent_specific_history': [...],                # Targeted historical context
        'engagement_insights': {...},                   # Raw engagement metrics
        'proven_strategies': {...}                      # Extracted patterns
    }
}
```

## 🎯 **Key Benefits**

1. **Single Context Generation**: AI context created once (3-day analysis), used by both agents
2. **Agent-Specific History**: Each agent gets relevant past analyses from holistic_analysis_results
3. **Recent Engagement Focus**: 3-day analysis provides timely, relevant insights
4. **Clean Data Separation**: AI context stored in holistic_memory_analysis_context, history from existing tables
5. **No Redundant Data**: Removed engagement_insights and proven_strategies - agents extract what they need

## 📊 **Data Storage Summary**

### **holistic_memory_analysis_context table stores:**
```python
{
    'context_summary': "AI analysis of 3-day engagement patterns...",
    'source_data': {'calendar_count': 3, 'checkin_count': 3, 'data_period': {...}},
    'data_period_days': 3,
    'generation_method': 'ai_raw_data'
}
```

### **holistic_analysis_results table provides:**
```python
# Historical behavior and circadian analyses (last 2 each)
# Used by agents for pattern recognition and consistency
```

## 📈 **Expected Agent Outputs (Enhanced)**

### **Behavior Agent Output (With 3-day Context)**
```python
behavior_result = {
    'behavioral_signature': 'Systematic early-bird with recent morning success patterns',
    'recommendations': [
        'Continue leveraging your proven 6-9 AM peak window for high-priority tasks',
        'Build on your successful morning workout routine (100% completion rate in last 3 days)',
        'Address afternoon productivity gap - no completed tasks in 2-4 PM window recently'
    ],
    'readiness_level': 8,  # Higher due to consistent recent patterns
    'personalization_notes': 'Based on 3-day engagement analysis showing 100% morning completion vs 0% afternoon'
}
```

### **Circadian Agent Output (With 3-day Context)**
```python
circadian_result = {
    'chronotype_assessment': {
        'primary_type': 'early_bird',
        'confidence_score': 0.95  # Very high confidence due to recent consistent pattern
    },
    'energy_zone_analysis': {
        'peak_windows': ['6:00-9:00 AM'],     # Confirmed by 100% recent completion
        'productive_windows': ['9:00-11:00 AM'],  # From historical analysis
        'optimization_windows': ['2:00-4:00 PM']  # Based on recent 0% completion
    },
    'timing_recommendations': [
        'Schedule workouts at 6:00 AM (100% completion rate in last 3 days)',
        'Use 9-11 AM for complex cognitive tasks (historical strength)',
        'Implement structured approach for 2-4 PM slot (recent 0% completion needs intervention)'
    ]
}
```

This shows how **3-day AI context** provides **timely insights** while **historical analyses** provide **pattern consistency**, leading to **highly accurate and personalized recommendations**!