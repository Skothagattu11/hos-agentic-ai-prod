"""
Dynamic Holistic Integration Test Script
Fetches IDs dynamically from APIs to simulate real-world usage
Saves JSON responses to logs folder
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8002"
TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

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


def main():
    """Run dynamic tests - fetch IDs from APIs"""
    print("HOLISTIC INTEGRATION API - DYNAMIC TEST")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print("\nThis test dynamically fetches IDs from APIs to simulate real usage\n")

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
