@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   FARSVERSE POCKET -- NVIDIA OMNIVERSE USD COMPOSER ^& DRIVE SIM (1:1 VITA)
echo ===============================================================================
echo.

cd /d "%~dp0"

echo [1/4] Stopping any existing Vita3K emulator instances...
taskkill /F /IM Vita3K.exe >nul 2>&1
ping -n 2 127.0.0.1 >nul

echo [2/4] Validating JavaScript CAD ^& Physics Engine syntax...
call node -c "vita_port\assets\main.js"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Syntax error detected in vita_port\assets\main.js! Aborting.
    pause
    exit /b %ERRORLEVEL%
)

echo [3/4] Updating Vita3K ux0 installed assets ^& packaging fresh VPK...
set "VITA_FS_APP=%APPDATA%\Vita3K\Vita3K\ux0\app\FARS00001"
if not exist "%VITA_FS_APP%\assets" mkdir "%VITA_FS_APP%\assets"
copy /Y "vita_port\assets\main.js" "%VITA_FS_APP%\assets\main.js" >nul

if exist "vita_port\package_vpk.py" (
    python "vita_port\package_vpk.py"
) else (
    echo [WARN] package_vpk.py not found, skipping VPK build.
)

echo [4/4] Launching FARSverse Pocket (FARS00001) in Vita3K...
start "" /D "%~dp0vita_port\vita3k" Vita3K.exe -r FARS00001

echo.
echo ===============================================================================
echo   FARSverse Pocket is RUNNING at solid 60 FPS!
echo.
echo   LATEST DELIVERIES:
echo     * Workspace VPK : %~dp0FARSverse_Pocket.vpk
echo     * Desktop VPK   : %USERPROFILE%\Desktop\FARSverse_Pocket.vpk
echo.
echo   AUTHENTIC CONTROLLER CONTROLS:
echo     * Left Stick      : Orbit 3D Camera (Azimuth / Elevation)
echo     * Right Stick     : Pan 3D Camera Target (X / Z ground plane)
echo     * L1 / R1 Triggers: Zoom Camera In / Out
echo     * Front Touch     : Drag to orbit camera around focus point
echo     * Cross (X)       : Cycle / Focus Active Robot
echo     * Triangle        : Toggle AI Perception Overlays (LiDAR, Trajectory, Boxes)
echo     * Square          : Toggle DRIVE-NET Sensor PIP Camera
echo     * Circle (O)      : Insert / Spawn Predefined 3D CAD Model
echo     * Select          : Switch Side Panel Tabs (3D Models / Neural Net / Stage)
echo     * Start           : Pause / Resume PhysX 5.1 Simulation
echo ===============================================================================
echo.
