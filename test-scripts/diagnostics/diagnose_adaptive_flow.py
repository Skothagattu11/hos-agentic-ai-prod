#!/usr/bin/env python3
"""
Comprehensive diagnostic of the adaptive feedback flow.
Traces data from AI generation through feedback to next plan adaptation.
"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# The 3 test plans
PLAN_IDS = [
    'c4a4a963-8f5e-4579-8f97-cb6ffd0eaf3c',  # Plan 1 (cold start)
    '2fb2a4e6-0ae2-4bc3-9e82-526d2925929e',  # Plan 2 (positive feedback)
    '45d35e78-363b-4a41-9ed2-b9a0b12bbfcb',  # Plan 3 (friction-reduction)
]

USER_ID = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'

print("="*80)
print("ADAPTIVE FEEDBACK FLOW DIAGNOSTIC")
print("="*80)
print()

for i, plan_id in enumerate(PLAN_IDS, 1):
    print(f"\n{'='*80}")
    print(f"PLAN {i}: {plan_id}")
    print(f"{'='*80}\n")

    # 1. Check raw AI output
    print(f"[1] RAW AI OUTPUT:")
    print("-" * 80)

    result = supabase.table('holistic_analysis_results').select(
        'analysis_result, created_at'
    ).eq('id', plan_id).execute()

    if result.data:
        analysis_result = result.data[0]['analysis_result']
        created_at = result.data[0]['created_at']

        print(f"Generated: {created_at}")

        if isinstance(analysis_result, dict):
            content = analysis_result.get('content', '')
            if isinstance(content, str):
                # Parse JSON from content
                try:
                    parsed = json.loads(content)
                    time_blocks = parsed.get('time_blocks', [])

                    # Count tasks by category from AI output
                    ai_categories = defaultdict(int)
                    sample_tasks = []

                    for block in time_blocks:
                        for task in block.get('tasks', []):
                            cat = task.get('category', 'NO_CATEGORY')
                            ai_categories[cat] += 1
                            if len(sample_tasks) < 3:
                                sample_tasks.append({
                                    'title': task.get('title'),
                                    'category': cat,
                                    'block': block.get('block_name')
                                })

                    print(f"\n✅ AI Generated Categories:")
                    for cat, count in sorted(ai_categories.items()):
                        print(f"   {cat}: {count} tasks")

                    print(f"\n   Sample tasks from AI:")
                    for task in sample_tasks:
                        print(f"   - [{task['category']}] {task['title']}")

                except:
                    print("   ⚠️  Could not parse AI output as JSON")

    # 2. Check extracted plan_items
    print(f"\n[2] EXTRACTED PLAN_ITEMS:")
    print("-" * 80)

    items = supabase.table('plan_items').select(
        'title, category, scheduled_time'
    ).eq('analysis_result_id', plan_id).execute()

    if items.data:
        extracted_categories = defaultdict(int)
        for item in items.data:
            cat = item.get('category') or 'NULL'
            extracted_categories[cat] += 1

        print(f"✅ Total plan_items: {len(items.data)}")
        print(f"\n   Categories in plan_items table:")
        for cat, count in sorted(extracted_categories.items()):
            print(f"   {cat}: {count} tasks")

        print(f"\n   Sample tasks from plan_items:")
        for item in items.data[:3]:
            print(f"   - [{item.get('category') or 'NULL'}] {item['title']} @ {item.get('scheduled_time')}")

        # Check if categories match AI output
        if extracted_categories.get('NULL', 0) > 0:
            print(f"\n   ⚠️  WARNING: {extracted_categories['NULL']} tasks have NULL category!")
            print(f"   ⚠️  Extraction may not be working correctly")
    else:
        print("   ❌ NO plan_items found!")

    # 3. Check check-ins (only for Plans 1 and 2, since Plan 3 is final)
    if i < 3:
        print(f"\n[3] CHECK-INS (Feedback for next plan):")
        print("-" * 80)

        checkins = supabase.table('task_checkins').select(
            'plan_item_id, continue_preference, experience_rating, planned_date'
        ).in_('plan_item_id', [item['id'] for item in supabase.table('plan_items').select('id').eq('analysis_result_id', plan_id).execute().data]).execute()

        if checkins.data:
            print(f"✅ Total check-ins: {len(checkins.data)}")

            # Count by preference
            continue_counts = defaultdict(int)
            rating_sum = 0
            rating_count = 0

            for checkin in checkins.data:
                pref = checkin.get('continue_preference') or 'NULL'
                continue_counts[pref] += 1

                rating = checkin.get('experience_rating')
                if rating:
                    rating_sum += rating
                    rating_count += 1

            print(f"\n   Continue preferences:")
            for pref, count in sorted(continue_counts.items()):
                print(f"   {pref}: {count}")

            if rating_count > 0:
                avg_rating = rating_sum / rating_count
                print(f"\n   Average experience rating: {avg_rating:.1f}/5")
        else:
            print("   ⚠️  No check-ins found for this plan")

print("\n" + "="*80)
print("FEEDBACK ANALYSIS SUMMARY")
print("="*80)

# Analyze feedback between plans
print("\n[FRICTION ANALYSIS]")
print("-" * 80)

# Get all check-ins for the user
all_checkins = supabase.table('task_checkins').select(
    'continue_preference, experience_rating, planned_date, plan_item_id'
).eq('profile_id', USER_ID).execute()

if all_checkins.data:
    # Join with plan_items to get categories
    all_items = supabase.table('plan_items').select(
        'id, category, analysis_result_id'
    ).eq('profile_id', USER_ID).execute()

    item_map = {item['id']: item for item in all_items.data}

    # Group by category
    category_feedback = defaultdict(lambda: {
        'yes': 0, 'maybe': 0, 'no': 0,
        'rating_sum': 0, 'rating_count': 0
    })

    for checkin in all_checkins.data:
        item_id = checkin['plan_item_id']
        if item_id in item_map:
            cat = item_map[item_id].get('category') or 'NULL'

            pref = checkin.get('continue_preference')
            if pref == 'yes':
                category_feedback[cat]['yes'] += 1
            elif pref == 'no':
                category_feedback[cat]['no'] += 1
            else:
                category_feedback[cat]['maybe'] += 1

            rating = checkin.get('experience_rating')
            if rating:
                category_feedback[cat]['rating_sum'] += rating
                category_feedback[cat]['rating_count'] += 1

    print("\nCategory Friction Levels:")
    print()

    for cat in sorted(category_feedback.keys()):
        feedback = category_feedback[cat]
        total = feedback['yes'] + feedback['maybe'] + feedback['no']

        if total > 0:
            yes_rate = feedback['yes'] / total
            no_rate = feedback['no'] / total

            avg_rating = 0
            if feedback['rating_count'] > 0:
                avg_rating = feedback['rating_sum'] / feedback['rating_count']

            # Calculate friction (higher = more friction)
            # Based on: low rating + high rejection = high friction
            experience_friction = (5 - avg_rating) / 4.0
            continuation_friction = (no_rate * 0.8) + ((total - feedback['yes']) / total * 0.4)
            friction_score = (experience_friction * 0.6) + (continuation_friction * 0.4)

            sentiment = "✅ LOW " if friction_score <= 0.3 else "😐 MED" if friction_score <= 0.6 else "❌ HIGH"

            print(f"{sentiment} {cat:20} - {total:2} tasks (yes:{feedback['yes']:2}, maybe:{feedback['maybe']:2}, no:{feedback['no']:2}, rating:{avg_rating:.1f}/5, friction:{friction_score:.2f})")

print("\n" + "="*80)
print("EXPECTED vs ACTUAL BEHAVIOR")
print("="*80)

# Check if Plan 3 has nutrition tasks (should be SIMPLIFIED, not EXCLUDED)
plan3_items = supabase.table('plan_items').select('category, title').eq('analysis_result_id', PLAN_IDS[2]).execute()

plan3_categories = set(item.get('category') for item in plan3_items.data if item.get('category'))

print(f"\nPlan 3 Categories Present: {sorted(plan3_categories)}")

if 'nutrition' in plan3_categories:
    nutrition_tasks = [item['title'] for item in plan3_items.data if item.get('category') == 'nutrition']
    print(f"\n✅ CORRECT: Plan 3 HAS nutrition tasks ({len(nutrition_tasks)})")
    print(f"   Sample nutrition tasks:")
    for task in nutrition_tasks[:3]:
        print(f"   - {task}")
else:
    print(f"\n❌ ERROR: Plan 3 MISSING nutrition tasks (should simplify, not exclude!)")

if 'stress_management' in plan3_categories:
    stress_tasks = [item['title'] for item in plan3_items.data if item.get('category') == 'stress_management']
    print(f"\n✅ CORRECT: Plan 3 HAS stress_management tasks ({len(stress_tasks)})")
    print(f"   Sample stress tasks:")
    for task in stress_tasks[:3]:
        print(f"   - {task}")
else:
    print(f"\n❌ ERROR: Plan 3 MISSING stress_management tasks (should simplify, not exclude!)")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
