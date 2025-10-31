#!/usr/bin/env python3
"""Check if the generated plans actually have tasks in plan_items table."""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

plan_ids = [
    '2620b2f7-f2f8-4eab-9a0c-cc7888da6497',  # Plan 1
    '74518e4d-beb4-4aed-8684-a0e5a6d7e8fd',  # Plan 2
    '5e06a236-1c6b-4c1f-b71d-c88e49bdcb65',  # Plan 3
]

print("🔍 Checking plan_items for each analysis_id...\n")

for i, plan_id in enumerate(plan_ids, 1):
    print(f"Plan {i}: {plan_id}")

    # Get tasks grouped by category
    result = supabase.table('plan_items').select('category, title').eq('analysis_result_id', plan_id).execute()

    tasks = result.data
    print(f"   Total tasks: {len(tasks)}")

    if tasks:
        # Group by category
        by_category = {}
        for task in tasks:
            cat = task.get('category', 'unknown')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(task['title'])

        print(f"   Categories:")
        for cat, task_list in sorted(by_category.items()):
            print(f"      {cat}: {len(task_list)} tasks")
            for title in task_list[:3]:  # Show first 3
                print(f"         - {title}")
            if len(task_list) > 3:
                print(f"         ... and {len(task_list) - 3} more")
    else:
        print("   ⚠️  NO TASKS FOUND!")

    print()

print("\n" + "="*70)
print("FRICTION ANALYSIS:")
print("="*70)

# Check if Plan 3 has nutrition/stress_management tasks
plan3_tasks = supabase.table('plan_items').select('category, title').eq(
    'analysis_result_id', plan_ids[2]
).execute().data

has_nutrition = any(t['category'] == 'nutrition' for t in plan3_tasks)
has_stress = any(t['category'] == 'stress_management' for t in plan3_tasks)

if has_nutrition:
    print("✅ Plan 3 HAS nutrition tasks")
    nutrition_tasks = [t['title'] for t in plan3_tasks if t['category'] == 'nutrition']
    print(f"   Tasks: {nutrition_tasks}")
else:
    print("❌ Plan 3 MISSING nutrition tasks (should simplify, not exclude!)")

if has_stress:
    print("✅ Plan 3 HAS stress_management tasks")
    stress_tasks = [t['title'] for t in plan3_tasks if t['category'] == 'stress_management']
    print(f"   Tasks: {stress_tasks}")
else:
    print("❌ Plan 3 MISSING stress_management tasks (should simplify, not exclude!)")
