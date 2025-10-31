#!/usr/bin/env python3
"""Check the FULL result structure to find where the AI output is stored."""

import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

plan_id = '5e06a236-1c6b-4c1f-b71d-c88e49bdcb65'  # Plan 3

# Get the full record
result = supabase.table('holistic_analysis_results').select('*').eq('id', plan_id).execute()

if result.data:
    plan = result.data[0]

    print("🔍 FULL RECORD STRUCTURE:")
    print("="*70)

    for key, value in plan.items():
        if key in ['id', 'analysis_type', 'created_at', 'profile_id']:
            print(f"{key}: {value}")
        elif key == 'result':
            print(f"\nresult (JSON):")
            if isinstance(value, dict):
                print(f"  Keys: {list(value.keys())}")
                for k in value.keys():
                    v = value[k]
                    if isinstance(v, (dict, list)):
                        print(f"    {k}: {type(v).__name__} with {len(v)} items")
                    else:
                        print(f"    {k}: {str(v)[:100]}")
            else:
                print(f"  Type: {type(value)}")
                print(f"  Preview: {str(value)[:200]}")
        else:
            if value and len(str(value)) > 100:
                print(f"{key}: {type(value).__name__} ({len(str(value))} chars)")
            else:
                print(f"{key}: {value}")

    print("\n" + "="*70)
    print("DETAILED result FIELD:")
    print("="*70)

    result_data = plan.get('result')
    if result_data:
        if isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except:
                pass

        print(json.dumps(result_data, indent=2))
