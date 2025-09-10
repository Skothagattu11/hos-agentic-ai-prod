"""
Analysis Results API Endpoints
Direct access to holistic_analysis_results table for fetching analysis IDs
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from supabase import create_client, Client
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Get Supabase client using environment variables"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    
    return create_client(supabase_url, supabase_key)

# Create router
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

class AnalysisResult(BaseModel):
    """Model for analysis result data"""
    id: str
    user_id: str
    archetype: str
    analysis_type: str
    analysis_date: Optional[str]
    created_at: str
    has_time_blocks: bool = False
    has_plan_items: bool = False
    time_blocks_count: int = 0
    plan_items_count: int = 0

class UserAnalysesResponse(BaseModel):
    """Response model for user analyses"""
    user_id: str
    target_date: str
    analyses: List[AnalysisResult]
    most_recent_with_data: Optional[AnalysisResult] = None
    total_count: int

@router.get("/user/{user_id}/results")
async def get_user_analysis_results(
    user_id: str = Path(..., description="User ID"),
    target_date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format"),
    include_extracted: bool = Query(True, description="Include extraction status (time_blocks/plan_items)"),
    limit: int = Query(10, description="Maximum number of results to return")
):
    """
    Get analysis results from holistic_analysis_results table for a user
    
    This endpoint directly queries the holistic_analysis_results table and optionally
    checks for extracted time_blocks and plan_items.
    
    Returns:
    - List of analysis results with their IDs
    - Extraction status (whether time_blocks/plan_items exist)
    - Most recent analysis that has extracted data
    """
    try:
        supabase = get_supabase_client()
        
        # Use provided date or today
        query_date = target_date if target_date else date.today().isoformat()
        logger.info(f"Fetching analysis results for user {user_id}, date: {query_date}")
        
        # Build base query
        query = supabase.table("holistic_analysis_results")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)
        
        # Optionally filter by date
        if target_date:
            # Filter by analysis_date matching the target date
            query = query.eq("analysis_date", query_date)
        
        # Execute query
        result = query.execute()
        
        if not result.data:
            logger.warning(f"No analysis results found for user {user_id}")
            return UserAnalysesResponse(
                user_id=user_id,
                target_date=query_date,
                analyses=[],
                most_recent_with_data=None,
                total_count=0
            )
        
        analyses = []
        most_recent_with_data = None
        
        for analysis in result.data:
            analysis_obj = AnalysisResult(
                id=analysis['id'],
                user_id=analysis['user_id'],
                archetype=analysis.get('archetype', 'Unknown'),
                analysis_type=analysis.get('analysis_type', 'Unknown'),
                analysis_date=analysis.get('analysis_date'),
                created_at=analysis['created_at']
            )
            
            # Check for extracted data if requested
            if include_extracted:
                # Check time_blocks
                time_blocks_result = supabase.table("time_blocks")\
                    .select("id")\
                    .eq("analysis_result_id", analysis['id'])\
                    .execute()
                
                # Check plan_items
                plan_items_result = supabase.table("plan_items")\
                    .select("id")\
                    .eq("analysis_result_id", analysis['id'])\
                    .execute()
                
                analysis_obj.has_time_blocks = len(time_blocks_result.data) > 0
                analysis_obj.has_plan_items = len(plan_items_result.data) > 0
                analysis_obj.time_blocks_count = len(time_blocks_result.data)
                analysis_obj.plan_items_count = len(plan_items_result.data)
                
                # Track most recent with data
                if (analysis_obj.has_time_blocks or analysis_obj.has_plan_items) and not most_recent_with_data:
                    most_recent_with_data = analysis_obj
            
            analyses.append(analysis_obj)
        
        return UserAnalysesResponse(
            user_id=user_id,
            target_date=query_date,
            analyses=analyses,
            most_recent_with_data=most_recent_with_data,
            total_count=len(analyses)
        )
        
    except Exception as e:
        logger.error(f"Error fetching analysis results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis results: {str(e)}")

@router.get("/user/{user_id}/latest-with-data")
async def get_latest_analysis_with_data(
    user_id: str = Path(..., description="User ID"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type (e.g., 'routine_plan', 'nutrition_plan')")
):
    """
    Get the most recent analysis that has extracted time_blocks and/or plan_items
    
    This is useful for finding the analysis_result_id that should be used for
    displaying plan items or triggering extraction.
    """
    try:
        supabase = get_supabase_client()
        
        logger.info(f"Finding latest analysis with data for user {user_id}")
        
        # Get recent analyses
        query = supabase.table("holistic_analysis_results")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(20)  # Check last 20 analyses
        
        if analysis_type:
            query = query.eq("analysis_type", analysis_type)
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No analyses found for user {user_id}")
        
        # Check each analysis for extracted data
        for analysis in result.data:
            # Check if this analysis has time_blocks
            time_blocks_result = supabase.table("time_blocks")\
                .select("id")\
                .eq("analysis_result_id", analysis['id'])\
                .limit(1)\
                .execute()
            
            # Check if this analysis has plan_items
            plan_items_result = supabase.table("plan_items")\
                .select("id")\
                .eq("analysis_result_id", analysis['id'])\
                .limit(1)\
                .execute()
            
            # If either exists, this is our target
            if time_blocks_result.data or plan_items_result.data:
                return {
                    "analysis_result_id": analysis['id'],
                    "user_id": analysis['user_id'],
                    "archetype": analysis.get('archetype', 'Unknown'),
                    "analysis_type": analysis.get('analysis_type', 'Unknown'),
                    "analysis_date": analysis.get('analysis_date'),
                    "created_at": analysis['created_at'],
                    "has_time_blocks": len(time_blocks_result.data) > 0,
                    "has_plan_items": len(plan_items_result.data) > 0,
                    "message": "Found analysis with extracted data"
                }
        
        # No analysis with extracted data found
        # Return the most recent analysis anyway for potential extraction
        most_recent = result.data[0]
        return {
            "analysis_result_id": most_recent['id'],
            "user_id": most_recent['user_id'],
            "archetype": most_recent.get('archetype', 'Unknown'),
            "analysis_type": most_recent.get('analysis_type', 'Unknown'),
            "analysis_date": most_recent.get('analysis_date'),
            "created_at": most_recent['created_at'],
            "has_time_blocks": False,
            "has_plan_items": False,
            "message": "No analysis with extracted data found, returning most recent",
            "needs_extraction": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding latest analysis with data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find analysis: {str(e)}")

@router.get("/result/{analysis_id}/status")
async def get_analysis_extraction_status(
    analysis_id: str = Path(..., description="Analysis Result ID")
):
    """
    Check extraction status for a specific analysis result
    
    Returns whether time_blocks and plan_items have been extracted
    """
    try:
        supabase = get_supabase_client()
        
        # Get the analysis
        analysis_result = supabase.table("holistic_analysis_results")\
            .select("*")\
            .eq("id", analysis_id)\
            .single()\
            .execute()
        
        if not analysis_result.data:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        
        # Check time_blocks
        time_blocks_result = supabase.table("time_blocks")\
            .select("id, block_title, time_range")\
            .eq("analysis_result_id", analysis_id)\
            .execute()
        
        # Check plan_items  
        plan_items_result = supabase.table("plan_items")\
            .select("id, title, time_block")\
            .eq("analysis_result_id", analysis_id)\
            .execute()
        
        return {
            "analysis_result_id": analysis_id,
            "user_id": analysis_result.data['user_id'],
            "archetype": analysis_result.data.get('archetype', 'Unknown'),
            "analysis_type": analysis_result.data.get('analysis_type', 'Unknown'),
            "analysis_date": analysis_result.data.get('analysis_date'),
            "created_at": analysis_result.data['created_at'],
            "extraction_status": {
                "has_time_blocks": len(time_blocks_result.data) > 0,
                "time_blocks_count": len(time_blocks_result.data),
                "time_blocks": [
                    {"id": tb['id'], "title": tb['block_title'], "time_range": tb['time_range']}
                    for tb in time_blocks_result.data[:5]  # First 5 for preview
                ],
                "has_plan_items": len(plan_items_result.data) > 0,
                "plan_items_count": len(plan_items_result.data),
                "plan_items_preview": [
                    {"id": pi['id'], "title": pi['title'], "time_block": pi['time_block']}
                    for pi in plan_items_result.data[:5]  # First 5 for preview
                ]
            },
            "needs_extraction": len(time_blocks_result.data) == 0 and len(plan_items_result.data) == 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking extraction status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")

@router.post("/user/{user_id}/extract-latest")
async def extract_latest_unprocessed_analysis(
    user_id: str = Path(..., description="User ID"),
    analysis_type: Optional[str] = Query("routine_plan", description="Type of analysis to extract")
):
    """
    Find and extract the most recent unprocessed analysis for a user
    
    This is a convenience endpoint that:
    1. Finds the most recent analysis without extracted data
    2. Triggers extraction automatically
    3. Returns the extraction results
    """
    try:
        supabase = get_supabase_client()
        
        logger.info(f"Finding unprocessed analysis for user {user_id}")
        
        # Get recent analyses
        query = supabase.table("holistic_analysis_results")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("analysis_type", analysis_type)\
            .order("created_at", desc=True)\
            .limit(10)
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No {analysis_type} analyses found for user {user_id}")
        
        # Find first analysis without extracted data
        target_analysis = None
        for analysis in result.data:
            # Check if this analysis has plan_items
            plan_items_result = supabase.table("plan_items")\
                .select("id")\
                .eq("analysis_result_id", analysis['id'])\
                .limit(1)\
                .execute()
            
            # If no plan items, this needs extraction
            if not plan_items_result.data:
                target_analysis = analysis
                break
        
        if not target_analysis:
            # All analyses already have extracted data
            return {
                "message": "All recent analyses already have extracted data",
                "most_recent_id": result.data[0]['id'] if result.data else None
            }
        
        # Import and use the extraction service
        from services.plan_extraction_service import PlanExtractionService
        
        extraction_service = PlanExtractionService()
        
        # Trigger extraction
        logger.info(f"Extracting plan items for analysis {target_analysis['id']}")
        extracted_items = await extraction_service.extract_and_store_plan_items(
            target_analysis['id'],
            user_id,
            target_analysis.get('analysis_date')
        )
        
        return {
            "success": True,
            "message": f"Successfully extracted {len(extracted_items)} items",
            "analysis_result_id": target_analysis['id'],
            "archetype": target_analysis.get('archetype'),
            "analysis_date": target_analysis.get('analysis_date'),
            "created_at": target_analysis['created_at'],
            "items_extracted": len(extracted_items),
            "items": extracted_items[:5]  # Return first 5 items as preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract_latest_unprocessed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract: {str(e)}")