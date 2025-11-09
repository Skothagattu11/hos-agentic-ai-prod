"""
Direct check of database constraints using PostgreSQL connection
"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_constraints_direct():
    # Get database URL
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return

    print("🔍 Connecting to database to check constraints...\n")

    try:
        import asyncpg

        conn = await asyncpg.connect(database_url)

        # Query 1: Check foreign key constraints on saved_schedules
        print("1️⃣ Checking foreign key constraints on saved_schedules:")
        constraints = await conn.fetch("""
            SELECT
                conname AS constraint_name,
                contype AS constraint_type,
                pg_get_constraintdef(oid) AS constraint_definition
            FROM pg_constraint
            WHERE conrelid = 'saved_schedules'::regclass
            AND contype = 'f'
        """)

        if constraints:
            print("   ❌ Foreign key constraints found:")
            for c in constraints:
                print(f"      • {c['constraint_name']}: {c['constraint_definition']}")
            print("\n   🔧 To remove, run this SQL:")
            for c in constraints:
                print(f"      ALTER TABLE saved_schedules DROP CONSTRAINT {c['constraint_name']} CASCADE;")
        else:
            print("   ✅ No foreign key constraints found")

        print()

        # Query 2: Check column types
        print("2️⃣ Checking column types:")
        columns = await conn.fetch("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'saved_schedules'
            AND column_name IN ('id', 'user_id')
        """)

        for col in columns:
            print(f"   • {col['column_name']}: {col['data_type']} ({col['udt_name']})")

        print()

        # Query 3: Check if user_id from sample exists
        print("3️⃣ Checking if sample user_id exists in database:")
        sample_user_id = "a57f70b4-d0a4-4aef-b721-a4b526f64869"

        # Check saved_schedules
        existing_schedules = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM saved_schedules
            WHERE user_id = $1
        """, sample_user_id)

        print(f"   • saved_schedules entries for {sample_user_id}: {existing_schedules[0]['count']}")

        # Check if auth.users table exists and has this user
        try:
            auth_user = await conn.fetch("""
                SELECT id FROM auth.users WHERE id = $1
            """, sample_user_id)

            if auth_user:
                print(f"   ✅ User exists in auth.users table")
            else:
                print(f"   ❌ User NOT found in auth.users table")
                print(f"      This is why the foreign key constraint fails!")
        except Exception as e:
            print(f"   ⚠️  Could not check auth.users table: {e}")

        await conn.close()

        print("\n" + "="*80)
        print("DIAGNOSIS:")
        print("="*80)
        if constraints:
            print("The foreign key constraint EXISTS and is blocking inserts.")
            print("You need to remove it using the SQL commands shown above.")
        else:
            print("No foreign key constraints found. The issue might be elsewhere.")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have asyncpg installed: pip install asyncpg")

if __name__ == "__main__":
    asyncio.run(check_constraints_direct())
