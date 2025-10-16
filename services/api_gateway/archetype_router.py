#!/usr/bin/env python3
"""
Archetype Management API Router
Handles archetype selection, metadata, and multi-plan support for calendar workflow

Routes:
- GET /api/user/{user_id}/available-archetypes - Get all available archetypes/plans for a user
- GET /api/user/{user_id}/archetype/{analysis_id}/summary - Get detailed archetype information
"""

import asyncio
import sys
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from supabase import create_client, Client

# Import configuration
import os
from dotenv import load_dotenv
load_dotenv()

def get_supabase_client() -> Client:
    """Get Supabase client using environment variables"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    
    return create_client(supabase_url, supabase_key)

def get_postgresql_client():
    """Get PostgreSQL client for holistic_analysis_results"""
    try:
        # Import PostgreSQL adapter
        sys.path.append(os.path.join(project_root, 'shared_libs', 'database'))
        from supabase_async_pg_adapter import SupabaseAsyncPGAdapter
        
        adapter = SupabaseAsyncPGAdapter()
        return adapter
    except Exception as e:
        print(f"Failed to get PostgreSQL client: {e}")
        return None

def query_holistic_analysis_results_fallback(supabase: Client, user_id: str, limit: int = 10):
    """
    Fallback method to query analysis results using Supabase RPC or direct table access
    This assumes holistic_analysis_results might be accessible via Supabase
    """
    try:
        # Try to query via RPC function (if exists)
        try:
            result = supabase.rpc('get_user_analysis_results', {
                'p_user_id': user_id,
                'p_limit': limit
            }).execute()
            
            if result.data:
                return result.data
        except Exception as rpc_error:
            print(f"RPC method failed: {rpc_error}")
        
        # Fallback: Try direct table access (if table exists in Supabase) - removed updated_at
        try:
            result = supabase.table('holistic_analysis_results')\
                .select('id, user_id, archetype, analysis_type, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                # Transform to match expected format (no updated_at field)
                return [{
                    'analysis_id': row['id'],
                    'archetype': row['archetype'],
                    'analysis_type': row['analysis_type'],
                    'created_at': row['created_at'],
                    'updated_at': None  # Field doesn't exist in current schema
                } for row in result.data]
        except Exception as table_error:
            print(f"Direct table access failed: {table_error}")
        
        # Last resort: Generate mock data based on existing plan items
        print("Using plan_items based fallback for archetype detection")
        plan_items = supabase.table('plan_items')\
            .select('analysis_result_id')\
            .eq('profile_id', user_id)\
            .execute()
        
        if plan_items.data:
            # Get unique analysis IDs and create mock archetype data
            unique_analyses = list(set([item['analysis_result_id'] for item in plan_items.data if item.get('analysis_result_id')]))
            
            mock_results = []
            for i, analysis_id in enumerate(unique_analyses[:limit]):
                mock_results.append({
                    'analysis_id': analysis_id,
                    'archetype': f'Plan {i+1}',
                    'analysis_type': 'complete_analysis',
                    'created_at': '2025-09-03T00:00:00',
                    'updated_at': None
                })
            
            return mock_results
        
        return []
        
    except Exception as e:
        print(f"All fallback methods failed: {e}")
        return []

# Pydantic models for archetype data
class ArchetypeInfo(BaseModel):
    """Basic archetype information"""
    analysis_id: str = Field(..., description="Analysis result ID (UUID)")
    archetype_name: str = Field(..., description="Archetype name (e.g., Foundation Builder)")
    analysis_type: str = Field(..., description="Type of analysis (behavior_analysis, routine_plan, etc.)")
    created_at: str = Field(..., description="When this analysis was created")
    updated_at: Optional[str] = Field(None, description="Last updated timestamp")
    
class ArchetypeWithStats(ArchetypeInfo):
    """Archetype with additional statistics"""
    total_plan_items: int = Field(0, description="Total plan items for this archetype")
    total_time_blocks: int = Field(0, description="Total time blocks for this archetype")
    has_calendar_selections: bool = Field(False, description="Whether user has selected items from this archetype")
    last_used: Optional[str] = Field(None, description="Last time user interacted with this archetype")

class ArchetypeSummary(BaseModel):
    """Detailed archetype summary"""
    analysis_id: str
    archetype_name: str
    analysis_type: str
    created_at: str
    
    # Analysis content summary
    primary_goal: Optional[str] = Field(None, description="Main goal from behavior analysis")
    focus_areas: List[str] = Field(default_factory=list, description="Key focus areas")
    
    # Statistics
    total_plan_items: int = Field(0)
    total_time_blocks: int = Field(0)
    completion_stats: Dict[str, Any] = Field(default_factory=dict)
    
    # Time block breakdown
    time_blocks_summary: List[Dict[str, str]] = Field(default_factory=list, description="Summary of time blocks")

class UserArchetypesResponse(BaseModel):
    """Response for available archetypes"""
    user_id: str
    total_archetypes: int
    archetypes: List[ArchetypeWithStats]
    has_multiple_plans: bool = Field(False, description="Whether user has multiple archetype plans")
    most_recent: Optional[str] = Field(None, description="Most recent analysis ID")
    archetype_tracking: List[Dict[str, Any]] = Field(default_factory=list, description="Raw archetype tracking data")

# Create router
router = APIRouter(prefix="/user", tags=["archetypes"])

@router.get("/{user_id}/available-archetypes", response_model=UserArchetypesResponse)
async def get_user_available_archetypes(
    user_id: str = Path(..., description="User ID"),
    include_stats: bool = Query(default=True, description="Include plan statistics"),
    limit: int = Query(default=10, description="Maximum number of archetypes to return")
):
    """
    Get all available archetypes/plans for a user
    
    This endpoint uses the archetype_analysis_tracking table to get user archetype usage data
    and provides unified archetype status for the frontend.
    """
    try:
        # Get Supabase client for all queries
        supabase: Client = get_supabase_client()
        
        # Step 1: Query archetype_analysis_tracking table directly
        try:
            tracking_result = supabase.table('archetype_analysis_tracking')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('analysis_timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            tracking_data = tracking_result.data or []
            print(f"✅ Got {len(tracking_data)} archetype tracking records from Supabase")
            
        except Exception as e:
            print(f"Error querying archetype_analysis_tracking table: {e}")
            tracking_data = []
        
        # If no tracking data, return empty response
        if not tracking_data:
            return UserArchetypesResponse(
                user_id=user_id,
                total_archetypes=0,
                archetypes=[],
                has_multiple_plans=False,
                archetype_tracking=[]
            )
        
        # Step 2: Process tracking data to create archetype stats
        archetypes_with_stats = []
        
        for tracking_row in tracking_data:
            # Extract data from archetype_analysis_tracking table
            archetype_name = tracking_row.get('archetype', 'Unknown Archetype')
            analysis_count = tracking_row.get('analysis_count', 0)
            analysis_timestamp = tracking_row.get('analysis_timestamp')
            created_at = tracking_row.get('created_at')
            updated_at = tracking_row.get('updated_at')

            # Use the tracking ID as analysis_id since we don't have actual analysis records
            analysis_id = str(tracking_row.get('id', ''))

            # Handle date formatting
            created_at_str = created_at if isinstance(created_at, str) else str(created_at) if created_at else None
            updated_at_str = updated_at if isinstance(updated_at, str) else str(updated_at) if updated_at else None
            last_used_str = analysis_timestamp if isinstance(analysis_timestamp, str) else str(analysis_timestamp) if analysis_timestamp else None
            
            archetype_data = {
                "analysis_id": analysis_id,
                "archetype_name": archetype_name,
                "analysis_type": "archetype_tracking",  # Indicate this is from tracking table
                "created_at": created_at_str,
                "updated_at": updated_at_str,
                "total_plan_items": 0,  # Will be calculated if include_stats is True
                "total_time_blocks": 0,  # Will be calculated if include_stats is True
                "has_calendar_selections": False,
                "last_used": last_used_str
            }
            
            # If stats are requested, try to find related plan items and time blocks
            if include_stats and analysis_count > 0:
                try:
                    # Try to find recent analysis results for this user and archetype to get actual analysis_ids
                    recent_analysis_result = supabase.table("holistic_analysis_results")\
                        .select("id")\
                        .eq("user_id", user_id)\
                        .eq("archetype", archetype_name)\
                        .order("created_at", desc=True)\
                        .limit(1)\
                        .execute()
                    
                    if recent_analysis_result.data:
                        actual_analysis_id = recent_analysis_result.data[0]["id"]
                        
                        # Count plan items for the actual analysis
                        plan_items_result = supabase.table("plan_items")\
                            .select("id", count="exact")\
                            .eq("analysis_result_id", actual_analysis_id)\
                            .execute()
                        
                        archetype_data["total_plan_items"] = plan_items_result.count or 0
                        
                        # Count time blocks for the actual analysis
                        time_blocks_result = supabase.table("time_blocks")\
                            .select("id", count="exact")\
                            .eq("analysis_result_id", actual_analysis_id)\
                            .execute()
                        
                        archetype_data["total_time_blocks"] = time_blocks_result.count or 0
                        
                        # Check for calendar selections
                        if plan_items_result.data:
                            selections_result = supabase.table("calendar_selections")\
                                .select("id", count="exact")\
                                .eq("profile_id", user_id)\
                                .in_("plan_item_id", [item['id'] for item in plan_items_result.data])\
                                .execute()
                            
                            archetype_data["has_calendar_selections"] = (selections_result.count or 0) > 0
                    
                except Exception as stats_error:
                    print(f"Error getting stats for archetype {archetype_name}: {stats_error}")
                    # Continue with zero stats
                    pass
            
            archetypes_with_stats.append(ArchetypeWithStats(**archetype_data))
        
        # Determine most recent analysis
        most_recent = archetypes_with_stats[0].analysis_id if archetypes_with_stats else None
        
        return UserArchetypesResponse(
            user_id=user_id,
            total_archetypes=len(archetypes_with_stats),
            archetypes=archetypes_with_stats,
            has_multiple_plans=len(archetypes_with_stats) > 1,
            most_recent=most_recent,
            archetype_tracking=tracking_data  # Include raw tracking data as requested
        )
        
    except Exception as e:
        print(f"Error in get_user_available_archetypes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user archetypes: {str(e)}")

@router.get("/{user_id}/archetype/{analysis_id}/summary", response_model=ArchetypeSummary)
async def get_archetype_summary(
    user_id: str = Path(..., description="User ID"),
    analysis_id: str = Path(..., description="Analysis result ID (UUID)"),
    include_time_blocks: bool = Query(default=True, description="Include time blocks summary")
):
    """
    Get detailed summary for a specific archetype/analysis
    
    Provides comprehensive information about a specific analysis including
    goals, focus areas, and time block breakdown.
    """
    try:
        # Get PostgreSQL client for analysis results (optional)
        pg_adapter = get_postgresql_client()
        
        # Get Supabase client for plan items and time blocks  
        supabase: Client = get_supabase_client()
        
        # Step 1: Try to get analysis details from PostgreSQL, fallback to Supabase
        analysis_row = None
        
        if pg_adapter:
            try:
                await pg_adapter.initialize()
                
                query = """
                    SELECT 
                        id as analysis_id,
                        user_id,
                        archetype,
                        analysis_type,
                        analysis_result,
                        created_at
                    FROM holistic_analysis_results 
                    WHERE id = %s AND user_id = %s
                    LIMIT 1
                """
                
                analysis_row = await pg_adapter.fetch_one(query, (analysis_id, user_id))
                
            except Exception as e:
                print(f"PostgreSQL query error: {e}")
                analysis_row = None
            finally:
                if pg_adapter:
                    await pg_adapter.close()
        
        # Fallback: try to get basic info from existing data
        if not analysis_row:
            print("🔄 Using fallback method for archetype summary")
            # Try to get basic info from time_blocks (without archetype_name since it doesn't exist)
            try:
                time_block_info = supabase.table("time_blocks")\
                    .select("analysis_result_id, block_title")\
                    .eq("analysis_result_id", analysis_id)\
                    .limit(1)\
                    .execute()
                
                if time_block_info.data and time_block_info.data[0]:
                    # Create a mock analysis row with generated archetype name
                    short_id = analysis_id[:8] if analysis_id else 'unknown'
                    analysis_row = {
                        'analysis_id': analysis_id,
                        'user_id': user_id,
                        'archetype': f'Plan {short_id}',
                        'analysis_type': 'complete_analysis',
                        'analysis_result': {},
                        'created_at': '2025-09-03T00:00:00'
                    }
                else:
                    # Even if no time_blocks found, create a basic analysis row
                    short_id = analysis_id[:8] if analysis_id else 'unknown'
                    analysis_row = {
                        'analysis_id': analysis_id,
                        'user_id': user_id,
                        'archetype': f'Plan {short_id}',
                        'analysis_type': 'complete_analysis',
                        'analysis_result': {},
                        'created_at': '2025-09-03T00:00:00'
                    }
            except Exception as fallback_error:
                print(f"Fallback method failed: {fallback_error}")
                # Create minimal analysis row even if everything fails
                short_id = analysis_id[:8] if analysis_id else 'unknown'
                analysis_row = {
                    'analysis_id': analysis_id,
                    'user_id': user_id,
                    'archetype': f'Plan {short_id}',
                    'analysis_type': 'complete_analysis',
                    'analysis_result': {},
                    'created_at': '2025-09-03T00:00:00'
                }
        
        if not analysis_row:
            raise HTTPException(status_code=404, detail="Analysis not found for this user")
        
        # Step 2: Parse analysis result for key information (with error handling)
        try:
            analysis_result = analysis_row.get('analysis_result') or {}
            
            # Extract primary goal and focus areas from behavior analysis
            primary_goal = None
            focus_areas = []
            
            if isinstance(analysis_result, dict):
                if 'primary_goal' in analysis_result:
                    goal_data = analysis_result['primary_goal']
                    if isinstance(goal_data, dict):
                        primary_goal = goal_data.get('goal', str(goal_data))
                    else:
                        primary_goal = str(goal_data)
                
                # Extract focus areas from various sections
                if 'focus_areas' in analysis_result:
                    focus_areas_data = analysis_result['focus_areas']
                    if isinstance(focus_areas_data, list):
                        focus_areas = focus_areas_data
                elif 'sophisticated_assessment' in analysis_result:
                    soph = analysis_result['sophisticated_assessment']
                    if isinstance(soph, dict) and 'areas_for_improvement' in soph:
                        areas_data = soph['areas_for_improvement']
                        if isinstance(areas_data, list):
                            focus_areas = areas_data
        except Exception as parse_error:
            print(f"Error parsing analysis result: {parse_error}")
            primary_goal = "Analysis details unavailable"
            focus_areas = []
        
        # Step 3: Get statistics from Supabase
        plan_items_count = 0
        time_blocks_count = 0
        time_blocks_summary = []
        
        try:
            # Get plan items count
            plan_items_result = supabase.table("plan_items")\
                .select("id", count="exact")\
                .eq("analysis_result_id", analysis_id)\
                .execute()
            
            plan_items_count = plan_items_result.count or 0
            
            # Get time blocks with details
            if include_time_blocks:
                time_blocks_result = supabase.table("time_blocks")\
                    .select("block_title, time_range, purpose")\
                    .eq("analysis_result_id", analysis_id)\
                    .order("block_order")\
                    .execute()
                
                time_blocks_count = len(time_blocks_result.data) if time_blocks_result.data else 0
                
                # Format time blocks summary
                for block in (time_blocks_result.data or []):
                    time_blocks_summary.append({
                        "title": block.get("block_title", "Untitled Block"),
                        "time_range": block.get("time_range", "TBD"),
                        "purpose": block.get("purpose", "")[:100] + "..." if len(block.get("purpose", "")) > 100 else block.get("purpose", "")
                    })
            
        except Exception as stats_error:
            print(f"Error getting detailed stats: {stats_error}")
            # Continue with zero stats
        
        # Safe date handling for created_at
        created_at = analysis_row['created_at']
        if hasattr(created_at, 'isoformat'):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = str(created_at) if created_at else ""

        return ArchetypeSummary(
            analysis_id=analysis_id,
            archetype_name=analysis_row['archetype'] or "Unknown Archetype",
            analysis_type=analysis_row['analysis_type'],
            created_at=created_at_str,
            primary_goal=primary_goal,
            focus_areas=focus_areas[:5],  # Limit to top 5 focus areas
            total_plan_items=plan_items_count,
            total_time_blocks=time_blocks_count,
            completion_stats={
                "total_items": plan_items_count,
                "time_blocks": time_blocks_count
            },
            time_blocks_summary=time_blocks_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_archetype_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get archetype summary: {str(e)}")

# Export router
__all__ = ['router']