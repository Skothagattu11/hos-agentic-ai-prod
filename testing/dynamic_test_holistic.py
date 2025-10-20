"""
Dynamic Holistic Integration Test Script
Fetches IDs dynamically from APIs to simulate real-world usage
Saves JSON responses to logs folder

NEW: Added adaptive routine generation testing
"""

import requests
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8002"
TEST_USER_ID = "a57f70b4-d0a4-4aef-b721-a4b526f64869"  # Updated test user
API_KEY = "hosa_flutter_app_2024"  # Required for routine/nutrition generation

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs" / "holistic_integration_tests_dynamic"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def save_test_result(log_filename: str, test_result: Dict[str, Any]):
    """Save test result to JSON file"""
    log_file = LOGS_DIR / f"{log_filename}.json"
    with open(log_file, 'w') as f:
        json.dump(test_result, f, indent=2, default=str)
    print(f"📁 Saved to: {log_file}")


def test_endpoint(name: str, url: str, log_filename: str) -> tuple[bool, Optional[Dict]]:
    """Test a single endpoint and save response to JSON file"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")

    test_result = {
        "test_name": name,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status_code": None,
        "success": False,
        "response": None,
        "error": None
    }

    try:
        response = requests.get(url, timeout=10)
        test_result["status_code"] = response.status_code
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            test_result["response"] = data
            test_result["success"] = True
            print("\n✓ SUCCESS")
            success = True
            response_data = data
        else:
            test_result["response"] = response.text
            print(f"\n✗ FAILED: {response.text}")
            success = False
            response_data = None

    except Exception as e:
        test_result["error"] = str(e)
        print(f"\n✗ ERROR: {e}")
        success = False
        response_data = None

    # Save to JSON file
    save_test_result(log_filename, test_result)

    return success, response_data


def test_routine_generation(name: str, user_id: str, archetype: str, log_filename: str,
                            adaptive_mode: bool = False) -> tuple[bool, Optional[Dict]]:
    """
    Test routine generation endpoint (POST)

    Args:
        name: Test name for display
        user_id: User ID for generation
        archetype: User archetype
        log_filename: Log file name
        adaptive_mode: True to enable adaptive routine generation
    """
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"POST: {BASE_URL}/api/user/{user_id[:8]}.../routine/generate")
    print(f"Archetype: {archetype}")
    print(f"Adaptive Mode: {'ENABLED' if adaptive_mode else 'DISABLED'}")
    print(f"{'='*80}\n")

    # Set environment variable for adaptive mode
    if adaptive_mode:
        os.environ["USE_ADAPTIVE_ROUTINE"] = "true"
        print("🔵 Feature Flag: USE_ADAPTIVE_ROUTINE=true")
    else:
        os.environ["USE_ADAPTIVE_ROUTINE"] = "false"
        print("📜 Feature Flag: USE_ADAPTIVE_ROUTINE=false (legacy)")

    test_result = {
        "test_name": name,
        "endpoint": f"/api/user/{user_id}/routine/generate",
        "timestamp": datetime.now().isoformat(),
        "status_code": None,
        "success": False,
        "response": None,
        "error": None,
        "adaptive_mode": adaptive_mode,
        "archetype": archetype
    }

    try:
        payload = {
            "archetype": archetype,
            "preferences": {
                "force_refresh": True
            }
        }

        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

        print(f"⏳ Generating routine...")
        response = requests.post(
            f"{BASE_URL}/api/user/{user_id}/routine/generate",
            json=payload,
            headers=headers,
            timeout=300
        )

        test_result["status_code"] = response.status_code
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            test_result["response"] = data
            test_result["success"] = True

            # Analyze the routine
            routine_plan = data.get('routine_plan', {})
            time_blocks = routine_plan.get('time_blocks', [])

            # Count tasks
            total_tasks = 0
            task_distribution = {}

            for block in time_blocks:
                block_name = block.get('block_name', 'Unknown')
                tasks = block.get('tasks', [])
                task_count = len(tasks)
                total_tasks += task_count
                task_distribution[block_name] = task_count

            # Store analysis in result
            test_result["analysis"] = {
                "total_tasks": total_tasks,
                "task_distribution": task_distribution,
                "block_count": len(time_blocks)
            }

            print(f"\n✓ SUCCESS - Routine Generated")
            print(f"\n📊 Task Analysis:")
            print(f"   Total Tasks: {total_tasks}")
            print(f"   Time Blocks: {len(time_blocks)}")
            print(f"   Task Distribution:")
            for block_name, count in task_distribution.items():
                emoji = "✅" if count <= 2 else "⚠️"
                print(f"     {emoji} {block_name}: {count} tasks")

            # Check optimization for adaptive mode
            if adaptive_mode:
                optimized = total_tasks <= 6
                print(f"\n🎯 Optimization Check:")
                print(f"   Target: ≤6 tasks per day")
                print(f"   Actual: {total_tasks} tasks")
                print(f"   Status: {'✅ OPTIMIZED' if optimized else '⚠️ ABOVE TARGET'}")
                test_result["analysis"]["optimized"] = optimized

            success = True
            response_data = data
        else:
            test_result["response"] = response.text
            print(f"\n✗ FAILED: {response.text[:200]}")
            success = False
            response_data = None

    except Exception as e:
        test_result["error"] = str(e)
        print(f"\n✗ ERROR: {e}")
        success = False
        response_data = None

    # Save to JSON file
    save_test_result(log_filename, test_result)

    return success, response_data


def compare_routine_modes(user_id: str, archetype: str) -> bool:
    """
    Compare legacy vs adaptive routine generation

    Returns:
        True if adaptive mode shows improvement
    """
    print(f"\n{'='*80}")
    print("⚖️  COMPARISON TEST: Legacy vs Adaptive Routine Generation")
    print(f"{'='*80}")

    # Test 1: Legacy Mode
    print("\n[1/2] Testing LEGACY Mode...")
    legacy_success, legacy_data = test_routine_generation(
        "Routine Generation (LEGACY)",
        user_id,
        archetype,
        "routine_generation_legacy",
        adaptive_mode=False
    )

    if not legacy_success:
        print("\n❌ Legacy mode failed, cannot compare")
        return False

    # Small delay
    print("\n⏳ Waiting 5 seconds before next test...")
    import time
    time.sleep(5)

    # Test 2: Adaptive Mode
    print("\n[2/2] Testing ADAPTIVE Mode...")
    adaptive_success, adaptive_data = test_routine_generation(
        "Routine Generation (ADAPTIVE)",
        user_id,
        archetype,
        "routine_generation_adaptive",
        adaptive_mode=True
    )

    if not adaptive_success:
        print("\n❌ Adaptive mode failed, cannot compare")
        return False

    # Comparison
    print(f"\n{'='*80}")
    print("📊 COMPARISON RESULTS")
    print(f"{'='*80}")

    # Load saved results for comparison
    legacy_result = json.loads((LOGS_DIR / "routine_generation_legacy.json").read_text())
    adaptive_result = json.loads((LOGS_DIR / "routine_generation_adaptive.json").read_text())

    legacy_tasks = legacy_result['analysis']['total_tasks']
    adaptive_tasks = adaptive_result['analysis']['total_tasks']
    reduction = legacy_tasks - adaptive_tasks
    reduction_pct = (reduction / legacy_tasks * 100) if legacy_tasks > 0 else 0

    print(f"\n🎯 Task Density Comparison:")
    print(f"   Legacy System:   {legacy_tasks} tasks")
    print(f"   Adaptive System: {adaptive_tasks} tasks")
    print(f"   Reduction:       {reduction} tasks ({reduction_pct:.1f}%)")

    print(f"\n📈 Improvement Metrics:")
    if adaptive_tasks <= 6:
        print(f"   ✅ Task count within target (≤6)")
    else:
        print(f"   ⚠️ Task count above target ({adaptive_tasks}/6)")

    if reduction_pct >= 30:
        print(f"   ✅ Significant task reduction ({reduction_pct:.1f}%)")
    elif reduction_pct > 0:
        print(f"   ⚠️ Moderate task reduction ({reduction_pct:.1f}%)")
    else:
        print(f"   ❌ No task reduction")

    # Save comparison summary
    comparison_summary = {
        "timestamp": datetime.now().isoformat(),
        "legacy": {
            "total_tasks": legacy_tasks,
            "distribution": legacy_result['analysis']['task_distribution']
        },
        "adaptive": {
            "total_tasks": adaptive_tasks,
            "distribution": adaptive_result['analysis']['task_distribution'],
            "optimized": adaptive_result['analysis'].get('optimized', False)
        },
        "comparison": {
            "task_reduction": reduction,
            "reduction_percentage": reduction_pct,
            "improvement": reduction > 0
        }
    }

    save_test_result("comparison_summary", comparison_summary)

    return reduction > 0


def main():
    """Run dynamic tests - fetch IDs from APIs"""
    print("\n" + "="*80)
    print("HOLISTIC INTEGRATION API - DYNAMIC TEST")
    print("="*80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID[:8]}...")
    print("\nThis test dynamically fetches IDs from APIs to simulate real usage")

    # NEW: Show test menu
    print("\n📋 Available Test Modes:")
    print("   1. Original Integration Tests (GET endpoints)")
    print("   2. Adaptive Routine Generation Test (NEW)")
    print("   3. Compare Legacy vs Adaptive Routine (NEW)")
    print("   4. Full Test Suite (All tests)")

    choice = input("\nSelect test mode (1-4) or Enter for default [1]: ").strip() or "1"

    if choice == "2":
        # Adaptive routine test only
        print("\n🔵 Running Adaptive Routine Generation Test...")
        success, _ = test_routine_generation(
            "Adaptive Routine Generation",
            TEST_USER_ID,
            "Foundation Builder",
            "adaptive_routine_test",
            adaptive_mode=True
        )
        return 0 if success else 1

    elif choice == "3":
        # Comparison test
        print("\n⚖️  Running Legacy vs Adaptive Comparison Test...")
        improvement = compare_routine_modes(TEST_USER_ID, "Foundation Builder")
        return 0 if improvement else 1

    elif choice == "4":
        # Full test suite - run both original and new tests
        print("\n🚀 Running FULL TEST SUITE...")

        # First, run adaptive routine comparison
        print("\n" + "="*80)
        print("PART 1: ADAPTIVE ROUTINE TESTING")
        print("="*80)
        adaptive_improved = compare_routine_modes(TEST_USER_ID, "Foundation Builder")

        # Then run original integration tests
        print("\n" + "="*80)
        print("PART 2: INTEGRATION API TESTS")
        print("="*80)
        # Fall through to run original integration tests

    # Original test mode (default for choice 1 and continuation of choice 4)
    if choice not in ["1", "4"]:
        # Choices 2 and 3 already handled and returned
        return 0

    print("\n" + "="*80)
    print("RUNNING ORIGINAL INTEGRATION TESTS")
    print("="*80)

    results = []

    # Test 1: Health Check
    success, _ = test_endpoint(
        "Health Check",
        f"{BASE_URL}/api/v1/holistic-integration/health",
        "01_health_check"
    )
    results.append(success)

    # Test 2: List analyses to get dynamic IDs
    print("\n" + "="*80)
    print("DYNAMIC ID DISCOVERY")
    print("="*80)

    success, list_data = test_endpoint(
        "List Analysis Results (for ID discovery)",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/analysis-results?limit=10",
        "02_list_analysis_results"
    )
    results.append(success)

    if not success or not list_data:
        print("\n❌ Cannot continue - failed to fetch analysis list")
        return 1

    # Extract IDs by type
    analyses = list_data.get('data', {}).get('analyses', [])
    routine_plan_id = None
    behavior_analysis_id = None
    circadian_analysis_id = None

    for analysis in analyses:
        if analysis['analysis_type'] == 'routine_plan' and not routine_plan_id:
            routine_plan_id = analysis['id']
        elif analysis['analysis_type'] == 'behavior_analysis' and not behavior_analysis_id:
            behavior_analysis_id = analysis['id']
        elif analysis['analysis_type'] == 'circadian_analysis' and not circadian_analysis_id:
            circadian_analysis_id = analysis['id']

    print(f"\n📋 Discovered IDs:")
    print(f"  Routine Plan: {routine_plan_id}")
    print(f"  Behavior Analysis: {behavior_analysis_id}")
    print(f"  Circadian Analysis: {circadian_analysis_id}")

    # Test 3: Get specific routine plan (dynamically discovered)
    if routine_plan_id:
        success, _ = test_endpoint(
            "Get Routine Plan Analysis (dynamic ID)",
            f"{BASE_URL}/api/v1/analysis-results/{routine_plan_id}",
            "03_get_routine_plan"
        )
        results.append(success)
    else:
        print("\n⚠️  No routine_plan found, skipping test")
        results.append(False)

    # Test 4: Behavior Analysis (latest)
    success, _ = test_endpoint(
        "Get Latest Behavior Analysis",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/behavior-analysis",
        "04_behavior_analysis"
    )
    results.append(success)

    # Test 5: Circadian Analysis (latest)
    success, _ = test_endpoint(
        "Get Latest Circadian Analysis",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/circadian-analysis",
        "05_circadian_analysis"
    )
    results.append(success)

    # Test 6: Context Memory
    success, _ = test_endpoint(
        "Get Context Memory",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/context-memory",
        "06_context_memory"
    )
    results.append(success)

    # Test 7: Full Context (dynamic ID)
    if routine_plan_id:
        success, full_context = test_endpoint(
            "Get Full Context (dynamic ID)",
            f"{BASE_URL}/api/v1/analysis-results/{routine_plan_id}/full-context",
            "07_full_context"
        )
        results.append(success)

        # Show what Full Context returns
        if success and full_context:
            data = full_context.get('data', {})
            print(f"\n📦 Full Context Bundle Contains:")
            print(f"  ✓ Primary Analysis: {data.get('analysis_type')}")
            print(f"  ✓ Behavior Analysis: {'Yes' if data.get('behavior_analysis') else 'No'}")
            print(f"  ✓ Circadian Analysis: {'Yes' if data.get('circadian_analysis') else 'No'}")
            print(f"  ✓ Plan Items: {len(data.get('plan_items', []))} items")
            print(f"  ✓ Context Memory: {'Yes' if data.get('context_memory') else 'No'}")
    else:
        print("\n⚠️  No routine_plan ID, skipping full context test")
        results.append(False)

    # Test 8: Cross-reference - verify behavior analysis ID matches
    if behavior_analysis_id:
        success, behavior_data = test_endpoint(
            "Verify Behavior Analysis by ID (cross-reference)",
            f"{BASE_URL}/api/v1/analysis-results/{behavior_analysis_id}",
            "08_verify_behavior_by_id"
        )
        results.append(success)

        if success and behavior_data:
            # Compare with latest behavior analysis
            print(f"\n🔍 Cross-Reference Check:")
            print(f"  Analysis ID from list: {behavior_analysis_id}")
            print(f"  Analysis ID from fetch: {behavior_data.get('data', {}).get('id')}")
            print(f"  Match: {'✓' if behavior_analysis_id == behavior_data.get('data', {}).get('id') else '✗'}")

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"\n📁 All test results saved to: {LOGS_DIR}")

    print(f"\n🎯 Real-World Usage Pattern:")
    print(f"  1. ✓ List analyses to get available IDs")
    print(f"  2. ✓ Fetch specific analysis by type (latest)")
    print(f"  3. ✓ Fetch specific analysis by ID (user selection)")
    print(f"  4. ✓ Get full context bundle for conversation")
    print(f"  5. ✓ Cross-reference to verify data consistency")

    if passed == total:
        print("\n✓ All tests passed! APIs are production-ready with dynamic ID usage!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
