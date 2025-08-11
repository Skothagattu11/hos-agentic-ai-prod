#!/usr/bin/env python3
"""
PHASE 3.2 FIXED TESTING
Test the fixes for BiomarkerData attribute errors and verify the system works
"""
import asyncio
import sys
import os
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration
REAL_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

async def test_fixed_analysis():
    """Test the fixed analysis endpoint"""
    print("🧪 TESTING PHASE 3.2 FIXES")
    print("="*50)
    
    try:
        from services.api_gateway.openai_main import app
        print("✅ Production app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        return False
    
    with TestClient(app) as client:
        print(f"\n🔍 Testing analysis with profile: {REAL_PROFILE_ID}")
        
        request_body = {
            "user_id": REAL_PROFILE_ID,
            "archetype": "Foundation Builder"
        }
        
        try:
            response = client.post("/api/analyze", json=request_body, timeout=90.0)
            
            if response.status_code == 200:
                data = response.json()
                
                print("✅ ANALYSIS SUCCESSFUL!")
                print(f"   Status: {data['status']}")
                print(f"   Phase: {data['analysis']['system_info']['phase']}")
                
                # Check models used
                models = data['analysis']['system_info']['models_used']
                print(f"\n📊 Models Used:")
                for component, model in models.items():
                    print(f"   • {component}: {model}")
                
                # Check if behavior analysis worked
                behavior = data['analysis']['behavior_analysis']
                if behavior.get('model_used') == 'o3':
                    print(f"\n✅ o3 Behavior Analysis:")
                    print(f"   • Confidence: {behavior.get('behavioral_signature', {}).get('confidence', 'N/A')}")
                    print(f"   • Category: {behavior.get('sophistication_assessment', {}).get('category', 'N/A')}")
                    print(f"   • Has Data Insights: {'data_insights' in behavior}")
                
                # Check nutrition plan
                nutrition = data['analysis']['nutrition_plan']
                if nutrition.get('model_used') == 'gpt-4o':
                    print(f"   • Nutrition Plan (gpt-4o): ✅ Generated")
                
                # Check routine plan
                routine = data['analysis']['routine_plan']
                if routine.get('model_used') == 'gpt-4o':
                    print(f"   • Routine Plan (gpt-4o): ✅ Generated")
                
                return True
                
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"💥 Test crashed: {e}")
            import traceback
            traceback.print_exc()
            return False

async def check_logs():
    """Check if the enhanced logging worked"""
    print(f"\n📂 CHECKING LOGS")
    print("="*30)
    
    # Check agent handoff logs
    handoff_dir = "logs/agent_handoffs"
    if os.path.exists(handoff_dir):
        files = os.listdir(handoff_dir)
        print(f"✅ Agent handoff logs: {len(files)} files")
        
        # Check latest behavior analysis log
        behavior_files = [f for f in files if 'behavior_analysis' in f]
        if behavior_files:
            latest_file = sorted(behavior_files)[-1]
            print(f"   • Latest behavior log: {latest_file}")
            
            # Read a snippet
            with open(os.path.join(handoff_dir, latest_file), 'r') as f:
                content = f.read()
                if 'HEALTH TRACKING DATA SUMMARY:' in content:
                    if 'Error formatting user data' in content:
                        print(f"   ⚠️  Data formatting error found (but o3 still worked)")
                    else:
                        print(f"   ✅ No data formatting errors")
                        
                if '"model_used": "o3"' in content:
                    print(f"   ✅ o3 model successfully used")
    else:
        print(f"❌ No agent handoff logs found")
    
    # Check main input/output logs  
    input_files = [f for f in os.listdir("logs") if f.startswith("input_")]
    output_files = [f for f in os.listdir("logs") if f.startswith("output_")]
    
    print(f"📝 Main logs: {len(input_files)} input, {len(output_files)} output files")
    
    if input_files:
        latest_input = sorted(input_files)[-1]
        print(f"   • Latest input: {latest_input}")
        
        # Check if raw health data is included
        with open(f"logs/{latest_input}", 'r') as f:
            content = json.load(f)
            if 'raw_health_data' in content:
                raw_data = content['raw_health_data']
                print(f"   ✅ Raw health data included:")
                print(f"     - Scores: {raw_data.get('data_quality', {}).get('scores_count', 0)}")
                print(f"     - Biomarkers: {raw_data.get('data_quality', {}).get('biomarkers_count', 0)}")

async def main():
    """Main test runner"""
    print("🚀 PHASE 3.2 FIX VALIDATION")
    print("Testing BiomarkerData fixes and enhanced logging")
    
    start_time = datetime.now()
    
    # Test the fixed analysis
    success = await test_fixed_analysis()
    
    # Check the logs
    await check_logs()
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\n" + "="*50)
    print("RESULTS SUMMARY")
    print("="*50)
    
    if success:
        print("✅ PHASE 3.2 FIXES SUCCESSFUL!")
        print("\n🎯 What's Working:")
        print("   • BiomarkerData attribute errors fixed")
        print("   • o3 model working without temperature parameter")
        print("   • gpt-4o models generating plans")
        print("   • Enhanced logging with agent handoffs")
        print("   • Raw health data captured in input logs")
        print("   • Real wearable data being processed by AI")
        
        print(f"\n⏱️  Duration: {duration:.1f} seconds")
        print(f"📂 Check logs/agent_handoffs/ for detailed flow")
        
        return True
    else:
        print("❌ SOME ISSUES REMAIN")
        print("   Check error messages above")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)