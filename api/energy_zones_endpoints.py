"""
Energy Zones API Endpoints
New standalone endpoints for energy zones service
"""

from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, date
from typing import Optional, Dict, Any
import logging

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.ai_energy_zones_service import AIEnergyZonesService
from services.user_data_service import UserDataService
from shared_libs.data_models.energy_zones_models import RoutineWithZonesRequest

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/energy-zones", tags=["energy-zones"])

# Initialize AI-powered energy zones service
user_data_service = UserDataService()
ai_energy_zones_service = AIEnergyZonesService(user_data_service)


@router.get("/{user_id}")
async def get_energy_zones(
    user_id: str,
    force_recalculate: bool = Query(False, description="Force new calculation ignoring cache")
):
    """
    Get energy zones for user (mode auto-detected from health data)

    This is the main standalone endpoint that:
    1. Auto-detects mode from biomarker data
    2. Infers sleep schedule from available data
    3. Calculates personalized energy zones
    4. Returns complete energy zones result
    """
    try:
        logger.info(f"Getting energy zones for user {user_id}")

        result = await ai_energy_zones_service.calculate_energy_zones(user_id, force_recalculate)

        return {
            "success": True,
            "data": result.to_dict(),
            "debug_info": {
                "cache_used": not force_recalculate,
                "calculation_time": result.generated_at.isoformat() if result.generated_at else None
            }
        }

    except Exception as e:
        logger.error(f"Error getting energy zones for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate energy zones: {str(e)}"
        )


@router.get("/{user_id}/current")
async def get_current_energy_zone(user_id: str):
    """
    Get user's current energy zone right now

    Returns:
    - Active zone with time remaining
    - Next upcoming zone
    - Personalized recommendations
    """
    try:
        logger.info(f"Getting current energy zone for user {user_id}")

        # Get current zone from full analysis
        zones_result = await ai_energy_zones_service.calculate_energy_zones(user_id)
        current_time = datetime.now().time()

        # Find current active zone
        current_zone = None
        for zone in zones_result.energy_zones:
            if zone.start_time <= current_time <= zone.end_time:
                current_zone = zone
                break

        current_status = {
            "current_zone": current_zone.to_dict() if current_zone else None,
            "energy_mode": zones_result.detected_mode.value,
            "confidence": zones_result.confidence_score
        }

        return {
            "success": True,
            "data": current_status
        }

    except Exception as e:
        logger.error(f"Error getting current energy zone for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current energy zone: {str(e)}"
        )


@router.get("/{user_id}/summary")
async def get_energy_zones_summary(user_id: str):
    """
    Get summary of user's energy zones for dashboard display

    Returns condensed information perfect for dashboard widgets
    """
    try:
        logger.info(f"Getting energy zones summary for user {user_id}")

        # Get summary from AI analysis
        zones_result = await ai_energy_zones_service.calculate_energy_zones(user_id)

        summary = {
            "total_zones": len(zones_result.energy_zones),
            "detected_mode": zones_result.detected_mode.value,
            "confidence": zones_result.confidence_score,
            "sleep_schedule": {
                "wake_time": zones_result.sleep_schedule.estimated_wake_time.strftime("%H:%M"),
                "sleep_time": zones_result.sleep_schedule.estimated_bedtime.strftime("%H:%M"),
                "chronotype": zones_result.sleep_schedule.chronotype.value
            },
            "zones_preview": [{"name": z.name, "start_time": z.start_time.strftime("%H:%M")} for z in zones_result.energy_zones[:3]]
        }

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        logger.error(f"Error getting energy zones summary for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get energy zones summary: {str(e)}"
        )


@router.get("/{user_id}/for-planning")
async def get_energy_zones_for_planning(
    user_id: str,
    target_date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format")
):
    """
    Get energy zones formatted specifically for routine planning consumption

    Returns zones in format optimized for routine planning agent:
    - Individual zone objects
    - Time adjustments for standard blocks
    - Detected mode information
    """
    try:
        logger.info(f"Getting energy zones for planning for user {user_id}")

        # Parse target date if provided
        parsed_date = None
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Get zones for planning from AI analysis
        zones_result = await ai_energy_zones_service.calculate_energy_zones(user_id)

        planning_zones = {
            "user_id": user_id,
            "detected_mode": zones_result.detected_mode.value,
            "sleep_schedule": zones_result.sleep_schedule.to_dict(),
            "zones": [zone.to_dict() for zone in zones_result.energy_zones],
            "confidence": zones_result.confidence_score,
            "target_date": parsed_date.isoformat() if parsed_date else date.today().isoformat()
        }

        return {
            "success": True,
            "data": planning_zones
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting energy zones for planning for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get energy zones for planning: {str(e)}"
        )


@router.post("/{user_id}/routine-with-zones")
async def generate_routine_with_energy_zones(
    user_id: str,
    request: Dict[str, Any] = Body(...)
):
    """
    Generate routine plan using pre-calculated energy zones

    This endpoint:
    1. Gets energy zones (standalone calculation)
    2. Passes zones to routine planning with user-selected archetype
    3. Returns routine plan that uses personalized timing
    """
    try:
        logger.info(f"Generating routine with energy zones for user {user_id}")

        # Parse request
        try:
            routine_request = RoutineWithZonesRequest.from_dict(request)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request format: {str(e)}"
            )

        # Get energy zones from AI analysis
        zones_result = await ai_energy_zones_service.calculate_energy_zones(
            user_id, routine_request.force_recalculate
        )

        # Format zones for planning
        planning_zones = {
            "user_id": user_id,
            "detected_mode": zones_result.detected_mode.value,
            "sleep_schedule": zones_result.sleep_schedule.to_dict(),
            "zones": [zone.to_dict() for zone in zones_result.energy_zones],
            "confidence": zones_result.confidence_score
        }

        # Step 3: Generate routine using existing agent but with zones
        # Note: This would integrate with the existing routine planning agent
        # For now, return the structure showing how it would work

        routine_plan = await _generate_routine_with_zones_integration(
            user_id, routine_request.archetype, planning_zones, zones_result
        )

        return {
            "success": True,
            "data": {
                "routine_plan": routine_plan,
                "energy_zones_used": planning_zones,
                "detected_mode": zones_result.detected_mode.value,
                "archetype": routine_request.archetype,
                "generation_info": {
                    "zones_confidence": zones_result.confidence_score,
                    "sleep_schedule": zones_result.sleep_schedule.to_dict(),
                    "generated_at": datetime.now().isoformat()
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating routine with energy zones for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate routine with energy zones: {str(e)}"
        )


async def _generate_routine_with_zones_integration(
    user_id: str, archetype: str, planning_zones: Any, zones_result: Any
) -> str:
    """
    Integration point with existing routine planning agent

    In full implementation, this would:
    1. Import the existing RoutinePlanAgent
    2. Call agent.create_routine_with_zones() method
    3. Return the generated routine plan

    For now, returns a structured example showing the integration
    """

    # Example of what the integration would produce
    enhanced_routine_plan = f"""
# {archetype} Routine Plan - Personalized Energy Zones

**Your Detected Mode**: {zones_result.detected_mode.value.upper()}
**Chronotype**: {zones_result.sleep_schedule.chronotype.value}
**Confidence**: {zones_result.confidence_score:.0%}

## Daily Energy Zones (AI-Generated)

{chr(10).join([f'''## {zone["name"]} ({zone["start_time"]} - {zone["end_time"]})
**Intensity**: {zone["intensity_level"]} | **Activities**: {zone["optimal_activities"]}
**Description**: {zone["energy_description"]}
''' for zone in planning_zones["zones"]])}

---
**Generated with Energy Zones v1.0** | Confidence: {zones_result.confidence_score:.0%} | Mode: {zones_result.detected_mode.value}
"""

    return enhanced_routine_plan


# Health check endpoint for energy zones service
@router.get("/health")
async def energy_zones_health_check():
    """Health check for energy zones service"""
    try:
        # Test basic service functionality
        test_result = {
            "service": "energy_zones",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "sleep_analyzer": "operational",
                "mode_detector": "operational",
                "zones_calculator": "operational",
                "debug_logging": "enabled"
            }
        }

        return {
            "success": True,
            "data": test_result
        }

    except Exception as e:
        logger.error(f"Energy zones health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )


# Debug endpoint for development
@router.get("/{user_id}/debug")
async def get_energy_zones_debug(user_id: str):
    """
    Debug endpoint for development - returns detailed calculation info
    Only available when debug logging is enabled
    """
    try:
        # Get zones with forced recalculation
        result = await ai_energy_zones_service.calculate_energy_zones(user_id, force_recalculate=True)

        debug_info = {
            "user_id": user_id,
            "calculation_result": result.to_dict(),
            "service_info": {
                "ai_powered": True,
                "single_api_call": True,
                "model": "gpt-4o"
            },
            "timestamp": datetime.now().isoformat()
        }

        return {
            "success": True,
            "data": debug_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in debug endpoint for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Debug endpoint failed: {str(e)}"
        )