"""
Test Insights Integration (MVP)
Simple test to verify insights extraction and API work
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
TEST_ARCHETYPE = "Foundation Builder"

async def test_insights_generation():
    """Test the complete insights flow"""
    
    print("\n" + "="*60)
    print("🧪 INSIGHTS INTEGRATION TEST (MVP)")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Test generating insights
        print("\n1️⃣ Testing Insights Generation...")
        print("-" * 40)
        
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/insights/generate",
                json={
                    "user_id": TEST_USER_ID,
                    "archetype": TEST_ARCHETYPE,
                    "force_refresh": False
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Insights generated successfully!")
                    print(f"   Source: {data['source']}")
                    print(f"   Count: {data['count']} insights")
                    
                    if data['insights']:
                        print("\n   Sample Insights:")
                        for i, insight in enumerate(data['insights'][:3], 1):
                            print(f"   {i}. {insight['title']}")
                            print(f"      Type: {insight['type']}, Priority: {insight['priority']}")
                            print(f"      Actionability: {insight['actionability_score']:.1f}")
                            print()
                    
                    # Store first insight ID for later tests
                    first_insight_id = data['insights'][0]['id'] if data['insights'] else None
                else:
                    print(f"❌ Failed to generate insights: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    first_insight_id = None
                    
        except Exception as e:
            print(f"❌ Error generating insights: {str(e)}")
            first_insight_id = None
        
        # 2. Test getting cached insights
        print("\n2️⃣ Testing Get Cached Insights...")
        print("-" * 40)
        
        try:
            async with session.get(
                f"{BASE_URL}/api/v1/insights/{TEST_USER_ID}?limit=5"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Retrieved {data['count']} cached insights")
                    print(f"   Source: {data['source']}")
                else:
                    print(f"❌ Failed to get insights: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error getting insights: {str(e)}")
        
        # 3. Test acknowledging an insight
        if first_insight_id:
            print("\n3️⃣ Testing Acknowledge Insight...")
            print("-" * 40)
            
            try:
                async with session.patch(
                    f"{BASE_URL}/api/v1/insights/{first_insight_id}/acknowledge"
                ) as response:
                    if response.status == 200:
                        print(f"✅ Insight acknowledged successfully")
                    else:
                        print(f"❌ Failed to acknowledge insight: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error acknowledging insight: {str(e)}")
        
        # 4. Test rating an insight
        if first_insight_id:
            print("\n4️⃣ Testing Rate Insight...")
            print("-" * 40)
            
            try:
                async with session.post(
                    f"{BASE_URL}/api/v1/insights/{first_insight_id}/rate",
                    params={
                        "rating": 4,
                        "feedback": "Very helpful insight!"
                    }
                ) as response:
                    if response.status == 200:
                        print(f"✅ Insight rated 4/5 successfully")
                    else:
                        print(f"❌ Failed to rate insight: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error rating insight: {str(e)}")
        
        # 5. Skip routine analysis test (endpoint not available in MVP)
        print("\n5️⃣ Routine Analysis Test - SKIPPED (Not implemented in MVP)")
        print("-" * 40)
        
        # 6. Verify insights were created from routine analysis
        print("\n6️⃣ Verifying Insights from Routine Analysis...")
        print("-" * 40)
        
        try:
            async with session.get(
                f"{BASE_URL}/api/v1/insights/{TEST_USER_ID}?limit=20"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Count insights by type
                    type_counts = {}
                    for insight in data['insights']:
                        insight_type = insight['type']
                        type_counts[insight_type] = type_counts.get(insight_type, 0) + 1
                    
                    print(f"✅ Total insights: {data['count']}")
                    print("   Insights by type:")
                    for itype, count in type_counts.items():
                        print(f"   - {itype}: {count}")
                else:
                    print(f"❌ Failed to verify insights: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error verifying insights: {str(e)}")
    
    print("\n" + "="*60)
    print("🎯 TEST COMPLETE")
    print("="*60)

async def test_threshold_behavior():
    """Test that 50-item threshold is working"""
    
    print("\n" + "="*60)
    print("🧪 TESTING 50-ITEM THRESHOLD")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. First call - should use fresh or cached based on data
        print("\n1️⃣ First insights generation...")
        async with session.post(
            f"{BASE_URL}/api/v1/insights/generate",
            json={
                "user_id": TEST_USER_ID,
                "archetype": TEST_ARCHETYPE,
                "force_refresh": False
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Source: {data['source']}")
        
        # 2. Immediate second call - should use cached
        print("\n2️⃣ Immediate second call (should be cached)...")
        async with session.post(
            f"{BASE_URL}/api/v1/insights/generate",
            json={
                "user_id": TEST_USER_ID,
                "archetype": TEST_ARCHETYPE,
                "force_refresh": False
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Source: {data['source']}")
                if data['source'] == 'cached':
                    print("   ✅ Correctly using cached analysis!")
                else:
                    print("   ⚠️ Expected cached but got fresh")
        
        # 3. Force refresh
        print("\n3️⃣ Force refresh...")
        async with session.post(
            f"{BASE_URL}/api/v1/insights/generate",
            json={
                "user_id": TEST_USER_ID,
                "archetype": TEST_ARCHETYPE,
                "force_refresh": True
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Source: {data['source']}")
                if data['source'] == 'fresh':
                    print("   ✅ Force refresh working!")

if __name__ == "__main__":
    print("\n🚀 Starting Insights Integration Test...")
    print("Make sure the server is running on http://localhost:8001")
    
    # Run tests
    asyncio.run(test_insights_generation())
    asyncio.run(test_threshold_behavior())
    
    print("\n✅ All tests completed!")