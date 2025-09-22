"""
Energy Zones Data Models
Defines all data structures for the Energy Zones Service
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class ModeType(Enum):
    """Energy mode types based on biomarker data"""
    RECOVERY = "recovery"
    PRODUCTIVE = "productive"
    PERFORMANCE = "performance"


class ZoneName(Enum):
    """Energy zone types throughout the day"""
    FOUNDATION = "foundation"
    PEAK = "peak"
    MAINTENANCE = "maintenance"
    RECOVERY = "recovery"


class IntensityLevel(Enum):
    """Activity intensity recommendations"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ChronotypeCategory(Enum):
    """Chronotype classifications"""
    MORNING_LARK = "morning_lark"
    EVENING_OWL = "evening_owl"
    NEUTRAL = "neutral"


@dataclass
class SleepSchedule:
    """Inferred sleep schedule for a user"""
    estimated_wake_time: time
    estimated_bedtime: time
    chronotype: ChronotypeCategory
    confidence_score: float  # 0.0 to 1.0
    data_sources: List[str] = field(default_factory=list)
    sleep_duration_avg_minutes: Optional[int] = None
    inference_date: Optional[date] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "estimated_wake_time": self.estimated_wake_time.isoformat(),
            "estimated_bedtime": self.estimated_bedtime.isoformat(),
            "chronotype": self.chronotype.value,
            "confidence_score": self.confidence_score,
            "data_sources": self.data_sources,
            "sleep_duration_avg_minutes": self.sleep_duration_avg_minutes,
            "inference_date": self.inference_date.isoformat() if self.inference_date else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SleepSchedule':
        """Create from dictionary"""
        return cls(
            estimated_wake_time=time.fromisoformat(data["estimated_wake_time"]),
            estimated_bedtime=time.fromisoformat(data["estimated_bedtime"]),
            chronotype=ChronotypeCategory(data["chronotype"]),
            confidence_score=data["confidence_score"],
            data_sources=data.get("data_sources", []),
            sleep_duration_avg_minutes=data.get("sleep_duration_avg_minutes"),
            inference_date=date.fromisoformat(data["inference_date"]) if data.get("inference_date") else None
        )


@dataclass
class EnergyZone:
    """Individual energy zone with timing and characteristics"""
    zone_name: ZoneName
    start_time: time
    end_time: time
    energy_level: int  # 0-100
    intensity_level: IntensityLevel
    optimal_activities: List[str]
    description: str
    start_offset_hours: float  # Hours after wake time
    duration_hours: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "zone_name": self.zone_name.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "energy_level": self.energy_level,
            "intensity_level": self.intensity_level.value,
            "optimal_activities": self.optimal_activities,
            "description": self.description,
            "start_offset_hours": self.start_offset_hours,
            "duration_hours": self.duration_hours
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnergyZone':
        """Create from dictionary"""
        return cls(
            zone_name=ZoneName(data["zone_name"]),
            start_time=time.fromisoformat(data["start_time"]),
            end_time=time.fromisoformat(data["end_time"]),
            energy_level=data["energy_level"],
            intensity_level=IntensityLevel(data["intensity_level"]),
            optimal_activities=data["optimal_activities"],
            description=data["description"],
            start_offset_hours=data["start_offset_hours"],
            duration_hours=data["duration_hours"]
        )

    def is_active_at(self, current_time: time) -> bool:
        """Check if zone is active at given time"""
        return self.start_time <= current_time <= self.end_time

    def time_remaining_minutes(self, current_time: time) -> int:
        """Calculate minutes remaining in this zone"""
        if not self.is_active_at(current_time):
            return 0

        # Convert times to minutes since midnight for calculation
        current_minutes = current_time.hour * 60 + current_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute

        # Handle day boundary crossing
        if end_minutes < current_minutes:
            end_minutes += 24 * 60

        return max(0, end_minutes - current_minutes)


@dataclass
class EnergyZoneDefinition:
    """Reference definition for energy zones from database"""
    id: str
    zone_name: ZoneName
    mode_type: ModeType
    start_offset_hours: float
    duration_hours: float
    base_energy_level: int
    intensity_level: IntensityLevel
    optimal_activities: List[str]
    description: str
    is_active: bool = True

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'EnergyZoneDefinition':
        """Create from database row"""
        return cls(
            id=row["id"],
            zone_name=ZoneName(row["zone_name"]),
            mode_type=ModeType(row["mode_type"]),
            start_offset_hours=row["start_offset_hours"],
            duration_hours=row["duration_hours"],
            base_energy_level=row["base_energy_level"],
            intensity_level=IntensityLevel(row["intensity_level"]),
            optimal_activities=row["optimal_activities"],
            description=row["description"],
            is_active=row.get("is_active", True)
        )


@dataclass
class BiomarkerSnapshot:
    """Snapshot of biomarker data used for zone calculation"""
    readiness_score: Optional[float] = None
    sleep_score: Optional[float] = None
    activity_score: Optional[float] = None
    hrv_score: Optional[float] = None
    sleep_duration_hours: Optional[float] = None
    sleep_efficiency: Optional[float] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "readiness_score": self.readiness_score,
            "sleep_score": self.sleep_score,
            "activity_score": self.activity_score,
            "hrv_score": self.hrv_score,
            "sleep_duration_hours": self.sleep_duration_hours,
            "sleep_efficiency": self.sleep_efficiency,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiomarkerSnapshot':
        """Create from dictionary"""
        return cls(
            readiness_score=data.get("readiness_score"),
            sleep_score=data.get("sleep_score"),
            activity_score=data.get("activity_score"),
            hrv_score=data.get("hrv_score"),
            sleep_duration_hours=data.get("sleep_duration_hours"),
            sleep_efficiency=data.get("sleep_efficiency"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )


@dataclass
class EnergyZonesResult:
    """Complete result of energy zones calculation"""
    user_id: str
    calculation_date: date
    detected_mode: ModeType
    sleep_schedule: SleepSchedule
    energy_zones: List[EnergyZone]
    confidence_score: float
    biomarker_snapshot: Optional[BiomarkerSnapshot] = None
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "calculation_date": self.calculation_date.isoformat(),
            "detected_mode": self.detected_mode.value,
            "sleep_schedule": self.sleep_schedule.to_dict(),
            "energy_zones": [zone.to_dict() for zone in self.energy_zones],
            "confidence_score": self.confidence_score,
            "biomarker_snapshot": self.biomarker_snapshot.to_dict() if self.biomarker_snapshot else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnergyZonesResult':
        """Create from dictionary"""
        return cls(
            user_id=data["user_id"],
            calculation_date=date.fromisoformat(data["calculation_date"]),
            detected_mode=ModeType(data["detected_mode"]),
            sleep_schedule=SleepSchedule.from_dict(data["sleep_schedule"]),
            energy_zones=[EnergyZone.from_dict(zone) for zone in data["energy_zones"]],
            confidence_score=data["confidence_score"],
            biomarker_snapshot=BiomarkerSnapshot.from_dict(data["biomarker_snapshot"]) if data.get("biomarker_snapshot") else None,
            generated_at=datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )

    def get_current_zone(self, current_time: Optional[time] = None) -> Optional[EnergyZone]:
        """Get the energy zone active at current time"""
        if current_time is None:
            current_time = datetime.now().time()

        for zone in self.energy_zones:
            if zone.is_active_at(current_time):
                return zone
        return None

    def get_zone_by_name(self, zone_name: ZoneName) -> Optional[EnergyZone]:
        """Get zone by name"""
        for zone in self.energy_zones:
            if zone.zone_name == zone_name:
                return zone
        return None


@dataclass
class CurrentEnergyZoneStatus:
    """Current energy zone status for real-time queries"""
    user_id: str
    current_time: time
    active_zone: Optional[EnergyZone]
    time_remaining_minutes: int
    next_zone: Optional[EnergyZone] = None
    recommendation_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "current_time": self.current_time.isoformat(),
            "active_zone": self.active_zone.to_dict() if self.active_zone else None,
            "time_remaining_minutes": self.time_remaining_minutes,
            "next_zone": self.next_zone.to_dict() if self.next_zone else None,
            "recommendation_message": self.recommendation_message
        }


@dataclass
class PlanningEnergyZones:
    """Energy zones formatted specifically for routine planning consumption"""
    user_id: str
    foundation_zone: EnergyZone
    peak_zone: EnergyZone
    maintenance_zone: EnergyZone
    recovery_zone: EnergyZone
    detected_mode: ModeType
    time_adjustments: Dict[str, int] = field(default_factory=dict)  # Minutes to shift standard blocks

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "foundation_zone": self.foundation_zone.to_dict(),
            "peak_zone": self.peak_zone.to_dict(),
            "maintenance_zone": self.maintenance_zone.to_dict(),
            "recovery_zone": self.recovery_zone.to_dict(),
            "detected_mode": self.detected_mode.value,
            "time_adjustments": self.time_adjustments
        }


@dataclass
class RoutineWithZonesRequest:
    """Request model for generating routine with energy zones"""
    archetype: str  # User-selected archetype
    target_date: Optional[str] = None  # YYYY-MM-DD format
    force_recalculate: bool = False  # Force new zone calculation

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoutineWithZonesRequest':
        """Create from request dictionary"""
        return cls(
            archetype=data["archetype"],
            target_date=data.get("target_date"),
            force_recalculate=data.get("force_recalculate", False)
        )


# Utility functions for working with energy zones data

def calculate_energy_adjustment(base_level: int, biomarker_score: Optional[float], mode: ModeType) -> int:
    """Calculate adjusted energy level based on biomarkers and mode"""
    if biomarker_score is None:
        return base_level

    # Mode-specific adjustments
    mode_multipliers = {
        ModeType.RECOVERY: 0.7,    # Reduce energy in recovery mode
        ModeType.PRODUCTIVE: 1.0,  # Standard energy
        ModeType.PERFORMANCE: 1.2  # Boost energy in performance mode
    }

    # Biomarker influence (readiness score typically 0-100)
    biomarker_factor = (biomarker_score / 100.0) if biomarker_score <= 100 else 1.0

    # Calculate adjusted level
    adjusted = base_level * mode_multipliers[mode] * biomarker_factor

    # Ensure within bounds
    return max(0, min(100, int(adjusted)))


def format_time_range(start_time: time, end_time: time) -> str:
    """Format time range for display"""
    return f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"


def serialize_zones_for_db(zones: List[EnergyZone]) -> str:
    """Serialize zones list for database storage"""
    return json.dumps([zone.to_dict() for zone in zones])


def deserialize_zones_from_db(zones_json: str) -> List[EnergyZone]:
    """Deserialize zones list from database"""
    zones_data = json.loads(zones_json)
    return [EnergyZone.from_dict(zone_data) for zone_data in zones_data]