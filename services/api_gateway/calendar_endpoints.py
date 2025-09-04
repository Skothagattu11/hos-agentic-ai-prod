#!/usr/bin/env python3
"""
Simple Calendar Endpoints - Minimal Working Version
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from pydantic import BaseModel, Field
import os
from datetime import datetime
import uuid

# Simple router setup
router = APIRouter(prefix="/api/calendar", tags=["calendar"])

class CalendarSelectionRequest(BaseModel):
    """Request model for selecting plan items for calendar"""
    profile_id: str = Field(..., description="User profile ID")
    selected_plan_items: List[str] = Field(..., description="List of plan item IDs to add to calendar")
    date: Optional[str] = Field(default=None, description="Date for selections (YYYY-MM-DD, defaults to today)")
    selection_notes: Optional[str] = Field(default=None, description="Optional notes about the selection")

@router.get("/time-blocks/{profile_id}")
async def get_time_blocks_for_archetype(
    profile_id: str = Path(..., description="User profile ID"),
    archetype_filter: Optional[str] = Query(default=None, description="Filter by specific archetype/analysis_id"),
    date: Optional[str] = Query(default=None, description="Date filter (YYYY-MM-DD)")
):
    """Get time blocks with calendar items - SIMPLIFIED SINGLE QUERY"""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
        
        supabase = create_client(supabase_url, supabase_key)
        filter_date = date or datetime.now().strftime('%Y-%m-%d')
        
        # STEP 1: Get time blocks for the archetype
        time_blocks_query = supabase.table("time_blocks").select(
            "id, analysis_result_id, block_title, time_range, block_order, purpose"
        ).eq("profile_id", profile_id)
        
        if archetype_filter:
            time_blocks_query = time_blocks_query.eq("analysis_result_id", archetype_filter)
        
        time_blocks_result = time_blocks_query.order("block_order").execute()
        time_blocks = time_blocks_result.data or []
        
        # STEP 2: Get all calendar items - SAFE APPROACH
        calendar_items = []
        if time_blocks:
            time_block_ids = [tb['id'] for tb in time_blocks]
            
            # Get calendar selections first (SAFE - no joins)
            calendar_query = supabase.table("calendar_selections")\
                .select("id, plan_item_id, selection_timestamp, calendar_notes")\
                .eq("profile_id", profile_id)\
                .eq("selected_for_calendar", True)
            
            calendar_result = calendar_query.execute()
            
            # If we have calendar selections, get the plan items
            if calendar_result.data:
                plan_item_ids = [sel['plan_item_id'] for sel in calendar_result.data]
                
                # Get plan items for calendar selections
                # Include items that belong to current time blocks OR have NULL time_block_id
                plan_items_query = supabase.table("plan_items")\
                    .select("""
                        id,
                        title,
                        description,
                        time_block_id,
                        scheduled_time,
                        scheduled_end_time,
                        estimated_duration_minutes,
                        task_type,
                        priority_level,
                        analysis_result_id
                    """)\
                    .in_("id", plan_item_ids)
                
                plan_items_result = plan_items_query.execute()
                plan_items_lookup = {item['id']: item for item in (plan_items_result.data or [])}
                
                # Combine calendar selections with plan items
                time_block_ids_set = set(time_block_ids) if time_block_ids else set()
                
                for selection in calendar_result.data:
                    plan_item = plan_items_lookup.get(selection['plan_item_id'])
                    if plan_item:
                        # If archetype filter is specified, only include items from that archetype
                        if archetype_filter:
                            matches_archetype = plan_item.get('analysis_result_id') == archetype_filter
                            if matches_archetype:
                                calendar_items.append({
                                "selection_id": selection['id'],
                                "plan_item_id": selection['plan_item_id'],
                                "time_block_id": plan_item['time_block_id'],
                                "title": plan_item['title'],
                                "description": plan_item.get('description'),
                                "scheduled_time": plan_item.get('scheduled_time'),
                                "scheduled_end_time": plan_item.get('scheduled_end_time'),
                                "estimated_duration_minutes": plan_item.get('estimated_duration_minutes'),
                                "task_type": plan_item.get('task_type'),
                                "priority_level": plan_item.get('priority_level'),
                                "selected_at": selection.get('selection_timestamp'),
                                "calendar_notes": selection.get('calendar_notes')
                            })
                        else:
                            # No archetype filter - include items that belong to current time blocks
                            belongs_to_timeblock = plan_item.get('time_block_id') in time_block_ids_set
                            if belongs_to_timeblock:
                                calendar_items.append({
                                    "selection_id": selection['id'],
                                    "plan_item_id": selection['plan_item_id'],
                                    "time_block_id": plan_item['time_block_id'],
                                    "title": plan_item['title'],
                                    "description": plan_item.get('description'),
                                    "scheduled_time": plan_item.get('scheduled_time'),
                                    "scheduled_end_time": plan_item.get('scheduled_end_time'),
                                    "estimated_duration_minutes": plan_item.get('estimated_duration_minutes'),
                                    "task_type": plan_item.get('task_type'),
                                    "priority_level": plan_item.get('priority_level'),
                                    "selected_at": selection.get('selection_timestamp'),
                                    "calendar_notes": selection.get('calendar_notes')
                                })
        
        return {
            "success": True,
            "date": filter_date,
            "archetype_filter": archetype_filter,
            "time_blocks": time_blocks,
            "calendar_items": calendar_items,
            "total_time_blocks": len(time_blocks),
            "total_calendar_items": len(calendar_items)
        }
        
    except Exception as e:
        error_msg = f"Error in get_time_blocks_for_archetype: {str(e)}"
        print(error_msg)
        print(f"Profile ID: {profile_id}")
        print(f"Archetype filter: {archetype_filter}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get time blocks: {str(e)}"
        )

@router.get("/available-items/{profile_id}")
async def get_available_plan_items(
    profile_id: str = Path(..., description="User profile ID"),
    date: Optional[str] = Query(default=None, description="Date filter (YYYY-MM-DD)"),
    include_calendar_status: bool = Query(default=True, description="Include calendar selection status"),
    archetype_filter: Optional[str] = Query(default=None, description="Filter by specific archetype/analysis_id")
):
    """Get available plan items for calendar selection with archetype information (for routine plan tab)"""
    try:
        # Import supabase here to avoid startup issues
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
        
        supabase = create_client(supabase_url, supabase_key)
        filter_date = date or datetime.now().strftime('%Y-%m-%d')
        
        # Enhanced query with time_blocks (removed archetype_name as it doesn't exist)
        query = supabase.table("plan_items")\
            .select("""
                *,
                time_blocks!fk_plan_items_time_block_id (
                    id,
                    analysis_result_id,
                    block_title,
                    time_range,
                    purpose,
                    why_it_matters,
                    connection_to_insights,
                    health_data_integration
                )
            """)\
            .eq("profile_id", profile_id)
        
        # Apply archetype filter if specified
        if archetype_filter:
            query = query.eq("analysis_result_id", archetype_filter)
        
        result = query.order("scheduled_time").execute()
        
        # Get archetype information for each plan item
        enhanced_plan_items = []
        archetype_summary = {}
        
        for item in (result.data or []):
            # Add archetype metadata to each plan item
            analysis_id = item.get('analysis_result_id')
            
            # Since archetype_name doesn't exist in time_blocks, we'll generate a simple name
            archetype_name = None
            if analysis_id:
                if analysis_id not in archetype_summary:
                    # Generate a simple archetype name based on analysis_id
                    # We'll use the first 8 chars of the analysis_id to create a unique name
                    short_id = analysis_id[:8] if analysis_id else 'unknown'
                    archetype_name = f'Plan {short_id}'
                    archetype_summary[analysis_id] = archetype_name
                else:
                    archetype_name = archetype_summary[analysis_id]
            
            # Add archetype metadata to plan item
            enhanced_item = {
                **item,
                'archetype_metadata': {
                    'analysis_id': analysis_id,
                    'archetype_name': archetype_name or 'Unknown Archetype'
                }
            }
            enhanced_plan_items.append(enhanced_item)
        
        # Build response with archetype breakdown
        archetypes_found = {}
        for item in enhanced_plan_items:
            archetype_info = item['archetype_metadata']
            analysis_id = archetype_info['analysis_id']
            archetype_name = archetype_info['archetype_name']
            
            if analysis_id not in archetypes_found:
                archetypes_found[analysis_id] = {
                    'archetype_name': archetype_name,
                    'analysis_id': analysis_id,
                    'item_count': 0
                }
            archetypes_found[analysis_id]['item_count'] += 1
        
        return {
            "success": True,
            "date": filter_date,
            "total_items": len(enhanced_plan_items),
            "plan_items": enhanced_plan_items,
            "archetype_summary": {
                "total_archetypes": len(archetypes_found),
                "has_multiple_archetypes": len(archetypes_found) > 1,
                "archetypes": list(archetypes_found.values()),
                "applied_filter": archetype_filter
            }
        }
        
    except Exception as e:
        print(f"Error in get_available_plan_items: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available plan items: {str(e)}"
        )

@router.get("/selections/{profile_id}")
async def get_calendar_selections(
    profile_id: str = Path(..., description="User profile ID"),
    date: Optional[str] = Query(default=None, description="Date filter (YYYY-MM-DD)")
):
    """Get current calendar selections for a user and date"""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
        
        supabase = create_client(supabase_url, supabase_key)
        
        query = supabase.table("calendar_selections")\
            .select("""
                *,
                plan_items!inner (
                    id,
                    title,
                    description,
                    time_block_id,
                    scheduled_time,
                    scheduled_end_time,
                    estimated_duration_minutes,
                    task_type,
                    priority_level,
                    time_blocks!fk_plan_items_time_block_id (
                        id,
                        block_title,
                        time_range
                    )
                )
            """)\
            .eq("profile_id", profile_id)\
            .eq("selected_for_calendar", True)
        
        if date:
            # Filter by date if provided
            query = query.gte("selection_timestamp", f"{date}T00:00:00")\
                         .lt("selection_timestamp", f"{date}T23:59:59")
        
        result = query.order("selection_timestamp").execute()
        
        return {
            "success": True,
            "date": date,
            "selections": result.data or [],
            "total_selections": len(result.data or [])
        }
        
    except Exception as e:
        print(f"Error in get_calendar_selections: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get calendar selections: {str(e)}"
        )

@router.delete("/remove-selection")
async def remove_calendar_selection(
    profile_id: str = Query(..., description="User profile ID"),
    plan_item_id: str = Query(..., description="Plan item ID to remove from calendar")
):
    """Remove a plan item from calendar selections with validation"""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # 1. First check if the selection exists
        existing_selection = supabase.table("calendar_selections")\
            .select("id, plan_item_id")\
            .eq("profile_id", profile_id)\
            .eq("plan_item_id", plan_item_id)\
            .eq("selected_for_calendar", True)\
            .execute()
        
        if not existing_selection.data:
            raise HTTPException(
                status_code=404,
                detail=f"Calendar selection not found for plan_item_id: {plan_item_id}"
            )
        
        # 2. Get plan item details for better response
        plan_item = supabase.table("plan_items")\
            .select("title")\
            .eq("id", plan_item_id)\
            .single()\
            .execute()
        
        plan_item_title = plan_item.data.get('title', 'Unknown') if plan_item.data else 'Unknown'
        
        # 3. Delete the calendar selection
        result = supabase.table("calendar_selections")\
            .delete()\
            .eq("profile_id", profile_id)\
            .eq("plan_item_id", plan_item_id)\
            .execute()
        
        # 4. Verify deletion was successful
        if not result.data:
            # Double check if it was actually deleted
            check_deleted = supabase.table("calendar_selections")\
                .select("id")\
                .eq("profile_id", profile_id)\
                .eq("plan_item_id", plan_item_id)\
                .eq("selected_for_calendar", True)\
                .execute()
            
            if check_deleted.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to remove calendar selection - item still exists"
                )
        
        return {
            "success": True,
            "message": f"Removed '{plan_item_title}' from calendar",
            "profile_id": profile_id,
            "plan_item_id": plan_item_id,
            "removed_item_title": plan_item_title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in remove_calendar_selection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove calendar selection: {str(e)}"
        )

@router.post("/select")
async def select_plan_items_for_calendar(request: CalendarSelectionRequest):
    """Select plan items for calendar with validation"""
    try:
        # Import supabase here to avoid startup issues
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
        
        supabase = create_client(supabase_url, supabase_key)
        selection_date = request.date or datetime.now().strftime('%Y-%m-%d')
        
        # 1. Validate all plan items exist and belong to the same profile
        plan_items_check = supabase.table("plan_items")\
            .select("id, profile_id, analysis_result_id, time_block_id, title")\
            .in_("id", request.selected_plan_items)\
            .execute()
        
        found_items = {item['id']: item for item in (plan_items_check.data or [])}
        missing_items = set(request.selected_plan_items) - set(found_items.keys())
        
        if missing_items:
            raise HTTPException(
                status_code=400, 
                detail=f"Plan items not found: {list(missing_items)}"
            )
        
        # 2. Validate all items belong to the same profile
        profile_ids = {item['profile_id'] for item in found_items.values()}
        if len(profile_ids) > 1 or request.profile_id not in profile_ids:
            raise HTTPException(
                status_code=403,
                detail="Cannot select plan items from different profiles"
            )
        
        # 3. Validate time_block_ids are consistent (belong to same analysis)
        analysis_ids = {item['analysis_result_id'] for item in found_items.values()}
        if len(analysis_ids) > 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot mix plan items from different analyses/archetypes"
            )
        
        # 4. Check for existing selections to prevent duplicates
        existing_selections = supabase.table("calendar_selections")\
            .select("plan_item_id")\
            .eq("profile_id", request.profile_id)\
            .in_("plan_item_id", request.selected_plan_items)\
            .eq("selected_for_calendar", True)\
            .execute()
        
        existing_ids = {sel['plan_item_id'] for sel in (existing_selections.data or [])}
        new_items = [pid for pid in request.selected_plan_items if pid not in existing_ids]
        
        if not new_items:
            return {
                "success": True,
                "message": "All items already selected for calendar",
                "date": selection_date,
                "selections_created": 0,
                "already_selected": len(existing_ids)
            }
        
        # 5. Create calendar selections for new items only
        selections = []
        for plan_item_id in new_items:
            plan_item = found_items[plan_item_id]
            selection = {
                "id": str(uuid.uuid4()),
                "profile_id": request.profile_id,
                "plan_item_id": plan_item_id,
                "selected_for_calendar": True,
                "selection_timestamp": datetime.now().isoformat(),
                "calendar_notes": request.selection_notes or f"Added from routine plan: {plan_item['title']}"
            }
            selections.append(selection)
        
        # 6. Insert selections with proper error handling
        if selections:
            try:
                result = supabase.table("calendar_selections").insert(selections).execute()
                
                return {
                    "success": True,
                    "message": f"Added {len(new_items)} new items to calendar",
                    "date": selection_date,
                    "selections_created": len(selections),
                    "already_selected": len(existing_ids),
                    "skipped_duplicates": len(existing_ids)
                }
                
            except Exception as insert_error:
                # Handle potential constraint violations
                if "unique_calendar_selection" in str(insert_error):
                    raise HTTPException(
                        status_code=409,
                        detail="Some items are already selected for calendar"
                    )
                else:
                    raise insert_error
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to select items for calendar: {str(e)}"
        )

@router.get("/workflow-stats/{profile_id}")
async def get_workflow_stats(
    profile_id: str = Path(..., description="User profile ID"),
    date: Optional[str] = Query(default=None, description="Date filter (YYYY-MM-DD)")
):
    """Get workflow statistics for calendar engagement tracking"""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Missing Supabase configuration")
        
        supabase = create_client(supabase_url, supabase_key)
        filter_date = date or datetime.now().strftime('%Y-%m-%d')
        
        # Get total plan items for the date
        plan_items_query = supabase.table("plan_items")\
            .select("id")\
            .eq("profile_id", profile_id)
        
        # Note: We'd typically filter by extraction date, but for simplicity using all items
        plan_items_result = plan_items_query.execute()
        total_plan_items = len(plan_items_result.data or [])
        
        # Get calendar selections for the date
        calendar_query = supabase.table("calendar_selections")\
            .select("id")\
            .eq("profile_id", profile_id)\
            .eq("selected_for_calendar", True)\
            .gte("selection_timestamp", f"{filter_date}T00:00:00")\
            .lt("selection_timestamp", f"{filter_date}T23:59:59")
        
        calendar_result = calendar_query.execute()
        calendar_selected = len(calendar_result.data or [])
        
        # Get task check-ins for the date
        checkin_query = supabase.table("task_checkins")\
            .select("id")\
            .eq("profile_id", profile_id)\
            .eq("planned_date", filter_date)
        
        checkin_result = checkin_query.execute()
        checked_in = len(checkin_result.data or [])
        
        # Calculate rates
        calendar_not_selected = max(0, total_plan_items - calendar_selected)
        calendar_but_no_checkin = max(0, calendar_selected - checked_in)
        
        selection_rate_percent = (calendar_selected / total_plan_items * 100) if total_plan_items > 0 else 0
        completion_rate_percent = (checked_in / calendar_selected * 100) if calendar_selected > 0 else 0
        
        return {
            "profile_id": profile_id,
            "date": filter_date,
            "total_plan_items": total_plan_items,
            "calendar_selected": calendar_selected,
            "calendar_not_selected": calendar_not_selected,
            "checked_in": checked_in,
            "calendar_but_no_checkin": calendar_but_no_checkin,
            "selection_rate_percent": round(selection_rate_percent, 2),
            "completion_rate_percent": round(completion_rate_percent, 2)
        }
        
    except Exception as e:
        print(f"Error in get_workflow_stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow stats: {str(e)}"
        )