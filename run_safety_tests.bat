@echo off
REM Safety Test Runner Script for Windows
REM Runs safety validation tests within the .venv virtual environment
REM
REM Usage:
REM   run_safety_tests.bat unit             Run unit tests only
REM   run_safety_tests.bat quick            Run quick integration test (1 plan)
REM   run_safety_tests.bat full             Run full integration test (15 plans)
REM   run_safety_tests.bat archetype NAME   Test specific archetype
REM   run_safety_tests.bat all              Run all tests

setlocal enabledelayedexpansion

REM Get script directory
cd /d "%~dp0"

REM Check if .venv exists
if not exist ".venv" (
    echo [ERROR] .venv virtual environment not found
    echo Please create it first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if httpx is installed
python -c "import httpx" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing httpx (required for integration tests)...
    pip install httpx
)

REM Parse command line arguments
if "%1"=="unit" goto :run_unit
if "%1"=="quick" goto :run_quick
if "%1"=="full" goto :run_full
if "%1"=="archetype" goto :run_archetype
if "%1"=="all" goto :run_all
goto :show_usage

:run_unit
echo.
echo ================================================================================
echo   UNIT TESTS - Safety Validator Logic
echo ================================================================================
echo.
python testing\test_safety_validation.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Unit tests failed
    call :cleanup
    exit /b 1
)
echo.
echo [SUCCESS] Unit tests complete
echo.
goto :cleanup

:run_quick
echo.
echo ================================================================================
echo   QUICK INTEGRATION TEST - Single Plan Generation
echo ================================================================================
echo.
echo [WARNING] Make sure the server is running on http://localhost:8002
echo           Start with: python start_openai.py
echo.
pause
python testing\test_safety_integration_endpoint.py --quick
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Quick test failed
    call :cleanup
    exit /b 1
)
echo.
echo [SUCCESS] Quick test complete
echo.
goto :cleanup

:run_full
echo.
echo ================================================================================
echo   FULL INTEGRATION TEST - Multiple Archetypes and Iterations
echo ================================================================================
echo.
echo [WARNING] Make sure the server is running on http://localhost:8002
echo           Start with: python start_openai.py
echo.
echo [INFO] This will generate 15 plans (5 archetypes x 3 iterations)
echo        Estimated time: 5-10 minutes
echo.
pause
python testing\test_safety_integration_endpoint.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Full test failed
    call :cleanup
    exit /b 1
)
echo.
echo [SUCCESS] Full test complete
echo [INFO] Report saved to: testing\safety_test_report.json
echo.
goto :cleanup

:run_archetype
if "%2"=="" (
    echo [ERROR] Please specify archetype name
    echo Usage: run_safety_tests.bat archetype "Foundation Builder"
    goto :cleanup
)
echo.
echo ================================================================================
echo   ARCHETYPE TEST - %2
echo ================================================================================
echo.
echo [WARNING] Make sure the server is running on http://localhost:8002
echo           Start with: python start_openai.py
echo.
pause
python testing\test_safety_integration_endpoint.py --archetype "%2"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Archetype test failed
    call :cleanup
    exit /b 1
)
echo.
echo [SUCCESS] Archetype test complete
echo.
goto :cleanup

:run_all
call :run_unit
if %ERRORLEVEL% NEQ 0 (
    call :cleanup
    exit /b 1
)

echo.
echo [INFO] Starting integration tests...
echo [WARNING] Make sure the server is running on http://localhost:8002
echo.
pause

call :run_quick
if %ERRORLEVEL% NEQ 0 (
    call :cleanup
    exit /b 1
)

call :run_full
if %ERRORLEVEL% NEQ 0 (
    call :cleanup
    exit /b 1
)

echo.
echo [SUCCESS] All tests complete!
echo.
goto :cleanup

:show_usage
echo Safety Test Runner (Windows)
echo.
echo Usage:
echo   run_safety_tests.bat unit             Run unit tests only
echo   run_safety_tests.bat quick            Run quick integration test (1 plan)
echo   run_safety_tests.bat full             Run full integration test (15 plans)
echo   run_safety_tests.bat archetype NAME   Test specific archetype
echo   run_safety_tests.bat all              Run all tests
echo.
echo Examples:
echo   run_safety_tests.bat unit
echo   run_safety_tests.bat quick
echo   run_safety_tests.bat archetype "Peak Performer"
echo.
goto :cleanup

:cleanup
REM Deactivate virtual environment
call deactivate 2>nul
endlocal
exit /b 0
