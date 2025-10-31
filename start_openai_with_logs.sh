#!/bin/bash
# Start OpenAI server with comprehensive logging to file

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate timestamped log filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/server_${TIMESTAMP}.log"

echo "========================================"
echo "Starting HolisticOS AI Server with Logging"
echo "========================================"
echo ""
echo "Server output will be saved to: $LOG_FILE"
echo "Press Ctrl+C to stop the server"
echo ""
echo "To view logs in real-time (in another terminal):"
echo "  tail -f $LOG_FILE"
echo ""
echo "========================================"
echo ""

# Start server and pipe output to both console AND file
# Using 'tee' so you can see logs in terminal AND they're saved to file
python start_openai.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "========================================"
echo "Server stopped. Logs saved to: $LOG_FILE"
echo "========================================"
