"""
Get Supabase JWT Token

Simple script to login to Supabase and get JWT token for testing.

Usage:
    python testing/get_supabase_token.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


def main():
    print("\n" + "=" * 70)
    print("  GET SUPABASE JWT TOKEN")
    print("=" * 70)
    print("\nThis will login to Supabase and display your JWT token")

    # Get Supabase credentials from .env
    supabase_url = (
        os.getenv('SUPABASE_CAL_URL') or
        os.getenv('SUPABASE_URL')
    )
    supabase_key = (
        os.getenv('SUPABASE_CAL_ANON_KEY') or
        os.getenv('SUPABASE_KEY') or
        os.getenv('SUPABASE_ANON_KEY')
    )

    if not supabase_url or not supabase_key:
        print("\n❌ Error: Supabase credentials not found in .env")
        print("\nPlease set one of:")
        print("  - SUPABASE_CAL_URL and SUPABASE_CAL_ANON_KEY")
        print("  - SUPABASE_URL and SUPABASE_KEY")
        return

    print(f"\n📡 Supabase URL: {supabase_url}")

    # Get email and password
    print("\n" + "─" * 70)
    email = input("Email: ").strip()
    if not email:
        print("❌ Email is required")
        return

    import getpass
    password = getpass.getpass("Password: ")
    if not password:
        print("❌ Password is required")
        return

    print("\n🔄 Logging in to Supabase...")

    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        # Login
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.user or not response.session:
            print("\n❌ Login failed - no session returned")
            return

        # Display results
        print("\n" + "=" * 70)
        print("  ✅ LOGIN SUCCESSFUL")
        print("=" * 70)

        print(f"\n👤 User ID:")
        print(f"   {response.user.id}")

        print(f"\n📧 Email:")
        print(f"   {response.user.email}")

        print(f"\n🔑 Supabase JWT Token:")
        print(f"   {response.session.access_token}")

        print(f"\n⏰ Token Expires:")
        from datetime import datetime
        expires_at = datetime.fromtimestamp(response.session.expires_at)
        print(f"   {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n" + "=" * 70)
        print("  COPY THESE VALUES FOR TESTING")
        print("=" * 70)
        print("\nUse these in test_google_calendar_integration.py:")
        print(f"\n  User ID: {response.user.id}")
        print(f"\n  JWT Token: {response.session.access_token}")

    except Exception as e:
        print(f"\n❌ Login failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check your email and password are correct")
        print("  2. Verify user exists in Supabase Dashboard → Authentication → Users")
        print(f"  3. Your Supabase URL: {supabase_url}")
        print("\n  4. Check your .env file has:")
        print("     SUPABASE_CAL_URL=https://your-project.supabase.co")
        print("     SUPABASE_CAL_ANON_KEY=your_anon_key")


if __name__ == "__main__":
    main()
