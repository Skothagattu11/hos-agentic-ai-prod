"""
Task Loader Service - Phase 1

This service loads plan_items from Supabase for calendar anchoring.
It uses Supabase REST API client (not pgadapter) for development compatibility.

Key Features:
- Loads plan_items filtered by analysis_result_id
- Joins with time_blocks for contextual metadata
- Returns tasks ready for anchoring algorithm
- Uses Supabase REST API (works in development)

Integration:
- Reads from: plan_items, time_blocks tables
- Never modifies: task_checkins, time_blocks (read-only for patterns)
- Respects: Friction-reduction system (Phase 5.0)
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
from dataclasses import dataclass
from supabase import create_client, Client

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TimeBlockContext:
    """
    Context from time_blocks table

    Provides additional metadata about when tasks should occur
    """
    block_id: str
    block_title: str
    time_range: str  # e.g., "6:00-7:00 AM"
    purpose: Optional[str] = None
    why_it_matters: Optional[str] = None
    block_order: int = 1


@dataclass
class PlanItemToAnchor:
    """
    Represents a plan_item ready for calendar anchoring

    This model includes both the task details and time block context
    """
    # Core task fields (required - no defaults)
    id: str
    title: str
    category: str
    priority_level: str
    estimated_duration_minutes: int
    plan_date: date
    analysis_result_id: str

    # Optional fields (with defaults)
    description: Optional[str] = None
    task_type: Optional[str] = None
    scheduled_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    time_block: Optional[TimeBlockContext] = None
    is_trackable: bool = True
    is_anchored: bool = False
    confidence_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "task_type": self.task_type,
            "priority_level": self.priority_level,
            "scheduled_time": self.scheduled_time.strftime("%H:%M:%S") if self.scheduled_time else None,
            "scheduled_end_time": self.scheduled_end_time.strftime("%H:%M:%S") if self.scheduled_end_time else None,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "plan_date": self.plan_date.isoformat(),
            "analysis_result_id": self.analysis_result_id,
            "is_trackable": self.is_trackable,
            "is_anchored": self.is_anchored,
            "confidence_score": self.confidence_score,
        }

        if self.time_block:
            result["time_block"] = {
                "block_id": self.time_block.block_id,
                "block_title": self.time_block.block_title,
                "time_range": self.time_block.time_range,
                "purpose": self.time_block.purpose,
                "block_order": self.time_block.block_order,
            }

        return result


# ============================================================================
# Task Loader Service
# ============================================================================

class TaskLoaderService:
    """
    Service for loading plan_items from Supabase for anchoring

    This service uses Supabase REST API client for development compatibility.
    It loads tasks with time_blocks context for intelligent anchoring.

    Usage:
        service = TaskLoaderService()
        tasks = await service.load_plan_items_to_anchor(
            analysis_result_id="uuid-123",
            plan_date=date(2025, 11, 6)
        )
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize task loader service

        Args:
            supabase_client: Optional pre-configured Supabase client
        """
        if supabase_client:
            self.supabase = supabase_client
        else:
            # Create client from environment variables
            # Use SERVICE_KEY for backend operations (has full permissions)
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment"
                )

            self.supabase = create_client(supabase_url, supabase_key)

        logger.info("[TASK-LOADER] Initialized with Supabase REST API client")

    async def load_plan_items_to_anchor(
        self,
        analysis_result_id: str,
        plan_date: Optional[date] = None,
        include_already_anchored: bool = False
    ) -> List[PlanItemToAnchor]:
        """
        Load plan_items ready for calendar anchoring

        Args:
            analysis_result_id: UUID of plan generation result
            plan_date: Optional date to filter by (if None, loads all items for this plan)
            include_already_anchored: Include tasks that are already anchored

        Returns:
            List of PlanItemToAnchor objects with time_blocks context

        Raises:
            Exception: If database query fails
        """
        try:
            logger.info(
                f"[TASK-LOADER] Loading plan_items for analysis_result_id={analysis_result_id}"
                + (f", date={plan_date}" if plan_date else " (all dates)")
            )

            # Step 1: Load plan_items
            query = (
                self.supabase
                .table('plan_items')
                .select('*')
                .eq('analysis_result_id', analysis_result_id)
                .eq('is_trackable', True)
                .eq('marked_as_deleted', False)  # Exclude deleted items
                .order('scheduled_time', desc=False)
            )

            # Optional: filter by date if provided
            if plan_date:
                query = query.eq('plan_date', plan_date.isoformat())

            # Optionally filter out already-anchored items
            # Note: Using 'added_to_calendar' field instead of 'is_anchored'
            if not include_already_anchored:
                query = query.eq('added_to_calendar', False)

            response = query.execute()

            # Debug logging
            print(f"[DEBUG] Query filters:")
            print(f"  - analysis_result_id: {analysis_result_id}")
            print(f"  - plan_date: {plan_date.isoformat() if plan_date else 'None (all dates)'}")
            print(f"  - is_trackable: True")
            print(f"  - marked_as_deleted: False")
            print(f"  - added_to_calendar: {False if not include_already_anchored else 'any'}")
            print(f"[DEBUG] Response status: {response.status_code if hasattr(response, 'status_code') else 'N/A'}")
            print(f"[DEBUG] Response data count: {len(response.data) if response.data else 0}")

            if not response.data:
                logger.warning(
                    f"[TASK-LOADER] No plan_items found for analysis_result_id={analysis_result_id}"
                )

                # Try a simpler query to debug
                print(f"\n[DEBUG] Trying simpler query without filters...")
                simple_query = (
                    self.supabase
                    .table('plan_items')
                    .select('id, title, analysis_result_id, plan_date, is_trackable, marked_as_deleted, added_to_calendar')
                    .eq('analysis_result_id', analysis_result_id)
                    .limit(5)
                )
                simple_response = simple_query.execute()
                print(f"[DEBUG] Simple query returned {len(simple_response.data) if simple_response.data else 0} results")
                if simple_response.data:
                    print(f"[DEBUG] Sample items:")
                    for item in simple_response.data[:3]:
                        print(f"  - {item.get('title')}: trackable={item.get('is_trackable')}, deleted={item.get('marked_as_deleted')}, calendar={item.get('added_to_calendar')}, date={item.get('plan_date')}")

                return []

            plan_items = response.data
            logger.info(f"[TASK-LOADER] Loaded {len(plan_items)} plan_items")

            # Step 2: Load time_blocks for context
            time_blocks_map = await self._load_time_blocks(analysis_result_id)

            # Step 3: Combine plan_items with time_blocks context
            tasks = []
            for item in plan_items:
                task = self._parse_plan_item(item, time_blocks_map)
                if task:
                    tasks.append(task)

            logger.info(
                f"[TASK-LOADER] ✅ Loaded {len(tasks)} tasks ready for anchoring"
            )

            return tasks

        except Exception as e:
            logger.error(f"[TASK-LOADER] Error loading plan_items: {str(e)}")
            raise

    async def _load_time_blocks(
        self,
        analysis_result_id: str
    ) -> Dict[str, TimeBlockContext]:
        """
        Load time_blocks for analysis_result_id

        Args:
            analysis_result_id: UUID of plan generation result

        Returns:
            Dictionary mapping time_block_id to TimeBlockContext
        """
        try:
            response = (
                self.supabase
                .table('time_blocks')
                .select('*')
                .eq('analysis_result_id', analysis_result_id)
                .order('block_order', desc=False)
                .execute()
            )

            if not response.data:
                logger.debug(
                    f"[TASK-LOADER] No time_blocks found for analysis_result_id={analysis_result_id}"
                )
                return {}

            # Build map of block_id -> TimeBlockContext
            blocks_map = {}
            for block in response.data:
                block_id = block.get('id')
                if block_id:
                    blocks_map[block_id] = TimeBlockContext(
                        block_id=block_id,
                        block_title=block.get('block_title', 'Unknown Block'),
                        time_range=block.get('time_range', ''),
                        purpose=block.get('purpose'),
                        why_it_matters=block.get('why_it_matters'),
                        block_order=block.get('block_order', 1)
                    )

            logger.info(f"[TASK-LOADER] Loaded {len(blocks_map)} time_blocks")

            return blocks_map

        except Exception as e:
            logger.error(f"[TASK-LOADER] Error loading time_blocks: {str(e)}")
            return {}

    def _parse_plan_item(
        self,
        item: Dict[str, Any],
        time_blocks_map: Dict[str, TimeBlockContext]
    ) -> Optional[PlanItemToAnchor]:
        """
        Parse plan_item dictionary into PlanItemToAnchor object

        Args:
            item: Plan item dictionary from Supabase
            time_blocks_map: Map of time_block_id to TimeBlockContext

        Returns:
            PlanItemToAnchor object or None if invalid
        """
        try:
            # Parse required fields
            item_id = item.get('id')
            title = item.get('title')
            category = item.get('category')
            analysis_result_id = item.get('analysis_result_id')

            if not all([item_id, title, category, analysis_result_id]):
                logger.warning(f"[TASK-LOADER] Missing required fields in plan_item: {item_id}")
                return None

            # Parse date
            plan_date_str = item.get('plan_date')
            if not plan_date_str:
                logger.warning(f"[TASK-LOADER] Missing plan_date for item: {item_id}")
                return None

            plan_date_obj = datetime.fromisoformat(str(plan_date_str)).date()

            # Parse times (may be None)
            scheduled_time_obj = None
            if item.get('scheduled_time'):
                try:
                    scheduled_time_obj = datetime.strptime(
                        str(item['scheduled_time']), "%H:%M:%S"
                    ).time()
                except:
                    # Try alternative format
                    try:
                        scheduled_time_obj = datetime.fromisoformat(
                            str(item['scheduled_time'])
                        ).time()
                    except:
                        pass

            scheduled_end_time_obj = None
            if item.get('scheduled_end_time'):
                try:
                    scheduled_end_time_obj = datetime.strptime(
                        str(item['scheduled_end_time']), "%H:%M:%S"
                    ).time()
                except:
                    try:
                        scheduled_end_time_obj = datetime.fromisoformat(
                            str(item['scheduled_end_time'])
                        ).time()
                    except:
                        pass

            # Get time block context
            time_block_id = item.get('time_block_id')
            time_block = time_blocks_map.get(time_block_id) if time_block_id else None

            # Create PlanItemToAnchor object
            return PlanItemToAnchor(
                id=item_id,
                title=title,
                description=item.get('description'),
                category=category,
                task_type=item.get('task_type'),
                priority_level=item.get('priority_level', 'medium'),
                scheduled_time=scheduled_time_obj,
                scheduled_end_time=scheduled_end_time_obj,
                estimated_duration_minutes=item.get('estimated_duration_minutes', 15),
                plan_date=plan_date_obj,
                time_block=time_block,
                analysis_result_id=analysis_result_id,
                is_trackable=item.get('is_trackable', True),
                is_anchored=item.get('added_to_calendar', False),  # Map to correct DB field
                confidence_score=item.get('confidence_score')
            )

        except Exception as e:
            logger.error(f"[TASK-LOADER] Error parsing plan_item: {str(e)}")
            return None

    async def update_anchored_times(
        self,
        anchored_tasks: List[Dict[str, Any]]
    ) -> bool:
        """
        Batch update plan_items with anchored times

        Args:
            anchored_tasks: List of dicts with task_id, anchored_time, metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                f"[TASK-LOADER] Updating {len(anchored_tasks)} plan_items with anchored times"
            )

            # Batch update (Supabase doesn't support true batch, so update one by one)
            success_count = 0
            for task_data in anchored_tasks:
                task_id = task_data.get('task_id')
                anchored_time = task_data.get('anchored_time')
                anchored_end_time = task_data.get('anchored_end_time')
                metadata = task_data.get('anchoring_metadata', {})
                confidence = task_data.get('confidence_score', 0.0)

                try:
                    response = (
                        self.supabase
                        .table('plan_items')
                        .update({
                            'scheduled_time': anchored_time,
                            'scheduled_end_time': anchored_end_time,
                            'anchoring_metadata': metadata,
                            'is_anchored': True,
                            'anchored_at': datetime.utcnow().isoformat(),
                            'confidence_score': confidence,
                            'updated_at': datetime.utcnow().isoformat()
                        })
                        .eq('id', task_id)
                        .execute()
                    )

                    if response.data:
                        success_count += 1
                    else:
                        logger.warning(f"[TASK-LOADER] Failed to update task {task_id}")

                except Exception as e:
                    logger.error(f"[TASK-LOADER] Error updating task {task_id}: {str(e)}")
                    continue

            logger.info(
                f"[TASK-LOADER] ✅ Successfully updated {success_count}/{len(anchored_tasks)} tasks"
            )

            return success_count == len(anchored_tasks)

        except Exception as e:
            logger.error(f"[TASK-LOADER] Error in batch update: {str(e)}")
            return False


# ============================================================================
# Singleton Instance
# ============================================================================

_task_loader_instance: Optional[TaskLoaderService] = None


def get_task_loader_service() -> TaskLoaderService:
    """
    Get singleton instance of TaskLoaderService

    Returns:
        TaskLoaderService instance
    """
    global _task_loader_instance

    if _task_loader_instance is None:
        _task_loader_instance = TaskLoaderService()

    return _task_loader_instance
