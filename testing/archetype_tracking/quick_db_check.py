#!/usr/bin/env python3
"""
Quick check if archetype_analysis_tracking table exists and what's in it
"""

import asyncio
import os
from supabase import create_client

async def check_table():
    """Check archetype table via direct Supabase client"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Try to query the table
        print("🔍 Checking archetype_analysis_tracking table...")
        result = supabase.table('archetype_analysis_tracking').select('*').limit(5).execute()
        
        print(f"✅ Table exists! Found {len(result.data)} records")
        
        if result.data:
            print("📋 Sample records:")
            for i, record in enumerate(result.data):
                print(f"   {i+1}. {record}")
        else:
            print("📋 Table is empty")
            
        # Try a simple INSERT to test
        print("\n🧪 Testing INSERT...")
        test_result = supabase.table('archetype_analysis_tracking').insert({
            'user_id': 'test_user_insert',
            'archetype': 'Foundation Builder', 
            'last_analysis_at': '2025-08-19T17:30:00Z',
            'analysis_count': 1
        }).execute()
        
        if test_result.data:
            print("✅ INSERT works!")
            print(f"   Inserted: {test_result.data[0]}")
            
            # Clean up test data
            cleanup = supabase.table('archetype_analysis_tracking').delete().eq('user_id', 'test_user_insert').execute()
            print("🗑️  Test data cleaned up")
        else:
            print("❌ INSERT failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_table())