"""
Admin APIs for Dashboard
Dedicated endpoints for bio-coach-hub admin dashboard
Separated from main API for better organization
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Setup logging
logger = logging.getLogger(__name__)

# Create router for admin endpoints
router = APIRouter(prefix="/api/admin", tags=["admin"])

# =====================================================================
# Response Models
# =====================================================================

class UserSummary(BaseModel):
    id: str
    name: Optional[str]
    age: Optional[int]
    total_analyses: int
    last_analysis_date: Optional[str]
    latest_archetype: Optional[str]
    has_health_data: bool
    overall_score: Optional[float]
    profile_created: Optional[str]

class UserListResponse(BaseModel):
    users: List[UserSummary]
    total_count: int
    has_more: bool

class AnalysisSummary(BaseModel):
    total_analyses: int
    behavior_analyses: int
    nutrition_analyses: int
    routine_analyses: int
    complete_analyses: int
    last_analysis_date: Optional[str]
    latest_archetype: Optional[str]

class UserProfileResponse(BaseModel):
    id: str
    name: Optional[str]
    age: Optional[int]
    profile_created: Optional[str]
    analysis_summary: AnalysisSummary
    current_health_scores: Dict[str, Optional[float]]
    data_availability: Dict[str, Any]

class AnalysisData(BaseModel):
    analysis_id: str
    analysis_date: str
    analysis_type: str
    archetype: Optional[str]
    created_at: str
    analysis_trigger: Optional[str]
    confidence_score: Optional[float]
    completeness_score: Optional[float]
    behavior_analysis: Optional[Dict[str, Any]]
    routine_plan: Optional[Dict[str, Any]]
    nutrition_plan: Optional[Dict[str, Any]]
    input_summary: Optional[Dict[str, Any]]
    raw_analysis_result: Optional[Dict[str, Any]]

class AnalysisDataResponse(BaseModel):
    user_id: str
    date: str
    total_analyses: int
    analyses: List[AnalysisData]

# =====================================================================
# Admin API Endpoints
# =====================================================================

@router.get("/users", response_model=UserListResponse)
async def get_admin_users_list(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """
    Get list of all users with their summary information
    Used by dashboard homepage (Index.tsx)
    
    Args:
        limit: Number of results to return (max 200)
        offset: Number of results to skip for pagination
        status: Optional filter by user status
    
    Returns:
        UserListResponse with users array and pagination info
    """
    try:
        from supabase import create_client
        import os
        
        # Use Supabase client directly for better reliability
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # Get profiles using Supabase client
        # Get profiles using Supabase client
        profiles_response = (
            supabase.table("profiles")
            .select("id, data, created_at")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        profiles_data = profiles_response.data if profiles_response.data else []
        
        # Get analysis data for each user
        users = []
        for profile_row in profiles_data:
            user_id = profile_row['id']
            
            # Get analysis count for this user
            count_response = (
                supabase.table("holistic_analysis_results")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            total_analyses = count_response.count or 0
            
            # Get latest analysis info
            latest_response = (
                supabase.table("holistic_analysis_results")
                .select("archetype, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            latest_analysis = latest_response.data[0] if latest_response.data else {}
            
            # Extract user info from profile data
            profile_data = profile_row.get('data', {})
            if isinstance(profile_data, dict):
                name = (
                    profile_data.get('name') or 
                    (profile_data.get('profileInfo', {}).get('externalId') if isinstance(profile_data.get('profileInfo'), dict) else None) or
                    f"User {user_id[:8]}"
                )
                age = profile_data.get('age')
                if isinstance(age, str) and age.isdigit():
                    age = int(age)
                elif not isinstance(age, int):
                    age = None
            else:
                name = f"User {user_id[:8]}"
                age = None
            
            users.append(UserSummary(
                id=user_id,
                name=name,
                age=age,
                total_analyses=total_analyses,
                last_analysis_date=latest_analysis.get('created_at'),
                latest_archetype=latest_analysis.get('archetype'),
                has_health_data=total_analyses > 0,
                overall_score=None,
                profile_created=profile_row.get('created_at')
            ))
        
        # Get total count for pagination
        total_count_response = (
            supabase.table("profiles")
            .select("id", count="exact")
            .execute()
        )
        total_count = total_count_response.count or 0
        
        return UserListResponse(
            users=users,
            total_count=total_count,
            has_more=(offset + limit) < total_count
        )
        
    except Exception as e:
        logger.error(f"[ADMIN_API] Failed to get users list: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.get("/user/{user_id}/overview", response_model=UserProfileResponse)
async def get_admin_user_overview(user_id: str):
    """
    Get comprehensive user profile overview
    Used by UserProfile page header
    
    Args:
        user_id: The user's unique identifier
    
    Returns:
        UserProfileResponse with complete user profile data
    """
    try:
        from supabase import create_client
        import os
        
        # Use Supabase client directly
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # Get user profile using Supabase client
        profile_response = (
            supabase.table("profiles")
            .select("id, data, created_at, updated_at, last_analysis_at")
            .eq("id", user_id)
            .execute()
        )
        
        if not profile_response.data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        profile = profile_response.data[0]
        
        # Extract user info from profile data
        profile_data = profile.get('data', {})
        if isinstance(profile_data, dict):
            name = (
                profile_data.get('name') or 
                (profile_data.get('profileInfo', {}).get('externalId') if isinstance(profile_data.get('profileInfo'), dict) else None) or
                f"User {user_id[:8]}"
            )
            age = profile_data.get('age')
            if isinstance(age, str) and age.isdigit():
                age = int(age)
            elif not isinstance(age, int):
                age = None
        else:
            name = f"User {user_id[:8]}"
            age = None
        
        # Get analysis summary using Supabase client
        all_analyses_response = (
            supabase.table("holistic_analysis_results")
            .select("analysis_type, created_at, archetype")
            .eq("user_id", user_id)
            .execute()
        )
        
        analyses_data = all_analyses_response.data if all_analyses_response.data else []
        
        # Calculate summary statistics
        total_analyses = len(analyses_data)
        behavior_analyses = len([a for a in analyses_data if a.get('analysis_type') == 'behavior_analysis'])
        nutrition_analyses = len([a for a in analyses_data if a.get('analysis_type') == 'nutrition_plan'])
        routine_analyses = len([a for a in analyses_data if a.get('analysis_type') == 'routine_plan'])
        complete_analyses = len([a for a in analyses_data if a.get('analysis_type') == 'complete_analysis'])
        
        # Get latest analysis info
        latest_analysis = max(analyses_data, key=lambda x: x.get('created_at', ''), default={}) if analyses_data else {}
        
        analysis_summary = {
            'total_analyses': total_analyses,
            'behavior_analyses': behavior_analyses,
            'nutrition_analyses': nutrition_analyses,
            'routine_analyses': routine_analyses,
            'complete_analyses': complete_analyses,
            'last_analysis_date': latest_analysis.get('created_at'),
            'latest_archetype': latest_analysis.get('archetype')
        }
        
        return UserProfileResponse(
            id=profile['id'],
            name=name,
            age=age,
            profile_created=profile.get('created_at'),
            analysis_summary=AnalysisSummary(
                total_analyses=analysis_summary.get('total_analyses', 0),
                behavior_analyses=analysis_summary.get('behavior_analyses', 0),
                nutrition_analyses=analysis_summary.get('nutrition_analyses', 0),
                routine_analyses=analysis_summary.get('routine_analyses', 0),
                complete_analyses=analysis_summary.get('complete_analyses', 0),
                last_analysis_date=analysis_summary.get('last_analysis_date'),
                latest_archetype=analysis_summary.get('latest_archetype')
            ),
            current_health_scores={
                "overall": None,  # TODO: Calculate from scores table
                "readiness": None,
                "sleep": None,
                "activity": None,
                "mental_wellbeing": None
            },
            data_availability={
                "has_analysis_data": analysis_summary.get('total_analyses', 0) > 0,
                "has_health_scores": False,  # TODO: Check scores table
                "has_biomarkers": False,  # TODO: Check biomarkers table
                "last_data_update": analysis_summary.get('last_analysis_date')
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN_API] Failed to get user overview for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user overview: {str(e)}")


@router.get("/user/{user_id}/analysis-data", response_model=AnalysisDataResponse)
async def get_admin_user_analysis_data(
    user_id: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    limit: int = Query(10, ge=1, le=50),
    analysis_type: Optional[str] = None
):
    """
    Get user's analysis data for a specific date
    Used by Behavior Analysis, Routine Plan, and Nutrition Plan tabs
    
    Args:
        user_id: The user's unique identifier
        date: Date to retrieve data for (YYYY-MM-DD)
        limit: Maximum number of analyses to return
        analysis_type: Optional filter by analysis type
    
    Returns:
        AnalysisDataResponse with analyses for the specified date
    """
    try:
        from supabase import create_client
        import os
        
        # Use Supabase client directly
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # Parse and validate date
        try:
            target_date = datetime.fromisoformat(date).date()
        except:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get analysis data using Supabase client
        query_builder = (
            supabase.table("holistic_analysis_results")
            .select("id, analysis_date, analysis_type, archetype, analysis_result, input_summary, confidence_score, completeness_score, created_at, analysis_trigger")
            .eq("user_id", user_id)
        )
        
        # Filter by date - use local time without timezone to avoid UTC issues
        start_datetime = f"{target_date}T00:00:00"
        end_datetime = f"{target_date}T23:59:59.999999"
        
        query_builder = query_builder.gte("analysis_date", start_datetime)
        query_builder = query_builder.lt("analysis_date", f"{target_date + timedelta(days=1)}T00:00:00")
        
        # Add optional analysis type filter
        if analysis_type:
            query_builder = query_builder.eq("analysis_type", analysis_type)
            
        # Execute query
        results_response = (
            query_builder
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        results = results_response.data if results_response.data else []
        
        # Transform results
        analyses = []
        for row in results:
            # Extract and parse JSON fields
            analysis_result = row.get('analysis_result')
            input_summary = row.get('input_summary')
            
            # Parse input_summary if it's a string
            parsed_input_summary = None
            if input_summary:
                if isinstance(input_summary, str):
                    try:
                        import json
                        parsed_input_summary = json.loads(input_summary)
                    except (json.JSONDecodeError, TypeError):
                        parsed_input_summary = {"raw_data": input_summary, "parse_error": "Failed to parse input_summary"}
                else:
                    parsed_input_summary = input_summary
            
            # Handle analysis_result
            if isinstance(analysis_result, str):
                # Already a string, use as-is
                analysis_result_string = analysis_result
                # Also parse for raw_analysis_result
                try:
                    import json
                    parsed_raw_result = json.loads(analysis_result)
                except (json.JSONDecodeError, TypeError):
                    parsed_raw_result = {"raw_data": analysis_result, "parse_error": "Failed to parse raw_analysis_result"}
            else:
                # It's JSONB, convert to string and parse
                analysis_result_string = str(analysis_result) if analysis_result else "{}"
                parsed_raw_result = analysis_result if analysis_result else {}
            
            # Parse components from analysis_result
            # Note: analysis_result is a JSONB string that needs double-parsing
            behavior_analysis = None
            routine_plan = None
            nutrition_plan = None
            
            # The database stores analysis_result as JSONB containing a JSON string
            # We need to extract the string value and parse it as JSON
            try:
                if analysis_result and isinstance(analysis_result, str):
                    # Parse the JSON string to get the actual data
                    import json
                    parsed_data = json.loads(analysis_result)
                    
                    analysis_type = row['analysis_type']
                    
                    if analysis_type == 'behavior_analysis':
                        # For behavior_analysis, the entire parsed data is behavior data
                        behavior_analysis = parsed_data
                    elif analysis_type == 'routine_plan':
                        # For routine_plan, the entire parsed data is routine data
                        routine_plan = parsed_data
                    elif analysis_type == 'nutrition_plan':
                        # For nutrition_plan, the entire parsed data is nutrition data
                        nutrition_plan = parsed_data
                    elif analysis_type == 'complete_analysis':
                        # For complete_analysis, check for nested components
                        behavior_analysis = parsed_data.get('behavior_analysis')
                        routine_plan = parsed_data.get('routine_plan')
                        nutrition_plan = parsed_data.get('nutrition_plan')
                        
                        # If no nested components, determine type by content
                        if not any([behavior_analysis, routine_plan, nutrition_plan]):
                            if 'behavioral_signature' in parsed_data or 'primary_goal' in parsed_data:
                                behavior_analysis = parsed_data
                            elif 'content' in parsed_data or 'daily_activities' in parsed_data:
                                routine_plan = parsed_data
                            elif 'daily_meals' in parsed_data or 'nutritional_goals' in parsed_data:
                                nutrition_plan = parsed_data
                                
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse analysis_result for {row['analysis_id']}: {e}")
                # Keep as raw data for debugging
                if row['analysis_type'] == 'behavior_analysis':
                    behavior_analysis = {'raw_data': analysis_result, 'parse_error': str(e)}
                elif row['analysis_type'] == 'routine_plan':
                    routine_plan = {'raw_data': analysis_result, 'parse_error': str(e)}
                elif row['analysis_type'] == 'nutrition_plan':
                    nutrition_plan = {'raw_data': analysis_result, 'parse_error': str(e)}
            
            analyses.append(AnalysisData(
                analysis_id=str(row['id']),
                analysis_date=row['analysis_date'],
                analysis_type=row['analysis_type'],
                archetype=row['archetype'],
                created_at=row['created_at'],
                analysis_trigger=row.get('analysis_trigger'),
                confidence_score=row.get('confidence_score'),
                completeness_score=row.get('completeness_score'),
                behavior_analysis=behavior_analysis,
                routine_plan=routine_plan,
                nutrition_plan=nutrition_plan,
                input_summary=parsed_input_summary,
                raw_analysis_result=parsed_raw_result  # Include parsed data
            ))
        
        # No cleanup needed for Supabase client
        
        return AnalysisDataResponse(
            user_id=user_id,
            date=date,
            total_analyses=len(analyses),
            analyses=analyses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN_API] Failed to get analysis data for {user_id} on {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis data: {str(e)}")


# =====================================================================
# Helper function to register admin routes with main app
# =====================================================================

def register_admin_routes(app):
    """
    Register admin routes with the main FastAPI app
    Call this from openai_main.py to include admin endpoints
    
    Usage in openai_main.py:
        from services.api_gateway.admin_apis import register_admin_routes
        register_admin_routes(app)
    """
    app.include_router(router)
    logger.info("[ADMIN_API] Admin routes registered successfully")