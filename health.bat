@echo off
echo =========================================
echo  System Health Check
echo =========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requests if not present (for health check)
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing requests package for health checks...
    pip install requests
)

echo Running comprehensive health check...
echo.

REM Run health check
python health_check.py %*

echo.
pause
