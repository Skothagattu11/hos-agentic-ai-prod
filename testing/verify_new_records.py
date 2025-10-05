#!/usr/bin/env python3
"""
Verify that markdown regeneration creates NEW records (not updates existing)
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

print(f"\n📋 Checking routine_plan records for user {TEST_USER_ID[:8]}...\n")

# Get all routine_plan records for this user, ordered by creation date
result = supabase.table('holistic_analysis_results')\
    .select('id, created_at, archetype')\
    .eq('user_id', TEST_USER_ID)\
    .eq('analysis_type', 'routine_plan')\
    .order('created_at', desc=False)\
    .execute()

if result.data:
    print(f"✅ Found {len(result.data)} routine_plan records:\n")
    for i, record in enumerate(result.data, 1):
        print(f"   {i}. ID: {record['id']}")
        print(f"      Created: {record['created_at']}")
        print(f"      Archetype: {record['archetype']}\n")

    if len(result.data) >= 2:
        print(f"✅ SUCCESS: Multiple routine plans exist - markdown regeneration creates new records!")
    else:
        print(f"⚠️  WARNING: Only 1 record found - run markdown regeneration test again to verify")
else:
    print(f"❌ No routine_plan records found")
