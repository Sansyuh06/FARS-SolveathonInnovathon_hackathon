@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse -- NVIDIA Omniverse(TM) Isaac Sim (PyQt6 Native Studio)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Ollama AI Engine (Port 11434)...
start "Ollama-Engine" /min cmd /c "ollama serve"

echo [2/3] Starting FARSverse Authoritative Simulation Backend (Port 8080)...
start "FARSverse-Backend" /min cmd /c "python fars_platform/run.py --no-3d"

echo Waiting for simulation engine to initialize...
timeout /t 3 /nobreak >nul

echo [3/3] Launching FARSverse Native Desktop Studio (PyQt6 with PyTorch CUDA)...
python -m desktop.fars_omniverse_pyqt

echo.
echo FARSverse Desktop closed.
pause
