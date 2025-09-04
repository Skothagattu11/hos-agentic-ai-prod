#!/usr/bin/env python3
"""
Calendar Selection Service
Manages the calendar_selections table and workflow for plan item selections
"""

import os
import uuid
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from supabase import create_client
import logging

logger = logging.getLogger(__name__)

class CalendarSelectionService:
    """Service for managing calendar selections and plan item workflow"""
    
    def __init__(self):
        """Initialize the calendar selection service with Supabase connection"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_KEY.")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)

    async def add_plan_item_to_calendar(
        self, 
        profile_id: str, 
        plan_item_id: str, 
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a single plan item to calendar selections
        
        Args:
            profile_id: User profile ID
            plan_item_id: Plan item ID to add to calendar
            notes: Optional notes about the selection
            
        Returns:
            Dict with selection details and success status
        """
        try:
            # Check if plan item exists
            plan_item_check = self.supabase.table("plan_items")\
                .select("id, title, time_block_id, scheduled_time")\
                .eq("id", plan_item_id)\
                .eq("profile_id", profile_id)\
                .execute()
            
            if not plan_item_check.data:
                raise ValueError(f"Plan item {plan_item_id} not found for user {profile_id}")
            
            plan_item = plan_item_check.data[0]
            
            # Create calendar selection
            selection = {
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "plan_item_id": plan_item_id,
                "selected_for_calendar": True,
                "selection_timestamp": datetime.now().isoformat(),
                "calendar_notes": notes
            }
            
            # Upsert to handle duplicates
            result = self.supabase.table("calendar_selections").upsert(
                selection,
                on_conflict="profile_id,plan_item_id"
            ).execute()
            
            logger.info(f"Added plan item {plan_item_id} to calendar for user {profile_id}")
            
            return {
                "success": True,
                "selection_id": selection["id"],
                "plan_item": plan_item,
                "message": f"Added '{plan_item['title']}' to calendar"
            }
            
        except Exception as e:
            logger.error(f"Error adding plan item to calendar: {e}")
            raise e

    async def remove_plan_item_from_calendar(
        self, 
        profile_id: str, 
        plan_item_id: str
    ) -> Dict[str, Any]:
        """
        Remove a plan item from calendar selections
        
        Args:
            profile_id: User profile ID
            plan_item_id: Plan item ID to remove from calendar
            
        Returns:
            Dict with removal status
        """
        try:
            # Delete the calendar selection
            result = self.supabase.table("calendar_selections")\
                .delete()\
                .eq("profile_id", profile_id)\
                .eq("plan_item_id", plan_item_id)\
                .execute()
            
            logger.info(f"Removed plan item {plan_item_id} from calendar for user {profile_id}")
            
            return {
                "success": True,
                "message": "Item removed from calendar",
                "removed_items": len(result.data or [])
            }
            
        except Exception as e:
            logger.error(f"Error removing plan item from calendar: {e}")
            raise e

    async def get_calendar_selections(
        self, 
        profile_id: str, 
        date_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current calendar selections for a user
        
        Args:
            profile_id: User profile ID
            date_filter: Optional date filter (YYYY-MM-DD)
            
        Returns:
            Dict with calendar selections and metadata
        """
        try:
            query = self.supabase.table("calendar_selections")\
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
                            time_range,
                            block_order
                        )
                    )
                """)\
                .eq("profile_id", profile_id)\
                .eq("selected_for_calendar", True)
            
            if date_filter:
                query = query.gte("selection_timestamp", f"{date_filter}T00:00:00")\
                             .lt("selection_timestamp", f"{date_filter}T23:59:59")
            
            result = query.order("selection_timestamp").execute()
            
            # Group by time block for easier frontend consumption
            time_blocks = {}
            selections = result.data or []
            
            for selection in selections:
                plan_item = selection.get('plan_items')
                if plan_item and plan_item.get('time_blocks'):
                    time_block = plan_item['time_blocks']
                    time_block_id = time_block['id']
                    
                    if time_block_id not in time_blocks:
                        time_blocks[time_block_id] = {
                            "time_block": time_block,
                            "items": []
                        }
                    
                    time_blocks[time_block_id]["items"].append({
                        "selection_id": selection['id'],
                        "plan_item": plan_item,
                        "selected_at": selection['selection_timestamp'],
                        "notes": selection.get('calendar_notes')
                    })
            
            return {
                "success": True,
                "profile_id": profile_id,
                "date_filter": date_filter,
                "total_selections": len(selections),
                "selections": selections,
                "time_blocks": time_blocks
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar selections: {e}")
            raise e

    async def get_calendar_items_for_time_blocks(
        self, 
        profile_id: str, 
        archetype_filter: Optional[str] = None,
        date_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get calendar items organized by time blocks for a specific archetype
        
        Args:
            profile_id: User profile ID
            archetype_filter: Filter by analysis_result_id (archetype)
            date_filter: Optional date filter (YYYY-MM-DD)
            
        Returns:
            Dict with time blocks and their calendar-selected items
        """
        try:
            # Get time blocks structure
            time_blocks_query = self.supabase.table("time_blocks")\
                .select("*")\
                .eq("profile_id", profile_id)
            
            if archetype_filter:
                time_blocks_query = time_blocks_query.eq("analysis_result_id", archetype_filter)
            
            time_blocks_result = time_blocks_query.order("block_order").execute()
            
            # Get calendar selections for these time blocks
            calendar_items = {}
            if time_blocks_result.data:
                time_block_ids = [tb['id'] for tb in time_blocks_result.data]
                
                # Get plan items that are selected for calendar and belong to these time blocks
                selections_query = self.supabase.table("calendar_selections")\
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
                            priority_level
                        )
                    """)\
                    .eq("profile_id", profile_id)\
                    .eq("selected_for_calendar", True)\
                    .in_("plan_items.time_block_id", time_block_ids)
                
                if date_filter:
                    selections_query = selections_query.gte("selection_timestamp", f"{date_filter}T00:00:00")\
                                                     .lt("selection_timestamp", f"{date_filter}T23:59:59")
                
                selections_result = selections_query.execute()
                
                # Organize items by time block
                for selection in (selections_result.data or []):
                    plan_item = selection.get('plan_items')
                    if plan_item:
                        time_block_id = plan_item.get('time_block_id')
                        if time_block_id not in calendar_items:
                            calendar_items[time_block_id] = []
                        
                        calendar_items[time_block_id].append({
                            "selection_id": selection['id'],
                            "plan_item_id": selection['plan_item_id'],
                            "title": plan_item.get('title'),
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
                "profile_id": profile_id,
                "archetype_filter": archetype_filter,
                "date_filter": date_filter,
                "time_blocks": time_blocks_result.data or [],
                "calendar_items": calendar_items,
                "total_time_blocks": len(time_blocks_result.data or []),
                "total_calendar_items": sum(len(items) for items in calendar_items.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting calendar items for time blocks: {e}")
            raise e

    async def bulk_add_to_calendar(
        self, 
        profile_id: str, 
        plan_item_ids: List[str], 
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add multiple plan items to calendar selections at once
        
        Args:
            profile_id: User profile ID
            plan_item_ids: List of plan item IDs to add
            notes: Optional notes for all selections
            
        Returns:
            Dict with bulk operation results
        """
        try:
            selections = []
            for plan_item_id in plan_item_ids:
                selection = {
                    "id": str(uuid.uuid4()),
                    "profile_id": profile_id,
                    "plan_item_id": plan_item_id,
                    "selected_for_calendar": True,
                    "selection_timestamp": datetime.now().isoformat(),
                    "calendar_notes": notes
                }
                selections.append(selection)
            
            # Bulk upsert
            result = self.supabase.table("calendar_selections").upsert(
                selections,
                on_conflict="profile_id,plan_item_id"
            ).execute()
            
            logger.info(f"Bulk added {len(plan_item_ids)} items to calendar for user {profile_id}")
            
            return {
                "success": True,
                "items_processed": len(plan_item_ids),
                "selections_created": len(selections),
                "message": f"Added {len(selections)} items to calendar"
            }
            
        except Exception as e:
            logger.error(f"Error in bulk add to calendar: {e}")
            raise e

    async def get_selection_stats(
        self, 
        profile_id: str, 
        date_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about calendar selections for analytics
        
        Args:
            profile_id: User profile ID
            date_filter: Optional date filter (YYYY-MM-DD)
            
        Returns:
            Dict with selection statistics
        """
        try:
            # Get total available plan items
            plan_items_query = self.supabase.table("plan_items")\
                .select("id")\
                .eq("profile_id", profile_id)
            
            plan_items_result = plan_items_query.execute()
            total_available = len(plan_items_result.data or [])
            
            # Get calendar selections
            selections_query = self.supabase.table("calendar_selections")\
                .select("id")\
                .eq("profile_id", profile_id)\
                .eq("selected_for_calendar", True)
            
            if date_filter:
                selections_query = selections_query.gte("selection_timestamp", f"{date_filter}T00:00:00")\
                                                 .lt("selection_timestamp", f"{date_filter}T23:59:59")
            
            selections_result = selections_query.execute()
            total_selected = len(selections_result.data or [])
            
            # Calculate selection rate
            selection_rate = (total_selected / total_available * 100) if total_available > 0 else 0
            
            return {
                "profile_id": profile_id,
                "date_filter": date_filter,
                "total_available": total_available,
                "total_selected": total_selected,
                "not_selected": total_available - total_selected,
                "selection_rate_percent": round(selection_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting selection stats: {e}")
            raise e


# Singleton instance for use across the application
calendar_selection_service = CalendarSelectionService()