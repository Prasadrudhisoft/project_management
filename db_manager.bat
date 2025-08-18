@echo off
setlocal enabledelayedexpansion

echo =========================================
echo  Database Manager - Project Manager
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

echo Select an option:
echo.
echo 1. Initialize/Reset Database
echo 2. Create Database Backup
echo 3. Restore Database from Backup
echo 4. Check Database Schema
echo 5. Create Demo Data
echo 6. Fix Database Schema (Fix PyMySQL errors)
echo 7. Exit
echo.

set /p choice=Enter your choice (1-7):

if "%choice%"=="1" goto init_db
if "%choice%"=="2" goto backup_db
if "%choice%"=="3" goto restore_db
if "%choice%"=="4" goto check_schema
if "%choice%"=="5" goto create_demo
if "%choice%"=="6" goto fix_schema
if "%choice%"=="7" goto exit
goto invalid_choice

:init_db
echo.
echo =========================================
echo  Initializing Database...
echo =========================================
echo.
echo WARNING: This will drop all existing tables and data!
set /p confirm=Are you sure? (y/N): 
if /i not "%confirm%"=="y" goto menu

python -c "
from utils.db_helper import DatabaseHelper
import config
try:
    db = DatabaseHelper(config.DB_CONFIG)
    db.init_database()
    print('✓ Database initialized successfully!')
except Exception as e:
    print(f'❌ Error: {e}')
"
pause
goto menu

:backup_db
echo.
echo =========================================
echo  Creating Database Backup...
echo =========================================
echo.

REM Create backups directory if it doesn't exist
if not exist backups mkdir backups

REM Generate timestamp for backup filename
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

echo Backup filename: backup_%timestamp%.sql
echo.

python -c "
import os, subprocess
import config

db_config = config.DB_CONFIG
backup_file = f'backups/backup_%timestamp%.sql'

try:
    # Use mysqldump to create backup
    cmd = [
        'mysqldump',
        '-h', db_config['host'],
        '-u', db_config['user'],
        f'-p{db_config[\"password\"]}',
        db_config['database']
    ]
    
    with open(backup_file, 'w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    
    if result.returncode == 0:
        print(f'✓ Backup created successfully: {backup_file}')
    else:
        print(f'❌ Backup failed: {result.stderr}')
except Exception as e:
    print(f'❌ Error creating backup: {e}')
"
pause
goto menu

:restore_db
echo.
echo =========================================
echo  Restore Database from Backup
echo =========================================
echo.

if not exist backups (
    echo ERROR: No backups directory found!
    pause
    goto menu
)

echo Available backups:
echo.
dir /b backups\*.sql 2>nul
if %errorlevel% neq 0 (
    echo No backup files found!
    pause
    goto menu
)

echo.
set /p backup_file=Enter backup filename (or 'cancel' to go back): 

if /i "%backup_file%"=="cancel" goto menu

if not exist "backups\%backup_file%" (
    echo ERROR: Backup file not found!
    pause
    goto menu
)

echo.
echo WARNING: This will overwrite the current database!
set /p confirm=Are you sure? (y/N): 
if /i not "%confirm%"=="y" goto menu

python -c "
import os, subprocess
import config

db_config = config.DB_CONFIG
backup_file = 'backups/%backup_file%'

try:
    cmd = [
        'mysql',
        '-h', db_config['host'],
        '-u', db_config['user'],
        f'-p{db_config[\"password\"]}',
        db_config['database']
    ]
    
    with open(backup_file, 'r') as f:
        result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
    
    if result.returncode == 0:
        print(f'✓ Database restored successfully from {backup_file}')
    else:
        print(f'❌ Restore failed: {result.stderr}')
except Exception as e:
    print(f'❌ Error restoring backup: {e}')
"
pause
goto menu

:check_schema
echo.
echo =========================================
echo  Checking Database Schema...
echo =========================================
echo.

python check_db_schema.py
pause
goto menu

:create_demo
echo.
echo =========================================
echo  Creating Demo Data...
echo =========================================
echo.

python -c "
from utils.db_helper import DatabaseHelper
import config

try:
    db = DatabaseHelper(config.DB_CONFIG)
    # Set CREATE_DEMO_DATA to True temporarily
    import os
    os.environ['CREATE_DEMO_DATA'] = 'True'
    
    db.init_database()
    print('✓ Demo data created successfully!')
    print('')
    print('Demo credentials:')
    print('Admin:   admin@demo.com / admin')
    print('Manager: manager@demo.com / manager')
    print('Member:  member@demo.com / member')
except Exception as e:
    print(f'❌ Error creating demo data: {e}')
"
pause
goto menu

:fix_schema
echo.
echo =========================================
echo  Fix Database Schema (PyMySQL Errors)
echo =========================================
echo.
echo This will add missing columns to fix PyMySQL errors.
echo The most common issue is missing 'assigned_manager_id' column.
echo.
echo This is safe to run and won't delete any data.
set /p confirm=Continue with schema fix? (y/N): 
if /i not "%confirm%"=="y" goto menu

echo.
echo Running database schema fix...
python fix_database_schema.py
echo.
echo Schema fix completed! Check the output above for results.
pause
goto menu

:invalid_choice
echo Invalid choice! Please select 1-7.
pause

:menu
echo.
goto :eof

:exit
echo Goodbye!
timeout /t 2 >nul
