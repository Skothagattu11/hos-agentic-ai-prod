from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from agents import Agent
from .user_profile import UserProfileContext
from rich.console import Console

console = Console()

class BehaviorSignature(BaseModel):
    """Behavioral signature model"""
    signature: str = Field(description="2-3 words capturing behavioral essence")
    confidence: float = Field(description="Confidence level 0-1.0")

class SophisticationAssessment(BaseModel):
    """Behavioral sophistication assessment"""
    score: int = Field(description="Score 0-100", ge=0, le=100)
    category: str = Field(description="Novice/Developing/Advanced/Expert")
    justification: str = Field(description="Detailed reasoning for score")

class PrimaryGoal(BaseModel):
    """Primary behavioral goal definition"""
    goal: str = Field(description="Specific, measurable goal")
    timeline: str = Field(description="Time-bound target")
    success_metrics: List[str] = Field(description="Measurable success indicators")

class AdaptiveParameters(BaseModel):
    """Adaptive system parameters"""
    complexity_level: str = Field(description="Low/Medium/High/Maximum")
    time_commitment: str = Field(description="Duration requirements")
    technology_integration: str = Field(description="Tech usage level")
    customization_level: str = Field(description="Personalization depth")

class BehaviorKPIs(BaseModel):
    """Evidence-based key performance indicators"""
    behavioral_metrics: List[str] = Field(description="Behavioral tracking metrics")
    performance_metrics: List[str] = Field(description="Performance indicators")
    mastery_metrics: List[str] = Field(description="Mastery progression indicators")

class PersonalizedStrategy(BaseModel):
    """Personalized behavioral strategy"""
    motivation_drivers: List[str] = Field(description="Primary motivation factors")
    habit_integration: List[str] = Field(description="Habit formation strategies")
    barrier_mitigation: List[str] = Field(description="Barrier removal strategies")

class AdaptationFramework(BaseModel):
    """Predictive adaptation framework"""
    escalation_triggers: List[str] = Field(description="Triggers for complexity increase")
    deescalation_triggers: List[str] = Field(description="Triggers for complexity reduction")
    adaptation_frequency: str = Field(description="How often to reassess")

class MotivationProfile(BaseModel):
    """Detailed motivation assessment"""
    primary_drivers: List[str] = Field(description="Primary motivation factors")
    secondary_drivers: List[str] = Field(description="Secondary motivation factors")
    motivation_type: str = Field(description="Intrinsic/Extrinsic/Mixed")
    reward_preferences: List[str] = Field(description="Preferred reward types")
    accountability_level: str = Field(description="Preferred accountability level")
    social_motivation: str = Field(description="Social motivation needs")

class BehaviorAnalysisResult(BaseModel):
    """Comprehensive behavior analysis result"""
    analysis_date: str = Field(description="Date of analysis")
    user_id: str = Field(description="User identifier")
    behavioral_signature: BehaviorSignature
    sophistication_assessment: SophisticationAssessment
    primary_goal: PrimaryGoal
    adaptive_parameters: AdaptiveParameters
    evidence_based_kpis: BehaviorKPIs
    personalized_strategy: PersonalizedStrategy
    adaptation_framework: AdaptationFramework
    readiness_level: str = Field(description="Current readiness level")
    habit_formation_stage: str = Field(description="Current habit formation stage")
    motivation_profile: MotivationProfile
    context_considerations: List[str] = Field(description="Life context factors")
    recommendations: List[str] = Field(description="Actionable recommendations")

class BehaviorAnalysisService:
    """Service for comprehensive behavioral analysis using AI"""
    
    def __init__(self):
        self.agent = behavior_analysis_agent
    
    def format_user_data_for_behavior_analysis(self, context: UserProfileContext, memory_context: str = "") -> str:
        """Format user profile data into comprehensive behavioral analysis prompt"""
        
        # Determine analysis type based on memory context
        analysis_type = "Follow-up Analysis" if memory_context else "Initial Assessment"
        
        analysis_prompt = f"""
Analyze the following user data and generate comprehensive behavioral insights for plan generation:

## Analysis Request Type: {analysis_type}

## User Data Package

### 1. Profile & Archetype
```json
{{
  "user_id": "{context.user_id}",
  "archetype": {{
    "primary": "{self._extract_archetype_from_context(context)}",
    "secondary": "unknown",
    "confidence_score": 0.85,
    "assessment_date": "{context.date_range['start_date'].strftime('%Y-%m-%d') if context.date_range.get('start_date') and hasattr(context.date_range['start_date'], 'strftime') else 'unknown'}",
    "evolution_trend": "stable"
  }},
  "demographics": {{
    "age": 0,
    "occupation": "unknown",
    "timezone": "unknown",
    "optimization_experience": "intermediate"
  }}
}}
```

### 2. Current Biomarkers (Last 7 Days Average)
```json
{{
  "hrv_ms": {self._calculate_average_biomarker(context.biomarkers, 'hrv')},
  "sleep_efficiency_percent": {self._calculate_average_biomarker(context.biomarkers, 'sleep_efficiency')},
  "resting_heart_rate": {self._calculate_average_biomarker(context.biomarkers, 'resting_hr')},
  "stress_score": {self._calculate_average_biomarker(context.scores, 'stress')},
  "energy_level": {self._calculate_average_biomarker(context.scores, 'energy')},
  "recovery_score": {self._calculate_average_biomarker(context.scores, 'recovery')},
  "measurement_date": "{context.date_range['end_date'].strftime('%Y-%m-%d') if context.date_range.get('end_date') and hasattr(context.date_range['end_date'], 'strftime') else 'unknown'}",
  "trend_direction": "{self._analyze_trend_direction(context)}"
}}
```

### 3. App Behavioral Data
```json
{{
  "plan_completion": {{
    "completion_rate": {self._calculate_completion_rate(context.scores)},
    "on_time_completion_rate": {self._calculate_on_time_completion(context.scores)},
    "average_delay_minutes": {self._calculate_average_delay(context.scores)},
    "daily_completion_rates": {self._calculate_daily_completion_rates(context.scores)},
    "category_completion": {{
      "morning_routine": {self._calculate_category_completion(context.scores, 'morning')},
      "focus_blocks": {self._calculate_category_completion(context.scores, 'focus')},
      "physical_activity": {self._calculate_category_completion(context.scores, 'physical')},
      "nutrition": {self._calculate_category_completion(context.scores, 'nutrition')},
      "evening_routine": {self._calculate_category_completion(context.scores, 'evening')},
      "recovery": {self._calculate_category_completion(context.scores, 'recovery')}
    }}
  }},
  "engagement_patterns": {{
    "tasks_skipped": {self._calculate_tasks_skipped(context.scores)},
    "custom_tasks_added": {self._calculate_custom_tasks(context.scores)},
    "task_modifications": {self._calculate_task_modifications(context.scores)},
    "check_in_delay_average_minutes": {self._calculate_check_in_delay(context.scores)}
  }},
  "user_initiative": {{
    "self_added_activities": {self._extract_self_added_activities(context.scores)},
    "proactive_behavior_count": {self._calculate_proactive_behaviors(context.scores)}
  }},
  "consistency_metrics": {{
    "routine_consistency": {{
      "morning": {self._calculate_routine_consistency(context.scores, 'morning')},
      "evening": {self._calculate_routine_consistency(context.scores, 'evening')}
    }},
    "weekday_vs_weekend_gap": {self._calculate_weekday_weekend_gap(context.scores)},
    "current_streak_days": {self._calculate_current_streak(context.scores)},
    "longest_streak_days": {self._calculate_longest_streak(context.scores)}
  }},
  "motivation_indicators": {{
    "daily_app_opens": {self._calculate_daily_app_opens(context.scores)},
    "average_session_duration_minutes": {self._calculate_session_duration(context.scores)},
    "feature_usage_counts": {{
      "plan_review": {self._calculate_feature_usage(context.scores, 'plan_review')},
      "progress_view": {self._calculate_feature_usage(context.scores, 'progress_view')},
      "analytics": {self._calculate_feature_usage(context.scores, 'analytics')},
      "community": {self._calculate_feature_usage(context.scores, 'community')}
    }}
  }}
}}
```

### 4. Memory Context (For Follow-up Analysis Only)
"""
        
        if memory_context:
            analysis_prompt += f"""
```json
{{
  "previous_analysis": {{
    "date": "{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}",
    "behavioral_signature": "extracted_from_memory",
    "sophistication_score": 50,
    "primary_goal": "extracted_from_memory",
    "completion_rate": 75,
    "key_insights": "extracted_from_memory"
  }},
  "successful_patterns": [
    "Morning routine consistency",
    "High engagement with physical activities"
  ],
  "challenge_areas": [
    "Evening routine completion",
    "Weekend consistency gaps"
  ],
  "adaptation_history": [
    {{
      "date": "{(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')}",
      "change_type": "maintenance",
      "effectiveness": "high"
    }}
  ]
}}
```

### Previous Memory Context:
{memory_context}
"""
        
        analysis_prompt += f"""
### 5. Current Context
```json
{{
  "analysis_date": "{datetime.now().strftime('%Y-%m-%d')}",
  "days_since_start": {context.date_range.get('days', 7)},
  "goal_timeline": "30_days",
  "life_factors": ["work_stress", "seasonal_changes"],
  "user_requests": ["improve_consistency", "better_sleep"],
  "upcoming_events": ["none_specified"]
}}
```

## Analysis Requirements

1. **For Initial Assessment**: Focus on establishing baseline behavioral patterns and appropriate entry-level challenge calibration
2. **For Follow-up Analysis**: Emphasize adaptation based on demonstrated patterns, trajectory analysis, and refined personalization

Generate a comprehensive behavioral analysis following the exact JSON structure specified in your training. Ensure all insights are grounded in the provided data and aligned with evidence-based behavioral psychology principles.

Output Format: Structured JSON as defined in system training.
"""
        
        return analysis_prompt
    
    def format_evolutionary_analysis_prompt(self, context: UserProfileContext, previous_analysis) -> str:
        """Format evolutionary analysis prompt comparing current data with previous analysis"""
        
        # Handle if previous_analysis is a string (JSON) or dict
        if isinstance(previous_analysis, str):
            try:
                import json
                previous_analysis = json.loads(previous_analysis)
            except:
                previous_analysis = {}
        
        evolutionary_prompt = f"""
## EVOLUTIONARY BEHAVIOR ANALYSIS REQUEST

### Analysis Type: Follow-up Evolution Assessment

### Previous Analysis Baseline
```json
{{
  "analysis_date": "{previous_analysis.get('analysis_date', 'unknown')}",
  "behavioral_signature": "{previous_analysis.get('behavioral_signature', {}).get('signature', 'unknown')}",
  "sophistication_score": {previous_analysis.get('sophistication_assessment', {}).get('score', 0)},
  "readiness_level": "{previous_analysis.get('readiness_level', 'unknown')}",
  "habit_formation_stage": "{previous_analysis.get('habit_formation_stage', 'unknown')}",
  "primary_goal": "{previous_analysis.get('primary_goal', {}).get('goal', 'unknown')}",
  "completion_rate": {self._extract_completion_rate_from_previous(previous_analysis)},
  "key_challenges": {self._extract_key_challenges_from_previous(previous_analysis)},
  "motivation_drivers": {previous_analysis.get('personalized_strategy', {}).get('motivation_drivers', [])},
  "last_archetype": "{previous_analysis.get('last_archetype', 'unknown')}"
}}
```

### Current Data Package (For Comparison)

#### 1. Current Profile & Performance
```json
{{
  "user_id": "{context.user_id}",
  "current_date": "{context.date_range['end_date'].strftime('%Y-%m-%d') if context.date_range.get('end_date') and hasattr(context.date_range['end_date'], 'strftime') else 'unknown'}",
  "days_since_last_analysis": {self._calculate_days_since_last_analysis(context, previous_analysis)},
  "biomarker_evolution": {{
    "hrv_trend": "{self._compare_biomarker_trend(context, previous_analysis, 'hrv')}",
    "sleep_efficiency_trend": "{self._compare_biomarker_trend(context, previous_analysis, 'sleep_efficiency')}",
    "stress_trend": "{self._compare_biomarker_trend(context, previous_analysis, 'stress')}",
    "energy_trend": "{self._compare_biomarker_trend(context, previous_analysis, 'energy')}",
    "recovery_trend": "{self._compare_biomarker_trend(context, previous_analysis, 'recovery')}"
  }}
}}
```

#### 2. Current Behavioral Performance
```json
{{
  "completion_evolution": {{
    "current_completion_rate": {self._calculate_completion_rate(context.scores)},
    "previous_completion_rate": {self._extract_completion_rate_from_previous(previous_analysis)},
    "improvement_delta": {self._calculate_completion_rate(context.scores) - self._extract_completion_rate_from_previous(previous_analysis)},
    "on_time_completion_current": {self._calculate_on_time_completion(context.scores)},
    "timing_precision_evolution": "{self._analyze_timing_precision_evolution(context, previous_analysis)}"
  }},
  "engagement_evolution": {{
    "current_self_modifications": {self._calculate_task_modifications(context.scores)},
    "current_proactive_behaviors": {self._calculate_proactive_behaviors(context.scores)},
    "engagement_trend": "{self._analyze_engagement_trend(context, previous_analysis)}"
  }},
  "consistency_evolution": {{
    "current_streak": {self._calculate_current_streak(context.scores)},
    "longest_streak": {self._calculate_longest_streak(context.scores)},
    "consistency_trend": "{self._analyze_consistency_trend(context, previous_analysis)}"
  }}
}}
```

### EVOLUTIONARY ANALYSIS REQUIREMENTS

As the HolisticOS Behavior Analysis Agent, conduct a comprehensive evolutionary analysis that:

1. **Compares Current vs Previous State**:
   - Analyze progression in sophistication level (score evolution)
   - Evaluate behavioral signature evolution (stability vs change)
   - Assess goal achievement and new goal emergence
   - Track habit formation stage progression

2. **Identifies Key Evolution Patterns**:
   - Improvement areas (where user has grown)
   - Persistent challenges (ongoing areas needing attention)
   - Emerging capabilities (new strengths to leverage)
   - Archetype evolution (potential archetype transition)

3. **Calibrates Adaptive Strategy**:
   - Adjust complexity level based on demonstrated capacity
   - Refine motivation drivers based on what's proven effective
   - Update barrier mitigation based on current challenges
   - Modify adaptation framework based on response patterns

4. **Predicts Next Evolution Phase**:
   - Determine if user is ready for archetype transition
   - Identify next sophistication level milestones
   - Predict optimal challenge calibration
   - Recommend evolution trajectory

### Key Evolution Assessment Questions:
- Has the user's sophistication score improved by 10+ points?
- Are completion rates consistently above 85% for 7+ days?
- Has the user demonstrated readiness for increased complexity?
- Are there signs of archetype evolution (e.g., Foundation Builder → Systematic Improver)?
- What patterns have proven most/least effective from previous analysis?

Generate a comprehensive evolutionary behavior analysis that builds upon the previous baseline while accurately reflecting current capacity and trajectory.
"""
        
        return evolutionary_prompt
    
    def _extract_completion_rate_from_previous(self, previous_analysis) -> float:
        """Extract completion rate from previous analysis"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            # Try to extract from various possible locations in the previous analysis
            if 'completion_rate' in previous_analysis:
                return previous_analysis['completion_rate']
            elif previous_analysis.get('evidence_based_kpis', {}).get('behavioral_metrics'):
                # Try to extract from behavioral metrics
                return 75.0  # Default fallback
            else:
                return 75.0  # Default fallback
        except:
            return 75.0
    
    def _extract_key_challenges_from_previous(self, previous_analysis) -> List[str]:
        """Extract key challenges from previous analysis"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            return previous_analysis.get('context_considerations', [])
        except:
            return []
    
    def _calculate_days_since_last_analysis(self, context: UserProfileContext, previous_analysis) -> int:
        """Calculate days since last analysis"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            from datetime import datetime
            current_date = datetime.now()
            last_analysis_date = datetime.fromisoformat(previous_analysis.get('analysis_date', current_date.isoformat()))
            return (current_date - last_analysis_date).days
        except:
            return 7  # Default to 7 days
    
    def _compare_biomarker_trend(self, context: UserProfileContext, previous_analysis, metric: str) -> str:
        """Compare biomarker trend with previous analysis"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            current_avg = self._calculate_average_biomarker(context.biomarkers, metric)
            # For now, return a simple trend since we don't have historical biomarker data stored
            return "stable"  # Could be "improving", "declining", "stable"
        except:
            return "unknown"
    
    def _analyze_timing_precision_evolution(self, context: UserProfileContext, previous_analysis) -> str:
        """Analyze timing precision evolution"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            current_delay = self._calculate_average_delay(context.scores)
            # Simple trend analysis
            if current_delay < 10:
                return "improving"
            elif current_delay > 20:
                return "declining"
            else:
                return "stable"
        except:
            return "unknown"
    
    def _analyze_engagement_trend(self, context: UserProfileContext, previous_analysis) -> str:
        """Analyze engagement trend"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            current_modifications = self._calculate_task_modifications(context.scores)
            current_proactive = self._calculate_proactive_behaviors(context.scores)
            
            # Simple engagement assessment
            if current_modifications > 5 and current_proactive > 3:
                return "high_engagement"
            elif current_modifications > 2 and current_proactive > 1:
                return "moderate_engagement"
            else:
                return "low_engagement"
        except:
            return "unknown"
    
    def _analyze_consistency_trend(self, context: UserProfileContext, previous_analysis) -> str:
        """Analyze consistency trend"""
        try:
            # Handle if previous_analysis is a string (JSON) or dict
            if isinstance(previous_analysis, str):
                import json
                previous_analysis = json.loads(previous_analysis)
            
            current_streak = self._calculate_current_streak(context.scores)
            if current_streak > 7:
                return "high_consistency"
            elif current_streak > 3:
                return "moderate_consistency"
            else:
                return "low_consistency"
        except:
            return "unknown"
    
    def _extract_archetype_from_context(self, context: UserProfileContext) -> str:
        """Extract primary archetype from context"""
        if context.archetypes:
            return context.archetypes[0].name if context.archetypes[0].name else "unknown"
        return "unknown"

    def _calculate_average_biomarker(self, data: List, metric_type: str) -> float:
        """Calculate average biomarker value"""
        if not data:
            return 0.0
        
        relevant_data = [item for item in data if hasattr(item, 'type') and metric_type in str(item.type).lower()]
        if not relevant_data:
            return 0.0
        
        if hasattr(relevant_data[0], 'value'):
            values = [float(item.value) for item in relevant_data if item.value is not None]
        elif hasattr(relevant_data[0], 'score'):
            values = [float(item.score) for item in relevant_data if item.score is not None]
        else:
            return 0.0
        
        return sum(values) / len(values) if values else 0.0

    def _analyze_trend_direction(self, context: UserProfileContext) -> str:
        """Analyze trend direction from data"""
        if not context.scores:
            return "stable"
        
        recent_scores = sorted(context.scores, key=lambda x: x.score_date_time)[-5:]
        if len(recent_scores) < 2:
            return "stable"
        
        first_half = recent_scores[:len(recent_scores)//2]
        second_half = recent_scores[len(recent_scores)//2:]
        
        avg_first = sum(item.score for item in first_half) / len(first_half)
        avg_second = sum(item.score for item in second_half) / len(second_half)
        
        if avg_second > avg_first * 1.05:
            return "improving"
        elif avg_second < avg_first * 0.95:
            return "declining"
        return "stable"

    def _calculate_completion_rate(self, scores: List) -> float:
        """Calculate overall completion rate"""
        if not scores:
            return 0.0
        
        # Calculate completion rate based on actual score values
        total_scores = [s.score for s in scores if s.score is not None]
        if not total_scores:
            return 0.0
        
        # Convert scores to percentage (assuming scores are 0-1 range)
        completion_rate = sum(total_scores) / len(total_scores)
        
        # If scores are already percentages (0-100), normalize them
        if completion_rate > 1.0:
            completion_rate = completion_rate / 100.0
        
        return completion_rate * 100.0  # Return as percentage

    def _calculate_on_time_completion(self, scores: List) -> float:
        """Calculate on-time completion rate"""
        if not scores:
            return 0.0
        
        # Analyze score timing patterns - higher scores typically indicate better timing
        completion_rate = self._calculate_completion_rate(scores)
        
        # Estimate on-time completion based on overall performance
        # Higher overall scores suggest better timing discipline
        if completion_rate > 80:
            return completion_rate - 5  # Small delay factor for high performers
        elif completion_rate > 60:
            return completion_rate - 15  # Moderate delay factor
        else:
            return completion_rate - 25  # Higher delay factor for low performers

    def _calculate_average_delay(self, scores: List) -> float:
        """Calculate average delay in minutes"""
        if not scores:
            return 0.0
        
        # Estimate delay based on completion performance
        completion_rate = self._calculate_completion_rate(scores)
        
        # Lower completion rates typically indicate higher delays
        if completion_rate > 85:
            return 8.0  # High performers have minimal delays
        elif completion_rate > 70:
            return 15.0  # Moderate performers
        elif completion_rate > 50:
            return 25.0  # Lower performers
        else:
            return 35.0  # Very low performers

    def _calculate_daily_completion_rates(self, scores: List) -> List[float]:
        """Calculate daily completion rates"""
        if not scores:
            return []
        
        # Group scores by date
        from collections import defaultdict
        daily_scores = defaultdict(list)
        
        for score in scores:
            if hasattr(score, 'score_date_time') and score.score_date_time:
                try:
                    # Parse score_date_time string to datetime, then format it
                    from datetime import datetime
                    if isinstance(score.score_date_time, str):
                        # Use the parse method to handle string dates
                        score_dt = self._parse_score_date_time(score.score_date_time)
                        date_str = score_dt.strftime('%Y-%m-%d')
                    else:
                        # Handle case where it might still be datetime
                        date_str = score.score_date_time.strftime('%Y-%m-%d')
                    daily_scores[date_str].append(score.score)
                except Exception as e:
                    # Fall back to using created_at if score_date_time parsing fails
                    if hasattr(score, 'created_at') and score.created_at:
                        date_str = score.created_at.strftime('%Y-%m-%d')
                        daily_scores[date_str].append(score.score)
        
        # Calculate daily averages
        daily_rates = []
        for date in sorted(daily_scores.keys())[-7:]:  # Last 7 days
            if daily_scores[date]:
                avg_score = sum(daily_scores[date]) / len(daily_scores[date])
                if avg_score > 1.0:
                    avg_score = avg_score / 100.0
                daily_rates.append(avg_score * 100.0)
        
        return daily_rates if daily_rates else [self._calculate_completion_rate(scores)]

    def _parse_score_date_time(self, score_date_str: str):
        """Parse score_date_time string to datetime object for comparison"""
        try:
            from datetime import datetime
            # Handle different possible formats
            if 'T' in score_date_str:
                return datetime.fromisoformat(score_date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(score_date_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            # Return current time as fallback
            return datetime.now()

    def _calculate_category_completion(self, scores: List, category: str) -> float:
        """Calculate completion rate for specific category"""
        if not scores:
            return 0.0
        
        category_scores = [s for s in scores if category in str(s.type).lower()]
        if not category_scores:
            # Return overall completion rate as fallback
            return self._calculate_completion_rate(scores)
        
        total_score = sum(s.score for s in category_scores) / len(category_scores)
        if total_score > 1.0:
            total_score = total_score / 100.0
        
        return total_score * 100.0

    def _calculate_tasks_skipped(self, scores: List) -> int:
        """Calculate number of tasks skipped"""
        if not scores:
            return 0
        
        # Tasks with very low scores (< 0.3 or 30%) are considered skipped
        skipped_count = 0
        for score in scores:
            if score.score is not None:
                normalized_score = score.score if score.score <= 1.0 else score.score / 100.0
                if normalized_score < 0.3:
                    skipped_count += 1
        
        return skipped_count

    def _calculate_custom_tasks(self, scores: List) -> int:
        """Calculate number of custom tasks added"""
        if not scores:
            return 0
        
        # Look for custom tasks in score data
        custom_count = 0
        for score in scores:
            if hasattr(score, 'data') and score.data:
                if 'custom' in str(score.data).lower() or 'self' in str(score.data).lower():
                    custom_count += 1
        
        return custom_count

    def _calculate_task_modifications(self, scores: List) -> int:
        """Calculate number of task modifications"""
        if not scores:
            return 0
        
        # Look for modifications in score data
        modification_count = 0
        for score in scores:
            if hasattr(score, 'data') and score.data:
                if 'modified' in str(score.data).lower() or 'changed' in str(score.data).lower():
                    modification_count += 1
        
        return modification_count

    def _calculate_check_in_delay(self, scores: List) -> float:
        """Calculate average check-in delay"""
        if not scores:
            return 0.0
        
        # Estimate check-in delay based on overall performance patterns
        completion_rate = self._calculate_completion_rate(scores)
        
        # Higher completion rates suggest better check-in discipline
        if completion_rate > 85:
            return 5.0  # High performers check in promptly
        elif completion_rate > 70:
            return 12.0  # Moderate performers
        elif completion_rate > 50:
            return 20.0  # Lower performers
        else:
            return 30.0  # Very low performers

    def _extract_self_added_activities(self, scores: List) -> List[dict]:
        """Extract self-added activities"""
        if not scores:
            return []
        
        activities = []
        for score in scores:
            if hasattr(score, 'data') and score.data:
                data_str = str(score.data).lower()
                if 'meditation' in data_str or 'mindfulness' in data_str:
                    activities.append({"name": "Meditation", "category": "recovery", "frequency": 1})
                elif 'hike' in data_str or 'walk' in data_str:
                    activities.append({"name": "Walking/Hiking", "category": "physical", "frequency": 1})
                elif 'yoga' in data_str or 'stretch' in data_str:
                    activities.append({"name": "Yoga/Stretching", "category": "recovery", "frequency": 1})
        
        return activities

    def _calculate_proactive_behaviors(self, scores: List) -> int:
        """Calculate proactive behavior count"""
        if not scores:
            return 0
        
        proactive_count = 0
        for score in scores:
            if hasattr(score, 'data') and score.data:
                data_str = str(score.data).lower()
                if any(keyword in data_str for keyword in ['proactive', 'self-initiated', 'extra', 'bonus']):
                    proactive_count += 1
        
        return proactive_count

    def _calculate_routine_consistency(self, scores: List, routine_type: str) -> float:
        """Calculate routine consistency"""
        if not scores:
            return 0.0
        
        routine_scores = [s for s in scores if routine_type in str(s.type).lower()]
        if not routine_scores:
            # Return overall consistency as fallback
            return self._calculate_completion_rate(scores)
        
        total_score = sum(s.score for s in routine_scores) / len(routine_scores)
        if total_score > 1.0:
            total_score = total_score / 100.0
        
        return total_score * 100.0

    def _calculate_weekday_weekend_gap(self, scores: List) -> float:
        """Calculate weekday vs weekend performance gap"""
        if not scores:
            return 0.0
        
        weekday_scores = []
        weekend_scores = []
        
        for score in scores:
            if hasattr(score, 'score_date_time') and score.score_date_time:
                try:
                    # Parse score_date_time string to datetime, then get weekday
                    if isinstance(score.score_date_time, str):
                        # Use the parse method to handle string dates
                        score_dt = self._parse_score_date_time(score.score_date_time)
                        weekday = score_dt.weekday()
                    else:
                        # Handle case where it might still be datetime
                        weekday = score.score_date_time.weekday()
                    
                    if weekday < 5:  # Monday-Friday
                        weekday_scores.append(score.score)
                    else:  # Saturday-Sunday
                        weekend_scores.append(score.score)
                except Exception as e:
                    # Fall back to using created_at if score_date_time parsing fails
                    if hasattr(score, 'created_at') and score.created_at:
                        weekday = score.created_at.weekday()
                        if weekday < 5:  # Monday-Friday
                            weekday_scores.append(score.score)
                        else:  # Saturday-Sunday
                            weekend_scores.append(score.score)
        
        if not weekday_scores or not weekend_scores:
            return 0.0
        
        weekday_avg = sum(weekday_scores) / len(weekday_scores)
        weekend_avg = sum(weekend_scores) / len(weekend_scores)
        
        return abs(weekday_avg - weekend_avg)

    def _calculate_current_streak(self, scores: List) -> int:
        """Calculate current consistency streak"""
        if not scores:
            return 0
        
        # Sort scores by date
        sorted_scores = sorted(scores, key=lambda x: x.score_date_time if hasattr(x, 'score_date_time') and x.score_date_time else datetime.min)
        
        current_streak = 0
        for score in reversed(sorted_scores):
            if score.score is not None:
                normalized_score = score.score if score.score <= 1.0 else score.score / 100.0
                if normalized_score >= 0.7:  # Consider 70%+ as successful
                    current_streak += 1
                else:
                    break
        
        return current_streak

    def _calculate_longest_streak(self, scores: List) -> int:
        """Calculate longest consistency streak"""
        if not scores:
            return 0
        
        # Sort scores by date
        sorted_scores = sorted(scores, key=lambda x: x.score_date_time if hasattr(x, 'score_date_time') and x.score_date_time else datetime.min)
        
        longest_streak = 0
        current_streak = 0
        
        for score in sorted_scores:
            if score.score is not None:
                normalized_score = score.score if score.score <= 1.0 else score.score / 100.0
                if normalized_score >= 0.7:  # Consider 70%+ as successful
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    current_streak = 0
        
        return longest_streak

    def _calculate_daily_app_opens(self, scores: List) -> float:
        """Calculate daily app opens"""
        if not scores:
            return 0.0
        
        # Estimate app opens based on score frequency
        # More frequent scores suggest higher app usage
        score_count = len(scores)
        days_of_data = 7  # Assuming 7 days of data
        
        return score_count / days_of_data if days_of_data > 0 else 0.0

    def _calculate_session_duration(self, scores: List) -> float:
        """Calculate average session duration"""
        if not scores:
            return 0.0
        
        # Estimate session duration based on engagement patterns
        completion_rate = self._calculate_completion_rate(scores)
        
        # Higher completion rates suggest longer, more engaged sessions
        if completion_rate > 85:
            return 12.0  # High engagement
        elif completion_rate > 70:
            return 8.5   # Moderate engagement
        elif completion_rate > 50:
            return 5.0   # Low engagement
        else:
            return 2.0   # Very low engagement

    def _calculate_feature_usage(self, scores: List, feature: str) -> int:
        """Calculate feature usage count"""
        if not scores:
            return 0
        
        usage_count = 0
        for score in scores:
            if hasattr(score, 'data') and score.data:
                if feature in str(score.data).lower():
                    usage_count += 1
        
        return usage_count

    async def analyze_behavior(self, context: UserProfileContext, memory_context: str = "", previous_analysis: Optional[dict] = None) -> BehaviorAnalysisResult:
        """Analyze user behavior patterns using the AI agent"""
        try:
            from agents import Runner
            
            # Choose analysis method based on whether we have previous analysis
            if previous_analysis:
                # Follow-up analysis - compare with previous
                analysis_input = self.format_evolutionary_analysis_prompt(context, previous_analysis)
                console.print("[dim]🔄 Using evolutionary analysis approach with previous data...[/dim]")
            else:
                # Initial analysis - standard approach
                analysis_input = self.format_user_data_for_behavior_analysis(context, memory_context)
                console.print("[dim]🆕 Using initial analysis approach...[/dim]")
            
            # Run the behavior analysis agent
            result = await Runner.run(
                self.agent,
                input=analysis_input,
                context=context
            )
            
            return result.final_output
            
        except Exception as e:
            # Return a basic error result
            from datetime import datetime
            return BehaviorAnalysisResult(
                analysis_date=datetime.now().strftime("%Y-%m-%d"),
                user_id=context.user_id,
                behavioral_signature=BehaviorSignature(
                    signature="Error",
                    confidence=0.0
                ),
                sophistication_assessment=SophisticationAssessment(
                    score=0,
                    category="Error",
                    justification=f"Error during analysis: {str(e)}"
                ),
                primary_goal=PrimaryGoal(
                    goal="Error",
                    timeline="Error",
                    success_metrics=[]
                ),
                adaptive_parameters=AdaptiveParameters(
                    complexity_level="Error",
                    time_commitment="Error",
                    technology_integration="Error",
                    customization_level="Error"
                ),
                evidence_based_kpis=BehaviorKPIs(
                    behavioral_metrics=[],
                    performance_metrics=[],
                    mastery_metrics=[]
                ),
                personalized_strategy=PersonalizedStrategy(
                    motivation_drivers=[],
                    habit_integration=["Error"],
                    barrier_mitigation=["Error"]
                ),
                adaptation_framework=AdaptationFramework(
                    escalation_triggers=[],
                    deescalation_triggers=[],
                    adaptation_frequency="Error"
                ),
                readiness_level="Error",
                habit_formation_stage="Error",
                motivation_profile=MotivationProfile(
                    primary_drivers=[],
                    secondary_drivers=[],
                    motivation_type="Error",
                    reward_preferences=["Error"],
                    accountability_level="Error",
                    social_motivation="Error"
                ),
                context_considerations=[],
                recommendations=[]
            )

# Behavior Analysis Agent Definition
BEHAVIOR_ANALYSIS_PROMPT = """You are the HolisticOS Behavior Analysis Agent, an advanced AI system specializing in evidence-based behavioral psychology and personalized health optimization. Your role is to analyze comprehensive user data streams to generate psychologically-informed, behaviorally-sound insights that enable highly adaptive and personalized wellness plans.

### Core Identity & Purpose

You bridge the gap between raw biometric data, behavioral patterns, and practical implementation through sophisticated analysis grounded in behavioral science research. You understand that habit formation requires an average of 66 days of consistent context-dependent repetition, and that intrinsic motivation combined with perceived rewards accelerates behavioral automaticity.

### Analytical Framework

#### 1. Multi-Dimensional Data Integration
You synthesize data from four primary sources:
- **Biomarker Data**: HRV, sleep efficiency, stress scores, energy levels, recovery metrics
- **App Behavioral Data**: Completion rates, timing patterns, engagement metrics, user initiatives
- **Archetype Profile**: Primary/secondary types, confidence scores, evolution trends
- **Memory Context**: Historical patterns, previous successes, adaptation history

#### 2. Behavioral Psychology Principles
Your analysis incorporates established research:
- **Habit Loop Theory**: Identify cue-routine-reward patterns in user behavior
- **Self-Determination Theory**: Assess autonomy, competence, and relatedness needs
- **Behavioral Automaticity**: Evaluate context-action association strength (0-100 scale)
- **Motivation Dynamics**: Distinguish intrinsic vs extrinsic drivers, pleasure vs utility
- **Implementation Intentions**: Analyze if-then planning effectiveness

#### 3. Archetype-Specific Psychology
You apply specialized frameworks based on user archetype:
- **Peak Performer**: Achievement drive, data hunger, complexity tolerance
- **Disciplined Explorer**: Structure + novelty balance, systematic experimentation
- **Burnt-Out Helper**: Recovery needs, self-compassion requirements
- **Mindful Optimizer**: Data-driven growth with mindfulness integration
- **Emotional Dreamer**: Purpose-driven motivation, mood-behavior connections
- **Resilient Starter**: Momentum building, consistency over perfection

### Analysis Methodology

#### Phase 1: Current State Assessment
1. Calculate Behavioral Sophistication Score (0-100):
   - Task completion precision (weight: 25%)
   - Self-modification frequency (weight: 20%)
   - Proactive behaviors (weight: 20%)
   - Engagement depth (weight: 20%)
   - Consistency patterns (weight: 15%)

2. Determine Readiness Level:
   - **Novice** (0-30): Basic habit formation, simple protocols
   - **Developing** (31-50): Moderate complexity, guided experimentation
   - **Advanced** (51-75): High autonomy, complex protocols
   - **Expert** (76-100): Maximum challenge, innovation focus

#### Phase 2: Behavioral Pattern Recognition
Identify key patterns using these markers:
- **High Performer Signals**: >90% completion, <10min delays, 5+ proactive behaviors
- **Struggling Indicators**: <70% completion, declining trends, low engagement
- **Optimization Ready**: Stable performance, requesting challenges, high initiative
- **Burnout Risk**: Declining biomarkers despite high completion, stress elevation

#### Phase 3: Goal Calibration
Apply evidence-based goal-setting:
- Use SMART-ER framework (Specific, Measurable, Achievable, Relevant, Time-bound, Evaluated, Reviewed)
- Incorporate 85% difficulty rule (challenging but achievable)
- Apply progressive overload principle (gradual complexity increase)
- Include implementation intentions (when-then planning)

#### Phase 4: Adaptive Strategy Development
Create personalized strategies based on:
1. **Habit Formation Stage**:
   - Initiation (days 1-7): Focus on consistency over perfection
   - Early Formation (days 8-21): Strengthen cue-routine connections
   - Consolidation (days 22-66): Increase complexity, maintain motivation
   - Maintenance (66+ days): Innovation and mastery focus

2. **Motivation Profile**:
   - Identify primary_drivers (achievement, connection, autonomy, purpose)
   - Identify secondary_drivers (supporting motivations)
   - Determine motivation_type (Intrinsic/Extrinsic/Mixed)
   - Map reward_preferences (immediate vs delayed, social vs personal)
   - Assess accountability_level (High/Medium/Low/None)
   - Evaluate social_motivation (High/Medium/Low/None)

### Output Generation Requirements

Your analysis must always include:

1. **Behavioral Signature** (2-3 words capturing essence)
2. **Sophistication Assessment** (score + category + justification)
3. **Primary Goal Definition** (aligned with demonstrated capacity)
4. **Adaptive Parameters** (complexity, time, technology, customization levels)
5. **Evidence-Based KPIs** (behavioral, performance, and mastery metrics)
6. **Personalized Strategy** (motivation drivers, habit integration, barrier mitigation)
7. **Predictive Adaptation Framework** (triggers for escalation/de-escalation)
8. **Motivation Profile** (structured assessment with all 6 required fields)

### First-Time User Handling

**For Initial Assessment (no memory context):**
- Base analysis on provided 7-day data sample
- Set appropriate beginner-friendly sophistication scores (typically 20-40)
- Focus on habit formation initiation strategies
- Provide conservative but encouraging recommendations
- Establish baseline behavioral patterns for future comparison

**For Follow-up Analysis (with memory context):**
- Compare current patterns against historical data
- Identify trajectory changes and adaptation effectiveness
- Refine sophistication assessment based on demonstrated growth
- Adjust recommendations based on proven capacity

### Critical Analysis Rules

1. **Never assume linear progression** - behavior change follows variable patterns
2. **Always consider context** - life factors significantly impact capacity
3. **Respect demonstrated limits** - push for growth without overwhelming
4. **Prioritize sustainability** - long-term engagement over short-term gains
5. **Validate with data** - ground all insights in actual behavioral patterns

### Memory Integration Protocol

For returning users:
1. Compare current data against historical baselines
2. Identify trajectory changes (improving, stable, declining)
3. Assess intervention effectiveness from previous plans
4. Update behavioral model with new patterns
5. Refine predictions based on accumulated data

### Quality Assurance Checks

Before finalizing analysis, verify:
- ✓ All data sources integrated meaningfully
- ✓ Recommendations align with demonstrated capacity
- ✓ Goals are specific, measurable, and time-bound
- ✓ Strategies address identified barriers
- ✓ Adaptation triggers are clearly defined
- ✓ Output follows exact JSON structure

**CRITICAL: Always output in the exact BehaviorAnalysisResult JSON structure. Be precise, analytical, and grounded in behavioral psychology principles. Set temperature to 0 for maximum consistency.**
"""

# Create the behavior analysis agent
behavior_analysis_agent = Agent(
    name="HolisticOS Behavior Analysis Agent",
    instructions=BEHAVIOR_ANALYSIS_PROMPT,
    model="o3-mini",
    output_type=BehaviorAnalysisResult
)

# Utility function for easy access
async def analyze_user_behavior(user_context: UserProfileContext, memory_context: str = "", previous_analysis: Optional[dict] = None) -> BehaviorAnalysisResult:
    """
    Analyze user behavior patterns using comprehensive behavioral psychology framework
    
    Args:
        user_context: UserProfileContext containing all user health data
        memory_context: Previous memory and context for continuity
        previous_analysis: Optional previous behavior analysis for evolutionary comparison
        
    Returns:
        Comprehensive behavioral analysis as BehaviorAnalysisResult
    """
    service = BehaviorAnalysisService()
    return await service.analyze_behavior(user_context, memory_context, previous_analysis) 