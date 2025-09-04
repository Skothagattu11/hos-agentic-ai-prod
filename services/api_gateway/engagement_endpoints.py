"""
User Engagement API Endpoints

This module provides FastAPI endpoints for the dual engagement system:
1. Task check-in tracking (granular completion data)
2. Daily journaling (holistic reflection data)  
3. Plan management (extract and retrieve plan items)
"""

import asyncio
import logging
from datetime import date, datetime, time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from services.plan_extraction_service import PlanExtractionService
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from shared_libs.exceptions.holisticos_exceptions import HolisticOSException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/engagement", tags=["user-engagement"])

# =====================================================
# Pydantic Models
# =====================================================

class CompletionStatus(str, Enum):
    completed = "completed"
    partial = "partial"
    skipped = "skipped"

class NutritionStatus(str, Enum):
    on_track = "on_track"
    mostly = "mostly"
    off_track = "off_track"

# Task Check-in Models
class TaskCheckInRequest(BaseModel):
    """Request model for individual task completion check-in"""
    profile_id: str = Field(..., description="User profile ID")
    plan_item_id: str = Field(..., description="Plan item UUID")
    analysis_result_id: Optional[str] = Field(None, description="Analysis result UUID") 
    completion_status: CompletionStatus = Field(..., description="Task completion status")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="Task satisfaction rating")
    planned_date: date = Field(..., description="Date the task was planned for")
    user_notes: Optional[str] = Field(None, max_length=500, description="Optional user notes")
    
    @validator('satisfaction_rating')
    def validate_satisfaction_for_completed(cls, v, values):
        """Satisfaction rating recommended for completed tasks"""
        if values.get('completion_status') == CompletionStatus.completed and v is None:
            # Don't require it, but log for analytics
            pass
        return v

class TaskCheckInResponse(BaseModel):
    """Response model for task check-in"""
    success: bool
    message: str
    task_checkin_id: Optional[str] = None
    completion_status: Optional[CompletionStatus] = None

# Daily Journal Models
class DailyJournalRequest(BaseModel):
    """Request model for daily journal submission"""
    profile_id: str = Field(..., description="User profile ID")
    journal_date: date = Field(..., description="Date of the journal entry")
    
    # Overall day assessment (1-5 scales)
    energy_level: Optional[int] = Field(None, ge=1, le=5, description="Energy level rating")
    mood_rating: Optional[int] = Field(None, ge=1, le=5, description="Mood rating")
    sleep_quality: Optional[int] = Field(None, ge=1, le=5, description="Sleep quality rating")
    stress_level: Optional[int] = Field(None, ge=1, le=5, description="Stress level rating")
    
    # Nutrition summary
    nutrition_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="Nutrition satisfaction")
    hydration_glasses: Optional[int] = Field(None, ge=0, description="Glasses of water consumed")
    meal_timing_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="Meal timing satisfaction")
    
    # Habit completions
    breathing_exercises_completed: Optional[bool] = Field(None, description="Breathing exercises completed")
    sunlight_exposure_completed: Optional[bool] = Field(None, description="Sunlight exposure completed")
    mindfulness_practice_completed: Optional[bool] = Field(None, description="Mindfulness practice completed")
    
    # Reflection fields
    what_went_well: Optional[str] = Field(None, max_length=1000, description="Positive reflections")
    what_was_challenging: Optional[str] = Field(None, max_length=1000, description="Challenges faced")
    tomorrow_intentions: Optional[str] = Field(None, max_length=1000, description="Plans for tomorrow")
    gratitude_notes: Optional[List[str]] = Field(None, description="Gratitude notes")
    
    # Voice notes
    voice_note_url: Optional[str] = Field(None, description="Voice note URL")
    voice_note_duration_seconds: Optional[int] = Field(None, ge=1, description="Voice note duration")
    
    # Completion metadata
    time_to_complete_seconds: Optional[int] = Field(None, ge=1, description="Time taken to complete journal")

class DailyJournalResponse(BaseModel):
    """Response model for daily journal submission"""
    success: bool
    message: str
    journal_id: Optional[str] = None

# Plan Management Models
class PlanExtractionRequest(BaseModel):
    """Request model for extracting plan items"""
    analysis_result_id: str = Field(..., description="Analysis result ID to extract from")
    profile_id: str = Field(..., description="User profile ID")

class PlanItemResponse(BaseModel):
    """Response model for plan items"""
    id: str
    item_id: str
    title: str
    description: Optional[str]
    scheduled_time: Optional[str]
    estimated_duration_minutes: Optional[int]
    task_type: str
    time_block: str
    is_completed: Optional[bool] = None
    completion_status: Optional[str] = None
    satisfaction_rating: Optional[int] = None

class CurrentPlanResponse(BaseModel):
    """Response model for current user plans"""
    routine_plan: Optional[Dict[str, Any]]
    nutrition_plan: Optional[Dict[str, Any]]
    items: List[PlanItemResponse]
    date: str

# =====================================================
# Dependency Injection
# =====================================================

async def get_supabase() -> Client:
    """Get Supabase client instance with proper service role authentication"""
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL is required")
    
    # Prefer service key for API operations (bypasses RLS)
    if service_key:
        print(f"✅ Using SUPABASE_SERVICE_KEY for admin operations")
        return create_client(supabase_url, service_key)
    elif anon_key:
        print(f"⚠️ Using SUPABASE_KEY (anon) - RLS policies will apply")
        return create_client(supabase_url, anon_key)
    else:
        raise ValueError("Either SUPABASE_SERVICE_KEY or SUPABASE_KEY is required")

async def get_plan_service() -> PlanExtractionService:
    """Get plan extraction service instance"""
    return PlanExtractionService()

# =====================================================
# Task Check-in Endpoints
# =====================================================

@router.post("/task-checkin", response_model=TaskCheckInResponse)
async def submit_task_checkin(
    request: TaskCheckInRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Submit a task completion check-in
    
    This endpoint allows users to mark individual tasks as completed, partial, or skipped
    with optional satisfaction ratings and notes.
    """
    try:
        # Get analysis_result_id if not provided
        analysis_result_id = request.analysis_result_id
        if not analysis_result_id:
            # Look up analysis_result_id from plan_items table
            plan_item_result = supabase.table("plan_items")\
                .select("analysis_result_id")\
                .eq("id", request.plan_item_id)\
                .execute()
            
            if plan_item_result.data:
                analysis_result_id = plan_item_result.data[0]["analysis_result_id"]
            else:
                raise HTTPException(status_code=404, detail="Plan item not found")
        
        # Prepare data for insertion
        checkin_data = {
            'profile_id': request.profile_id,
            'plan_item_id': request.plan_item_id,
            'analysis_result_id': analysis_result_id,
            'completion_status': request.completion_status.value,
            'satisfaction_rating': request.satisfaction_rating,
            'planned_date': request.planned_date.isoformat(),
            'user_notes': request.user_notes,
            'completed_at': datetime.now().isoformat() if request.completion_status != CompletionStatus.skipped else None,
            'actual_completion_time': datetime.now().isoformat() if request.completion_status != CompletionStatus.skipped else None
        }
        
        # Use upsert to handle updates to existing check-ins
        result = supabase.table("task_checkins")\
            .upsert(checkin_data, on_conflict="profile_id,plan_item_id,planned_date")\
            .execute()
        
        if result.data:
            logger.info(f"Task check-in recorded for profile {request.profile_id}, task {request.plan_item_id}")
            return TaskCheckInResponse(
                success=True,
                message="Task check-in recorded successfully",
                task_checkin_id=result.data[0]["id"],
                completion_status=request.completion_status
            )
        else:
            raise HolisticOSException("Failed to record task check-in")
            
    except Exception as e:
        logger.error(f"Error recording task check-in: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record task check-in: {str(e)}")

@router.get("/tasks/{profile_id}")
async def get_user_tasks(
    profile_id: str,
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format"),
    plan_service: PlanExtractionService = Depends(get_plan_service),
    supabase: Client = Depends(get_supabase)
):
    """
    Get user's tasks for a specific date with completion status
    
    Returns the user's current plan items organized by time blocks with their completion status.
    """
    try:
        # Use provided date or default to today
        target_date = date.fromisoformat(date_param) if date_param else date.today()
        
        # Get current plan items for user
        plan_data = await plan_service.get_current_plan_items_for_user(
            profile_id, target_date.isoformat()
        )
        
        # Get completion status for the target date
        checkin_result = supabase.table("task_checkins")\
            .select("plan_item_id, completion_status, satisfaction_rating, completed_at")\
            .eq("profile_id", profile_id)\
            .eq("planned_date", target_date.isoformat())\
            .execute()
        
        # Create completion lookup
        completions = {
            item["plan_item_id"]: item 
            for item in checkin_result.data or []
        }
        
        # Organize items by time blocks
        time_blocks = {}
        for item in plan_data["items"]:
            time_block = item["time_block"]
            if time_block not in time_blocks:
                time_blocks[time_block] = []
            
            # Add completion status
            completion_data = completions.get(item["id"], {})
            item["is_completed"] = completion_data.get("completion_status") == "completed"
            item["completion_status"] = completion_data.get("completion_status")
            item["satisfaction_rating"] = completion_data.get("satisfaction_rating")
            item["completed_at"] = completion_data.get("completed_at")
            
            time_blocks[time_block].append(item)
        
        # Convert to ordered list
        ordered_blocks = []
        for block_name, tasks in time_blocks.items():
            # Sort tasks by order within block
            tasks.sort(key=lambda x: x.get("task_order_in_block", 0))
            ordered_blocks.append({
                "name": block_name,
                "tasks": tasks
            })
        
        # Sort blocks by order
        ordered_blocks.sort(key=lambda x: min(task.get("time_block_order", 0) for task in x["tasks"]) if x["tasks"] else 0)
        
        return {
            "date": target_date.isoformat(),
            "plan_info": {
                "routine_plan": plan_data["routine_plan"],
                "nutrition_plan": plan_data["nutrition_plan"]
            },
            "time_blocks": ordered_blocks
        }
        
    except Exception as e:
        logger.error(f"Error fetching user tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

# =====================================================
# Daily Journal Endpoints
# =====================================================

@router.post("/journal", response_model=DailyJournalResponse)
async def submit_daily_journal(
    request: DailyJournalRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Submit a daily journal entry
    
    This endpoint captures holistic daily reflection data including wellbeing ratings,
    habit completions, and qualitative reflections.
    """
    try:
        # Prepare data for insertion
        journal_data = {
            'profile_id': request.profile_id,
            'journal_date': request.journal_date.isoformat(),
            'energy_level': request.energy_level,
            'mood_rating': request.mood_rating,
            'sleep_quality': request.sleep_quality,
            'stress_level': request.stress_level,
            'nutrition_satisfaction': request.nutrition_satisfaction,
            'hydration_glasses': request.hydration_glasses,
            'meal_timing_satisfaction': request.meal_timing_satisfaction,
            'breathing_exercises_completed': request.breathing_exercises_completed,
            'sunlight_exposure_completed': request.sunlight_exposure_completed,
            'mindfulness_practice_completed': request.mindfulness_practice_completed,
            'what_went_well': request.what_went_well,
            'what_was_challenging': request.what_was_challenging,
            'tomorrow_intentions': request.tomorrow_intentions,
            'gratitude_notes': request.gratitude_notes,
            'voice_note_url': request.voice_note_url,
            'voice_note_duration_seconds': request.voice_note_duration_seconds,
            'time_to_complete_seconds': request.time_to_complete_seconds,
            'completed_at': datetime.now().isoformat()
        }
        
        # Use upsert to handle updates to existing journal entries
        result = supabase.table("daily_journals")\
            .upsert(journal_data, on_conflict="profile_id,journal_date")\
            .execute()
        
        if result.data:
            logger.info(f"Daily journal recorded for profile {request.profile_id}, date {request.journal_date}")
            return DailyJournalResponse(
                success=True,
                message="Daily journal recorded successfully",
                journal_id=result.data[0]["id"]
            )
        else:
            raise HolisticOSException("Failed to record daily journal")
            
    except Exception as e:
        logger.error(f"Error recording daily journal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record daily journal: {str(e)}")

@router.get("/journal/{profile_id}")
async def get_daily_journal(
    profile_id: str,
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get daily journal entry for a specific date
    """
    try:
        target_date = date.fromisoformat(date_param) if date_param else date.today()
        
        result = supabase.table("daily_journals")\
            .select("*")\
            .eq("profile_id", profile_id)\
            .eq("journal_date", target_date.isoformat())\
            .single()\
            .execute()
        
        if result.data:
            return result.data
        else:
            return {"message": "No journal entry found for this date"}
            
    except Exception as e:
        logger.error(f"Error fetching daily journal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily journal: {str(e)}")

@router.get("/journal/{profile_id}/history")
async def get_journal_history(
    profile_id: str,
    days: int = Query(30, description="Number of days of history to fetch"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get journal history for analytics and trend analysis
    """
    try:
        result = supabase.table("daily_journals")\
            .select("*")\
            .eq("profile_id", profile_id)\
            .order("journal_date", desc=True)\
            .limit(days)\
            .execute()
        
        return {
            "profile_id": profile_id,
            "days_requested": days,
            "entries_found": len(result.data or []),
            "journals": result.data or []
        }
        
    except Exception as e:
        logger.error(f"Error fetching journal history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch journal history: {str(e)}")

# =====================================================
# Plan Management Endpoints  
# =====================================================

@router.post("/extract-plan-items")
async def extract_plan_items(
    request: PlanExtractionRequest,
    plan_service: PlanExtractionService = Depends(get_plan_service)
):
    """
    Extract trackable tasks from an analysis result and store as plan items
    
    This endpoint should be called after a new plan is generated to make its tasks
    available for check-in tracking.
    """
    try:
        extracted_items = await plan_service.extract_and_store_plan_items(
            request.analysis_result_id,
            request.profile_id
        )
        
        return {
            "success": True,
            "message": f"Extracted {len(extracted_items)} plan items",
            "analysis_result_id": request.analysis_result_id,
            "items_extracted": len(extracted_items),
            "items": extracted_items
        }
        
    except Exception as e:
        logger.error(f"Error extracting plan items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract plan items: {str(e)}")

@router.get("/plans/{profile_id}/current", response_model=CurrentPlanResponse)
async def get_current_plans(
    profile_id: str,
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format"),
    plan_service: PlanExtractionService = Depends(get_plan_service)
):
    """
    Get user's current active plans with trackable items
    """
    try:
        target_date = date_param or date.today().isoformat()
        plan_data = await plan_service.get_current_plan_items_for_user(profile_id, target_date)
        
        return CurrentPlanResponse(
            routine_plan=plan_data["routine_plan"],
            nutrition_plan=plan_data["nutrition_plan"],
            items=[PlanItemResponse(**item) for item in plan_data["items"]],
            date=plan_data["date"]
        )
        
    except Exception as e:
        logger.error(f"Error fetching current plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch current plans: {str(e)}")

# =====================================================
# Analytics Endpoints (Basic)
# =====================================================

@router.get("/analytics/{profile_id}/completion-summary")
async def get_completion_summary(
    profile_id: str,
    days: int = Query(7, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase)
):
    """
    Get task completion summary for analytics
    """
    try:
        from datetime import timedelta
        
        start_date = date.today() - timedelta(days=days)
        
        # Get task completion data
        result = supabase.table("task_checkins")\
            .select("completion_status, satisfaction_rating, planned_date")\
            .eq("profile_id", profile_id)\
            .gte("planned_date", start_date.isoformat())\
            .execute()
        
        data = result.data or []
        
        if not data:
            return {"message": "No completion data found", "summary": {}}
        
        # Calculate summary statistics
        total_tasks = len(data)
        completed = len([d for d in data if d["completion_status"] == "completed"])
        partial = len([d for d in data if d["completion_status"] == "partial"])
        skipped = len([d for d in data if d["completion_status"] == "skipped"])
        
        # Calculate average satisfaction for completed tasks
        satisfaction_ratings = [d["satisfaction_rating"] for d in data if d["satisfaction_rating"] is not None]
        avg_satisfaction = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else None
        
        return {
            "profile_id": profile_id,
            "days_analyzed": days,
            "summary": {
                "total_tasks": total_tasks,
                "completed": completed,
                "partial": partial,
                "skipped": skipped,
                "completion_rate": completed / total_tasks if total_tasks > 0 else 0,
                "average_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating completion summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate completion summary: {str(e)}")

# Health check endpoint
@router.get("/health")
async def engagement_health_check():
    """Health check for engagement endpoints"""
    return {"status": "healthy", "service": "user-engagement", "timestamp": datetime.now().isoformat()}