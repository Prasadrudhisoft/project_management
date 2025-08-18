@echo off
echo =========================================
echo  Fix PyMySQL Database Error
echo =========================================
echo.
echo This will fix the error:
echo "Unknown column 'assigned_manager_id' in 'where clause'"
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

echo Running database schema fix...
echo.

REM Run the fix script
python fix_database_schema.py

echo.
echo Fix completed! You should now be able to login as a manager.
echo.
pause
