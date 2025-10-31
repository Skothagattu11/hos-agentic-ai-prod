#!/usr/bin/env python3
"""Check the raw AI output to see if categories are in the original plan."""

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

print(f"🔍 Checking raw AI output for Plan 3: {plan_id}\n")

# Get the analysis result
result = supabase.table('holistic_analysis_results').select('*').eq('id', plan_id).execute()

if result.data:
    plan = result.data[0]

    print(f"Analysis Type: {plan.get('analysis_type')}")
    print(f"Status: {plan.get('status')}")
    print(f"Created: {plan.get('created_at')}")
    print()

    # Check the raw result JSON
    raw_result = plan.get('result', {})

    if isinstance(raw_result, str):
        raw_result = json.loads(raw_result)

    print("="*70)
    print("RAW AI OUTPUT (routine_plan):")
    print("="*70)

    routine_plan = raw_result.get('routine_plan', {})

    if isinstance(routine_plan, str):
        print(routine_plan[:1000])  # First 1000 chars
        print("\n... (truncated)")
    else:
        print(json.dumps(routine_plan, indent=2)[:2000])
        print("\n... (truncated)")

    print()
    print("="*70)
    print("EXTRACTION CHECK:")
    print("="*70)

    # Check if routine_plan has tasks with categories
    if isinstance(routine_plan, dict):
        tasks = routine_plan.get('tasks', [])
        print(f"Found {len(tasks)} tasks in routine_plan.tasks")

        if tasks:
            print("\nFirst 3 tasks:")
            for task in tasks[:3]:
                print(f"  - {task.get('title', 'NO TITLE')}")
                print(f"    Category: {task.get('category', 'NO CATEGORY')}")
                print(f"    Time: {task.get('time', 'NO TIME')}")
                print()

    # Check plan_items table
    print("\n" + "="*70)
    print("PLAN_ITEMS TABLE:")
    print("="*70)

    items = supabase.table('plan_items').select('*').eq('analysis_result_id', plan_id).limit(3).execute().data

    print(f"Found {len(items)} items in plan_items table")

    for item in items:
        print(f"\n  - {item.get('title')}")
        print(f"    Category: {item.get('category')}")
        print(f"    Scheduled: {item.get('scheduled_time')}")

else:
    print("❌ Plan not found!")
