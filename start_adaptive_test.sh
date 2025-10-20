#!/bin/bash
# Start server with adaptive routine generation enabled

echo "🔧 Setting environment variables..."
export USE_ADAPTIVE_ROUTINE=true
export ENVIRONMENT=development
export LOG_LEVEL=INFO

echo "🚀 Starting server with adaptive routine generation..."
echo "   Feature Flag: USE_ADAPTIVE_ROUTINE=true"
echo ""

python start_openai.py
