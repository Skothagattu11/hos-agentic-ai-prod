"""
Check the schema of holistic_analysis_results table
"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_schema():
    database_url = os.getenv("DATABASE_URL")

    try:
        import asyncpg
        conn = await asyncpg.connect(database_url)

        # Get column info
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'holistic_analysis_results'
            ORDER BY ordinal_position
        """)

        print("📊 holistic_analysis_results table schema:\n")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   • {col['column_name']}: {col['data_type']} {nullable}{default}")

        # Get primary key
        pk = await conn.fetch("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = 'holistic_analysis_results'::regclass
            AND i.indisprimary
        """)

        if pk:
            print(f"\n🔑 Primary key: {', '.join([p['attname'] for p in pk])}")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
