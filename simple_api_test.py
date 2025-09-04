#!/usr/bin/env python3
"""
Simple API test to verify time_blocks relationship
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_direct():
    """Test database directly using Supabase"""
    print("🗄️ Testing Database Direct Query")
    print("=" * 40)
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials in .env file")
            return
            
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")
        
        # Test the same query the API uses
        profile_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
        
        print(f"🔍 Querying plan_items for profile: {profile_id}")
        
        result = supabase.table("plan_items")\
            .select("""
                id, title, time_block_id, scheduled_time,
                time_blocks!fk_plan_items_time_block_id (
                    id,
                    block_title,
                    time_range
                )
            """)\
            .eq("profile_id", profile_id)\
            .order("scheduled_time")\
            .limit(10)\
            .execute()
        
        if result.data:
            print(f"✅ Database query successful: {len(result.data)} items")
            
            items_with_blocks = 0
            items_without_blocks = 0
            
            for i, item in enumerate(result.data):
                has_time_blocks = item.get('time_blocks') is not None
                if has_time_blocks:
                    items_with_blocks += 1
                    print(f"  ✅ {i+1}. '{item['title']}' -> '{item['time_blocks']['block_title']}'")
                else:
                    items_without_blocks += 1
                    print(f"  ❌ {i+1}. '{item['title']}' -> No time_blocks (time_block_id: {item['time_block_id']})")
            
            print(f"\n📊 Summary:")
            print(f"   - Items with time_blocks: {items_with_blocks}")
            print(f"   - Items without time_blocks: {items_without_blocks}")
            
            if items_with_blocks > 0:
                print("🎉 SUCCESS: Database relationships are working!")
            else:
                print("❌ ISSUE: No time_blocks relationships found")
                
                # Show what time_blocks exist
                time_blocks = supabase.table("time_blocks")\
                    .select("id, block_title, time_range, analysis_result_id")\
                    .eq("profile_id", profile_id)\
                    .limit(5)\
                    .execute()
                
                if time_blocks.data:
                    print(f"\n🏗️ Available time_blocks ({len(time_blocks.data)}):")
                    for tb in time_blocks.data:
                        print(f"   - {tb['block_title']} ({tb['analysis_result_id'][:8]}...)")
                else:
                    print("❌ No time_blocks found for this profile")
        else:
            print("❌ No data returned from database")
            
    except ImportError:
        print("❌ Supabase library not available")
    except Exception as e:
        print(f"❌ Database query failed: {e}")

def test_api_endpoint():
    """Test the available-items API endpoint"""
    print("🧪 Testing API Endpoint for Time Blocks")
    print("=" * 50)
    
    # Configuration
    BASE_URL = "http://localhost:8002/api/calendar"
    PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
    DATE = "2025-09-03"
    
    # Test the API endpoint
    url = f"{BASE_URL}/available-items/{PROFILE_ID}?date={DATE}&include_calendar_status=true"
    print(f"🌐 Calling: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📋 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            print(f"📊 Total items: {data.get('total_items', 0)}")
            
            plan_items = data.get('plan_items', [])
            print(f"📋 Plan items count: {len(plan_items)}")
            
            if plan_items:
                # Analyze the first few items
                print("\n🔍 Sample items analysis:")
                
                items_with_time_blocks = 0
                items_without_time_blocks = 0
                
                for i, item in enumerate(plan_items[:5]):  # Check first 5
                    has_time_blocks = 'time_blocks' in item and item['time_blocks'] is not None
                    time_block_id = item.get('time_block_id')
                    
                    if has_time_blocks:
                        items_with_time_blocks += 1
                        block_title = item['time_blocks'].get('block_title', 'No title')
                        print(f"  ✅ {i+1}. '{item['title']}' -> '{block_title}'")
                    else:
                        items_without_time_blocks += 1
                        print(f"  ❌ {i+1}. '{item['title']}' -> No time_blocks (time_block_id: {time_block_id})")
                
                # Summary
                total_checked = min(5, len(plan_items))
                print(f"\n📊 Sample Analysis ({total_checked} items):")
                print(f"   - With time_blocks: {items_with_time_blocks}")
                print(f"   - Without time_blocks: {items_without_time_blocks}")
                
                if items_with_time_blocks > 0:
                    print("🎉 SUCCESS: API is returning time_blocks data!")
                    print("   The JOIN is working and relationships exist.")
                else:
                    print("❌ ISSUE: No time_blocks data in response")
                    print("   Either relationships are missing or JOIN isn't working.")
                    
                    # Show raw structure of first item
                    if plan_items:
                        print(f"\n🔍 Raw structure of first item:")
                        first_item = plan_items[0]
                        print(f"   Keys: {list(first_item.keys())}")
                        print(f"   time_block_id: {first_item.get('time_block_id')}")
                        print(f"   time_blocks: {first_item.get('time_blocks')}")
            else:
                print("❌ No plan items returned")
                
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure the API server is running on localhost:8002")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 Simple Time Blocks API Test")
    print("=" * 50)
    
    # Test 1: Database direct (most reliable)
    test_database_direct()
    
    # Test 2: API endpoint (if available)
    print("\n")
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")
    print("\n💡 If you see time_blocks data, the fix is working!")
    print("💡 If not, you may need to:")
    print("   1. Run the database constraints SQL")
    print("   2. Clear and re-extract the plan items")
    print("   3. Check if the API server is running the updated code")

if __name__ == "__main__":
    main()