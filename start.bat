@echo off
echo =========================================
echo  Simple Project Manager - Starting...
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

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

REM Set production environment
set FLASK_ENV=production
set FLASK_DEBUG=0

echo ✓ Environment: Production
echo ✓ Starting server on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo =========================================
echo.

REM Start the application
python app.py
