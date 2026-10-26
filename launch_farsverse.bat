@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse -- Interactive Robotics Simulation Platform
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Starting FARSverse Backend (FastAPI on Port 8080)...
start "FARSverse-Backend" /min cmd /c "python fars_platform/run.py --no-3d"

echo [2/3] Waiting for backend server to initialize...
timeout /t 3 /nobreak >nul

echo [3/3] Starting FARSverse Studio (Next.js on Port 3000)...
cd desktop\farsy-main
start "FARSverse-Studio" cmd /c "npm run dev"

echo.
echo Launching FARSverse Studio in your web browser: http://localhost:3000
timeout /t 4 /nobreak >nul
start http://localhost:3000

echo.
echo FARSverse is now running!
echo Keep the terminal windows open while using the simulation.
echo Press any key to exit this launcher window...
pause >nul
