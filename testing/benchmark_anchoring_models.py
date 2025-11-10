"""
AI Anchoring Model Benchmark - Compare OpenAI vs Gemini

Tests both OpenAI GPT-4o and Google Gemini Flash for task anchoring:
- Speed (time to complete)
- Quality (number of tasks anchored, confidence scores)
- Cost estimation

Usage:
    python testing/benchmark_anchoring_models.py <analysis_result_id> <user_id>
"""

import asyncio
import sys
import os
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from services.anchoring import (
    AIAnchoringAgent,
    TaskToAnchor,
    AvailableSlot,
    CalendarEvent,
    GapType,
    GapSize,
)
from services.anchoring.task_loader_service import get_task_loader_service


async def fetch_real_tasks(analysis_result_id: str) -> List[TaskToAnchor]:
    """Fetch real tasks from database"""
    task_loader = get_task_loader_service()

    print(f"   Fetching tasks for plan {analysis_result_id[:8]}...")

    plan_items = await task_loader.load_plan_items_to_anchor(
        analysis_result_id=analysis_result_id,
        plan_date=None,
        include_already_anchored=True
    )

    tasks = []
    for item in plan_items:
        # Handle None values
        scheduled_time = item.scheduled_time if item.scheduled_time else time(8, 0)

        if item.scheduled_end_time:
            scheduled_end_time = item.scheduled_end_time
        else:
            duration = item.estimated_duration_minutes or 15
            total_minutes = scheduled_time.hour * 60 + scheduled_time.minute + duration
            end_hour = (total_minutes // 60) % 24
            end_minute = total_minutes % 60
            scheduled_end_time = time(end_hour, end_minute)

        task = TaskToAnchor(
            id=item.id,
            title=item.title,
            description=item.description,
            category=item.category or "general",
            priority_level=item.priority_level or "medium",
            scheduled_time=scheduled_time,
            scheduled_end_time=scheduled_end_time,
            estimated_duration_minutes=item.estimated_duration_minutes or 15,
            time_block=None,
            energy_zone_preference=None
        )
        tasks.append(task)

    print(f"   Loaded {len(tasks)} tasks from database")
    return tasks


def create_mock_calendar() -> List[CalendarEvent]:
    """Create mock calendar events"""
    target_date = date.today()

    events = [
        CalendarEvent(
            id="event_1",
            title="Morning Exercise",
            start_time=datetime.combine(target_date, time(6, 0)),
            end_time=datetime.combine(target_date, time(7, 0))
        ),
        CalendarEvent(
            id="event_2",
            title="Team Standup",
            start_time=datetime.combine(target_date, time(9, 0)),
            end_time=datetime.combine(target_date, time(10, 0))
        ),
        CalendarEvent(
            id="event_3",
            title="Project Planning",
            start_time=datetime.combine(target_date, time(11, 0)),
            end_time=datetime.combine(target_date, time(12, 0))
        ),
        CalendarEvent(
            id="event_4",
            title="Lunch Break",
            start_time=datetime.combine(target_date, time(13, 0)),
            end_time=datetime.combine(target_date, time(13, 30))
        ),
        CalendarEvent(
            id="event_5",
            title="Client Meeting",
            start_time=datetime.combine(target_date, time(15, 0)),
            end_time=datetime.combine(target_date, time(16, 0))
        ),
        CalendarEvent(
            id="event_6",
            title="Dinner",
            start_time=datetime.combine(target_date, time(18, 0)),
            end_time=datetime.combine(target_date, time(18, 45))
        ),
    ]

    return events


def create_mock_slots() -> List[AvailableSlot]:
    """Create mock available slots"""
    slots = [
        AvailableSlot(
            slot_id="slot_1",
            start_time=time(7, 0),
            end_time=time(9, 0),
            duration_minutes=120,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.LARGE,
            before_event_title="Morning Exercise",
            after_event_title="Team Standup"
        ),
        AvailableSlot(
            slot_id="slot_2",
            start_time=time(10, 0),
            end_time=time(11, 0),
            duration_minutes=60,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.MEDIUM,
            before_event_title="Team Standup",
            after_event_title="Project Planning"
        ),
        AvailableSlot(
            slot_id="slot_3",
            start_time=time(12, 0),
            end_time=time(13, 0),
            duration_minutes=60,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.MEDIUM,
            before_event_title="Project Planning",
            after_event_title="Lunch Break"
        ),
        AvailableSlot(
            slot_id="slot_4",
            start_time=time(13, 30),
            end_time=time(15, 0),
            duration_minutes=90,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.LARGE,
            before_event_title="Lunch Break",
            after_event_title="Client Meeting"
        ),
        AvailableSlot(
            slot_id="slot_5",
            start_time=time(16, 0),
            end_time=time(18, 0),
            duration_minutes=120,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.LARGE,
            before_event_title="Client Meeting",
            after_event_title="Dinner"
        ),
    ]

    return slots


async def benchmark_model(
    provider: str,
    model: str,
    tasks: List[TaskToAnchor],
    slots: List[AvailableSlot],
    calendar_events: List[CalendarEvent]
) -> Dict[str, Any]:
    """Benchmark a specific model"""

    print(f"\n{'='*80}")
    print(f" Testing: {provider.upper()} - {model}")
    print(f"{'='*80}")

    try:
        # Create agent with specific provider/model
        agent = AIAnchoringAgent(provider=provider, model=model)

        # Time the anchoring
        start = datetime.now()
        result = await agent.anchor_tasks(
            tasks=tasks,
            slots=slots,
            calendar_events=calendar_events,
            user_profile=None,
            target_date=date.today()
        )
        end = datetime.now()

        elapsed = (end - start).total_seconds()

        # Calculate quality metrics
        anchored_pct = (result.tasks_anchored / result.total_tasks * 100) if result.total_tasks > 0 else 0
        rescheduled_pct = (result.tasks_rescheduled / result.total_tasks * 100) if result.total_tasks > 0 else 0

        benchmark_result = {
            "provider": provider,
            "model": model,
            "success": True,
            "time_seconds": elapsed,
            "total_tasks": result.total_tasks,
            "tasks_anchored": result.tasks_anchored,
            "tasks_rescheduled": result.tasks_rescheduled,
            "tasks_kept_original": result.tasks_kept_original,
            "average_confidence": result.average_confidence,
            "anchored_percentage": anchored_pct,
            "rescheduled_percentage": rescheduled_pct,
            "unassigned_count": len(result.unassigned_tasks),
            "error": None
        }

        print(f"\n[RESULT] {provider.upper()} - {model}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Tasks Anchored: {result.tasks_anchored}/{result.total_tasks} ({anchored_pct:.1f}%)")
        print(f"   Tasks Rescheduled: {result.tasks_rescheduled} ({rescheduled_pct:.1f}%)")
        print(f"   Average Confidence: {result.average_confidence:.2%}")
        print(f"   Unassigned: {len(result.unassigned_tasks)}")

        return benchmark_result

    except Exception as e:
        print(f"\n[ERROR] {provider.upper()} - {model} failed: {str(e)}")
        return {
            "provider": provider,
            "model": model,
            "success": False,
            "time_seconds": None,
            "error": str(e)
        }


async def run_benchmark(analysis_result_id: str, user_id: str):
    """Run complete benchmark comparing all models"""

    print("\n" + "="*80)
    print(" AI ANCHORING MODEL BENCHMARK - OpenAI vs Gemini")
    print("="*80)
    print("\n   Comparing different AI models for task anchoring")
    print(f"   User ID: {user_id[:8]}...")
    print(f"   Plan ID: {analysis_result_id[:8]}...")

    # Load test data
    print(f"\n[SETUP] Loading test data...")

    try:
        tasks = await fetch_real_tasks(analysis_result_id)
    except Exception as e:
        print(f"   Warning: Could not load real tasks ({str(e)}), using mock data")
        tasks = []

    if not tasks or len(tasks) == 0:
        print("   No tasks found - cannot run benchmark")
        return

    calendar_events = create_mock_calendar()
    slots = create_mock_slots()

    print(f"   Created {len(calendar_events)} calendar events")
    print(f"   Created {len(slots)} available slots")
    print(f"   Testing with {len(tasks)} real tasks")

    # Models to test
    models_to_test = []

    # OpenAI models (if key available)
    if os.getenv('OPENAI_API_KEY'):
        models_to_test.extend([
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
        ])
    else:
        print("\n[SKIP] OpenAI tests skipped (OPENAI_API_KEY not set)")

    # Gemini models (if key available)
    if os.getenv('GEMINI_API_KEY'):
        models_to_test.extend([
            ("gemini", "gemini-2.0-flash-exp"),
            ("gemini", "gemini-2.0-flash-thinking-exp-01-21"),
        ])
    else:
        print("\n[SKIP] Gemini tests skipped (GEMINI_API_KEY not set)")

    if not models_to_test:
        print("\n[ERROR] No API keys configured. Set OPENAI_API_KEY or GEMINI_API_KEY in .env")
        return

    # Run benchmarks
    results = []
    for provider, model in models_to_test:
        result = await benchmark_model(provider, model, tasks, slots, calendar_events)
        results.append(result)
        await asyncio.sleep(2)  # Brief pause between tests

    # Summary comparison
    print(f"\n{'='*80}")
    print(" BENCHMARK SUMMARY")
    print(f"{'='*80}")

    # Sort by speed
    successful_results = [r for r in results if r["success"]]
    successful_results.sort(key=lambda x: x["time_seconds"] if x["time_seconds"] else float('inf'))

    if not successful_results:
        print("\n[ERROR] No models completed successfully")
        return

    print(f"\n{'Provider':<10} {'Model':<35} {'Time':<10} {'Anchored':<12} {'Confidence':<12} {'Status':<10}")
    print("-" * 90)

    for result in results:
        if result["success"]:
            print(f"{result['provider']:<10} "
                  f"{result['model']:<35} "
                  f"{result['time_seconds']:.2f}s{'':<5} "
                  f"{result['tasks_anchored']}/{result['total_tasks']}{'':<4} "
                  f"{result['average_confidence']:.1%}{'':<6} "
                  f"{'OK':<10}")
        else:
            print(f"{result['provider']:<10} "
                  f"{result['model']:<35} "
                  f"{'FAILED':<10} "
                  f"{'-':<12} "
                  f"{'-':<12} "
                  f"{'ERROR':<10}")

    # Winner analysis
    fastest = successful_results[0]
    print(f"\n[WINNER] Fastest Model: {fastest['provider'].upper()} - {fastest['model']}")
    print(f"   Time: {fastest['time_seconds']:.2f}s")
    print(f"   Anchored: {fastest['tasks_anchored']}/{fastest['total_tasks']} ({fastest['anchored_percentage']:.1f}%)")
    print(f"   Confidence: {fastest['average_confidence']:.1%}")

    # Speed comparison
    if len(successful_results) > 1:
        slowest = successful_results[-1]
        speedup = slowest["time_seconds"] / fastest["time_seconds"]
        print(f"\n[IMPROVEMENT] {fastest['provider'].upper()}-{fastest['model']} is {speedup:.1f}x faster than {slowest['provider'].upper()}-{slowest['model']}")
        time_saved = slowest["time_seconds"] - fastest["time_seconds"]
        print(f"   Saves {time_saved:.1f} seconds per request")

    # Cost estimation
    print(f"\n[COST ESTIMATION] (per 1000 requests)")
    for result in successful_results:
        if result["provider"] == "openai":
            if "gpt-4o" in result["model"] and "mini" not in result["model"]:
                cost = 10.0  # ~$0.01 per request
            else:  # gpt-4o-mini
                cost = 2.0  # ~$0.002 per request
        else:  # gemini
            cost = 5.0  # ~$0.005 per request (estimated)

        print(f"   {result['provider'].upper()}-{result['model']}: ${cost:.2f}")

    # Quality vs Speed trade-off
    print(f"\n[ANALYSIS] Quality vs Speed Trade-off:")
    best_confidence = max(r["average_confidence"] for r in successful_results)
    for result in successful_results:
        quality_pct = (result["average_confidence"] / best_confidence * 100) if best_confidence > 0 else 0
        print(f"   {result['provider'].upper()}-{result['model']:<30} "
              f"Quality: {quality_pct:.0f}%  "
              f"Speed: {result['time_seconds']:.1f}s")

    # Recommendations
    print(f"\n[RECOMMENDATION]")
    gemini_results = [r for r in successful_results if r["provider"] == "gemini"]
    openai_results = [r for r in successful_results if r["provider"] == "openai"]

    if gemini_results and openai_results:
        gemini_fastest = min(gemini_results, key=lambda x: x["time_seconds"])
        openai_fastest = min(openai_results, key=lambda x: x["time_seconds"])

        if gemini_fastest["time_seconds"] < openai_fastest["time_seconds"]:
            speedup = openai_fastest["time_seconds"] / gemini_fastest["time_seconds"]
            quality_diff = abs(gemini_fastest["average_confidence"] - openai_fastest["average_confidence"])

            print(f"   ✅ Use Gemini ({gemini_fastest['model']}) for {speedup:.1f}x speed improvement")
            print(f"   Quality difference: {quality_diff:.1%}")
            if speedup > 2:
                print(f"   💰 Gemini is also ~2-4x cheaper than OpenAI")
        else:
            print(f"   OpenAI is faster in this test, but check cost-benefit")
    elif gemini_results:
        print(f"   ✅ Use Gemini ({gemini_results[0]['model']}) - only provider tested")
    elif openai_results:
        print(f"   ✅ Use OpenAI ({openai_results[0]['model']}) - only provider tested")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nUsage: python testing/benchmark_anchoring_models.py <analysis_result_id> <user_id>")
        print("\nExample:")
        print("   python testing/benchmark_anchoring_models.py f88566ff-18d1-43f3-84d4-eef98d6c5bed a57f70b4-d0a4-4aef-b721-a4b526f64869")
        sys.exit(1)

    analysis_result_id = sys.argv[1]
    user_id = sys.argv[2]

    asyncio.run(run_benchmark(analysis_result_id, user_id))
