#!/usr/bin/env python
"""
Simple Python Test Runner - Works on all platforms

Usage:
    python run_tests.py unit             Run unit tests only
    python run_tests.py quick            Run quick integration test (1 plan)
    python run_tests.py full             Run full integration test (15 plans)
    python run_tests.py archetype NAME   Test specific archetype
    python run_tests.py all              Run all tests
"""

import sys
import os
import subprocess
import argparse

# ANSI color codes for terminal output
COLORS = {
    'BLUE': '\033[0;34m',
    'GREEN': '\033[0;32m',
    'YELLOW': '\033[1;33m',
    'RED': '\033[0;31m',
    'NC': '\033[0m'  # No Color
}

def print_colored(text, color='NC'):
    """Print colored text"""
    if sys.platform == 'win32':
        # Windows terminal may not support colors well
        print(text)
    else:
        print(f"{COLORS.get(color, COLORS['NC'])}{text}{COLORS['NC']}")

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def run_command(cmd, description=None):
    """Run a command and return exit code"""
    if description:
        print_colored(f"\n[INFO] {description}", 'BLUE')

    print_colored(f"Running: {' '.join(cmd)}", 'YELLOW')
    result = subprocess.run(cmd)
    return result.returncode

def run_unit_tests():
    """Run unit tests"""
    print_section("UNIT TESTS - Safety Validator Logic")

    exit_code = run_command(
        [sys.executable, "testing/test_safety_validation.py"],
        "Running safety validator unit tests"
    )

    if exit_code == 0:
        print_colored("\n✅ Unit tests complete\n", 'GREEN')
    else:
        print_colored("\n❌ Unit tests failed\n", 'RED')

    return exit_code

def run_quick_test():
    """Run quick integration test"""
    print_section("QUICK INTEGRATION TEST - Single Plan Generation")

    print_colored("⚠️  Make sure the server is running on http://localhost:8002", 'YELLOW')
    print_colored("   Start with: python start_openai.py\n", 'YELLOW')

    input("Press Enter to continue or Ctrl+C to cancel...")

    exit_code = run_command(
        [sys.executable, "testing/test_safety_integration_endpoint.py", "--quick"],
        "Running quick integration test"
    )

    if exit_code == 0:
        print_colored("\n✅ Quick test complete\n", 'GREEN')
    else:
        print_colored("\n❌ Quick test failed\n", 'RED')

    return exit_code

def run_full_test():
    """Run full integration test"""
    print_section("FULL INTEGRATION TEST - Multiple Archetypes & Iterations")

    print_colored("⚠️  Make sure the server is running on http://localhost:8002", 'YELLOW')
    print_colored("   Start with: python start_openai.py\n", 'YELLOW')
    print_colored("⏱  This will generate 15 plans (5 archetypes × 3 iterations)", 'YELLOW')
    print_colored("   Estimated time: 5-10 minutes\n", 'YELLOW')

    input("Press Enter to continue or Ctrl+C to cancel...")

    exit_code = run_command(
        [sys.executable, "testing/test_safety_integration_endpoint.py"],
        "Running full integration test"
    )

    if exit_code == 0:
        print_colored("\n✅ Full test complete", 'GREEN')
        print_colored("📄 Report saved to: testing/safety_test_report.json\n", 'GREEN')
    else:
        print_colored("\n❌ Full test failed\n", 'RED')

    return exit_code

def run_archetype_test(archetype):
    """Run test for specific archetype"""
    print_section(f"ARCHETYPE TEST - {archetype}")

    print_colored("⚠️  Make sure the server is running on http://localhost:8002", 'YELLOW')
    print_colored("   Start with: python start_openai.py\n", 'YELLOW')

    input("Press Enter to continue or Ctrl+C to cancel...")

    exit_code = run_command(
        [sys.executable, "testing/test_safety_integration_endpoint.py", "--archetype", archetype],
        f"Running test for {archetype}"
    )

    if exit_code == 0:
        print_colored(f"\n✅ Archetype test complete\n", 'GREEN')
    else:
        print_colored(f"\n❌ Archetype test failed\n", 'RED')

    return exit_code

def run_all_tests():
    """Run all tests"""
    # Unit tests
    exit_code = run_unit_tests()
    if exit_code != 0:
        return exit_code

    # Integration tests
    print_colored("\nStarting integration tests...", 'YELLOW')
    print_colored("⚠️  Make sure the server is running on http://localhost:8002\n", 'YELLOW')

    input("Press Enter to continue or Ctrl+C to cancel...")

    # Quick test
    exit_code = run_quick_test()
    if exit_code != 0:
        return exit_code

    # Full test
    exit_code = run_full_test()
    if exit_code != 0:
        return exit_code

    print_colored("\n🎉 All tests complete!\n", 'GREEN')
    return 0

def show_usage():
    """Show usage information"""
    print_colored("Safety Test Runner", 'BLUE')
    print("\nUsage:")
    print("  python run_tests.py unit             Run unit tests only")
    print("  python run_tests.py quick            Run quick integration test (1 plan)")
    print("  python run_tests.py full             Run full integration test (15 plans)")
    print("  python run_tests.py archetype NAME   Test specific archetype")
    print("  python run_tests.py all              Run all tests")
    print("\nExamples:")
    print('  python run_tests.py unit')
    print('  python run_tests.py quick')
    print('  python run_tests.py archetype "Peak Performer"')
    print()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Safety Test Runner")
    parser.add_argument('command', nargs='?', choices=['unit', 'quick', 'full', 'archetype', 'all'],
                       help='Test command to run')
    parser.add_argument('archetype_name', nargs='?', help='Archetype name (for archetype command)')

    args = parser.parse_args()

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Route to appropriate function
    if args.command == 'unit':
        return run_unit_tests()
    elif args.command == 'quick':
        return run_quick_test()
    elif args.command == 'full':
        return run_full_test()
    elif args.command == 'archetype':
        if not args.archetype_name:
            print_colored("Error: Please specify archetype name", 'RED')
            print('Usage: python run_tests.py archetype "Foundation Builder"')
            return 1
        return run_archetype_test(args.archetype_name)
    elif args.command == 'all':
        return run_all_tests()
    else:
        show_usage()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_colored("\n\nTest cancelled by user", 'YELLOW')
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n\nError: {e}", 'RED')
        sys.exit(1)
