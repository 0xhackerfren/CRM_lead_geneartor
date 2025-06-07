@echo off
title CRM Lead Generation AI Agent

echo.
echo ========================================
echo  CRM Lead Generation AI Agent
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "crm_venv\" (
    echo Creating virtual environment...
    python -m venv crm_venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call crm_venv\Scripts\activate.bat

:: Install/update requirements
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Run the application
echo.
echo Starting CRM Lead Generation AI Agent...
echo The application will open in your browser at http://localhost:7860
echo.
python main.py

pause 