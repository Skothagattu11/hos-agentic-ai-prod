#!/usr/bin/env python3
"""
Quick database schema check for archetype_analysis_tracking table
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared_libs.supabase_client.adapter import SupabaseAsyncPGAdapter

async def check_archetype_tracking_table():
    """Check if archetype_analysis_tracking table exists and is properly configured"""
    
    print("🔍 Checking archetype_analysis_tracking table schema...")
    print("=" * 60)
    
    adapter = SupabaseAsyncPGAdapter()
    
    try:
        # No initialization needed for SupabaseAsyncPGAdapter
        
        # Check if table exists
        print("\n1. Checking if table exists...")
        table_check = await adapter.execute_query("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'archetype_analysis_tracking'
            );
        """)
        
        table_exists = table_check[0]['exists'] if table_check else False
        
        if table_exists:
            print("✅ archetype_analysis_tracking table EXISTS")
            
            # Check table structure
            print("\n2. Checking table structure...")
            structure = await adapter.execute_query("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'archetype_analysis_tracking'
                ORDER BY ordinal_position;
            """)
            
            print("   Columns:")
            for col in structure:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   • {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            # Check constraints
            print("\n3. Checking constraints...")
            constraints = await adapter.execute_query("""
                SELECT conname, contype, pg_get_constraintdef(c.oid) as definition
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                WHERE t.relname = 'archetype_analysis_tracking';
            """)
            
            print("   Constraints:")
            for constraint in constraints:
                constraint_type = {
                    'p': 'PRIMARY KEY',
                    'u': 'UNIQUE',
                    'c': 'CHECK',
                    'f': 'FOREIGN KEY'
                }.get(constraint['contype'], constraint['contype'])
                print(f"   • {constraint['conname']} ({constraint_type}): {constraint['definition']}")
            
            # Check indexes
            print("\n4. Checking indexes...")
            indexes = await adapter.execute_query("""
                SELECT indexname, indexdef
                FROM pg_indexes 
                WHERE tablename = 'archetype_analysis_tracking';
            """)
            
            print("   Indexes:")
            for idx in indexes:
                print(f"   • {idx['indexname']}: {idx['indexdef']}")
            
            # Check if RLS is enabled
            print("\n5. Checking Row Level Security...")
            rls_check = await adapter.execute_query("""
                SELECT relname, relrowsecurity, relforcerowsecurity
                FROM pg_class 
                WHERE relname = 'archetype_analysis_tracking';
            """)
            
            if rls_check:
                rls_enabled = rls_check[0]['relrowsecurity']
                print(f"   RLS Enabled: {'✅ YES' if rls_enabled else '❌ NO'}")
                
                # Check RLS policies
                policies = await adapter.execute_query("""
                    SELECT policyname, permissive, roles, cmd, qual, with_check
                    FROM pg_policies 
                    WHERE tablename = 'archetype_analysis_tracking';
                """)
                
                print("   RLS Policies:")
                for policy in policies:
                    print(f"   • {policy['policyname']} for {policy['roles']} - {policy['cmd']}")
            
            # Check sample data count
            print("\n6. Checking data count...")
            count_result = await adapter.execute_query("""
                SELECT COUNT(*) as total_records,
                       COUNT(DISTINCT user_id) as unique_users,
                       COUNT(DISTINCT archetype) as unique_archetypes
                FROM archetype_analysis_tracking;
            """)
            
            if count_result:
                stats = count_result[0]
                print(f"   Total Records: {stats['total_records']}")
                print(f"   Unique Users: {stats['unique_users']}")
                print(f"   Unique Archetypes: {stats['unique_archetypes']}")
            
            # Check test user specifically
            print(f"\n7. Checking test user (35pDPUIfAoRl2Y700bFkxPKYjjf2)...")
            test_user_data = await adapter.execute_query("""
                SELECT user_id, archetype, last_analysis_at, analysis_count, created_at
                FROM archetype_analysis_tracking
                WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
                ORDER BY last_analysis_at DESC;
            """)
            
            if test_user_data:
                print("   Test User Records:")
                for record in test_user_data:
                    print(f"   • {record['archetype']}: last={record['last_analysis_at']}, count={record['analysis_count']}")
            else:
                print("   ❌ No records found for test user")
            
        else:
            print("❌ archetype_analysis_tracking table DOES NOT EXIST")
            print("\n🚨 MIGRATION REQUIRED:")
            print("   Run: psql $DATABASE_URL < supabase/migrations/create_archetype_analysis_tracking.sql")
        
        print("\n" + "=" * 60)
        if table_exists:
            print("✅ DATABASE SCHEMA CHECK COMPLETE")
            print("   The archetype_analysis_tracking table is properly configured.")
        else:
            print("❌ DATABASE MIGRATION NEEDED")
            print("   Apply the database migration before running tests.")
        
        return table_exists
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # No cleanup needed for SupabaseAsyncPGAdapter
        pass

if __name__ == "__main__":
    asyncio.run(check_archetype_tracking_table())