#!/usr/bin/env python3
"""
Phase 1 Testing Script - Real User Data Integration MVP
CTO Testing: Simple, Comprehensive, Easy to Debug
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.user_data_service import UserDataService, get_user_health_data
from services.health_data_client import HealthDataClient

async def test_api_client():
    """Test API client functionality"""
    print("\n" + "="*50)
    print("TESTING API CLIENT")
    print("="*50)
    
    client = HealthDataClient()
    
    # Test health check
    print("\n[TEST] API Health Check...")
    health = await client.health_check()
    print(f"API Status: {health['api_status']}")
    print(f"Base URL: {health['base_url']}")
    
    if health['api_status'] == 'healthy':
        print("✅ API Client is healthy")
    else:
        print("⚠️  API Client health check failed (expected for MVP - API might not be fully configured)")
    
    return health['api_status'] == 'healthy'

async def test_user_data_service():
    """Test UserDataService functionality"""
    print("\n" + "="*50)
    print("TESTING USER DATA SERVICE")
    print("="*50)
    
    service = UserDataService()
    
    try:
        # Test database connection
        print("\n[TEST] Database Health Check...")
        db_health = await service.health_check()
        print(f"Database Status: {db_health['status']}")
        
        if db_health['status'] == 'healthy':
            print("✅ Database connection is healthy")
        else:
            print(f"❌ Database connection failed: {db_health.get('error', 'Unknown error')}")
            return False
        
        # Test data fetching with a test user
        print("\n[TEST] User Data Fetching...")
        test_user_id = "test_user_phase1"
        
        print(f"Attempting to fetch data for user: {test_user_id}")
        user_data = await service.get_user_health_data(test_user_id, days=7)
        
        print(f"✅ Data fetch completed successfully!")
        print(f"User ID: {user_data.user_id}")
        print(f"Scores: {user_data.data_quality.scores_count}")
        print(f"Biomarkers: {user_data.data_quality.biomarkers_count}")
        print(f"Archetypes: {user_data.data_quality.archetypes_count}")
        print(f"Data Quality: {user_data.data_quality.quality_level}")
        print(f"Date Range: {user_data.date_range.days} days")
        
        # Test agent-specific data views
        print(f"\n[TEST] Agent Data Views...")
        behavior_data = user_data.behavior_data
        memory_data = user_data.memory_data
        nutrition_data = user_data.nutrition_data
        routine_data = user_data.routine_data
        adaptation_data = user_data.adaptation_data
        insights_data = user_data.insights_data
        
        print(f"✅ All 6 agent data views accessible")
        print(f"Behavior data keys: {list(behavior_data.keys())}")
        print(f"Memory data keys: {list(memory_data.keys())}")
        print(f"Nutrition data keys: {list(nutrition_data.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ UserDataService test failed: {e}")
        return False
    finally:
        await service.cleanup()

async def test_convenience_function():
    """Test the convenience function"""
    print("\n" + "="*50)
    print("TESTING CONVENIENCE FUNCTION")
    print("="*50)
    
    try:
        print("\n[TEST] get_user_health_data function...")
        test_user_id = "test_user_convenience"
        
        user_data = await get_user_health_data(test_user_id, days=3)
        
        print(f"✅ Convenience function works!")
        print(f"User: {user_data.user_id}")
        print(f"Quality: {user_data.data_quality.quality_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling and graceful failures"""
    print("\n" + "="*50)
    print("TESTING ERROR HANDLING")
    print("="*50)
    
    service = UserDataService()
    
    try:
        print("\n[TEST] Invalid user ID handling...")
        invalid_user = "definitely_does_not_exist_12345"
        
        user_data = await service.get_user_health_data(invalid_user, days=7)
        
        # Should not crash, should return empty data gracefully
        print(f"✅ Error handling works - no crash on invalid user")
        print(f"Quality level: {user_data.data_quality.quality_level}")
        print(f"Has data: {user_data.data_quality.has_recent_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    finally:
        await service.cleanup()

async def main():
    """Main test runner"""
    print("🚀 HOLISTICOS MVP - PHASE 1 TESTING")
    print("Real User Data Integration - Foundation Infrastructure")
    print("CTO Testing: Comprehensive validation of MVP implementation")
    
    start_time = datetime.now()
    
    # Run all tests
    tests = [
        ("API Client", test_api_client),
        ("User Data Service", test_user_data_service),
        ("Convenience Function", test_convenience_function),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} test...")
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("PHASE 1 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Duration: {duration:.2f} seconds")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 1 is ready for Phase 2.")
        print("\n✅ Foundation Infrastructure Complete:")
        print("   • UserDataService with API-first approach")
        print("   • HealthDataClient with retry logic and error handling")
        print("   • Enhanced health data models with agent-specific views")
        print("   • Robust error handling and graceful failures")
        print("   • Comprehensive logging for troubleshooting")
        print("\n🚀 Ready to proceed to Phase 2: FastAPI Integration")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review and fix issues before proceeding.")
        print("\n🔧 Common troubleshooting:")
        print("   • Check database connection in .env file")
        print("   • Verify Supabase credentials are correct")
        print("   • Ensure hos-fapi-hm-sahha-main is accessible")
        print("   • Check network connectivity")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)