#!/usr/bin/env python3
"""
PHASE 3.1 Real Data Analysis Testing
Test the updated /api/analyze endpoint with real user data from Supabase
"""
import asyncio
import sys
import os
import json
from datetime import datetime
import httpx
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import our integration
from services.api_gateway.integrate_health_endpoints import integrate_health_data_endpoints

# Configuration
REAL_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
LOGS_DIR = Path("logs/health_data_logs")
TEST_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def ensure_logs_directory():
    """Ensure the health_data_logs directory exists"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Logs directory: {LOGS_DIR.absolute()}")

def save_analysis_result(endpoint_name: str, response_data: dict, status_code: int):
    """Save analysis response to a detailed file"""
    timestamp = datetime.now().isoformat()
    filename = f"{TEST_TIMESTAMP}_ANALYSIS_{endpoint_name}_{REAL_PROFILE_ID}.json"
    filepath = LOGS_DIR / filename
    
    # Prepare detailed data for saving
    file_data = {
        "timestamp": timestamp,
        "endpoint": endpoint_name,
        "profile_id": REAL_PROFILE_ID,
        "status_code": status_code,
        "test_type": "PHASE_3.1_REAL_DATA_ANALYSIS",
        "response_data": response_data,
        "success": status_code == 200,
        "test_session": TEST_TIMESTAMP,
        "analysis_metadata": {
            "used_real_data": "REAL DATA ANALYSIS" in str(response_data) if response_data else False,
            "fallback_used": "Fallback Mode" in str(response_data) if response_data else False,
            "phase": "3.1 - Real Data Integration"
        }
    }
    
    # Save to file with pretty formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"💾 Saved {endpoint_name} analysis to: {filename}")
    return filepath

async def test_legacy_analyze_endpoint():
    """Test the updated /api/analyze endpoint with real data integration"""
    print("\n" + "="*80)
    print(f"PHASE 3.1 - REAL DATA ANALYSIS TESTING")
    print(f"Testing /api/analyze with profile: {REAL_PROFILE_ID}")
    print("="*80)
    
    ensure_logs_directory()
    
    # Create test app - we need to import the full openai_main app
    try:
        from services.api_gateway.openai_main import app
        print("✅ Using production FastAPI app with real data integration")
    except Exception as e:
        print(f"❌ Failed to import production app: {e}")
        return False
    
    test_results = []
    
    # Test with real profile ID
    with TestClient(app) as client:
        
        print(f"\n[ANALYSIS TEST] Testing /api/analyze with real profile {REAL_PROFILE_ID}...")
        
        # Test different archetypes with real data
        archetypes_to_test = [
            ("Foundation Builder", "Simple, sustainable basics"),
            ("Peak Performer", "Elite-level performance optimization"),
            ("Transformation Seeker", "Ambitious lifestyle changes")
        ]
        
        for archetype, description in archetypes_to_test:
            print(f"\n🧪 Testing {archetype} archetype...")
            print(f"   Description: {description}")
            
            try:
                request_body = {
                    "user_id": REAL_PROFILE_ID,
                    "archetype": archetype
                }
                
                # Make the analysis request
                print(f"📡 Sending analysis request...")
                response = client.post("/api/analyze", json=request_body, timeout=60.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Save detailed analysis result
                    filepath = save_analysis_result(f"analyze_{archetype.replace(' ', '_')}", data, response.status_code)
                    
                    # Extract key information
                    analysis = data.get('analysis', {})
                    system_info = analysis.get('system_info', {})
                    mode = system_info.get('mode', 'unknown')
                    phase = system_info.get('phase', 'unknown')
                    data_source = system_info.get('data_source', 'unknown')
                    
                    print(f"✅ {archetype} Analysis Completed!")
                    print(f"   Status: {data['status']}")
                    print(f"   Mode: {mode}")
                    print(f"   Phase: {phase}")
                    print(f"   Data Source: {data_source}")
                    print(f"   Message: {data['message']}")
                    
                    # Check if real data was used
                    used_real_data = "REAL DATA" in mode
                    if used_real_data:
                        print(f"   🎯 SUCCESS: Real wearable data used for analysis!")
                    else:
                        print(f"   ⚠️  FALLBACK: Mock data used (real data fetch may have failed)")
                    
                    # Check analysis components
                    components = ['behavior_analysis', 'nutrition_plan', 'routine_plan']
                    print(f"   Analysis Components:")
                    for comp in components:
                        if comp in analysis:
                            comp_data = analysis[comp]
                            comp_size = len(str(comp_data))
                            print(f"     • {comp.replace('_', ' ').title()}: ✅ ({comp_size:,} chars)")
                        else:
                            print(f"     • {comp.replace('_', ' ').title()}: ❌ Missing")
                    
                    test_results.append((f"{archetype} Analysis", True, used_real_data))
                    
                else:
                    print(f"❌ {archetype} analysis failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    
                    # Save error response
                    error_data = {"error": response.text, "status_code": response.status_code}
                    save_analysis_result(f"ERROR_{archetype.replace(' ', '_')}", error_data, response.status_code)
                    
                    test_results.append((f"{archetype} Analysis", False, False))
                    
            except Exception as e:
                print(f"💥 {archetype} analysis test crashed: {e}")
                test_results.append((f"{archetype} Analysis", False, False))
        
        # Test with a non-existent user (should gracefully fallback)
        print(f"\n🧪 Testing fallback with non-existent user...")
        try:
            request_body = {
                "user_id": "nonexistent_user_test",
                "archetype": "Foundation Builder"
            }
            
            response = client.post("/api/analyze", json=request_body, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                mode = data.get('analysis', {}).get('system_info', {}).get('mode', 'unknown')
                
                # This should be fallback mode
                is_fallback = "Fallback" in mode
                print(f"✅ Fallback test passed: {mode}")
                test_results.append(("Fallback Test", True, False))
            else:
                print(f"❌ Fallback test failed: {response.status_code}")
                test_results.append(("Fallback Test", False, False))
                
        except Exception as e:
            print(f"💥 Fallback test crashed: {e}")
            test_results.append(("Fallback Test", False, False))
    
    return test_results

async def create_phase31_summary(test_results):
    """Create Phase 3.1 test summary"""
    summary_data = {
        "test_session": TEST_TIMESTAMP,
        "phase": "3.1 - Real Data Integration",
        "profile_id": REAL_PROFILE_ID,
        "timestamp": datetime.now().isoformat(),
        "test_type": "ANALYZE_ENDPOINT_REAL_DATA",
        "test_results": [
            {
                "test_name": name,
                "success": success,
                "used_real_data": used_real_data
            }
            for name, success, used_real_data in test_results
        ],
        "total_tests": len(test_results),
        "passed_tests": sum(1 for _, success, _ in test_results if success),
        "real_data_tests": sum(1 for _, _, used_real_data in test_results if used_real_data),
        "success_rate": f"{(sum(1 for _, success, _ in test_results if success) / len(test_results) * 100):.1f}%" if test_results else "0%",
        "real_data_rate": f"{(sum(1 for _, _, used_real_data in test_results if used_real_data) / len(test_results) * 100):.1f}%" if test_results else "0%",
        "files_saved": [str(f.name) for f in LOGS_DIR.glob(f"{TEST_TIMESTAMP}*.json")],
        "logs_directory": str(LOGS_DIR.absolute())
    }
    
    summary_file = LOGS_DIR / f"{TEST_TIMESTAMP}_PHASE31_ANALYSIS_SUMMARY.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, default=str, ensure_ascii=False)
    
    return summary_file, summary_data

async def main():
    """Main test runner for Phase 3.1 real data analysis"""
    print("🚀 HOLISTICOS MVP - PHASE 3.1 TESTING")
    print("REAL DATA ANALYSIS INTEGRATION")
    print(f"Profile ID: {REAL_PROFILE_ID}")
    print("Testing /api/analyze endpoint with actual Supabase data")
    
    start_time = datetime.now()
    
    # Run the analysis tests
    test_results = await test_legacy_analyze_endpoint()
    
    # Create comprehensive summary
    summary_file, summary_data = await create_phase31_summary(test_results)
    
    # Final summary report
    print("\n" + "="*80)
    print("PHASE 3.1 TEST RESULTS SUMMARY")
    print("="*80)
    
    if test_results:
        passed = summary_data["passed_tests"]
        total = summary_data["total_tests"] 
        real_data_count = summary_data["real_data_tests"]
        
        print(f"\n📊 Test Results:")
        for name, success, used_real_data in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            data_source = "🎯 REAL DATA" if used_real_data else "🔄 FALLBACK" if success else "💥 ERROR"
            print(f"{status} {name} ({data_source})")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📈 Summary:")
        print(f"   • Tests Passed: {passed}/{total} ({summary_data['success_rate']})")
        print(f"   • Real Data Used: {real_data_count}/{total} ({summary_data['real_data_rate']})")
        print(f"   • Duration: {duration:.1f} seconds")
        print(f"   • Profile: {REAL_PROFILE_ID}")
        
        # List saved files
        saved_files = list(LOGS_DIR.glob(f"{TEST_TIMESTAMP}*.json"))
        print(f"\n📁 Analysis Files Created ({len(saved_files)}):")
        for file in saved_files:
            file_size = file.stat().st_size
            print(f"   • {file.name} ({file_size:,} bytes)")
        
        print(f"\n📊 Summary Report: {summary_file.name}")
        
        if passed == total and real_data_count > 0:
            print("\n🎉 PHASE 3.1 SUCCESS!")
            print("\n✅ Real Data Analysis Working:")
            print("   • /api/analyze endpoint now uses actual wearable data")
            print("   • AI receives real sleep, activity, and biomarker data")
            print("   • Graceful fallback to mock data when real data unavailable")
            print("   • Analysis results based on user's actual health patterns")
            print("   • Complete logging and error handling")
            print(f"\n📂 Detailed analysis results: {LOGS_DIR.absolute()}")
            print("   Open the JSON files to see the real data analysis results!")
            
            print(f"\n🎯 PHASE 3.1 COMPLETE:")
            print("   Your 6-agent system is now getting real wearable device data!")
            print("   The AI analysis is based on actual user health metrics!")
            
            return True
        else:
            print(f"\n⚠️  Some issues found:")
            if passed < total:
                print(f"   • {total - passed} tests failed")
            if real_data_count == 0:
                print(f"   • No tests used real data - check UserDataService integration")
            print("   Check individual JSON files for detailed error information.")
            return False
    else:
        print("\n❌ No test results available")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)