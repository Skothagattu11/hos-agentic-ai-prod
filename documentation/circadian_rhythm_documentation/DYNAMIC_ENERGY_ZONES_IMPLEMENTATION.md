# Dynamic Energy Zones Mapping Implementation Plan

## Overview

Dynamic Energy Zones Mapping is a system that learns each user's individual energy patterns throughout the day and dynamically schedules activities during their optimal energy windows. This goes beyond static time blocks to create truly personalized, energy-aware scheduling.

## What Are Dynamic Energy Zones?

### Energy Zone Definition
An energy zone is a time period when a user consistently experiences a particular energy level, mapped across multiple dimensions:

- **Cognitive Energy**: Mental clarity, focus capability, decision-making capacity
- **Physical Energy**: Movement capacity, strength, endurance
- **Emotional Energy**: Motivation, enthusiasm, social capacity
- **Creative Energy**: Innovation, problem-solving, artistic expression

### Zone Types
1. **Peak Zones**: Highest energy and capacity (15-25% of day)
2. **Productive Zones**: Good sustained energy (40-50% of day)
3. **Maintenance Zones**: Moderate energy, routine tasks (20-25% of day)
4. **Recovery Zones**: Low energy, rest and restoration (10-15% of day)

## Implementation Architecture

### Phase 1: Energy Data Collection System (Weeks 1-2)

#### 1.1 Multi-Source Energy Tracking

**New Service: `services/energy_tracking_service.py`**

```python
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time, timedelta
from pydantic import BaseModel
import numpy as np

class EnergyReading(BaseModel):
    user_id: str
    timestamp: datetime
    cognitive_energy: float  # 0-10 scale
    physical_energy: float   # 0-10 scale
    emotional_energy: float  # 0-10 scale
    creative_energy: float   # 0-10 scale
    overall_energy: float    # 0-10 scale
    source: str  # "manual", "wearable", "behavioral", "predicted"
    confidence: float  # 0-1 scale
    context: Dict[str, Any]  # sleep, meal timing, activities, etc.

class EnergyPattern(BaseModel):
    user_id: str
    day_of_week: int  # 0-6
    time_slot: str    # "07:00-07:30"
    energy_type: str  # "cognitive", "physical", "emotional", "creative"
    average_energy: float
    std_deviation: float
    sample_count: int
    confidence_score: float
    last_updated: datetime

class EnergyTrackingService:
    """Collect and analyze user energy patterns from multiple sources"""

    def __init__(self):
        self.energy_sources = {
            "manual": self._process_manual_input,
            "wearable": self._process_wearable_data,
            "behavioral": self._process_behavioral_signals,
            "task_completion": self._process_task_performance,
            "sleep": self._process_sleep_data
        }

    async def collect_energy_reading(
        self,
        user_id: str,
        source: str,
        raw_data: Dict[str, Any]
    ) -> EnergyReading:
        """Process raw data into standardized energy reading"""

        processor = self.energy_sources.get(source)
        if not processor:
            raise ValueError(f"Unknown energy source: {source}")

        return await processor(user_id, raw_data)

    async def _process_manual_input(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> EnergyReading:
        """Process user's manual energy self-assessment"""
        return EnergyReading(
            user_id=user_id,
            timestamp=datetime.now(),
            cognitive_energy=data.get('cognitive', 5.0),
            physical_energy=data.get('physical', 5.0),
            emotional_energy=data.get('emotional', 5.0),
            creative_energy=data.get('creative', 5.0),
            overall_energy=data.get('overall', 5.0),
            source="manual",
            confidence=0.9,  # High confidence in self-assessment
            context=data.get('context', {})
        )

    async def _process_wearable_data(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> EnergyReading:
        """Convert wearable metrics to energy estimation"""

        # Extract key metrics
        hrv = data.get('hrv_score', 50)
        heart_rate = data.get('heart_rate', 70)
        sleep_score = data.get('sleep_score', 0.7)
        activity_level = data.get('activity_level', 0.5)

        # Convert to energy estimates using validated algorithms
        physical_energy = self._calculate_physical_energy(
            hrv, heart_rate, sleep_score, activity_level
        )
        cognitive_energy = self._calculate_cognitive_energy(
            hrv, sleep_score, data.get('stress_level', 0.5)
        )

        return EnergyReading(
            user_id=user_id,
            timestamp=datetime.now(),
            cognitive_energy=cognitive_energy,
            physical_energy=physical_energy,
            emotional_energy=(cognitive_energy + physical_energy) / 2,
            creative_energy=cognitive_energy * 0.8,  # Cognitive-dependent
            overall_energy=(physical_energy + cognitive_energy) / 2,
            source="wearable",
            confidence=0.7,  # Good confidence in wearable data
            context=data
        )

    async def _process_behavioral_signals(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> EnergyReading:
        """Infer energy from behavioral patterns"""

        # Analyze task completion patterns
        completion_rate = data.get('task_completion_rate', 0.5)
        completion_speed = data.get('average_completion_time', 1.0)
        task_difficulty = data.get('average_task_difficulty', 5.0)

        # Infer energy from behavior
        cognitive_energy = min(10, completion_rate * 10 + (1/completion_speed) * 2)
        physical_energy = data.get('movement_frequency', 5.0)

        return EnergyReading(
            user_id=user_id,
            timestamp=datetime.now(),
            cognitive_energy=cognitive_energy,
            physical_energy=physical_energy,
            emotional_energy=completion_rate * 8,  # Emotional state affects completion
            creative_energy=cognitive_energy * 0.9,
            overall_energy=(cognitive_energy + physical_energy + completion_rate * 8) / 3,
            source="behavioral",
            confidence=0.6,  # Moderate confidence in behavioral inference
            context=data
        )

    def _calculate_physical_energy(
        self,
        hrv: float,
        heart_rate: int,
        sleep_score: float,
        activity_level: float
    ) -> float:
        """Calculate physical energy from physiological markers"""

        # Normalize HRV (assume baseline around 50)
        hrv_score = min(10, (hrv / 50) * 7)

        # Heart rate efficiency (lower resting HR = better)
        hr_score = max(0, 10 - (heart_rate - 60) / 10)

        # Sleep impact
        sleep_impact = sleep_score * 10

        # Recent activity impact
        activity_impact = min(10, activity_level * 8)

        # Weighted combination
        physical_energy = (
            hrv_score * 0.3 +
            hr_score * 0.2 +
            sleep_impact * 0.4 +
            activity_impact * 0.1
        )

        return max(0, min(10, physical_energy))

    def _calculate_cognitive_energy(
        self,
        hrv: float,
        sleep_score: float,
        stress_level: float
    ) -> float:
        """Calculate cognitive energy from relevant markers"""

        # HRV strongly correlates with cognitive capacity
        hrv_impact = min(10, (hrv / 50) * 8)

        # Sleep quality is crucial for cognitive function
        sleep_impact = sleep_score * 10

        # Stress negatively impacts cognition
        stress_impact = (1 - stress_level) * 6

        cognitive_energy = (
            hrv_impact * 0.4 +
            sleep_impact * 0.5 +
            stress_impact * 0.1
        )

        return max(0, min(10, cognitive_energy))
```

#### 1.2 Energy Data Collection Infrastructure

```sql
-- Real-time energy readings
CREATE TABLE energy_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    cognitive_energy FLOAT CHECK (cognitive_energy BETWEEN 0 AND 10),
    physical_energy FLOAT CHECK (physical_energy BETWEEN 0 AND 10),
    emotional_energy FLOAT CHECK (emotional_energy BETWEEN 0 AND 10),
    creative_energy FLOAT CHECK (creative_energy BETWEEN 0 AND 10),
    overall_energy FLOAT CHECK (overall_energy BETWEEN 0 AND 10),
    source VARCHAR(50) NOT NULL,
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Energy patterns analysis
CREATE TABLE energy_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    time_slot VARCHAR(20) NOT NULL, -- "07:00-07:30"
    energy_type VARCHAR(20) NOT NULL,
    average_energy FLOAT,
    std_deviation FLOAT,
    sample_count INTEGER,
    confidence_score FLOAT,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, day_of_week, time_slot, energy_type)
);

-- Energy zone definitions
CREATE TABLE user_energy_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(20) NOT NULL, -- "peak", "productive", "maintenance", "recovery"
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week INTEGER[] NOT NULL, -- [1,2,3,4,5] for weekdays
    energy_characteristics JSONB,
    confidence_score FLOAT,
    last_calculated TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);
```

### Phase 2: Energy Pattern Analysis Engine (Weeks 3-4)

#### 2.1 Pattern Recognition and Zone Identification

**New Service: `services/energy_pattern_analysis_service.py`**

```python
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple

class EnergyZone(BaseModel):
    zone_id: str
    zone_name: str
    zone_type: str  # "peak", "productive", "maintenance", "recovery"
    start_time: time
    end_time: time
    days_of_week: List[int]
    energy_characteristics: Dict[str, float]
    confidence_score: float
    activities_suited: List[str]
    activities_avoided: List[str]

class EnergyPatternAnalysisService:
    """Analyze energy readings to identify consistent patterns and zones"""

    def __init__(self):
        self.min_samples_for_pattern = 14  # 2 weeks minimum
        self.zone_stability_threshold = 0.7  # 70% consistency required

    async def analyze_user_energy_patterns(
        self,
        user_id: str,
        analysis_period_days: int = 30
    ) -> Dict[str, List[EnergyZone]]:
        """Analyze user's energy patterns and identify optimal zones"""

        # Get energy data for analysis period
        energy_data = await self._get_energy_data(user_id, analysis_period_days)

        if len(energy_data) < self.min_samples_for_pattern:
            return {"message": "Insufficient data for pattern analysis"}

        # Analyze patterns by day type (weekday vs weekend)
        weekday_zones = await self._identify_energy_zones(
            energy_data, user_id, day_type="weekday"
        )
        weekend_zones = await self._identify_energy_zones(
            energy_data, user_id, day_type="weekend"
        )

        return {
            "weekday_zones": weekday_zones,
            "weekend_zones": weekend_zones,
            "overall_patterns": await self._generate_pattern_summary(energy_data)
        }

    async def _identify_energy_zones(
        self,
        energy_data: List[EnergyReading],
        user_id: str,
        day_type: str
    ) -> List[EnergyZone]:
        """Use clustering to identify consistent energy zones"""

        # Filter data by day type
        if day_type == "weekday":
            filtered_data = [r for r in energy_data if r.timestamp.weekday() < 5]
        else:
            filtered_data = [r for r in energy_data if r.timestamp.weekday() >= 5]

        # Create time-energy matrix
        time_energy_matrix = self._create_time_energy_matrix(filtered_data)

        # Apply clustering to identify zones
        zones = self._cluster_energy_zones(time_energy_matrix, user_id, day_type)

        # Validate and rank zones by confidence
        validated_zones = await self._validate_energy_zones(zones, filtered_data)

        return sorted(validated_zones, key=lambda z: z.confidence_score, reverse=True)

    def _create_time_energy_matrix(
        self,
        energy_data: List[EnergyReading]
    ) -> np.ndarray:
        """Create matrix of time slots vs energy levels for clustering"""

        # Create 30-minute time slots for the day (48 slots)
        time_slots = [(i * 30) for i in range(48)]  # Minutes since midnight

        # Initialize matrix: [time_slot, cognitive, physical, emotional, creative]
        matrix = []

        for time_slot in time_slots:
            slot_start = time_slot
            slot_end = time_slot + 30

            # Find energy readings in this time slot
            slot_readings = []
            for reading in energy_data:
                minutes_since_midnight = reading.timestamp.hour * 60 + reading.timestamp.minute
                if slot_start <= minutes_since_midnight < slot_end:
                    slot_readings.append(reading)

            if slot_readings:
                # Average energy levels for this time slot
                avg_cognitive = np.mean([r.cognitive_energy for r in slot_readings])
                avg_physical = np.mean([r.physical_energy for r in slot_readings])
                avg_emotional = np.mean([r.emotional_energy for r in slot_readings])
                avg_creative = np.mean([r.creative_energy for r in slot_readings])

                matrix.append([
                    time_slot, avg_cognitive, avg_physical, avg_emotional, avg_creative
                ])

        return np.array(matrix)

    def _cluster_energy_zones(
        self,
        time_energy_matrix: np.ndarray,
        user_id: str,
        day_type: str
    ) -> List[EnergyZone]:
        """Use DBSCAN clustering to identify energy zones"""

        if len(time_energy_matrix) < 5:  # Need minimum data points
            return []

        # Prepare data for clustering (exclude time column for clustering)
        energy_features = time_energy_matrix[:, 1:]  # cognitive, physical, emotional, creative

        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(energy_features)

        # Apply DBSCAN clustering
        clustering = DBSCAN(eps=0.5, min_samples=3).fit(scaled_features)
        labels = clustering.labels_

        # Convert clusters to energy zones
        zones = []
        unique_labels = set(labels)

        for label in unique_labels:
            if label == -1:  # Noise points, skip
                continue

            # Get time slots and energy characteristics for this cluster
            cluster_indices = np.where(labels == label)[0]
            cluster_times = time_energy_matrix[cluster_indices, 0]  # Time slots
            cluster_energies = time_energy_matrix[cluster_indices, 1:]  # Energy values

            # Calculate zone characteristics
            avg_energies = np.mean(cluster_energies, axis=0)
            zone_type = self._classify_zone_type(avg_energies)

            # Determine time range
            start_time_minutes = int(np.min(cluster_times))
            end_time_minutes = int(np.max(cluster_times)) + 30

            zone = EnergyZone(
                zone_id=f"{user_id}_{day_type}_{zone_type}_{label}",
                zone_name=f"{zone_type.title()} Zone",
                zone_type=zone_type,
                start_time=time(start_time_minutes // 60, start_time_minutes % 60),
                end_time=time(end_time_minutes // 60, end_time_minutes % 60),
                days_of_week=list(range(5)) if day_type == "weekday" else [5, 6],
                energy_characteristics={
                    "cognitive": float(avg_energies[0]),
                    "physical": float(avg_energies[1]),
                    "emotional": float(avg_energies[2]),
                    "creative": float(avg_energies[3])
                },
                confidence_score=len(cluster_indices) / len(time_energy_matrix),
                activities_suited=self._get_suited_activities(zone_type, avg_energies),
                activities_avoided=self._get_avoided_activities(zone_type, avg_energies)
            )

            zones.append(zone)

        return zones

    def _classify_zone_type(self, avg_energies: np.ndarray) -> str:
        """Classify zone type based on average energy levels"""
        overall_energy = np.mean(avg_energies)

        if overall_energy >= 7.5:
            return "peak"
        elif overall_energy >= 6.0:
            return "productive"
        elif overall_energy >= 4.0:
            return "maintenance"
        else:
            return "recovery"

    def _get_suited_activities(self, zone_type: str, avg_energies: np.ndarray) -> List[str]:
        """Determine what activities are suited for this energy zone"""

        cognitive, physical, emotional, creative = avg_energies

        activities = []

        if zone_type == "peak":
            activities.extend(["complex_problem_solving", "creative_work", "challenging_exercise"])
            if cognitive >= 8:
                activities.extend(["strategic_planning", "learning_new_skills"])
            if physical >= 8:
                activities.extend(["high_intensity_workout", "sports_performance"])
            if creative >= 8:
                activities.extend(["artistic_creation", "innovation_sessions"])

        elif zone_type == "productive":
            activities.extend(["focused_work", "moderate_exercise", "skill_practice"])
            if cognitive >= 6:
                activities.extend(["analytical_tasks", "detailed_planning"])
            if physical >= 6:
                activities.extend(["strength_training", "cardio_sessions"])

        elif zone_type == "maintenance":
            activities.extend(["routine_tasks", "light_exercise", "social_activities"])
            activities.extend(["email_processing", "gentle_movement", "meal_preparation"])

        else:  # recovery
            activities.extend(["rest", "meditation", "gentle_stretching"])
            activities.extend(["reading", "light_meal", "nature_time"])

        return activities

    def _get_avoided_activities(self, zone_type: str, avg_energies: np.ndarray) -> List[str]:
        """Determine what activities to avoid during this energy zone"""

        avoided = []

        if zone_type == "recovery":
            avoided.extend([
                "high_intensity_exercise", "complex_decision_making",
                "challenging_conversations", "new_skill_learning"
            ])
        elif zone_type == "maintenance":
            avoided.extend([
                "peak_performance_tasks", "creative_breakthroughs",
                "intense_physical_training"
            ])
        elif zone_type == "productive":
            avoided.extend(["extremely_demanding_tasks"])

        return avoided
```

### Phase 3: Dynamic Zone-Based Scheduling (Weeks 5-6)

#### 3.1 Smart Activity Scheduler

**New Service: `services/dynamic_scheduling_service.py`**

```python
from typing import List, Dict, Optional, Tuple
from datetime import datetime, time, timedelta

class SchedulingConstraint(BaseModel):
    constraint_type: str  # "energy_minimum", "time_window", "dependency", "preference"
    parameters: Dict[str, Any]
    priority: int  # 1-10, higher = more important
    is_hard_constraint: bool  # True = must satisfy, False = prefer to satisfy

class ScheduledActivity(BaseModel):
    activity_id: str
    title: str
    energy_zone_assigned: str
    scheduled_start: datetime
    scheduled_end: datetime
    energy_requirements: Dict[str, float]
    confidence_score: float
    alternatives: List[Dict[str, Any]]
    adaptation_triggers: List[str]

class DynamicSchedulingService:
    """Schedule activities based on user's dynamic energy zones"""

    def __init__(self):
        self.energy_zone_service = EnergyPatternAnalysisService()
        self.activity_categorizer = ActivityEnergyRequirementsService()

    async def generate_dynamic_schedule(
        self,
        user_id: str,
        target_date: datetime,
        activities: List[Dict[str, Any]],
        constraints: List[SchedulingConstraint] = None
    ) -> List[ScheduledActivity]:
        """Generate optimal schedule based on energy zones and activity requirements"""

        # Get user's energy zones for target date
        user_zones = await self._get_user_energy_zones(user_id, target_date)

        # Analyze energy requirements for each activity
        activity_requirements = await self._analyze_activity_requirements(activities)

        # Apply scheduling algorithm
        schedule = await self._optimize_schedule(
            user_zones, activity_requirements, constraints, target_date
        )

        # Add adaptation triggers and alternatives
        enhanced_schedule = await self._enhance_with_adaptations(schedule, user_zones)

        return enhanced_schedule

    async def _analyze_activity_requirements(
        self,
        activities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze energy requirements for each activity"""

        enhanced_activities = []

        for activity in activities:
            # Determine energy requirements based on activity type and intensity
            energy_req = await self.activity_categorizer.get_energy_requirements(
                activity.get('task_type', 'general'),
                activity.get('intensity_hint', 'moderate'),
                activity.get('duration_minutes', 30)
            )

            activity['energy_requirements'] = energy_req
            activity['scheduling_flexibility'] = self._calculate_flexibility(activity)
            activity['optimal_zone_types'] = self._get_optimal_zones(energy_req)

            enhanced_activities.append(activity)

        return enhanced_activities

    async def _optimize_schedule(
        self,
        user_zones: List[EnergyZone],
        activities: List[Dict[str, Any]],
        constraints: List[SchedulingConstraint],
        target_date: datetime
    ) -> List[ScheduledActivity]:
        """Optimize activity scheduling using energy zone matching"""

        scheduled_activities = []

        # Sort activities by priority and energy requirements
        sorted_activities = sorted(
            activities,
            key=lambda a: (a.get('priority_level', 5), -max(a['energy_requirements'].values()))
        )

        # Sort zones by energy level (highest first)
        sorted_zones = sorted(
            user_zones,
            key=lambda z: sum(z.energy_characteristics.values()),
            reverse=True
        )

        # Greedy assignment algorithm
        used_time_slots = []

        for activity in sorted_activities:
            best_assignment = await self._find_best_zone_assignment(
                activity, sorted_zones, used_time_slots, target_date
            )

            if best_assignment:
                scheduled_activity = ScheduledActivity(
                    activity_id=activity.get('task_id', f"activity_{len(scheduled_activities)}"),
                    title=activity['title'],
                    energy_zone_assigned=best_assignment['zone'].zone_id,
                    scheduled_start=best_assignment['start_time'],
                    scheduled_end=best_assignment['end_time'],
                    energy_requirements=activity['energy_requirements'],
                    confidence_score=best_assignment['confidence'],
                    alternatives=[],
                    adaptation_triggers=[]
                )

                scheduled_activities.append(scheduled_activity)
                used_time_slots.append(best_assignment)

        return scheduled_activities

    async def _find_best_zone_assignment(
        self,
        activity: Dict[str, Any],
        available_zones: List[EnergyZone],
        used_slots: List[Dict],
        target_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Find the best energy zone assignment for an activity"""

        activity_duration = timedelta(minutes=activity.get('duration_minutes', 30))
        energy_requirements = activity['energy_requirements']

        best_assignment = None
        best_score = 0

        for zone in available_zones:
            # Check if this zone type is suitable for the activity
            if not self._is_zone_suitable(zone, energy_requirements):
                continue

            # Check for available time slots in this zone
            zone_start = datetime.combine(target_date.date(), zone.start_time)
            zone_end = datetime.combine(target_date.date(), zone.end_time)

            # Find available time windows
            available_windows = self._find_available_windows(
                zone_start, zone_end, activity_duration, used_slots
            )

            for window_start, window_end in available_windows:
                # Calculate match score
                score = self._calculate_zone_match_score(
                    zone, energy_requirements, window_start, activity
                )

                if score > best_score:
                    best_score = score
                    best_assignment = {
                        'zone': zone,
                        'start_time': window_start,
                        'end_time': window_start + activity_duration,
                        'confidence': score,
                        'match_reasons': self._get_match_reasons(zone, energy_requirements)
                    }

        return best_assignment

    def _calculate_zone_match_score(
        self,
        zone: EnergyZone,
        energy_requirements: Dict[str, float],
        scheduled_time: datetime,
        activity: Dict[str, Any]
    ) -> float:
        """Calculate how well a zone matches activity requirements"""

        # Base energy matching score
        energy_match = 0
        total_weight = 0

        for energy_type, required_level in energy_requirements.items():
            if energy_type in zone.energy_characteristics:
                available_level = zone.energy_characteristics[energy_type]
                # Preference for zones that exceed requirements
                match = min(1.0, available_level / max(required_level, 1.0))
                energy_match += match
                total_weight += 1

        energy_score = energy_match / max(total_weight, 1) if total_weight > 0 else 0

        # Zone confidence boost
        confidence_boost = zone.confidence_score * 0.2

        # Time preference (if activity has preferred timing)
        time_preference = self._calculate_time_preference(activity, scheduled_time)

        # Final score
        final_score = (energy_score * 0.6) + confidence_boost + (time_preference * 0.2)

        return min(1.0, final_score)

    async def _enhance_with_adaptations(
        self,
        schedule: List[ScheduledActivity],
        user_zones: List[EnergyZone]
    ) -> List[ScheduledActivity]:
        """Add adaptation triggers and alternatives to scheduled activities"""

        enhanced_schedule = []

        for activity in schedule:
            # Add adaptation triggers
            activity.adaptation_triggers = [
                f"If energy drops below {min(activity.energy_requirements.values()) * 0.7}: Move to recovery zone",
                f"If energy exceeds {max(activity.energy_requirements.values()) * 1.3}: Enhance intensity",
                "If zone becomes unavailable: Reschedule to next suitable zone"
            ]

            # Generate alternatives
            activity.alternatives = await self._generate_alternatives(activity, user_zones)

            enhanced_schedule.append(activity)

        return enhanced_schedule

class ActivityEnergyRequirementsService:
    """Determine energy requirements for different types of activities"""

    def __init__(self):
        self.activity_energy_profiles = {
            "high_exercise": {"cognitive": 3, "physical": 9, "emotional": 6, "creative": 3},
            "moderate_exercise": {"cognitive": 3, "physical": 6, "emotional": 5, "creative": 3},
            "easy_exercise": {"cognitive": 2, "physical": 3, "emotional": 4, "creative": 2},
            "complex_cognitive": {"cognitive": 9, "physical": 2, "emotional": 6, "creative": 8},
            "routine_cognitive": {"cognitive": 5, "physical": 2, "emotional": 4, "creative": 3},
            "creative_work": {"cognitive": 7, "physical": 2, "emotional": 7, "creative": 9},
            "social_activity": {"cognitive": 4, "physical": 3, "emotional": 8, "creative": 5},
            "meditation": {"cognitive": 3, "physical": 1, "emotional": 5, "creative": 4},
            "meal_preparation": {"cognitive": 3, "physical": 4, "emotional": 4, "creative": 5}
        }

    async def get_energy_requirements(
        self,
        task_type: str,
        intensity: str,
        duration_minutes: int
    ) -> Dict[str, float]:
        """Get energy requirements for a specific activity"""

        # Get base requirements
        base_requirements = self.activity_energy_profiles.get(
            task_type, {"cognitive": 4, "physical": 4, "emotional": 4, "creative": 4}
        )

        # Adjust for intensity
        intensity_multipliers = {
            "easy": 0.7,
            "moderate": 1.0,
            "high": 1.4
        }

        multiplier = intensity_multipliers.get(intensity, 1.0)

        # Adjust for duration (longer activities require sustained energy)
        duration_factor = min(1.5, 1.0 + (duration_minutes - 30) / 120)

        # Apply adjustments
        adjusted_requirements = {}
        for energy_type, base_value in base_requirements.items():
            adjusted_requirements[energy_type] = min(10, base_value * multiplier * duration_factor)

        return adjusted_requirements
```

### Phase 4: Real-time Zone Adaptation (Weeks 7-8)

#### 4.1 Dynamic Zone Adjustment System

**Enhanced Service: `services/real_time_zone_adaptation_service.py`**

```python
class ZoneAdaptation(BaseModel):
    adaptation_id: str
    user_id: str
    timestamp: datetime
    original_zone: str
    adapted_zone: str
    trigger_reason: str
    confidence: float
    duration_hours: int

class RealTimeZoneAdaptationService:
    """Adapt energy zones and schedules based on real-time conditions"""

    async def monitor_and_adapt_zones(self, user_id: str) -> List[ZoneAdaptation]:
        """Continuously monitor energy levels and adapt zones as needed"""

        # Get current energy reading
        current_energy = await self._get_latest_energy_reading(user_id)

        # Get predicted energy for current time
        predicted_energy = await self._get_predicted_energy(user_id, datetime.now())

        # Check for significant deviations
        adaptations = []

        if self._energy_deviation_significant(current_energy, predicted_energy):
            adaptation = await self._create_zone_adaptation(
                user_id, current_energy, predicted_energy
            )
            adaptations.append(adaptation)

            # Update schedule if needed
            await self._update_current_schedule(user_id, adaptation)

        return adaptations

    async def _create_zone_adaptation(
        self,
        user_id: str,
        current_energy: EnergyReading,
        predicted_energy: Dict[str, float]
    ) -> ZoneAdaptation:
        """Create zone adaptation based on energy deviation"""

        # Determine if current energy is higher or lower than predicted
        energy_diff = current_energy.overall_energy - predicted_energy.get('overall', 5.0)

        if energy_diff > 2.0:  # Significantly higher energy
            adapted_zone_type = "upgraded_to_productive" if predicted_energy.get('overall', 5.0) < 6 else "upgraded_to_peak"
            trigger_reason = f"Energy surge detected: {current_energy.overall_energy:.1f} vs predicted {predicted_energy.get('overall', 5.0):.1f}"
        elif energy_diff < -2.0:  # Significantly lower energy
            adapted_zone_type = "downgraded_to_recovery" if current_energy.overall_energy < 4 else "downgraded_to_maintenance"
            trigger_reason = f"Energy drop detected: {current_energy.overall_energy:.1f} vs predicted {predicted_energy.get('overall', 5.0):.1f}"
        else:
            return None  # No significant deviation

        return ZoneAdaptation(
            adaptation_id=f"zone_adapt_{user_id}_{int(current_energy.timestamp.timestamp())}",
            user_id=user_id,
            timestamp=current_energy.timestamp,
            original_zone=self._get_current_predicted_zone(user_id),
            adapted_zone=adapted_zone_type,
            trigger_reason=trigger_reason,
            confidence=current_energy.confidence,
            duration_hours=2  # Adaptation lasts for 2 hours by default
        )
```

## Integration with Existing System

### Integration Points

1. **Enhance Routine Generation Service**
```python
# In services/agents/routine/main.py
async def _create_energy_aware_routine_plan(
    self,
    user_context,
    archetype: str,
    behavior_analysis: Optional[dict] = None
) -> RoutinePlanResult:
    """Create routine plan based on user's energy zones"""

    # Get user's energy zones
    energy_zones = await self.energy_zone_service.get_user_energy_zones(user_context.user_id)

    # Generate activities based on zones
    zone_based_activities = await self.dynamic_scheduler.generate_dynamic_schedule(
        user_id=user_context.user_id,
        target_date=datetime.now(),
        activities=self._get_potential_activities(archetype),
        energy_zones=energy_zones
    )

    # Convert to existing RoutinePlanResult format
    return self._convert_to_routine_plan_result(zone_based_activities, archetype)
```

2. **Enhance Plan Extraction Service**
```python
# Add energy zone metadata to extracted tasks
def _extract_enhanced_task_with_energy_zones(self, task: ExtractedTask, user_id: str) -> ExtractedTask:
    """Enhance task with energy zone information"""

    # Get optimal energy zone for this task
    optimal_zone = self.energy_analysis_service.get_optimal_zone_for_task(
        task.task_type,
        task.intensity_hint,
        user_id
    )

    # Add energy zone metadata
    task.optimal_energy_zone = optimal_zone
    task.energy_requirements = self.activity_energy_service.get_energy_requirements(
        task.task_type, task.intensity_hint, task.estimated_duration_minutes
    )

    return task
```

## Expected Output with Dynamic Energy Zones

### Enhanced Task Output with Energy Zone Mapping:

```json
{
  "task_id": "morning_optimization_peak_001",
  "title": "Strategic Planning Session",
  "archetype_specific_title": "Peak Performance Planning Protocol",
  "energy_zone_assignment": {
    "zone_id": "user123_weekday_peak_1",
    "zone_name": "Cognitive Peak Zone",
    "zone_type": "peak",
    "scheduled_time": "09:15-10:45 AM",
    "energy_match_score": 0.92,
    "match_reasons": [
      "High cognitive energy available (8.4/10)",
      "Zone confidence: 89%",
      "Historical success rate: 94% for similar tasks"
    ]
  },
  "energy_requirements": {
    "cognitive": 8.5,
    "physical": 2.0,
    "emotional": 6.0,
    "creative": 7.5
  },
  "dynamic_adaptations": {
    "real_time_triggers": [
      "If cognitive energy drops below 7.0: Switch to routine planning",
      "If energy exceeds 9.0: Add complexity challenges",
      "If zone becomes unavailable: Move to secondary peak zone (2:00-3:30 PM)"
    ],
    "alternative_versions": [
      {
        "condition": "low_energy_day",
        "modified_task": "Simple priority review (20 min)",
        "target_zone": "maintenance_zone"
      },
      {
        "condition": "high_energy_day",
        "modified_task": "Strategic innovation session (90 min)",
        "target_zone": "extended_peak_zone"
      }
    ]
  },
  "personalized_timing": {
    "optimal_start": "09:15 AM",
    "latest_start": "10:00 AM",
    "flexibility_window": "45 minutes",
    "user_peak_probability": "87%",
    "circadian_alignment": "optimal"
  }
}
```

This dynamic energy zones system would transform your routine generation from static time blocks to truly personalized, energy-responsive scheduling that adapts to each user's unique daily energy patterns.