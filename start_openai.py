#!/usr/bin/env python3
"""
HolisticOS OpenAI-Based Startup Script
Uses OpenAI API directly with HolisticOS system prompts - avoids TensorFlow issues
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 HolisticOS OpenAI-Based Testing Mode")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent
    print(f"📁 Project Root: {project_root}")
    
    # Change to project directory
    os.chdir(project_root)
    print(f"📍 Working Directory: {os.getcwd()}")
    
    # Set Python path
    os.environ["PYTHONPATH"] = str(project_root)
    print(f"🐍 Python Path: {project_root}")
    
    # Check environment file and OpenAI key
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ No .env file found")
        return False
    
    print("✓ Environment file found")
    
    # Load environment and check OpenAI key
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            print(f"✓ OpenAI API key loaded ({openai_key[:8]}...)")
        else:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
    except ImportError:
        print("⚠ python-dotenv not available")
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ OPENAI_API_KEY not found")
            return False
    
    # Test system prompts
    try:
        sys.path.insert(0, str(project_root))
        from shared_libs.utils.system_prompts import get_system_prompt
        prompt = get_system_prompt("behavior_analysis")
        print(f"✓ HolisticOS System Prompts loaded ({len(prompt):,} chars)")
    except Exception as e:
        print(f"❌ System Prompts error: {e}")
        return False
    
    print("\n🎯 Starting HolisticOS OpenAI Integration API...")
    print("   Mode: Direct OpenAI API + HolisticOS Prompts")
    print("   URL: http://localhost:8001")
    print("   Docs: http://localhost:8001/docs")
    print("   Health: http://localhost:8001/api/health")
    
    print("\n✅ Benefits of This Approach:")
    print("   • No TensorFlow compatibility issues")
    print("   • Uses your HolisticOS system prompts")
    print("   • Full archetype support (6 types)")
    print("   • Direct OpenAI GPT-4 integration")
    print("   • Same API interface as original system")
    
    print("\n🧪 Test Commands:")
    print("   # Health Check:")
    print("   curl http://localhost:8001/api/health")
    print()
    print("   # Foundation Builder Analysis:")
    print("   curl -X POST http://localhost:8001/api/analyze \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"user_id\": \"test_foundation\", \"archetype\": \"Foundation Builder\"}'")
    print()
    print("   # Peak Performer Analysis:")
    print("   curl -X POST http://localhost:8001/api/analyze \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"user_id\": \"test_peak\", \"archetype\": \"Peak Performer\"}'")
    print()
    print("   # Systematic Improver Analysis:")
    print("   curl -X POST http://localhost:8001/api/analyze \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"user_id\": \"test_systematic\", \"archetype\": \"Systematic Improver\"}'")
    
    print("\n" + "=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Start the OpenAI-based API gateway
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "services.api_gateway.openai_main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ]
        
        print(f"💻 Starting: {' '.join(cmd)}")
        print(f"🏠 Directory: {os.getcwd()}")
        print()
        
        # Run the server
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
    sys.exit(0 if success else 1)