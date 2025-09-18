# Advanced Implementation Plan: Post-MVP to Full Feature System

## Overview

This plan builds on your MVP implementation to achieve the advanced features that provide truly dynamic, adaptive, educational health optimization experiences. The plan is designed to work with your existing architecture while systematically adding sophisticated capabilities.

## Starting Point: Post-MVP Architecture

After MVP implementation, you'll have:
- ✅ Enhanced task classification with intensity hints
- ✅ Archetype-specific communication
- ✅ Basic scaling guidance
- ✅ Improved user presentation layer
- ✅ Optional metadata columns for future expansion

## Advanced Feature Implementation Roadmap

### Phase 4: Flexible Time Block Architecture (Weeks 4-6)

#### 4.1 Dynamic Time Block Generation System

**New Service: `services/time_block_generation_service.py`**

```python
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from pydantic import BaseModel

class ArchetypeTimeBlockTemplate(BaseModel):
    archetype: str
    template_name: str
    blocks: List[Dict[str, Any]]
    total_duration_minutes: int
    energy_distribution: Dict[str, float]  # morning: 0.4, midday: 0.3, evening: 0.3

class DynamicTimeBlock(BaseModel):
    block_id: str
    title: str
    archetype_specific_title: str
    start_time: time
    end_time: time
    purpose: str
    energy_requirement: str  # "low", "medium", "high"
    flexibility_minutes: int  # How much this block can shift
    dependencies: List[str]  # Other blocks this depends on
    archetype_messaging: str
    alternative_versions: List[Dict]  # Different versions for different energy levels

class TimeBlockGenerationService:
    """Generate archetype-specific, flexible time block structures"""

    def __init__(self):
        self.archetype_templates = self._load_archetype_templates()

    def _load_archetype_templates(self) -> Dict[str, List[ArchetypeTimeBlockTemplate]]:
        """Load archetype-specific time block templates"""
        return {
            "Peak Performer": [
                ArchetypeTimeBlockTemplate(
                    archetype="Peak Performer",
                    template_name="optimization_protocol",
                    blocks=[
                        {
                            "title": "Dawn Optimization Protocol",
                            "time_range": "5:00-6:30 AM",
                            "purpose": "Circadian advantage and metabolic priming",
                            "energy_requirement": "medium",
                            "core_activities": ["hrv_assessment", "light_exposure", "hydration_protocol"]
                        },
                        {
                            "title": "Peak Performance Window",
                            "time_range": "9:00-11:30 AM",
                            "purpose": "High-cognitive load optimization",
                            "energy_requirement": "high",
                            "core_activities": ["focus_work", "performance_tracking", "optimization_protocols"]
                        },
                        {
                            "title": "Recovery Analytics Session",
                            "time_range": "2:00-2:30 PM",
                            "purpose": "Data review and adaptive planning",
                            "energy_requirement": "low",
                            "core_activities": ["data_analysis", "recovery_assessment", "plan_adjustment"]
                        },
                        {
                            "title": "Evening Optimization Review",
                            "time_range": "8:00-9:00 PM",
                            "purpose": "Performance analysis and next-day prep",
                            "energy_requirement": "medium",
                            "core_activities": ["performance_review", "next_day_planning", "sleep_optimization"]
                        }
                    ],
                    total_duration_minutes: 270,
                    energy_distribution = {"morning": 0.35, "midday": 0.45, "evening": 0.20}
                )
            ],
            "Foundation Builder": [
                ArchetypeTimeBlockTemplate(
                    archetype="Foundation Builder",
                    template_name="gentle_building",
                    blocks=[
                        {
                            "title": "Gentle Awakening Ritual",
                            "time_range": "7:30-8:30 AM",
                            "purpose": "Comfort-centered day initiation",
                            "energy_requirement": "low",
                            "core_activities": ["peaceful_waking", "comfort_hydration", "gentle_movement"]
                        },
                        {
                            "title": "Midday Nourishment",
                            "time_range": "12:00-1:00 PM",
                            "purpose": "Energy restoration and self-care",
                            "energy_requirement": "medium",
                            "core_activities": ["mindful_eating", "social_connection", "brief_rest"]
                        },
                        {
                            "title": "Evening Comfort Ritual",
                            "time_range": "7:00-8:00 PM",
                            "purpose": "Peaceful transition to rest",
                            "energy_requirement": "low",
                            "core_activities": ["comfort_activities", "gratitude_practice", "sleep_preparation"]
                        }
                    ],
                    total_duration_minutes = 180,
                    energy_distribution = {"morning": 0.25, "midday": 0.45, "evening": 0.30}
                )
            ]
            # ... templates for all 6 archetypes
        }

    async def generate_flexible_time_blocks(
        self,
        archetype: str,
        mode: str,
        user_constraints: Dict[str, Any],
        current_progression_level: str
    ) -> List[DynamicTimeBlock]:
        """Generate archetype-specific time blocks with flexibility"""

        template = self._select_template(archetype, mode, current_progression_level)
        user_schedule = user_constraints.get('preferred_schedule', {})

        flexible_blocks = []
        for block_template in template.blocks:
            # Adapt timing based on user constraints
            adapted_timing = self._adapt_timing_to_user(block_template, user_schedule)

            # Create multiple versions for different energy levels
            block_versions = self._create_energy_variants(block_template, mode)

            dynamic_block = DynamicTimeBlock(
                block_id=f"{archetype}_{block_template['title'].lower().replace(' ', '_')}",
                title=block_template['title'],
                archetype_specific_title=self._customize_title_for_archetype(
                    block_template['title'], archetype
                ),
                start_time=adapted_timing['start'],
                end_time=adapted_timing['end'],
                purpose=block_template['purpose'],
                energy_requirement=block_template['energy_requirement'],
                flexibility_minutes=self._calculate_flexibility(block_template, user_constraints),
                dependencies=block_template.get('dependencies', []),
                archetype_messaging=self._generate_archetype_messaging(
                    block_template, archetype, mode
                ),
                alternative_versions=block_versions
            )

            flexible_blocks.append(dynamic_block)

        return flexible_blocks
```

#### 4.2 Enhanced Database Schema

```sql
-- New table for flexible time block templates
CREATE TABLE archetype_time_block_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    archetype VARCHAR(50) NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    template_data JSONB NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced time_blocks table
ALTER TABLE time_blocks ADD COLUMN template_id UUID REFERENCES archetype_time_block_templates(id);
ALTER TABLE time_blocks ADD COLUMN energy_requirement VARCHAR(20);
ALTER TABLE time_blocks ADD COLUMN flexibility_minutes INTEGER DEFAULT 15;
ALTER TABLE time_blocks ADD COLUMN alternative_versions JSONB;
ALTER TABLE time_blocks ADD COLUMN dependencies JSONB;

-- User schedule preferences
CREATE TABLE user_schedule_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id VARCHAR(100) NOT NULL,
    wake_time TIME,
    sleep_time TIME,
    work_start_time TIME,
    work_end_time TIME,
    meal_preferences JSONB,
    exercise_preferences JSONB,
    constraint_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 5: Expanded Habit Repertoire System (Weeks 7-9)

#### 5.1 Comprehensive Habit Database

**New Service: `services/habit_repertoire_service.py`**

```python
from typing import Dict, List, Optional
from pydantic import BaseModel

class HabitDefinition(BaseModel):
    habit_id: str
    name: str
    category: str  # "movement", "nutrition", "mindfulness", "social", "cognitive"
    archetype_compatibility: List[str]
    difficulty_level: int  # 1-10
    prerequisites: List[str]  # Other habits that should be mastered first
    duration_minutes: int
    energy_requirement: str
    implementation_details: Dict[str, Any]
    scaling_options: Dict[str, Any]
    contraindications: List[str]
    educational_content: Dict[str, Any]

class HabitRepertoireService:
    """Manage expanded archetype-specific habit repertoire"""

    def __init__(self):
        self.habit_database = self._initialize_habit_database()

    def _initialize_habit_database(self) -> Dict[str, List[HabitDefinition]]:
        """Initialize comprehensive habit database by archetype"""
        return {
            "Peak Performer": [
                HabitDefinition(
                    habit_id="hrv_cold_exposure",
                    name="HRV-Guided Cold Exposure Protocol",
                    category="advanced_recovery",
                    archetype_compatibility=["Peak Performer", "Systematic Improver"],
                    difficulty_level=8,
                    prerequisites=["basic_breathing", "hrv_familiarity"],
                    duration_minutes=5,
                    energy_requirement="medium",
                    implementation_details={
                        "technique": "2-minute cold shower with real-time HRV monitoring",
                        "equipment": "HRV monitor, shower thermometer",
                        "optimal_timing": "Post-workout or morning",
                        "progression": "Start 30 seconds, increase by 15 seconds weekly"
                    },
                    scaling_options={
                        "beginner": "Cold face plunge for 30 seconds",
                        "intermediate": "2-minute cold shower",
                        "advanced": "Ice bath with breathing protocols"
                    },
                    contraindications=["cardiovascular conditions", "pregnancy"],
                    educational_content={
                        "benefits": "Improved stress resilience, metabolic enhancement",
                        "science": "Activates brown adipose tissue, improves HRV",
                        "research": "2021 study showing 15% improvement in stress markers"
                    }
                ),
                HabitDefinition(
                    habit_id="cgm_optimization",
                    name="Continuous Glucose Response Tracking",
                    category="metabolic_optimization",
                    archetype_compatibility=["Peak Performer"],
                    difficulty_level=9,
                    prerequisites=["nutrition_basics", "data_comfort"],
                    duration_minutes=2,  # For checking/logging
                    energy_requirement="low",
                    implementation_details={
                        "technique": "Post-meal glucose spike analysis with macro adjustments",
                        "equipment": "Continuous glucose monitor, tracking app",
                        "optimal_timing": "1-2 hours post-meal",
                        "interpretation": "Target <140 mg/dL peak, <40 mg/dL spike"
                    },
                    scaling_options={
                        "beginner": "Weekly glucose spot checks",
                        "intermediate": "Daily post-meal monitoring",
                        "advanced": "Continuous monitoring with meal optimization"
                    },
                    contraindications=["diabetes without medical supervision"],
                    educational_content={
                        "benefits": "Optimized energy levels, improved metabolic health",
                        "science": "Postprandial glucose response optimization",
                        "research": "2020 study on personalized nutrition effectiveness"
                    }
                )
            ],
            "Connected Explorer": [
                HabitDefinition(
                    habit_id="community_gardening",
                    name="Community Garden Volunteering",
                    category="meaningful_service",
                    archetype_compatibility=["Connected Explorer", "Foundation Builder"],
                    difficulty_level=3,
                    prerequisites=["basic_outdoor_comfort"],
                    duration_minutes=120,
                    energy_requirement="medium",
                    implementation_details={
                        "technique": "2-hour outdoor community connection with physical activity",
                        "location": "Local community garden or urban farm",
                        "activities": "Planting, weeding, harvesting, socializing",
                        "seasonal_adaptations": "Indoor seed starting in winter"
                    },
                    scaling_options={
                        "beginner": "30-minute garden visit and observation",
                        "intermediate": "1-hour hands-on gardening",
                        "advanced": "Leading garden workshops for others"
                    },
                    contraindications=["severe allergies", "mobility limitations"],
                    educational_content={
                        "benefits": "Social connection, physical activity, mental health",
                        "science": "Exposure to soil microbes improves immune function",
                        "research": "2019 study on gardening and stress reduction"
                    }
                ),
                HabitDefinition(
                    habit_id="cultural_language_exchange",
                    name="Cultural Language Exchange",
                    category="social_learning",
                    archetype_compatibility=["Connected Explorer", "Transformation Seeker"],
                    difficulty_level=4,
                    prerequisites=["social_comfort"],
                    duration_minutes=30,
                    energy_requirement="medium",
                    implementation_details={
                        "technique": "30-minute conversation practice with international community",
                        "platforms": "HelloTalk, Tandem, local language exchange meetups",
                        "structure": "15 min their language, 15 min your language",
                        "topics": "Culture, traditions, daily life, health practices"
                    },
                    scaling_options={
                        "beginner": "Text-based language exchange",
                        "intermediate": "Video conversations",
                        "advanced": "In-person cultural activities"
                    },
                    contraindications=["severe social anxiety without support"],
                    educational_content={
                        "benefits": "Cognitive enhancement, cultural awareness, social connection",
                        "science": "Bilingual brain shows increased neuroplasticity",
                        "research": "2018 study on language learning and brain health"
                    }
                )
            ]
            # ... Continue for all archetypes with 15-20 habits each
        }

    async def get_appropriate_habits(
        self,
        archetype: str,
        current_mastery_level: int,
        user_constraints: Dict[str, Any],
        mode: str
    ) -> List[HabitDefinition]:
        """Select appropriate habits based on user progression and constraints"""

        archetype_habits = self.habit_database.get(archetype, [])

        # Filter by difficulty level and prerequisites
        appropriate_habits = []
        for habit in archetype_habits:
            if self._is_habit_appropriate(habit, current_mastery_level, user_constraints, mode):
                appropriate_habits.append(habit)

        return appropriate_habits
```

#### 5.2 Habit Database Schema

```sql
-- Comprehensive habit definitions
CREATE TABLE habit_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    habit_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    archetype_compatibility JSONB NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 10),
    prerequisites JSONB,
    duration_minutes INTEGER,
    energy_requirement VARCHAR(20),
    implementation_details JSONB,
    scaling_options JSONB,
    contraindications JSONB,
    educational_content JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User habit mastery tracking
CREATE TABLE user_habit_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id VARCHAR(100) NOT NULL,
    habit_id VARCHAR(100) REFERENCES habit_definitions(habit_id),
    mastery_level INTEGER CHECK (mastery_level BETWEEN 0 AND 10),
    first_attempted DATE,
    last_attempted DATE,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 6: Real-time Adaptation System (Weeks 10-12)

#### 6.1 Real-time Monitoring and Adaptation Engine

**New Service: `services/real_time_adaptation_service.py`**

```python
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

class BiometricReading(BaseModel):
    user_id: str
    timestamp: datetime
    hrv_score: Optional[float]
    heart_rate: Optional[int]
    energy_level: Optional[float]  # 0-1 scale
    stress_level: Optional[float]  # 0-1 scale
    readiness_score: Optional[float]
    source: str  # "wearable", "manual", "app"

class AdaptationTrigger(BaseModel):
    trigger_id: str
    condition: str
    threshold: float
    action: str
    priority: int

class PlanAdaptation(BaseModel):
    adaptation_id: str
    timestamp: datetime
    user_id: str
    trigger_reason: str
    original_task: Dict[str, Any]
    adapted_task: Dict[str, Any]
    confidence_score: float
    expires_at: Optional[datetime]

class RealTimeAdaptationService:
    """Monitor biomarkers and adapt plans in real-time"""

    def __init__(self):
        self.adaptation_triggers = self._initialize_triggers()
        self.active_adaptations: Dict[str, List[PlanAdaptation]] = {}

    def _initialize_triggers(self) -> List[AdaptationTrigger]:
        """Define conditions that trigger plan adaptations"""
        return [
            AdaptationTrigger(
                trigger_id="energy_drop",
                condition="energy_level < 0.3 AND previous_energy_level > 0.6",
                threshold=0.3,
                action="reduce_intensity_by_50_percent",
                priority=1
            ),
            AdaptationTrigger(
                trigger_id="stress_spike",
                condition="stress_level > 0.8 AND hrv_score < baseline_hrv * 0.7",
                threshold=0.8,
                action="switch_to_recovery_activities",
                priority=1
            ),
            AdaptationTrigger(
                trigger_id="energy_surge",
                condition="energy_level > 0.8 AND readiness_score > 0.8",
                threshold=0.8,
                action="upgrade_to_performance_mode",
                priority=2
            ),
            AdaptationTrigger(
                trigger_id="sleep_debt",
                condition="sleep_quality < 0.6 FOR 2 consecutive days",
                threshold=0.6,
                action="prioritize_recovery_activities",
                priority=1
            )
        ]

    async def process_biometric_reading(self, reading: BiometricReading) -> List[PlanAdaptation]:
        """Process new biometric data and generate adaptations if needed"""
        adaptations = []

        # Get user's current plan for today
        current_plan = await self._get_current_user_plan(reading.user_id)
        if not current_plan:
            return adaptations

        # Check each trigger condition
        for trigger in self.adaptation_triggers:
            if await self._evaluate_trigger_condition(trigger, reading):
                adaptation = await self._create_adaptation(
                    trigger, reading, current_plan
                )
                if adaptation:
                    adaptations.append(adaptation)

        # Store and activate adaptations
        if adaptations:
            await self._store_and_activate_adaptations(reading.user_id, adaptations)

        return adaptations

    async def _evaluate_trigger_condition(
        self,
        trigger: AdaptationTrigger,
        reading: BiometricReading
    ) -> bool:
        """Evaluate if trigger condition is met"""

        # Get user's baseline and recent history
        user_baseline = await self._get_user_baseline(reading.user_id)
        recent_readings = await self._get_recent_readings(reading.user_id, hours=24)

        # Evaluate condition based on trigger type
        if trigger.trigger_id == "energy_drop":
            previous_energy = recent_readings[-1].energy_level if recent_readings else 0.5
            return (reading.energy_level < trigger.threshold and
                   previous_energy > 0.6)

        elif trigger.trigger_id == "stress_spike":
            baseline_hrv = user_baseline.get('hrv_score', 50)
            return (reading.stress_level > trigger.threshold and
                   reading.hrv_score < baseline_hrv * 0.7)

        elif trigger.trigger_id == "energy_surge":
            return (reading.energy_level > trigger.threshold and
                   reading.readiness_score > trigger.threshold)

        # Add more trigger evaluations...
        return False

    async def _create_adaptation(
        self,
        trigger: AdaptationTrigger,
        reading: BiometricReading,
        current_plan: Dict[str, Any]
    ) -> Optional[PlanAdaptation]:
        """Create specific plan adaptation based on trigger"""

        # Get upcoming tasks that can be adapted
        upcoming_tasks = await self._get_upcoming_tasks(reading.user_id)
        if not upcoming_tasks:
            return None

        # Select task to adapt based on timing and impact
        target_task = self._select_adaptation_target(upcoming_tasks, trigger)

        # Generate adapted version
        adapted_task = await self._generate_adapted_task(
            target_task, trigger.action, reading
        )

        return PlanAdaptation(
            adaptation_id=f"adapt_{reading.user_id}_{int(reading.timestamp.timestamp())}",
            timestamp=reading.timestamp,
            user_id=reading.user_id,
            trigger_reason=f"{trigger.trigger_id}: {trigger.condition}",
            original_task=target_task,
            adapted_task=adapted_task,
            confidence_score=self._calculate_adaptation_confidence(trigger, reading),
            expires_at=reading.timestamp + timedelta(hours=6)
        )

    async def _generate_adapted_task(
        self,
        original_task: Dict[str, Any],
        action: str,
        reading: BiometricReading
    ) -> Dict[str, Any]:
        """Generate adapted version of task based on action"""

        adapted_task = original_task.copy()

        if action == "reduce_intensity_by_50_percent":
            # Reduce duration and intensity
            if 'duration_minutes' in adapted_task:
                adapted_task['duration_minutes'] = max(5, adapted_task['duration_minutes'] // 2)

            adapted_task['intensity_hint'] = 'easy'
            adapted_task['adaptation_note'] = f"Reduced intensity due to low energy ({reading.energy_level:.1f})"
            adapted_task['scaling_info'] = "Take it extra easy today - listen to your body"

        elif action == "switch_to_recovery_activities":
            # Replace with recovery-focused alternatives
            adapted_task.update({
                'title': 'Gentle Recovery Session',
                'description': 'Stress-reducing activities prioritized due to elevated stress levels',
                'task_type': 'recovery_mindfulness',
                'intensity_hint': 'easy',
                'adaptation_note': f"Switched to recovery due to stress spike ({reading.stress_level:.1f})",
                'activities': ['deep_breathing', 'gentle_stretching', 'calming_music']
            })

        elif action == "upgrade_to_performance_mode":
            # Enhance task for optimal energy state
            if 'duration_minutes' in adapted_task:
                adapted_task['duration_minutes'] = min(60, adapted_task['duration_minutes'] * 1.3)

            adapted_task['intensity_hint'] = 'high'
            adapted_task['adaptation_note'] = f"Enhanced for optimal energy state ({reading.energy_level:.1f})"
            adapted_task['scaling_info'] = "You're feeling great - push yourself a bit more today!"

        return adapted_task
```

#### 6.2 Real-time Data Collection Infrastructure

```sql
-- Real-time biometric readings
CREATE TABLE biometric_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    hrv_score FLOAT,
    heart_rate INTEGER,
    energy_level FLOAT CHECK (energy_level BETWEEN 0 AND 1),
    stress_level FLOAT CHECK (stress_level BETWEEN 0 AND 1),
    readiness_score FLOAT CHECK (readiness_score BETWEEN 0 AND 1),
    source VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Plan adaptations log
CREATE TABLE plan_adaptations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adaptation_id VARCHAR(200) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    trigger_reason TEXT,
    original_task JSONB,
    adapted_task JSONB,
    confidence_score FLOAT,
    was_accepted BOOLEAN,
    user_feedback TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User baseline calculations
CREATE TABLE user_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    baseline_value FLOAT,
    calculation_method VARCHAR(100),
    data_points_used INTEGER,
    calculated_at TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, metric_name)
);
```

### Phase 7: Progressive Difficulty Tracking (Weeks 13-14)

#### 7.1 User Progression and Mastery System

**New Service: `services/progression_tracking_service.py`**

```python
class SkillMastery(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    current_level: int  # 0-10
    mastery_percentage: float  # 0-100
    attempts: int
    successes: int
    streak: int
    last_attempt: datetime
    mastery_criteria: Dict[str, Any]

class ProgressionLevel(BaseModel):
    level_id: str
    level_name: str
    archetype: str
    required_skills: List[str]
    unlocked_habits: List[str]
    estimated_weeks_to_complete: int
    description: str

class UserProgressionProfile(BaseModel):
    user_id: str
    archetype: str
    current_level: str
    weeks_in_system: int
    total_mastered_skills: int
    mastered_skills: List[str]
    in_progress_skills: List[str]
    ready_for_advancement: List[str]
    next_recommended_skills: List[str]
    progression_velocity: float  # skills mastered per week

class ProgressionTrackingService:
    """Track user skill progression and unlock new challenges"""

    def __init__(self):
        self.progression_levels = self._initialize_progression_levels()
        self.mastery_criteria = self._initialize_mastery_criteria()

    def _initialize_progression_levels(self) -> Dict[str, List[ProgressionLevel]]:
        """Define progression levels for each archetype"""
        return {
            "Foundation Builder": [
                ProgressionLevel(
                    level_id="fb_beginner",
                    level_name="Gentle Starter",
                    archetype="Foundation Builder",
                    required_skills=["basic_hydration", "gentle_movement", "comfort_rituals"],
                    unlocked_habits=["walking", "stretching", "tea_ceremony", "journaling"],
                    estimated_weeks_to_complete=4,
                    description="Building the foundation with gentle, nurturing habits"
                ),
                ProgressionLevel(
                    level_id="fb_developing",
                    level_name="Confidence Builder",
                    archetype="Foundation Builder",
                    required_skills=["consistent_movement", "social_connection", "self_care_routine"],
                    unlocked_habits=["partner_walks", "cooking_rituals", "gardening", "creative_expression"],
                    estimated_weeks_to_complete=6,
                    description="Growing confidence through consistent, enjoyable practices"
                ),
                ProgressionLevel(
                    level_id="fb_established",
                    level_name="Strong Foundation",
                    archetype="Foundation Builder",
                    required_skills=["habit_stacking", "community_engagement", "personal_care_mastery"],
                    unlocked_habits=["group_activities", "teaching_others", "adventure_planning"],
                    estimated_weeks_to_complete=8,
                    description="Solid foundation enabling exploration and leadership"
                )
            ],
            "Peak Performer": [
                ProgressionLevel(
                    level_id="pp_analytical",
                    level_name="Data-Driven Optimizer",
                    archetype="Peak Performer",
                    required_skills=["metric_tracking", "baseline_establishment", "optimization_protocols"],
                    unlocked_habits=["hrv_training", "macro_tracking", "performance_testing"],
                    estimated_weeks_to_complete=3,
                    description="Establishing measurement systems and optimization baselines"
                ),
                ProgressionLevel(
                    level_id="pp_advanced",
                    level_name="Performance Engineer",
                    archetype="Peak Performer",
                    required_skills=["advanced_analytics", "protocol_design", "adaptation_mastery"],
                    unlocked_habits=["cold_exposure", "cgm_optimization", "nootropic_protocols"],
                    estimated_weeks_to_complete=4,
                    description="Advanced optimization techniques and experimental protocols"
                ),
                ProgressionLevel(
                    level_id="pp_expert",
                    level_name="Human Performance Expert",
                    archetype="Peak Performer",
                    required_skills=["system_design", "research_integration", "teaching_capability"],
                    unlocked_habits=["research_protocols", "coaching_others", "innovation_experiments"],
                    estimated_weeks_to_complete=6,
                    description="Leading-edge research integration and knowledge sharing"
                )
            ]
            # ... Continue for all archetypes
        }

    async def assess_user_progression(self, user_id: str) -> UserProgressionProfile:
        """Assess current user progression across all skills"""

        # Get user's skill mastery data
        skill_masteries = await self._get_user_skill_masteries(user_id)
        user_profile = await self._get_user_profile(user_id)
        archetype = user_profile.get('archetype', 'Foundation Builder')

        # Calculate current progression level
        current_level = self._calculate_current_level(skill_masteries, archetype)

        # Identify skills in different states
        mastered_skills = [s.skill_id for s in skill_masteries if s.mastery_percentage >= 80]
        in_progress_skills = [s.skill_id for s in skill_masteries if 20 <= s.mastery_percentage < 80]
        ready_for_advancement = self._identify_advancement_ready_skills(skill_masteries)

        # Calculate progression velocity
        weeks_in_system = self._calculate_weeks_in_system(user_id)
        progression_velocity = len(mastered_skills) / max(weeks_in_system, 1)

        # Recommend next skills
        next_recommended = await self._recommend_next_skills(
            current_level, mastered_skills, archetype
        )

        return UserProgressionProfile(
            user_id=user_id,
            archetype=archetype,
            current_level=current_level,
            weeks_in_system=weeks_in_system,
            total_mastered_skills=len(mastered_skills),
            mastered_skills=mastered_skills,
            in_progress_skills=in_progress_skills,
            ready_for_advancement=ready_for_advancement,
            next_recommended_skills=next_recommended,
            progression_velocity=progression_velocity
        )

    async def generate_progression_based_tasks(
        self,
        user_progression: UserProgressionProfile,
        time_blocks: List[DynamicTimeBlock]
    ) -> List[Dict[str, Any]]:
        """Generate tasks that match user's progression level"""

        progressive_tasks = []

        for time_block in time_blocks:
            # Get appropriate habits for this progression level
            level_definition = self.progression_levels[user_progression.archetype]
            current_level_def = next(
                (level for level in level_definition if level.level_id == user_progression.current_level),
                level_definition[0]
            )

            # Select habits that are appropriate for current progression
            available_habits = current_level_def.unlocked_habits

            # Choose habits that provide appropriate challenge
            for skill in user_progression.next_recommended_skills:
                task = await self._create_progression_task(
                    skill, time_block, user_progression
                )
                if task:
                    progressive_tasks.append(task)

        return progressive_tasks
```

### Phase 8: Rich Educational Content Generation (Weeks 15-16)

#### 8.1 Educational Content Generation System

**New Service: `services/educational_content_service.py`**

```python
class EducationalContent(BaseModel):
    content_id: str
    topic: str
    archetype_focus: str
    difficulty_level: int
    content_type: str  # "scientific_basis", "practical_guide", "troubleshooting"
    title: str
    summary: str
    detailed_content: Dict[str, Any]
    related_habits: List[str]
    sources: List[str]
    last_updated: datetime

class EducationalContentService:
    """Generate rich, archetype-specific educational content"""

    def __init__(self):
        self.content_templates = self._initialize_content_templates()
        self.research_database = self._initialize_research_database()

    async def generate_educational_content(
        self,
        task: Dict[str, Any],
        archetype: str,
        user_progression: UserProgressionProfile
    ) -> Dict[str, Any]:
        """Generate comprehensive educational content for a task"""

        base_content = await self._get_base_content(task['task_type'])

        educational_content = {
            "scientific_basis": await self._generate_scientific_basis(
                task, archetype, user_progression.current_level
            ),
            "practical_implementation": await self._generate_practical_guide(
                task, archetype, user_progression
            ),
            "personalization": await self._generate_personalization_guide(
                task, archetype, user_progression
            ),
            "success_indicators": await self._generate_success_indicators(
                task, archetype
            ),
            "troubleshooting": await self._generate_troubleshooting_guide(
                task, archetype
            ),
            "progressive_advancement": await self._generate_progression_path(
                task, user_progression
            )
        }

        return educational_content

    async def _generate_scientific_basis(
        self,
        task: Dict[str, Any],
        archetype: str,
        progression_level: str
    ) -> Dict[str, Any]:
        """Generate archetype-appropriate scientific explanations"""

        research_data = await self._get_relevant_research(task['task_type'])

        if archetype == "Peak Performer":
            return {
                "primary_mechanism": research_data['detailed_mechanism'],
                "supporting_research": research_data['latest_studies'][:3],
                "quantified_benefits": research_data['performance_metrics'],
                "optimization_factors": research_data['variables_to_track']
            }
        elif archetype == "Foundation Builder":
            return {
                "simple_explanation": research_data['simplified_mechanism'],
                "key_benefits": research_data['basic_benefits'],
                "why_it_helps": research_data['gentle_explanation'],
                "reassurance": "This is a well-established, safe practice"
            }
        # ... Continue for all archetypes

    async def _generate_practical_guide(
        self,
        task: Dict[str, Any],
        archetype: str,
        user_progression: UserProgressionProfile
    ) -> Dict[str, Any]:
        """Generate detailed, actionable implementation guidance"""

        base_technique = await self._get_base_technique(task['task_type'])

        practical_guide = {
            "step_by_step_instructions": self._adapt_instructions_for_archetype(
                base_technique['steps'], archetype
            ),
            "equipment_needed": base_technique.get('equipment', []),
            "optimal_timing": self._get_timing_recommendations(task, archetype),
            "duration_guidance": self._get_duration_recommendations(
                task, user_progression.current_level
            ),
            "preparation_steps": base_technique.get('preparation', []),
            "environmental_considerations": base_technique.get('environment', [])
        }

        return practical_guide

    async def _generate_personalization_guide(
        self,
        task: Dict[str, Any],
        archetype: str,
        user_progression: UserProgressionProfile
    ) -> Dict[str, Any]:
        """Generate archetype-specific personalization advice"""

        return {
            "archetype_optimization": self._get_archetype_specific_advice(task, archetype),
            "modifications": {
                "low_energy": self._generate_low_energy_modification(task, archetype),
                "high_energy": self._generate_high_energy_modification(task, archetype),
                "time_constraints": self._generate_time_constraint_modification(task),
                "travel": self._generate_travel_modification(task),
                "seasonal": self._generate_seasonal_modifications(task)
            },
            "progression_path": {
                "current_level": self._describe_current_level(task, user_progression),
                "next_level": self._describe_next_level(task, user_progression),
                "mastery_indicators": self._get_mastery_indicators(task, archetype)
            }
        }
```

## Implementation Timeline Summary

### Months 1-2: Foundation Enhancement (Phases 4-5)
- **Phase 4**: Flexible Time Block Architecture (Weeks 4-6)
- **Phase 5**: Expanded Habit Repertoire System (Weeks 7-9)

### Months 3-4: Intelligence Layer (Phases 6-8)
- **Phase 6**: Real-time Adaptation System (Weeks 10-12)
- **Phase 7**: Progressive Difficulty Tracking (Weeks 13-14)
- **Phase 8**: Rich Educational Content Generation (Weeks 15-16)

## Expected Advanced System Output

After full implementation, a single task would look like:

```json
{
  "task_id": "morning_light_exposure_advanced_fb_001",
  "title": "Morning Light Exposure with Gratitude Practice",
  "archetype_specific_title": "Gentle Morning Light Ritual",
  "description": "Combine natural light exposure with mindful gratitude practice",
  "category": "circadian_mindfulness",
  "intensity_hint": "easy",
  "user_friendly_intensity": "Light and gentle - like a warm hug from the morning sun",
  "duration_minutes": 15,
  "energy_requirement": "low",

  "time_block": {
    "block_id": "foundation_builder_gentle_awakening",
    "title": "Gentle Awakening Ritual",
    "archetype_messaging": "Building momentum - feel the power of consistency",
    "time_range": "7:30-8:30 AM",
    "flexibility_minutes": 30,
    "alternative_versions": [
      {"low_energy": "5-minute window sitting with warm drink"},
      {"high_energy": "20-minute garden walk with gratitude journaling"}
    ]
  },

  "progression_context": {
    "skill_level": "developing_foundation_builder",
    "progression_note": "You've mastered basic morning routines - ready for mindfulness integration",
    "skill_building": ["mindfulness_integration", "gratitude_practice", "nature_connection"],
    "next_progression": "Partner morning walks in 3 weeks",
    "mastery_indicators": [
      "Feeling naturally drawn to morning light",
      "Spontaneous gratitude thoughts during exposure",
      "Consistent 10+ day streaks"
    ]
  },

  "educational_content": {
    "scientific_basis": {
      "simple_explanation": "Morning light helps your body's natural clock stay in rhythm",
      "key_benefits": ["Better sleep timing", "Improved mood", "Natural energy"],
      "why_it_helps": "Like plants, humans need light to thrive and feel their best",
      "reassurance": "This is a gentle, natural practice used for thousands of years"
    },
    "practical_implementation": {
      "step_by_step_instructions": [
        "Find a comfortable spot near a window or outside",
        "Sit with your morning drink (tea, coffee, or water)",
        "Look toward the brightest part of the sky (not directly at sun)",
        "Think of 3 things you're grateful for while enjoying the light",
        "Notice how the light feels on your face and in your eyes",
        "End with a deep breath and positive intention for the day"
      ],
      "equipment_needed": ["Comfortable seating", "Morning beverage (optional)"],
      "optimal_timing": "Within 30 minutes of waking, facing east if possible",
      "duration_guidance": "Start with 5 minutes, gradually increase as it becomes enjoyable"
    },
    "personalization": {
      "archetype_optimization": "As a Foundation Builder, focus on the comfort and ritual aspects. Make this feel nurturing rather than clinical. Let it become a cherished part of your morning rather than another task to complete.",
      "modifications": {
        "low_energy": "Just step outside with your morning drink - no specific duration required",
        "high_energy": "Combine with gentle stretching or gratitude journaling",
        "cloudy_days": "Even cloudy light is beneficial - focus on the gratitude practice",
        "winter": "Sit by the brightest window with a warm drink and cozy blanket"
      }
    }
  },

  "real_time_adaptations": {
    "current_status": "standard",
    "recent_adaptations": [],
    "adaptation_triggers": [
      "If stress > 0.7: Add extra gratitude focus",
      "If energy < 0.3: Reduce to 5 minutes window sitting",
      "If energy > 0.8: Add gentle morning walk option"
    ]
  },

  "success_tracking": {
    "completion_criteria": "Spent time in morning light with grateful awareness",
    "quality_indicators": ["Felt peaceful", "Noticed gratitude", "Enjoyed the experience"],
    "streak_bonuses": {
      "7_days": "Unlock: Morning mindfulness expansion options",
      "14_days": "Unlock: Partner morning ritual options",
      "30_days": "Unlock: Teaching this practice to others"
    }
  }
}
```

This advanced system would provide truly adaptive, educational, progressively challenging health optimization that evolves with the user while maintaining their archetype's core philosophy and communication style.