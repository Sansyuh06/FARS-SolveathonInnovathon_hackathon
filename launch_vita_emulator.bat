@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse Pocket -- PS Vita Emulator Testbench (Vita3K)
echo ============================================================
echo.

cd /d "%~dp0"

echo Launching FARSverse Pocket (FARS00001) in Vita3K...
start "" "vita_port\vita3k\Vita3K.exe" -r FARS00001

echo.
echo ============================================================
echo   FARSverse Pocket is RUNNING!
echo   - Native Resolution: 960x544
echo   - Controls:
echo       * L1 / R1         : Cycle AMR Robots (1 to 5)
echo       * D-Pad Up / Down : Navigate Mission Roster
echo       * Cross (X)       : Assign Selected Mission
echo       * Circle (O)      : Dock AMR at Charging Bay
echo       * Square          : Emergency Stop (E-Stop)
echo       * Triangle        : Ping / Sync Host Network
echo       * Left Analog     : Pan Hospital Digital Twin Map
echo ============================================================
echo.
