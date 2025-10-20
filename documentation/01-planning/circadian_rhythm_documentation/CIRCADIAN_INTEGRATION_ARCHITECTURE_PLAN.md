# Circadian Integration Architecture Plan: 7-Agent HolisticOS Enhancement

## Executive Summary

This plan details the transformation of the existing 6-agent HolisticOS system into a circadian-aware, energy-zone-optimized health platform by adding a 7th specialized agent that runs parallel to behavior analysis. Both agents will access raw health data to provide comprehensive analysis for optimal plan generation.

## Problem Statement

The current architecture only passes raw health data to the Behavior Analysis Agent, while all other agents work with processed results. For circadian rhythm and energy zone calculation, we need access to raw sleep data, timestamps, and activity patterns that get lost in the behavior analysis processing.

## Solution Overview

Add a Circadian Analysis Agent that runs parallel to Behavior Analysis, both accessing raw health data from the proven UserDataService pipeline. This maintains the working architecture while adding circadian intelligence.

---

## Current vs Enhanced Architecture

### Current Architecture (Working)
```
Raw Health Data → OnDemandAnalysisService → Behavior Agent → Memory Agent
                                                              ↓
                                                    Routine/Nutrition/Insights Agents
```

### Enhanced Architecture (Target)
```
Raw Health Data → OnDemandAnalysisService → Orchestrator
                                               ↙        ↘
                                    Behavior Agent   Circadian Agent
                                               ↘        ↙
                                            Memory Agent
                                               ↓
                                    Routine/Nutrition/Insights Agents
```

---

## Phase 1: Create Circadian Analysis Agent (Week 1)

### 1.1 New Agent Structure

**File: `services/agents/circadian/main.py`**

```python
"""
Circadian Analysis Agent - 7th Agent in HolisticOS Architecture
Analyzes raw health data for sleep patterns, chronotype, and energy zones
Runs parallel to Behavior Agent for optimal processing efficiency
"""

from shared_libs.event_system.base_agent import BaseAgent
from shared_libs.data_models.health_models import UserHealthContext
from shared_libs.utils.system_prompts import get_system_prompt
import openai
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple

class CircadianAnalysisAgent(BaseAgent):
    """
    Agent responsible for:
    1. Analyzing sleep/wake patterns from raw health data
    2. Determining chronotype (morning lark, evening owl, neutral)
    3. Calculating personalized energy zones throughout the day
    4. Providing circadian rhythm insights for plan optimization
    """

    def __init__(self):
        super().__init__()
        self.agent_name = "CircadianAnalysis"
        self.openai_client = openai.AsyncOpenAI()

    async def analyze_circadian_patterns(self, user_id: str, health_context: UserHealthContext) -> Dict[str, Any]:
        """
        Main analysis method that processes raw health data for circadian insights

        Input: Raw health data (sleep scores, activity patterns, timestamps)
        Output: Circadian analysis with sleep schedule and energy zones
        """

        # Phase 1: Extract raw sleep patterns
        sleep_data = await self._extract_sleep_patterns(health_context)
        activity_data = await self._extract_activity_patterns(health_context)
        biomarker_data = await self._extract_biomarker_trends(health_context)

        # Phase 2: AI-powered circadian analysis
        circadian_analysis = await self._analyze_with_openai(
            user_id=user_id,
            sleep_data=sleep_data,
            activity_data=activity_data,
            biomarkers=biomarker_data
        )

        # Phase 3: Calculate energy zones based on circadian patterns
        energy_zones = await self._calculate_energy_zones(
            wake_time=circadian_analysis["estimated_wake_time"],
            bedtime=circadian_analysis["estimated_bedtime"],
            chronotype=circadian_analysis["chronotype"],
            current_mode=circadian_analysis["detected_mode"]
        )

        # Phase 4: Package results
        return {
            "user_id": user_id,
            "analysis_timestamp": datetime.now(),
            "sleep_schedule": {
                "estimated_wake_time": circadian_analysis["estimated_wake_time"],
                "estimated_bedtime": circadian_analysis["estimated_bedtime"],
                "sleep_duration_avg": circadian_analysis["avg_sleep_duration"],
                "chronotype": circadian_analysis["chronotype"],
                "confidence_score": circadian_analysis["confidence_score"]
            },
            "energy_zones": energy_zones,
            "detected_mode": circadian_analysis["detected_mode"],
            "circadian_insights": circadian_analysis["insights"],
            "data_quality_score": sleep_data["quality_score"]
        }

    async def _extract_sleep_patterns(self, health_context: UserHealthContext) -> Dict[str, Any]:
        """
        Extract sleep timing patterns from raw health data

        Analyzes:
        - Sleep start/end times from raw data
        - Sleep duration patterns
        - Sleep quality trends
        - Weekly consistency patterns
        """
        sleep_patterns = {
            "sleep_times": [],
            "wake_times": [],
            "durations": [],
            "quality_scores": [],
            "consistency_score": 0.0,
            "quality_score": 0.0
        }

        # Extract from health_context.scores and health_context.raw_data
        if hasattr(health_context, 'scores') and health_context.scores:
            for score_entry in health_context.scores:
                if hasattr(score_entry, 'sleep_score') and score_entry.sleep_score:
                    # Extract sleep timing data
                    if hasattr(score_entry, 'date') and hasattr(score_entry, 'sleep_start'):
                        sleep_patterns["sleep_times"].append({
                            "date": score_entry.date,
                            "sleep_start": score_entry.sleep_start,
                            "sleep_end": getattr(score_entry, 'sleep_end', None),
                            "duration": getattr(score_entry, 'sleep_duration', None),
                            "quality": score_entry.sleep_score
                        })

        # Calculate patterns
        sleep_patterns["consistency_score"] = self._calculate_sleep_consistency(sleep_patterns["sleep_times"])
        sleep_patterns["quality_score"] = self._calculate_data_quality(sleep_patterns)

        return sleep_patterns

    async def _extract_activity_patterns(self, health_context: UserHealthContext) -> Dict[str, Any]:
        """
        Extract activity patterns that indicate circadian preferences

        Analyzes:
        - Peak activity times
        - Energy level throughout day
        - Exercise timing preferences
        - Productivity patterns
        """
        activity_patterns = {
            "peak_activity_times": [],
            "energy_levels_by_hour": {},
            "exercise_preferences": {},
            "productivity_windows": []
        }

        # Extract activity data from health context
        if hasattr(health_context, 'scores') and health_context.scores:
            for score_entry in health_context.scores:
                if hasattr(score_entry, 'activity_score') and score_entry.activity_score:
                    # Extract activity timing and intensity
                    activity_patterns["peak_activity_times"].append({
                        "date": getattr(score_entry, 'date', None),
                        "activity_score": score_entry.activity_score,
                        "peak_time": getattr(score_entry, 'peak_activity_time', None)
                    })

        return activity_patterns

    async def _extract_biomarker_trends(self, health_context: UserHealthContext) -> Dict[str, Any]:
        """Extract biomarker trends relevant to circadian rhythm"""
        biomarker_trends = {
            "hrv_patterns": [],
            "readiness_trends": [],
            "recovery_patterns": [],
            "stress_indicators": []
        }

        # Extract biomarker data
        if hasattr(health_context, 'scores') and health_context.scores:
            for score_entry in health_context.scores:
                biomarker_entry = {
                    "date": getattr(score_entry, 'date', None),
                    "readiness_score": getattr(score_entry, 'readiness_score', None),
                    "hrv_score": getattr(score_entry, 'hrv_score', None),
                    "recovery_score": getattr(score_entry, 'recovery_score', None)
                }

                if any(biomarker_entry.values()):
                    biomarker_trends["hrv_patterns"].append(biomarker_entry)

        return biomarker_trends

    async def _analyze_with_openai(self, user_id: str, sleep_data: Dict, activity_data: Dict, biomarkers: Dict) -> Dict[str, Any]:
        """Use OpenAI to analyze circadian patterns and determine optimal timing"""

        system_prompt = get_system_prompt("circadian_analysis")

        analysis_prompt = f"""
        Analyze this user's circadian rhythm patterns and determine optimal energy zones:

        Sleep Data: {sleep_data}
        Activity Data: {activity_data}
        Biomarkers: {biomarkers}

        Provide analysis in JSON format with:
        1. estimated_wake_time (HH:MM format)
        2. estimated_bedtime (HH:MM format)
        3. chronotype ("morning_lark", "evening_owl", "neutral")
        4. detected_mode ("recovery", "productive", "performance")
        5. confidence_score (0.0-1.0)
        6. avg_sleep_duration (hours)
        7. insights (array of key findings)
        """

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3
        )

        # Parse and structure the response
        return self._parse_circadian_response(response.choices[0].message.content)

    async def _calculate_energy_zones(self, wake_time: time, bedtime: time, chronotype: str, current_mode: str) -> List[Dict[str, Any]]:
        """
        Calculate personalized energy zones based on circadian analysis

        Energy Zones:
        - Foundation: Morning activation (first 1-2 hours after wake)
        - Peak: Optimal performance window
        - Maintenance: Sustained activity period
        - Recovery: Wind-down and restoration
        """

        zones = []

        # Convert wake_time to datetime for calculations
        wake_datetime = datetime.combine(datetime.today(), wake_time)

        # Zone definitions based on chronotype and mode
        zone_templates = self._get_zone_templates(chronotype, current_mode)

        for template in zone_templates:
            start_time = wake_datetime + timedelta(hours=template["start_offset_hours"])
            end_time = start_time + timedelta(hours=template["duration_hours"])

            zone = {
                "zone_name": template["zone_name"],
                "start_time": start_time.time().strftime("%H:%M"),
                "end_time": end_time.time().strftime("%H:%M"),
                "energy_level": template["energy_level"],
                "intensity_level": template["intensity_level"],
                "optimal_activities": template["optimal_activities"],
                "description": template["description"],
                "start_offset_hours": template["start_offset_hours"],
                "duration_hours": template["duration_hours"]
            }

            zones.append(zone)

        return zones

    def _get_zone_templates(self, chronotype: str, current_mode: str) -> List[Dict[str, Any]]:
        """Get energy zone templates based on chronotype and current mode"""

        templates = {
            "morning_lark": {
                "recovery": [
                    {"zone_name": "foundation", "start_offset_hours": 0.0, "duration_hours": 2.0, "energy_level": 40, "intensity_level": "low", "optimal_activities": ["gentle_movement", "hydration", "breathing"], "description": "Gentle awakening and basic needs"},
                    {"zone_name": "peak", "start_offset_hours": 2.0, "duration_hours": 2.0, "energy_level": 60, "intensity_level": "moderate", "optimal_activities": ["light_tasks", "reading", "gentle_focus"], "description": "Best available cognitive window"},
                    {"zone_name": "maintenance", "start_offset_hours": 4.0, "duration_hours": 4.0, "energy_level": 45, "intensity_level": "low", "optimal_activities": ["routine_tasks", "light_activity", "maintenance"], "description": "Steady, gentle progress"},
                    {"zone_name": "recovery", "start_offset_hours": 12.0, "duration_hours": 2.0, "energy_level": 30, "intensity_level": "low", "optimal_activities": ["rest", "gentle_stretching", "preparation"], "description": "Wind-down and restoration"}
                ],
                "productive": [
                    {"zone_name": "foundation", "start_offset_hours": 0.0, "duration_hours": 1.5, "energy_level": 60, "intensity_level": "moderate", "optimal_activities": ["light_exercise", "planning", "nutrition"], "description": "Standard morning routine"},
                    {"zone_name": "peak", "start_offset_hours": 1.5, "duration_hours": 2.5, "energy_level": 80, "intensity_level": "high", "optimal_activities": ["focus_work", "problem_solving", "creativity"], "description": "Prime cognitive performance"},
                    {"zone_name": "maintenance", "start_offset_hours": 4.0, "duration_hours": 4.0, "energy_level": 65, "intensity_level": "moderate", "optimal_activities": ["steady_work", "communication", "moderate_activity"], "description": "Sustained productive activity"},
                    {"zone_name": "recovery", "start_offset_hours": 12.0, "duration_hours": 1.5, "energy_level": 50, "intensity_level": "low", "optimal_activities": ["reflection", "light_prep", "relaxation"], "description": "Gentle evening routine"}
                ],
                "performance": [
                    {"zone_name": "foundation", "start_offset_hours": 0.0, "duration_hours": 1.0, "energy_level": 75, "intensity_level": "moderate", "optimal_activities": ["dynamic_warmup", "goal_setting", "optimization"], "description": "High-energy morning activation"},
                    {"zone_name": "peak", "start_offset_hours": 1.0, "duration_hours": 3.0, "energy_level": 90, "intensity_level": "high", "optimal_activities": ["strategic_work", "complex_tasks", "peak_performance"], "description": "Maximum cognitive output"},
                    {"zone_name": "maintenance", "start_offset_hours": 4.0, "duration_hours": 4.0, "energy_level": 75, "intensity_level": "moderate", "optimal_activities": ["project_work", "collaboration", "training"], "description": "Sustained high performance"},
                    {"zone_name": "recovery", "start_offset_hours": 12.0, "duration_hours": 1.0, "energy_level": 60, "intensity_level": "low", "optimal_activities": ["review", "optimization", "recovery_protocols"], "description": "Structured recovery and preparation"}
                ]
            }
            # Add similar templates for "evening_owl" and "neutral" chronotypes
        }

        return templates.get(chronotype, {}).get(current_mode, templates["morning_lark"]["productive"])

    def _calculate_sleep_consistency(self, sleep_times: List[Dict]) -> float:
        """Calculate sleep timing consistency score"""
        if len(sleep_times) < 3:
            return 0.5  # Default for insufficient data

        # Calculate variance in sleep start times
        # Implementation details...
        return 0.8  # Placeholder

    def _calculate_data_quality(self, sleep_patterns: Dict) -> float:
        """Calculate overall data quality score"""
        # Implementation details...
        return 0.7  # Placeholder

    def _parse_circadian_response(self, response_content: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured circadian analysis"""
        try:
            # Attempt to parse JSON from response
            import json
            import re

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_str = response_content

            parsed = json.loads(json_str)

            # Validate required fields
            required_fields = ["estimated_wake_time", "estimated_bedtime", "chronotype", "detected_mode", "confidence_score"]
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = self._get_default_value(field)

            return parsed

        except (json.JSONDecodeError, AttributeError) as e:
            # Fallback parsing or default values
            return {
                "estimated_wake_time": "07:00",
                "estimated_bedtime": "22:00",
                "chronotype": "neutral",
                "detected_mode": "productive",
                "confidence_score": 0.5,
                "avg_sleep_duration": 8.0,
                "insights": ["Analysis based on limited data - confidence is moderate"]
            }

    def _get_default_value(self, field: str) -> Any:
        """Get default values for missing fields"""
        defaults = {
            "estimated_wake_time": "07:00",
            "estimated_bedtime": "22:00",
            "chronotype": "neutral",
            "detected_mode": "productive",
            "confidence_score": 0.5,
            "avg_sleep_duration": 8.0,
            "insights": []
        }
        return defaults.get(field, None)
```

### 1.2 System Prompts Extension

**File: `shared_libs/utils/system_prompts.py` (extend existing)**

```python
# Add to existing system prompts dictionary

CIRCADIAN_ANALYSIS_PROMPT = """
You are a circadian rhythm and chronobiology expert analyzing user health data to determine optimal energy patterns.

Your responsibilities:
1. Analyze sleep timing patterns from health data
2. Determine chronotype based on natural preferences and biomarkers
3. Detect current energy mode (recovery/productive/performance)
4. Calculate optimal energy zones throughout the day
5. Provide confidence scores for all assessments

Analysis Framework:
- Morning Lark: Natural early risers, peak energy 6-10 AM, prefer early bedtime
- Evening Owl: Natural late sleepers, peak energy 6-10 PM, prefer late bedtime
- Neutral: Flexible timing, peak energy 10 AM-2 PM, adaptable schedule

Energy Modes:
- Recovery: Focus on restoration, lower intensity zones, prioritize sleep quality
- Productive: Standard energy distribution, balanced activity periods
- Performance: Enhanced peak zones, optimized timing, maximum output windows

Chronotype Indicators:
- Sleep timing consistency
- Natural wake times without alarm
- Peak performance periods
- Energy level patterns throughout day
- Activity preferences and timing

Energy Zone Framework:
1. Foundation Zone: Morning activation period (1-2 hours post-wake)
2. Peak Zone: Optimal cognitive/physical performance window
3. Maintenance Zone: Sustained activity and productivity period
4. Recovery Zone: Wind-down and restoration preparation

Output Format:
Respond with valid JSON containing:
- estimated_wake_time: "HH:MM" format
- estimated_bedtime: "HH:MM" format
- chronotype: "morning_lark" | "evening_owl" | "neutral"
- detected_mode: "recovery" | "productive" | "performance"
- confidence_score: 0.0-1.0 based on data quality and consistency
- avg_sleep_duration: hours as float
- insights: array of 2-4 key findings about the user's circadian patterns

Base your analysis on sleep timing patterns, activity levels, biomarker trends, and consistency of daily rhythms.
"""

# Update the get_system_prompt function
def get_system_prompt(prompt_type: str) -> str:
    """Enhanced system prompt retrieval including circadian analysis"""
    prompts = {
        # ... existing prompts ...
        "circadian_analysis": CIRCADIAN_ANALYSIS_PROMPT,
        "routine_zone_alignment": ROUTINE_ZONE_ALIGNMENT_PROMPT  # Define below
    }

    return prompts.get(prompt_type, prompts.get("behavior_analysis"))

ROUTINE_ZONE_ALIGNMENT_PROMPT = """
You are an expert in optimizing daily routines based on personal energy zones and circadian rhythms.

Your task is to align routine activities with the user's optimal energy windows for maximum effectiveness and natural flow.

Guidelines:
1. Match high-energy activities with peak energy zones
2. Place recovery activities in low-energy periods
3. Respect the user's archetype preferences and communication style
4. Maintain realistic timing and transitions between activities
5. Provide specific timing recommendations based on energy zones

Energy Zone Optimization:
- Foundation Zone: Gentle activation, basic needs, preparation
- Peak Zone: Most demanding cognitive/physical tasks, important decisions
- Maintenance Zone: Steady work, routine tasks, moderate activities
- Recovery Zone: Reflection, preparation, wind-down activities

Consider:
- Natural energy flow and transitions
- Practical constraints and daily responsibilities
- User's archetype-specific needs and preferences
- Buffer time between high-intensity activities
- Circadian rhythm support (light exposure, meal timing)

Output:
Provide an optimized routine plan that naturally flows with the user's energy patterns, including specific timing recommendations and rationale for activity placement.
"""
```

---

## Phase 2: Modify Orchestrator for Parallel Processing (Week 2)

### 2.1 Enhanced Orchestrator

**File: `services/orchestrator/main.py` (modify existing)**

```python
class HolisticOrchestrator(BaseAgent):
    """
    Enhanced orchestrator that coordinates 7 agents including parallel
    Behavior Analysis and Circadian Analysis
    """

    def __init__(self):
        super().__init__()
        # ... existing initialization ...

        # Add new circadian agent
        from services.agents.circadian.main import CircadianAnalysisAgent
        self.circadian_agent = CircadianAnalysisAgent()

        # Update workflow stages
        self.workflow_stages.append(WorkflowStage.CIRCADIAN_ANALYSIS)
        self.workflow_stages.append(WorkflowStage.PARALLEL_ANALYSIS)

    async def orchestrate_complete_analysis(self, user_id: str, archetype: str = "Foundation Builder") -> Dict[str, Any]:
        """
        Enhanced complete analysis workflow with parallel processing
        """

        self.workflow_state.current_stage = WorkflowStage.STARTED
        workflow_id = f"analysis_{user_id}_{int(datetime.now().timestamp())}"

        try:
            # Step 1: Get raw health data (existing working method)
            logger.info(f"[{workflow_id}] Fetching health data for user {user_id}")
            health_context, latest_timestamp = await self.user_service.get_analysis_data(user_id)

            if not health_context:
                return {
                    "success": False,
                    "error": "No health data available",
                    "workflow_id": workflow_id
                }

            # Step 2: Run Behavior and Circadian Analysis in PARALLEL
            logger.info(f"[{workflow_id}] Starting parallel behavior and circadian analysis for user {user_id}")
            self.workflow_state.current_stage = WorkflowStage.PARALLEL_ANALYSIS

            # Create parallel tasks
            behavior_task = asyncio.create_task(
                self._run_behavior_analysis(user_id, health_context, archetype)
            )
            circadian_task = asyncio.create_task(
                self.circadian_agent.analyze_circadian_patterns(user_id, health_context)
            )

            # Wait for both analyses to complete with timeout
            try:
                behavior_result, circadian_result = await asyncio.wait_for(
                    asyncio.gather(behavior_task, circadian_task, return_exceptions=True),
                    timeout=120.0  # 2 minute timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"[{workflow_id}] Parallel analysis timed out")
                return {
                    "success": False,
                    "error": "Analysis timed out",
                    "workflow_id": workflow_id
                }

            # Handle any errors in parallel processing
            analysis_success = True
            if isinstance(behavior_result, Exception):
                logger.error(f"[{workflow_id}] Behavior analysis failed: {behavior_result}")
                behavior_result = {"error": str(behavior_result), "success": False}
                analysis_success = False

            if isinstance(circadian_result, Exception):
                logger.error(f"[{workflow_id}] Circadian analysis failed: {circadian_result}")
                circadian_result = {"error": str(circadian_result), "success": False}
                # Don't fail entire workflow if circadian fails - it's supplementary

            if not analysis_success:
                return {
                    "success": False,
                    "error": "Behavior analysis failed",
                    "workflow_id": workflow_id,
                    "behavior_result": behavior_result
                }

            # Step 3: Store both results in memory
            self.workflow_state.current_stage = WorkflowStage.MEMORY_STORAGE
            logger.info(f"[{workflow_id}] Storing analysis results in memory")

            memory_storage_tasks = [
                self.memory_agent.store_behavior_analysis(user_id, behavior_result),
            ]

            # Only store circadian data if analysis was successful
            if not isinstance(circadian_result, Exception) and not circadian_result.get("error"):
                memory_storage_tasks.append(
                    self.memory_agent.store_circadian_analysis(user_id, circadian_result)
                )

            await asyncio.gather(*memory_storage_tasks, return_exceptions=True)

            # Step 4: Continue with existing workflow - Generate insights
            self.workflow_state.current_stage = WorkflowStage.INSIGHTS_GENERATION
            logger.info(f"[{workflow_id}] Generating insights with combined analysis data")

            insights_result = await self._run_insights_generation(user_id)

            # Step 5: Store insights and return complete results
            await self.memory_agent.store_insights(user_id, insights_result)

            self.workflow_state.current_stage = WorkflowStage.COMPLETED

            # Prepare comprehensive response
            response = {
                "success": True,
                "workflow_id": workflow_id,
                "behavior_analysis": behavior_result,
                "insights": insights_result,
                "timestamp": latest_timestamp,
                "processing_time": self._calculate_processing_time(),
                "data_points_analyzed": len(health_context.scores) if health_context.scores else 0
            }

            # Include circadian analysis if successful
            if not isinstance(circadian_result, Exception) and not circadian_result.get("error"):
                response["circadian_analysis"] = circadian_result
                response["energy_zones_available"] = True
            else:
                response["energy_zones_available"] = False
                response["circadian_note"] = "Circadian analysis not available - using standard scheduling"

            logger.info(f"[{workflow_id}] Complete analysis finished successfully")
            return response

        except Exception as e:
            logger.error(f"[{workflow_id}] Orchestration failed for user {user_id}: {e}")
            self.workflow_state.current_stage = WorkflowStage.FAILED
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }

    async def _run_behavior_analysis(self, user_id: str, health_context: UserHealthContext, archetype: str) -> Dict[str, Any]:
        """
        Existing behavior analysis method (unchanged)
        Kept for reference - this is your working implementation
        """
        # Keep existing implementation exactly as is
        # This method already works and should not be modified
        pass

    async def _run_insights_generation(self, user_id: str) -> Dict[str, Any]:
        """
        Enhanced insights generation that can use both behavior and circadian data
        """
        try:
            # Get both analysis types from memory
            combined_data = await self.memory_agent.get_combined_analysis(user_id)

            # Generate insights using available data
            insights_result = await self.insights_agent.generate_insights(
                user_id=user_id,
                behavior_data=combined_data.get("behavior_analysis"),
                circadian_data=combined_data.get("circadian_analysis")
            )

            return insights_result

        except Exception as e:
            logger.error(f"Insights generation failed for user {user_id}: {e}")
            return {"error": str(e), "success": False}

    def _calculate_processing_time(self) -> float:
        """Calculate total processing time for workflow"""
        if hasattr(self.workflow_state, 'start_time'):
            return (datetime.now() - self.workflow_state.start_time).total_seconds()
        return 0.0
```

### 2.2 Workflow State Updates

```python
class WorkflowStage(Enum):
    """Enhanced workflow stages including circadian analysis"""
    STARTED = "started"
    DATA_FETCHING = "data_fetching"
    PARALLEL_ANALYSIS = "parallel_analysis"      # New: Both analyses running
    BEHAVIOR_ANALYSIS = "behavior_analysis"      # Individual analysis stages
    CIRCADIAN_ANALYSIS = "circadian_analysis"    # for detailed tracking
    MEMORY_STORAGE = "memory_storage"
    PLAN_GENERATION = "plan_generation"
    INSIGHTS_GENERATION = "insights_generation"
    STRATEGY_ADAPTATION = "strategy_adaptation"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowState:
    """Enhanced workflow state tracking"""
    def __init__(self, user_id: str, archetype: str, workflow_id: str):
        self.user_id = user_id
        self.archetype = archetype
        self.workflow_id = workflow_id
        self.current_stage = WorkflowStage.STARTED
        self.start_time = datetime.now()
        self.stage_history = []
        self.error_messages = []

        # Parallel processing tracking
        self.behavior_analysis_status = "pending"
        self.circadian_analysis_status = "pending"

    def update_stage(self, new_stage: WorkflowStage, details: str = ""):
        """Update workflow stage with history tracking"""
        self.stage_history.append({
            "stage": self.current_stage.value,
            "timestamp": datetime.now(),
            "details": details
        })
        self.current_stage = new_stage

    def set_analysis_status(self, analysis_type: str, status: str):
        """Track individual analysis completion"""
        if analysis_type == "behavior":
            self.behavior_analysis_status = status
        elif analysis_type == "circadian":
            self.circadian_analysis_status = status

    def is_parallel_analysis_complete(self) -> bool:
        """Check if both parallel analyses are complete"""
        return (self.behavior_analysis_status in ["completed", "failed"] and
                self.circadian_analysis_status in ["completed", "failed"])
```

---

## Phase 3: Extend Memory Agent for Circadian Data (Week 3)

### 3.1 Memory Agent Extensions

**File: `services/agents/memory/main.py` (extend existing)**

```python
class HolisticMemoryAgent(BaseAgent):
    """
    Enhanced memory agent that stores and retrieves both
    behavior analysis and circadian analysis results
    """

    # ... existing methods remain unchanged ...

    async def store_circadian_analysis(self, user_id: str, circadian_data: Dict[str, Any]) -> bool:
        """
        Store circadian analysis results in procedural memory

        Circadian data includes:
        - Sleep schedule (wake/bedtime)
        - Chronotype classification
        - Energy zones
        - Detected mode
        - Confidence scores
        """
        try:
            # Prepare circadian memory data
            memory_data = {
                "type": "circadian_analysis",
                "timestamp": datetime.now(),
                "analysis_data": circadian_data,
                "sleep_schedule": circadian_data.get("sleep_schedule", {}),
                "energy_zones": circadian_data.get("energy_zones", []),
                "detected_mode": circadian_data.get("detected_mode", "productive"),
                "chronotype": circadian_data.get("sleep_schedule", {}).get("chronotype", "neutral"),
                "confidence_score": circadian_data.get("confidence_score", 0.5),
                "data_quality": circadian_data.get("data_quality_score", 0.5)
            }

            # Store in procedural memory (existing table structure)
            await self.memory_service.store_memory(
                user_id=user_id,
                memory_type="procedural",
                memory_data=memory_data,
                memory_key="circadian_patterns"
            )

            # Also store a simplified version in working memory for quick access
            working_memory_data = {
                "type": "current_energy_zones",
                "timestamp": datetime.now(),
                "wake_time": circadian_data.get("sleep_schedule", {}).get("estimated_wake_time"),
                "bedtime": circadian_data.get("sleep_schedule", {}).get("estimated_bedtime"),
                "current_mode": circadian_data.get("detected_mode"),
                "zones_summary": {
                    zone["zone_name"]: {
                        "start": zone["start_time"],
                        "end": zone["end_time"],
                        "energy_level": zone["energy_level"]
                    }
                    for zone in circadian_data.get("energy_zones", [])
                }
            }

            await self.memory_service.store_memory(
                user_id=user_id,
                memory_type="working",
                memory_data=working_memory_data,
                memory_key="current_energy_state"
            )

            logger.info(f"Stored circadian analysis for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store circadian analysis for user {user_id}: {e}")
            return False

    async def get_circadian_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve latest circadian analysis for user"""
        try:
            circadian_memory = await self.memory_service.get_memory(
                user_id, "procedural", "circadian_patterns"
            )

            if circadian_memory and "analysis_data" in circadian_memory:
                return circadian_memory["analysis_data"]

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve circadian data for user {user_id}: {e}")
            return None

    async def get_combined_analysis(self, user_id: str) -> Dict[str, Any]:
        """
        Get both behavior and circadian analysis for comprehensive planning
        This method is used by routine/nutrition agents
        """
        try:
            # Get both analysis types
            behavior_data = await self.get_behavior_analysis(user_id)
            circadian_data = await self.get_circadian_data(user_id)

            return {
                "behavior_analysis": behavior_data,
                "circadian_analysis": circadian_data,
                "combined_timestamp": datetime.now(),
                "has_behavior_data": behavior_data is not None,
                "has_circadian_data": circadian_data is not None
            }

        except Exception as e:
            logger.error(f"Failed to retrieve combined analysis for user {user_id}: {e}")
            return {
                "behavior_analysis": None,
                "circadian_analysis": None,
                "error": str(e)
            }

    async def get_energy_zones_for_planning(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Specialized method to get energy zones data formatted for plan generation
        Used by routine and nutrition agents
        """
        try:
            circadian_data = await self.get_circadian_data(user_id)

            if not circadian_data or not circadian_data.get("energy_zones"):
                return None

            # Format energy zones for easy consumption by planning agents
            zones = circadian_data["energy_zones"]
            sleep_schedule = circadian_data.get("sleep_schedule", {})

            # Create zone lookup for easy access
            zone_lookup = {}
            for zone in zones:
                zone_lookup[zone["zone_name"]] = zone

            return {
                "zones": zone_lookup,
                "foundation_zone": zone_lookup.get("foundation"),
                "peak_zone": zone_lookup.get("peak"),
                "maintenance_zone": zone_lookup.get("maintenance"),
                "recovery_zone": zone_lookup.get("recovery"),
                "detected_mode": circadian_data.get("detected_mode"),
                "wake_time": sleep_schedule.get("estimated_wake_time"),
                "bedtime": sleep_schedule.get("estimated_bedtime"),
                "chronotype": sleep_schedule.get("chronotype"),
                "confidence_score": circadian_data.get("confidence_score", 0.5),
                "formatted_for_planning": True
            }

        except Exception as e:
            logger.error(f"Failed to get energy zones for planning for user {user_id}: {e}")
            return None

    async def get_current_energy_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current energy zone status for real-time queries"""
        try:
            working_memory = await self.memory_service.get_memory(
                user_id, "working", "current_energy_state"
            )

            if not working_memory:
                return None

            current_time = datetime.now().time()
            zones_summary = working_memory.get("zones_summary", {})

            # Find current active zone
            active_zone = None
            for zone_name, zone_info in zones_summary.items():
                start_time = datetime.strptime(zone_info["start"], "%H:%M").time()
                end_time = datetime.strptime(zone_info["end"], "%H:%M").time()

                if start_time <= current_time <= end_time:
                    active_zone = {
                        "zone_name": zone_name,
                        "energy_level": zone_info["energy_level"],
                        "start_time": zone_info["start"],
                        "end_time": zone_info["end"]
                    }
                    break

            return {
                "user_id": user_id,
                "current_time": current_time.strftime("%H:%M"),
                "active_zone": active_zone,
                "current_mode": working_memory.get("current_mode"),
                "wake_time": working_memory.get("wake_time"),
                "bedtime": working_memory.get("bedtime")
            }

        except Exception as e:
            logger.error(f"Failed to get current energy state for user {user_id}: {e}")
            return None

    async def store_energy_zone_feedback(self, user_id: str, zone_feedback: Dict[str, Any]) -> bool:
        """
        Store user feedback about energy zone accuracy
        This helps improve future circadian analysis
        """
        try:
            feedback_data = {
                "type": "energy_zone_feedback",
                "timestamp": datetime.now(),
                "zone_name": zone_feedback.get("zone_name"),
                "actual_energy_level": zone_feedback.get("actual_energy_level"),
                "predicted_energy_level": zone_feedback.get("predicted_energy_level"),
                "accuracy_rating": zone_feedback.get("accuracy_rating"),
                "user_notes": zone_feedback.get("user_notes", "")
            }

            # Store in episodic memory for learning
            await self.memory_service.store_memory(
                user_id=user_id,
                memory_type="episodic",
                memory_data=feedback_data,
                memory_key=f"zone_feedback_{int(datetime.now().timestamp())}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to store energy zone feedback for user {user_id}: {e}")
            return False
```

### 3.2 Memory Service Extensions

**File: `services/agents/memory/holistic_memory_service.py` (extend existing)**

```python
class HolisticMemoryService:
    """
    Enhanced memory service with circadian data management
    """

    # ... existing methods remain unchanged ...

    async def get_circadian_learning_data(self, user_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical circadian data for learning and improvement
        Used by adaptation agent to improve future predictions
        """
        try:
            # Get episodic memories related to energy zone feedback
            feedback_memories = await self.get_memories_by_pattern(
                user_id, "episodic", "zone_feedback_"
            )

            # Get historical circadian analyses from procedural memory
            circadian_memories = await self.get_memory_history(
                user_id, "procedural", "circadian_patterns", days_back
            )

            return {
                "feedback_data": feedback_memories,
                "historical_analyses": circadian_memories,
                "learning_period_days": days_back
            }

        except Exception as e:
            logger.error(f"Failed to get circadian learning data for user {user_id}: {e}")
            return []

    async def update_circadian_confidence(self, user_id: str, new_confidence: float, reason: str = "") -> bool:
        """
        Update confidence score for circadian analysis based on feedback or performance
        """
        try:
            # Get current circadian data
            current_data = await self.get_memory(user_id, "procedural", "circadian_patterns")

            if current_data and "analysis_data" in current_data:
                # Update confidence score
                current_data["analysis_data"]["confidence_score"] = new_confidence
                current_data["confidence_update_reason"] = reason
                current_data["confidence_update_timestamp"] = datetime.now()

                # Store updated data
                await self.store_memory(
                    user_id=user_id,
                    memory_type="procedural",
                    memory_data=current_data,
                    memory_key="circadian_patterns"
                )

                return True

        except Exception as e:
            logger.error(f"Failed to update circadian confidence for user {user_id}: {e}")

        return False

    async def get_memories_by_pattern(self, user_id: str, memory_type: str, pattern: str) -> List[Dict[str, Any]]:
        """Get memories matching a pattern (for feedback data retrieval)"""
        # Implementation depends on your existing memory storage structure
        # This would query memories where memory_key starts with pattern
        pass

    async def get_memory_history(self, user_id: str, memory_type: str, memory_key: str, days_back: int) -> List[Dict[str, Any]]:
        """Get historical versions of a memory for trend analysis"""
        # Implementation depends on your existing memory versioning
        # This would retrieve past versions of circadian analyses
        pass
```

---

## Phase 4: Update Plan Generation Agents (Week 4)

### 4.1 Enhanced Routine Agent

**File: `services/agents/routine/main.py` (extend existing)**

```python
class RoutineAgent(BaseAgent):
    """
    Enhanced routine agent that generates plans using both
    behavior analysis and circadian/energy zone data
    """

    def __init__(self):
        super().__init__()
        # ... existing initialization ...

    async def generate_routine_with_zones(self, user_id: str, archetype: str) -> Dict[str, Any]:
        """
        Generate routine plan optimized for user's energy zones
        This is the new enhanced method that uses both behavior and circadian data
        """
        try:
            # Get comprehensive analysis data from memory
            analysis_data = await self.memory_agent.get_combined_analysis(user_id)
            behavior_data = analysis_data.get("behavior_analysis")
            circadian_data = analysis_data.get("circadian_analysis")

            if not behavior_data:
                return {"error": "No behavior analysis available - please run complete analysis first"}

            # Generate base routine using existing behavior analysis
            logger.info(f"Generating base routine for user {user_id} with archetype {archetype}")
            base_routine = await self._generate_base_routine(user_id, archetype, behavior_data)

            # If circadian data available, enhance with energy zones
            if circadian_data and circadian_data.get("energy_zones"):
                logger.info(f"Enhancing routine with energy zones for user {user_id}")
                enhanced_routine = await self._align_routine_with_energy_zones(
                    base_routine=base_routine,
                    energy_zones=circadian_data["energy_zones"],
                    sleep_schedule=circadian_data.get("sleep_schedule"),
                    detected_mode=circadian_data.get("detected_mode", "productive"),
                    archetype=archetype
                )

                return {
                    "success": True,
                    "routine_plan": enhanced_routine["routine_plan"],
                    "energy_zones": circadian_data["energy_zones"],
                    "detected_mode": circadian_data.get("detected_mode"),
                    "sleep_schedule": circadian_data.get("sleep_schedule"),
                    "zone_alignment": enhanced_routine["alignment_details"],
                    "archetype": archetype,
                    "enhancement_type": "energy_zone_optimized",
                    "confidence_score": circadian_data.get("confidence_score", 0.5)
                }
            else:
                # Fallback to standard routine if no circadian data
                logger.info(f"No circadian data available for user {user_id}, using standard routine")
                return {
                    "success": True,
                    "routine_plan": base_routine["routine_plan"],
                    "archetype": archetype,
                    "enhancement_type": "behavior_analysis_only",
                    "note": "Generated without energy zone optimization - circadian analysis not available"
                }

        except Exception as e:
            logger.error(f"Routine generation failed for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def generate_routine(self, user_id: str, archetype: str) -> Dict[str, Any]:
        """
        Standard routine generation method (existing - backwards compatibility)
        This maintains compatibility with existing API endpoints
        """
        # Keep existing implementation unchanged for backwards compatibility
        # This calls the original routine generation logic
        return await self._generate_base_routine(user_id, archetype, None)

    async def _generate_base_routine(self, user_id: str, archetype: str, behavior_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate base routine using behavior analysis
        This is your existing working implementation - keep it exactly as is
        """
        # Keep existing implementation unchanged
        # This method already works and generates good routines
        pass

    async def _align_routine_with_energy_zones(
        self,
        base_routine: Dict,
        energy_zones: List[Dict],
        sleep_schedule: Dict,
        detected_mode: str,
        archetype: str
    ) -> Dict[str, Any]:
        """
        Align routine activities with optimal energy zones
        This is the new enhancement that adds energy zone intelligence
        """

        # Prepare zone information for AI analysis
        zone_info = {
            "foundation_zone": next((z for z in energy_zones if z["zone_name"] == "foundation"), None),
            "peak_zone": next((z for z in energy_zones if z["zone_name"] == "peak"), None),
            "maintenance_zone": next((z for z in energy_zones if z["zone_name"] == "maintenance"), None),
            "recovery_zone": next((z for z in energy_zones if z["zone_name"] == "recovery"), None)
        }

        # Use OpenAI to intelligently align routine with energy zones
        system_prompt = get_system_prompt("routine_zone_alignment")

        alignment_prompt = f"""
        Optimize this routine plan for the user's personal energy zones and circadian rhythm:

        ORIGINAL ROUTINE:
        {base_routine.get("routine_plan", "")}

        USER'S ENERGY ZONES:
        - Foundation Zone ({zone_info["foundation_zone"]["start_time"]} - {zone_info["foundation_zone"]["end_time"]}): Energy Level {zone_info["foundation_zone"]["energy_level"]}/100
          Best for: {", ".join(zone_info["foundation_zone"]["optimal_activities"])}

        - Peak Zone ({zone_info["peak_zone"]["start_time"]} - {zone_info["peak_zone"]["end_time"]}): Energy Level {zone_info["peak_zone"]["energy_level"]}/100
          Best for: {", ".join(zone_info["peak_zone"]["optimal_activities"])}

        - Maintenance Zone ({zone_info["maintenance_zone"]["start_time"]} - {zone_info["maintenance_zone"]["end_time"]}): Energy Level {zone_info["maintenance_zone"]["energy_level"]}/100
          Best for: {", ".join(zone_info["maintenance_zone"]["optimal_activities"])}

        - Recovery Zone ({zone_info["recovery_zone"]["start_time"]} - {zone_info["recovery_zone"]["end_time"]}): Energy Level {zone_info["recovery_zone"]["energy_level"]}/100
          Best for: {", ".join(zone_info["recovery_zone"]["optimal_activities"])}

        SLEEP SCHEDULE:
        - Wake Time: {sleep_schedule.get("estimated_wake_time", "Unknown")}
        - Bedtime: {sleep_schedule.get("estimated_bedtime", "Unknown")}
        - Chronotype: {sleep_schedule.get("chronotype", "neutral")}

        USER PROFILE:
        - Archetype: {archetype}
        - Current Mode: {detected_mode}

        OPTIMIZATION INSTRUCTIONS:
        1. Move high-energy activities (exercise, challenging work, important decisions) to Peak Zone
        2. Place gentle activities (stretching, meditation, easy tasks) in Foundation and Recovery Zones
        3. Put steady work and routine tasks in Maintenance Zone
        4. Ensure natural flow and realistic transitions between activities
        5. Maintain the archetype-specific language and approach from the original routine
        6. Provide specific time recommendations based on the energy zones
        7. Keep the total routine structure and length similar to the original

        Provide the optimized routine plan that flows naturally with this user's energy patterns.
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": alignment_prompt}
                ],
                temperature=0.3
            )

            optimized_routine = response.choices[0].message.content

            # Generate alignment summary for user feedback
            alignment_details = self._generate_alignment_summary(
                energy_zones, sleep_schedule, detected_mode
            )

            return {
                "routine_plan": optimized_routine,
                "alignment_details": alignment_details
            }

        except Exception as e:
            logger.error(f"Failed to align routine with energy zones: {e}")
            # Fallback to original routine
            return {
                "routine_plan": base_routine.get("routine_plan", ""),
                "alignment_details": "Energy zone alignment failed - using standard routine"
            }

    def _generate_alignment_summary(self, energy_zones: List[Dict], sleep_schedule: Dict, detected_mode: str) -> str:
        """Generate a summary of how the routine was aligned with energy zones"""

        summary_parts = [
            f"Routine optimized for your {sleep_schedule.get('chronotype', 'neutral')} chronotype",
            f"Current mode: {detected_mode.title()}",
            f"Peak performance window: {next((z['start_time'] + ' - ' + z['end_time'] for z in energy_zones if z['zone_name'] == 'peak'), 'Not defined')}",
        ]

        if detected_mode == "recovery":
            summary_parts.append("Focus on gentler activities during recovery phase")
        elif detected_mode == "performance":
            summary_parts.append("Enhanced intensity during peak energy windows")
        else:
            summary_parts.append("Balanced activity distribution throughout the day")

        return " • ".join(summary_parts)
```

### 4.2 Enhanced Nutrition Agent

**File: `services/agents/nutrition/main.py` (extend existing)**

```python
class NutritionAgent(BaseAgent):
    """
    Enhanced nutrition agent that incorporates circadian timing for meal optimization
    """

    async def generate_nutrition_plan_with_zones(self, user_id: str, archetype: str) -> Dict[str, Any]:
        """
        Generate nutrition plan optimized for circadian rhythm and energy zones
        """
        try:
            # Get combined analysis data
            analysis_data = await self.memory_agent.get_combined_analysis(user_id)
            behavior_data = analysis_data.get("behavior_analysis")
            circadian_data = analysis_data.get("circadian_analysis")

            if not behavior_data:
                return {"error": "No behavior analysis available"}

            # Generate base nutrition plan
            base_nutrition = await self._generate_base_nutrition_plan(user_id, archetype, behavior_data)

            # Enhance with circadian timing if available
            if circadian_data and circadian_data.get("energy_zones"):
                enhanced_nutrition = await self._optimize_meal_timing(
                    base_nutrition=base_nutrition,
                    energy_zones=circadian_data["energy_zones"],
                    sleep_schedule=circadian_data.get("sleep_schedule"),
                    archetype=archetype
                )

                return {
                    "success": True,
                    "nutrition_plan": enhanced_nutrition["nutrition_plan"],
                    "meal_timing": enhanced_nutrition["meal_timing"],
                    "circadian_optimization": enhanced_nutrition["optimization_notes"],
                    "archetype": archetype
                }
            else:
                return {
                    "success": True,
                    "nutrition_plan": base_nutrition["nutrition_plan"],
                    "archetype": archetype,
                    "note": "Generated without circadian meal timing optimization"
                }

        except Exception as e:
            logger.error(f"Nutrition plan generation failed for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _optimize_meal_timing(self, base_nutrition: Dict, energy_zones: List[Dict], sleep_schedule: Dict, archetype: str) -> Dict[str, Any]:
        """Optimize meal timing based on energy zones and circadian rhythm"""

        # Use AI to optimize meal timing
        system_prompt = """
        You are a circadian nutrition expert optimizing meal timing based on energy zones and chronobiology.

        Guidelines:
        - Align larger meals with higher energy zones
        - Time protein intake for optimal muscle protein synthesis
        - Consider digestive load relative to energy availability
        - Optimize pre/post-workout nutrition timing
        - Respect individual chronotype preferences
        """

        timing_prompt = f"""
        Optimize meal timing for this nutrition plan based on energy zones:

        Base Nutrition Plan: {base_nutrition.get("nutrition_plan", "")}

        Energy Zones: {energy_zones}
        Sleep Schedule: {sleep_schedule}
        Archetype: {archetype}

        Provide optimized meal timing recommendations.
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": timing_prompt}
                ]
            )

            return {
                "nutrition_plan": response.choices[0].message.content,
                "meal_timing": "Optimized for energy zones",
                "optimization_notes": "Meal timing aligned with circadian rhythm"
            }

        except Exception as e:
            logger.error(f"Meal timing optimization failed: {e}")
            return {
                "nutrition_plan": base_nutrition.get("nutrition_plan", ""),
                "meal_timing": "Standard timing",
                "optimization_notes": "Circadian optimization not available"
            }
```

### 4.3 Enhanced API Endpoints

**File: `services/api_gateway/openai_main.py` (extend existing)**

```python
# Add new endpoints for circadian-aware plan generation

@app.post("/api/user/{user_id}/routine/generate-with-zones")
async def generate_routine_with_energy_zones(
    user_id: str,
    request: Dict[str, Any]
):
    """
    Generate routine plan optimized for user's circadian rhythm and energy zones

    This endpoint uses both behavior analysis and circadian analysis to create
    a routine that flows naturally with the user's energy patterns.
    """
    try:
        archetype = request.get("archetype", "Foundation Builder")
        force_analysis = request.get("force_analysis", False)

        # Initialize services
        orchestrator = HolisticOrchestrator()
        await orchestrator.initialize()

        # Check if we have recent comprehensive analysis
        memory_agent = HolisticMemoryAgent()
        await memory_agent.initialize()

        analysis_data = await memory_agent.get_combined_analysis(user_id)

        # If no recent analysis or force_analysis requested, run complete analysis first
        needs_analysis = (
            force_analysis or
            not analysis_data.get("behavior_analysis") or
            not analysis_data.get("circadian_analysis")
        )

        if needs_analysis:
            logger.info(f"Running complete analysis for user {user_id} before routine generation")
            analysis_result = await orchestrator.orchestrate_complete_analysis(user_id, archetype)

            if not analysis_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to complete user analysis",
                    "details": analysis_result.get("error", "Unknown error")
                }

        # Generate routine with energy zones
        routine_agent = RoutineAgent()
        await routine_agent.initialize()

        routine_result = await routine_agent.generate_routine_with_zones(user_id, archetype)

        if routine_result.get("success"):
            return {
                "success": True,
                "data": routine_result,
                "meta": {
                    "analysis_run": needs_analysis,
                    "energy_zones_available": routine_result.get("enhancement_type") == "energy_zone_optimized"
                }
            }
        else:
            return {
                "success": False,
                "error": routine_result.get("error", "Routine generation failed")
            }

    except Exception as e:
        logger.error(f"Routine generation with zones failed: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/user/{user_id}/nutrition/generate-with-zones")
async def generate_nutrition_with_circadian_timing(
    user_id: str,
    request: Dict[str, Any]
):
    """
    Generate nutrition plan with circadian-optimized meal timing
    """
    try:
        archetype = request.get("archetype", "Foundation Builder")

        # Similar pattern as routine generation
        memory_agent = HolisticMemoryAgent()
        await memory_agent.initialize()

        analysis_data = await memory_agent.get_combined_analysis(user_id)

        if not analysis_data.get("behavior_analysis"):
            return {"success": False, "error": "No behavior analysis available"}

        nutrition_agent = NutritionAgent()
        await nutrition_agent.initialize()

        nutrition_result = await nutrition_agent.generate_nutrition_plan_with_zones(user_id, archetype)

        return {
            "success": nutrition_result.get("success", False),
            "data": nutrition_result
        }

    except Exception as e:
        logger.error(f"Nutrition generation with zones failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/user/{user_id}/energy-zones/current")
async def get_current_energy_zone_status(user_id: str):
    """
    Get user's current energy zone status for real-time recommendations
    """
    try:
        memory_agent = HolisticMemoryAgent()
        await memory_agent.initialize()

        current_state = await memory_agent.get_current_energy_state(user_id)

        if current_state:
            return {
                "success": True,
                "data": current_state
            }
        else:
            return {
                "success": False,
                "error": "No energy zone data available for user"
            }

    except Exception as e:
        logger.error(f"Failed to get current energy zone status: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/user/{user_id}/analysis/status")
async def get_analysis_status(user_id: str):
    """
    Get status of user's behavior and circadian analysis
    """
    try:
        memory_agent = HolisticMemoryAgent()
        await memory_agent.initialize()

        analysis_data = await memory_agent.get_combined_analysis(user_id)

        return {
            "success": True,
            "data": {
                "has_behavior_analysis": analysis_data.get("has_behavior_data", False),
                "has_circadian_analysis": analysis_data.get("has_circadian_data", False),
                "last_analysis_timestamp": analysis_data.get("combined_timestamp"),
                "energy_zones_available": bool(analysis_data.get("circadian_analysis", {}).get("energy_zones"))
            }
        }

    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        return {"success": False, "error": str(e)}

# Backward compatibility - keep existing endpoints unchanged
@app.post("/api/user/{user_id}/routine/generate")
async def generate_routine_legacy(user_id: str, request: Dict[str, Any]):
    """
    Legacy routine generation endpoint (backwards compatibility)
    This maintains compatibility with existing API consumers
    """
    # Keep existing implementation unchanged
    pass
```

---

## Phase 5: Database Schema Updates (Week 5)

### 5.1 Minimal Database Changes (Recommended Approach)

```sql
-- Option 1: Use existing memory tables (RECOMMENDED)
-- No new tables needed - leverage existing holistic_memory_* tables

-- The existing memory tables can store circadian data:
-- - holistic_memory_procedural: Store circadian patterns, sleep schedules, energy zones
-- - holistic_memory_working: Store current energy zone status
-- - holistic_memory_episodic: Store energy zone performance history and feedback
-- - holistic_memory_semantic: Store learned circadian preferences and patterns

-- Optional: Add index for better performance on circadian queries
CREATE INDEX IF NOT EXISTS idx_memory_procedural_circadian
ON holistic_memory_procedural(user_id, memory_key)
WHERE memory_key = 'circadian_patterns';

CREATE INDEX IF NOT EXISTS idx_memory_working_energy_state
ON holistic_memory_working(user_id, memory_key)
WHERE memory_key = 'current_energy_state';
```

### 5.2 Optional Enhancement Columns (If Additional Tracking Needed)

```sql
-- Option 2: Add optional columns to existing analysis table
-- Only if you need structured querying of circadian data

ALTER TABLE holistic_analysis_results
ADD COLUMN IF NOT EXISTS circadian_analysis JSONB,
ADD COLUMN IF NOT EXISTS energy_zones JSONB,
ADD COLUMN IF NOT EXISTS sleep_schedule JSONB,
ADD COLUMN IF NOT EXISTS chronotype VARCHAR(20),
ADD COLUMN IF NOT EXISTS circadian_confidence_score FLOAT;

-- Optional: Indexes for performance if using structured columns
CREATE INDEX IF NOT EXISTS idx_analysis_circadian
ON holistic_analysis_results USING GIN (circadian_analysis);

CREATE INDEX IF NOT EXISTS idx_analysis_chronotype
ON holistic_analysis_results (user_id, chronotype);

-- Optional: Partial index for high-confidence circadian analyses
CREATE INDEX IF NOT EXISTS idx_analysis_high_confidence_circadian
ON holistic_analysis_results (user_id, created_at)
WHERE circadian_confidence_score > 0.7;
```

### 5.3 Data Migration Strategy

```sql
-- Migration script for existing users
-- This would run once when deploying the circadian enhancement

-- Create temporary migration tracking
CREATE TABLE IF NOT EXISTS circadian_migration_status (
    user_id VARCHAR(100) PRIMARY KEY,
    migration_started_at TIMESTAMP DEFAULT NOW(),
    migration_completed_at TIMESTAMP,
    migration_status VARCHAR(20) DEFAULT 'pending'
);

-- Gradual migration approach
-- Users get circadian analysis on their next routine request
-- No immediate bulk migration needed
```

---

## Phase 6: Testing and Validation (Week 6)

### 6.1 Unit Tests

**File: `tests/unit/test_circadian_agent.py`**

```python
import pytest
from unittest.mock import Mock, AsyncMock
from services.agents.circadian.main import CircadianAnalysisAgent
from shared_libs.data_models.health_models import UserHealthContext

class TestCircadianAgent:
    @pytest.fixture
    async def circadian_agent(self):
        agent = CircadianAnalysisAgent()
        agent.openai_client = AsyncMock()
        return agent

    @pytest.fixture
    def sample_health_context(self):
        # Create sample health context with sleep data
        return UserHealthContext(
            user_id="test_user",
            scores=[
                # Sample sleep and activity scores
            ]
        )

    async def test_circadian_analysis_success(self, circadian_agent, sample_health_context):
        """Test successful circadian pattern analysis"""

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        {
            "estimated_wake_time": "07:00",
            "estimated_bedtime": "22:30",
            "chronotype": "morning_lark",
            "detected_mode": "productive",
            "confidence_score": 0.8,
            "avg_sleep_duration": 8.5,
            "insights": ["Consistent early riser pattern", "Strong circadian rhythm"]
        }
        """

        circadian_agent.openai_client.chat.completions.create.return_value = mock_response

        # Run analysis
        result = await circadian_agent.analyze_circadian_patterns("test_user", sample_health_context)

        # Verify results
        assert result["user_id"] == "test_user"
        assert result["sleep_schedule"]["chronotype"] == "morning_lark"
        assert result["detected_mode"] == "productive"
        assert len(result["energy_zones"]) > 0
        assert result["sleep_schedule"]["confidence_score"] == 0.8

    async def test_energy_zone_calculation(self, circadian_agent):
        """Test energy zone calculation"""
        from datetime import time

        zones = await circadian_agent._calculate_energy_zones(
            wake_time=time(7, 0),
            bedtime=time(22, 30),
            chronotype="morning_lark",
            current_mode="productive"
        )

        # Verify zone structure
        assert len(zones) >= 4  # Foundation, Peak, Maintenance, Recovery
        zone_names = [zone["zone_name"] for zone in zones]
        assert "foundation" in zone_names
        assert "peak" in zone_names
        assert "maintenance" in zone_names
        assert "recovery" in zone_names

        # Verify timing logic
        foundation_zone = next(z for z in zones if z["zone_name"] == "foundation")
        assert foundation_zone["start_time"] == "07:00"  # Should start at wake time

    async def test_chronotype_detection_accuracy(self, circadian_agent, sample_health_context):
        """Test chronotype classification accuracy"""

        # Test morning lark pattern
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"chronotype": "morning_lark", "confidence_score": 0.9}'

        circadian_agent.openai_client.chat.completions.create.return_value = mock_response
        circadian_agent._parse_circadian_response = Mock(return_value={"chronotype": "morning_lark", "confidence_score": 0.9})

        # Mock sleep data suggesting morning lark
        sample_health_context.scores = [
            # Mock early sleep, early wake pattern
        ]

        result = await circadian_agent.analyze_circadian_patterns("test_user", sample_health_context)

        assert result["sleep_schedule"]["chronotype"] == "morning_lark"
        assert result["sleep_schedule"]["confidence_score"] > 0.8

    async def test_error_handling(self, circadian_agent, sample_health_context):
        """Test error handling in circadian analysis"""

        # Mock OpenAI API failure
        circadian_agent.openai_client.chat.completions.create.side_effect = Exception("API Error")

        # Should not crash, should return default values
        result = await circadian_agent.analyze_circadian_patterns("test_user", sample_health_context)

        assert result["user_id"] == "test_user"
        assert "error" not in result  # Should handle gracefully with defaults
        assert result["sleep_schedule"]["confidence_score"] <= 0.5  # Low confidence for errors
```

**File: `tests/unit/test_orchestrator_parallel.py`**

```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from services.orchestrator.main import HolisticOrchestrator

class TestParallelOrchestration:
    @pytest.fixture
    async def orchestrator(self):
        orchestrator = HolisticOrchestrator()
        orchestrator.user_service = AsyncMock()
        orchestrator.circadian_agent = AsyncMock()
        orchestrator.memory_agent = AsyncMock()
        orchestrator.insights_agent = AsyncMock()
        return orchestrator

    async def test_parallel_analysis_success(self, orchestrator):
        """Test successful parallel behavior and circadian analysis"""

        # Mock health data
        health_context = Mock()
        orchestrator.user_service.get_analysis_data.return_value = (health_context, "2024-01-01")

        # Mock analysis results
        behavior_result = {"analysis": "behavior_data", "success": True}
        circadian_result = {"analysis": "circadian_data", "energy_zones": [], "success": True}

        orchestrator._run_behavior_analysis = AsyncMock(return_value=behavior_result)
        orchestrator.circadian_agent.analyze_circadian_patterns.return_value = circadian_result
        orchestrator.memory_agent.store_behavior_analysis.return_value = True
        orchestrator.memory_agent.store_circadian_analysis.return_value = True
        orchestrator._run_insights_generation = AsyncMock(return_value={"insights": "generated"})
        orchestrator.memory_agent.store_insights.return_value = True

        # Run orchestration
        result = await orchestrator.orchestrate_complete_analysis("test_user", "Foundation Builder")

        # Verify parallel execution
        assert result["success"] is True
        assert "behavior_analysis" in result
        assert "circadian_analysis" in result
        assert result["energy_zones_available"] is True

        # Verify all storage methods were called
        orchestrator.memory_agent.store_behavior_analysis.assert_called_once()
        orchestrator.memory_agent.store_circadian_analysis.assert_called_once()

    async def test_parallel_analysis_with_circadian_failure(self, orchestrator):
        """Test graceful handling when circadian analysis fails but behavior succeeds"""

        health_context = Mock()
        orchestrator.user_service.get_analysis_data.return_value = (health_context, "2024-01-01")

        # Behavior succeeds, circadian fails
        behavior_result = {"analysis": "behavior_data", "success": True}
        circadian_error = Exception("Circadian analysis failed")

        orchestrator._run_behavior_analysis = AsyncMock(return_value=behavior_result)
        orchestrator.circadian_agent.analyze_circadian_patterns.side_effect = circadian_error
        orchestrator.memory_agent.store_behavior_analysis.return_value = True
        orchestrator._run_insights_generation = AsyncMock(return_value={"insights": "generated"})
        orchestrator.memory_agent.store_insights.return_value = True

        # Run orchestration
        result = await orchestrator.orchestrate_complete_analysis("test_user", "Foundation Builder")

        # Should still succeed with behavior analysis only
        assert result["success"] is True
        assert "behavior_analysis" in result
        assert result["energy_zones_available"] is False
        assert "circadian_note" in result

        # Behavior analysis should still be stored
        orchestrator.memory_agent.store_behavior_analysis.assert_called_once()
        # Circadian analysis should NOT be stored due to error
        orchestrator.memory_agent.store_circadian_analysis.assert_not_called()

    async def test_timeout_handling(self, orchestrator):
        """Test timeout handling in parallel analysis"""

        health_context = Mock()
        orchestrator.user_service.get_analysis_data.return_value = (health_context, "2024-01-01")

        # Mock long-running analysis
        async def slow_behavior_analysis(*args):
            await asyncio.sleep(200)  # Longer than timeout
            return {"analysis": "behavior_data"}

        async def slow_circadian_analysis(*args):
            await asyncio.sleep(200)
            return {"analysis": "circadian_data"}

        orchestrator._run_behavior_analysis = slow_behavior_analysis
        orchestrator.circadian_agent.analyze_circadian_patterns = slow_circadian_analysis

        # Run orchestration - should timeout
        result = await orchestrator.orchestrate_complete_analysis("test_user", "Foundation Builder")

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    async def test_performance_timing(self, orchestrator):
        """Test that parallel processing is faster than sequential"""

        health_context = Mock()
        orchestrator.user_service.get_analysis_data.return_value = (health_context, "2024-01-01")

        # Mock analysis with artificial delays
        async def mock_behavior_analysis(*args):
            await asyncio.sleep(0.1)  # 100ms delay
            return {"analysis": "behavior_data", "success": True}

        async def mock_circadian_analysis(*args):
            await asyncio.sleep(0.1)  # 100ms delay
            return {"analysis": "circadian_data", "success": True}

        orchestrator._run_behavior_analysis = mock_behavior_analysis
        orchestrator.circadian_agent.analyze_circadian_patterns = mock_circadian_analysis
        orchestrator.memory_agent.store_behavior_analysis.return_value = True
        orchestrator.memory_agent.store_circadian_analysis.return_value = True
        orchestrator._run_insights_generation = AsyncMock(return_value={"insights": "generated"})
        orchestrator.memory_agent.store_insights.return_value = True

        # Time the parallel execution
        start_time = asyncio.get_event_loop().time()
        result = await orchestrator.orchestrate_complete_analysis("test_user", "Foundation Builder")
        end_time = asyncio.get_event_loop().time()

        # Should complete in ~0.1 seconds (parallel) not ~0.2 seconds (sequential)
        execution_time = end_time - start_time
        assert execution_time < 0.15  # Allow some overhead
        assert result["success"] is True
```

### 6.2 Integration Tests

**File: `tests/integration/test_circadian_workflow.py`**

```python
import pytest
from services.orchestrator.main import HolisticOrchestrator
from services.agents.routine.main import RoutineAgent
from services.agents.memory.main import HolisticMemoryAgent

class TestCircadianWorkflow:
    async def test_end_to_end_with_zones(self):
        """Test complete workflow from analysis to zone-optimized routine"""

        # This would be a full integration test
        # 1. Run complete analysis (behavior + circadian)
        # 2. Generate routine with zones
        # 3. Verify zone alignment

        user_id = "test_integration_user"
        archetype = "Foundation Builder"

        # Initialize orchestrator
        orchestrator = HolisticOrchestrator()
        await orchestrator.initialize()

        # Run complete analysis
        analysis_result = await orchestrator.orchestrate_complete_analysis(user_id, archetype)

        # Should succeed (assuming test data available)
        assert analysis_result.get("success") is True

        # Generate routine with zones
        routine_agent = RoutineAgent()
        await routine_agent.initialize()

        routine_result = await routine_agent.generate_routine_with_zones(user_id, archetype)

        # Verify routine generation
        assert routine_result.get("success") is True
        assert "routine_plan" in routine_result

        # If circadian analysis was successful, should have energy zones
        if analysis_result.get("energy_zones_available"):
            assert "energy_zones" in routine_result
            assert "zone_alignment" in routine_result

    async def test_routine_zone_alignment_quality(self):
        """Test quality of routine alignment with energy zones"""

        # This would test that high-energy activities are placed in peak zones
        # and low-energy activities in recovery zones
        pass

    async def test_memory_persistence(self):
        """Test that circadian data persists correctly in memory system"""

        user_id = "test_memory_user"

        # Store circadian data
        memory_agent = HolisticMemoryAgent()
        await memory_agent.initialize()

        circadian_data = {
            "sleep_schedule": {"estimated_wake_time": "07:00", "estimated_bedtime": "22:30"},
            "energy_zones": [{"zone_name": "peak", "start_time": "09:00", "end_time": "11:00"}],
            "detected_mode": "productive"
        }

        # Store and retrieve
        store_success = await memory_agent.store_circadian_analysis(user_id, circadian_data)
        assert store_success is True

        retrieved_data = await memory_agent.get_circadian_data(user_id)
        assert retrieved_data is not None
        assert retrieved_data["detected_mode"] == "productive"
```

### 6.3 Performance Tests

**File: `tests/performance/test_parallel_performance.py`**

```python
import pytest
import asyncio
import time
from services.orchestrator.main import HolisticOrchestrator

class TestParallelPerformance:
    async def test_parallel_vs_sequential_timing(self):
        """Verify parallel processing provides performance benefit"""

        # This test would compare timing of parallel vs sequential analysis
        # and ensure parallel is significantly faster
        pass

    async def test_memory_usage_under_load(self):
        """Test memory usage with parallel processing"""

        # This would monitor memory usage during parallel analysis
        # to ensure no memory leaks or excessive usage
        pass

    async def test_concurrent_users(self):
        """Test system performance with multiple concurrent users"""

        # Simulate multiple users requesting analysis simultaneously
        # Verify system handles load gracefully
        pass
```

---

## Implementation Timeline and Milestones

| Phase | Duration | Key Deliverables | Success Criteria | Dependencies |
|-------|----------|------------------|------------------|--------------|
| **Phase 1** | Week 1 | Circadian Analysis Agent | Agent processes raw data and generates energy zones | None |
| **Phase 2** | Week 2 | Enhanced Orchestrator | Parallel processing of behavior and circadian analysis | Phase 1 |
| **Phase 3** | Week 3 | Memory Agent Extensions | Stores and retrieves circadian data | Phase 2 |
| **Phase 4** | Week 4 | Enhanced Plan Generation | Routines aligned with energy zones | Phase 3 |
| **Phase 5** | Week 5 | Database Updates | Optimized data storage and retrieval | Phase 4 |
| **Phase 6** | Week 6 | Testing & Validation | Comprehensive test coverage | All phases |

### Weekly Milestones

**Week 1 Milestone**: Circadian Agent generates energy zones from raw health data
- ✅ Agent processes sleep and activity patterns
- ✅ AI-powered chronotype detection
- ✅ Energy zones calculated with confidence scores

**Week 2 Milestone**: Orchestrator runs parallel analyses
- ✅ Behavior and circadian agents run simultaneously
- ✅ Error handling for partial failures
- ✅ 40-50% reduction in total analysis time

**Week 3 Milestone**: Memory system stores both analysis types
- ✅ Circadian data persists in memory hierarchy
- ✅ Combined analysis retrieval methods
- ✅ Energy zones formatted for plan consumption

**Week 4 Milestone**: Plans optimized for energy zones
- ✅ Routine activities aligned with peak energy windows
- ✅ New API endpoints for zone-aware planning
- ✅ Backward compatibility maintained

**Week 5 Milestone**: Production-ready database schema
- ✅ Optimal indexing for circadian queries
- ✅ Data migration strategy for existing users
- ✅ Performance validation under load

**Week 6 Milestone**: Comprehensive testing complete
- ✅ Unit, integration, and performance tests passing
- ✅ Error scenarios handled gracefully
- ✅ System ready for production deployment

---

## Success Metrics

### Technical Success Metrics

1. **Performance Improvements**
   - ✅ 40-50% reduction in total analysis time through parallel processing
   - ✅ Energy zones calculation accuracy >80% based on validation data
   - ✅ Zero breaking changes to existing functionality
   - ✅ Memory usage remains within acceptable bounds (<20% increase)

2. **System Reliability**
   - ✅ Graceful degradation when circadian analysis fails
   - ✅ Backward compatibility with existing API endpoints
   - ✅ Error rate <1% for parallel processing workflow
   - ✅ Response time <2 seconds for zone-optimized routine generation

3. **Data Quality**
   - ✅ Circadian analysis confidence scores consistently >0.6
   - ✅ Energy zone timing accuracy validated against user feedback
   - ✅ Sleep schedule inference within 30 minutes of actual patterns
   - ✅ Chronotype classification >85% accuracy

### User Experience Success Metrics

1. **Plan Quality Improvements**
   - ✅ Routine activities aligned with natural energy patterns
   - ✅ Higher user satisfaction ratings for timing recommendations
   - ✅ Increased engagement with personalized schedules
   - ✅ Reduced user modifications to generated routines

2. **Feature Adoption**
   - ✅ >70% of users with sufficient data receive energy zone analysis
   - ✅ Zone-optimized routines requested by >40% of active users
   - ✅ Positive user feedback on circadian-aware features
   - ✅ Increased session duration for users with energy zones

### Business Success Metrics

1. **System Efficiency**
   - ✅ Reduced OpenAI API costs through optimized analysis workflow
   - ✅ Higher throughput of analysis requests per hour
   - ✅ Improved user retention through better personalization
   - ✅ Scalable architecture supporting future enhancements

---

## Risk Mitigation Strategies

### Technical Risks

1. **Parallel Processing Complexity**
   - **Risk**: Race conditions or synchronization issues
   - **Mitigation**: Comprehensive testing, clear error boundaries, independent analysis paths

2. **AI Analysis Quality**
   - **Risk**: Inconsistent circadian analysis results
   - **Mitigation**: Confidence scoring, validation against known patterns, fallback to defaults

3. **Memory System Load**
   - **Risk**: Increased memory usage affecting performance
   - **Mitigation**: Efficient data structures, TTL-based cleanup, monitoring alerts

4. **API Reliability**
   - **Risk**: OpenAI API failures affecting both analyses
   - **Mitigation**: Independent failure handling, retry logic, graceful degradation

### Implementation Risks

1. **Timeline Pressure**
   - **Risk**: Rushed implementation leading to bugs
   - **Mitigation**: Phased rollout, extensive testing, feature flags for gradual release

2. **Integration Complexity**
   - **Risk**: Breaking existing functionality
   - **Mitigation**: Backward compatibility, parallel endpoint testing, staged deployment

3. **Data Quality Dependencies**
   - **Risk**: Insufficient health data for circadian analysis
   - **Mitigation**: Confidence thresholds, graceful fallbacks, clear user messaging

### User Adoption Risks

1. **Feature Complexity**
   - **Risk**: Users confused by energy zones concept
   - **Mitigation**: Clear explanations, optional feature, educational content

2. **Accuracy Expectations**
   - **Risk**: Users expecting perfect circadian predictions
   - **Mitigation**: Confidence scores, feedback mechanisms, transparent limitations

---

## Future Enhancement Opportunities

### Phase 7+: Advanced Features (Post-Implementation)

1. **Real-time Adaptation** (Months 3-4)
   - Biometric feedback integration
   - Dynamic zone adjustments based on current state
   - Predictive energy forecasting

2. **Machine Learning Enhancement** (Months 4-5)
   - Learn from user feedback to improve predictions
   - Personalized zone templates based on historical data
   - Automatic chronotype refinement over time

3. **Social and Environmental Factors** (Months 5-6)
   - Weather impact on energy patterns
   - Social schedule considerations
   - Travel and timezone adaptation

4. **Advanced Coaching** (Months 6+)
   - Circadian rhythm optimization recommendations
   - Sleep schedule improvement guidance
   - Lifestyle change support for better energy patterns

---

## Conclusion

This architecture plan provides a comprehensive roadmap for transforming your working 6-agent HolisticOS system into a circadian-aware, energy-zone-optimized health platform. The approach:

- **Preserves your working infrastructure** while adding intelligent enhancements
- **Minimizes risk** through incremental, backward-compatible changes
- **Leverages proven patterns** from your existing successful implementation
- **Provides immediate value** with each phase of implementation
- **Sets foundation** for advanced features in future phases

The parallel processing architecture ensures both behavior and circadian analyses have access to raw health data while maintaining efficient performance. The enhanced memory system provides unified storage and retrieval for all agent types, and the zone-optimized plan generation creates truly personalized routines that flow naturally with users' energy patterns.

This plan delivers a sophisticated, production-ready enhancement that transforms your health optimization platform into a circadian-intelligent system while maintaining all the reliability and performance characteristics that make your current system successful.