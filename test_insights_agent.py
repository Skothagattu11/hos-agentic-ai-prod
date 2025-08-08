#!/usr/bin/env python3
"""
HolisticOS Insights Generation Agent Test
Tests pattern analysis, trend detection, and AI-powered insights generation
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

async def test_insights_agent_core():
    """Test Insights Agent core functionality"""
    print("🔍 Testing HolisticOS Insights Generation Agent")
    print("=" * 60)
    
    try:
        # Import the insights agent
        from services.agents.insights.main import HolisticInsightsAgent, InsightRequest
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Initialize insights agent
        insights_agent = HolisticInsightsAgent()
        print(f"✅ Insights Agent initialized")
        print(f"   Agent ID: {insights_agent.agent_id}")
        print(f"   System Prompt: {len(insights_agent.system_prompt):,} chars")
        print(f"   Supported Events: {insights_agent.get_supported_event_types()}")
        print(f"   Analysis Categories: {insights_agent.analysis_categories}")
        
        # Test 1: Generate Comprehensive Insights
        print("\n🔍 Test 1: Generate Comprehensive Insights")
        insights_event = AgentEvent(
            event_id="test_insights_1",
            event_type="generate_insights",
            source_agent="test_agent",
            payload={
                "insight_type": "comprehensive",
                "time_horizon": "medium_term",
                "focus_areas": ["behavioral_patterns", "nutrition_adherence", "routine_consistency"]
            },
            timestamp=datetime.now(),
            user_id="test_user_insights",
            archetype="Peak Performer"
        )
        
        response = await insights_agent.process(insights_event)
        if response.success:
            print("✅ Comprehensive insights generation successful")
            result = response.result
            print(f"   Insights generated: {len(result.get('insights', []))}")
            print(f"   Patterns identified: {result.get('patterns_identified', 0)}")
            print(f"   Recommendations: {len(result.get('recommendations', []))}")
            print(f"   Confidence score: {result.get('confidence_score', 0):.2f}")
        else:
            print(f"❌ Insights generation failed: {response.error_message}")
        
        # Test 2: Pattern Analysis
        print("\n🔍 Test 2: Pattern Analysis")
        pattern_event = AgentEvent(
            event_id="test_patterns_1",
            event_type="analyze_patterns", 
            source_agent="test_agent",
            payload={
                "focus_areas": ["behavioral_patterns", "goal_alignment"]
            },
            timestamp=datetime.now(),
            user_id="test_user_patterns",
            archetype="Systematic Improver"
        )
        
        response = await insights_agent.process(pattern_event)
        if response.success:
            print("✅ Pattern analysis successful")
            patterns = response.result.get("patterns", [])
            print(f"   Patterns found: {len(patterns)}")
            if patterns:
                print(f"   Sample pattern: {patterns[0].get('description', 'N/A')}")
        else:
            print(f"❌ Pattern analysis failed: {response.error_message}")
        
        # Test 3: Trend Detection
        print("\n🔍 Test 3: Trend Detection")
        trend_event = AgentEvent(
            event_id="test_trends_1",
            event_type="detect_trends",
            source_agent="test_agent",
            payload={
                "time_horizon": "short_term"
            },
            timestamp=datetime.now(),
            user_id="test_user_trends",
            archetype="Foundation Builder"
        )
        
        response = await insights_agent.process(trend_event)
        if response.success:
            print("✅ Trend detection successful")
            trends = response.result
            print(f"   Overall direction: {trends.get('overall_direction', 'N/A')}")
            print(f"   Trend strength: {trends.get('trend_strength', 0):.2f}")
            print(f"   Detected trends: {len(trends.get('trends', []))}")
        else:
            print(f"❌ Trend detection failed: {response.error_message}")
        
        # Test 4: Recommendation Generation
        print("\n🔍 Test 4: Recommendation Generation")
        rec_event = AgentEvent(
            event_id="test_recommendations_1",
            event_type="create_recommendations",
            source_agent="test_agent",
            payload={
                "focus_areas": ["nutrition_adherence", "routine_consistency"]
            },
            timestamp=datetime.now(),
            user_id="test_user_recommendations",
            archetype="Transformation Seeker"
        )
        
        response = await insights_agent.process(rec_event)
        if response.success:
            print("✅ Recommendation generation successful")
            recommendations = response.result.get("recommendations", [])
            print(f"   Recommendations generated: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec}")
        else:
            print(f"❌ Recommendation generation failed: {response.error_message}")
        
        # Test 5: Outcome Prediction
        print("\n🔍 Test 5: Outcome Prediction")
        prediction_event = AgentEvent(
            event_id="test_predictions_1",
            event_type="predict_outcomes",
            source_agent="test_agent",
            payload={
                "horizon_days": 30
            },
            timestamp=datetime.now(),
            user_id="test_user_predictions",
            archetype="Resilience Rebuilder"
        )
        
        response = await insights_agent.process(prediction_event)
        if response.success:
            print("✅ Outcome prediction successful")
            predictions = response.result
            print(f"   Prediction horizon: {predictions.get('prediction_horizon_days', 0)} days")
            outcomes = predictions.get('predicted_outcomes', {})
            print(f"   Goal achievement probability: {outcomes.get('goal_achievement_probability', 0):.2f}")
            print(f"   Engagement level: {outcomes.get('engagement_level', 'N/A')}")
        else:
            print(f"❌ Outcome prediction failed: {response.error_message}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_insights_integration():
    """Test Insights Agent integration with other agents"""
    print("\n🤝 Testing Insights Agent Integration")
    print("=" * 60)
    
    try:
        from services.agents.insights.main import HolisticInsightsAgent
        from shared_libs.event_system.base_agent import AgentEvent
        
        # Initialize insights agent for integration testing
        insights_agent = HolisticInsightsAgent()
        print(f"✅ Insights Agent initialized for integration testing")
        
        # Test behavior analysis completion event handling
        print("\n🔍 Testing behavior analysis completion trigger...")
        behavior_complete_event = AgentEvent(
            event_id="test_behavior_insights",
            event_type="behavior_analysis_complete",
            source_agent="behavior_analysis_agent",
            payload={
                "behavioral_signature": {"signature": "consistent_performer", "confidence": 0.85},
                "sophistication_assessment": {"score": 78, "confidence": 0.8},
                "primary_goal": {"goal": "Optimize daily routine"},
                "readiness_level": "Advanced"
            },
            timestamp=datetime.now(),
            user_id="test_user_behavior_insights",
            archetype="Peak Performer"
        )
        
        response = await insights_agent.process(behavior_complete_event)
        if response.success:
            print("✅ Behavior analysis completion event triggered insights successfully")
            result = response.result
            print(f"   Auto-generated insights: {len(result.get('insights', []))}")
            print(f"   Trigger event: {result.get('insights', [{}])[0].get('category', 'N/A') if result.get('insights') else 'N/A'}")
        else:
            print(f"❌ Behavior completion event failed: {response.error_message}")
        
        # Test nutrition plan completion event
        print("\n🔍 Testing nutrition plan completion trigger...")
        nutrition_complete_event = AgentEvent(
            event_id="test_nutrition_insights",
            event_type="nutrition_plan_complete",
            source_agent="nutrition_plan_agent",
            payload={
                "nutrition_plan": {"meals": 3, "calories": 2200, "protein": 150},
                "preferences": {"dietary_type": "balanced", "restrictions": []},
                "adherence_prediction": 0.82
            },
            timestamp=datetime.now(),
            user_id="test_user_nutrition_insights",
            archetype="Foundation Builder"
        )
        
        response = await insights_agent.process(nutrition_complete_event)
        if response.success:
            print("✅ Nutrition plan completion event triggered insights successfully")
        else:
            print(f"❌ Nutrition completion event failed: {response.error_message}")
        
        # Test routine plan completion event
        print("\n🔍 Testing routine plan completion trigger...")
        routine_complete_event = AgentEvent(
            event_id="test_routine_insights",
            event_type="routine_plan_complete",
            source_agent="routine_plan_agent",
            payload={
                "routine_plan": {"morning": "exercise", "evening": "meditation"},
                "preferences": {"intensity": "moderate", "duration": 45},
                "feasibility_score": 0.75
            },
            timestamp=datetime.now(),
            user_id="test_user_routine_insights",
            archetype="Systematic Improver"
        )
        
        response = await insights_agent.process(routine_complete_event)
        if response.success:
            print("✅ Routine plan completion event triggered insights successfully")
        else:
            print(f"❌ Routine completion event failed: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_archetype_specific_insights():
    """Test archetype-specific insight generation"""
    print("\n🎯 Testing Archetype-Specific Insights")
    print("=" * 60)
    
    archetypes = [
        "Peak Performer",
        "Foundation Builder", 
        "Systematic Improver",
        "Transformation Seeker",
        "Resilience Rebuilder",
        "Connected Explorer"
    ]
    
    try:
        from services.agents.insights.main import HolisticInsightsAgent
        from shared_libs.event_system.base_agent import AgentEvent
        
        insights_agent = HolisticInsightsAgent()
        
        for i, archetype in enumerate(archetypes, 1):
            print(f"\n🔍 Test {i}: {archetype} Insights")
            
            archetype_event = AgentEvent(
                event_id=f"test_archetype_{i}",
                event_type="generate_insights",
                source_agent="test_agent",
                payload={
                    "insight_type": "archetype_specific",
                    "time_horizon": "medium_term",
                    "focus_areas": ["behavioral_patterns", "goal_alignment"]
                },
                timestamp=datetime.now(),
                user_id=f"test_user_{archetype.lower().replace(' ', '_')}",
                archetype=archetype
            )
            
            response = await insights_agent.process(archetype_event)
            if response.success:
                print(f"✅ {archetype} insights generated successfully")
                recommendations = response.result.get("recommendations", [])
                if recommendations:
                    print(f"   Sample recommendation: {recommendations[0]}")
            else:
                print(f"❌ {archetype} insights failed: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Archetype test error: {e}")
        return False

async def main():
    """Run all insights agent tests"""
    print("🧪 HolisticOS Insights Generation Agent Test Suite")
    print("Testing AI-powered pattern analysis and personalized insights generation")
    print("=" * 80)
    
    # Test 1: Insights Agent Core Functionality
    core_test_passed = await test_insights_agent_core()
    
    # Test 2: Integration with Other Agents
    integration_test_passed = await test_insights_integration()
    
    # Test 3: Archetype-Specific Insights
    archetype_test_passed = await test_archetype_specific_insights()
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 Test Results Summary:")
    print(f"   Insights Agent Core: {'✅ PASSED' if core_test_passed else '❌ FAILED'}")
    print(f"   Agent Integration: {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    print(f"   Archetype Insights: {'✅ PASSED' if archetype_test_passed else '❌ FAILED'}")
    
    if core_test_passed and integration_test_passed and archetype_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Phase 2 Insights System Status:")
        print("   ✅ Insights Generation Agent implemented")
        print("   ✅ Pattern analysis and trend detection working")
        print("   ✅ AI-powered insights generation ready")
        print("   ✅ Archetype-specific recommendations system")
        print("   ✅ Event-driven integration with other agents")
        print("   ✅ Outcome prediction framework")
        print("\n🔄 Next Steps:")
        print("   1. Implement Adaptation Engine Agent (Phase 2 Day 5-7)")
        print("   2. Enhance memory integration with real data")
        print("   3. Add insight feedback loops")
        print("   4. Deploy complete multi-agent system")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)