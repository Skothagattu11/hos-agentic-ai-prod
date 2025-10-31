#!/usr/bin/env python3
"""
Quick script to set timezone for test user
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env")
        return False

    supabase = create_client(supabase_url, supabase_key)
    user_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'

    # Check current timezone
    print(f"Checking user {user_id}...")
    result = supabase.table('users').select('id, email, time_zone').eq('id', user_id).execute()

    if not result.data:
        print(f"[ERROR] User {user_id} not found in database")
        return False

    print(f"Current user data: {result.data[0]}")

    current_timezone = result.data[0].get('time_zone')

    if current_timezone:
        print(f"[INFO] User already has timezone: {current_timezone}")
        return True

    # Set timezone to America/New_York
    print(f"Setting timezone to America/New_York...")
    update_result = supabase.table('users').update({
        'time_zone': 'America/New_York'
    }).eq('id', user_id).execute()

    if update_result.data:
        print(f"[SUCCESS] Timezone updated successfully!")
        print(f"Updated user data: {update_result.data[0]}")
        return True
    else:
        print(f"[ERROR] Failed to update timezone")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
