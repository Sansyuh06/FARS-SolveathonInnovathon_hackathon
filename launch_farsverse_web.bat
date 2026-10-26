@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse -- Web Edition (Next.js + Three.js)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Starting FARSverse Backend (FastAPI on Port 8080)...
start "FARSverse-Backend" /min cmd /c "python fars_platform/run.py --no-3d"

timeout /t 3 /nobreak >nul

echo [2/3] Starting FARSverse Studio Web (Port 3000)...
cd desktop\farsy-main
start "FARSverse-Studio" cmd /c "npm run dev"

echo.
echo Launching FARSverse Studio Web: http://localhost:3000
timeout /t 4 /nobreak >nul
start http://localhost:3000
