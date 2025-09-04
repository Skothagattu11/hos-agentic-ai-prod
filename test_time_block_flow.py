#!/usr/bin/env python3
"""
Test script to verify the complete time_blocks and plan_items flow
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Import from current directory structure
from services.plan_extraction_service import PlanExtractionService
from supabase import create_client

async def test_complete_flow():
    """Test the complete extraction and API flow"""
    print("🧪 Testing Complete Time Blocks Flow")
    print("=" * 50)
    
    # Configuration
    TEST_PROFILE_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
    
    try:
        # Initialize services
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return False
            
        supabase = create_client(supabase_url, supabase_key)
        extraction_service = PlanExtractionService()
        
        print("✅ Services initialized")
        
        # Step 1: Find existing analysis results
        print("\n📋 Step 1: Finding analysis results...")
        analysis_results = supabase.table("holistic_analysis_results")\
            .select("id, analysis_type, archetype, created_at")\
            .eq("user_id", TEST_PROFILE_ID)\
            .order("created_at", desc=True)\
            .limit(2)\
            .execute()
        
        if not analysis_results.data:
            print("❌ No analysis results found for user")
            return False
            
        print(f"✅ Found {len(analysis_results.data)} analysis results")
        for result in analysis_results.data:
            print(f"   - {result['id']}: {result['analysis_type']} ({result['archetype']})")
        
        # Step 2: Clear existing data for clean test
        print("\n🧹 Step 2: Clearing existing plan_items and time_blocks...")
        
        # Delete plan_items first (due to foreign key)
        delete_items = supabase.table("plan_items")\
            .delete()\
            .eq("profile_id", TEST_PROFILE_ID)\
            .execute()
        print(f"✅ Deleted {len(delete_items.data or [])} plan_items")
        
        # Delete time_blocks
        delete_blocks = supabase.table("time_blocks")\
            .delete()\
            .eq("profile_id", TEST_PROFILE_ID)\
            .execute()
        print(f"✅ Deleted {len(delete_blocks.data or [])} time_blocks")
        
        # Step 3: Extract plan items for the latest analysis
        print("\n🔄 Step 3: Extracting plan items with time blocks...")
        test_analysis_id = analysis_results.data[0]['id']
        print(f"Using analysis ID: {test_analysis_id}")
        
        extracted_items = await extraction_service.extract_and_store_plan_items(
            test_analysis_id, 
            TEST_PROFILE_ID
        )
        
        print(f"✅ Extracted and stored {len(extracted_items)} plan items")
        
        # Step 4: Verify database relationships
        print("\n🔍 Step 4: Verifying database relationships...")
        
        # Check time_blocks table
        time_blocks = supabase.table("time_blocks")\
            .select("id, block_title, time_range, analysis_result_id")\
            .eq("profile_id", TEST_PROFILE_ID)\
            .eq("analysis_result_id", test_analysis_id)\
            .execute()
        
        print(f"✅ Created {len(time_blocks.data or [])} time blocks:")
        for block in (time_blocks.data or []):
            print(f"   - {block['block_title']} ({block['time_range']})")
        
        # Check plan_items relationships
        plan_items = supabase.table("plan_items")\
            .select("id, title, time_block_id, scheduled_time")\
            .eq("profile_id", TEST_PROFILE_ID)\
            .eq("analysis_result_id", test_analysis_id)\
            .execute()
        
        items_with_blocks = [item for item in (plan_items.data or []) if item['time_block_id']]
        items_without_blocks = [item for item in (plan_items.data or []) if not item['time_block_id']]
        
        print(f"✅ Plan items relationship status:")
        print(f"   - Total items: {len(plan_items.data or [])}")
        print(f"   - With time_block_id: {len(items_with_blocks)}")
        print(f"   - Missing time_block_id: {len(items_without_blocks)}")
        
        if items_without_blocks:
            print("⚠️  Items missing time_block_id:")
            for item in items_without_blocks[:3]:  # Show first 3
                print(f"     - {item['title']} ({item['scheduled_time']})")
        
        # Step 5: Test API endpoint
        print("\n🌐 Step 5: Testing API endpoint...")
        
        # Simulate the API call
        api_result = supabase.table("plan_items")\
            .select("""
                *,
                time_blocks!fk_plan_items_time_block_id (
                    id,
                    block_title,
                    time_range,
                    purpose
                )
            """)\
            .eq("profile_id", TEST_PROFILE_ID)\
            .eq("analysis_result_id", test_analysis_id)\
            .order("scheduled_time")\
            .execute()
        
        api_items_with_blocks = [
            item for item in (api_result.data or []) 
            if item.get('time_blocks')
        ]
        
        print(f"✅ API query results:")
        print(f"   - Total items returned: {len(api_result.data or [])}")
        print(f"   - Items with time_blocks data: {len(api_items_with_blocks)}")
        
        # Show sample with time block data
        if api_items_with_blocks:
            sample = api_items_with_blocks[0]
            print(f"   - Sample: '{sample['title']}' -> '{sample['time_blocks']['block_title']}'")
        
        # Step 6: Summary
        print("\n📊 Summary:")
        success_rate = len(items_with_blocks) / len(plan_items.data or []) * 100 if plan_items.data else 0
        
        print(f"   - Extraction Success: {len(extracted_items)} items stored")
        print(f"   - Time Block Creation: {len(time_blocks.data or [])} blocks")
        print(f"   - Relationship Success: {success_rate:.1f}% ({len(items_with_blocks)}/{len(plan_items.data or [])})")
        print(f"   - API Query Success: {len(api_items_with_blocks)} items with joined data")
        
        # Determine overall success
        overall_success = (
            len(time_blocks.data or []) > 0 and
            success_rate >= 80 and  # At least 80% of items should have relationships
            len(api_items_with_blocks) > 0
        )
        
        if overall_success:
            print("\n🎉 OVERALL: SUCCESS - Time blocks flow is working correctly!")
            return True
        else:
            print("\n❌ OVERALL: PARTIAL SUCCESS - Some issues remain")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_complete_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! The time blocks flow is working correctly.")
        print("\nNext steps:")
        print("1. The frontend should now display proper time block names")
        print("2. Items should be grouped by time blocks instead of 'unscheduled'")
        print("3. You can refresh your browser to see the changes")
    else:
        print("⚠️  Some issues were found. Check the output above for details.")
        print("\nRecommendations:")
        print("1. Run the database constraints SQL script")
        print("2. Check the extraction service logs for mapping issues")
        print("3. Verify the analysis result content structure")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)