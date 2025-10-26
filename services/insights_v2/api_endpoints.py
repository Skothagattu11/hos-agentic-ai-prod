"""
Insights V2 API Endpoints - Phase 1, Sprint 1.3

Provides FastAPI endpoints for manual insights generation.
Designed to be imported into openai_main.py without conflicts.

Endpoints:
- POST /api/v2/insights/{user_id}/generate - Manual trigger for insights
- GET /api/v2/insights/{user_id}/latest - Get latest generated insights
- PATCH /api/v2/insights/{insight_id}/acknowledge - Mark insight as seen
- POST /api/v2/insights/{insight_id}/feedback - Submit user feedback
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from .data_aggregation_service import get_data_aggregation_service
from .insights_generation_service import get_insights_generation_service, Insight


# Request/Response Models
class GenerateInsightsRequest(BaseModel):
    """Request to generate insights"""
    archetype: str = Field(
        default="Foundation Builder",
        description="User archetype for personalized insights"
    )
    timeframe_days: int = Field(
        default=3,
        ge=1,
        le=14,
        description="Number of days to analyze (1-14)"
    )
    force_refresh: bool = Field(
        default=False,
        description="Force fresh generation even if recent insights exist"
    )


class InsightsFeedbackRequest(BaseModel):
    """User feedback on insight quality"""
    helpful: bool = Field(description="Was this insight helpful?")
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 star rating")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class InsightsResponse(BaseModel):
    """Response containing generated insights"""
    status: str
    user_id: str
    insights: List[Dict[str, Any]]
    generated_at: str
    metadata: Dict[str, Any]


# Create router
router = APIRouter(prefix="/api/v2/insights", tags=["Insights V2"])


@router.post("/{user_id}/generate", response_model=InsightsResponse)
async def generate_insights(
    user_id: str,
    request: GenerateInsightsRequest,
    http_request: Request
):
    """
    **Manual Trigger: Generate Fresh Insights**

    Generates personalized insights for a user based on recent health and behavioral data.

    **Data Sources:**
    - Health Data: Last 3 days from Sahha API (sleep, activity, energy, readiness)
    - Behavioral Data: Last 3 days from Supabase (task completion, check-ins)
    - Baselines: 30-day rolling averages (cached in Redis)

    **Process:**
    1. Aggregate data from Sahha API and Supabase
    2. Build comprehensive InsightContext
    3. Generate insights using AI (GPT-4o or Claude Sonnet 4)
    4. Validate quality (confidence > 0.7, actionability > 0.6)
    5. Store in Supabase
    6. Return structured insights

    **Example Response:**
    ```json
    {
      "status": "success",
      "user_id": "user123",
      "insights": [
        {
          "insight_id": "uuid",
          "category": "sleep",
          "priority": "high",
          "title": "Sleep quality improving",
          "content": "Your sleep duration increased by 15% this week",
          "recommendation": "Keep your current bedtime routine",
          "confidence_score": 0.85,
          "actionability_score": 0.90
        }
      ],
      "generated_at": "2025-10-17T10:30:00Z",
      "metadata": {
        "insights_count": 3,
        "generation_time_ms": 1200,
        "model_used": "gpt-4o"
      }
    }
    ```
    """
    try:
        # API key validation (same pattern as existing endpoints)
        api_key = http_request.headers.get("X-API-Key")
        if api_key != "hosa_flutter_app_2024":
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

        # Get services
        data_service = await get_data_aggregation_service()
        insights_service = await get_insights_generation_service()

        # Build context
        context = await data_service.build_insight_context(
            user_id=user_id,
            archetype=request.archetype,
            days=request.timeframe_days
        )

        # Generate insights
        result = await insights_service.generate_daily_insights(context)

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=result.error_message or "Failed to generate insights"
            )

        # TODO: Store insights in Supabase (Phase 1, Sprint 1.3)
        # await insights_storage_service.store_insights(result.insights, user_id)

        # Format response to match Flutter app expectations
        # Flutter expects: {success, insights, source, count}
        formatted_insights = []
        for insight in result.insights:
            insight_dict = insight.to_dict()
            # Map backend fields to Flutter expected fields
            formatted_insights.append({
                "id": insight_dict["insight_id"],
                "title": insight_dict["title"],
                "content": insight_dict["content"],
                "type": insight_dict["category"],  # Flutter expects 'type' not 'category'
                "priority": 1 if insight_dict["priority"] == "high" else 2 if insight_dict["priority"] == "medium" else 3,
                "actionability_score": insight_dict["actionability_score"],
                "created_at": insight_dict["generated_at"]
            })

        # Return format matching Flutter InsightsResponse model
        return {
            "success": True,
            "insights": formatted_insights,
            "source": "generated",
            "count": len(formatted_insights)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/{user_id}/latest")
async def get_latest_insights(
    user_id: str,
    limit: int = 10,
    category: Optional[str] = None,
    http_request: Request = None
):
    """
    **Get Latest Generated Insights**

    Retrieves the most recent insights for a user from the database.

    **Query Parameters:**
    - `limit`: Maximum number of insights to return (default: 10)
    - `category`: Filter by category (sleep, activity, energy, etc.)

    **Status:** Phase 1, Sprint 1.3 - Not yet implemented
    """
    # API key validation
    if http_request:
        api_key = http_request.headers.get("X-API-Key")
        if api_key != "hosa_flutter_app_2024":
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

    # TODO: Implement retrieval from Supabase
    return {
        "status": "not_implemented",
        "message": "Insight retrieval will be implemented in Phase 1, Sprint 1.3",
        "user_id": user_id
    }


@router.patch("/{insight_id}/acknowledge")
async def acknowledge_insight(insight_id: str, http_request: Request):
    """
    **Mark Insight as Acknowledged**

    Updates the insight status to indicate the user has seen it.

    **Status:** Phase 1, Sprint 1.3 - Not yet implemented
    """
    # API key validation
    if http_request:
        api_key = http_request.headers.get("X-API-Key")
        if api_key != "hosa_flutter_app_2024":
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

    # TODO: Implement acknowledgment in Supabase
    return {
        "status": "not_implemented",
        "message": "Insight acknowledgment will be implemented in Phase 1, Sprint 1.3",
        "insight_id": insight_id
    }


@router.post("/{insight_id}/feedback")
async def submit_feedback(
    insight_id: str,
    feedback: InsightsFeedbackRequest,
    http_request: Request
):
    """
    **Submit User Feedback on Insight**

    Allows users to rate and provide feedback on insight quality.
    Feedback is used to improve future insights generation.

    **Status:** Phase 1, Sprint 1.3 - Not yet implemented
    """
    # API key validation
    if http_request:
        api_key = http_request.headers.get("X-API-Key")
        if api_key != "hosa_flutter_app_2024":
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

    # TODO: Implement feedback storage in Supabase
    return {
        "status": "not_implemented",
        "message": "Feedback submission will be implemented in Phase 1, Sprint 1.3",
        "insight_id": insight_id
    }


# Health check endpoint for insights service
@router.get("/health")
async def insights_health_check():
    """Health check for insights v2 service"""
    return {
        "status": "healthy",
        "service": "insights_v2",
        "phase": "Phase 1 - Daily Insights MVP",
        "endpoints_available": [
            "POST /api/v2/insights/{user_id}/generate",
            "GET /api/v2/insights/{user_id}/latest",
            "PATCH /api/v2/insights/{insight_id}/acknowledge",
            "POST /api/v2/insights/{insight_id}/feedback"
        ]
    }
