"""Simulated ESP32, IR sensors, camera modules, Wi-Fi and Bluetooth."""
from __future__ import annotations

import random
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from fars_platform.config import IMAGES_DIR, IR_SCAN_INTERVAL
from kernel.core.database import Database
from kernel.core.event_bus import EventBus
from fars_platform.services.access_control import AccessControlService

# Map campus zones to IoT device IDs in the database
LOCATION_IR_DEVICE: Dict[str, str] = {
    "Entrance": "ir-sensor-entrance",
    "MainHall": "ir-sensor-main",
    "Reception": "ir-sensor-entrance",
}
LOCATION_CAM_DEVICE: Dict[str, str] = {
    "Entrance": "cam-module-entrance",
    "MainHall": "cam-module-main",
    "Reception": "cam-module-entrance",
}


class DeviceHub:
    """Runs background loops that emulate physical IoT triggers."""

    def __init__(self, db: Database, access: AccessControlService, bus: EventBus):
        self.db = db
        self.access = access
        self.bus = bus
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._image_cycle: List[Path] = []
        self._cycle_index = 0
        self._load_images()

    def _load_images(self) -> None:
        if IMAGES_DIR.exists():
            self._image_cycle = sorted(
                p for p in IMAGES_DIR.iterdir()
                if p.suffix.lower() in (".jpg", ".jpeg", ".png")
            )
        if not self._image_cycle:
            print("[DeviceHub] No images in FARS/Images - camera sim will idle")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="FARS-IoT")
        self._thread.start()
        print("[DeviceHub] Simulated hardware started (ESP32 / IR / Camera / Wi-Fi)")

    def stop(self) -> None:
        self._stop.set()

    def _device_for_location(self, mapping: Dict[str, str], location: str) -> str:
        return mapping.get(location, mapping["Entrance"])

    def _run_loop(self) -> None:
        locations = ["Entrance", "MainHall", "Reception"]
        loc_idx = 0
        while not self._stop.is_set():
            location = locations[loc_idx % len(locations)]
            loc_idx += 1

            ir_id = self._device_for_location(LOCATION_IR_DEVICE, location)
            cam_id = self._device_for_location(LOCATION_CAM_DEVICE, location)

            self.bus.publish("ir_motion", location=location, device=ir_id)
            self.db.update_device(ir_id, "triggered", {"motion": True})

            if self._image_cycle:
                img = self._image_cycle[self._cycle_index % len(self._image_cycle)]
                self._cycle_index += 1

                self.bus.publish("camera_capture", path=str(img), location=location)
                self.db.update_device(cam_id, "capturing", {"frame": img.name})

                result = self.access.process_camera_frame(str(img), location)
                student = result.get("student") or {}
                self.bus.publish(
                    "face_scan_complete",
                    location=location,
                    granted=result.get("granted"),
                    student_id=student.get("id"),
                )
                self.db.update_device(cam_id, "online", {"last_frame": img.name})

            self.db.update_device("wifi-ap-campus", "online", {"clients": random.randint(12, 48)})
            self.db.update_device("ble-beacon-1", "online", {"rssi": random.randint(-70, -40)})
            self.db.update_device(
                "esp32-gateway-1", "online", {"uptime_sec": int(time.time()) % 100000}
            )

            time.sleep(IR_SCAN_INTERVAL)

    def trigger_manual_scan(self, location: str = "Entrance") -> dict:
        """API-triggered single scan."""
        if not self._image_cycle:
            return {"error": "no_images", "granted": False, "student": None}
        img = random.choice(self._image_cycle)
        return self.access.process_camera_frame(str(img), location)
