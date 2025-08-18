@echo off
echo =========================================
echo  Simple Project Manager - Setup Script
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

echo ✓ Python is installed
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

REM Install additional development packages
echo Installing development packages...
pip install bcrypt flask-wtf

REM Create .env file from template if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit the .env file and configure your database settings!
    echo - Set your database password
    echo - Generate a secure SECRET_KEY
    echo.
)

REM Create logs directory
if not exist logs (
    mkdir logs
    echo ✓ Created logs directory
)

REM Create uploads directory (if needed for file uploads)
if not exist uploads (
    mkdir uploads
    echo ✓ Created uploads directory
)

echo.
echo =========================================
echo  Setup completed successfully! 🎉
echo =========================================
echo.
echo Next steps:
echo 1. Edit .env file with your database settings
echo 2. Make sure MySQL is running
echo 3. Run: start.bat (to start the application)
echo.
echo For development mode, run: dev.bat
echo.

pause
