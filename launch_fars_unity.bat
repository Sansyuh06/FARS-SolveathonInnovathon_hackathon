@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARS Hospital Digital Twin -- Unity 6 Simulation Engine
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] Ensuring Ollama AI Engine is active (Port 11434)...
start "Ollama-Engine" /min cmd /c "ollama serve"

echo [2/2] Launching FARS Unity Native Engine...
cd /d "%~dp0unity_build"
start "" "FARS_Unity.exe"

echo.
echo ============================================================
echo   FARS Unity Simulation is RUNNING!
echo   - Controls:
echo       * Mouse Left Click : Select robot / Inspect
echo       * Scroll Wheel     : Zoom in / out
echo       * Middle Drag      : Orbit camera
echo       * 1 - 5 Keys       : Focus robot 1 to 5
echo       * TAB Key          : Open AI Command prompt
echo       * Home Key         : Reset camera overview
echo ============================================================
echo.
