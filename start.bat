@echo off
REM FARS - start full simulation (Windows)
REM Double-click this file, or run from CMD: start.bat

cd /d "%~dp0"

echo ==============================================
echo   FARS - Fully Automated Robotic Systems
echo ==============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
  pause
  exit /b 1
)

python --version
echo.

python -c "import fastapi, ursina" 2>nul
if errorlevel 1 (
  echo Installing dependencies from requirements.txt ...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
  )
  echo.
)

echo Starting FARS...
echo   In PowerShell use instead:  .\start.ps1
echo   Press Ctrl+C to stop.
echo.

python "%~dp0fars_platform\run.py" %*
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% neq 0 (
  echo.
  echo FARS exited with error. Try:  start.bat --no-3d
  pause
)
exit /b %EXITCODE%
