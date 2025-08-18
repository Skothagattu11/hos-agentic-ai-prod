#!/usr/bin/env python3
"""
Debug script to test and verify the complete HolisticOS flow
Tests the expected user journey with detailed debugging
"""

import asyncio
import sys
import os
import json
import aiohttp
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test configuration
TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
BASE_URL = "http://localhost:8001"
ARCHETYPE = "Foundation Builder"

def print_section(title, emoji="🔍"):
    """Print formatted section header"""
    print(f"\n{emoji} {title}")
    print("=" * 60)

async def check_database_state():
    """Check the current state of database tables"""
    print_section("DATABASE STATE CHECK", "🗄️")
    
    try:
        from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter
        
        # Connect to database
        db = SupabaseAsyncPGAdapter()
        await db.connect()
        
        # Check holistic_analysis_results
        query = """
            SELECT COUNT(*) as count FROM holistic_analysis_results 
            WHERE user_id = $1
        """
        result = await db.fetchval(query, TEST_USER_ID)
        print(f"📊 Analysis Results Count: {result or 0}")
        
        # Check for today's analyses
        today = datetime.now(timezone.utc).date().isoformat()
        query = """
            SELECT analysis_type, archetype, created_at 
            FROM holistic_analysis_results 
            WHERE user_id = $1 AND created_at >= $2
            ORDER BY created_at DESC
        """
        results = await db.fetch(query, TEST_USER_ID, f"{today}T00:00:00Z")
        
        if results:
            print(f"📅 Today's Analyses ({len(results)} found):")
            for r in results:
                print(f"   • {r['analysis_type']}: {r['archetype']} at {r['created_at']}")
        else:
            print("⚠️  No analyses found for today")
        
        # Check insights
        query = """
            SELECT COUNT(*) as count FROM holistic_insights 
            WHERE user_id = $1
        """
        result = await db.fetchval(query, TEST_USER_ID)
        print(f"✨ Total Insights Count: {result or 0}")
        
        # Check memory tables
        for table in ['holistic_working_memory', 'holistic_shortterm_memory', 
                     'holistic_longterm_memory', 'holistic_meta_memory']:
            query = f"SELECT COUNT(*) as count FROM {table} WHERE user_id = $1"
            result = await db.fetchval(query, TEST_USER_ID)
            print(f"🧠 {table}: {result or 0} records")
        
        await db.close()
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()

async def test_routine_generation():
    """Test routine generation with behavior analysis"""
    print_section("ROUTINE GENERATION TEST", "🏃")
    
    try:
        request_data = {
            "archetype": ARCHETYPE,
            "preferences": {
                "workout_time": "morning",
                "duration_minutes": 30,
                "intensity": "moderate"
            }
        }
        
        print("📤 Sending routine generation request...")
        print(f"   User: {TEST_USER_ID[:8]}...")
        print(f"   Archetype: {ARCHETYPE}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/user/{TEST_USER_ID}/routine/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                print(f"📥 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Check metadata
                    metadata = result.get('generation_metadata', {})
                    print("\n📋 Generation Metadata:")
                    print(f"   • Analysis Type: {metadata.get('analysis_type', 'unknown')}")
                    print(f"   • Memory Quality: {metadata.get('memory_quality', 'unknown')}")
                    print(f"   • Data Points: {metadata.get('new_data_points', 0)}")
                    print(f"   • Cached: {result.get('cached', False)}")
                    
                    # Check if routine was generated
                    if result.get('routine'):
                        print("\n✅ Routine Generated Successfully")
                        routine = result['routine']
                        if 'weekly_schedule' in routine:
                            print(f"   • Days: {len(routine['weekly_schedule'])}")
                    else:
                        print("\n⚠️ No routine in response")
                    
                    return True
                else:
                    error = await response.text()
                    print(f"\n❌ Failed with status {response.status}")
                    print(f"   Error: {error[:200]}...")
                    return False
                    
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_insights_generation():
    """Test insights generation"""
    print_section("INSIGHTS GENERATION TEST", "💡")
    
    try:
        request_data = {
            "user_id": TEST_USER_ID,
            "archetype": ARCHETYPE,
            "force_refresh": True
        }
        
        print("📤 Sending insights generation request...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/v1/insights/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                print(f"📥 Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('success'):
                        insights = result.get('insights', [])
                        print(f"\n✅ Generated {len(insights)} insights")
                        print(f"   • Source: {result.get('source', 'unknown')}")
                        
                        # Show first few insights
                        for i, insight in enumerate(insights[:3], 1):
                            print(f"\n   Insight {i}:")
                            print(f"     Title: {insight.get('title', 'N/A')}")
                            print(f"     Type: {insight.get('type', 'N/A')}")
                            print(f"     Priority: {insight.get('priority', 'N/A')}")
                        
                        return True
                    else:
                        print("\n⚠️ Insights API returned success=false")
                        return False
                else:
                    error = await response.text()
                    print(f"\n❌ Failed with status {response.status}")
                    print(f"   Error: {error[:200]}...")
                    return False
                    
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_log_files():
    """Check what log files were created"""
    print_section("LOG FILES CHECK", "📁")
    
    import glob
    from datetime import datetime
    
    logs_dir = "logs"
    
    # Check for analysis logs
    output_files = glob.glob(f"{logs_dir}/output_*.txt")
    if output_files:
        output_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        print(f"📄 Analysis Output Files ({len(output_files)} total):")
        for file in output_files[:3]:
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            size = os.path.getsize(file)
            print(f"   • {os.path.basename(file)}: {size:,} bytes - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for insights logs
    insights_files = glob.glob(f"{logs_dir}/insights_*.txt")
    if insights_files:
        insights_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        print(f"\n✨ Insights Files ({len(insights_files)} total):")
        for file in insights_files[:3]:
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            size = os.path.getsize(file)
            print(f"   • {os.path.basename(file)}: {size:,} bytes - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for agent handoff logs
    handoff_dir = f"{logs_dir}/agent_handoffs"
    if os.path.exists(handoff_dir):
        handoff_files = glob.glob(f"{handoff_dir}/*.txt")
        if handoff_files:
            print(f"\n🤝 Agent Handoff Files ({len(handoff_files)} total):")
            handoff_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            for file in handoff_files[:3]:
                print(f"   • {os.path.basename(file)}")

async def main():
    """Main test flow"""
    print("\n" + "="*60)
    print("🚀 HOLISTICOS MVP DEBUG TEST")
    print("="*60)
    print(f"\nTest User: {TEST_USER_ID[:8]}...")
    print(f"Archetype: {ARCHETYPE}")
    print(f"Server: {BASE_URL}")
    
    # Step 1: Check initial database state
    await check_database_state()
    
    # Step 2: Test routine generation (should trigger behavior analysis)
    success = await test_routine_generation()
    if not success:
        print("\n⚠️ Routine generation failed - stopping tests")
        return
    
    # Wait a moment for async processing
    await asyncio.sleep(2)
    
    # Step 3: Test insights generation
    await test_insights_generation()
    
    # Wait for any async operations
    await asyncio.sleep(2)
    
    # Step 4: Check final database state
    print("\n" + "="*60)
    print("FINAL STATE CHECK")
    await check_database_state()
    
    # Step 5: Check log files
    await check_log_files()
    
    print("\n" + "="*60)
    print("✅ DEBUG TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()