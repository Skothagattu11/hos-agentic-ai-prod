@echo off
REM HolisticOS OpenAI Server Startup Script with Logging for Windows
REM Usage: Double-click this file OR run from PowerShell/Command Prompt
REM All server output will be saved to logs/server_TIMESTAMP.log

REM Set UTF-8 encoding for Python to support emojis
set PYTHONIOENCODING=utf-8
chcp 65001 > nul

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Generate timestamped log filename using PowerShell
for /f "usebackq tokens=*" %%i in (`powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"`) do set TIMESTAMP=%%i
set LOG_FILE=logs\server_%TIMESTAMP%.log

echo ========================================
echo Starting HolisticOS AI Server with Logging
echo ========================================
echo.
echo Server output will be saved to: %LOG_FILE%
echo Press Ctrl+C to stop the server
echo.
echo To view logs in real-time (in another Command Prompt):
echo   powershell -Command "Get-Content %LOG_FILE% -Wait -Tail 50"
echo.
echo ========================================
echo.

REM Start server and redirect ALL output (stdout + stderr) to log file
REM Note: Output goes ONLY to file, not to console (for clean operation)
python start_openai.py > %LOG_FILE% 2>&1

echo.
echo ========================================
echo Server stopped. Logs saved to: %LOG_FILE%
echo ========================================
pause
