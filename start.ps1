# FARS - start full simulation (use this in PowerShell)
# Usage:  .\start.ps1
#         .\start.ps1 -No3d

param(
    [switch]$No3d
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=============================================="
Write-Host "  FARS - Fully Automated Robotic Systems"
Write-Host "=============================================="
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Install Python 3.10+ and add to PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python: $(python --version)"
Write-Host "Folder: $PSScriptRoot"
Write-Host ""

$depsOk = $true
python -c "import fastapi, ursina" 2>$null
if ($LASTEXITCODE -ne 0) { $depsOk = $false }

if (-not $depsOk) {
    Write-Host "Installing dependencies..."
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: pip install failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
}

$args = @()
if ($No3d) { $args += "--no-3d" }

Write-Host "Starting FARS..."
Write-Host "(Use Ctrl+C to stop)"
Write-Host ""

python "$PSScriptRoot\fars_platform\run.py" @args
$code = $LASTEXITCODE

if ($code -ne 0) {
    Write-Host ""
    Write-Host "FARS exited with error code $code" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
exit $code
