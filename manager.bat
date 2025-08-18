@echo off
setlocal enabledelayedexpansion

:main_menu
cls
echo.
echo     ================================================
echo     🚀 Simple Project Manager - Control Panel
echo     ================================================
echo.
echo     What would you like to do?
echo.
echo     1. 🔧 Setup Project (First time setup)
echo     2. ▶️  Start Application (Production)
echo     3. 🛠️  Start Development Mode
echo     4. 🏥 Run Health Check
echo     5. 💾 Database Manager
echo     6. 📊 View Application Status  
echo     7. 🔄 Update Dependencies
echo     8. 📋 View Logs
echo     9. 🧹 Clean Temporary Files
echo     10. 🔧 Fix PyMySQL Database Errors
echo     11. ❓ Help ^& Documentation
echo     12. 🚪 Exit
echo.
echo     ================================================
echo.

set /p choice=Enter your choice (1-12):

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto start_prod
if "%choice%"=="3" goto start_dev
if "%choice%"=="4" goto health_check
if "%choice%"=="5" goto database_manager
if "%choice%"=="6" goto app_status
if "%choice%"=="7" goto update_deps
if "%choice%"=="8" goto view_logs
if "%choice%"=="9" goto cleanup
if "%choice%"=="10" goto fix_database
if "%choice%"=="11" goto help
if "%choice%"=="12" goto exit
goto invalid_choice

:setup
cls
echo.
echo ================================================
echo 🔧 Setting up Simple Project Manager...
echo ================================================
echo.
call setup.bat
pause
goto main_menu

:start_prod
cls
echo.
echo ================================================
echo ▶️  Starting Application in Production Mode...
echo ================================================
echo.
call start.bat
pause
goto main_menu

:start_dev
cls
echo.
echo ================================================
echo 🛠️  Starting Application in Development Mode...
echo ================================================
echo.
call dev.bat
pause
goto main_menu

:health_check
cls
echo.
echo ================================================
echo 🏥 Running System Health Check...
echo ================================================
echo.
call health.bat
pause
goto main_menu

:database_manager
cls
echo.
echo ================================================
echo 💾 Opening Database Manager...
echo ================================================
echo.
call db_manager.bat
pause
goto main_menu

:app_status
cls
echo.
echo ================================================
echo 📊 Application Status Check
echo ================================================
echo.

echo Checking if application is running...
curl -s -o nul -w "%%{http_code}" http://localhost:5000 >temp_status.txt 2>nul
set /p status_code=<temp_status.txt
del temp_status.txt 2>nul

if "%status_code%"=="200" (
    echo ✅ Application is RUNNING
    echo 🌐 URL: http://localhost:5000
    echo 📊 Status Code: %status_code%
) else (
    echo ❌ Application is NOT RUNNING
    echo 💡 Tip: Use option 2 or 3 to start the application
)

echo.
echo Checking system resources...

REM Check if virtual environment exists
if exist venv (
    echo ✅ Virtual Environment: Ready
) else (
    echo ❌ Virtual Environment: Not found - Run setup first
)

REM Check if .env file exists  
if exist .env (
    echo ✅ Configuration: .env file present
) else (
    echo ❌ Configuration: .env file missing
)

REM Check database connection (if venv exists)
if exist venv (
    echo.
    echo Checking database connection...
    call venv\Scripts\activate.bat
    python -c "
from utils.db_helper import DatabaseHelper
import config
try:
    db = DatabaseHelper(config.DB_CONFIG)
    conn = db.get_connection()
    if conn:
        conn.close()
        print('✅ Database: Connected')
    else:
        print('❌ Database: Connection failed')
except Exception as e:
    print('❌ Database: Error -', str(e))
" 2>nul
)

echo.
pause
goto main_menu

:update_deps
cls
echo.
echo ================================================
echo 🔄 Updating Dependencies...
echo ================================================
echo.

if not exist venv (
    echo ❌ Virtual environment not found!
    echo Please run setup first (option 1)
    pause
    goto main_menu
)

call venv\Scripts\activate.bat
echo Updating pip...
python -m pip install --upgrade pip

echo.
echo Installing/Updating packages...
pip install -r requirements.txt --upgrade

echo.
echo Installing additional useful packages...
pip install requests flask-wtf

echo.
echo ✅ Dependencies updated successfully!
pause
goto main_menu

:view_logs
cls
echo.
echo ================================================
echo 📋 Log Viewer
echo ================================================
echo.

if not exist logs (
    echo No logs directory found.
    echo Logs will be created when you run the application.
    pause
    goto main_menu
)

echo Available log files:
echo.
dir /b logs\*.* 2>nul

if %errorlevel% neq 0 (
    echo No log files found yet.
    echo Logs will be created when you run health checks or deployments.
    pause
    goto main_menu
)

echo.
set /p log_choice=Enter log filename to view (or press Enter to go back): 

if "%log_choice%"=="" goto main_menu

if exist "logs\%log_choice%" (
    echo.
    echo Displaying: logs\%log_choice%
    echo ================================================
    type "logs\%log_choice%"
    echo ================================================
) else (
    echo File not found: logs\%log_choice%
)

echo.
pause
goto main_menu

:cleanup
cls
echo.
echo ================================================
echo 🧹 Cleaning Temporary Files...
echo ================================================
echo.

echo Cleaning Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f" 2>nul

echo Cleaning temporary files...
if exist temp_status.txt del temp_status.txt 2>nul
if exist *.tmp del *.tmp 2>nul

echo Cleaning old log files (older than 30 days)...
forfiles /p logs /s /m *.* /d -30 /c "cmd /c del @path" 2>nul

echo.
echo ✅ Cleanup completed!
pause
goto main_menu

:fix_database
cls
echo.
echo ================================================
echo 🔧 Fix PyMySQL Database Errors
echo ================================================
echo.
echo This will fix the error:
echo "Unknown column 'assigned_manager_id' in 'where clause'"
echo.
echo This is safe and won't delete any existing data.
echo.
call fix_pymysql_error.bat
pause
goto main_menu

:help
cls
echo.
echo ================================================
echo ❓ Help ^& Documentation
echo ================================================
echo.
echo 🚀 QUICK START GUIDE:
echo.
echo 1. First Time Setup:
echo    - Run option 1 to set up the project
echo    - Edit .env file with your database settings
echo    - Make sure MySQL is running
echo.
echo 2. Running the Application:
echo    - Option 2: Production mode (recommended)
echo    - Option 3: Development mode (for coding)
echo.
echo 3. Maintenance:
echo    - Option 4: Check system health
echo    - Option 5: Manage database backups
echo    - Option 7: Update dependencies
echo.
echo 📖 CONFIGURATION:
echo.
echo - Database settings: Edit .env file
echo - Application branding: Edit branding_config.py
echo - Flask settings: Edit config.py
echo.
echo 🔧 TROUBLESHOOTING:
echo.
echo Common issues:
echo - Database connection error: Check MySQL is running
echo - Module not found: Run option 7 to update dependencies
echo - Permission error: Run as administrator
echo - Port already in use: Stop other applications on port 5000
echo.
echo 📱 DEFAULT LOGIN CREDENTIALS:
echo.
echo After running setup with demo data:
echo - Admin: admin@demo.com / admin
echo - Manager: manager@demo.com / manager  
echo - Member: member@demo.com / member
echo.
echo 🌐 APPLICATION URLS:
echo.
echo - Main app: http://localhost:5000
echo - Admin panel: http://localhost:5000/users (admin only)
echo - Reports: http://localhost:5000/reports (admin/manager)
echo.
echo 📂 PROJECT STRUCTURE:
echo.
echo - app.py: Main application file
echo - config.py: Configuration settings
echo - utils/: Database helper functions
echo - templates/: HTML templates
echo - static/: CSS, JS, images
echo - logs/: Application logs
echo - backups/: Database backups
echo.
pause
goto main_menu

:invalid_choice
cls
echo.
echo ❌ Invalid choice! Please select a number between 1-12.
timeout /t 2 >nul
goto main_menu

:exit
cls
echo.
echo ================================================
echo 👋 Thank you for using Simple Project Manager!
echo ================================================
echo.
echo Made with ❤️ by Rudhisoft (Razi and Om)
echo.
echo Visit us at: https://www.projectpro.com
echo Support: rudhisoft@gmail.com
echo.
timeout /t 3 >nul
exit /b 0
