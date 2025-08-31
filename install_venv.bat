@echo off
echo Installing Python virtual environment...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Installing dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo ========================================
echo Virtual environment setup complete!
echo.
echo To activate the environment, run:
echo    venv\Scripts\activate.bat
echo.
echo To run the API server:
echo    venv\Scripts\python.exe -m uvicorn app.api.main:app --reload --port 8080
echo ========================================
pause