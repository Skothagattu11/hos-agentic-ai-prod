#!/usr/bin/env python3
"""
Test environment configuration behavior
Shows how the system behaves differently in development vs production
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from shared_libs.utils.environment_config import EnvironmentConfig

def test_environment_config():
    """Test and display environment configuration"""
    
    print("=" * 60)
    print("🔍 ENVIRONMENT CONFIGURATION TEST")
    print("=" * 60)
    
    # Current environment
    current_env = EnvironmentConfig.get_environment()
    print(f"\n📌 Current Environment: {current_env.upper()}")
    print(f"   - Is Development: {EnvironmentConfig.is_development()}")
    print(f"   - Is Production: {EnvironmentConfig.is_production()}")
    print(f"   - Is Staging: {EnvironmentConfig.is_staging()}")
    
    # Database configuration
    print(f"\n💾 Database Configuration:")
    print(f"   - Should Use Connection Pool: {EnvironmentConfig.should_use_connection_pool()}")
    print(f"   - DATABASE_URL Set: {bool(os.getenv('DATABASE_URL'))}")
    if os.getenv('DATABASE_URL'):
        db_url = os.getenv('DATABASE_URL')
        if 'db.ijcckqnqruwvqqbkiubb.supabase.co' in db_url:
            print(f"   - URL Type: IPv6 Direct (WSL2 Incompatible)")
        elif 'pooler.supabase.com' in db_url:
            print(f"   - URL Type: Supavisor Pooler (IPv4 Compatible)")
        else:
            print(f"   - URL Type: Custom")
    
    db_config = EnvironmentConfig.get_database_config()
    print(f"\n   Pool Settings:")
    print(f"   - Min Connections: {db_config['min_size']}")
    print(f"   - Max Connections: {db_config['max_size']}")
    print(f"   - Command Timeout: {db_config['command_timeout']}s")
    
    # Other configurations
    print(f"\n⚙️ Other Settings:")
    print(f"   - Log Level: {EnvironmentConfig.get_log_level()}")
    print(f"   - Debug Endpoints Enabled: {EnvironmentConfig.should_enable_debug_endpoints()}")
    
    timeout_config = EnvironmentConfig.get_timeout_config()
    print(f"\n⏱️ Timeout Configuration:")
    for key, value in timeout_config.items():
        print(f"   - {key}: {value}s")
    
    # Behavior summary
    print(f"\n✅ BEHAVIOR SUMMARY FOR {current_env.upper()}:")
    if EnvironmentConfig.is_development():
        print("   • Connection pool DISABLED (using Supabase client)")
        print("   • Debug endpoints ENABLED")
        print("   • Lower timeouts for faster development")
        print("   • Detailed logging (INFO level)")
    elif EnvironmentConfig.is_production():
        print("   • Connection pool ENABLED")
        print("   • Debug endpoints DISABLED")
        print("   • Higher timeouts for reliability")
        print("   • Minimal logging (WARNING level)")
    
    print("\n" + "=" * 60)
    
    # Test switching environments
    print("\n🔄 Testing Environment Switch...")
    original_env = os.environ.get("ENVIRONMENT", "development")
    
    # Test production mode
    os.environ["ENVIRONMENT"] = "production"
    print(f"\nSwitched to PRODUCTION:")
    print(f"   - Should Use Connection Pool: {EnvironmentConfig.should_use_connection_pool()}")
    print(f"   - Debug Endpoints: {EnvironmentConfig.should_enable_debug_endpoints()}")
    
    # Restore original
    os.environ["ENVIRONMENT"] = original_env
    print(f"\nRestored to {original_env.upper()}")
    
    print("\n✅ Environment configuration test complete!")

if __name__ == "__main__":
    test_environment_config()