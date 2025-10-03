"""
Quick test script for Holistic Integration endpoints
Simple curl-like test to verify endpoints are working
Saves JSON responses to logs folder
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8002"
TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
TEST_ANALYSIS_ID = "7f785ff5-d785-4013-8c6a-bbd0802f3eed"

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs" / "holistic_integration_tests"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def test_endpoint(name: str, url: str, log_filename: str):
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
            print("\nResponse:")
            print(json.dumps(data, indent=2, default=str))
            print("\n✓ SUCCESS")
            success = True
        else:
            test_result["response"] = response.text
            print(f"\n✗ FAILED: {response.text}")
            success = False

    except Exception as e:
        test_result["error"] = str(e)
        print(f"\n✗ ERROR: {e}")
        success = False

    # Save to JSON file
    log_file = LOGS_DIR / f"{log_filename}.json"
    with open(log_file, 'w') as f:
        json.dump(test_result, f, indent=2, default=str)
    print(f"📁 Saved to: {log_file}")

    return success


def main():
    """Run quick tests"""
    print("HOLISTIC INTEGRATION API - QUICK TEST")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}\n")

    results = []

    # Test 1: Health Check
    results.append(test_endpoint(
        "Health Check",
        f"{BASE_URL}/api/v1/holistic-integration/health",
        "01_health_check"
    ))

    # Test 2: Get Specific Analysis
    results.append(test_endpoint(
        "Get Analysis Result",
        f"{BASE_URL}/api/v1/analysis-results/{TEST_ANALYSIS_ID}",
        "02_get_analysis_result"
    ))

    # Test 3: Behavior Analysis
    results.append(test_endpoint(
        "Behavior Analysis",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/behavior-analysis",
        "03_behavior_analysis"
    ))

    # Test 4: Circadian Analysis
    results.append(test_endpoint(
        "Circadian Analysis",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/circadian-analysis",
        "04_circadian_analysis"
    ))

    # Test 5: Context Memory
    results.append(test_endpoint(
        "Context Memory",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/context-memory",
        "05_context_memory"
    ))

    # Test 6: List Analyses
    results.append(test_endpoint(
        "List Analysis Results",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}/analysis-results?limit=5",
        "06_list_analysis_results"
    ))

    # Test 7: Full Context
    results.append(test_endpoint(
        "Full Context",
        f"{BASE_URL}/api/v1/analysis-results/{TEST_ANALYSIS_ID}/full-context",
        "07_full_context"
    ))

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"\n📁 All test results saved to: {LOGS_DIR}")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
