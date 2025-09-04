#!/usr/bin/env python3
"""
Test the corrected JOIN syntax directly with Supabase
"""
import os
import sys

# Load environment variables manually
def load_env_manual():
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        print("❌ .env file not found")
        return None
    return env_vars

env_vars = load_env_manual()
if not env_vars:
    print("❌ Could not load environment variables")
    sys.exit(1)

try:
    from supabase import create_client, Client
    
    # Get Supabase credentials
    supabase_url = env_vars.get('SUPABASE_URL')
    supabase_key = env_vars.get('SUPABASE_SERVICE_KEY') or env_vars.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env")
        print(f"   SUPABASE_URL: {'✅' if supabase_url else '❌'}")
        print(f"   SUPABASE_KEY: {'✅' if supabase_key else '❌'}")
        sys.exit(1)
        
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase client initialized")
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   This test requires the supabase library")
    print("\n🔍 ANALYSIS: Based on your simple_api_test.py results:")
    print("   - Database direct query: ✅ 100% success with time_blocks")
    print("   - API endpoint query: ❌ Returns time_blocks: None")
    print("\n💡 CONCLUSION: API server is using OLD JOIN syntax")
    print("   The server needs the CORRECTED JOIN syntax:")
    print("   time_blocks!fk_plan_items_time_block_id (...)")
    print("   Instead of: time_blocks:time_block_id (...)")
    sys.exit(1)
except Exception as e:
    print(f"❌ Setup error: {e}")
    sys.exit(1)

def test_corrected_join():
    """Test the CORRECTED JOIN syntax that should be in the API"""
    print("\n🧪 Testing CORRECTED JOIN Syntax")
    print("=" * 50)
    
    profile_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
    
    try:
        # This is the CORRECTED JOIN syntax from our updated calendar_endpoints.py
        result = supabase.table("plan_items")\
            .select("""
                id, title, time_block_id, scheduled_time,
                time_blocks!fk_plan_items_time_block_id (
                    id,
                    block_title,
                    time_range,
                    purpose
                )
            """)\
            .eq("profile_id", profile_id)\
            .order("scheduled_time")\
            .limit(5)\
            .execute()
        
        if result.data:
            print(f"✅ CORRECTED JOIN query successful: {len(result.data)} items")
            
            items_with_blocks = [item for item in result.data if item.get('time_blocks')]
            items_without_blocks = [item for item in result.data if not item.get('time_blocks')]
            
            print(f"   - Items with time_blocks: {len(items_with_blocks)}")
            print(f"   - Items without time_blocks: {len(items_without_blocks)}")
            
            for i, item in enumerate(result.data):
                has_time_blocks = item.get('time_blocks') is not None
                if has_time_blocks:
                    block_title = item['time_blocks']['block_title']
                    print(f"  ✅ {i+1}. '{item['title']}' -> '{block_title}'")
                else:
                    print(f"  ❌ {i+1}. '{item['title']}' -> No time_blocks (time_block_id: {item.get('time_block_id')})")
            
            if len(items_with_blocks) > 0:
                print("\n🎉 SUCCESS: CORRECTED JOIN syntax works!")
                print("   This is what the API should return when using updated code.")
                return True
            else:
                print("\n❌ ISSUE: Even corrected syntax returning no time_blocks")
                return False
        else:
            print("❌ No data returned from query")
            return False
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def test_old_join():
    """Test the OLD JOIN syntax that's likely in the current API server"""
    print("\n🔍 Testing OLD JOIN Syntax (What Current API Might Be Using)")
    print("=" * 60)
    
    profile_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
    
    try:
        # This is the OLD JOIN syntax that FAILS with foreign key constraints
        result = supabase.table("plan_items")\
            .select("""
                id, title, time_block_id, scheduled_time,
                time_blocks:time_block_id (
                    id,
                    block_title,
                    time_range
                )
            """)\
            .eq("profile_id", profile_id)\
            .order("scheduled_time")\
            .limit(5)\
            .execute()
        
        if result.data:
            items_with_blocks = [item for item in result.data if item.get('time_blocks')]
            print(f"⚠️  OLD JOIN returned {len(result.data)} items")
            print(f"   - Items with time_blocks: {len(items_with_blocks)}")
            
            if len(items_with_blocks) == 0:
                print("   ❌ OLD syntax returns time_blocks: None (as expected)")
                return False
            else:
                print("   ⚠️  OLD syntax worked unexpectedly")
                return True
        else:
            print("❌ OLD syntax returned no data")
            return False
            
    except Exception as e:
        print(f"❌ OLD JOIN syntax failed (expected): {e}")
        return False

def main():
    print("🚀 JOIN Syntax Comparison Test")
    print("=" * 50)
    
    # Test the corrected syntax
    corrected_works = test_corrected_join()
    
    # Test the old syntax
    old_works = test_old_join()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   - CORRECTED JOIN (fk_plan_items_time_block_id): {'✅ WORKS' if corrected_works else '❌ FAILED'}")
    print(f"   - OLD JOIN (time_block_id): {'⚠️  WORKS' if old_works else '❌ FAILED (expected)'}")
    
    if corrected_works and not old_works:
        print("\n🎉 PERFECT: Corrected syntax works, old syntax fails")
        print("   The API server needs to use the corrected syntax")
    elif corrected_works:
        print("\n✅ GOOD: Corrected syntax works")
        print("   API server should use fk_plan_items_time_block_id constraint")
    else:
        print("\n❌ ISSUE: Neither syntax working - check database setup")
    
    return corrected_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)