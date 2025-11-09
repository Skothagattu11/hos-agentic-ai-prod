"""
Anchoring endpoint implementation using Supabase REST API + Real Anchoring AI

This uses:
1. Supabase REST API to fetch saved_schedules and plan_items
2. Real AnchoringCoordinator with AI scoring for intelligent task anchoring
3. Saved schedule tasks act as "calendar events" for anchoring
"""
import os
import httpx
from datetime import datetime, date as date_type, time as time_type
from typing import List, Dict, Any


async def generate_anchors_via_rest_api(body: dict) -> dict:
    """
    Generate anchored tasks using real AnchoringCoordinator + Supabase REST API

    Flow:
    1. Fetch saved schedule tasks from database (these become "calendar events")
    2. Fetch plan items for the user/date
    3. Use AnchoringCoordinator to intelligently match tasks to schedule slots
    4. Return anchored + standalone tasks

    Args:
        body: {
            "user_id": str,
            "date": str (ISO format),
            "schedule_id": str (optional),
            "include_google_calendar": bool,
            "confidence_threshold": float,
            "use_ai_scoring": bool (optional, default True)
        }

    Returns:
        {
            "anchored_tasks": List[dict],
            "standalone_tasks": List[dict],
            "message": str
        }
    """
    user_id = body.get("user_id")
    date_str = body.get("date")
    schedule_id = body.get("schedule_id")
    confidence_threshold = body.get("confidence_threshold", 0.7)
    use_ai_scoring = body.get("use_ai_scoring", True)  # Use AI by default

    # Use TWO databases:
    # 1. SUPABASE_CAL_URL for saved_schedules (calendar database)
    # 2. SUPABASE_URL for plan_items (main database)
    supabase_cal_url = os.getenv("SUPABASE_CAL_URL")
    supabase_cal_key = os.getenv("SUPABASE_CAL_SERVICE_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    # Headers for calendar database
    headers_cal = {
        "apikey": supabase_cal_key,
        "Authorization": f"Bearer {supabase_cal_key}",
        "Content-Type": "application/json"
    }

    # Headers for main database
    headers_main = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }

    print(f"🎯 [ANCHORING-REST] Request: user={user_id}, date={date_str}, schedule={schedule_id}, ai={use_ai_scoring}")

    # Import anchoring services
    from services.anchoring import (
        AnchoringCoordinator,
        TaskToAnchor,
        CalendarEvent,
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ===================================================================
        # STEP 1: Fetch saved schedule tasks (these become calendar events)
        # ===================================================================
        calendar_events = []
        if schedule_id:
            print(f"📅 [ANCHORING-REST] Fetching schedule tasks for {schedule_id}")

            response = await client.get(
                f"{supabase_cal_url}/rest/v1/scheduled_tasks?schedule_id=eq.{schedule_id}&order=start_time.asc",
                headers=headers_cal
            )

            if response.status_code == 200:
                tasks = response.json()
                target_date = date_type.fromisoformat(date_str)

                for task in tasks:
                    # Convert schedule task to CalendarEvent format
                    start_time_str = task['start_time']  # "HH:MM:SS"
                    end_time_str = task['end_time']

                    # Parse times
                    start_parts = start_time_str.split(':')
                    end_parts = end_time_str.split(':')
                    start_time = time_type(int(start_parts[0]), int(start_parts[1]))
                    end_time = time_type(int(end_parts[0]), int(end_parts[1]))

                    # Create CalendarEvent from schedule task
                    calendar_events.append(CalendarEvent(
                        id=task['id'],
                        title=task['task_name'],
                        start_time=datetime.combine(target_date, start_time),
                        end_time=datetime.combine(target_date, end_time)
                    ))

                print(f"✅ [ANCHORING-REST] Loaded {len(calendar_events)} calendar events from saved schedule")

        # ===================================================================
        # STEP 2: Fetch plan items for the date
        # ===================================================================
        print(f"📋 [ANCHORING-REST] Fetching plan items for {date_str}")

        # Get analysis for the date (from main database)
        response = await client.get(
            f"{supabase_url}/rest/v1/holistic_analysis_results"
            f"?user_id=eq.{user_id}"
            f"&analysis_date=eq.{date_str}"
            f"&order=created_at.desc"
            f"&limit=1",
            headers=headers_main
        )

        if response.status_code != 200 or not response.json():
            print(f"⚠️ [ANCHORING-REST] No analysis found for {date_str}")
            return {
                "anchored_tasks": [],
                "standalone_tasks": [],
                "message": f"No plan found for {date_str}. Create a plan first."
            }

        analysis = response.json()[0]
        analysis_id = analysis['id']
        print(f"📊 [ANCHORING-REST] Found analysis: {analysis_id}")

        # Fetch plan items (from main database)
        response = await client.get(
            f"{supabase_url}/rest/v1/plan_items"
            f"?analysis_result_id=eq.{analysis_id}"
            f"&plan_date=eq.{date_str}"
            f"&order=scheduled_time.asc",
            headers=headers_main
        )

        if response.status_code != 200:
            print(f"❌ [ANCHORING-REST] Failed to fetch plan items")
            return {
                "anchored_tasks": [],
                "standalone_tasks": [],
                "message": "Failed to fetch plan items"
            }

        plan_items = response.json()
        print(f"✅ [ANCHORING-REST] Found {len(plan_items)} plan items")

        # ===================================================================
        # STEP 3: Convert plan items to TaskToAnchor format
        # ===================================================================
        tasks_to_anchor = []
        for item in plan_items:
            scheduled_time_str = item.get('scheduled_time', '08:00')
            if isinstance(scheduled_time_str, str):
                # Parse time
                time_parts = scheduled_time_str.split(':')
                scheduled_time = time_type(int(time_parts[0]), int(time_parts[1]))
            else:
                scheduled_time = time_type(8, 0)

            # Calculate end time based on duration
            duration_minutes = item.get('estimated_duration_minutes', 15)
            total_minutes = scheduled_time.hour * 60 + scheduled_time.minute + duration_minutes
            end_hour = (total_minutes // 60) % 24
            end_minute = total_minutes % 60
            scheduled_end_time = time_type(end_hour, end_minute)

            tasks_to_anchor.append(TaskToAnchor(
                id=item['id'],
                title=item['title'],
                description=item.get('description', item['title']),
                category=item.get('category', 'general'),
                priority_level=item.get('priority_level', 'medium'),
                scheduled_time=scheduled_time,
                scheduled_end_time=scheduled_end_time,
                estimated_duration_minutes=duration_minutes,
                time_block=item.get('time_block', 'morning'),
                energy_zone_preference=None
            ))

        print(f"🔧 [ANCHORING-REST] Converted {len(tasks_to_anchor)} tasks to anchor")

        # ===================================================================
        # STEP 4: Use AnchoringCoordinator (WITH AI if requested)
        # ===================================================================
        if schedule_id and calendar_events and tasks_to_anchor:
            print(f"🤖 [ANCHORING-REST] Running AnchoringCoordinator (AI={use_ai_scoring})")

            # Initialize coordinator
            coordinator = AnchoringCoordinator(use_ai_scoring=use_ai_scoring)

            # Create custom calendar provider with our saved schedule events
            from services.anchoring.calendar_integration_service import CalendarFetchResult, CalendarConnectionStatus

            # Mock the calendar fetch to return our saved schedule events
            class SavedScheduleCalendarService:
                async def fetch_calendar_events(
                    self,
                    user_id: str,
                    target_date: date_type,
                    supabase_token: str = None,
                    use_mock_data: bool = False,
                    mock_profile: str = None
                ):
                    """Return saved schedule events as calendar events"""
                    return CalendarFetchResult(
                        success=True,
                        events=calendar_events,
                        connection_status=CalendarConnectionStatus.CONNECTED,
                        total_events=len(calendar_events),
                        date=target_date,
                        is_mock_data=False
                    )

            # Temporarily replace calendar service
            original_calendar_service = coordinator.calendar_service
            coordinator.calendar_service = SavedScheduleCalendarService()

            try:
                # Run anchoring!
                target_date = date_type.fromisoformat(date_str)
                result = await coordinator.anchor_tasks(
                    user_id=user_id,
                    tasks=tasks_to_anchor,
                    target_date=target_date,
                    use_mock_calendar=False,  # We're providing real events
                    min_gap_minutes=5
                )

                print(f"✅ [ANCHORING-REST] Anchoring complete: {len(result.assignments)} anchored, {len(result.unassigned_tasks)} standalone")

                # Create task mapping for quick lookup
                task_map = {task.id: task for task in tasks_to_anchor}

                # Format response
                anchored_tasks = []
                for assignment in result.assignments:
                    # Only include if confidence meets threshold
                    if assignment.confidence_score >= confidence_threshold:
                        # Find the calendar event this was anchored to
                        # Use anchored_time to find the event
                        anchored_event = next(
                            (e for e in calendar_events if e.start_time.time() <= assignment.anchored_time <= e.end_time.time()),
                            None
                        )

                        # Get the original task object
                        task = task_map.get(assignment.task_id)

                        anchored_tasks.append({
                            "task_id": assignment.task_id,
                            "task_name": assignment.task_title,
                            "task_description": assignment.task_title,
                            "duration_minutes": assignment.duration_minutes,
                            "anchored_time": f"{date_str}T{assignment.anchored_time.strftime('%H:%M:%S')}",
                            "anchored_to_event_id": anchored_event.id if anchored_event else schedule_id,
                            "anchored_to_event_title": anchored_event.title if anchored_event else "Schedule Event",
                            "confidence": assignment.confidence_score,
                            "health_tag": task.category if task else "general",
                            "reasoning": assignment.scoring_breakdown.get('reasoning', 'Algorithmically matched')
                        })

                # Format standalone tasks (use unassigned_tasks, not unanchored_tasks)
                standalone_tasks = []
                unassigned_task_ids = result.unassigned_tasks if hasattr(result, 'unassigned_tasks') else []

                # Find the actual task objects for unassigned IDs
                unassigned_task_objects = [t for t in tasks_to_anchor if t.id in unassigned_task_ids]

                for task in unassigned_task_objects:
                    # Find original plan item to get time
                    plan_item = next((p for p in plan_items if p['id'] == task.id), None)
                    if plan_item:
                        scheduled_time = plan_item.get('scheduled_time', '08:00')[:5]
                        duration = task.estimated_duration_minutes
                        end_time = _add_minutes_to_time(scheduled_time, duration)

                        standalone_tasks.append({
                            "task_id": task.id,
                            "task_name": task.title,
                            "start_time": scheduled_time,
                            "end_time": end_time,
                            "duration_minutes": duration
                        })

                return {
                    "anchored_tasks": anchored_tasks,
                    "standalone_tasks": standalone_tasks,
                    "message": f"Successfully anchored {len(anchored_tasks)} tasks using {'AI-enhanced' if use_ai_scoring else 'algorithmic'} scoring"
                }

            finally:
                # Restore original calendar service
                coordinator.calendar_service = original_calendar_service

        else:
            # No schedule selected - return all as standalone
            print(f"⚡ [ANCHORING-REST] No schedule selected, returning all as standalone")

            standalone_tasks = []
            for item in plan_items:
                scheduled_time = item.get('scheduled_time', '08:00')
                if isinstance(scheduled_time, str):
                    scheduled_time = scheduled_time[:5]

                duration = item.get('estimated_duration_minutes', 15)
                end_time = _add_minutes_to_time(scheduled_time, duration)

                standalone_tasks.append({
                    "task_id": item['id'],
                    "task_name": item['title'],
                    "start_time": scheduled_time,
                    "end_time": end_time,
                    "duration_minutes": duration
                })

            return {
                "anchored_tasks": [],
                "standalone_tasks": standalone_tasks,
                "message": "No schedule selected - all tasks standalone"
            }


def _add_minutes_to_time(time_str: str, minutes: int) -> str:
    """Add minutes to HH:MM time string"""
    h, m = map(int, time_str.split(':'))
    total_minutes = h * 60 + m + minutes
    new_h = (total_minutes // 60) % 24
    new_m = total_minutes % 60
    return f"{new_h:02d}:{new_m:02d}"
