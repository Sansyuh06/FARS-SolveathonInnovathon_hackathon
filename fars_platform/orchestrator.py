"""Orchestrates API server, IoT simulation, and 3D digital twin."""
from __future__ import annotations

import os
import socket
import sys
import threading
import traceback

import uvicorn

from kernel.api.app import create_app
from fars_platform.config import API_HOST, API_PORT, SIMULATION_DIR
from kernel.core.database import Database
from kernel.core.event_bus import EventBus
from kernel.core.platform_state import PlatformState
from fars_platform.services.access_control import AccessControlService
from fars_platform.services.analytics import AnalyticsService
from fars_platform.services.face_service import FaceRecognitionService
from virtual_devices.simulated_hardware.device_hub import DeviceHub
from fars_platform.util.network import find_free_port, wait_for_server

# Set by orchestrator so other modules can read the bound port
ACTIVE_API_PORT: int = API_PORT


def _start_api(app, host: str, port: int) -> threading.Thread:
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)

    def run() -> None:
        server.run()

    t = threading.Thread(target=run, daemon=True, name="FARS-API")
    t.start()
    return t


def run_platform(with_3d: bool = True) -> None:
    global ACTIVE_API_PORT

    def _log(msg: str) -> None:
        print(msg, flush=True)

    _log("=" * 60)
    _log("  FARS - Fully Automated Robotic Systems")
    _log("  Production Simulation (all software, no hardware)")
    _log("=" * 60)

    # Resolve API port (env override, else 8080, else next free)
    port = int(os.environ.get("FARS_PORT", API_PORT))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((API_HOST, port))
    except OSError:
        old = port
        port = find_free_port(API_HOST, 8080, 8099)
        _log(f"  Note: port {old} is busy - using {port} instead.")

    ACTIVE_API_PORT = port
    os.environ["FARS_PORT"] = str(port)

    db = Database()
    bus = EventBus()
    face = FaceRecognitionService()
    added = db.sync_students_from_face_ids(face.list_registered_ids())
    if added:
        _log(f"  Synced {added} student(s) from face encodings into database.")
    access = AccessControlService(db, face, bus)
    analytics = AnalyticsService(db, bus)
    devices = DeviceHub(db, access, bus)
    state = PlatformState()

    app = create_app(db, analytics, access, devices, bus, state)
    devices.start()

    _log("  Starting API server...")
    _start_api(app, API_HOST, port)

    if not wait_for_server(API_HOST, port, timeout=20):
        _log("  ERROR: API server did not start. Check errors above.")
        devices.stop()
        sys.exit(1)

    state.running = True
    db.log_event("system", f"FARS platform started on port {port}")

    _log("")
    _log(f"  Admin dashboard: http://{API_HOST}:{port}/")
    _log(f"  API docs:        http://{API_HOST}:{port}/docs")

    if with_3d:
        _log("  3D simulation starting...")
        _log("  (Close the 3D window or press Ctrl+C here to stop.)\n")
        if str(SIMULATION_DIR) not in sys.path:
            sys.path.insert(0, str(SIMULATION_DIR))
        try:
            from main_simulation import run_integrated_simulation

            run_integrated_simulation()
        except Exception:
            _log("\n  ERROR: 3D simulation failed to start:")
            traceback.print_exc()
            _log("\n  Tip: run without 3D:  python fars_platform/run.py --no-3d")
            _log(f"  Dashboard is still available at http://{API_HOST}:{port}/\n")
            _run_headless(devices)
    else:
        _log("  Running headless (API + IoT). Press Ctrl+C to stop.\n")
        _run_headless(devices)


def _run_headless(devices: DeviceHub) -> None:
    import time

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Shutting down...", flush=True)
    finally:
        devices.stop()


if __name__ == "__main__":
    run_platform(with_3d="--no-3d" not in sys.argv)
