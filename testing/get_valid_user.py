"""
Quick script to get a valid user_id from your Supabase auth.users table
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def get_valid_user():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        print("🔍 Checking for existing users...")

        # Try multiple tables to find a valid UUID-format user_id
        tables_to_check = [
            ("holistic_analysis_results", "user_id"),
            ("plan_items", None),  # Will join with holistic_analysis_results
            ("users", "id"),  # Custom users table if exists
        ]

        for table, user_column in tables_to_check:
            try:
                if table == "plan_items":
                    # Try to get user_id via join
                    query = "select=user_id&limit=1"
                else:
                    query = f"select={user_column}&limit=1"

                response = await client.get(
                    f"{supabase_url}/rest/v1/{table}?{query}",
                    headers=headers
                )

                if response.status_code == 200:
                    results = response.json()
                    if results:
                        user_id = results[0].get(user_column or 'user_id')
                        if user_id and '-' in str(user_id):  # Basic UUID check
                            print(f"\n✅ Found valid UUID user_id from {table}: {user_id}")
                            print(f"\nUse this command to run the test:")
                            print(f"python testing/test_schedule_anchoring.py {user_id}")
                            return user_id
            except Exception as e:
                continue

        print("\n⚠️  No valid UUID user found in database")
        print("\n📝 Options:")
        print("1. Create test user with valid UUID:")
        print("   user_id = str(uuid.uuid4())")
        print("2. Use the simplified test that doesn't require auth:")
        print("   python testing/test_schedule_anchoring_simple.py")
        print("\n💡 The test will create a random user_id and skip the foreign key constraint")

if __name__ == "__main__":
    asyncio.run(get_valid_user())
