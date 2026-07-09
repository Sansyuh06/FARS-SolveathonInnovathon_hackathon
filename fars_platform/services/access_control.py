"""Access control — ties face recognition to attendance, logging, and robot tasks."""
from __future__ import annotations

from typing import Any, Dict

from fars_platform.config import ATTENDANCE_LOG, UNKNOWN_FACE_DENY
from kernel.core.database import Database
from kernel.core.event_bus import EventBus
from kernel.core.platform_state import PendingSimTask, PlatformState
from fars_platform.services.face_service import FaceRecognitionService

_VALID_NODES = frozenset({
    "Entrance", "Reception", "MainHall", "Pharmacy", "EmergencyRoom",
    "WaitingHall", "ChargingDock", "HallNorth", "WestCorr1", "EastCorr1",
})


class AccessControlService:
    def __init__(self, db: Database, face: FaceRecognitionService, bus: EventBus):
        self.db = db
        self.face = face
        self.bus = bus
        self.state = PlatformState()

    def process_camera_frame(self, image_path: str, location: str = "Entrance") -> Dict[str, Any]:
        from pathlib import Path

        result = self.face.identify_from_image_path(Path(image_path))
        self.state.set_face_match(result)

        if result["recognized"]:
            return self._handle_recognized(result, location)

        return self._handle_unknown(result, location)

    def _handle_recognized(self, result: Dict[str, Any], location: str) -> Dict[str, Any]:
        sid = result["student_id"]
        student = self.db.get_student(sid)
        if student is None:
            self.db.sync_students_from_face_ids([sid])
            student = self.db.get_student(sid)

        granted = student is not None and student.get("active", 1) == 1
        reason = "recognized_face" if granted else "inactive_account"
        logged = False

        if granted and student is not None:
            logged = self.db.record_attendance(sid, location)
            if logged:
                student = self.db.get_student(sid) or student
                self._append_attendance_file(student, location)
                self.bus.publish(
                    "attendance_logged",
                    student_id=sid,
                    name=student["name"],
                    location=location,
                )
                self.db.log_event("attendance", f"{student['name']} checked in at {location}")
            else:
                reason = "cooldown_active"

        self.db.record_access(sid, granted, location, reason)
        self.bus.publish(
            "access_granted" if granted else "access_denied",
            student_id=sid,
            location=location,
            reason=reason,
        )
        return {
            "granted": granted,
            "student": student,
            "attendance_logged": logged,
            "recognition": result,
        }

    def _handle_unknown(self, result: Dict[str, Any], location: str) -> Dict[str, Any]:
        self.db.record_access(None, False, location, result.get("reason", "unknown"))
        self.bus.publish(
            "access_denied",
            student_id=None,
            location=location,
            reason="unknown_face",
        )
        self.db.log_event("security", f"Unknown face at {location}")

        if UNKNOWN_FACE_DENY:
            node = location if location in _VALID_NODES else "Entrance"
            self.state.enqueue_task(
                PendingSimTask(
                    task_type="check_room",
                    location_node=node,
                    priority=3,
                    description=f"Security: verify unknown person at {location}",
                )
            )
        return {
            "granted": False,
            "student": None,
            "attendance_logged": False,
            "recognition": result,
        }

    def _append_attendance_file(self, student: dict, location: str) -> None:
        from datetime import datetime

        count = student.get("total_attendance", 0)
        line = (
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, "
            f"Student ID: {student['id']}, Name: {student['name']}, "
            f"Department: {student.get('department', '')}, Location: {location}, "
            f"Total Attendance: {count}\n"
        )
        ATTENDANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ATTENDANCE_LOG, "a", encoding="utf-8") as f:
            f.write(line)
