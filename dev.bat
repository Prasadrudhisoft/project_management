@echo off
echo =========================================
echo  Simple Project Manager - DEV MODE
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

REM Set development environment
set FLASK_ENV=development
set FLASK_DEBUG=1
set DEBUG=True

echo ✓ Environment: Development (Debug Mode ON)
echo ✓ Auto-reload: Enabled
echo ✓ Starting server on http://localhost:5000
echo.
echo The server will automatically restart when you make changes
echo Press Ctrl+C to stop the server
echo =========================================
echo.

REM Start the application in development mode
python app.py
