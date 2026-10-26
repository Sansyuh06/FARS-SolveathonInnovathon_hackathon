@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse -- NVIDIA Omniverse(TM) Isaac Sim 3D Studio
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Starting Ollama Local AI Engine (Port 11434)...
start "Ollama-Engine" /min cmd /c "ollama serve"

echo [2/3] Starting FARSverse Simulation Backend (Port 8080)...
start "FARSverse-Backend" /min cmd /c "python fars_platform/run.py --no-3d"

echo Waiting for backend engine...
timeout /t 3 /nobreak >nul

echo [3/3] Starting FARSverse 3D Studio (Port 3000)...
cd desktop\farsy-main
start "FARSverse-Studio" /min cmd /c "npm run dev"

echo.
echo Launching FARSverse 3D Studio in your browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ============================================================
echo   FARSverse 3D Simulation Platform is ACTIVE!
echo   - 3D Viewport: http://localhost:3000
echo   - Backend Engine: http://127.0.0.1:8080
echo   - Ollama AI (RTX 4060): http://127.0.0.1:11434
echo ============================================================
echo.
pause
