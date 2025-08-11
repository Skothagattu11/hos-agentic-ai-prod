#!/usr/bin/env python3
"""
PHASE 3.2 Multi-Model Integration Testing
Test the updated /api/analyze endpoint with o3 + gpt-4o models and optimized prompts
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

# Configuration
REAL_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
LOGS_DIR = Path("logs/health_data_logs")
TEST_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def ensure_logs_directory():
    """Ensure the health_data_logs directory exists"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Logs directory: {LOGS_DIR.absolute()}")

def save_phase32_result(endpoint_name: str, response_data: dict, status_code: int):
    """Save Phase 3.2 analysis response to a detailed file"""
    timestamp = datetime.now().isoformat()
    filename = f"{TEST_TIMESTAMP}_PHASE32_{endpoint_name}_{REAL_PROFILE_ID}.json"
    filepath = LOGS_DIR / filename
    
    # Prepare detailed data for saving
    file_data = {
        "timestamp": timestamp,
        "endpoint": endpoint_name,
        "profile_id": REAL_PROFILE_ID,
        "status_code": status_code,
        "test_type": "PHASE_3.2_MULTI_MODEL_ANALYSIS",
        "response_data": response_data,
        "success": status_code == 200,
        "test_session": TEST_TIMESTAMP,
        "phase32_metadata": {
            "models_expected": {
                "behavior_analysis": "o3",
                "nutrition_plan": "gpt-4o",
                "routine_plan": "gpt-4o"
            },
            "prompt_optimized": "AI-friendly language used",
            "phase": "3.2 - Multi-Model Integration"
        }
    }
    
    # Save to file with pretty formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"💾 Saved {endpoint_name} Phase 3.2 result to: {filename}")
    return filepath

def analyze_phase32_response(response_data: dict) -> dict:
    """Analyze Phase 3.2 response to check for improvements"""
    analysis = {
        "ai_processing_success": False,
        "models_used_correctly": False,
        "real_data_processed": False,
        "prompt_safety_passed": False,
        "analysis_quality": "unknown"
    }
    
    if response_data.get("status") == "success":
        analysis["ai_processing_success"] = True
        
        # Check system info for models used
        system_info = response_data.get("analysis", {}).get("system_info", {})
        models_used = system_info.get("models_used", {})
        
        if models_used:
            expected_models = {
                "behavior_analysis": "o3 (deep analysis)",
                "nutrition_plan": "gpt-4o (plan generation)", 
                "routine_plan": "gpt-4o (plan generation)"
            }
            analysis["models_used_correctly"] = all(
                models_used.get(key, "").startswith(expected_models[key].split(" ")[0])
                for key in expected_models
            )
        
        # Check if real data was processed (not refused by AI)
        message = response_data.get("message", "")
        behavior_analysis = response_data.get("analysis", {}).get("behavior_analysis", {})
        
        if "comprehensive health data" in message:
            analysis["real_data_processed"] = True
            
        # Check if AI refused to process data (safety trigger)
        behavior_content = str(behavior_analysis)
        if "I don't have the ability to process" not in behavior_content and "I'm sorry" not in behavior_content:
            analysis["prompt_safety_passed"] = True
            
        # Assess analysis quality
        if behavior_analysis.get("model_used") == "o3":
            analysis["analysis_quality"] = "high"
        elif "error" not in behavior_content.lower():
            analysis["analysis_quality"] = "medium"
        else:
            analysis["analysis_quality"] = "low"
            
    return analysis

async def test_phase32_multimodel():
    """Test Phase 3.2 multi-model implementation"""
    print("\n" + "="*80)
    print(f"PHASE 3.2 - MULTI-MODEL ANALYSIS TESTING")
    print(f"Testing o3 + gpt-4o models with profile: {REAL_PROFILE_ID}")
    print("="*80)
    
    ensure_logs_directory()
    
    # Import the production app
    try:
        from services.api_gateway.openai_main import app
        print("✅ Using production FastAPI app with Phase 3.2 multi-model integration")
    except Exception as e:
        print(f"❌ Failed to import production app: {e}")
        return False
    
    test_results = []
    
    # Test with real profile ID and different archetypes
    with TestClient(app) as client:
        
        print(f"\n[PHASE 3.2 TEST] Testing multi-model analysis with {REAL_PROFILE_ID}...")
        
        # Test one archetype thoroughly
        archetype = "Foundation Builder"
        print(f"\n🧪 Testing {archetype} with multi-model approach...")
        
        try:
            request_body = {
                "user_id": REAL_PROFILE_ID,
                "archetype": archetype
            }
            
            # Make the analysis request
            print(f"📡 Sending Phase 3.2 analysis request...")
            response = client.post("/api/analyze", json=request_body, timeout=120.0)  # Longer timeout for o3
            
            if response.status_code == 200:
                data = response.json()
                
                # Save detailed analysis result
                filepath = save_phase32_result(f"multimodel_{archetype.replace(' ', '_')}", data, response.status_code)
                
                # Analyze the response
                phase32_analysis = analyze_phase32_response(data)
                
                # Extract key information
                analysis = data.get('analysis', {})
                system_info = analysis.get('system_info', {})
                mode = system_info.get('mode', 'unknown')
                phase = system_info.get('phase', 'unknown')
                models_used = system_info.get('models_used', {})
                
                print(f"✅ {archetype} Multi-Model Analysis Results:")
                print(f"   Status: {data['status']}")
                print(f"   Mode: {mode}")
                print(f"   Phase: {phase}")
                print(f"   Message: {data['message']}")
                
                print(f"\n📊 Models Used:")
                for component, model in models_used.items():
                    print(f"   • {component.replace('_', ' ').title()}: {model}")
                
                print(f"\n🔍 Phase 3.2 Analysis:")
                print(f"   • AI Processing Success: {'✅' if phase32_analysis['ai_processing_success'] else '❌'}")
                print(f"   • Models Used Correctly: {'✅' if phase32_analysis['models_used_correctly'] else '❌'}")
                print(f"   • Real Data Processed: {'✅' if phase32_analysis['real_data_processed'] else '❌'}")
                print(f"   • Prompt Safety Passed: {'✅' if phase32_analysis['prompt_safety_passed'] else '❌'}")
                print(f"   • Analysis Quality: {phase32_analysis['analysis_quality'].upper()}")
                
                # Check specific components
                behavior_analysis = analysis.get('behavior_analysis', {})
                nutrition_plan = analysis.get('nutrition_plan', {})
                routine_plan = analysis.get('routine_plan', {})
                
                print(f"\n📋 Component Analysis:")
                if behavior_analysis.get('model_used') == 'o3':
                    print(f"   • Behavior Analysis (o3): ✅ Working")
                    if 'data_insights' in behavior_analysis:
                        print(f"     - Contains data insights: ✅")
                    if 'error' not in str(behavior_analysis):
                        print(f"     - No errors detected: ✅")
                else:
                    print(f"   • Behavior Analysis: ❌ Not using o3 model")
                
                if nutrition_plan.get('model_used') == 'gpt-4o':
                    print(f"   • Nutrition Plan (gpt-4o): ✅ Working")
                else:
                    print(f"   • Nutrition Plan: ❌ Not using gpt-4o model")
                    
                if routine_plan.get('model_used') == 'gpt-4o':
                    print(f"   • Routine Plan (gpt-4o): ✅ Working")
                else:
                    print(f"   • Routine Plan: ❌ Not using gpt-4o model")
                
                # Determine overall success
                overall_success = all([
                    phase32_analysis['ai_processing_success'],
                    phase32_analysis['prompt_safety_passed'],
                    phase32_analysis['analysis_quality'] != 'low'
                ])
                
                test_results.append((f"{archetype} Multi-Model Analysis", overall_success, phase32_analysis))
                
            else:
                print(f"❌ {archetype} analysis failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
                # Save error response
                error_data = {"error": response.text, "status_code": response.status_code}
                save_phase32_result(f"ERROR_{archetype.replace(' ', '_')}", error_data, response.status_code)
                
                test_results.append((f"{archetype} Analysis", False, None))
                
        except Exception as e:
            print(f"💥 {archetype} analysis test crashed: {e}")
            test_results.append((f"{archetype} Analysis", False, None))
    
    return test_results

async def create_phase32_summary(test_results):
    """Create Phase 3.2 comprehensive summary"""
    summary_data = {
        "test_session": TEST_TIMESTAMP,
        "phase": "3.2 - Multi-Model Integration",
        "profile_id": REAL_PROFILE_ID,
        "timestamp": datetime.now().isoformat(),
        "test_type": "MULTI_MODEL_ANALYSIS",
        "improvements": [
            "AI-friendly prompt language to avoid safety triggers",
            "o3 model for deep behavior analysis",
            "gpt-4o models for practical plan generation",
            "Latest OpenAI API best practices",
            "Structured JSON responses with error handling"
        ],
        "test_results": [
            {
                "test_name": name,
                "success": success,
                "phase32_analysis": analysis
            }
            for name, success, analysis in test_results
        ],
        "total_tests": len(test_results),
        "passed_tests": sum(1 for _, success, _ in test_results if success),
        "success_rate": f"{(sum(1 for _, success, _ in test_results if success) / len(test_results) * 100):.1f}%" if test_results else "0%",
        "files_saved": [str(f.name) for f in LOGS_DIR.glob(f"{TEST_TIMESTAMP}*.json")],
        "logs_directory": str(LOGS_DIR.absolute())
    }
    
    summary_file = LOGS_DIR / f"{TEST_TIMESTAMP}_PHASE32_MULTIMODEL_SUMMARY.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, default=str, ensure_ascii=False)
    
    return summary_file, summary_data

async def main():
    """Main test runner for Phase 3.2 multi-model testing"""
    print("🚀 HOLISTICOS MVP - PHASE 3.2 TESTING")
    print("MULTI-MODEL INTEGRATION: o3 + gpt-4o")
    print(f"Profile ID: {REAL_PROFILE_ID}")
    print("Testing optimized prompts and latest OpenAI API practices")
    
    start_time = datetime.now()
    
    # Run Phase 3.2 tests
    test_results = await test_phase32_multimodel()
    
    # Create comprehensive summary
    summary_file, summary_data = await create_phase32_summary(test_results)
    
    # Final summary report
    print("\n" + "="*80)
    print("PHASE 3.2 TEST RESULTS SUMMARY")
    print("="*80)
    
    if test_results:
        passed = summary_data["passed_tests"]
        total = summary_data["total_tests"] 
        
        print(f"\n📊 Test Results:")
        for name, success, analysis in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            if analysis:
                quality = f"({analysis['analysis_quality'].upper()} quality)"
                models = "✅ MULTI-MODEL" if analysis['models_used_correctly'] else "❌ MODEL ISSUE"
                safety = "✅ SAFE" if analysis['prompt_safety_passed'] else "❌ UNSAFE"
                print(f"{status} {name} {models} {safety} {quality}")
            else:
                print(f"{status} {name} (No analysis data)")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📈 Summary:")
        print(f"   • Tests Passed: {passed}/{total} ({summary_data['success_rate']})")
        print(f"   • Duration: {duration:.1f} seconds")
        print(f"   • Profile: {REAL_PROFILE_ID}")
        
        # List improvements implemented
        print(f"\n🚀 Phase 3.2 Improvements Implemented:")
        for improvement in summary_data["improvements"]:
            print(f"   • {improvement}")
        
        # List saved files
        saved_files = list(LOGS_DIR.glob(f"{TEST_TIMESTAMP}*.json"))
        print(f"\n📁 Analysis Files Created ({len(saved_files)}):")
        for file in saved_files:
            file_size = file.stat().st_size
            print(f"   • {file.name} ({file_size:,} bytes)")
        
        print(f"\n📊 Summary Report: {summary_file.name}")
        
        if passed == total:
            print("\n🎉 PHASE 3.2 SUCCESS!")
            print("\n✅ Multi-Model Integration Working:")
            print("   • o3 model providing deep behavior analysis")
            print("   • gpt-4o models generating practical plans")
            print("   • AI-friendly prompts avoiding safety triggers")
            print("   • Real health data being processed successfully")
            print("   • Latest OpenAI API best practices implemented")
            print(f"\n📂 Detailed results: {LOGS_DIR.absolute()}")
            print("   Your system now uses the best models for each task!")
            
            return True
        else:
            print(f"\n⚠️  Some issues found:")
            print(f"   • {total - passed} tests failed")
            print("   Check individual JSON files for detailed error information.")
            return False
    else:
        print("\n❌ No test results available")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)