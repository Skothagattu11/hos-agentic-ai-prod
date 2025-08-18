"""
Failure Injection Tools for Chaos Testing
Create controlled failure scenarios to test system resilience
"""

import os
import asyncio
import time
import psutil
import random
from typing import Dict, Any, List

class FailureInjector:
    """Tools to create controlled failure scenarios"""
    
    def __init__(self):
        self.original_env = {}
        self.active_failures = []
    
    # ========================
    # ENVIRONMENT MANIPULATION
    # ========================
    
    def simulate_missing_env_vars(self, env_vars: List[str]):
        """Temporarily remove environment variables to test error handling"""
        print(f"🧪 Simulating missing environment variables: {env_vars}")
        
        for var in env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
        
        self.active_failures.append("missing_env_vars")
    
    def simulate_invalid_database_url(self):
        """Set invalid database URL to test connection handling"""
        print("🧪 Simulating invalid database URL")
        
        if "DATABASE_URL" in os.environ:
            self.original_env["DATABASE_URL"] = os.environ["DATABASE_URL"]
        
        # Set invalid database URL
        os.environ["DATABASE_URL"] = "postgresql://invalid:invalid@invalid:5432/invalid"
        self.active_failures.append("invalid_database")
    
    def simulate_invalid_openai_key(self):
        """Set invalid OpenAI API key to test error handling"""
        print("🧪 Simulating invalid OpenAI API key")
        
        if "OPENAI_API_KEY" in os.environ:
            self.original_env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
        
        # Set invalid API key
        os.environ["OPENAI_API_KEY"] = "sk-invalid-key-for-testing"
        self.active_failures.append("invalid_openai_key")
    
    def restore_environment(self):
        """Restore original environment variables"""
        print("🔄 Restoring original environment variables")
        
        for var, value in self.original_env.items():
            os.environ[var] = value
        
        self.original_env.clear()
        self.active_failures.clear()
    
    # ========================
    # NETWORK SIMULATION
    # ========================
    
    def get_network_delay_script(self) -> str:
        """Get script to simulate network delays (requires sudo)"""
        return """
        # Network delay simulation (run with sudo)
        # Add 2 second delay to OpenAI API calls
        sudo tc qdisc add dev eth0 root netem delay 2000ms
        
        # Remove delay
        sudo tc qdisc del dev eth0 root netem
        """
    
    def get_memory_pressure_script(self) -> str:
        """Get script to create memory pressure"""
        return """
        # Memory pressure simulation
        # Fill up memory to test cleanup behavior
        python3 -c "
        import time
        data = []
        try:
            for i in range(1000):
                data.append('x' * 1024 * 1024)  # 1MB chunks
                time.sleep(0.1)
        except MemoryError:
            print('Memory pressure created')
            time.sleep(60)  # Hold for 1 minute
        "
        """
    
    # ========================
    # CONFIGURATION TWEAKS
    # ========================
    
    def set_aggressive_timeouts(self):
        """Set very short timeouts to trigger timeout handling"""
        print("🧪 Setting aggressive timeouts for testing")
        
        timeout_vars = {
            "OPENAI_REQUEST_TIMEOUT": "5",  # Very short
            "DATABASE_QUERY_TIMEOUT": "3", # Very short
            "BEHAVIOR_ANALYSIS_TIMEOUT": "10", # Very short
        }
        
        for var, value in timeout_vars.items():
            if var in os.environ:
                self.original_env[var] = os.environ[var]
            os.environ[var] = value
        
        self.active_failures.append("aggressive_timeouts")
    
    def set_strict_rate_limits(self):
        """Set very strict rate limits for testing"""
        print("🧪 Setting strict rate limits for testing")
        
        # These would be used by your rate limiting system
        rate_limit_vars = {
            "RATE_LIMIT_FREE_TIER": "2",  # Only 2 requests per hour
            "RATE_LIMIT_COST_DAILY": "0.10",  # Only $0.10 per day
        }
        
        for var, value in rate_limit_vars.items():
            if var in os.environ:
                self.original_env[var] = os.environ[var]
            os.environ[var] = value
        
        self.active_failures.append("strict_rate_limits")
    
    # ========================
    # CHAOS SCENARIOS
    # ========================
    
    def create_chaos_scenario(self, scenario: str) -> Dict[str, Any]:
        """Create specific chaos testing scenarios"""
        
        scenarios = {
            "missing_database": {
                "description": "Remove database configuration",
                "action": lambda: self.simulate_missing_env_vars(["DATABASE_URL", "SUPABASE_URL"]),
                "expected": "Database connection errors, graceful degradation"
            },
            
            "invalid_openai": {
                "description": "Invalid OpenAI API key",
                "action": lambda: self.simulate_invalid_openai_key(),
                "expected": "Authentication errors, retry logic activation"
            },
            
            "timeout_stress": {
                "description": "Very aggressive timeouts",
                "action": lambda: self.set_aggressive_timeouts(),
                "expected": "Timeout errors, fallback responses"
            },
            
            "rate_limit_stress": {
                "description": "Strict rate limiting",
                "action": lambda: self.set_strict_rate_limits(),
                "expected": "Rate limit violations, 429 responses"
            },
            
            "complete_breakdown": {
                "description": "Multiple system failures",
                "action": lambda: [
                    self.simulate_invalid_database_url(),
                    self.simulate_invalid_openai_key(),
                    self.set_aggressive_timeouts()
                ],
                "expected": "Multiple error types, system resilience testing"
            }
        }
        
        if scenario in scenarios:
            scenario_config = scenarios[scenario]
            print(f"🎭 Creating chaos scenario: {scenario}")
            print(f"📝 Description: {scenario_config['description']}")
            print(f"🎯 Expected: {scenario_config['expected']}")
            
            # Execute the scenario
            if callable(scenario_config["action"]):
                scenario_config["action"]()
            else:
                for action in scenario_config["action"]:
                    action()
            
            return scenario_config
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

# ========================
# TESTING RECOMMENDATIONS
# ========================

def get_testing_instructions() -> Dict[str, Any]:
    """Get comprehensive testing instructions"""
    
    return {
        "setup_requirements": {
            "description": "What you need to set up before testing",
            "items": [
                "✅ HolisticOS system running on localhost:8001",
                "✅ Real database with test user data",
                "✅ Valid OpenAI API key in environment",
                "✅ Email configuration for alerting tests",
                "📧 Test email addresses for alert validation",
                "⚠️ NO Redis required (system handles graceful degradation)"
            ]
        },
        
        "environment_variables": {
            "description": "Required environment variables for full testing",
            "required": {
                "OPENAI_API_KEY": "Your OpenAI API key",
                "DATABASE_URL": "PostgreSQL connection string OR",
                "SUPABASE_URL": "https://[project].supabase.co",
                "SUPABASE_KEY": "Your Supabase anon key"
            },
            "alerting": {
                "EMAIL_API_KEY": "re_fFmDBtr2_7TYL16MfehARj9dv2zC4xhf4",
                "EMAIL_PROVIDER": "resend",
                "ALERT_EMAIL_FROM": "alerts@holisticos.tech",
                "ALERT_EMAIL_RECIPIENTS": "surya.k@holisticos.tech,admin@holisticos.tech",
                "ALERT_EMAIL_USER": "Optional: SMTP fallback username",
                "ALERT_EMAIL_PASSWORD": "Optional: SMTP fallback password",
                "SMTP_SERVER": "Optional: smtp.holisticos.tech (fallback)",
                "SMTP_PORT": "Optional: 587 (fallback)"
            },
            "optional": {
                "SLACK_WEBHOOK_URL": "https://hooks.slack.com/... (fallback)",
                "REDIS_URL": "redis://localhost:6379 (optional)"
            },
            "testing_overrides": {
                "ENVIRONMENT": "testing",
                "OPENAI_REQUEST_TIMEOUT": "30",
                "DATABASE_QUERY_TIMEOUT": "30",
                "BEHAVIOR_ANALYSIS_TIMEOUT": "120"
            }
        },
        
        "failure_scenarios": {
            "description": "Specific failure scenarios to test",
            "scenarios": [
                {
                    "name": "Database Connection Failure",
                    "setup": "Set invalid DATABASE_URL",
                    "expected": "Health checks fail, error handling activates, system gracefully degrades"
                },
                {
                    "name": "OpenAI API Failure", 
                    "setup": "Set invalid OPENAI_API_KEY",
                    "expected": "Authentication errors, retry logic with exponential backoff"
                },
                {
                    "name": "Memory Pressure",
                    "setup": "Generate 50+ concurrent requests",
                    "expected": "Memory cleanup activates, LRU cache eviction, bounded collections work"
                },
                {
                    "name": "Rate Limiting",
                    "setup": "Make 10+ rapid requests with same user",
                    "expected": "Rate limiting kicks in, 429 responses, cost tracking accurate"
                },
                {
                    "name": "Timeout Scenarios",
                    "setup": "Set very low timeout values",
                    "expected": "Timeout errors handled gracefully, fallback responses"
                }
            ]
        },
        
        "testing_commands": {
            "description": "Commands to run different test scenarios",
            "commands": [
                "python tests/chaos/chaos_testing_suite.py",  # Full chaos testing
                "python tests/chaos/failure_injection.py",   # Specific failure scenarios
                "python tests/load/load_test_suite.py",      # Load testing
                "curl http://localhost:8001/api/health",     # Quick health check
                "curl http://localhost:8001/api/monitoring/stats"  # Monitoring data
            ]
        },
        
        "monitoring_during_tests": {
            "description": "What to monitor while testing",
            "endpoints": [
                "http://localhost:8001/api/health - System health",
                "http://localhost:8001/api/monitoring/stats - Performance metrics", 
                "http://localhost:8001/metrics - Prometheus metrics",
                "Check email for alerts during failures",
                "Monitor console logs for error handling"
            ]
        }
    }

if __name__ == "__main__":
    # Print testing instructions
    instructions = get_testing_instructions()
    
    print("🧪 CHAOS TESTING SETUP INSTRUCTIONS")
    print("=" * 50)
    
    for section, config in instructions.items():
        print(f"\n📋 {section.upper().replace('_', ' ')}")
        print(f"   {config['description']}")
        
        if 'items' in config:
            for item in config['items']:
                print(f"   {item}")
        
        if 'required' in config:
            print("   Required:")
            for key, desc in config['required'].items():
                print(f"     {key}: {desc}")
        
        if 'alerting' in config:
            print("   Email Alerting:")
            for key, desc in config['alerting'].items():
                print(f"     {key}: {desc}")
        
        if 'scenarios' in config:
            for scenario in config['scenarios']:
                print(f"   • {scenario['name']}: {scenario['setup']} → {scenario['expected']}")
        
        if 'commands' in config:
            for cmd in config['commands']:
                print(f"   • {cmd}")
        
        if 'endpoints' in config:
            for endpoint in config['endpoints']:
                print(f"   • {endpoint}")
    
    print("\n🚀 Ready to start chaos testing!")
    print("Run: python tests/chaos/chaos_testing_suite.py")