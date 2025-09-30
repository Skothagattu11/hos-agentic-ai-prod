"""
Insights API Endpoints (MVP)
Simple endpoints for generating and retrieving insights
"""

        # print("🔍 [DEBUG] Loading insights_endpoints.py...")  # Commented to reduce noise

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

        # print("🔍 [DEBUG] Basic imports loaded, attempting service imports...")  # Commented to reduce noise

try:
    from ..insights_extraction_service import insights_service
        # print("🔍 [DEBUG] insights_service imported successfully")  # Commented to reduce noise
except Exception as e:
        # print(f"❌ [DEBUG] Failed to import insights_service: {e}")  # Commented to reduce noise
    insights_service = None

try:
    from ..ai_context_integration_service import AIContextIntegrationService
        # print("🔍 [DEBUG] AIContextIntegrationService imported successfully")  # Commented to reduce noise
except Exception as e:
        # print(f"❌ [DEBUG] Failed to import AIContextIntegrationService: {e}")  # Commented to reduce noise
    AIContextIntegrationService = None

try:
    import structlog
    logger = structlog.get_logger(__name__)
        # print("🔍 [DEBUG] structlog logger imported successfully")  # Commented to reduce noise
except Exception as e:
        # print(f"❌ [DEBUG] Failed to import logger: {e}")  # Commented to reduce noise
    import logging
    logger = logging.getLogger(__name__)

try:
    from ..insights_logger import insights_logger
        # print("🔍 [DEBUG] insights_logger imported successfully")  # Commented to reduce noise
except Exception as e:
        # print(f"❌ [DEBUG] Failed to import insights_logger: {e}")  # Commented to reduce noise
    insights_logger = None

# Create router
router = APIRouter(prefix="/api/v1/insights", tags=["insights"])

# Request/Response models
class InsightsRequest(BaseModel):
    user_id: str
    archetype: str = "Foundation Builder"
    force_refresh: bool = False

class InsightResponse(BaseModel):
    id: str
    title: str
    content: str
    type: str
    priority: int
    actionability_score: float
    created_at: str

class InsightsResponse(BaseModel):
    success: bool
    insights: List[InsightResponse]
    source: str  # "cached" or "fresh"
    count: int

@router.post("/generate", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest):
    """
    Generate insights from existing analysis or create new ones
    MVP version - simplified without SharedBehaviorAnalysisService
    """
    try:
        memory_service = AIContextIntegrationService()
        
        # Simple check: if force_refresh or no recent analysis, generate fresh
        source = "cached"
        
        if request.force_refresh:
            source = "fresh"
            # SIMPLIFIED: Just mark as fresh, automatic extraction already happened during analysis storage
            logger.info("Force refresh requested - retrieving latest insights from database")
        
        # Get active insights (whether fresh or cached)
        if insights_service is None:
            raise HTTPException(status_code=503, detail="Insights service not available")
            
        insights_data = await insights_service.get_user_insights(
            user_id=request.user_id,
            limit=10
        )
        
        # Convert to response format
        insights = []
        for insight in insights_data:
            insights.append(InsightResponse(
                id=insight['id'],
                title=insight['insight_title'],
                content=insight['insight_content'],
                type=insight['insight_type'],
                priority=insight['priority'],
                actionability_score=float(insight['actionability_score']),
                created_at=insight['created_at']
            ))
        
        # Log insights to files
        if insights_logger and insights:
            try:
                log_results = await insights_logger.log_insights_comprehensive(
                    insights=[insight.dict() for insight in insights],
                    source=f"insights_api_{source}",
                    user_id=request.user_id,
                    archetype=request.archetype,
                    add_to_output=True,
                    create_dedicated=True
                )
                logger.info(f"Insights logged: {log_results}")
            except Exception as log_error:
                logger.error(f"Failed to log insights: {log_error}")
        
        return InsightsResponse(
            success=True,
            insights=insights,
            source=source,
            count=len(insights)
        )
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=InsightsResponse)
async def get_user_insights(user_id: str, limit: int = 10):
    """
    Get active insights for a user (cached)
    """
    try:
        # Check if service is available
        if insights_service is None:
            raise HTTPException(status_code=503, detail="Insights service not available")
            
        # Get active insights from database
        insights_data = await insights_service.get_user_insights(
            user_id=user_id,
            limit=limit
        )
        
        # Convert to response format
        insights = []
        for insight in insights_data:
            insights.append(InsightResponse(
                id=insight['id'],
                title=insight['insight_title'],
                content=insight['insight_content'],
                type=insight['insight_type'],
                priority=insight['priority'],
                actionability_score=float(insight['actionability_score']),
                created_at=insight['created_at']
            ))
        
        return InsightsResponse(
            success=True,
            insights=insights,
            source="cached",
            count=len(insights)
        )
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{insight_id}/acknowledge")
async def acknowledge_insight(insight_id: str):
    """
    Mark an insight as acknowledged by the user
    """
    try:
        from supabase import create_client
        import os
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        client = create_client(supabase_url, supabase_key)
        result = client.table('holistic_insights').update({
            'user_acknowledged': True,
            'last_surfaced_at': datetime.utcnow().isoformat()
        }).eq('id', insight_id).execute()
        
        if result.data:
            return {"success": True, "message": "Insight acknowledged"}
        else:
            raise HTTPException(status_code=404, detail="Insight not found")
            
    except Exception as e:
        logger.error(f"Error acknowledging insight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{insight_id}/rate")
async def rate_insight(insight_id: str, rating: int, feedback: Optional[str] = None):
    """
    Rate an insight (1-5 stars)
    """
    try:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        from supabase import create_client
        import os
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        client = create_client(supabase_url, supabase_key)
        update_data = {'user_rating': rating}
        if feedback:
            update_data['user_feedback'] = feedback
            
        result = client.table('holistic_insights').update(update_data).eq('id', insight_id).execute()
        
        if result.data:
            return {"success": True, "message": f"Insight rated {rating}/5"}
        else:
            raise HTTPException(status_code=404, detail="Insight not found")
            
    except Exception as e:
        logger.error(f"Error rating insight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))