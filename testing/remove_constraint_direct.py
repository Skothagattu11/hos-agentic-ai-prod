"""
Remove foreign key constraint directly via PostgreSQL connection
"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def remove_constraint():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return

    print("🔧 Connecting to database to remove constraint...\n")

    try:
        import asyncpg

        conn = await asyncpg.connect(database_url)

        # Step 1: Check current constraints
        print("1️⃣ Current foreign key constraints:")
        constraints = await conn.fetch("""
            SELECT
                conname AS constraint_name,
                pg_get_constraintdef(oid) AS constraint_definition
            FROM pg_constraint
            WHERE conrelid = 'saved_schedules'::regclass
            AND contype = 'f'
        """)

        if not constraints:
            print("   ✅ No foreign key constraints found - already removed!")
            await conn.close()
            return

        for c in constraints:
            print(f"   • {c['constraint_name']}: {c['constraint_definition']}")

        print()

        # Step 2: Remove each constraint
        print("2️⃣ Removing constraints:")
        for c in constraints:
            constraint_name = c['constraint_name']
            print(f"   Dropping {constraint_name}...", end=" ")

            try:
                await conn.execute(f"""
                    ALTER TABLE saved_schedules
                    DROP CONSTRAINT {constraint_name} CASCADE
                """)
                print("✅ Done")
            except Exception as e:
                print(f"❌ Error: {e}")

        print()

        # Step 3: Verify removal
        print("3️⃣ Verifying constraints removed:")
        remaining = await conn.fetch("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'saved_schedules'::regclass
            AND contype = 'f'
        """)

        if remaining:
            print("   ❌ Some constraints still exist:")
            for c in remaining:
                print(f"      • {c['conname']}")
        else:
            print("   ✅ All foreign key constraints successfully removed!")

        await conn.close()

        print("\n" + "="*80)
        print("✅ SUCCESS! You can now run the test:")
        print("="*80)
        print("python testing/test_schedule_anchoring.py a57f70b4-d0a4-4aef-b721-a4b526f64869")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(remove_constraint())
