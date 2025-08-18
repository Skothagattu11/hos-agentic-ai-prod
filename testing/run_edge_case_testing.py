#!/usr/bin/env python3
"""
Edge Case Testing Runner for HolisticOS MVP
Comprehensive testing suite for production readiness validation
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to Python path (go up one level from testing folder)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    
    # Try to load from .env file in project root
    env_file_path = os.path.join(project_root, '.env')
    if os.path.exists(env_file_path):
        load_dotenv(env_file_path)
        print(f"✅ Loaded environment variables from {env_file_path}")
    else:
        print(f"⚠️  .env file not found at {env_file_path}")
        
except ImportError:
    print("⚠️  python-dotenv not found. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

from tests.chaos.chaos_testing_suite import ChaosTestingSuite
from tests.chaos.failure_injection import FailureInjector, get_testing_instructions

def print_banner():
    """Print testing banner"""
    print("🧪" + "=" * 60 + "🧪")
    print("     HOLISTICOS MVP - EDGE CASE TESTING SUITE")
    print("     Production Readiness Validation")
    print("🧪" + "=" * 60 + "🧪")
    print()

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Environment Configuration Check...")
    
    # Debug: Show some key environment variables
    debug_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "EMAIL_API_KEY"]
    print("Debug - Environment variables status:")
    for var in debug_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: {value[:10]}..." if len(value) > 10 else f"  {var}: {value}")
        else:
            print(f"  {var}: NOT SET")
    print()
    
    required_vars = ["OPENAI_API_KEY"]
    database_vars = ["DATABASE_URL", "SUPABASE_URL"]
    alerting_vars = ["EMAIL_API_KEY", "EMAIL_PROVIDER", "ALERT_EMAIL_FROM", "ALERT_EMAIL_RECIPIENTS"]
    optional_vars = ["SLACK_WEBHOOK_URL", "REDIS_URL", "ALERT_EMAIL_USER", "SMTP_SERVER"]
    
    missing_required = []
    missing_database = []
    missing_alerting = []
    available_optional = []
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"  ✅ {var}: Configured")
    
    # Check database configuration (need at least one)
    has_database_config = False
    for var in database_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Configured")
            has_database_config = True
        else:
            missing_database.append(var)
    
    if not has_database_config:
        missing_required.extend(missing_database)
    
    # Check alerting configuration
    has_alerting_config = True
    for var in alerting_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ⚠️  {var}: Not configured (needed for email alerts)")
            missing_alerting.append(var)
            has_alerting_config = False
    
    # Check optional variables
    for var in optional_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Configured")
            available_optional.append(var)
        else:
            print(f"  ⚠️  {var}: Not configured (optional)")
    
    print()
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nPlease set these variables before running tests.")
        return False
    
    if missing_alerting:
        print("⚠️  Email alerting not configured (tests will run but alerting tests may fail):")
        for var in missing_alerting:
            print(f"   - {var}")
        print()
    
    print("✅ Environment configuration looks good!")
    return True

async def run_baseline_test():
    """Run baseline functionality test"""
    print("📊 Running Baseline Functionality Test...")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test basic health check
            async with session.get("http://localhost:8001/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"  ✅ Health Check: {health_data.get('overall_status', 'unknown')}")
                    return True
                else:
                    print(f"  ❌ Health Check Failed: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        print(f"  ❌ Baseline Test Failed: {str(e)}")
        print("  💡 Make sure HolisticOS is running on localhost:8001")
        return False

async def run_comprehensive_testing(user_id: str = None):
    """Run the complete chaos testing suite"""
    print("🚀 Starting Comprehensive Edge Case Testing...")
    if user_id:
        print(f"📌 Using User ID: {user_id}")
    print()
    
    try:
        async with ChaosTestingSuite() as chaos_tester:
            # Override primary user if provided
            if user_id:
                chaos_tester.primary_user = user_id
                chaos_tester.test_users[0] = user_id
                chaos_tester.users_with_analysis[0] = user_id
            report = await chaos_tester.run_all_chaos_tests()
            
            # Print summary
            summary = report["chaos_testing_report"]["summary"]
            print("\n" + "="*60)
            print("📊 TESTING SUMMARY")
            print("="*60)
            print(f"Total Tests: {summary['total_tests']}")
            print(f"✅ Passed: {summary['passed']}")
            print(f"⚠️  Partial: {summary['partial']}")
            print(f"❌ Failed: {summary['failed']}")
            print(f"💥 Crashed: {summary['crashed']}")
            print(f"🎯 Overall Score: {summary['score']}/100")
            print(f"🚀 Production Readiness: {summary['production_readiness']}")
            
            # Print recommendations
            if report["chaos_testing_report"]["recommendations"]:
                print("\n📋 RECOMMENDATIONS:")
                for rec in report["chaos_testing_report"]["recommendations"]:
                    print(f"  {rec}")
            
            return report
            
    except Exception as e:
        print(f"❌ Comprehensive testing failed: {str(e)}")
        return None

def run_failure_scenario(scenario_name: str):
    """Run specific failure scenario"""
    print(f"🎭 Running Failure Scenario: {scenario_name}")
    
    injector = FailureInjector()
    
    try:
        scenario_config = injector.create_chaos_scenario(scenario_name)
        
        print("⏳ Scenario active. Test your system now...")
        print("   - Check health endpoints")
        print("   - Monitor error handling")
        print("   - Verify alerting behavior")
        print("   - Test recovery mechanisms")
        print()
        
        input("Press Enter when you've finished testing this scenario...")
        
    except Exception as e:
        print(f"❌ Scenario setup failed: {str(e)}")
    finally:
        # Always restore environment
        injector.restore_environment()
        print("🔄 Environment restored")

def print_manual_testing_guide():
    """Print manual testing instructions"""
    print("📋 MANUAL TESTING GUIDE")
    print("="*40)
    
    instructions = get_testing_instructions()
    
    print("\n🔧 ENVIRONMENT SETUP:")
    for var, desc in instructions["environment_variables"]["required"].items():
        print(f"  export {var}='{desc}'")
    
    print("\n📧 EMAIL ALERTING SETUP:")
    for var, desc in instructions["environment_variables"]["alerting"].items():
        print(f"  export {var}='{desc}'")
    
    print(f"\n🧪 FAILURE SCENARIOS TO TEST:")
    for scenario in instructions["failure_scenarios"]["scenarios"]:
        print(f"  • {scenario['name']}")
        print(f"    Setup: {scenario['setup']}")
        print(f"    Expected: {scenario['expected']}")
        print()
    
    print("🔗 MONITORING ENDPOINTS:")
    for endpoint in instructions["monitoring_during_tests"]["endpoints"]:
        print(f"  • {endpoint}")

def main():
    """Main testing orchestrator"""
    print_banner()
    
    # Default user ID - YOUR REAL USER ID
    default_user_id = "35pDPUIfAoRl2Y700bFkxPKYjjf2"
    user_id = None
    
    # Check for user ID in arguments (format: --user=ID)
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--user="):
            user_id = arg.split("=")[1]
            sys.argv.pop(i)
            break
        elif arg == default_user_id:
            # If the exact default user ID is provided as an argument
            user_id = arg
            sys.argv.pop(i)
            break
    
    # Use default if not provided
    if not user_id:
        user_id = default_user_id
    
    print(f"📌 Using User ID: {user_id}")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "env-check":
            check_environment()
            return
        
        elif command == "baseline":
            if not check_environment():
                return
            asyncio.run(run_baseline_test())
            return
        
        elif command == "full":
            if not check_environment():
                return
            baseline_ok = asyncio.run(run_baseline_test())
            if baseline_ok:
                asyncio.run(run_comprehensive_testing(user_id))
            return
        
        elif command == "production-ready":
            # One-shot comprehensive validation for production readiness
            if not check_environment():
                return
            
            print("🚀 PRODUCTION READINESS VALIDATION")
            print("=" * 50)
            print("Running comprehensive test suite to validate production deployment...")
            print()
            
            # Step 1: Baseline test
            baseline_ok = asyncio.run(run_baseline_test())
            if not baseline_ok:
                print("❌ Baseline test failed. Cannot proceed with production validation.")
                return
            
            # Step 2: Full chaos testing
            report = asyncio.run(run_comprehensive_testing(user_id))
            if not report:
                print("❌ Comprehensive testing failed.")
                return
            
            # Step 3: Production readiness summary
            print("\n" + "🎯" * 20)
            print("PRODUCTION READINESS SUMMARY")
            print("🎯" * 20)
            
            summary = report["chaos_testing_report"]["summary"]
            print(f"📊 Total Tests: {summary['total_tests']}")
            print(f"✅ Passed: {summary['passed']}")
            print(f"⚠️  Partial: {summary['partial']}")
            print(f"❌ Failed: {summary['failed']}")
            print(f"💥 Crashed: {summary['crashed']}")
            print(f"🎯 Overall Score: {summary['score']}/100")
            
            if summary['score'] >= 80:
                print(f"🚀 PRODUCTION READY ✅")
                print("Your system is ready for deployment!")
            else:
                print(f"⚠️  NEEDS WORK ❌")
                print("Address the issues below before production deployment:")
                for rec in report["chaos_testing_report"]["recommendations"]:
                    print(f"  {rec}")
            
            print(f"\n💾 Detailed report saved as: chaos_test_report_{int(datetime.now().timestamp())}.json")
            return
        
        elif command == "scenario":
            if len(sys.argv) < 3:
                print("❌ Please specify scenario name")
                print("Available scenarios: missing_database, invalid_openai, timeout_stress, rate_limit_stress, complete_breakdown")
                return
            scenario = sys.argv[2]
            run_failure_scenario(scenario)
            return
        
        elif command == "guide":
            print_manual_testing_guide()
            return
    
    # Interactive menu
    while True:
        print("🎯 EDGE CASE TESTING MENU")
        print("=" * 30)
        print("1. 🔍 Check Environment")
        print("2. 📊 Run Baseline Test")
        print("3. 🧪 Run Full Chaos Testing")
        print("4. 🚀 Production Readiness Validation (One-Shot)")
        print("5. 🎭 Run Failure Scenario")
        print("6. 📋 Manual Testing Guide")
        print("7. 🚪 Exit")
        print()
        
        choice = input("Select option (1-7): ").strip()
        
        if choice == "1":
            check_environment()
            
        elif choice == "2":
            if not check_environment():
                continue
            baseline_ok = asyncio.run(run_baseline_test())
            
        elif choice == "3":
            if not check_environment():
                continue
            baseline_ok = asyncio.run(run_baseline_test())
            if baseline_ok:
                report = asyncio.run(run_comprehensive_testing(user_id))
                if report:
                    print(f"\n💾 Report saved as: chaos_test_report_{int(datetime.now().timestamp())}.json")
            
        elif choice == "4":
            # Production Readiness Validation (One-Shot)
            if not check_environment():
                continue
            
            print("🚀 PRODUCTION READINESS VALIDATION")
            print("=" * 50)
            print("Running comprehensive test suite to validate production deployment...")
            print()
            
            baseline_ok = asyncio.run(run_baseline_test())
            if baseline_ok:
                report = asyncio.run(run_comprehensive_testing(user_id))
                if report:
                    print("\n" + "🎯" * 20)
                    print("PRODUCTION READINESS SUMMARY")
                    print("🎯" * 20)
                    
                    summary = report["chaos_testing_report"]["summary"]
                    print(f"📊 Total Tests: {summary['total_tests']}")
                    print(f"✅ Passed: {summary['passed']}")
                    print(f"⚠️  Partial: {summary['partial']}")
                    print(f"❌ Failed: {summary['failed']}")
                    print(f"💥 Crashed: {summary['crashed']}")
                    print(f"🎯 Overall Score: {summary['score']}/100")
                    
                    if summary['score'] >= 80:
                        print(f"🚀 PRODUCTION READY ✅")
                        print("Your system is ready for deployment!")
                    else:
                        print(f"⚠️  NEEDS WORK ❌")
                        print("Address the issues below before production deployment:")
                        for rec in report["chaos_testing_report"]["recommendations"]:
                            print(f"  {rec}")
                    
                    print(f"\n💾 Detailed report saved as: chaos_test_report_{int(datetime.now().timestamp())}.json")
            
        elif choice == "5":
            print("\nAvailable failure scenarios:")
            print("  • missing_database - Remove database configuration")
            print("  • invalid_openai - Invalid OpenAI API key") 
            print("  • timeout_stress - Very aggressive timeouts")
            print("  • rate_limit_stress - Strict rate limiting")
            print("  • complete_breakdown - Multiple system failures")
            
            scenario = input("\nEnter scenario name: ").strip()
            if scenario:
                run_failure_scenario(scenario)
            
        elif choice == "6":
            print_manual_testing_guide()
            
        elif choice == "7":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-7.")
        
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()