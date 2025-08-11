#!/usr/bin/env python3
"""
Real Profile Health Data Testing - Save Retrieved Data to Files
CTO Implementation: Test with real profile ID and comprehensive data logging
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

def save_response_to_file(endpoint_name: str, response_data: dict, status_code: int):
    """Save endpoint response to a text file"""
    timestamp = datetime.now().isoformat()
    filename = f"{TEST_TIMESTAMP}_{endpoint_name}_{REAL_PROFILE_ID}.json"
    filepath = LOGS_DIR / filename
    
    # Prepare data for saving
    file_data = {
        "timestamp": timestamp,
        "endpoint": endpoint_name,
        "profile_id": REAL_PROFILE_ID,
        "status_code": status_code,
        "response_data": response_data,
        "success": status_code == 200,
        "test_session": TEST_TIMESTAMP
    }
    
    # Save to file with pretty formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"💾 Saved {endpoint_name} data to: {filename}")
    return filepath

async def test_real_profile_endpoints():
    """Test all endpoints with real profile ID and save data to files"""
    print("\n" + "="*80)
    print(f"REAL PROFILE HEALTH DATA TESTING - {TEST_TIMESTAMP}")
    print(f"Profile ID: {REAL_PROFILE_ID}")
    print("="*80)
    
    ensure_logs_directory()
    
    # Create test app
    app = FastAPI(title="Real Profile Health Data Testing", version="1.0.0")
    
    try:
        # Integrate endpoints
        print("\n[SETUP] Integrating health data endpoints...")
        integration_success = integrate_health_data_endpoints(app)
        
        if not integration_success:
            print("❌ Failed to integrate endpoints")
            return False
        
        print("✅ Endpoints integrated successfully")
        
        # Test results tracking
        test_results = []
        
        # Create test client
        with TestClient(app) as client:
            
            # 1. Test system health check
            print("\n[TEST 1/6] System Health Check...")
            try:
                response = client.get("/api/v1/health-data/system/health")
                data = response.json() if response.status_code == 200 else {"error": response.text}
                
                filepath = save_response_to_file("system_health", data, response.status_code)
                
                if response.status_code == 200:
                    print(f"✅ System Status: {data['data']['system_status']}")
                    print(f"   Database: {data['data']['database_status']}")
                    print(f"   API Client: {data['data']['api_client_status']}")
                    test_results.append(("System Health", True))
                else:
                    print(f"❌ System health check failed: {response.status_code}")
                    test_results.append(("System Health", False))
                    
            except Exception as e:
                print(f"💥 System health test crashed: {e}")
                test_results.append(("System Health", False))
            
            # 2. Test complete user health context
            print(f"\n[TEST 2/6] Complete Health Context for {REAL_PROFILE_ID}...")
            try:
                response = client.get(f"/api/v1/health-data/users/{REAL_PROFILE_ID}/health-context?days=7&include_agent_views=true")
                data = response.json() if response.status_code == 200 else {"error": response.text}
                
                filepath = save_response_to_file("health_context", data, response.status_code)
                
                if response.status_code == 200:
                    quality = data['data']['data_quality']
                    agent_readiness = data['data'].get('agent_readiness', {})
                    ready_count = sum(1 for ready in agent_readiness.values() if ready)
                    
                    print(f"✅ Data Retrieved Successfully!")
                    print(f"   Quality Level: {quality['quality_level']}")
                    print(f"   Completeness: {quality['completeness_score']:.2f}")
                    print(f"   Scores Count: {quality['scores_count']}")
                    print(f"   Biomarkers Count: {quality['biomarkers_count']}")
                    print(f"   Ready Agents: {ready_count}/6")
                    print(f"   Agent Views: {'agent_views' in data['data']}")
                    test_results.append(("Health Context", True))
                else:
                    print(f"❌ Health context failed: {response.status_code}")
                    print(f"   Error: {data.get('error', 'Unknown error')}")
                    test_results.append(("Health Context", False))
                    
            except Exception as e:
                print(f"💥 Health context test crashed: {e}")
                test_results.append(("Health Context", False))
            
            # 3. Test user health summary
            print(f"\n[TEST 3/6] Health Summary for {REAL_PROFILE_ID}...")
            try:
                response = client.get(f"/api/v1/health-data/users/{REAL_PROFILE_ID}/summary")
                data = response.json() if response.status_code == 200 else {"error": response.text}
                
                filepath = save_response_to_file("health_summary", data, response.status_code)
                
                if response.status_code == 200:
                    ready_agents = sum(1 for ready in data['agent_readiness'].values() if ready)
                    print(f"✅ Summary Retrieved!")
                    print(f"   Data Quality: {data['data_quality']}")
                    print(f"   Latest Scores: {len(data['latest_scores'])}")
                    print(f"   Current Archetype: {data.get('archetype', 'None')}")
                    print(f"   Ready Agents: {ready_agents}/6")
                    test_results.append(("Health Summary", True))
                else:
                    print(f"❌ Health summary failed: {response.status_code}")
                    test_results.append(("Health Summary", False))
                    
            except Exception as e:
                print(f"💥 Health summary test crashed: {e}")
                test_results.append(("Health Summary", False))
            
            # 4. Test data quality assessment
            print(f"\n[TEST 4/6] Data Quality Assessment for {REAL_PROFILE_ID}...")
            try:
                response = client.get(f"/api/v1/health-data/users/{REAL_PROFILE_ID}/data-quality?days=7")
                data = response.json() if response.status_code == 200 else {"error": response.text}
                
                filepath = save_response_to_file("data_quality", data, response.status_code)
                
                if response.status_code == 200:
                    print(f"✅ Data Quality Assessment!")
                    print(f"   Quality Level: {data['quality_level']}")
                    print(f"   Completeness Score: {data['completeness_score']:.2f}")
                    print(f"   Scores: {data['scores_count']}, Biomarkers: {data['biomarkers_count']}")
                    print(f"   Recent Data: {data['has_recent_data']}")
                    print(f"   Recommendations: {len(data['recommendations'])}")
                    for rec in data['recommendations']:
                        print(f"     • {rec}")
                    test_results.append(("Data Quality", True))
                else:
                    print(f"❌ Data quality assessment failed: {response.status_code}")
                    test_results.append(("Data Quality", False))
                    
            except Exception as e:
                print(f"💥 Data quality test crashed: {e}")
                test_results.append(("Data Quality", False))
            
            # 5. Test all agent-specific data endpoints
            print(f"\n[TEST 5/6] Agent-Specific Data for {REAL_PROFILE_ID}...")
            agents = ["behavior", "memory", "nutrition", "routine", "adaptation", "insights"]
            agent_results = {}
            
            for agent in agents:
                try:
                    response = client.get(f"/api/v1/health-data/users/{REAL_PROFILE_ID}/agent/{agent}/data?days=7")
                    data = response.json() if response.status_code == 200 else {"error": response.text}
                    
                    # Save each agent's data to separate file
                    filepath = save_response_to_file(f"agent_{agent}", data, response.status_code)
                    
                    if response.status_code == 200:
                        is_ready = data['data']['is_ready']
                        agent_data = data['data']['agent_data']
                        print(f"   • {agent.capitalize()}: {'✅ Ready' if is_ready else '⚠️  Not Ready'} - {len(str(agent_data))} chars data")
                        agent_results[agent] = True
                    else:
                        print(f"   • {agent.capitalize()}: ❌ Error {response.status_code}")
                        agent_results[agent] = False
                        
                except Exception as e:
                    print(f"   • {agent.capitalize()}: 💥 Exception {e}")
                    agent_results[agent] = False
            
            agent_success_count = sum(1 for success in agent_results.values() if success)
            print(f"✅ Agent endpoints working: {agent_success_count}/6")
            test_results.append(("Agent Data", agent_success_count == 6))
            
            # 6. Test analysis trigger
            print(f"\n[TEST 6/6] Analysis Trigger for {REAL_PROFILE_ID}...")
            try:
                request_body = {
                    "archetype": "Foundation Builder",
                    "analysis_type": "complete",
                    "days": 7,
                    "priority": "normal"
                }
                response = client.post(f"/api/v1/health-data/users/{REAL_PROFILE_ID}/analyze", json=request_body)
                data = response.json() if response.status_code == 200 else {"error": response.text}
                
                filepath = save_response_to_file("analysis_trigger", data, response.status_code)
                
                if response.status_code == 200:
                    analysis_data = data['data']
                    print(f"✅ Analysis Triggered!")
                    print(f"   Analysis ID: {analysis_data['analysis_id']}")
                    print(f"   Status: {analysis_data['status']}")
                    print(f"   User Data Summary:")
                    summary = analysis_data['user_data_summary']
                    print(f"     - Scores: {summary['scores_count']}")
                    print(f"     - Biomarkers: {summary['biomarkers_count']}")
                    print(f"     - Quality: {summary['data_quality']}")
                    print(f"     - Ready Agents: {summary['ready_agents']}/{summary['total_agents']}")
                    test_results.append(("Analysis Trigger", True))
                else:
                    print(f"❌ Analysis trigger failed: {response.status_code}")
                    test_results.append(("Analysis Trigger", False))
                    
            except Exception as e:
                print(f"💥 Analysis trigger test crashed: {e}")
                test_results.append(("Analysis Trigger", False))
        
        return test_results
        
    except Exception as e:
        print(f"❌ Real profile endpoint testing failed: {e}")
        return []

def create_test_summary_file(test_results):
    """Create a comprehensive summary file"""
    summary_data = {
        "test_session": TEST_TIMESTAMP,
        "profile_id": REAL_PROFILE_ID,
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results,
        "passed_tests": sum(1 for _, result in test_results if result),
        "total_tests": len(test_results),
        "success_rate": f"{(sum(1 for _, result in test_results if result) / len(test_results) * 100):.1f}%" if test_results else "0%",
        "files_saved": list(LOGS_DIR.glob(f"{TEST_TIMESTAMP}*.json")),
        "logs_directory": str(LOGS_DIR.absolute())
    }
    
    summary_file = LOGS_DIR / f"{TEST_TIMESTAMP}_SUMMARY.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, default=str, ensure_ascii=False)
    
    return summary_file

async def main():
    """Main test runner for real profile testing"""
    print("🚀 HOLISTICOS MVP - REAL PROFILE TESTING")
    print(f"Profile ID: {REAL_PROFILE_ID}")
    print("Comprehensive health data retrieval and logging")
    
    start_time = datetime.now()
    
    # Run real profile tests
    test_results = await test_real_profile_endpoints()
    
    # Create summary
    summary_file = create_test_summary_file(test_results)
    
    # Final summary
    print("\n" + "="*80)
    print("REAL PROFILE TEST RESULTS SUMMARY")
    print("="*80)
    
    if test_results:
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Profile ID: {REAL_PROFILE_ID}")
        print(f"Data saved to: {LOGS_DIR.absolute()}")
        
        # List saved files
        saved_files = list(LOGS_DIR.glob(f"{TEST_TIMESTAMP}*.json"))
        print(f"\n📁 Files Created ({len(saved_files)}):")
        for file in saved_files:
            file_size = file.stat().st_size
            print(f"   • {file.name} ({file_size:,} bytes)")
        
        print(f"\n📊 Summary Report: {summary_file.name}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Real user data retrieved successfully!")
            print("\n✅ Real Profile Data Available:")
            print("   • Complete health context with agent views")
            print("   • Health summary with latest scores")
            print("   • Data quality assessment with recommendations")
            print("   • Individual agent data for all 6 agents")
            print("   • Analysis trigger ready for orchestrator")
            print("   • System health monitoring working")
            print(f"\n📂 All data saved to: {LOGS_DIR.absolute()}")
            print("   Open the JSON files to examine the real user health data!")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check individual JSON files for details.")
            return False
    else:
        print("\n❌ No test results available")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)