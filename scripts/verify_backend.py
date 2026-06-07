#!/usr/bin/env python3
"""Verify all backend modules import and core flows work without runtime errors."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "full_simulation"))
sys.path.insert(0, str(ROOT / "FARS"))

errors: list[str] = []


def check(label: str, fn) -> None:
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as exc:
        errors.append(f"{label}: {exc}")
        print(f"  FAIL {label}: {exc}")


def main() -> int:
    print("FARS backend verification\n")

    def import_platform():
        from fars_platform.core.database import Database
        from fars_platform.core.event_bus import EventBus
        from fars_platform.services.face_service import FaceRecognitionService
        from fars_platform.services.access_control import AccessControlService
        from fars_platform.services.analytics import AnalyticsService
        from fars_platform.simulated_hardware.device_hub import DeviceHub
        from fars_platform.api.app import create_app
        from fars_platform.core.platform_state import PlatformState

        db = Database()
        bus = EventBus()
        face = FaceRecognitionService()
        db.sync_students_from_face_ids(face.list_registered_ids())
        access = AccessControlService(db, face, bus)
        analytics = AnalyticsService(db, bus)
        hub = DeviceHub(db, access, bus)
        app = create_app(db, analytics, access, hub, bus, PlatformState())
        assert app is not None
        r = hub.trigger_manual_scan("Entrance")
        assert "recognition" in r or "error" in r

    check("fars_platform stack", import_platform)

    def import_simulation():
        import navigation  # noqa: F401
        import task_manager  # noqa: F401
        import llm_command_parser  # noqa: F401
        result = llm_command_parser.parse_command("assist patient in room 5")
        assert result and result["location_node"] == "Room5"

    check("full_simulation modules", import_simulation)

    def import_legacy_helpers():
        import firebase_setup  # noqa: F401
        assert firebase_setup.get_credentials_path().exists()

    check("FARS firebase_setup", import_legacy_helpers)

    print()
    if errors:
        print(f"FAILED ({len(errors)} error(s))")
        for e in errors:
            print(" -", e)
        return 1
    print("All backend checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
