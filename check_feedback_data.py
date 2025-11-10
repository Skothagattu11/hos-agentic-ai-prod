#!/usr/bin/env python3
"""
Check if user has check-in feedback data for task library selection
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

USER_ID = "a57f70b4-d0a4-4aef-b721-a4b526f64869"

print("\n" + "="*80)
print("  CHECKING FEEDBACK DATA FOR TASK LIBRARY SELECTION")
print("="*80)
print()

# Check task_checkins
checkins = supabase.table('task_checkins').select('*').eq('profile_id', USER_ID).execute()
print(f"📊 Task Check-ins: {len(checkins.data)} records")

if checkins.data:
    print(f"   Latest check-in: {checkins.data[0].get('created_at', 'N/A')}")
    print(f"   Sample data:")
    for checkin in checkins.data[:3]:
        print(f"     • {checkin.get('task_title', 'N/A')} - enjoyed: {checkin.get('enjoyed', 'N/A')}, continue: {checkin.get('continue_preference', 'N/A')}")
else:
    print("   ⚠️  NO CHECK-IN DATA FOUND")
    print("   → System will use pure AI (cold start)")
    print()
    print("   To enable library task selection, you need:")
    print("   1. User completes tasks from a plan")
    print("   2. User checks in with feedback (enjoyed, continue_preference)")
    print("   3. After ~7-10 check-ins, system starts using library tasks")

print()
print("="*80)
