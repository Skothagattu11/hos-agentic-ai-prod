"""
Verify database constraints on saved_schedules table
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def check_constraints():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }

    print("🔍 Checking saved_schedules table constraints...")
    print(f"   Database: {supabase_url}\n")

    # Test: Try to insert a test record with a non-existent user_id
    test_schedule = {
        "id": "00000000-0000-0000-0000-000000000001",
        "user_id": "test-user-that-doesnt-exist-123",
        "name": "Constraint Test Schedule",
        "selected_days": "[1,2,3,4,5]"
    }

    async with httpx.AsyncClient() as client:
        print("📝 Attempting to insert test record with fake user_id...")
        response = await client.post(
            f"{supabase_url}/rest/v1/saved_schedules",
            headers=headers,
            json=test_schedule
        )

        if response.status_code in [200, 201]:
            print("✅ SUCCESS! Foreign key constraint is removed.")
            print("   Test record was inserted successfully.")

            # Clean up test record
            print("\n🧹 Cleaning up test record...")
            delete_response = await client.delete(
                f"{supabase_url}/rest/v1/saved_schedules?id=eq.{test_schedule['id']}",
                headers=headers
            )
            print("   Test record deleted.")

            print("\n✅ Database is ready for testing!")
            print("\nYou can now run:")
            print("   python testing/test_schedule_anchoring.py a57f70b4-d0a4-4aef-b721-a4b526f64869")

        else:
            print("❌ FAILED! Foreign key constraint still exists.")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            print("\n🔧 You need to run this SQL in Supabase SQL Editor:")
            print("   ALTER TABLE saved_schedules DROP CONSTRAINT IF EXISTS fk_saved_schedules_user CASCADE;")
            print("\n   Or check if there's another constraint with a different name:")
            print("   SELECT conname FROM pg_constraint WHERE conrelid = 'saved_schedules'::regclass AND contype = 'f';")

if __name__ == "__main__":
    asyncio.run(check_constraints())
