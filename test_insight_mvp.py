#!/usr/bin/env python3
"""
MVP Test Script for Insights System
Tests the insights functionality after fixing the KeyError 'data' issue
"""
import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

async def test_insights_mvp():
    """MVP test for insights system - tests the fixed adapter"""
    print("🎯 [INSIGHTS_MVP_TEST] Starting comprehensive insights test...")
    
    try:
        # Test 1: Service Import
        print("\n1️⃣ Testing service imports...")
        try:
            from services.insights_extraction_service import insights_service
            print("✅ insights_service imported successfully")
        except Exception as e:
            print(f"❌ Failed to import insights_service: {e}")
            return False
        
        # Test 2: Database Connection
        print("\n2️⃣ Testing database connection...")
        try:
            db = await insights_service._ensure_db_connection()
            print(f"✅ Database connected: {type(db)}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Test 3: Store Simple Insight (This was failing with KeyError 'data')
        print("\n3️⃣ Testing insight storage (KeyError 'data' fix)...")
        user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
        title = f"MVP Test Insight - {datetime.now().strftime('%H:%M:%S')}"
        content = "This tests the fixed SupabaseAsyncPGAdapter that now includes 'holistic_insights' in the table list for INSERT operations."
        
        try:
            success = await insights_service.store_simple_insight(
                user_id=user_id,
                title=title,
                content=content,
                insight_type="mvp_test",
                archetype="Foundation Builder"
            )
            
            if success:
                print("✅ Insight stored successfully - KeyError 'data' FIXED!")
            else:
                print("❌ Insight storage returned False")
                return False
                
        except Exception as e:
            print(f"❌ Insight storage failed: {e}")
            print(f"Error type: {type(e)}")
            return False
        
        # Test 4: Retrieve Insights
        print("\n4️⃣ Testing insight retrieval...")
        try:
            insights = await insights_service.get_user_insights(user_id, limit=5)
            print(f"✅ Retrieved {len(insights)} insights")
            
            if insights:
                for i, insight in enumerate(insights[:2], 1):
                    print(f"   {i}. {insight['insight_title'][:50]}...")
            else:
                print("⚠️ No insights found")
                
        except Exception as e:
            print(f"❌ Insight retrieval failed: {e}")
            return False
        
        # Test 5: Extract Insights from Mock Analysis
        print("\n5️⃣ Testing insight extraction from analysis...")
        try:
            mock_analysis = {
                "recommendations": [
                    "Focus on consistent sleep schedule",
                    "Increase daily water intake", 
                    "Add 10 minutes of morning stretching"
                ],
                "primary_goal": {"goal": "Improve energy levels through better habits"}
            }
            
            insights_count = await insights_service.extract_and_store_insights(
                analysis_result=mock_analysis,
                analysis_type="behavior_analysis",
                user_id=user_id,
                archetype="Foundation Builder"
            )
            
            print(f"✅ Extracted and stored {insights_count} insights from mock analysis")
            
        except Exception as e:
            print(f"❌ Insight extraction failed: {e}")
            return False
        
        # Test 6: Final Verification
        print("\n6️⃣ Final verification...")
        try:
            final_insights = await insights_service.get_user_insights(user_id, limit=10)
            total_insights = len(final_insights)
            mvp_test_insights = len([i for i in final_insights if 'mvp_test' in i.get('insight_type', '')])
            
            print(f"✅ Total insights for user: {total_insights}")
            print(f"✅ MVP test insights created: {mvp_test_insights}")
            
            return True
            
        except Exception as e:
            print(f"❌ Final verification failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ [CRITICAL_ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting MVP Insights Test...")
    result = asyncio.run(test_insights_mvp())
    
    if result:
        print("\n🎉 [SUCCESS] MVP INSIGHTS TEST PASSED!")
        print("✅ KeyError 'data' issue has been resolved")
        print("✅ Insights system is working end-to-end")
    else:
        print("\n💥 [FAILED] MVP INSIGHTS TEST FAILED")
        print("❌ Check the errors above for details")