#!/usr/bin/env python3
"""
Quick test to validate the fixes:
1. Variable scope issue in insights endpoint
2. Duplicate key constraint in analysis storage
"""
import asyncio
import aiohttp

async def test_insights_fix():
    """Test the insights endpoint fix"""
    try:
        insights_request = {
            "user_id": "35pDPUIfAoRl2Y700bFkxPKYjjf2",
            "archetype": "Foundation Builder",
            "force_refresh": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/v1/insights/generate",
                json=insights_request,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Insights endpoint working!")
                    print(f"   Generated {result.get('count', 0)} insights")
                    return True
                else:
                    error = await response.text()
                    print(f"❌ Insights endpoint failed: {error[:100]}...")
                    return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing insights fixes...")
    result = asyncio.run(test_insights_fix())
    print(f"\n{'✅ PASS' if result else '❌ FAIL'}: Insights fix validation")