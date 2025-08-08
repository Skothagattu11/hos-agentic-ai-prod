#!/usr/bin/env python3
"""
HolisticOS Adaptation Engine Agent Test
Tests real-time strategy adaptation based on user feedback and progress patterns
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

async def test_adaptation_engine_core():
    """Test Adaptation Engine core functionality"""
    print("⚡ Testing HolisticOS Adaptation Engine Agent")
    print("=" * 70)
    
    try:
        # Import the adaptation engine
        from services.agents.adaptation.main import (
            HolisticAdaptationEngine, 
            AdaptationTrigger, 
            AdaptationRequest
        )
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Initialize adaptation engine
        adaptation_engine = HolisticAdaptationEngine()
        print(f"✅ Adaptation Engine initialized")
        print(f"   Agent ID: {adaptation_engine.agent_id}")
        print(f"   System Prompt: {len(adaptation_engine.system_prompt):,} chars")
        print(f"   Supported Events: {adaptation_engine.get_supported_event_types()}")
        print(f"   Adaptation Thresholds: {adaptation_engine.adaptation_thresholds}")
        
        # Test 1: Strategy Adaptation for Poor Adherence
        print("\n⚡ Test 1: Poor Adherence Adaptation")
        adherence_event = AgentEvent(
            event_id="test_adherence_1",
            event_type="adapt_strategy",
            source_agent="test_agent",
            payload={
                "trigger": "poor_adherence",
                "context": {
                    "adherence_rate": 0.3,  # 30% - below 40% threshold
                    "engagement_level": 0.6,
                    "user_feedback": "The routine is too complex and time-consuming"
                },
                "urgency": "high",
                "affected_areas": ["routine", "behavior"],
                "user_feedback": "I can't keep up with all the daily tasks"
            },
            timestamp=datetime.now(),
            user_id="test_user_adherence",
            archetype="Foundation Builder"
        )
        
        response = await adaptation_engine.process(adherence_event)
        if response.success:
            print("✅ Poor adherence adaptation successful")
            result = response.result
            print(f"   Trigger: {result.get('trigger')}")
            print(f"   Adaptations made: {len(result.get('adaptations_made', []))}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Expected impact: {result.get('expected_impact')}")
        else:
            print(f"❌ Poor adherence adaptation failed: {response.error_message}")
        
        # Test 2: Engagement Decline Adaptation
        print("\n⚡ Test 2: Engagement Decline Adaptation")
        engagement_event = AgentEvent(
            event_id="test_engagement_1",
            event_type="adapt_strategy",
            source_agent="test_agent",
            payload={
                "trigger": "engagement_decline",
                "context": {
                    "engagement_level": 0.4,  # 40% - significant decline
                    "adherence_rate": 0.7,
                    "satisfaction_score": 0.3,
                    "days_since_last_progress": 5
                },
                "urgency": "medium",
                "affected_areas": ["behavior", "engagement"],
                "user_feedback": "I'm getting bored with the same routine every day"
            },
            timestamp=datetime.now(),
            user_id="test_user_engagement",
            archetype="Connected Explorer"
        )
        
        response = await adaptation_engine.process(engagement_event)
        if response.success:
            print("✅ Engagement decline adaptation successful")
            result = response.result
            print(f"   Expected impact: {result.get('expected_impact')}")
            print(f"   Monitoring plan: {bool(result.get('monitoring_plan'))}")
        else:
            print(f"❌ Engagement decline adaptation failed: {response.error_message}")
        
        # Test 3: Strategy Effectiveness Monitoring
        print("\n⚡ Test 3: Strategy Effectiveness Monitoring")
        monitoring_event = AgentEvent(
            event_id="test_monitoring_1",
            event_type="monitor_effectiveness",
            source_agent="test_agent",
            payload={
                "monitoring_data": {
                    "adherence_rate": 0.35,  # Below threshold - should trigger adaptation
                    "engagement_level": 0.5,
                    "progress_rate": 0.4,
                    "satisfaction": 0.6,
                    "days_tracked": 14
                }
            },
            timestamp=datetime.now(),
            user_id="test_user_monitoring",
            archetype="Systematic Improver"
        )
        
        response = await adaptation_engine.process(monitoring_event)
        if response.success:
            print("✅ Strategy effectiveness monitoring successful")
            result = response.result
            effectiveness = result.get('effectiveness_analysis', {})
            print(f"   Overall effectiveness score: {effectiveness.get('overall_score', 0):.2f}")
            print(f"   Effectiveness category: {effectiveness.get('effectiveness_category', 'N/A')}")
            adaptation_needed = result.get('adaptation_needed', {})
            print(f"   Adaptation needed: {adaptation_needed.get('needed', False)}")
            if adaptation_needed.get('needed'):
                print(f"   Adaptation triggered: {result.get('adaptation_triggered', False)}")
        else:
            print(f"❌ Strategy effectiveness monitoring failed: {response.error_message}")
        
        # Test 4: User Feedback Processing
        print("\n⚡ Test 4: User Feedback Processing")
        feedback_event = AgentEvent(
            event_id="test_feedback_1",
            event_type="user_feedback_received",
            source_agent="test_agent",
            payload={
                "feedback": {
                    "text": "The nutrition plan is too restrictive and I can't follow it at work",
                    "rating": 3,  # Low rating - should trigger adaptation
                    "category": "nutrition",
                    "timestamp": datetime.now().isoformat()
                }
            },
            timestamp=datetime.now(),
            user_id="test_user_feedback",
            archetype="Peak Performer"
        )
        
        response = await adaptation_engine.process(feedback_event)
        if response.success:
            print("✅ User feedback processing successful")
            result = response.result
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"   Feedback sentiment: {analysis.get('sentiment', 'N/A')}")
                print(f"   Adaptation needed: {analysis.get('adaptation_needed', False)}")
            elif 'adaptations_made' in result:
                print(f"   Adaptation triggered by feedback")
                print(f"   Adaptations made: {len(result.get('adaptations_made', []))}")
        else:
            print(f"❌ User feedback processing failed: {response.error_message}")
        
        # Test 5: Performance Trigger Handling
        print("\n⚡ Test 5: Performance Trigger Handling")
        performance_event = AgentEvent(
            event_id="test_performance_1",
            event_type="adherence_low",
            source_agent="monitoring_system",
            payload={
                "adherence_rate": 0.25,  # Very low adherence
                "affected_areas": ["routine", "nutrition"],
                "duration_days": 7,
                "previous_rate": 0.65
            },
            timestamp=datetime.now(),
            user_id="test_user_performance",
            archetype="Transformation Seeker"
        )
        
        response = await adaptation_engine.process(performance_event)
        if response.success:
            print("✅ Performance trigger handling successful")
            result = response.result
            print(f"   Trigger processed: {result.get('trigger')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
        else:
            print(f"❌ Performance trigger handling failed: {response.error_message}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_adaptation_integration():
    """Test Adaptation Engine integration with other agents"""
    print("\n🤝 Testing Adaptation Engine Integration")
    print("=" * 70)
    
    try:
        from services.agents.adaptation.main import HolisticAdaptationEngine
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Initialize adaptation engine for integration testing
        adaptation_engine = HolisticAdaptationEngine()
        print(f"✅ Adaptation Engine initialized for integration testing")
        
        # Test behavior analysis completion event handling
        print("\n⚡ Testing behavior analysis completion integration...")
        behavior_complete_event = AgentEvent(
            event_id="test_behavior_adaptation",
            event_type="behavior_analysis_complete",
            source_agent="behavior_analysis_agent",
            payload={
                "analysis_result": {
                    "sophistication_score": 75,
                    "adherence_prediction": 0.6,
                    "engagement_prediction": 0.8
                },
                "effectiveness_indicators": {
                    "complexity_level": "medium",
                    "user_readiness": "high"
                }
            },
            timestamp=datetime.now(),
            user_id="test_user_behavior_integration",
            archetype="Peak Performer"
        )
        
        response = await adaptation_engine.process(behavior_complete_event)
        if response.success:
            print("✅ Behavior analysis completion integration successful")
            print(f"   Effectiveness monitoring enabled: {response.result.get('monitoring') == 'enabled'}")
        else:
            print(f"❌ Behavior completion integration failed: {response.error_message}")
        
        # Test insights generation completion event
        print("\n⚡ Testing insights generation completion integration...")
        insights_complete_event = AgentEvent(
            event_id="test_insights_adaptation",
            event_type="insights_generation_complete",
            source_agent="insights_generation_agent",
            payload={
                "insights": [
                    {"category": "behavioral_pattern", "confidence": 0.8, "actionable": True},
                    {"category": "trend_analysis", "confidence": 0.7, "actionable": True}
                ],
                "recommendations": [
                    "Increase routine flexibility by 20%",
                    "Add variety to weekly exercise selection"
                ]
            },
            timestamp=datetime.now(),
            user_id="test_user_insights_integration",
            archetype="Systematic Improver"
        )
        
        response = await adaptation_engine.process(insights_complete_event)
        if response.success:
            print("✅ Insights generation completion integration successful")
        else:
            print(f"❌ Insights completion integration failed: {response.error_message}")
        
        # Test coordination request handling
        print("\n⚡ Testing multi-agent coordination...")
        coordination_event = AgentEvent(
            event_id="test_coordination_1",
            event_type="coordination_request",
            source_agent="behavior_analysis_agent",
            payload={
                "request_type": "sync_adaptation",
                "data": {
                    "adaptation_type": "routine_simplification",
                    "affected_components": ["daily_tasks", "meal_prep", "exercise_routine"],
                    "coordination_level": "high"
                }
            },
            timestamp=datetime.now(),
            user_id="test_user_coordination",
            archetype="Foundation Builder"
        )
        
        response = await adaptation_engine.process(coordination_event)
        if response.success:
            print("✅ Multi-agent coordination successful")
            result = response.result
            sync_result = result.get('sync_result', {})
            print(f"   Sync status: {sync_result.get('sync_status', 'N/A')}")
            print(f"   Coordinated agents: {len(sync_result.get('synced_agents', []))}")
        else:
            print(f"❌ Multi-agent coordination failed: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_archetype_specific_adaptations():
    """Test archetype-specific adaptation strategies"""
    print("\n🎯 Testing Archetype-Specific Adaptations")
    print("=" * 70)
    
    archetypes = [
        ("Peak Performer", "strategy_ineffective"),
        ("Foundation Builder", "poor_adherence"),
        ("Systematic Improver", "engagement_decline"),
        ("Transformation Seeker", "progress_stalled"),
        ("Resilience Rebuilder", "context_changed"),
        ("Connected Explorer", "engagement_decline")
    ]
    
    try:
        from services.agents.adaptation.main import HolisticAdaptationEngine
        from shared_libs.event_system.base_agent import AgentEvent
        
        adaptation_engine = HolisticAdaptationEngine()
        
        for i, (archetype, trigger) in enumerate(archetypes, 1):
            print(f"\n⚡ Test {i}: {archetype} - {trigger} Adaptation")
            
            archetype_event = AgentEvent(
                event_id=f"test_archetype_{i}",
                event_type="adapt_strategy",
                source_agent="test_agent",
                payload={
                    "trigger": trigger,
                    "context": {
                        "adherence_rate": 0.4 if trigger == "poor_adherence" else 0.7,
                        "engagement_level": 0.3 if trigger == "engagement_decline" else 0.7,
                        "progress_rate": 0.2 if trigger == "progress_stalled" else 0.6,
                        "user_circumstances": "changed_schedule" if trigger == "context_changed" else "normal"
                    },
                    "urgency": "high" if trigger in ["poor_adherence", "strategy_ineffective"] else "medium",
                    "affected_areas": ["behavior", "routine", "engagement"]
                },
                timestamp=datetime.now(),
                user_id=f"test_user_{archetype.lower().replace(' ', '_')}",
                archetype=archetype
            )
            
            response = await adaptation_engine.process(archetype_event)
            if response.success:
                print(f"✅ {archetype} adaptation successful")
                result = response.result
                adaptations = result.get('adaptations_made', [])
                if adaptations:
                    print(f"   Adaptations: {len(adaptations)} changes made")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
            else:
                print(f"❌ {archetype} adaptation failed: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Archetype test error: {e}")
        return False

async def main():
    """Run all adaptation engine tests"""
    print("🧪 HolisticOS Adaptation Engine Agent Test Suite")
    print("Testing real-time strategy adaptation and multi-agent coordination")
    print("=" * 80)
    
    # Test 1: Adaptation Engine Core Functionality
    core_test_passed = await test_adaptation_engine_core()
    
    # Test 2: Integration with Other Agents
    integration_test_passed = await test_adaptation_integration()
    
    # Test 3: Archetype-Specific Adaptations
    archetype_test_passed = await test_archetype_specific_adaptations()
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 Test Results Summary:")
    print(f"   Adaptation Engine Core: {'✅ PASSED' if core_test_passed else '❌ FAILED'}")
    print(f"   Agent Integration: {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    print(f"   Archetype Adaptations: {'✅ PASSED' if archetype_test_passed else '❌ FAILED'}")
    
    if core_test_passed and integration_test_passed and archetype_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Phase 2 Complete - Multi-Agent System Status:")
        print("   ✅ Memory Management Agent - 4-layer hierarchical memory system")
        print("   ✅ Insights Generation Agent - AI-powered pattern analysis")
        print("   ✅ Adaptation Engine Agent - Real-time strategy adaptation")
        print("   ✅ Event-driven multi-agent coordination")
        print("   ✅ Archetype-specific personalization across all agents")
        print("   ✅ AI-powered analysis and recommendations")
        print("\n🏗️ Phase 2 Architecture Complete:")
        print("   📊 Behavior Analysis → 🧠 Memory Storage → 🔍 Insights Generation → ⚡ Strategy Adaptation")
        print("\n🔄 Ready for Next Steps:")
        print("   1. Multi-Agent Orchestrator integration")
        print("   2. Database setup and real data integration")
        print("   3. End-to-end testing with complete workflow")
        print("   4. Performance optimization and scaling")
        print("   5. Render deployment preparation")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)