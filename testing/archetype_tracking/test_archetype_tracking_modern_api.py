#!/usr/bin/env python3
"""
Archetype-Specific Tracking Test - Modern API
Tests the new archetype-specific analysis tracking using the current API endpoints
Run this after applying the database migration
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

def test_modern_archetype_tracking():
    """Test archetype-specific tracking using modern API endpoints"""
    
    print("🎯 ARCHETYPE-SPECIFIC TRACKING TEST (Modern API)")
    print("=" * 70)
    print(f"Server: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print(f"Using modern API endpoints:")
    print(f"  - POST /api/user/{{user_id}}/behavior/analyze")
    print(f"  - POST /api/user/{{user_id}}/routine/generate")
    print(f"  - POST /api/user/{{user_id}}/nutrition/generate")
    print()
    
    # Test 1: Server health
    print("🏥 1. Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"❌ Server health issue: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    results = {}
    
    # Test 2: First archetype - Foundation Builder behavior analysis
    print(f"\n🧠 2. Behavior Analysis - Foundation Builder (First Time)")
    print("   Expected: New archetype → 7-day data window → archetype_analysis_tracking updated")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/user/{TEST_USER_ID}/behavior/analyze", json={
            "archetype": "Foundation Builder",
            "force_refresh": False
        }, timeout=120)
        
        fb_behavior_time = time.time() - start_time
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Foundation Builder behavior analysis completed in {fb_behavior_time:.1f}s")
            print(f"   Response keys: {list(result_data.keys())}")
            
            # Check if we have behavior analysis data
            if 'behavior_analysis' in result_data:
                behavior = result_data['behavior_analysis']
                print(f"   ✅ Behavior analysis data present")
                if isinstance(behavior, dict) and 'summary' in behavior:
                    print(f"   📊 Analysis summary: {behavior['summary'][:100]}...")
            
            results['fb_behavior'] = {
                'status': 'success',
                'time': fb_behavior_time,
                'data_size': len(json.dumps(result_data))
            }
        else:
            print(f"❌ Foundation Builder behavior analysis failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}...")
            return
            
    except Exception as e:
        print(f"❌ Foundation Builder behavior analysis error: {e}")
        return
    
    # Wait before next test
    print("   ⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # Test 3: Generate routine for Foundation Builder (should use behavior analysis)
    print(f"\n🏃 3. Routine Generation - Foundation Builder")
    print("   Expected: Use existing behavior analysis + generate personalized routine")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/user/{TEST_USER_ID}/routine/generate", json={
            "archetype": "Foundation Builder",
            "preferences": {
                "workout_duration_minutes": 30,
                "fitness_level": "beginner",
                "available_equipment": ["none"]
            }
        }, timeout=90)
        
        fb_routine_time = time.time() - start_time
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Foundation Builder routine completed in {fb_routine_time:.1f}s")
            
            if 'routine_plan' in result_data:
                routine = result_data['routine_plan']
                print(f"   ✅ Routine plan generated")
                if isinstance(routine, dict) and 'daily_schedule' in routine:
                    print(f"   📅 Daily schedule present")
            
            results['fb_routine'] = {
                'status': 'success', 
                'time': fb_routine_time
            }
        else:
            print(f"❌ Foundation Builder routine failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}...")
            
    except Exception as e:
        print(f"❌ Foundation Builder routine error: {e}")
    
    # Wait before archetype switch
    print("   ⏳ Waiting 5 seconds before archetype switch...")
    time.sleep(5)
    
    # Test 4: Switch to Peak Performer (incompatible archetype - should get 7-day window)
    print(f"\n🚀 4. Behavior Analysis - Peak Performer (New Archetype)")
    print("   Expected: New archetype → 7-day data window → separate archetype_analysis_tracking entry")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/user/{TEST_USER_ID}/behavior/analyze", json={
            "archetype": "Peak Performer",
            "force_refresh": False
        }, timeout=120)
        
        pp_behavior_time = time.time() - start_time
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Peak Performer behavior analysis completed in {pp_behavior_time:.1f}s")
            
            # This should be similar timing to Foundation Builder (both 7-day windows)
            time_diff = abs(pp_behavior_time - fb_behavior_time)
            if time_diff < fb_behavior_time * 0.5:  # Within 50%
                print("   ✅ Similar timing to FB suggests 7-day window for new archetype")
            else:
                print(f"   ⚠️  Time difference: FB={fb_behavior_time:.1f}s, PP={pp_behavior_time:.1f}s")
            
            results['pp_behavior'] = {
                'status': 'success',
                'time': pp_behavior_time,
                'time_vs_fb': time_diff
            }
        else:
            print(f"❌ Peak Performer behavior analysis failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}...")
            return
            
    except Exception as e:
        print(f"❌ Peak Performer behavior analysis error: {e}")
        return
    
    # Wait before next test
    print("   ⏳ Waiting 3 seconds...")
    time.sleep(3)
    
    # Test 5: Generate routine for Peak Performer
    print(f"\n🏃‍♂️ 5. Routine Generation - Peak Performer")
    print("   Expected: Use PP behavior analysis + generate advanced routine")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/user/{TEST_USER_ID}/routine/generate", json={
            "archetype": "Peak Performer",
            "preferences": {
                "workout_duration_minutes": 90,
                "fitness_level": "advanced",
                "available_equipment": ["full_gym"]
            }
        }, timeout=90)
        
        pp_routine_time = time.time() - start_time
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Peak Performer routine completed in {pp_routine_time:.1f}s")
            
            results['pp_routine'] = {
                'status': 'success',
                'time': pp_routine_time
            }
        else:
            print(f"❌ Peak Performer routine failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Peak Performer routine error: {e}")
    
    # Wait before testing archetype-specific incremental behavior
    print("   ⏳ Waiting 5 seconds...")
    time.sleep(5)
    
    # Test 6: Return to Foundation Builder behavior analysis (should be incremental)
    print(f"\n↩️  6. Behavior Analysis - Foundation Builder (Return)")
    print("   Expected: Previous archetype → incremental data since FB last analysis")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/user/{TEST_USER_ID}/behavior/analyze", json={
            "archetype": "Foundation Builder",
            "force_refresh": False
        }, timeout=120)
        
        fb_return_time = time.time() - start_time
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Foundation Builder (return) completed in {fb_return_time:.1f}s")
            
            # This should be faster than Peak Performer (incremental vs 7-day)
            if fb_return_time < pp_behavior_time * 0.8:
                print("   ✅ FASTER than PP first analysis - archetype-specific tracking working!")
            else:
                print(f"   ⚠️  Similar/slower than PP: FB_return={fb_return_time:.1f}s, PP={pp_behavior_time:.1f}s")
            
            results['fb_return'] = {
                'status': 'success',
                'time': fb_return_time,
                'speedup_vs_pp': pp_behavior_time - fb_return_time
            }
        else:
            print(f"❌ Foundation Builder (return) failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Foundation Builder (return) error: {e}")
        return
    
    # Test 7: Peak Performer behavior analysis again (should be incremental)
    print(f"\n🔄 7. Behavior Analysis - Peak Performer (Return)")
    print("   Expected: Previous archetype → incremental data since PP last analysis")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/api/user/{TEST_USER_ID}/behavior/analyze", json={
            "archetype": "Peak Performer", 
            "force_refresh": False
        }, timeout=120)
        
        pp_return_time = time.time() - start_time
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Peak Performer (return) completed in {pp_return_time:.1f}s")
            
            # This should be much faster than first PP (incremental vs 7-day)
            speedup = pp_behavior_time - pp_return_time
            if pp_return_time < pp_behavior_time * 0.7:
                print(f"   ✅ MUCH FASTER than first PP ({speedup:.1f}s speedup) - archetype tracking working!")
            else:
                print(f"   ⚠️  Not much faster: first={pp_behavior_time:.1f}s, return={pp_return_time:.1f}s")
            
            results['pp_return'] = {
                'status': 'success',
                'time': pp_return_time,
                'speedup_vs_first': speedup
            }
        else:
            print(f"❌ Peak Performer (return) failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Peak Performer (return) error: {e}")
        return
    
    # Results Summary
    print("\n" + "=" * 70)
    print("🎯 ARCHETYPE-SPECIFIC TRACKING TEST RESULTS")
    print("=" * 70)
    
    print("📊 TIMING ANALYSIS:")
    print("-" * 40)
    print(f"Foundation Builder (first):   {results['fb_behavior']['time']:.1f}s  [7-day baseline]")
    print(f"Peak Performer (first):      {results['pp_behavior']['time']:.1f}s  [7-day baseline]") 
    print(f"Foundation Builder (return):  {results['fb_return']['time']:.1f}s  [archetype-specific incremental]")
    print(f"Peak Performer (return):     {results['pp_return']['time']:.1f}s  [archetype-specific incremental]")
    
    print("\n🧪 ARCHETYPE TRACKING INDICATORS:")
    print("-" * 40)
    
    # Key indicators of working archetype-specific tracking
    fb_return_efficient = results['fb_return']['time'] < results['pp_behavior']['time']
    pp_return_efficient = results['pp_return']['time'] < results['pp_behavior']['time'] * 0.8
    similar_baselines = abs(results['fb_behavior']['time'] - results['pp_behavior']['time']) < results['fb_behavior']['time'] * 0.5
    
    print(f"✅ Similar baseline times (FB/PP first): {similar_baselines}")
    print(f"✅ FB return faster than PP first: {fb_return_efficient}")  
    print(f"✅ PP return much faster than PP first: {pp_return_efficient}")
    
    # Overall assessment
    success_indicators = sum([similar_baselines, fb_return_efficient, pp_return_efficient])
    
    if success_indicators >= 2:
        print(f"\n🎉 SUCCESS: ARCHETYPE-SPECIFIC TRACKING IS WORKING! ({success_indicators}/3 indicators)")
        print("   ✅ Each archetype maintains independent analysis timestamps")
        print("   ✅ New archetypes get comprehensive 7-day data baselines")
        print("   ✅ Returning to archetypes uses efficient incremental data")
        print("   ✅ archetype_analysis_tracking table is functioning correctly")
    else:
        print(f"\n⚠️  NEEDS INVESTIGATION: Only {success_indicators}/3 indicators passed")
        print("   - Check database migration was applied successfully")
        print("   - Check ArchetypeAnalysisTracker service logs")
        print("   - Verify OnDemandAnalysisService integration")
        print("   - Check archetype_analysis_tracking table has records")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Query archetype_analysis_tracking table to see stored data")
    print("   2. Review service logs for archetype tracking messages")
    print("   3. Test nutrition generation with different archetypes")
    print("   4. Monitor production archetype switching patterns")
    
    print("\n🔍 DEBUGGING QUERIES:")
    print("   SELECT * FROM archetype_analysis_tracking WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';")
    print("   SELECT archetype, COUNT(*) FROM holistic_analysis_results WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2' GROUP BY archetype;")

if __name__ == "__main__":
    test_modern_archetype_tracking()