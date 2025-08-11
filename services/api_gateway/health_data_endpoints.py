"""
Health Data Endpoints for HolisticOS MVP - Phase 2 Implementation
CTO Design: Simple, Production-Ready, Easy to Debug FastAPI Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum

# Import our Phase 1 components
from ..user_data_service import UserDataService, get_user_health_data
from shared_libs.data_models.health_models import UserHealthContext, ArchetypeType, DataQualityLevel

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/health-data", tags=["health-data"])

# Pydantic models for API responses - clean and type-safe
class HealthDataResponse(BaseModel):
    """Standard health data response"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class DataQualityResponse(BaseModel):
    """Data quality assessment response"""
    quality_level: DataQualityLevel
    completeness_score: float
    scores_count: int
    biomarkers_count: int
    archetypes_count: int
    has_recent_data: bool
    recommendations: List[str] = Field(default_factory=list)

class AnalysisRequest(BaseModel):
    """Request model for triggering analysis"""
    archetype: ArchetypeType
    analysis_type: str = Field(default="complete", pattern="^(behavior|nutrition|routine|complete)$")
    days: int = Field(default=7, ge=1, le=30)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")

class UserHealthSummary(BaseModel):
    """Compact user health summary"""
    user_id: str
    data_quality: DataQualityLevel
    latest_scores: List[Dict[str, Any]] = Field(default_factory=list)
    archetype: Optional[str] = None
    last_analysis: Optional[datetime] = None
    agent_readiness: Dict[str, bool] = Field(default_factory=dict)

# Utility functions
async def get_user_service() -> UserDataService:
    """Dependency injection for UserDataService"""
    return UserDataService()

def calculate_agent_readiness(user_context: UserHealthContext) -> Dict[str, bool]:
    """Calculate which agents have sufficient data to run analysis"""
    quality = user_context.data_quality
    
    return {
        "behavior_agent": quality.scores_count >= 3,
        "memory_agent": quality.has_recent_data,
        "nutrition_agent": quality.completeness_score >= 0.3,
        "routine_agent": quality.scores_count >= 1,
        "adaptation_agent": quality.completeness_score >= 0.5,
        "insights_agent": quality.scores_count + quality.biomarkers_count >= 2
    }

# Main endpoints
@router.get(
    "/users/{user_id}/health-context",
    response_model=HealthDataResponse,
    summary="Get complete user health context",
    description="Fetch comprehensive health data for all 6 agents with quality metrics"
)
async def get_user_health_context(
    user_id: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to fetch"),
    include_agent_views: bool = Query(default=True, description="Include agent-specific data views"),
    service: UserDataService = Depends(get_user_service)
) -> HealthDataResponse:
    """
    Main endpoint for getting user health context - designed for 6-agent system
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"[ENDPOINT] Getting health context for user {user_id}, {days} days")
        
        # Get comprehensive user data
        user_context = await service.get_user_health_data(user_id, days)
        
        # Prepare response data
        response_data = {
            "user_id": user_context.user_id,
            "date_range": {
                "start_date": user_context.date_range.start_date.isoformat(),
                "end_date": user_context.date_range.end_date.isoformat(),
                "days": user_context.date_range.days
            },
            "data_quality": {
                "quality_level": user_context.data_quality.quality_level,
                "completeness_score": user_context.data_quality.completeness_score,
                "scores_count": user_context.data_quality.scores_count,
                "biomarkers_count": user_context.data_quality.biomarkers_count,
                "archetypes_count": user_context.data_quality.archetypes_count,
                "has_recent_data": user_context.data_quality.has_recent_data
            },
            "raw_data": {
                "scores": [score.dict() for score in user_context.scores],
                "biomarkers": [bio.dict() for bio in user_context.biomarkers],
                "archetypes": [arch.dict() for arch in user_context.archetypes]
            }
        }
        
        # Add agent-specific views if requested
        if include_agent_views:
            response_data["agent_views"] = {
                "behavior_data": user_context.behavior_data,
                "memory_data": user_context.memory_data,
                "nutrition_data": user_context.nutrition_data,
                "routine_data": user_context.routine_data,
                "adaptation_data": user_context.adaptation_data,
                "insights_data": user_context.insights_data
            }
        
        # Calculate agent readiness
        agent_readiness = calculate_agent_readiness(user_context)
        response_data["agent_readiness"] = agent_readiness
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return HealthDataResponse(
            success=True,
            data=response_data,
            metadata={
                "fetch_duration_seconds": duration,
                "api_source": "database_fallback" if not user_context.data_quality.has_recent_data else "api_primary",
                "cache_used": False,  # Will implement cache tracking later
                "data_freshness": user_context.fetch_timestamp.isoformat(),
                "ready_agents": sum(1 for ready in agent_readiness.values() if ready),
                "total_agents": len(agent_readiness)
            }
        )
        
    except Exception as e:
        logger.error(f"[ENDPOINT_ERROR] Failed to get health context for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch health data for user {user_id}: {str(e)}"
        )
    finally:
        await service.cleanup()

@router.get(
    "/users/{user_id}/summary",
    response_model=UserHealthSummary,
    summary="Get user health summary",
    description="Quick health overview for dashboard display"
)
async def get_user_health_summary(
    user_id: str,
    service: UserDataService = Depends(get_user_service)
) -> UserHealthSummary:
    """
    Quick user health summary - optimized for dashboard/overview display
    """
    try:
        logger.info(f"[ENDPOINT] Getting health summary for user {user_id}")
        
        # Get basic user data (3 days for speed)
        user_context = await service.get_user_health_data(user_id, days=3)
        
        # Get latest scores (limit to 5 for summary)
        latest_scores = []
        for score in user_context.scores[:5]:
            latest_scores.append({
                "type": score.type,
                "score": score.score,
                "date": score.created_at.isoformat()
            })
        
        # Get current archetype
        current_archetype = None
        if user_context.archetypes:
            current_archetype = user_context.archetypes[0].name
        
        # Calculate agent readiness
        agent_readiness = calculate_agent_readiness(user_context)
        
        return UserHealthSummary(
            user_id=user_id,
            data_quality=user_context.data_quality.quality_level,
            latest_scores=latest_scores,
            archetype=current_archetype,
            last_analysis=user_context.fetch_timestamp,
            agent_readiness=agent_readiness
        )
        
    except Exception as e:
        logger.error(f"[ENDPOINT_ERROR] Failed to get health summary for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch health summary for user {user_id}: {str(e)}"
        )
    finally:
        await service.cleanup()

@router.get(
    "/users/{user_id}/data-quality",
    response_model=DataQualityResponse,
    summary="Assess data quality for user",
    description="Get detailed data quality metrics and recommendations"
)
async def get_data_quality_assessment(
    user_id: str,
    days: int = Query(default=7, ge=1, le=30),
    service: UserDataService = Depends(get_user_service)
) -> DataQualityResponse:
    """
    Data quality assessment endpoint - helps troubleshoot data issues
    """
    try:
        logger.info(f"[ENDPOINT] Assessing data quality for user {user_id}")
        
        user_context = await service.get_user_health_data(user_id, days)
        quality = user_context.data_quality
        
        # Generate recommendations based on data quality
        recommendations = []
        if quality.scores_count == 0:
            recommendations.append("No health scores found - check wearable device connection")
        elif quality.scores_count < 5:
            recommendations.append("Limited health scores - encourage more consistent device usage")
            
        if quality.biomarkers_count == 0:
            recommendations.append("No biomarker data available - ensure comprehensive health tracking")
            
        if quality.archetypes_count == 0:
            recommendations.append("No archetype data - user may need initial health assessment")
            
        if quality.completeness_score < 0.3:
            recommendations.append("Low data completeness - recommend data sync or device troubleshooting")
        elif quality.completeness_score < 0.7:
            recommendations.append("Moderate data completeness - some analysis features may be limited")
            
        if not quality.has_recent_data:
            recommendations.append("No recent data - check device connectivity and sync status")
        
        if not recommendations:
            recommendations.append("Data quality is good - all analysis features available")
        
        return DataQualityResponse(
            quality_level=quality.quality_level,
            completeness_score=quality.completeness_score,
            scores_count=quality.scores_count,
            biomarkers_count=quality.biomarkers_count,
            archetypes_count=quality.archetypes_count,
            has_recent_data=quality.has_recent_data,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"[ENDPOINT_ERROR] Failed to assess data quality for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess data quality for user {user_id}: {str(e)}"
        )
    finally:
        await service.cleanup()

@router.get(
    "/users/{user_id}/agent/{agent_name}/data",
    response_model=HealthDataResponse,
    summary="Get agent-specific data",
    description="Fetch data prepared for a specific agent"
)
async def get_agent_specific_data(
    user_id: str,
    agent_name: str,
    days: int = Query(default=7, ge=1, le=30),
    service: UserDataService = Depends(get_user_service)
) -> HealthDataResponse:
    """
    Agent-specific data endpoint - optimized for individual agent needs
    """
    # Validate agent name
    valid_agents = ["behavior", "memory", "nutrition", "routine", "adaptation", "insights"]
    if agent_name not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent name. Must be one of: {', '.join(valid_agents)}"
        )
    
    try:
        logger.info(f"[ENDPOINT] Getting {agent_name} agent data for user {user_id}")
        
        user_context = await service.get_user_health_data(user_id, days)
        
        # Get agent-specific data
        agent_data_map = {
            "behavior": user_context.behavior_data,
            "memory": user_context.memory_data,
            "nutrition": user_context.nutrition_data,
            "routine": user_context.routine_data,
            "adaptation": user_context.adaptation_data,
            "insights": user_context.insights_data
        }
        
        agent_data = agent_data_map[agent_name]
        
        # Check if agent has sufficient data
        agent_readiness = calculate_agent_readiness(user_context)
        is_ready = agent_readiness.get(f"{agent_name}_agent", False)
        
        return HealthDataResponse(
            success=True,
            data={
                "agent_name": agent_name,
                "user_id": user_id,
                "agent_data": agent_data,
                "is_ready": is_ready,
                "data_quality": user_context.data_quality.dict()
            },
            metadata={
                "agent_ready": is_ready,
                "data_completeness": user_context.data_quality.completeness_score,
                "recommendation": "Agent ready for analysis" if is_ready else f"Insufficient data for {agent_name} agent"
            }
        )
        
    except Exception as e:
        logger.error(f"[ENDPOINT_ERROR] Failed to get {agent_name} data for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch {agent_name} data for user {user_id}: {str(e)}"
        )
    finally:
        await service.cleanup()

@router.post(
    "/users/{user_id}/analyze",
    response_model=HealthDataResponse,
    summary="Trigger health analysis",
    description="Start health analysis with real user data - integrates with 6-agent system"
)
async def trigger_health_analysis(
    user_id: str,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    service: UserDataService = Depends(get_user_service)
) -> HealthDataResponse:
    """
    Trigger analysis endpoint - designed to integrate with existing orchestrator
    """
    try:
        logger.info(f"[ENDPOINT] Triggering {request.analysis_type} analysis for user {user_id} with {request.archetype} archetype")
        
        # Get user data first to validate
        user_context = await service.get_user_health_data(user_id, request.days)
        
        # Check data quality
        if user_context.data_quality.quality_level == DataQualityLevel.POOR and request.priority != "urgent":
            logger.warning(f"[ENDPOINT] Poor data quality for {user_id}, but proceeding with analysis")
        
        # Calculate agent readiness
        agent_readiness = calculate_agent_readiness(user_context)
        ready_agents = sum(1 for ready in agent_readiness.values() if ready)
        
        # Create analysis task ID
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # For MVP: Return immediately with analysis context
        # In Phase 3, this will integrate with your orchestrator
        analysis_response = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "archetype": request.archetype,
            "analysis_type": request.analysis_type,
            "status": "queued",
            "user_data_summary": {
                "scores_count": user_context.data_quality.scores_count,
                "biomarkers_count": user_context.data_quality.biomarkers_count,
                "data_quality": user_context.data_quality.quality_level,
                "ready_agents": ready_agents,
                "total_agents": len(agent_readiness)
            },
            "estimated_completion": "2-5 minutes",
            "next_steps": [
                f"Connect to analysis stream at /api/v1/health-data/analysis/{analysis_id}/stream",
                "Monitor analysis progress via Server-Sent Events",
                "Results will be available via analysis status endpoint"
            ]
        }
        
        # Background task would integrate with orchestrator here
        # background_tasks.add_task(run_analysis_with_orchestrator, analysis_id, user_context, request)
        
        return HealthDataResponse(
            success=True,
            data=analysis_response,
            metadata={
                "ready_for_orchestrator": True,
                "user_data_fetched": True,
                "agent_readiness": agent_readiness
            }
        )
        
    except Exception as e:
        logger.error(f"[ENDPOINT_ERROR] Failed to trigger analysis for {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger analysis for user {user_id}: {str(e)}"
        )
    finally:
        await service.cleanup()

@router.get(
    "/system/health",
    response_model=HealthDataResponse,
    summary="System health check",
    description="Check health of data fetching system"
)
async def system_health_check(
    service: UserDataService = Depends(get_user_service)
) -> HealthDataResponse:
    """
    System health endpoint - monitoring for production
    """
    try:
        # Check service health
        health_result = await service.health_check()
        
        # Check API client health
        api_health = await service.api_client.health_check()
        
        overall_status = "healthy" if (
            health_result["status"] == "healthy" and 
            api_health["api_status"] == "healthy"
        ) else "degraded"
        
        return HealthDataResponse(
            success=overall_status == "healthy",
            data={
                "system_status": overall_status,
                "database_status": health_result["status"],
                "api_client_status": api_health["api_status"],
                "cache_size": health_result.get("cache_size", 0),
                "api_stats": api_health.get("request_stats", {}),
                "components": {
                    "user_data_service": health_result["status"],
                    "health_data_client": api_health["api_status"],
                    "supabase_adapter": "healthy" if health_result.get("profiles_accessible") else "unknown"
                }
            },
            metadata={
                "last_check": datetime.now().isoformat(),
                "uptime_check": True,
                "monitoring_ready": True
            }
        )
        
    except Exception as e:
        logger.error(f"[ENDPOINT_ERROR] System health check failed: {e}")
        return HealthDataResponse(
            success=False,
            data={
                "system_status": "unhealthy",
                "error": str(e)
            },
            metadata={
                "last_check": datetime.now().isoformat(),
                "error_occurred": True
            }
        )
    finally:
        await service.cleanup()

# Export router for easy integration
__all__ = ["router"]