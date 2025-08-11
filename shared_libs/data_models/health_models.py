"""
Health Data Models for HolisticOS MVP - Real User Data Integration
CTO Design: Simple, Type-Safe, Easy to Debug, Scalable
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# Simple enums for better type safety - no over-engineering
class DataQualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good" 
    FAIR = "fair"
    POOR = "poor"

class ArchetypeType(str, Enum):
    FOUNDATION_BUILDER = "Foundation Builder"
    TRANSFORMATION_SEEKER = "Transformation Seeker"
    SYSTEMATIC_IMPROVER = "Systematic Improver"
    PEAK_PERFORMER = "Peak Performer"
    RESILIENCE_REBUILDER = "Resilience Rebuilder"
    CONNECTED_EXPLORER = "Connected Explorer"

# Core data models - simple and clean
class HealthScore(BaseModel):
    """Individual health score - clean and simple"""
    id: str
    profile_id: str
    type: str
    score: float = Field(..., ge=0, le=100)
    data: Dict[str, Any] = Field(default_factory=dict)
    score_date_time: Union[str, datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BiomarkerData(BaseModel):
    """Biomarker data - structured and validated"""
    id: str
    profile_id: str
    category: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    start_date_time: datetime
    end_date_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ArchetypeData(BaseModel):
    """User archetype data"""
    id: str
    profile_id: str
    name: str
    periodicity: str
    value: str
    data: Dict[str, Any] = Field(default_factory=dict)
    start_date_time: datetime
    end_date_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Aggregated data models for agents
class DataQuality(BaseModel):
    """Data quality metrics for troubleshooting"""
    scores_count: int = 0
    biomarkers_count: int = 0
    archetypes_count: int = 0
    date_coverage_days: int = 0
    has_recent_data: bool = False
    completeness_score: float = Field(0.0, ge=0.0, le=1.0)
    quality_level: DataQualityLevel = DataQualityLevel.POOR
    missing_data_types: List[str] = Field(default_factory=list)
    data_freshness_hours: Optional[float] = None
    
    @validator('quality_level', always=True)
    def determine_quality_level(cls, v, values):
        """Auto-calculate quality level based on completeness"""
        score = values.get('completeness_score', 0.0)
        if score >= 0.8:
            return DataQualityLevel.EXCELLENT
        elif score >= 0.6:
            return DataQualityLevel.GOOD
        elif score >= 0.3:
            return DataQualityLevel.FAIR
        else:
            return DataQualityLevel.POOR

class DateRange(BaseModel):
    """Simple date range model"""
    start_date: datetime
    end_date: datetime
    days: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserHealthContext(BaseModel):
    """
    Main user health context - designed for 6-agent architecture
    Simple, comprehensive, easy to debug
    """
    user_id: str
    scores: List[HealthScore] = Field(default_factory=list)
    biomarkers: List[BiomarkerData] = Field(default_factory=list)
    archetypes: List[ArchetypeData] = Field(default_factory=list)
    date_range: DateRange
    data_quality: DataQuality
    fetch_timestamp: datetime
    
    # Agent-specific data views (computed properties for efficiency)
    @property
    def behavior_data(self) -> Dict[str, Any]:
        """Data prepared for Behavior Analysis Agent"""
        return {
            'activity_scores': [s for s in self.scores if 'activity' in s.type.lower()],
            'sleep_scores': [s for s in self.scores if 'sleep' in s.type.lower()],
            'engagement_biomarkers': [b for b in self.biomarkers if 'engagement' in b.category.lower()],
            'recent_patterns': self._get_recent_activity_patterns(),
            'quality_metrics': {
                'data_completeness': self.data_quality.completeness_score,
                'has_sufficient_data': len(self.scores) >= 5
            }
        }
    
    @property
    def memory_data(self) -> Dict[str, Any]:
        """Data prepared for Memory Management Agent"""
        return {
            'historical_scores': self.scores,
            'preference_indicators': self._extract_preference_signals(),
            'behavior_consistency': self._calculate_consistency_metrics(),
            'archetype_evolution': self.archetypes,
            'memory_context': {
                'data_span_days': self.date_range.days,
                'reliability_score': self.data_quality.completeness_score
            }
        }
    
    @property
    def nutrition_data(self) -> Dict[str, Any]:
        """Data prepared for Nutrition Plan Agent"""
        return {
            'metabolic_scores': [s for s in self.scores if any(term in s.type.lower() for term in ['metabolic', 'energy', 'recovery'])],
            'nutrition_biomarkers': [b for b in self.biomarkers if 'nutrition' in b.category.lower() or 'metabolic' in b.category.lower()],
            'dietary_patterns': self._extract_dietary_signals(),
            'current_archetype': self._get_current_archetype(),
            'nutritional_needs_indicators': self._assess_nutritional_needs()
        }
    
    @property 
    def routine_data(self) -> Dict[str, Any]:
        """Data prepared for Routine Plan Agent"""
        return {
            'fitness_scores': [s for s in self.scores if any(term in s.type.lower() for term in ['fitness', 'activity', 'exercise'])],
            'recovery_biomarkers': [b for b in self.biomarkers if 'recovery' in b.category.lower()],
            'activity_capacity': self._assess_activity_capacity(),
            'routine_preferences': self._extract_routine_preferences(),
            'readiness_metrics': self._calculate_readiness_score()
        }
    
    @property
    def adaptation_data(self) -> Dict[str, Any]:
        """Data prepared for Adaptation Engine"""
        return {
            'response_patterns': self._analyze_response_patterns(),
            'adaptation_signals': self._identify_adaptation_needs(),
            'progress_indicators': self._track_progress_metrics(),
            'stress_resilience': self._assess_stress_patterns(),
            'change_readiness': self._evaluate_change_capacity()
        }
    
    @property
    def insights_data(self) -> Dict[str, Any]:
        """Data prepared for Insights & Recommendations Agent"""
        return {
            'trend_data': self._calculate_trends(),
            'correlation_opportunities': self._identify_correlations(),
            'anomaly_indicators': self._detect_anomalies(),
            'insight_triggers': self._find_insight_opportunities(),
            'recommendation_context': self._build_recommendation_context()
        }
    
    # Helper methods for computed properties - simple implementations
    def _get_recent_activity_patterns(self) -> Dict[str, Any]:
        """Extract recent activity patterns - simple heuristics"""
        if not self.scores:
            return {}
        
        recent_scores = sorted(self.scores, key=lambda x: x.created_at, reverse=True)[:7]
        avg_score = sum(s.score for s in recent_scores) / len(recent_scores) if recent_scores else 0
        
        return {
            'average_score': avg_score,
            'score_trend': 'improving' if len(recent_scores) > 1 and recent_scores[0].score > recent_scores[-1].score else 'stable',
            'consistency': len(recent_scores) / 7  # Simple consistency metric
        }
    
    def _extract_preference_signals(self) -> Dict[str, Any]:
        """Extract user preference signals from data"""
        return {
            'preferred_activity_times': self._analyze_activity_timing(),
            'intensity_preferences': self._analyze_intensity_patterns(),
            'consistency_patterns': self._analyze_consistency()
        }
    
    def _calculate_consistency_metrics(self) -> Dict[str, float]:
        """Calculate behavior consistency metrics"""
        if len(self.scores) < 3:
            return {'consistency_score': 0.0, 'reliability': 0.0}
        
        # Simple standard deviation-based consistency
        scores = [s.score for s in self.scores]
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        consistency = 1.0 - min(1.0, variance / 100)  # Normalize to 0-1
        
        return {
            'consistency_score': consistency,
            'reliability': min(1.0, len(self.scores) / 14)  # 14 days = fully reliable
        }
    
    def _extract_dietary_signals(self) -> Dict[str, Any]:
        """Extract dietary pattern signals"""
        return {
            'energy_patterns': [b for b in self.biomarkers if 'energy' in b.type.lower()],
            'recovery_indicators': [b for b in self.biomarkers if 'recovery' in b.type.lower()],
            'metabolic_health': self._assess_metabolic_health()
        }
    
    def _get_current_archetype(self) -> Optional[str]:
        """Get most recent archetype"""
        if not self.archetypes:
            return None
        return sorted(self.archetypes, key=lambda x: x.start_date_time, reverse=True)[0].name
    
    def _assess_nutritional_needs(self) -> Dict[str, Any]:
        """Assess nutritional needs from biomarkers"""
        return {
            'energy_needs': self._calculate_energy_needs(),
            'recovery_needs': self._calculate_recovery_needs(),
            'performance_goals': self._identify_performance_goals()
        }
    
    def _assess_activity_capacity(self) -> Dict[str, Any]:
        """Assess current activity capacity"""
        activity_scores = [s for s in self.scores if 'activity' in s.type.lower()]
        if not activity_scores:
            return {'capacity_level': 'unknown'}
        
        avg_activity = sum(s.score for s in activity_scores) / len(activity_scores)
        return {
            'capacity_level': 'high' if avg_activity > 75 else 'moderate' if avg_activity > 50 else 'low',
            'recent_activity': avg_activity,
            'trend': self._calculate_activity_trend()
        }
    
    def _extract_routine_preferences(self) -> Dict[str, Any]:
        """Extract routine preferences from data"""
        return {
            'activity_preferences': self._analyze_activity_types(),
            'timing_preferences': self._analyze_activity_timing(),
            'intensity_preferences': self._analyze_intensity_patterns()
        }
    
    def _calculate_readiness_score(self) -> float:
        """Calculate overall readiness score"""
        if not self.scores:
            return 0.0
        
        readiness_scores = [s for s in self.scores if 'readiness' in s.type.lower()]
        if readiness_scores:
            return sum(s.score for s in readiness_scores) / len(readiness_scores)
        
        # Fallback: use overall score average
        return sum(s.score for s in self.scores) / len(self.scores)
    
    # Simple implementations for other helper methods
    def _analyze_response_patterns(self) -> Dict[str, Any]:
        return {'patterns': 'placeholder'}
    
    def _identify_adaptation_needs(self) -> Dict[str, Any]:
        return {'needs': 'placeholder'}
    
    def _track_progress_metrics(self) -> Dict[str, Any]:
        return {'progress': 'placeholder'}
    
    def _assess_stress_patterns(self) -> Dict[str, Any]:
        return {'stress_level': 'unknown'}
    
    def _evaluate_change_capacity(self) -> Dict[str, Any]:
        return {'capacity': 'moderate'}
    
    def _calculate_trends(self) -> Dict[str, Any]:
        return {'trends': 'placeholder'}
    
    def _identify_correlations(self) -> Dict[str, Any]:
        return {'correlations': []}
    
    def _detect_anomalies(self) -> Dict[str, Any]:
        return {'anomalies': []}
    
    def _find_insight_opportunities(self) -> Dict[str, Any]:
        return {'opportunities': []}
    
    def _build_recommendation_context(self) -> Dict[str, Any]:
        return {'context': 'placeholder'}
    
    def _analyze_activity_timing(self) -> Dict[str, Any]:
        return {'preferred_times': []}
    
    def _analyze_intensity_patterns(self) -> Dict[str, Any]:
        return {'preferred_intensity': 'moderate'}
    
    def _analyze_consistency(self) -> Dict[str, Any]:
        return {'consistency_pattern': 'variable'}
    
    def _assess_metabolic_health(self) -> Dict[str, Any]:
        return {'metabolic_status': 'unknown'}
    
    def _calculate_energy_needs(self) -> str:
        return 'moderate'
    
    def _calculate_recovery_needs(self) -> str:
        return 'moderate'
    
    def _identify_performance_goals(self) -> List[str]:
        return []
    
    def _calculate_activity_trend(self) -> str:
        return 'stable'
    
    def _analyze_activity_types(self) -> Dict[str, Any]:
        return {'types': []}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Agent-specific input models for type safety
class AgentInputData(BaseModel):
    """Base class for agent input data"""
    user_id: str
    archetype: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)

class BehaviorAnalysisInput(AgentInputData):
    """Input model for Behavior Analysis Agent"""
    activity_data: Dict[str, Any] = Field(default_factory=dict)
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    behavior_context: Dict[str, Any] = Field(default_factory=dict)

class MemoryManagementInput(AgentInputData):
    """Input model for Memory Management Agent"""
    historical_data: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    memory_context: Dict[str, Any] = Field(default_factory=dict)

class NutritionPlanInput(AgentInputData):
    """Input model for Nutrition Plan Agent"""
    metabolic_data: Dict[str, Any] = Field(default_factory=dict)
    dietary_preferences: Dict[str, Any] = Field(default_factory=dict)
    nutrition_context: Dict[str, Any] = Field(default_factory=dict)

class RoutinePlanInput(AgentInputData):
    """Input model for Routine Plan Agent"""
    fitness_data: Dict[str, Any] = Field(default_factory=dict)
    activity_preferences: Dict[str, Any] = Field(default_factory=dict)
    routine_context: Dict[str, Any] = Field(default_factory=dict)

class AdaptationEngineInput(AgentInputData):
    """Input model for Adaptation Engine"""
    response_data: Dict[str, Any] = Field(default_factory=dict)
    adaptation_signals: Dict[str, Any] = Field(default_factory=dict)
    adaptation_context: Dict[str, Any] = Field(default_factory=dict)

class InsightsRecommendationsInput(AgentInputData):
    """Input model for Insights & Recommendations Agent"""
    analytics_data: Dict[str, Any] = Field(default_factory=dict)
    insight_triggers: Dict[str, Any] = Field(default_factory=dict)
    insights_context: Dict[str, Any] = Field(default_factory=dict)

# Utility functions for easy data conversion
def create_health_context_from_raw_data(
    user_id: str,
    raw_scores: List[Dict],
    raw_biomarkers: List[Dict],
    raw_archetypes: List[Dict],
    days: int = 7
) -> UserHealthContext:
    """Convert raw API/DB data to UserHealthContext - simple and reliable"""
    from datetime import datetime, timezone, timedelta
    
    # Convert raw data to models
    scores = []
    for item in raw_scores:
        try:
            scores.append(HealthScore(**item))
        except Exception as e:
            print(f"Warning: Skipping invalid score data: {e}")
    
    biomarkers = []
    for item in raw_biomarkers:
        try:
            biomarkers.append(BiomarkerData(**item))
        except Exception as e:
            print(f"Warning: Skipping invalid biomarker data: {e}")
    
    archetypes = []
    for item in raw_archetypes:
        try:
            archetypes.append(ArchetypeData(**item))
        except Exception as e:
            print(f"Warning: Skipping invalid archetype data: {e}")
    
    # Create date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    date_range = DateRange(start_date=start_date, end_date=end_date, days=days)
    
    # Calculate data quality
    total_records = len(scores) + len(biomarkers)
    completeness_score = min(1.0, total_records / 20)  # 20 records = complete
    
    data_quality = DataQuality(
        scores_count=len(scores),
        biomarkers_count=len(biomarkers),
        archetypes_count=len(archetypes),
        date_coverage_days=days,
        has_recent_data=total_records > 0,
        completeness_score=completeness_score
    )
    
    return UserHealthContext(
        user_id=user_id,
        scores=scores,
        biomarkers=biomarkers,
        archetypes=archetypes,
        date_range=date_range,
        data_quality=data_quality,
        fetch_timestamp=datetime.now(timezone.utc)
    )