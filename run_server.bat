@echo off
echo Starting RAG API Server...
echo.

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run install_venv.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting server on http://localhost:8080
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.api.main:app --reload --port 8080