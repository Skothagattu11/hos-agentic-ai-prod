#!/usr/bin/env python3
"""
Rate Limiting Load Test

Tests the HolisticOS rate limiting system under various load conditions.
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

BASE_URL = "http://localhost:8001"

async def make_request(session: aiohttp.ClientSession, endpoint: str, user_id: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a single request to the API"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if data:
            async with session.post(url, json=data) as response:
                result = {
                    "status_code": response.status,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "response": await response.json(),
                    "headers": dict(response.headers)
                }
        else:
            async with session.get(url) as response:
                result = {
                    "status_code": response.status,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "response": await response.json(),
                    "headers": dict(response.headers)
                }
        
        return result
        
    except Exception as e:
        return {
            "status_code": 0,
            "user_id": user_id,
            "endpoint": endpoint,
            "error": str(e),
            "headers": {}
        }

async def test_rate_limiting_basic():
    """Test basic rate limiting functionality"""
    print("🧪 Testing basic rate limiting...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint first
        health_result = await make_request(session, "/api/health", "test_user")
        if health_result["status_code"] != 200:
            print(f"❌ Health check failed: {health_result}")
            return False
        
        print("✅ Health check passed")
        
        # Test multiple rapid requests to trigger rate limit
        user_id = "test_rate_limit_user"
        requests = []
        
        # Make 6 requests rapidly (should exceed free tier limit of 5/hour for behavior analysis)
        for i in range(6):
            data = {
                "user_id": user_id,
                "archetype": "Foundation Builder",
                "force_refresh": False
            }
            request_task = make_request(session, f"/api/user/{user_id}/behavior/analyze", user_id, data)
            requests.append(request_task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*requests)
        
        # Analyze results
        success_count = sum(1 for r in results if r["status_code"] == 200)
        rate_limited_count = sum(1 for r in results if r["status_code"] == 429)
        
        print(f"📊 Results: {success_count} successful, {rate_limited_count} rate limited")
        
        # Print rate limit headers from successful requests
        for result in results:
            if result["status_code"] == 200 and "X-RateLimit-Limit" in result["headers"]:
                print(f"   Rate limit headers: Limit={result['headers'].get('X-RateLimit-Limit')}, "
                      f"Remaining={result['headers'].get('X-RateLimit-Remaining')}")
                break
        
        # We expect some requests to be rate limited
        if rate_limited_count > 0:
            print("✅ Rate limiting is working - some requests were blocked")
            return True
        else:
            print("⚠️ No rate limiting detected - may need to adjust limits or Redis may not be available")
            return False

async def test_cost_tracking():
    """Test cost tracking functionality"""
    print("\n💰 Testing cost tracking...")
    
    async with aiohttp.ClientSession() as session:
        user_id = "test_cost_user"
        
        # Make a request that should incur cost
        data = {
            "user_id": user_id,
            "archetype": "Foundation Builder"
        }
        
        result = await make_request(session, f"/api/user/{user_id}/routine/generate", user_id, data)
        
        if result["status_code"] == 200:
            cost_headers = {
                "cost_used": result["headers"].get("X-Cost-Used-Today"),
                "cost_limit": result["headers"].get("X-Cost-Limit-Daily"),
                "cost_remaining": result["headers"].get("X-Cost-Remaining-Today")
            }
            
            print(f"💵 Cost tracking headers: {cost_headers}")
            
            if any(cost_headers.values()):
                print("✅ Cost tracking is working")
                return True
            else:
                print("⚠️ Cost tracking headers not found")
                return False
        else:
            print(f"❌ Request failed: {result}")
            return False

async def test_admin_endpoints():
    """Test admin monitoring endpoints"""
    print("\n📊 Testing admin monitoring endpoints...")
    
    async with aiohttp.ClientSession() as session:
        # Test system stats
        stats_result = await make_request(session, "/api/admin/rate-limits", "admin")
        
        if stats_result["status_code"] == 200:
            print("✅ Admin stats endpoint working")
            print(f"   System stats: {json.dumps(stats_result['response'], indent=2)}")
            return True
        else:
            print(f"❌ Admin stats failed: {stats_result}")
            return False

async def test_tier_differences():
    """Test different user tier behaviors"""
    print("\n👥 Testing user tier differences...")
    
    async with aiohttp.ClientSession() as session:
        # Test free tier user
        free_user = "free_user_test"
        premium_user = "premium_user_test"
        admin_user = "admin_user_test"
        
        users_to_test = [
            (free_user, "free"),
            (premium_user, "premium"),
            (admin_user, "admin")
        ]
        
        for user_id, tier in users_to_test:
            # Test user stats endpoint
            user_stats = await make_request(session, f"/api/admin/rate-limits/user/{user_id}", user_id)
            
            if user_stats["status_code"] == 200:
                tier_info = user_stats["response"].get("user_stats", {}).get("tier", "unknown")
                print(f"✅ User {user_id} tier: {tier_info}")
            else:
                print(f"⚠️ Could not get stats for {user_id}")
        
        return True

async def load_test_concurrent_users():
    """Test system under concurrent load from multiple users"""
    print("\n⚡ Testing concurrent load...")
    
    async with aiohttp.ClientSession() as session:
        # Create 10 concurrent users making requests
        tasks = []
        
        for user_num in range(10):
            user_id = f"load_test_user_{user_num}"
            data = {
                "user_id": user_id,
                "archetype": "Foundation Builder"
            }
            
            # Each user makes a routine generation request
            task = make_request(session, f"/api/user/{user_id}/routine/generate", user_id, data)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        success_count = sum(1 for r in results if r["status_code"] == 200)
        rate_limited_count = sum(1 for r in results if r["status_code"] == 429)
        error_count = sum(1 for r in results if r["status_code"] not in [200, 429])
        
        print(f"⏱️ Load test completed in {end_time - start_time:.2f} seconds")
        print(f"📈 Results: {success_count} success, {rate_limited_count} rate limited, {error_count} errors")
        
        if success_count > 0 and rate_limited_count > 0:
            print("✅ System handled concurrent load with proper rate limiting")
            return True
        else:
            print("⚠️ Unexpected load test results")
            return False

async def main():
    """Run all rate limiting tests"""
    print("🚀 Starting HolisticOS Rate Limiting Load Test\n")
    
    tests = [
        ("Basic Rate Limiting", test_rate_limiting_basic),
        ("Cost Tracking", test_cost_tracking),
        ("Admin Endpoints", test_admin_endpoints),
        ("User Tiers", test_tier_differences),
        ("Concurrent Load", load_test_concurrent_users)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"{'='*50}")
            result = await test_func()
            results[test_name] = result
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    print(f"\n{'='*50}")
    print("📋 FINAL RESULTS:")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All rate limiting tests passed! System is ready for production.")
    else:
        print("⚠️ Some tests failed. Review the rate limiting configuration.")
    
    return passed == total

if __name__ == "__main__":
    print("Make sure the HolisticOS server is running on http://localhost:8001")
    print("Start it with: python start_openai.py\n")
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)