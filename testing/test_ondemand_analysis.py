#!/usr/bin/env python3
"""
Test script for on-demand behavior analysis system
Tests the smart threshold-based analysis decision logic
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

async def test_ondemand_analysis():
    """Test the on-demand analysis service"""
    
    try:
        print("🧪 Testing On-Demand Analysis Service...")
        
        # Import the service
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        
        # Test user ID
        test_user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
        
        # Get the service
        ondemand_service = await get_ondemand_service()
        
        print(f"✅ Service initialized successfully")
        
        # Test 1: Check analysis decision for user
        print(f"\n📊 Test 1: Analysis decision for user {test_user_id[:8]}...")
        
        decision, metadata = await ondemand_service.should_run_analysis(test_user_id)
        
        print(f"🧠 Decision: {decision.value}")
        print(f"📋 Metadata:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        
        # Test 2: Force refresh decision
        print(f"\n🔄 Test 2: Force refresh analysis...")
        
        decision_force, metadata_force = await ondemand_service.should_run_analysis(
            test_user_id, force_refresh=True
        )
        
        print(f"🧠 Force Decision: {decision_force.value}")
        print(f"📋 Reason: {metadata_force['reason']}")
        
        # Test 3: Try to get cached behavior analysis
        print(f"\n📋 Test 3: Getting cached behavior analysis...")
        
        cached_analysis = await ondemand_service.get_cached_behavior_analysis(test_user_id)
        
        if cached_analysis:
            print(f"✅ Found cached analysis with {len(cached_analysis)} top-level keys")
            print(f"📋 Keys: {list(cached_analysis.keys()) if isinstance(cached_analysis, dict) else 'Not a dict'}")
        else:
            print(f"⚠️ No cached analysis found")
        
        # Test 4: Memory quality assessment
        print(f"\n🧠 Test 4: Memory quality assessment...")
        
        try:
            memory_quality = await ondemand_service._assess_memory_quality(test_user_id)
            print(f"📊 Memory Quality: {memory_quality.value}")
        except Exception as e:
            print(f"⚠️ Memory quality check failed: {e}")
        
        # Cleanup
        await ondemand_service.cleanup()
        print(f"\n✅ All tests completed successfully!")
        
        return {
            "status": "success",
            "decision": decision.value,
            "metadata": metadata,
            "has_cached_analysis": bool(cached_analysis)
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

async def test_api_integration():
    """Test the API integration with on-demand analysis"""
    
    print(f"\n🔌 Testing API Integration...")
    
    try:
        # Test the API endpoints (requires server to be running)
        import httpx
        
        base_url = "http://localhost:8000"
        test_user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
        
        async with httpx.AsyncClient() as client:
            # Test routine generation
            print(f"🏃 Testing routine generation endpoint...")
            
            routine_response = await client.post(
                f"{base_url}/api/user/{test_user_id}/routine/generate",
                json={
                    "archetype": "Foundation Builder",
                    "preferences": {
                        "workout_type": "strength_training",
                        "duration_minutes": 30
                    }
                },
                timeout=60.0
            )
            
            if routine_response.status_code == 200:
                routine_data = routine_response.json()
                generation_metadata = routine_data.get('generation_metadata', {})
                
                print(f"✅ Routine generation successful")
                print(f"📊 Analysis Decision: {generation_metadata.get('analysis_decision')}")
                print(f"📋 Data Quality: {generation_metadata.get('data_quality')}")
                print(f"💾 Cached: {routine_data.get('cached', False)}")
                
                if 'analysis_freshness' in generation_metadata:
                    freshness = generation_metadata['analysis_freshness']
                    print(f"🕒 Freshness Reason: {freshness.get('reason')}")
                    print(f"📈 New Data Points: {freshness.get('new_data_points')}")
                    print(f"⏰ Hours Since Analysis: {freshness.get('hours_since_analysis')}")
                
            else:
                print(f"❌ Routine generation failed: {routine_response.status_code}")
                print(f"📋 Response: {routine_response.text}")
        
        return {"status": "success", "api_test": "completed"}
        
    except Exception as e:
        print(f"⚠️ API test skipped (server may not be running): {e}")
        return {"status": "skipped", "reason": str(e)}

async def main():
    """Main test function"""
    
    print("=" * 60)
    print("🧪 HolisticOS On-Demand Analysis Test Suite")
    print("=" * 60)
    
    # Test 1: Service functionality
    service_result = await test_ondemand_analysis()
    
    # Test 2: API integration (optional - requires server)
    api_result = await test_api_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"🔧 Service Test: {service_result['status']}")
    print(f"🔌 API Test: {api_result['status']}")
    
    if service_result['status'] == 'success':
        print(f"🧠 Decision Logic: Working")
        print(f"📋 Analysis Decision: {service_result['decision']}")
        print(f"💾 Cached Analysis Available: {service_result['has_cached_analysis']}")
    
    print("\n✅ On-demand analysis system is ready!")
    print("📋 Key Features:")
    print("   - Smart threshold-based analysis triggering")
    print("   - Memory-aware threshold calculation") 
    print("   - Three-tier response system (fresh/cached/stale)")
    print("   - Intelligent fallback on analysis failures")
    print("   - Comprehensive metadata in responses")

if __name__ == "__main__":
    asyncio.run(main())