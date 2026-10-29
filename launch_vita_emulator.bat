@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   FARSverse Pocket -- NVIDIA Omniverse USD Composer (Vita3K)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] Installing latest FARSverse_Pocket.vpk into Vita3K...
"vita_port\vita3k\Vita3K.exe" -z "FARSverse_Pocket.vpk"

echo [2/2] Launching FARSverse Pocket (FARS00001) in Vita3K...
start "" "vita_port\vita3k\Vita3K.exe" -r FARS00001

echo.
echo ============================================================
echo   FARSverse Pocket is RUNNING!
echo   - UI Theme: NVIDIA Omniverse USD Composer 2023.2.5
echo   - 3D Viewport: True 3D Perspective CAD Renderer (60 FPS)
echo   - Controls:
echo       * L1 / R1         : Cycle USD Prims (AMRs, Machinery, Racks)
echo       * Right Stick     : Orbit 3D Camera (Yaw / Pitch)
echo       * Left Stick      : Pan 3D Camera Target (X / Z)
echo       * D-Pad Up / Down : Select Mission
echo       * Cross (X)       : Assign / Dispatch Mission
echo       * Circle (O)      : Return to Charging Dock
echo       * Square          : Emergency Stop (E-Stop)
echo       * Start           : Manual Host Link Sync
echo       * Select          : Reset Camera to Default Isometric View
echo ============================================================
echo.
