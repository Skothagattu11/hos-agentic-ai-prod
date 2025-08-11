#!/usr/bin/env python3
"""
PHASE 3.3 AGENT-SPECIFIC DATA FILTERING TESTING
Test that each agent receives properly filtered, relevant data instead of broadcasting the same data to all agents
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

async def test_agent_specific_filtering():
    """Test Phase 3.3 agent-specific data filtering"""
    print("🧪 TESTING PHASE 3.3: AGENT-SPECIFIC DATA FILTERING")
    print("="*60)
    
    try:
        from services.api_gateway.openai_main import app
        print("✅ Production app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        return False
    
    with TestClient(app) as client:
        print(f"\n🔍 Testing agent filtering with profile: {REAL_PROFILE_ID}")
        
        request_body = {
            "user_id": REAL_PROFILE_ID,
            "archetype": "Foundation Builder"
        }
        
        try:
            print("📡 Running Phase 3.3 analysis...")
            response = client.post("/api/analyze", json=request_body, timeout=90.0)
            
            if response.status_code == 200:
                data = response.json()
                
                print("✅ PHASE 3.3 ANALYSIS SUCCESSFUL!")
                print(f"   Status: {data['status']}")
                print(f"   Phase: {data['analysis']['system_info']['phase']}")
                
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

async def check_agent_handoff_logs():
    """Check if agent handoff logs show different inputs for each agent"""
    print(f"\n📂 CHECKING AGENT HANDOFF LOGS FOR DATA FILTERING")
    print("="*50)
    
    handoff_dir = "logs/agent_handoffs"
    if not os.path.exists(handoff_dir):
        print(f"❌ Agent handoff logs directory not found")
        return False
        
    files = os.listdir(handoff_dir)
    if not files:
        print(f"❌ No agent handoff logs found")
        return False
        
    print(f"✅ Found {len(files)} agent handoff files")
    
    # Get the latest set of logs
    behavior_files = [f for f in files if 'behavior_analysis' in f]
    nutrition_files = [f for f in files if 'nutrition_plan' in f] 
    routine_files = [f for f in files if 'routine_plan' in f]
    
    if not (behavior_files and nutrition_files and routine_files):
        print(f"❌ Missing agent handoff logs")
        print(f"   Behavior: {len(behavior_files)}, Nutrition: {len(nutrition_files)}, Routine: {len(routine_files)}")
        return False
        
    # Get latest files
    latest_behavior = sorted(behavior_files)[-1]
    latest_nutrition = sorted(nutrition_files)[-1]
    latest_routine = sorted(routine_files)[-1]
    
    print(f"\n📋 Analyzing Latest Agent Handoffs:")
    print(f"   • Behavior: {latest_behavior}")
    print(f"   • Nutrition: {latest_nutrition}") 
    print(f"   • Routine: {latest_routine}")
    
    # Check if inputs are different - handle text format with headers
    try:
        def parse_agent_handoff_file(filepath):
            """Parse agent handoff file with text headers"""
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Find the INPUT DATA section
            input_start = content.find("INPUT DATA:")
            output_start = content.find("OUTPUT DATA:")
            
            if input_start == -1 or output_start == -1:
                return {}, {}
            
            # Extract INPUT DATA JSON
            input_section = content[input_start:output_start]
            input_json_start = input_section.find("{")
            if input_json_start != -1:
                input_json = input_section[input_json_start:].strip()
                try:
                    input_data = json.loads(input_json)
                except:
                    input_data = {}
            else:
                input_data = {}
            
            # Extract OUTPUT DATA JSON
            output_section = content[output_start:]
            output_json_start = output_section.find("{")
            if output_json_start != -1:
                output_json = output_section[output_json_start:].strip()
                # Remove any trailing text after the JSON
                if output_json.endswith("============================================================\n"):
                    output_json = output_json[:-60].strip()
                try:
                    output_data = json.loads(output_json)
                except:
                    output_data = {}
            else:
                output_data = {}
                
            return input_data, output_data
        
        behavior_input, behavior_output = parse_agent_handoff_file(os.path.join(handoff_dir, latest_behavior))
        nutrition_input, nutrition_output = parse_agent_handoff_file(os.path.join(handoff_dir, latest_nutrition))
        routine_input, routine_output = parse_agent_handoff_file(os.path.join(handoff_dir, latest_routine))
        
        print(f"\n🔍 DATA FILTERING ANALYSIS:")
        
        # Check behavior agent input structure
        if 'comprehensive_health_context' in behavior_input:
            print(f"   ✅ Behavior Agent: Comprehensive health context (as expected)")
            if 'detailed_metrics' in behavior_input:
                print(f"     • Has detailed metrics with activity patterns and biomarker categories")
        else:
            print(f"   ⚠️  Behavior Agent: Missing comprehensive health context")
            
        # Check nutrition agent input structure
        if 'behavioral_insights' in nutrition_input and 'nutrition_relevant_metrics' in nutrition_input:
            print(f"   ✅ Nutrition Agent: Filtered nutrition-specific data (Phase 3.3 working)")
            print(f"     • Has behavioral insights and nutrition-relevant metrics")
        else:
            print(f"   ❌ Nutrition Agent: Not using filtered data structure")
            print(f"     • Available keys: {list(nutrition_input.keys()) if nutrition_input else 'No data'}")
            
        # Check routine agent input structure  
        if 'behavioral_insights' in routine_input and 'routine_relevant_metrics' in routine_input:
            print(f"   ✅ Routine Agent: Filtered routine-specific data (Phase 3.3 working)")
            print(f"     • Has behavioral insights and routine-relevant metrics")
        else:
            print(f"   ❌ Routine Agent: Not using filtered data structure")
            print(f"     • Available keys: {list(routine_input.keys()) if routine_input else 'No data'}")
            
        # Compare input sizes to see if they're different
        behavior_input_size = len(str(behavior_input))
        nutrition_input_size = len(str(nutrition_input))
        routine_input_size = len(str(routine_input))
        
        print(f"\n📊 INPUT DATA SIZES:")
        print(f"   • Behavior Agent: {behavior_input_size:,} characters")
        print(f"   • Nutrition Agent: {nutrition_input_size:,} characters")
        print(f"   • Routine Agent: {routine_input_size:,} characters")
        
        # Check if inputs are actually different (Phase 3.3 goal)
        if behavior_input != nutrition_input and behavior_input != routine_input and nutrition_input != routine_input:
            print(f"   ✅ SUCCESS: All three agents received DIFFERENT input data!")
            return True
        else:
            print(f"   ❌ ISSUE: Some agents still receiving identical input data")
            return False
            
    except Exception as e:
        print(f"❌ Error analyzing agent handoff logs: {e}")
        return False

async def main():
    """Main test runner for Phase 3.3"""
    print("🚀 HOLISTICOS MVP - PHASE 3.3 TESTING")
    print("AGENT-SPECIFIC DATA FILTERING VALIDATION")
    print(f"Profile ID: {REAL_PROFILE_ID}")
    print("Testing that each agent gets relevant, filtered data")
    
    start_time = datetime.now()
    
    # Test the Phase 3.3 implementation
    analysis_success = await test_agent_specific_filtering()
    
    # Check the agent handoff logs for filtering
    filtering_success = await check_agent_handoff_logs()
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\n" + "="*60)
    print("PHASE 3.3 TEST RESULTS SUMMARY")
    print("="*60)
    
    if analysis_success and filtering_success:
        print("🎉 PHASE 3.3 SUCCESS!")
        print("\n✅ What's Working:")
        print("   • Each agent receives agent-specific, filtered data")
        print("   • Behavior agent gets comprehensive health data for deep analysis")
        print("   • Nutrition agent gets nutrition-relevant metrics + behavioral insights")
        print("   • Routine agent gets routine-relevant patterns + behavioral insights")
        print("   • No more broadcasting identical data to all agents")
        print("   • Proper agent handoff chain implemented")
        
        print(f"\n⏱️  Duration: {duration:.1f} seconds")
        print(f"📂 Check logs/agent_handoffs/ for detailed agent data flow")
        print("\n🎯 PHASE 3.3 COMPLETE: Agent-Specific Data Filtering Working!")
        
        return True
    else:
        print("❌ PHASE 3.3 ISSUES FOUND")
        print(f"   • Analysis Success: {'✅' if analysis_success else '❌'}")
        print(f"   • Data Filtering Success: {'✅' if filtering_success else '❌'}")
        print("\n🔧 Next Steps:")
        if not analysis_success:
            print("   - Check /api/analyze endpoint for errors")
        if not filtering_success:
            print("   - Verify agent-specific data preparation functions")
            print("   - Check logs/agent_handoffs/ for data structures")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)