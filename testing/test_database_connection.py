#!/usr/bin/env python3
"""
Test Database Connection Script
Try different Supavisor connection string formats to find the working one
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection(connection_string, description):
    """Test a specific connection string"""
    print(f"\n🔍 Testing: {description}")
    print(f"   Connection: {connection_string[:50]}...")
    
    try:
        # Try to connect
        conn = await asyncpg.connect(connection_string, timeout=10)
        
        # Test with a simple query
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        print(f"✅ SUCCESS: {description}")
        return True
        
    except asyncpg.PostgresError as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

async def main():
    """Test various connection string formats"""
    project_id = "ijcckqnqruwvqqbkiubb"
    password = "urzv9pXEu6pqxBqo"
    
    # Test different regions and formats
    test_configs = [
        # Supavisor Session Mode - different regions
        (f"postgresql://postgres.{project_id}:{password}@aws-0-us-east-1.pooler.supabase.com:5432/postgres", "Supavisor Session (us-east-1)"),
        (f"postgresql://postgres.{project_id}:{password}@aws-0-us-west-1.pooler.supabase.com:5432/postgres", "Supavisor Session (us-west-1)"),
        (f"postgresql://postgres.{project_id}:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres", "Supavisor Session (eu-west-1)"),
        (f"postgresql://postgres.{project_id}:{password}@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres", "Supavisor Session (ap-southeast-1)"),
        
        # Supavisor Transaction Mode
        (f"postgresql://postgres.{project_id}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres", "Supavisor Transaction (us-east-1)"),
        (f"postgresql://postgres.{project_id}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres", "Supavisor Transaction (us-west-1)"),
        
        # Alternative username format
        (f"postgresql://postgres:{password}@aws-0-us-east-1.pooler.supabase.com:5432/postgres", "Alternative username (us-east-1)"),
    ]
    
    print("🔍 Testing Supabase database connections...")
    print("=" * 60)
    
    working_connections = []
    
    for connection_string, description in test_configs:
        success = await test_connection(connection_string, description)
        if success:
            working_connections.append((connection_string, description))
    
    print("\n" + "=" * 60)
    if working_connections:
        print("✅ WORKING CONNECTIONS:")
        for conn_str, desc in working_connections:
            print(f"   {desc}")
            print(f"   {conn_str}")
    else:
        print("❌ No working connections found")
        print("\n💡 Try checking:")
        print("   1. Supabase project settings for connection pooling")
        print("   2. Database password in Supabase dashboard")
        print("   3. Project region in Supabase dashboard")

if __name__ == "__main__":
    asyncio.run(main())