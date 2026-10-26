#!/usr/bin/env bash
# FARSverse - Interactive Robotics Simulation Platform Launcher

echo "============================================================"
echo "  FARSverse -- Interactive Robotics Simulation Platform"
echo "============================================================"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[1/3] Starting FARSverse Backend (FastAPI on Port 8080)..."
python3 fars_platform/run.py --no-3d &
BACKEND_PID=$!

echo "[2/3] Waiting for backend server to initialize..."
sleep 3

echo "[3/3] Starting FARSverse Studio (Next.js on Port 3000)..."
cd desktop/farsy-main
npm run dev &
FRONTEND_PID=$!

echo ""
echo "FARSverse is running at http://localhost:3000"
echo "API & WebSocket Server at http://127.0.0.1:8080"
echo "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT SIGTERM
wait
