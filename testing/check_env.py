#!/usr/bin/env python3
"""
Quick environment variable checker
"""
import os
from dotenv import load_dotenv

print("🔍 Environment Variable Checker")
print("=" * 40)

# Load .env file
env_file = ".env"
if os.path.exists(env_file):
    print(f"✅ Found {env_file} file")
    load_dotenv(env_file)
    print(f"✅ Loaded environment variables from {env_file}")
else:
    print(f"❌ {env_file} file not found")

print("\n📋 Checking key variables:")

# Check key variables
key_vars = {
    "OPENAI_API_KEY": "OpenAI API Key",
    "SUPABASE_URL": "Supabase URL", 
    "SUPABASE_KEY": "Supabase Key",
    "EMAIL_API_KEY": "Email API Key (Resend)",
    "EMAIL_PROVIDER": "Email Provider",
    "ALERT_EMAIL_FROM": "Alert Email From",
    "ALERT_EMAIL_RECIPIENTS": "Alert Email Recipients"
}

all_set = True
for var, description in key_vars.items():
    value = os.getenv(var)
    if value:
        # Show first 10 chars for security
        display_value = f"{value[:10]}..." if len(value) > 10 else value
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ❌ {var}: NOT SET")
        all_set = False

print(f"\n{'✅ All key variables are set!' if all_set else '⚠️ Some variables are missing'}")

# Show .env file content (masked)
print(f"\n📄 .env file content (values masked):")
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    print(f"  {line_num:2d}: {key}=***")
                else:
                    print(f"  {line_num:2d}: {line}")
            elif line.startswith('#'):
                print(f"  {line_num:2d}: {line}")