"""
AI Model Speed Benchmark - Compare Different Models

Tests multiple AI models for batch scoring speed and quality:
1. gpt-4o-mini (current)
2. gpt-4o (OpenAI latest)
3. gpt-3.5-turbo (OpenAI fastest)
4. gemini-1.5-flash (Google fastest)

Usage:
    python testing/benchmark_ai_models.py
"""

import asyncio
import sys
import os
from datetime import time, datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from services.anchoring.ai_scorer_service import AIScorerService
from services.anchoring.basic_scorer_service import TaskToAnchor
from services.anchoring.calendar_gap_finder import AvailableSlot, GapType, GapSize


def create_test_data():
    """Create test tasks and slots"""
    tasks = [
        TaskToAnchor(
            id="task_1",
            title="Morning Yoga",
            description="15-minute gentle yoga session",
            category="movement",
            priority_level="medium",
            scheduled_time=time(9, 0),
            scheduled_end_time=time(9, 15),
            estimated_duration_minutes=15,
            time_block="Morning Block",
            energy_zone_preference="peak"
        ),
        TaskToAnchor(
            id="task_2",
            title="Drink Water",
            description="Hydration check",
            category="hydration",
            priority_level="medium",
            scheduled_time=time(9, 0),
            scheduled_end_time=time(9, 5),
            estimated_duration_minutes=5,
            time_block="Morning Block",
            energy_zone_preference="peak"
        ),
        TaskToAnchor(
            id="task_3",
            title="Healthy Breakfast",
            description="Nutritious morning meal",
            category="nutrition",
            priority_level="high",
            scheduled_time=time(9, 0),
            scheduled_end_time=time(9, 20),
            estimated_duration_minutes=20,
            time_block="Morning Block",
            energy_zone_preference="peak"
        ),
        TaskToAnchor(
            id="task_4",
            title="Morning Walk",
            description="30-minute outdoor walk",
            category="movement",
            priority_level="medium",
            scheduled_time=time(9, 0),
            scheduled_end_time=time(9, 30),
            estimated_duration_minutes=30,
            time_block="Morning Block",
            energy_zone_preference="peak"
        ),
    ]

    slots = [
        AvailableSlot(
            slot_id="slot_1",
            start_time=time(6, 0),
            end_time=time(6, 30),
            duration_minutes=30,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.MEDIUM,
            before_event_title=None,
            after_event_title=None
        ),
        AvailableSlot(
            slot_id="slot_2",
            start_time=time(7, 0),
            end_time=time(7, 45),
            duration_minutes=45,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.MEDIUM,
            before_event_title=None,
            after_event_title=None
        ),
        AvailableSlot(
            slot_id="slot_3",
            start_time=time(8, 0),
            end_time=time(9, 0),
            duration_minutes=60,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.LARGE,
            before_event_title=None,
            after_event_title=None
        ),
        AvailableSlot(
            slot_id="slot_4",
            start_time=time(10, 0),
            end_time=time(10, 30),
            duration_minutes=30,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.MEDIUM,
            before_event_title=None,
            after_event_title=None
        ),
        AvailableSlot(
            slot_id="slot_5",
            start_time=time(12, 0),
            end_time=time(12, 45),
            duration_minutes=45,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.MEDIUM,
            before_event_title=None,
            after_event_title=None
        ),
        AvailableSlot(
            slot_id="slot_6",
            start_time=time(14, 0),
            end_time=time(15, 0),
            duration_minutes=60,
            gap_type=GapType.BETWEEN_EVENTS,
            gap_size=GapSize.LARGE,
            before_event_title=None,
            after_event_title=None
        ),
    ]

    # Generate all valid combinations
    combinations = []
    for task in tasks:
        for slot in slots:
            if task.estimated_duration_minutes <= slot.duration_minutes:
                combinations.append((task, slot))

    return combinations


async def benchmark_openai_model(model_name: str, combinations: List) -> Dict[str, Any]:
    """Benchmark an OpenAI model"""
    print(f"\n{'='*80}")
    print(f" Testing: {model_name}")
    print(f"{'='*80}")

    try:
        # Create scorer with specific model
        scorer = AIScorerService(model=model_name, temperature=0.3)

        # Time the batch scoring
        start = datetime.now()
        scores = await scorer.score_batch(combinations)
        end = datetime.now()

        elapsed = (end - start).total_seconds()

        # Calculate quality metrics
        avg_score = sum(s.total_score for s in scores) / len(scores) if scores else 0

        result = {
            "model": model_name,
            "success": True,
            "time_seconds": elapsed,
            "combinations_scored": len(scores),
            "avg_score": avg_score,
            "scores_per_second": len(scores) / elapsed if elapsed > 0 else 0,
            "error": None
        }

        print(f"\n[RESULT] {model_name}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Scores: {len(scores)}")
        print(f"   Avg Quality: {avg_score:.1f}/33")
        print(f"   Speed: {result['scores_per_second']:.2f} scores/sec")

        return result

    except Exception as e:
        print(f"\n[ERROR] {model_name} failed: {str(e)}")
        return {
            "model": model_name,
            "success": False,
            "time_seconds": None,
            "combinations_scored": 0,
            "avg_score": 0,
            "scores_per_second": 0,
            "error": str(e)
        }


async def benchmark_gemini_model(model_name: str, combinations: List) -> Dict[str, Any]:
    """Benchmark Google Gemini model"""
    print(f"\n{'='*80}")
    print(f" Testing: {model_name}")
    print(f"{'='*80}")

    try:
        import google.generativeai as genai
        import json

        # Configure Gemini
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(model_name)

        # Build prompt (similar to OpenAI)
        prompt = f"""Score {len(combinations)} task-slot combinations and return results as a JSON array.

For EACH combination, score these aspects:
1. Task Context (0-12 points): Does the task match this time of day?
2. Dependency & Flow (0-11 points): Does this create good momentum?
3. Energy & Focus (0-10 points): Does energy level match demands?

Combinations:
"""

        for idx, (task, slot) in enumerate(combinations, 1):
            prompt += f"""
{idx}. Task: {task.title} ({task.estimated_duration_minutes}min)
   Slot: {slot.start_time.strftime('%I:%M %p')}-{slot.end_time.strftime('%I:%M %p')}
   task_id: "{task.id}", slot_id: "{slot.slot_id}"
"""

        prompt += f"""
Return ONLY valid JSON with this structure:
{{
  "scores": [
    {{
      "task_id": "<task_id>",
      "slot_id": "<slot_id>",
      "total_score": <0-33>,
      "task_context_score": <0-12>,
      "dependency_score": <0-11>,
      "energy_score": <0-10>,
      "reasoning": "<brief explanation>"
    }},
    ... (repeat for all {len(combinations)} combinations)
  ]
}}
"""

        # Time the API call
        start = datetime.now()
        response = model.generate_content(prompt)
        end = datetime.now()

        elapsed = (end - start).total_seconds()

        # Parse response
        response_text = response.text
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result_json = json.loads(response_text.strip())
        scores_data = result_json.get("scores", [])

        # Calculate metrics
        avg_score = sum(s.get("total_score", 0) for s in scores_data) / len(scores_data) if scores_data else 0

        result = {
            "model": model_name,
            "success": True,
            "time_seconds": elapsed,
            "combinations_scored": len(scores_data),
            "avg_score": avg_score,
            "scores_per_second": len(scores_data) / elapsed if elapsed > 0 else 0,
            "error": None
        }

        print(f"\n[RESULT] {model_name}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Scores: {len(scores_data)}")
        print(f"   Avg Quality: {avg_score:.1f}/33")
        print(f"   Speed: {result['scores_per_second']:.2f} scores/sec")

        return result

    except Exception as e:
        print(f"\n[ERROR] {model_name} failed: {str(e)}")
        return {
            "model": model_name,
            "success": False,
            "time_seconds": None,
            "combinations_scored": 0,
            "avg_score": 0,
            "scores_per_second": 0,
            "error": str(e)
        }


async def run_benchmark():
    """Run complete benchmark comparing all models"""

    print("\n" + "="*80)
    print(" AI MODEL SPEED BENCHMARK")
    print("="*80)
    print("\n   Comparing different AI models for batch scoring speed")
    print("   Testing with 24 task-slot combinations")
    print("\n   Models to test:")
    print("   1. gpt-4o-mini (current)")
    print("   2. gpt-4o (OpenAI latest)")
    print("   3. gpt-3.5-turbo (OpenAI fastest)")
    print("   4. gemini-1.5-flash (Google fastest)")

    # Create test data
    print(f"\n[SETUP] Creating test data...")
    combinations = create_test_data()
    print(f"   Created {len(combinations)} task-slot combinations")

    # Run benchmarks
    results = []

    # Test OpenAI models
    openai_models = [
        "gpt-4o-mini",      # Current model
        "gpt-4o",           # Latest OpenAI
        "gpt-3.5-turbo",    # Fastest OpenAI
    ]

    for model in openai_models:
        result = await benchmark_openai_model(model, combinations)
        results.append(result)
        await asyncio.sleep(2)  # Brief pause between tests

    # Test Gemini if API key available
    if os.getenv('GEMINI_API_KEY'):
        result = await benchmark_gemini_model("gemini-1.5-flash", combinations)
        results.append(result)
    else:
        print(f"\n[SKIP] Gemini test skipped (GEMINI_API_KEY not set)")
        print("   To test Gemini, set GEMINI_API_KEY in .env file")

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

    print(f"\n{'Model':<20} {'Time':<12} {'Speed':<15} {'Quality':<12} {'Status':<10}")
    print("-" * 80)

    for result in results:
        if result["success"]:
            print(f"{result['model']:<20} "
                  f"{result['time_seconds']:.2f}s{'':<7} "
                  f"{result['scores_per_second']:.2f} scores/s{'':<2} "
                  f"{result['avg_score']:.1f}/33{'':<5} "
                  f"{'OK':<10}")
        else:
            print(f"{result['model']:<20} "
                  f"{'FAILED':<12} "
                  f"{'-':<15} "
                  f"{'-':<12} "
                  f"{'ERROR':<10}")

    # Winner analysis
    fastest = successful_results[0]
    print(f"\n[WINNER] Fastest Model: {fastest['model']}")
    print(f"   Time: {fastest['time_seconds']:.2f}s")
    print(f"   Speed: {fastest['scores_per_second']:.2f} scores/second")
    print(f"   Quality: {fastest['avg_score']:.1f}/33")

    # Speed improvements vs current
    current_result = next((r for r in results if r["model"] == "gpt-4o-mini"), None)
    if current_result and current_result["success"]:
        current_time = current_result["time_seconds"]
        for result in successful_results[1:]:
            speedup = current_time / result["time_seconds"]
            if speedup > 1:
                print(f"\n[IMPROVEMENT] {result['model']} is {speedup:.1f}x FASTER than current")
            elif speedup < 1:
                print(f"\n[SLOWER] {result['model']} is {1/speedup:.1f}x slower than current")

    # Quality vs speed trade-off
    print(f"\n[ANALYSIS] Quality vs Speed Trade-off:")
    best_quality = max(r["avg_score"] for r in successful_results)
    for result in successful_results:
        quality_pct = (result["avg_score"] / best_quality * 100) if best_quality > 0 else 0
        print(f"   {result['model']:<20} Quality: {quality_pct:.0f}%  Speed: {result['time_seconds']:.1f}s")

    # Recommendations
    print(f"\n[RECOMMENDATION]")
    if fastest["model"] != "gpt-4o-mini":
        quality_loss = ((current_result["avg_score"] - fastest["avg_score"]) / current_result["avg_score"] * 100) if current_result else 0
        time_saved = current_result["time_seconds"] - fastest["time_seconds"] if current_result else 0

        if quality_loss < 10:
            print(f"   Switch to {fastest['model']} for {speedup:.1f}x speed improvement")
            print(f"   Saves {time_saved:.1f} seconds with minimal quality loss ({quality_loss:.1f}%)")
        else:
            print(f"   {fastest['model']} is faster but loses {quality_loss:.0f}% quality")
            print(f"   Consider if speed is more important than accuracy")
    else:
        print(f"   Current model (gpt-4o-mini) is already optimal")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    print("\n[BENCHMARK] Starting AI model speed comparison...")
    asyncio.run(run_benchmark())
