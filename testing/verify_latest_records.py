#!/usr/bin/env python3
"""
Verify the latest routine_plan records are properly stored without MemoryQuality errors
"""
import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

print(f"\n📋 Checking latest routine_plan records for user {TEST_USER_ID[:8]}...\n")

# Get the 5 most recent routine_plan records
result = supabase.table('holistic_analysis_results')\
    .select('id, created_at, analysis_result, archetype')\
    .eq('user_id', TEST_USER_ID)\
    .eq('analysis_type', 'routine_plan')\
    .order('created_at', desc=True)\
    .limit(5)\
    .execute()

if result.data:
    print(f"✅ Found {len(result.data)} recent routine_plan records:\n")

    for i, record in enumerate(result.data, 1):
        print(f"{i}. ID: {record['id']}")
        print(f"   Created: {record['created_at']}")
        print(f"   Archetype: {record['archetype']}")

        # Parse and check analysis_result
        try:
            analysis_result = record['analysis_result']

            # Check if it's a string that needs parsing
            if isinstance(analysis_result, str):
                parsed = json.loads(analysis_result)
            else:
                parsed = analysis_result

            # Check for errors
            if 'error' in parsed:
                print(f"   ❌ ERROR: {parsed['error']}")
            else:
                # Check if it has the expected structure
                if 'markdown_plan' in parsed or 'routine_plan' in parsed:
                    print(f"   ✅ Valid routine plan data")

                    # Check for MemoryQuality in metadata
                    if 'metadata' in parsed and 'memory_quality' in parsed['metadata']:
                        mq = parsed['metadata']['memory_quality']
                        if isinstance(mq, str):
                            print(f"   ✅ Memory quality properly converted: '{mq}'")
                        else:
                            print(f"   ❌ Memory quality is NOT a string: {type(mq)}")
                else:
                    print(f"   ⚠️  Unknown structure")

        except Exception as e:
            print(f"   ❌ Parse error: {e}")

        print()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)

    errors = 0
    valid = 0

    for record in result.data:
        try:
            analysis_result = record['analysis_result']
            if isinstance(analysis_result, str):
                parsed = json.loads(analysis_result)
            else:
                parsed = analysis_result

            if 'error' in parsed:
                errors += 1
            else:
                valid += 1
        except:
            errors += 1

    print(f"✅ Valid records: {valid}")
    print(f"❌ Error records: {errors}")

    if errors == 0:
        print(f"\n🎉 All recent records are clean! MemoryQuality fix is working.")
    else:
        print(f"\n⚠️  {errors} record(s) have errors (likely old records before fix)")

else:
    print(f"❌ No routine_plan records found")
