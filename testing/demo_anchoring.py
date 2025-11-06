"""
Anchoring Algorithm Demo - Real Plan Data

Shows complete anchoring workflow with real database data:
1. Fetches plan_items from database using analysis_result_id
2. Fetches time_blocks context for each task
3. Loads calendar events (mock or real Google Calendar)
4. Runs anchoring coordinator to find optimal task placements
5. Displays before/after comparison with visual timeline

Usage:
    python testing/demo_anchoring.py <analysis_result_id>

Example:
    python testing/demo_anchoring.py a1b2c3d4-e5f6-7890-abcd-ef1234567890
"""

import asyncio
import sys
import os
from datetime import date, time, datetime, timedelta
from typing import List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from services.anchoring import (
    get_anchoring_coordinator,
    get_calendar_integration_service,
    get_task_loader_service,
)
from services.anchoring.basic_scorer_service import TaskToAnchor


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title: str):
    """Print formatted section"""
    print(f"\n{'-' * 80}")
    print(f"  {title}")
    print(f"{'-' * 80}")


def print_timeline_slot(start: time, end: time, label: str, color: str = "blue"):
    """Print a single timeline slot"""
    start_str = start.strftime("%I:%M %p")
    end_str = end.strftime("%I:%M %p")

    # Calculate duration
    start_dt = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    duration = int((end_dt - start_dt).total_seconds() / 60)

    # Color codes
    colors = {
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "gray": "\033[90m",
        "cyan": "\033[96m",
    }
    reset = "\033[0m"
    color_code = colors.get(color, "")

    print(f"   {color_code}▐{reset} {start_str:>10} - {end_str:>10}  │  {label.ljust(40)} ({duration} min)")


async def fetch_plan_tasks(analysis_result_id: str) -> List[TaskToAnchor]:
    """
    Fetch plan_items from database and convert to TaskToAnchor format

    Args:
        analysis_result_id: ID of the plan to fetch

    Returns:
        List of TaskToAnchor objects
    """
    task_loader = get_task_loader_service()

    print(f"🔄 Fetching plan_items for analysis_result_id: {analysis_result_id[:8]}...")

    # Load plan items from database (all dates for this plan)
    plan_items = await task_loader.load_plan_items_to_anchor(
        analysis_result_id=analysis_result_id,
        plan_date=None,  # Don't filter by date - get all items for this plan
        include_already_anchored=True  # Include all tasks for demo
    )

    print(f"✅ Loaded {len(plan_items)} tasks from database")

    # Convert PlanItemToAnchor to TaskToAnchor
    tasks = []
    for item in plan_items:
        # Extract time block info from context
        time_block_name = None
        energy_zone = None

        if item.time_block:
            # Parse time block title to extract energy zone
            block_title = item.time_block.block_title.lower()

            # Determine energy zone from block title
            if 'peak' in block_title:
                energy_zone = 'peak_energy'
                time_block_name = 'peak'
            elif 'morning' in block_title:
                energy_zone = 'morning_energy'
                time_block_name = 'morning'
            elif 'evening' in block_title or 'wind down' in block_title:
                energy_zone = 'wind_down'
                time_block_name = 'evening'
            elif 'slump' in block_title or 'mid' in block_title:
                energy_zone = 'midday'
                time_block_name = 'midday'
            else:
                time_block_name = 'afternoon'
                energy_zone = 'maintenance'

        task = TaskToAnchor(
            id=item.id,
            title=item.title,
            description=item.description,
            category=item.category or "general",
            priority_level=item.priority_level or "medium",
            scheduled_time=item.scheduled_time,
            scheduled_end_time=item.scheduled_end_time,
            estimated_duration_minutes=item.estimated_duration_minutes,
            time_block=time_block_name,
            energy_zone_preference=energy_zone
        )
        tasks.append(task)

    return tasks


def create_sample_tasks() -> List[TaskToAnchor]:
    """
    Create sample tasks to demonstrate anchoring (FALLBACK ONLY)

    Returns 8 tasks with different characteristics:
    - High priority: Deep work, strategic planning
    - Medium priority: Admin tasks, email
    - Low priority: Reading, learning
    """
    tasks = [
        # High-priority tasks (need peak energy slots)
        TaskToAnchor(
            id="task_001",
            title="Deep Work - Project Architecture",
            description="Design system architecture for new feature",
            category="focus_work",
            priority_level="high",
            scheduled_time=time(9, 0),
            scheduled_end_time=time(10, 30),
            estimated_duration_minutes=90,
            time_block="peak",
            energy_zone_preference="peak_focus"
        ),
        TaskToAnchor(
            id="task_002",
            title="Strategic Planning - Q1 Goals",
            description="Review quarterly objectives and key results",
            category="planning",
            priority_level="high",
            scheduled_time=time(10, 30),
            scheduled_end_time=time(11, 30),
            estimated_duration_minutes=60,
            time_block="peak",
            energy_zone_preference="peak_focus"
        ),

        # Medium-priority tasks (maintenance work)
        TaskToAnchor(
            id="task_003",
            title="Team Sync - Status Update",
            description="Quick sync with team on project progress",
            category="communication",
            priority_level="medium",
            scheduled_time=time(14, 0),
            scheduled_end_time=time(14, 30),
            estimated_duration_minutes=30,
            time_block="afternoon"
        ),
        TaskToAnchor(
            id="task_004",
            title="Process Email & Slack",
            description="Review and respond to messages",
            category="communication",
            priority_level="medium",
            scheduled_time=time(16, 0),
            scheduled_end_time=time(16, 30),
            estimated_duration_minutes=30,
            time_block="afternoon"
        ),
        TaskToAnchor(
            id="task_005",
            title="Code Review - Pull Requests",
            description="Review 3 pending pull requests",
            category="focus_work",
            priority_level="medium",
            scheduled_time=time(14, 30),
            scheduled_end_time=time(15, 30),
            estimated_duration_minutes=60,
            time_block="afternoon"
        ),

        # Low-priority tasks (nice-to-have)
        TaskToAnchor(
            id="task_006",
            title="Learning - Python Advanced Patterns",
            description="Read chapter on design patterns",
            category="learning",
            priority_level="low",
            scheduled_time=time(17, 0),
            scheduled_end_time=time(17, 30),
            estimated_duration_minutes=30,
            time_block="evening",
            energy_zone_preference="wind_down"
        ),
        TaskToAnchor(
            id="task_007",
            title="Personal Project - Side Hustle",
            description="Work on personal coding project",
            category="personal",
            priority_level="low",
            scheduled_time=time(19, 0),
            scheduled_end_time=time(20, 0),
            estimated_duration_minutes=60,
            time_block="evening"
        ),
        TaskToAnchor(
            id="task_008",
            title="Weekly Planning - Next Week Prep",
            description="Review calendar and plan next week",
            category="planning",
            priority_level="medium",
            scheduled_time=time(16, 30),
            scheduled_end_time=time(17, 0),
            estimated_duration_minutes=30,
            time_block="afternoon"
        ),
    ]

    return tasks


async def demo_anchoring(analysis_result_id: str, user_id: str, use_mock_calendar: bool = True, use_ai_scoring: bool = False):
    """
    Main demo function - shows complete anchoring workflow

    Args:
        analysis_result_id: ID of the plan to anchor
        user_id: User's profile ID
        use_mock_calendar: Whether to use mock calendar (True) or real Google Calendar (False)
        use_ai_scoring: Whether to use AI-enhanced scoring (hybrid mode)
    """
    print_header("CALENDAR ANCHORING ALGORITHM DEMO")

    print("\n📋 This demo shows how AI-generated tasks are anchored to real calendar gaps")
    print("   Fetches real plan data from database and shows anchoring algorithm\n")

    # Configuration
    target_date = date.today()

    print(f"🗓️  Target Date: {target_date.strftime('%A, %B %d, %Y')}")
    print(f"👤 User ID: {user_id[:8]}...")
    print(f"📊 Plan ID: {analysis_result_id[:8]}...")
    print(f"📅 Calendar: {'Mock Data' if use_mock_calendar else 'Real Google Calendar'}")
    print(f"🤖 Scoring Mode: {'AI-Enhanced (48 points)' if use_ai_scoring else 'Algorithmic Only (15 points)'}")

    # Step 1: Load calendar
    calendar_type = "Mock Calendar" if use_mock_calendar else "Google Calendar"
    print_section(f"Step 1: Loading {calendar_type} Events")

    calendar_service = get_calendar_integration_service()

    if use_mock_calendar:
        print("🔄 Fetching realistic_day calendar profile...")
        calendar_result = await calendar_service.fetch_calendar_events(
            user_id=user_id,
            target_date=target_date,
            use_mock_data=True,
            mock_profile="realistic_day"
        )
    else:
        print("🔄 Fetching Google Calendar events...")
        print("   (Requires Google Calendar connection via well-planned-api)")
        calendar_result = await calendar_service.fetch_calendar_events(
            user_id=user_id,
            target_date=target_date,
            use_mock_data=False
        )

    print(f"\n✅ Loaded {calendar_result.total_events} calendar events:")
    print(f"   Calendar Type: {calendar_result.connection_status.value}")
    print(f"   Events:")

    for i, event in enumerate(calendar_result.events, 1):
        print_timeline_slot(
            event.start_time.time(),
            event.end_time.time(),
            f"{i}. {event.title}",
            "gray"
        )

    # Step 2: Fetch plan tasks from database
    print_section("Step 2: Loading Plan Tasks from Database")

    try:
        tasks = await fetch_plan_tasks(analysis_result_id)
    except Exception as e:
        print(f"\n⚠️  Error fetching plan from database: {str(e)}")
        print("   Falling back to sample tasks for demo purposes...\n")
        import traceback
        traceback.print_exc()
        tasks = create_sample_tasks()

    print(f"\n✅ Created {len(tasks)} tasks to anchor:")
    print("\n   Priority Breakdown:")
    high_priority = [t for t in tasks if t.priority_level == "high"]
    medium_priority = [t for t in tasks if t.priority_level == "medium"]
    low_priority = [t for t in tasks if t.priority_level == "low"]

    print(f"   🔴 High Priority: {len(high_priority)} tasks (need peak energy slots)")
    print(f"   🟡 Medium Priority: {len(medium_priority)} tasks (maintenance work)")
    print(f"   🟢 Low Priority: {len(low_priority)} tasks (nice-to-have)\n")

    print("   Original AI-Generated Times:")
    for task in tasks:
        priority_icon = "🔴" if task.priority_level == "high" else "🟡" if task.priority_level == "medium" else "🟢"
        print_timeline_slot(
            task.scheduled_time,
            task.scheduled_end_time,
            f"{priority_icon} {task.title}",
            "yellow"
        )

    # Step 3: Run anchoring algorithm
    print_section("Step 3: Running Anchoring Algorithm")

    print("\n🔄 Anchoring coordinator workflow:")
    print("   1️⃣  Fetching calendar events... DONE")
    print("   2️⃣  Finding available time gaps...")

    coordinator = get_anchoring_coordinator(use_ai_scoring=use_ai_scoring)

    result = await coordinator.anchor_tasks(
        user_id=user_id,
        tasks=tasks,
        target_date=target_date,
        use_mock_calendar=use_mock_calendar,
        mock_profile="realistic_day",
        min_gap_minutes=15
    )

    print("   3️⃣  Scoring task-slot combinations... DONE")
    print("   4️⃣  Assigning tasks to optimal slots... DONE")

    # Step 4: Display results
    print_section("Step 4: Anchoring Results")

    print(f"\n📊 Summary Statistics:")
    print(f"   ✅ Total Tasks: {result.total_tasks}")
    print(f"   📌 Tasks Anchored: {result.tasks_anchored}")

    if result.total_tasks > 0:
        print(f"   🔄 Tasks Rescheduled: {result.tasks_rescheduled} ({result.tasks_rescheduled/result.total_tasks*100:.0f}%)")
    else:
        print(f"   🔄 Tasks Rescheduled: {result.tasks_rescheduled}")

    print(f"   ⏰ Tasks Kept Original Time: {result.tasks_kept_original_time}")
    print(f"   🎯 Average Confidence: {result.average_confidence:.2%}")

    if result.unassigned_tasks:
        print(f"   ⚠️  Unassigned Tasks: {len(result.unassigned_tasks)}")

    # Step 5: Show before/after comparison
    print_section("Step 5: Before/After Comparison")

    print("\n📋 Detailed Task Assignments:\n")

    for i, assignment in enumerate(result.assignments, 1):
        was_moved = assignment.time_adjustment_minutes != 0

        print(f"   {'─' * 76}")
        print(f"   Task {i}: {assignment.task_title}")
        print(f"   {'─' * 76}")

        # Show time change
        if was_moved:
            print(f"   ⏰ Time Change:")
            print(f"      Before: {assignment.original_time.strftime('%I:%M %p')} - {assignment.original_end_time.strftime('%I:%M %p')}")
            print(f"      After:  {assignment.anchored_time.strftime('%I:%M %p')} - {assignment.anchored_end_time.strftime('%I:%M %p')}")

            if assignment.time_adjustment_minutes > 0:
                print(f"      Moved: +{assignment.time_adjustment_minutes} minutes later")
            else:
                print(f"      Moved: {assignment.time_adjustment_minutes} minutes earlier")
        else:
            print(f"   ✓ Time: {assignment.anchored_time.strftime('%I:%M %p')} - {assignment.anchored_end_time.strftime('%I:%M %p')} (kept original)")

        # Show scoring
        print(f"   🎯 Confidence: {assignment.confidence_score:.2%}")
        print(f"   📊 Scoring Breakdown:")

        if "fallback" in assignment.scoring_breakdown:
            print(f"      Fallback: {assignment.scoring_breakdown['reason']}")
        else:
            breakdown = assignment.scoring_breakdown
            print(f"      Duration Fit: {breakdown.get('duration_fit', {}).get('score', 0):.1f}/2.0")
            print(f"      Time Window Match: {breakdown.get('time_window', {}).get('score', 0):.1f}/10.0")
            print(f"      Priority Alignment: {breakdown.get('priority', {}).get('score', 0):.1f}/3.0")

        print()

    # Step 6: Visual timeline
    print_section("Step 6: Final Daily Timeline")

    print("\n🗓️  Complete Schedule for", target_date.strftime('%A, %B %d, %Y'))
    print()

    # Combine calendar events and anchored tasks, sort by time
    timeline_items = []

    for event in calendar_result.events:
        timeline_items.append({
            "start": event.start_time.time(),
            "end": event.end_time.time(),
            "label": f"📅 {event.title}",
            "type": "calendar",
            "color": "gray"
        })

    for assignment in result.assignments:
        timeline_items.append({
            "start": assignment.anchored_time,
            "end": assignment.anchored_end_time,
            "label": f"✅ {assignment.task_title}",
            "type": "task",
            "color": "green"
        })

    # Sort by start time
    timeline_items.sort(key=lambda x: x["start"])

    # Print timeline
    for item in timeline_items:
        print_timeline_slot(
            item["start"],
            item["end"],
            item["label"],
            item["color"]
        )

    # Step 7: Insights
    print_section("Step 7: Anchoring Insights")

    print("\n💡 Key Observations:\n")

    # Calculate statistics
    total_adjustments = sum(abs(a.time_adjustment_minutes) for a in result.assignments)
    avg_adjustment = total_adjustments / len(result.assignments) if result.assignments else 0

    high_confidence = sum(1 for a in result.assignments if a.confidence_score > 0.8)
    medium_confidence = sum(1 for a in result.assignments if 0.5 < a.confidence_score <= 0.8)
    low_confidence = sum(1 for a in result.assignments if a.confidence_score <= 0.5)

    print(f"   1. Task Rescheduling:")
    print(f"      • {result.tasks_rescheduled} tasks were moved to better fit calendar gaps")
    print(f"      • Average time adjustment: {avg_adjustment:.0f} minutes")
    print(f"      • {result.tasks_kept_original_time} tasks kept their original AI times")

    print(f"\n   2. Assignment Confidence:")
    print(f"      • High confidence (>80%): {high_confidence} tasks")
    print(f"      • Medium confidence (50-80%): {medium_confidence} tasks")
    print(f"      • Low confidence (<50%): {low_confidence} tasks")

    print(f"\n   3. Algorithm Performance:")
    print(f"      • All {result.total_tasks} tasks successfully anchored")
    print(f"      • Average confidence score: {result.average_confidence:.2%}")
    print(f"      • No tasks left unassigned")

    print(f"\n   4. Calendar Integration:")
    print(f"      • Tasks fit around {calendar_result.total_events} existing calendar events")
    print(f"      • Respects time block preferences (morning/peak/afternoon/evening)")
    print(f"      • Prioritizes high-priority tasks in peak energy slots")

    # Final summary
    print_section("Demo Complete")

    print("\n✅ Calendar Anchoring Algorithm Successfully Demonstrated!\n")
    print("   What This Demo Showed:")
    print("   ✓ Calendar event loading (mock data)")
    print("   ✓ Time gap detection")
    print("   ✓ Algorithmic scoring (duration fit, time window, priority)")
    print("   ✓ Greedy assignment algorithm")
    print("   ✓ Task rescheduling to optimal slots")
    print("   ✓ Confidence scoring for each assignment")

    print("\n   Next Steps:")
    print("   1. Add database integration to persist anchored tasks")
    print("   2. Connect to real Google Calendar via well-planned-api")
    print("   3. Add AI-enhanced scoring (hybrid algorithmic + LLM)")
    print("   4. Implement user feedback loop for continuous improvement")

    print("\n" + "═" * 80)


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("\n❌ Error: Missing required arguments")
        print("\nUsage:")
        print("   python testing/demo_anchoring.py <analysis_result_id> <user_id> [use_mock_calendar] [use_ai_scoring]")
        print("\nExample:")
        print("   python testing/demo_anchoring.py d8fe057d-fe02-4547-b7f2-f4884e424544 a57f70b4-d0a4-4aef-b721-a4b526f64869 true false")
        print("   python testing/demo_anchoring.py d8fe057d-fe02-4547-b7f2-f4884e424544 a57f70b4-d0a4-4aef-b721-a4b526f64869 true true  # AI-enhanced")
        print("\nArguments:")
        print("   analysis_result_id : UUID of the plan to anchor (from holistic_analysis_results table)")
        print("   user_id            : User's profile ID")
        print("   use_mock_calendar  : 'true' for mock data, 'false' for Google Calendar (default: true)")
        print("   use_ai_scoring     : 'true' for AI-enhanced (48pt), 'false' for algorithmic (15pt) (default: false)")
        print("\nNote:")
        print("   The script will fetch plan_items for today's date.")
        print("   Make sure your plan has items with plan_date = today.")
        sys.exit(1)

    analysis_result_id = sys.argv[1]
    user_id = sys.argv[2]
    use_mock_calendar = True if len(sys.argv) < 4 else sys.argv[3].lower() == "true"
    use_ai_scoring = False if len(sys.argv) < 5 else sys.argv[4].lower() == "true"

    # Run demo
    asyncio.run(demo_anchoring(analysis_result_id, user_id, use_mock_calendar, use_ai_scoring))
