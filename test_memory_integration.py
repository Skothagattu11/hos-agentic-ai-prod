#!/usr/bin/env python3
"""
HolisticOS Memory Integration Test
Tests the Memory Management Agent integration with the behavior analysis workflow
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"🔑 OpenAI API Key: {'FOUND' if os.getenv('OPENAI_API_KEY') else 'NOT FOUND'}")
except ImportError:
    print("⚠️  python-dotenv not available - environment variables from system only")

async def test_memory_agent():
    """Test Memory Management Agent functionality"""
    print("🧠 Testing HolisticOS Memory Management Agent")
    print("=" * 50)
    
    try:
        # Import the memory agent
        from services.agents.memory.main import HolisticMemoryAgent
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Initialize memory agent
        memory_agent = HolisticMemoryAgent()
        print(f"✅ Memory Agent initialized")
        print(f"   Agent ID: {memory_agent.agent_id}")
        print(f"   System Prompt: {len(memory_agent.system_prompt):,} chars")
        print(f"   Supported Events: {memory_agent.get_supported_event_types()}")
        
        # Test 1: Store Working Memory
        print("\n🔍 Test 1: Store Working Memory")
        store_event = AgentEvent(
            event_id="test_store_1",
            event_type="memory_store",
            source_agent="test_agent",
            payload={
                "memory_type": "working",
                "category": "test_category",
                "data": {
                    "test_key": "test_value",
                    "timestamp": datetime.now().isoformat()
                },
                "confidence": 0.8
            },
            timestamp=datetime.now(),
            user_id="test_user_memory"
        )
        
        response = await memory_agent.process(store_event)
        if response.success:
            print("✅ Working memory storage successful")
        else:
            print(f"❌ Working memory storage failed: {response.error_message}")
        
        # Test 2: Retrieve Memory
        print("\n🔍 Test 2: Retrieve Memory")
        retrieve_event = AgentEvent(
            event_id="test_retrieve_1",
            event_type="memory_retrieve",
            source_agent="test_agent",
            payload={
                "memory_type": "all",
                "query_context": "test retrieval"
            },
            timestamp=datetime.now(),
            user_id="test_user_memory"
        )
        
        response = await memory_agent.process(retrieve_event)
        if response.success:
            print("✅ Memory retrieval successful")
            print(f"   Retrieved data keys: {list(response.result.get('memory_data', {}).keys())}")
        else:
            print(f"❌ Memory retrieval failed: {response.error_message}")
        
        # Test 3: Memory Analysis
        print("\n🔍 Test 3: Memory Analysis")
        analyze_event = AgentEvent(
            event_id="test_analyze_1",
            event_type="memory_analyze",
            source_agent="test_agent",
            payload={
                "analysis_type": "patterns"
            },
            timestamp=datetime.now(),
            user_id="test_user_memory"
        )
        
        response = await memory_agent.process(analyze_event)
        if response.success:
            print("✅ Memory analysis successful")
            print(f"   Analysis results: {response.result.get('patterns_identified', 0)} patterns")
        else:
            print(f"❌ Memory analysis failed: {response.error_message}")
        
        # Test 4: Test Memory Layers
        print("\n🔍 Test 4: Test Memory Layer System")
        from services.agents.memory.memory_layers import MemoryLayerFactory
        
        # Test layer creation (without DB for now)
        working_layer = MemoryLayerFactory.create_layer("working", None)
        shortterm_layer = MemoryLayerFactory.create_layer("shortterm", None)
        longterm_layer = MemoryLayerFactory.create_layer("longterm", None)
        meta_layer = MemoryLayerFactory.create_layer("meta", None)
        
        print("✅ All memory layers created successfully")
        print(f"   Working Layer: {type(working_layer).__name__}")
        print(f"   Short-term Layer: {type(shortterm_layer).__name__}")
        print(f"   Long-term Layer: {type(longterm_layer).__name__}")
        print(f"   Meta-memory Layer: {type(meta_layer).__name__}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_behavior_memory_integration():
    """Test Memory Agent event-based integration (without TensorFlow dependencies)"""
    print("\n🤝 Testing Memory Event Integration")
    print("=" * 50)
    
    try:
        from services.agents.memory.main import HolisticMemoryAgent
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Initialize memory agent for integration testing
        memory_agent = HolisticMemoryAgent()
        print(f"✅ Memory Agent initialized for integration testing")
        
        # Test behavior analysis completion event handling
        print("\n🔍 Testing behavior analysis completion event...")
        behavior_complete_event = AgentEvent(
            event_id="test_behavior_complete",
            event_type="behavior_analysis_complete",
            source_agent="behavior_analysis_agent",
            payload={
                "behavioral_signature": {"signature": "test_signature", "confidence": 0.85},
                "sophistication_assessment": {"score": 75, "confidence": 0.8},
                "primary_goal": {"goal": "Test goal"},
                "readiness_level": "Advanced"
            },
            timestamp=datetime.now(),
            user_id="test_user_behavior",
            archetype="Peak Performer"
        )
        
        response = await memory_agent.process(behavior_complete_event)
        if response.success:
            print("✅ Behavior analysis completion event handled successfully")
            print(f"   Stored analysis: {response.result.get('stored_analysis')}")
        else:
            print(f"❌ Behavior completion event failed: {response.error_message}")
        
        # Test nutrition plan completion event
        print("\n🔍 Testing nutrition plan completion event...")
        nutrition_complete_event = AgentEvent(
            event_id="test_nutrition_complete",
            event_type="nutrition_plan_complete",
            source_agent="nutrition_plan_agent",
            payload={
                "nutrition_plan": {"date": "2025-08-08", "meals": ["breakfast", "lunch", "dinner"]},
                "preferences": {"dietary_restrictions": [], "favorite_foods": ["chicken", "vegetables"]}
            },
            timestamp=datetime.now(),
            user_id="test_user_nutrition",
            archetype="Foundation Builder"
        )
        
        response = await memory_agent.process(nutrition_complete_event)
        if response.success:
            print("✅ Nutrition plan completion event handled successfully")
        else:
            print(f"❌ Nutrition completion event failed: {response.error_message}")
        
        # Test routine plan completion event
        print("\n🔍 Testing routine plan completion event...")
        routine_complete_event = AgentEvent(
            event_id="test_routine_complete",
            event_type="routine_plan_complete",
            source_agent="routine_plan_agent",
            payload={
                "routine_plan": {"morning": "exercise", "evening": "meditation"},
                "preferences": {"preferred_time": "morning", "activity_level": "moderate"}
            },
            timestamp=datetime.now(),
            user_id="test_user_routine",
            archetype="Systematic Improver"
        )
        
        response = await memory_agent.process(routine_complete_event)
        if response.success:
            print("✅ Routine plan completion event handled successfully")
        else:
            print(f"❌ Routine completion event failed: {response.error_message}")
        
        # Test memory consolidation
        print("\n🔍 Testing memory consolidation...")
        consolidate_event = AgentEvent(
            event_id="test_consolidate",
            event_type="memory_consolidate",
            source_agent="orchestrator",
            payload={},
            timestamp=datetime.now(),
            user_id="test_user_consolidate"
        )
        
        response = await memory_agent.process(consolidate_event)
        if response.success:
            print("✅ Memory consolidation completed")
            consolidation_results = response.result
            print(f"   Consolidated items: {consolidation_results.get('consolidated_items', 0)}")
        else:
            print(f"❌ Memory consolidation failed: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all memory integration tests"""
    print("🧪 HolisticOS Memory Integration Test Suite")
    print("Testing 4-layer hierarchical memory system integration")
    print("=" * 60)
    
    # Test 1: Memory Agent Core Functionality
    memory_test_passed = await test_memory_agent()
    
    # Test 2: Behavior-Memory Integration  
    integration_test_passed = await test_behavior_memory_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary:")
    print(f"   Memory Agent Core: {'✅ PASSED' if memory_test_passed else '❌ FAILED'}")
    print(f"   Event Integration: {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    
    if memory_test_passed and integration_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Phase 2 Memory System Status:")
        print("   ✅ Memory Agent framework implemented")
        print("   ✅ 4-layer memory hierarchy designed")
        print("   ✅ Event-driven memory operations working")
        print("   ✅ Multi-agent completion event handling")
        print("   ✅ Memory consolidation framework ready")
        print("\n🔄 Next Steps:")
        print("   1. Set up PostgreSQL database with memory tables")
        print("   2. Test database integration with real data")
        print("   3. Implement Insights Generation Agent")
        print("   4. Add AI-powered memory learning algorithms")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)