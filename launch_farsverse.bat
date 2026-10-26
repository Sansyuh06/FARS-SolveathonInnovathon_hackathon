@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse -- Autonomous Robotics Simulation Platform
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Starting Ollama Local AI Engine (Port 11434)...
start "Ollama-Engine" /min cmd /c "ollama serve"

echo [2/3] Starting FARSverse Simulation Backend (Port 8080)...
start "FARSverse-Backend" /min cmd /c "python fars_platform/run.py --no-3d"

echo Waiting for backend engine to initialize...
timeout /t 3 /nobreak >nul

echo [3/3] Starting FARSverse Studio (Port 3000)...
cd desktop\farsy-main
start "FARSverse-Studio" /min cmd /c "npm run dev"

echo.
echo Launching FARSverse Studio in your browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ============================================================
echo   FARSverse Simulation Platform is ACTIVE!
echo   - 3D Robotics Studio: http://localhost:3000
echo   - Simulation Engine:  http://127.0.0.1:8080
echo   - Ollama AI Engine:   http://127.0.0.1:11434
echo ============================================================
echo.
pause
