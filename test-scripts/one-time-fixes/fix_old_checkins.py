#!/usr/bin/env python3
"""
Fix old check-ins to work with simplified 2-question feedback system.

Workaround Options:
  1. Update old check-ins with default values (preserves data)
  2. Delete only conflicting check-ins (minimal deletion)
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

TEST_USER_ID = "a57f70b4-d0a4-4aef-b721-a4b526f64869"

print("🔧 Simplified Feedback System - Data Migration")
print("=" * 60)
print()

# Check current state
print("📊 Checking current state...")
result = supabase.table('task_checkins').select('*', count='exact').eq('profile_id', TEST_USER_ID).execute()
total = result.count

null_experience = supabase.table('task_checkins').select('*', count='exact').eq('profile_id', TEST_USER_ID).is_('experience_rating', 'null').execute().count

null_continue = supabase.table('task_checkins').select('*', count='exact').eq('profile_id', TEST_USER_ID).is_('continue_preference', 'null').execute().count

print(f"   Total check-ins: {total}")
print(f"   Missing experience_rating: {null_experience}")
print(f"   Missing continue_preference: {null_continue}")
print()

if null_experience == 0 and null_continue == 0:
    print("✅ All check-ins already have the new columns!")
    print("   You can now run: python run_feedback_test.py")
    sys.exit(0)

# Show options
print("Choose a workaround:")
print()
print("  1. UPDATE old check-ins with defaults (RECOMMENDED)")
print("     - Preserves all data")
print("     - Sets experience_rating from satisfaction_rating")
print("     - Sets continue_preference to 'maybe'")
print()
print("  2. DELETE only conflicting check-ins")
print("     - Removes check-ins that block the test")
print("     - Keeps other data intact")
print()
print("  3. DELETE all test user check-ins")
print("     - Fresh start for testing")
print("     - Removes all check-in history")
print()

choice = input("Enter choice (1/2/3): ").strip()

if choice == "1":
    print()
    print("▶️  Updating old check-ins with default values...")

    # Get all check-ins with NULL experience_rating
    old_checkins = supabase.table('task_checkins').select('id, satisfaction_rating').eq('profile_id', TEST_USER_ID).is_('experience_rating', 'null').execute().data

    updated = 0
    for checkin in old_checkins:
        # Set experience_rating from satisfaction_rating or default to 3
        experience_rating = checkin.get('satisfaction_rating') or 3

        supabase.table('task_checkins').update({
            'experience_rating': experience_rating,
            'continue_preference': 'maybe'
        }).eq('id', checkin['id']).execute()

        updated += 1

    print(f"   ✅ Updated {updated} check-ins")

elif choice == "2":
    print()
    print("▶️  Deleting only conflicting check-ins...")

    conflicting_plan_items = [
        'c4f527a1-4dd4-4086-9bee-0318a946d282',
        '6f9ad297-4c57-49ec-b18a-f7742d3c4328',
        'fa034fbd-973f-4b37-8bc8-581205bd3c9d',
        '758a80e5-4112-4df4-9017-bd147dd2849e',
        '279dbc2c-7c0b-4be1-b5fc-13ca3d9a7387',
        '9349f0fa-e1c0-4174-90d5-0fe85704c4ca',
        '1a72b9eb-4ba4-4d9d-b734-ef366b233de5',
        '4a71b960-a317-4766-b7b4-8e8be125495c',
        '84509da2-2e2a-40fb-811d-b55c4dc7d254',
        '84404c60-5a2b-4c29-bbc5-9433319e3b97',
        '372e4673-aef2-45a6-9dfd-19c3bdf1ead1',
        '56b7f2a1-dc9a-48ef-961b-e6c6b82513f1'
    ]

    result = supabase.table('task_checkins').delete().eq('profile_id', TEST_USER_ID).in_('plan_item_id', conflicting_plan_items).eq('planned_date', '2025-10-29').execute()

    print(f"   ✅ Deleted conflicting check-ins")

elif choice == "3":
    print()
    print("⚠️  This will delete ALL check-ins for the test user!")
    confirm = input("Are you sure? (yes/no): ").strip().lower()

    if confirm == "yes":
        result = supabase.table('task_checkins').delete().eq('profile_id', TEST_USER_ID).execute()
        print(f"   ✅ Deleted all check-ins")
    else:
        print("   ❌ Cancelled")
        sys.exit(0)
else:
    print("❌ Invalid choice")
    sys.exit(1)

# Verify final state
print()
print("📊 Final state:")
result = supabase.table('task_checkins').select('*', count='exact').eq('profile_id', TEST_USER_ID).execute()
remaining = result.count

null_experience_after = supabase.table('task_checkins').select('*', count='exact').eq('profile_id', TEST_USER_ID).is_('experience_rating', 'null').execute().count

null_continue_after = supabase.table('task_checkins').select('*', count='exact').eq('profile_id', TEST_USER_ID).is_('continue_preference', 'null').execute().count

print(f"   Total check-ins: {remaining}")
print(f"   Missing experience_rating: {null_experience_after}")
print(f"   Missing continue_preference: {null_continue_after}")
print()

if null_experience_after == 0 and null_continue_after == 0:
    print("✅ All done! Now run: python run_feedback_test.py")
else:
    print("⚠️  Some check-ins still have NULL values")
    print("   You may need to run option 1 to fix them")
