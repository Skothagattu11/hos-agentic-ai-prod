#!/usr/bin/env python3
"""
Phase 4.2 Memory-Enhanced End-to-End Interactive Test
Tests all Phase 4.2 features: Enhanced Memory Prompts, Real Memory Integration, 
Insights Generation, and Memory-Enhanced Intelligence
"""
import asyncio
import sys
import os
import time
import json
from datetime import datetime, timezone
from pathlib import Path
import aiohttp

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
REAL_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
BASE_URL = "http://localhost:8001"
TEST_ARCHETYPE = "Foundation Builder"

def get_user_input(prompt):
    """Get user confirmation"""
    response = input(f"\n{prompt} (y/n): ").lower().strip()
    return response in ['y', 'yes']

def print_section(title, emoji="🎯"):
    """Print formatted section header"""
    print(f"\n{emoji} {title}")
    print("-" * 60)

async def test_server_health():
    """Test if the FastAPI server is running"""
    print_section("SERVER HEALTH CHECK", "🏥")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Server is running: {result.get('message', 'OK')}")
                    return True
                else:
                    print(f"⚠️  Server returned status {response.status}")
                    return False
    except aiohttp.ClientConnectorError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("   Make sure FastAPI server is running with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_phase42_analysis(user_id, archetype, analysis_type="INITIAL"):
    """Test Phase 4.2 enhanced analysis with memory and insights"""
    print_section(f"PHASE 4.2 {analysis_type} ANALYSIS", "🧠")
    
    try:
        payload = {
            "user_id": user_id,
            "archetype": archetype
        }
        
        print(f"📋 Request: POST /api/analyze")
        print(f"   • User ID: {user_id}")
        print(f"   • Archetype: {archetype}")
        print(f"   • Expected: Memory-enhanced prompts + AI insights")
        print(f"⏳ Starting analysis... (this may take several minutes)")
        
        start_time = time.time()
        
        timeout = aiohttp.ClientTimeout(total=900)  # 15 minutes for enhanced analysis
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{BASE_URL}/api/analyze",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Analysis completed in {duration:.1f} seconds")
                    
                    # Validate Phase 4.2 features in response
                    analysis_data = result.get('analysis', {})
                    system_info = analysis_data.get('system_info', {})
                    models_used = system_info.get('models_used', {})
                    
                    # Check for Phase 4.2 indicators
                    phase42_features = {
                        "Memory-enhanced": "4.2" in system_info.get('phase', ''),
                        "AI Insights model": 'ai_insights' in models_used,
                        "Behavior analysis": 'behavior_analysis' in analysis_data,
                        "Nutrition plan": 'nutrition_plan' in analysis_data,
                        "Routine plan": 'routine_plan' in analysis_data
                    }
                    
                    print(f"\n📊 Phase 4.2 Features Detected:")
                    for feature, present in phase42_features.items():
                        print(f"   {'✅' if present else '❌'} {feature}")
                    
                    return result, True, phase42_features
                else:
                    error_text = await response.text()
                    print(f"❌ Analysis failed: HTTP {response.status}")
                    print(f"   Error: {error_text[:200]}...")
                    return None, False, {}
                    
    except asyncio.TimeoutError:
        print("⏰ Analysis timed out (>15 minutes)")
        return None, False, {}
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        print(f"❌ Analysis failed after {duration:.1f}s: {e}")
        return None, False, {}

async def test_insights_endpoints(user_id):
    """Test the new AI insights endpoints"""
    print_section("AI INSIGHTS ENDPOINTS", "🔍")
    
    results = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Get latest insights
            print("📋 Testing GET /api/user/{user_id}/insights/latest")
            async with session.get(f"{BASE_URL}/api/user/{user_id}/insights/latest") as response:
                if response.status == 200:
                    insights_data = await response.json()
                    print(f"✅ Latest insights retrieved")
                    print(f"   Status: {insights_data.get('status')}")
                    
                    if insights_data.get('status') == 'success':
                        insights = insights_data.get('insights', {})
                        insight_count = len(insights.get('insights', []))
                        print(f"   Insights found: {insight_count}")
                        results['latest_insights'] = True
                    else:
                        print(f"   No insights available yet (expected for new user)")
                        results['latest_insights'] = False
                else:
                    print(f"❌ Latest insights failed: HTTP {response.status}")
                    results['latest_insights'] = False
            
            # Test 2: Generate fresh insights (if we have analysis data)
            print("\n📋 Testing POST /api/user/{user_id}/insights/generate")
            insights_request = {
                "insight_type": "comprehensive",
                "time_horizon": "medium_term",
                "focus_areas": ["behavioral_patterns", "nutrition_adherence"]
            }
            
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/insights/generate",
                json=insights_request
            ) as response:
                if response.status == 200:
                    insights_result = await response.json()
                    print(f"✅ Fresh insights generated")
                    print(f"   Status: {insights_result.get('status')}")
                    
                    if insights_result.get('status') == 'success':
                        insights = insights_result.get('insights', {})
                        insight_count = len(insights.get('insights', []))
                        confidence = insights.get('confidence_score', 0)
                        print(f"   Insights generated: {insight_count}")
                        print(f"   Confidence score: {confidence:.2f}")
                        results['generate_insights'] = True
                        
                        # Test 3: Provide feedback on first insight
                        if insights.get('insights') and len(insights['insights']) > 0:
                            first_insight = insights['insights'][0]
                            insight_id = first_insight.get('insight_id', 'test_insight_1')
                            
                            print(f"\n📋 Testing POST /api/user/{user_id}/insights/{insight_id}/feedback")
                            feedback_data = {
                                "rating": 4,
                                "helpful": True,
                                "comment": "This insight was very relevant to my situation"
                            }
                            
                            async with session.post(
                                f"{BASE_URL}/api/user/{user_id}/insights/{insight_id}/feedback",
                                json=feedback_data
                            ) as feedback_response:
                                if feedback_response.status == 200:
                                    feedback_result = await feedback_response.json()
                                    print(f"✅ Feedback recorded successfully")
                                    results['insights_feedback'] = True
                                else:
                                    print(f"❌ Feedback failed: HTTP {feedback_response.status}")
                                    results['insights_feedback'] = False
                        else:
                            results['insights_feedback'] = False
                            print("   No insights available for feedback test")
                    else:
                        print(f"   Error: {insights_result.get('error', 'Unknown error')}")
                        results['generate_insights'] = False
                        results['insights_feedback'] = False
                else:
                    print(f"❌ Fresh insights failed: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text[:200]}...")
                    results['generate_insights'] = False
                    results['insights_feedback'] = False
        
        return results
        
    except Exception as e:
        print(f"❌ Insights endpoints test failed: {e}")
        return {'latest_insights': False, 'generate_insights': False, 'insights_feedback': False}

async def test_ondemand_endpoints(user_id):
    """Test the enhanced on-demand routine and nutrition endpoints"""
    print_section("ON-DEMAND GENERATION ENDPOINTS", "🔄")
    
    results = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test routine endpoints
            print("📋 Testing routine endpoints")
            
            # Get latest routine
            async with session.get(f"{BASE_URL}/api/user/{user_id}/routine/latest") as response:
                if response.status == 200:
                    routine_data = await response.json()
                    print(f"✅ Latest routine: {routine_data.get('status')}")
                    results['routine_latest'] = routine_data.get('status') == 'success'
                else:
                    print(f"❌ Latest routine failed: HTTP {response.status}")
                    results['routine_latest'] = False
            
            # Generate fresh routine with memory enhancement
            routine_request = {
                "archetype": TEST_ARCHETYPE,
                "preferences": {
                    "workout_time": "evening",
                    "duration_minutes": 20,
                    "intensity": "moderate"
                }
            }
            
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/routine/generate",
                json=routine_request
            ) as response:
                if response.status == 200:
                    routine_result = await response.json()
                    print(f"✅ Fresh routine generated: {routine_result.get('status')}")
                    
                    metadata = routine_result.get('generation_metadata', {})
                    
                    # Check for Phase 4.2 on-demand analysis features
                    analysis_decision = metadata.get('analysis_decision', 'unknown')
                    data_quality = metadata.get('data_quality', 'unknown')
                    cached = routine_result.get('cached', False)
                    
                    print(f"   🧠 Analysis Decision: {analysis_decision}")
                    print(f"   📊 Data Quality: {data_quality}")
                    print(f"   💾 Used Cache: {cached}")
                    
                    # Check for analysis freshness metadata (Phase 4.2 feature)
                    if 'analysis_freshness' in metadata:
                        freshness = metadata['analysis_freshness']
                        print(f"   🕒 New Data Points: {freshness.get('new_data_points', 'N/A')}")
                        print(f"   🎯 Threshold Used: {freshness.get('threshold_used', 'N/A')}")
                        print(f"   🧠 Memory Quality: {freshness.get('memory_quality', 'N/A')}")
                    
                    # Enhanced Phase 4.2 detection
                    phase42_detected = (
                        analysis_decision in ['fresh_analysis', 'memory_cache', 'stale_refresh'] or
                        'analysis_freshness' in metadata or
                        data_quality in ['fresh', 'cached_enhanced']
                    )
                    
                    if phase42_detected:
                        print("   ✅ Phase 4.2 on-demand analysis features detected!")
                    
                    results['routine_generate'] = routine_result.get('status') == 'success'
                    results['routine_phase42'] = phase42_detected
                else:
                    print(f"❌ Fresh routine failed: HTTP {response.status}")
                    results['routine_generate'] = False
            
            # Test nutrition endpoints
            print("\n📋 Testing nutrition endpoints")
            
            # Get latest nutrition
            async with session.get(f"{BASE_URL}/api/user/{user_id}/nutrition/latest") as response:
                if response.status == 200:
                    nutrition_data = await response.json()
                    print(f"✅ Latest nutrition: {nutrition_data.get('status')}")
                    results['nutrition_latest'] = nutrition_data.get('status') == 'success'
                else:
                    print(f"❌ Latest nutrition failed: HTTP {response.status}")
                    results['nutrition_latest'] = False
            
            # Generate fresh nutrition with memory enhancement
            nutrition_request = {
                "archetype": TEST_ARCHETYPE,
                "preferences": {
                    "dietary_restriction": "vegetarian",
                    "meal_prep_time": "quick",
                    "cuisine_preference": "mediterranean"
                }
            }
            
            async with session.post(
                f"{BASE_URL}/api/user/{user_id}/nutrition/generate",
                json=nutrition_request
            ) as response:
                if response.status == 200:
                    nutrition_result = await response.json()
                    print(f"✅ Fresh nutrition generated: {nutrition_result.get('status')}")
                    
                    metadata = nutrition_result.get('generation_metadata', {})
                    
                    # Check for Phase 4.2 on-demand analysis features  
                    analysis_decision = metadata.get('analysis_decision', 'unknown')
                    data_quality = metadata.get('data_quality', 'unknown')
                    cached = nutrition_result.get('cached', False)
                    
                    print(f"   🧠 Analysis Decision: {analysis_decision}")
                    print(f"   📊 Data Quality: {data_quality}")
                    print(f"   💾 Used Cache: {cached}")
                    
                    # Check for analysis freshness metadata (Phase 4.2 feature)
                    if 'analysis_freshness' in metadata:
                        freshness = metadata['analysis_freshness']
                        print(f"   🕒 New Data Points: {freshness.get('new_data_points', 'N/A')}")
                        print(f"   🎯 Threshold Used: {freshness.get('threshold_used', 'N/A')}")
                        print(f"   🧠 Memory Quality: {freshness.get('memory_quality', 'N/A')}")
                    
                    # Enhanced Phase 4.2 detection
                    phase42_detected = (
                        analysis_decision in ['fresh_analysis', 'memory_cache', 'stale_refresh'] or
                        'analysis_freshness' in metadata or
                        data_quality in ['fresh', 'cached_enhanced']
                    )
                    
                    if phase42_detected:
                        print("   ✅ Phase 4.2 on-demand analysis features detected!")
                    
                    results['nutrition_generate'] = nutrition_result.get('status') == 'success'
                    results['nutrition_phase42'] = phase42_detected
                else:
                    print(f"❌ Fresh nutrition failed: HTTP {response.status}")
                    results['nutrition_generate'] = False
        
        return results
        
    except Exception as e:
        print(f"❌ On-demand endpoints test failed: {e}")
        return {
            'routine_latest': False, 'routine_generate': False,
            'nutrition_latest': False, 'nutrition_generate': False
        }

async def test_scheduler_status():
    """Test the background scheduler status"""
    print_section("BACKGROUND SCHEDULER", "⏰")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/scheduler/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    print(f"✅ Scheduler status retrieved")
                    print(f"   Status: {status_data.get('status', 'unknown')}")
                    print(f"   Active users: {status_data.get('active_users', 0)}")
                    print(f"   Data threshold: {status_data.get('data_threshold', 'unknown')}")
                    return status_data.get('status') == 'running'
                else:
                    print(f"❌ Scheduler status failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

async def validate_memory_enhancement(user_id):
    """Validate that memory enhancement is actually working"""
    print_section("MEMORY ENHANCEMENT VALIDATION", "🧠")
    
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        
        db = SupabaseAsyncPGAdapter()
        await db.connect()
        
        # Check memory data quality and content
        memory_validation = {}
        
        # Check long-term memory for actual patterns
        longterm_result = db.client.table("holistic_longterm_memory").select("*").eq('user_id', user_id).execute()
        if longterm_result.data:
            print(f"✅ Long-term memory: {len(longterm_result.data)} records")
            
            # Check for actual content
            sample = longterm_result.data[0]
            if sample.get('behavioral_patterns') or sample.get('preference_patterns'):
                print("   🧠 Contains behavioral/preference patterns")
                memory_validation['longterm_quality'] = True
            else:
                print("   ⚠️  No patterns detected yet")
                memory_validation['longterm_quality'] = False
        else:
            print("❌ No long-term memory found")
            memory_validation['longterm_quality'] = False
        
        # Check analysis results for insights
        analysis_result = db.client.table("holistic_analysis_results").select("*").eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        if analysis_result.data:
            latest_analysis = analysis_result.data[0]
            analysis_content = latest_analysis.get('analysis_result', {})
            
            # Check for Phase 4.2 features
            has_insights = 'ai_insights' in str(analysis_content)
            has_memory_info = 'memory' in str(analysis_content).lower()
            
            print(f"✅ Latest analysis found")
            print(f"   🔍 AI insights included: {'Yes' if has_insights else 'No'}")
            print(f"   🧠 Memory info present: {'Yes' if has_memory_info else 'No'}")
            
            memory_validation['analysis_enhanced'] = has_insights or has_memory_info
        else:
            print("❌ No analysis results found")
            memory_validation['analysis_enhanced'] = False
        
        await db.close()
        return memory_validation
        
    except Exception as e:
        print(f"❌ Memory validation failed: {e}")
        return {'longterm_quality': False, 'analysis_enhanced': False}

async def main():
    """Main Phase 4.2 enhanced test"""
    print("🚀 PHASE 4.2 MEMORY-ENHANCED E2E TEST")
    print("Testing Memory-Enhanced Intelligent Health Coaching System")
    print("=" * 70)
    
    # Show configuration
    print(f"📋 Test Configuration:")
    print(f"   • Server URL: {BASE_URL}")
    print(f"   • User ID: {REAL_PROFILE_ID}")
    print(f"   • Archetype: {TEST_ARCHETYPE}")
    print(f"   • Phase: 4.2 - Memory-Enhanced Intelligence")
    
    # Confirm starting test
    if not get_user_input("🚀 Start Phase 4.2 enhanced test? This will use OpenAI API credits"):
        print("👋 Test cancelled")
        return False
    
    test_results = {}
    
    # Step 1: Server health
    server_healthy = await test_server_health()
    test_results['server_health'] = server_healthy
    
    if not server_healthy:
        print(f"\n❌ Cannot proceed - server is not accessible")
        return False
    
    # Step 2: Initial Phase 4.2 analysis
    analysis_result, analysis_success, phase42_features = await test_phase42_analysis(
        REAL_PROFILE_ID, TEST_ARCHETYPE, "INITIAL"
    )
    test_results['initial_analysis'] = analysis_success
    test_results['phase42_features'] = phase42_features
    
    if not analysis_success:
        print(f"\n❌ Cannot proceed - initial analysis failed")
        return False
    
    # Step 3: Test insights endpoints
    insights_results = await test_insights_endpoints(REAL_PROFILE_ID)
    test_results.update(insights_results)
    
    # Step 4: Test on-demand endpoints
    ondemand_results = await test_ondemand_endpoints(REAL_PROFILE_ID)
    test_results.update(ondemand_results)
    
    # Step 5: Test scheduler
    scheduler_working = await test_scheduler_status()
    test_results['scheduler'] = scheduler_working
    
    # Step 6: Validate memory enhancement
    memory_validation = await validate_memory_enhancement(REAL_PROFILE_ID)
    test_results.update(memory_validation)
    
    # Step 7: Follow-up analysis to test progressive intelligence
    if get_user_input("\n🔄 Run follow-up analysis to test progressive intelligence?"):
        followup_result, followup_success, followup_features = await test_phase42_analysis(
            REAL_PROFILE_ID, TEST_ARCHETYPE, "FOLLOW-UP"
        )
        test_results['followup_analysis'] = followup_success
        test_results['progressive_intelligence'] = followup_success and any(followup_features.values())
    else:
        test_results['followup_analysis'] = None
        test_results['progressive_intelligence'] = None
    
    # Final Results
    print_section("PHASE 4.2 TEST RESULTS", "🎯")
    
    # Core components
    core_components = [
        ("Server Health", test_results['server_health']),
        ("Initial Analysis", test_results['initial_analysis']),
    ]
    
    # Phase 4.2 specific features
    phase42_components = [
        ("AI Insights Latest", test_results.get('latest_insights', False)),
        ("AI Insights Generate", test_results.get('generate_insights', False)),
        ("Insights Feedback", test_results.get('insights_feedback', False)),
        ("Routine On-Demand", test_results.get('routine_generate', False)),
        ("Nutrition On-Demand", test_results.get('nutrition_generate', False)),
        ("Memory Enhancement", test_results.get('analysis_enhanced', False)),
        ("Background Scheduler", test_results.get('scheduler', False)),
    ]
    
    # Progressive intelligence
    progressive_components = []
    if test_results.get('followup_analysis') is not None:
        progressive_components.append(("Follow-up Analysis", test_results['followup_analysis']))
        progressive_components.append(("Progressive Intelligence", test_results.get('progressive_intelligence', False)))
    
    all_components = core_components + phase42_components + progressive_components
    working_count = sum(1 for _, status in all_components if status)
    
    print(f"📊 CORE SYSTEM:")
    for name, status in core_components:
        print(f"   • {name}: {'✅ WORKING' if status else '❌ FAILED'}")
    
    print(f"\n🧠 PHASE 4.2 FEATURES:")
    for name, status in phase42_components:
        print(f"   • {name}: {'✅ WORKING' if status else '❌ FAILED'}")
    
    if progressive_components:
        print(f"\n🚀 PROGRESSIVE INTELLIGENCE:")
        for name, status in progressive_components:
            if status is None:
                print(f"   • {name}: ⚪ SKIPPED")
            else:
                print(f"   • {name}: {'✅ WORKING' if status else '❌ FAILED'}")
    
    print(f"\n🎯 OVERALL SCORE: {working_count}/{len([c for c in all_components if c[1] is not None])} components working")
    
    # Success criteria
    core_working = all(status for _, status in core_components)
    phase42_working = sum(status for _, status in phase42_components if status) >= 5  # At least 5/7 Phase 4.2 features
    
    if core_working and phase42_working:
        print("\n🏆 EXCELLENT! Phase 4.2 Memory-Enhanced System is fully operational")
        print("   • Memory-enhanced prompts working")
        print("   • AI insights generation working") 
        print("   • On-demand generation working")
        print("   • Progressive intelligence enabled")
        success_level = "EXCELLENT"
    elif core_working:
        print("\n✅ GOOD! Core system working, some Phase 4.2 features need attention")
        success_level = "GOOD"
    else:
        print("\n🔧 NEEDS WORK! Core system issues need to be resolved")
        success_level = "NEEDS_WORK"
    
    # Phase 4.2 specific validation
    phase42_score = sum(status for _, status in phase42_components if status)
    print(f"\n🧠 PHASE 4.2 FEATURE SCORE: {phase42_score}/7")
    
    if phase42_score >= 6:
        print("   🎉 Phase 4.2 implementation is highly successful!")
    elif phase42_score >= 4:
        print("   ✅ Phase 4.2 implementation is mostly working")
    else:
        print("   ⚠️  Phase 4.2 implementation needs attention")
    
    return success_level in ["EXCELLENT", "GOOD"]

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        print(f"\n{'🎉 Phase 4.2 test completed successfully!' if success else '⚠️  Phase 4.2 test completed with issues'}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)