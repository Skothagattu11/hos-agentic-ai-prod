"""
Verify that extraction actually stored data in database
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def verify_extraction():
    """Check if plan_items and time_blocks were created"""

    analysis_id = "321cf069-9e66-4c22-89e4-69ac3de1fec0"  # From latest extraction test
    user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

    # Create Supabase client with SERVICE_KEY to bypass RLS
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")  # Use SERVICE_KEY to bypass RLS
    )

    print(f"\n🔍 Checking extraction results for analysis_id: {analysis_id}\n")

    # Check plan_items by analysis_id
    plan_items_result = supabase.table('plan_items')\
        .select('*', count='exact')\
        .eq('analysis_result_id', analysis_id)\
        .execute()

    plan_items_count = plan_items_result.count if plan_items_result.count else 0
    print(f"📋 Plan Items (by analysis_id): {plan_items_count} items found")

    # Also check by profile_id to see if there's ANY data for this user
    plan_items_by_user = supabase.table('plan_items')\
        .select('*', count='exact')\
        .eq('profile_id', user_id)\
        .execute()

    plan_items_user_count = plan_items_by_user.count if plan_items_by_user.count else 0
    print(f"📋 Plan Items (by user_id): {plan_items_user_count} items found")

    # Check time_blocks by analysis_id
    time_blocks_result = supabase.table('time_blocks')\
        .select('*', count='exact')\
        .eq('analysis_result_id', analysis_id)\
        .execute()

    time_blocks_count = time_blocks_result.count if time_blocks_result.count else 0
    print(f"⏰ Time Blocks (by analysis_id): {time_blocks_count} blocks found")

    # Also check by profile_id
    time_blocks_by_user = supabase.table('time_blocks')\
        .select('*', count='exact')\
        .eq('profile_id', user_id)\
        .execute()

    time_blocks_user_count = time_blocks_by_user.count if time_blocks_by_user.count else 0
    print(f"⏰ Time Blocks (by user_id): {time_blocks_user_count} blocks found")

    # Get sample data
    if plan_items_count > 0:
        sample_items = supabase.table('plan_items')\
            .select('title, task_type, scheduled_time')\
            .eq('analysis_result_id', analysis_id)\
            .limit(5)\
            .execute()

        print(f"\n📝 Sample Plan Items:")
        for item in sample_items.data:
            print(f"   - {item['title']} ({item['task_type']}) at {item['scheduled_time']}")

    if time_blocks_count > 0:
        sample_blocks = supabase.table('time_blocks')\
            .select('block_title, time_range')\
            .eq('analysis_result_id', analysis_id)\
            .limit(5)\
            .execute()

        print(f"\n⏱️  Sample Time Blocks:")
        for block in sample_blocks.data:
            print(f"   - {block['block_title']}: {block['time_range']}")

    # Validation
    print(f"\n✅ Validation:")
    if plan_items_count > 0 and time_blocks_count > 0:
        print(f"   ✅ Extraction successfully stored data in database")
        print(f"   ✅ {plan_items_count} plan items created")
        print(f"   ✅ {time_blocks_count} time blocks created")
    else:
        print(f"   ❌ Extraction may have failed - no data found")

if __name__ == "__main__":
    verify_extraction()
