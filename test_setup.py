#!/usr/bin/env python3
"""
HolisticOS Setup Test Script
Quick verification that everything is set up correctly
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    print("🔍 Testing File Structure...")
    
    project_root = Path(__file__).parent
    required_files = [
        "services/api_gateway/main.py",
        "services/orchestrator/main.py", 
        "services/agents/behavior/main.py",
        "services/agents/nutrition/main.py",
        "services/agents/routine/main.py",
        "shared_libs/utils/system_prompts.py",
        "shared_libs/event_system/base_agent.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files found")
        return True

def test_python_imports():
    """Test that Python can import our modules"""
    print("\n🐍 Testing Python Imports...")
    
    # Add project to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    tests = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("redis", "Redis client"),
        ("shared_libs.utils.system_prompts", "HolisticOS system prompts"),
        ("services.api_gateway.main", "API Gateway module")
    ]
    
    failed_imports = []
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name} - {description}")
        except ImportError as e:
            print(f"  ❌ {module_name} - {description} ({e})")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n❌ Failed to import {len(failed_imports)} modules")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print(f"\n✅ All {len(tests)} imports successful")
        return True

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔴 Testing Redis Connection...")
    
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        print("  ✓ Redis connection successful")
        return True
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        print("  Start Redis with: docker run -d -p 6379:6379 redis:alpine")
        return False

def test_environment():
    """Test environment variables"""
    print("\n🌍 Testing Environment...")
    
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("  ✓ .env file exists")
        
        # Load and check key variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            required_vars = ["OPENAI_API_KEY", "REDIS_URL"]
            optional_vars = ["SUPABASE_URL", "DATABASE_URL"]
            
            for var in required_vars:
                if os.getenv(var):
                    print(f"  ✓ {var} is set")
                else:
                    print(f"  ❌ {var} is not set")
            
            for var in optional_vars:
                if os.getenv(var):
                    print(f"  ✓ {var} is set")
                else:
                    print(f"  ⚠ {var} is not set (optional)")
                    
        except ImportError:
            print("  ⚠ python-dotenv not available, using system environment")
        
        return True
    else:
        print("  ❌ .env file not found")
        return False

def test_system_prompts():
    """Test system prompts functionality"""
    print("\n📝 Testing System Prompts...")
    
    try:
        from shared_libs.utils.system_prompts import get_system_prompt
        
        prompt_types = ["behavior_analysis", "plan_generation", "memory_management"]
        for prompt_type in prompt_types:
            prompt = get_system_prompt(prompt_type)
            if len(prompt) > 0:
                print(f"  ✓ {prompt_type} prompt loaded ({len(prompt):,} chars)")
            else:
                print(f"  ❌ {prompt_type} prompt is empty")
        
        print("\n✅ System prompts test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ System prompts test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 HolisticOS Setup Verification")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_python_imports), 
        ("Redis Connection", test_redis_connection),
        ("Environment Variables", test_environment),
        ("System Prompts", test_system_prompts)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your HolisticOS setup is ready.")
        print("\n🚀 Next steps:")
        print("  1. Run: python start_simple.py")
        print("  2. Test: curl http://localhost:8001/api/health")
        print("  3. Try full analysis with different archetypes")
        return True
    else:
        print(f"\n⚠ {len(results) - passed} tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)