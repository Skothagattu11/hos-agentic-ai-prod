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
    print("🚀 Starting HolisticOS OpenAI API...")
    
    # Get project root and setup
    project_root = Path(__file__).parent
    os.chdir(project_root)
    os.environ["PYTHONPATH"] = str(project_root)
    
    # Check environment
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ No .env file found")
        return False
    
    # Load environment and check OpenAI key
    try:
        from dotenv import load_dotenv
        load_dotenv()
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ OPENAI_API_KEY not found")
            return False
    except ImportError:
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not found")
            return False
    
    # Test system prompts
    try:
        sys.path.insert(0, str(project_root))
        from shared_libs.utils.system_prompts import get_system_prompt
        get_system_prompt("behavior_analysis")
    except Exception as e:
        print(f"❌ System Prompts error: {e}")
        return False
    
    print("✅ Environment ready - Starting server on http://localhost:8001")
    print("   Docs: http://localhost:8001/docs")
    print("   Health: http://localhost:8001/api/health")
    print("=" * 50)
    
    # Start the server
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "services.api_gateway.openai_main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ]
        
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