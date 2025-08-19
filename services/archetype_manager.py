"""
Archetype Management Service
Handles archetype switching, compatibility checking, and transition planning
"""

from enum import Enum
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class ArchetypeType(Enum):
    """Available user archetypes"""
    FOUNDATION_BUILDER = "Foundation Builder"
    PEAK_PERFORMER = "Peak Performer"
    SYSTEMATIC_IMPROVER = "Systematic Improver"
    TRANSFORMATION_SEEKER = "Transformation Seeker"
    RESILIENCE_REBUILDER = "Resilience Rebuilder"
    CONNECTED_EXPLORER = "Connected Explorer"

class TransitionStrategy(Enum):
    """How to handle archetype transitions"""
    FRESH_START = "fresh_start"        # Complete new analysis
    GRADUAL_BLEND = "gradual_blend"    # Blend old and new over time
    ADAPTIVE = "adaptive"               # Adapt existing to new
    USER_CHOICE = "user_choice"        # Let user decide

class ArchetypeManager:
    """
    Manages archetype transitions and compatibility
    Ensures users get appropriate plans when switching archetypes
    """
    
    # Compatibility matrix - which archetypes can smoothly transition
    COMPATIBILITY_MATRIX = {
        "Foundation Builder": {
            "compatible": ["Resilience Rebuilder", "Systematic Improver"],
            "semi_compatible": ["Connected Explorer"],
            "incompatible": ["Peak Performer", "Transformation Seeker"]
        },
        "Peak Performer": {
            "compatible": ["Systematic Improver"],
            "semi_compatible": ["Transformation Seeker"],
            "incompatible": ["Foundation Builder", "Resilience Rebuilder", "Connected Explorer"]
        },
        "Systematic Improver": {
            "compatible": ["Peak Performer", "Foundation Builder"],
            "semi_compatible": ["Transformation Seeker", "Resilience Rebuilder"],
            "incompatible": ["Connected Explorer"]
        },
        "Transformation Seeker": {
            "compatible": ["Connected Explorer"],
            "semi_compatible": ["Peak Performer", "Systematic Improver"],
            "incompatible": ["Foundation Builder", "Resilience Rebuilder"]
        },
        "Resilience Rebuilder": {
            "compatible": ["Foundation Builder"],
            "semi_compatible": ["Systematic Improver", "Connected Explorer"],
            "incompatible": ["Peak Performer", "Transformation Seeker"]
        },
        "Connected Explorer": {
            "compatible": ["Transformation Seeker"],
            "semi_compatible": ["Resilience Rebuilder", "Foundation Builder"],
            "incompatible": ["Peak Performer", "Systematic Improver"]
        }
    }
    
    # Time and complexity differences between archetypes
    ARCHETYPE_PROFILES = {
        "Foundation Builder": {
            "daily_time": 45,  # minutes
            "complexity": 2,    # 1-10 scale
            "focus": "basics"
        },
        "Peak Performer": {
            "daily_time": 120,
            "complexity": 9,
            "focus": "optimization"
        },
        "Systematic Improver": {
            "daily_time": 75,
            "complexity": 6,
            "focus": "consistency"
        },
        "Transformation Seeker": {
            "daily_time": 90,
            "complexity": 8,
            "focus": "change"
        },
        "Resilience Rebuilder": {
            "daily_time": 60,
            "complexity": 3,
            "focus": "recovery"
        },
        "Connected Explorer": {
            "daily_time": 60,
            "complexity": 5,
            "focus": "meaning"
        }
    }
    
    def assess_transition(
        self, 
        from_archetype: str, 
        to_archetype: str,
        user_history: Optional[Dict] = None
    ) -> Dict:
        """
        Assess how to handle an archetype transition
        
        Returns:
            Dict with transition strategy and recommendations
        """
        if from_archetype == to_archetype:
            return {
                "strategy": TransitionStrategy.ADAPTIVE,
                "reason": "Same archetype - minor adaptations only",
                "fresh_analysis_required": False,
                "transition_days": 0
            }
        
        # Check compatibility
        compatibility = self._check_compatibility(from_archetype, to_archetype)
        
        # Get profile differences
        time_diff = abs(
            self.ARCHETYPE_PROFILES[from_archetype]["daily_time"] -
            self.ARCHETYPE_PROFILES[to_archetype]["daily_time"]
        )
        complexity_diff = abs(
            self.ARCHETYPE_PROFILES[from_archetype]["complexity"] -
            self.ARCHETYPE_PROFILES[to_archetype]["complexity"]
        )
        
        # Determine strategy based on compatibility and differences
        if compatibility == "incompatible" or complexity_diff > 5:
            return {
                "strategy": TransitionStrategy.FRESH_START,
                "reason": f"Significant change from {from_archetype} to {to_archetype}",
                "fresh_analysis_required": True,
                "transition_days": 0,
                "warnings": [
                    f"Time commitment changes by {time_diff} minutes/day",
                    f"Complexity level changes by {complexity_diff} points",
                    "Previous strategies may not apply"
                ]
            }
        elif compatibility == "compatible" and complexity_diff <= 2:
            return {
                "strategy": TransitionStrategy.ADAPTIVE,
                "reason": "Compatible archetypes - can adapt existing analysis",
                "fresh_analysis_required": False,
                "transition_days": 3,
                "benefits": [
                    "Smooth transition maintains momentum",
                    "Existing habits can be built upon",
                    "Lower adjustment period"
                ]
            }
        else:  # semi_compatible or moderate differences
            return {
                "strategy": TransitionStrategy.GRADUAL_BLEND,
                "reason": "Moderate change - gradual transition recommended",
                "fresh_analysis_required": False,
                "transition_days": 7,
                "approach": "Blend current and target archetype strategies over a week"
            }
    
    def _check_compatibility(self, from_arch: str, to_arch: str) -> str:
        """Check compatibility between two archetypes"""
        matrix = self.COMPATIBILITY_MATRIX.get(from_arch, {})
        
        if to_arch in matrix.get("compatible", []):
            return "compatible"
        elif to_arch in matrix.get("semi_compatible", []):
            return "semi_compatible"
        else:
            return "incompatible"
    
    def get_transition_plan(
        self,
        from_archetype: str,
        to_archetype: str,
        current_analysis: Optional[Dict] = None
    ) -> Dict:
        """
        Create a detailed transition plan for archetype change
        """
        assessment = self.assess_transition(from_archetype, to_archetype)
        
        plan = {
            "assessment": assessment,
            "timeline": self._create_timeline(assessment),
            "modifications": self._get_plan_modifications(from_archetype, to_archetype),
            "user_guidance": self._get_user_guidance(from_archetype, to_archetype),
            "success_metrics": self._define_success_metrics(to_archetype)
        }
        
        return plan
    
    def _create_timeline(self, assessment: Dict) -> List[Dict]:
        """Create day-by-day transition timeline"""
        strategy = assessment["strategy"]
        days = assessment.get("transition_days", 0)
        
        timeline = []
        
        if strategy == TransitionStrategy.FRESH_START:
            timeline.append({
                "day": 0,
                "action": "Generate fresh analysis",
                "focus": "Complete reset to new archetype"
            })
        elif strategy == TransitionStrategy.GRADUAL_BLEND:
            for day in range(days):
                blend_ratio = (day + 1) / days
                timeline.append({
                    "day": day + 1,
                    "action": f"Blend {int((1-blend_ratio)*100)}% old, {int(blend_ratio*100)}% new",
                    "focus": f"Gradual transition - Day {day + 1} of {days}"
                })
        elif strategy == TransitionStrategy.ADAPTIVE:
            timeline.append({
                "day": 0,
                "action": "Adapt existing plans",
                "focus": "Minor adjustments to align with new archetype"
            })
        
        return timeline
    
    def _get_plan_modifications(self, from_arch: str, to_arch: str) -> Dict:
        """Get specific modifications needed for transition"""
        from_profile = self.ARCHETYPE_PROFILES[from_arch]
        to_profile = self.ARCHETYPE_PROFILES[to_arch]
        
        return {
            "time_adjustment": {
                "from": from_profile["daily_time"],
                "to": to_profile["daily_time"],
                "change": to_profile["daily_time"] - from_profile["daily_time"]
            },
            "complexity_adjustment": {
                "from": from_profile["complexity"],
                "to": to_profile["complexity"],
                "change": to_profile["complexity"] - from_profile["complexity"]
            },
            "focus_shift": {
                "from": from_profile["focus"],
                "to": to_profile["focus"]
            }
        }
    
    def _get_user_guidance(self, from_arch: str, to_arch: str) -> List[str]:
        """Get specific guidance for the user during transition"""
        guidance = []
        
        to_profile = self.ARCHETYPE_PROFILES[to_arch]
        
        if to_profile["complexity"] > 7:
            guidance.append("Prepare for more advanced strategies and detailed tracking")
        elif to_profile["complexity"] < 4:
            guidance.append("Focus on simplicity and sustainable habit building")
        
        if to_profile["daily_time"] > 90:
            guidance.append("Plan for increased time commitment - consider schedule adjustments")
        elif to_profile["daily_time"] < 60:
            guidance.append("Efficient, focused sessions will maximize your limited time")
        
        if to_profile["focus"] == "optimization":
            guidance.append("Get ready for data-driven decisions and performance metrics")
        elif to_profile["focus"] == "recovery":
            guidance.append("Prioritize rest and stress management in your approach")
        elif to_profile["focus"] == "change":
            guidance.append("Embrace comprehensive lifestyle modifications")
        
        return guidance
    
    def _define_success_metrics(self, archetype: str) -> List[str]:
        """Define success metrics for the new archetype"""
        metrics_map = {
            "Foundation Builder": [
                "Consistent daily completion",
                "Confidence in basic habits",
                "Gradual capacity building"
            ],
            "Peak Performer": [
                "Performance metric improvements",
                "Advanced protocol mastery",
                "Optimization velocity"
            ],
            "Systematic Improver": [
                "Routine consistency score",
                "Progressive overload tracking",
                "Habit formation rate"
            ],
            "Transformation Seeker": [
                "Lifestyle change adoption",
                "Breakthrough achievements",
                "Comprehensive progress"
            ],
            "Resilience Rebuilder": [
                "Stress reduction indicators",
                "Recovery quality metrics",
                "Sustainable progress"
            ],
            "Connected Explorer": [
                "Engagement quality",
                "Meaning and satisfaction scores",
                "Social wellness indicators"
            ]
        }
        
        return metrics_map.get(archetype, ["General health improvement"])
    
    async def should_force_fresh_analysis(
        self,
        user_id: str,
        old_archetype: str,
        new_archetype: str,
        last_analysis_date: datetime
    ) -> bool:
        """
        Determine if archetype change requires fresh analysis
        regardless of data thresholds
        """
        # Always fresh if incompatible
        if self._check_compatibility(old_archetype, new_archetype) == "incompatible":
            logger.info(f"Forcing fresh analysis: {old_archetype} → {new_archetype} are incompatible")
            return True
        
        # Check complexity difference
        complexity_diff = abs(
            self.ARCHETYPE_PROFILES[old_archetype]["complexity"] -
            self.ARCHETYPE_PROFILES[new_archetype]["complexity"]
        )
        
        if complexity_diff > 4:
            logger.info(f"Forcing fresh analysis: complexity difference of {complexity_diff}")
            return True
        
        # If last analysis is old, fresh is good anyway
        days_since = (datetime.now(timezone.utc) - last_analysis_date).days
        if days_since > 3:
            logger.info(f"Recommending fresh analysis: {days_since} days since last analysis")
            return True
        
        return False

# Singleton instance
archetype_manager = ArchetypeManager()