#!/usr/bin/env bash
# FARS - start full simulation (Git Bash / WSL / Linux / macOS)
# Do NOT use ./start.sh from PowerShell — use start.ps1 or start.bat instead.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "=============================================="
echo "  FARS - Fully Automated Robotic Systems"
echo "=============================================="
echo ""

if command -v python3 &>/dev/null; then
  PY=python3
elif command -v python &>/dev/null; then
  PY=python
else
  echo "ERROR: Python not found."
  exit 1
fi

echo "Using: $($PY --version)"
echo "Project: $ROOT"
echo ""

if ! "$PY" -c "import fastapi, ursina" 2>/dev/null; then
  echo "Installing dependencies..."
  "$PY" -m pip install -r "$ROOT/requirements.txt"
fi

echo "Starting FARS (Ctrl+C to stop)..."
echo ""

exec "$PY" "$ROOT/fars_platform/run.py" "$@"
