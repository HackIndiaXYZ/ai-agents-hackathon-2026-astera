@echo off
echo ========================================
echo   ASTERIA — AI Agent Startup
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and fill in your API keys.
    pause
    exit /b 1
)

echo [1/3] Starting backend server...
cd backend
start "Asteria Backend" cmd /k "python main.py"
cd ..

timeout /t 3 /nobreak >nul

echo [2/3] Opening frontend...
start frontend\index.html

echo [3/3] Done!
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause >nul
