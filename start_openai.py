#!/usr/bin/env python3
"""
HolisticOS OpenAI-Based Startup Script
Uses OpenAI API directly with HolisticOS system prompts - avoids TensorFlow issues
Now with ULTRA-QUIET mode: Only shows errors and critical issues
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# ============================================
# ULTRA-QUIET MODE CONFIGURATION
# ============================================

# Set environment for quiet operation BEFORE any imports
os.environ["LOG_LEVEL"] = "ERROR"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["STRUCTLOG_LEVEL"] = "ERROR"
os.environ["UVICORN_LOG_LEVEL"] = "error"

# Configure logging to show only errors
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)

# Silence ALL noisy third-party libraries and internal services
for logger_name in [
    "httpx", "httpcore", "asyncio", "uvicorn.access", 
    "uvicorn.error", "uvicorn", "aiohttp", "openai", "supabase",
    "services", "shared_libs", "root", "",
    "shared_libs.database.connection_pool",
    "shared_libs.monitoring.alerting", 
    "shared_libs.supabase_client.adapter",
    "shared_libs.caching.lru_cache",
    "services.memory_integration_service",
    "services.user_data_service",
    "services.ondemand_analysis_service",
    "services.health_data_client",
    "services.simple_analysis_tracker",
    "services.insights_extraction_service",
    "httpx._client",
    "httpx",  # Add base httpx logger
    "httpcore",  # Add httpcore logger
    # Additional specific service loggers
    "services.user_data_service.health_data_client",
    "services.insights_extraction_service.insights_logger",
    "services.memory_integration_service.holistic_memory_service",
    "shared_libs.caching",
    "shared_libs.monitoring",
    "psutil"
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
    
# Also set the root logger to ERROR to catch any missed loggers
logging.getLogger().setLevel(logging.ERROR)

def main():
    print("🤫 Starting HolisticOS in ULTRA-QUIET mode (errors only)...")
    print("=" * 60)
    
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
            "--reload",
            "--log-level", "error"
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