"""SQLite persistence — replaces Firebase for fully local production simulation."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fars_platform.config import DB_PATH, IMAGES_DIR


class Database:
    _lock = threading.RLock()

    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self._conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self.seed_if_empty()

    def _init_schema(self) -> None:
        with self._lock:
            c = self._conn.cursor()
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT,
                    starting_year INTEGER,
                    year INTEGER,
                    total_attendance INTEGER DEFAULT 0,
                    standing_rank INTEGER DEFAULT 0,
                    last_logged_time TEXT,
                    photo_path TEXT,
                    access_level TEXT DEFAULT 'student',
                    active INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS attendance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    event_type TEXT,
                    location TEXT,
                    recorded_at TEXT,
                    metadata TEXT
                );
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    granted INTEGER,
                    location TEXT,
                    reason TEXT,
                    recorded_at TEXT
                );
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    message TEXT,
                    payload TEXT,
                    recorded_at TEXT
                );
                CREATE TABLE IF NOT EXISTS iot_devices (
                    id TEXT PRIMARY KEY,
                    device_type TEXT,
                    location TEXT,
                    status TEXT,
                    last_seen TEXT,
                    metadata TEXT
                );
                CREATE TABLE IF NOT EXISTS analytics_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value REAL,
                    recorded_at TEXT
                );
                """
            )
            self._conn.commit()

    def seed_if_empty(self) -> None:
        with self._lock:
            count = self._conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            if count > 0:
                self._ensure_iot_devices()
                return

        self._seed_students_from_images()
        self._ensure_iot_devices()
        self.log_event("system", "Database seeded with campus roster and IoT devices")

    def _seed_students_from_images(self) -> None:
        if not IMAGES_DIR.exists():
            return
        for img in sorted(IMAGES_DIR.iterdir()):
            if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            self._insert_default_student(img.stem, str(img))

    def sync_students_from_face_ids(self, student_ids: List[str]) -> int:
        """Ensure every encoded face ID exists in the database."""
        added = 0
        for sid in student_ids:
            if not sid or self.get_student(sid):
                continue
            photo = IMAGES_DIR / f"{sid}.jpg"
            if not photo.exists():
                for ext in (".png", ".jpeg", ".JPG", ".PNG"):
                    alt = IMAGES_DIR / f"{sid}{ext}"
                    if alt.exists():
                        photo = alt
                        break
            self._insert_default_student(sid, str(photo) if photo.exists() else "")
            added += 1
        return added

    def _insert_default_student(self, sid: str, photo_path: str) -> None:
        name = sid.replace("SIT", "Student ").replace("SC", "-")
        self.upsert_student(
            {
                "id": sid,
                "name": name,
                "department": "CSE",
                "starting_year": 2023,
                "year": 2,
                "total_attendance": 0,
                "standing_rank": 1,
                "last_logged_time": "1970-01-01 00:00:00",
                "photo_path": photo_path,
                "access_level": "student",
            }
        )

    def _ensure_iot_devices(self) -> None:
        # Default IoT devices (simulated ESP32, IR, camera)
        devices = [
            ("esp32-gateway-1", "esp32", "Entrance", "online"),
            ("ir-sensor-entrance", "ir", "Entrance", "online"),
            ("cam-module-entrance", "camera", "Entrance", "online"),
            ("ir-sensor-main", "ir", "MainHall", "online"),
            ("cam-module-main", "camera", "MainHall", "online"),
            ("ble-beacon-1", "bluetooth", "Reception", "online"),
            ("wifi-ap-campus", "wifi", "Campus", "online"),
        ]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            for did, dtype, loc, status in devices:
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO iot_devices (id, device_type, location, status, last_seen, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (did, dtype, loc, status, now, "{}"),
                )
            self._conn.commit()

    def upsert_student(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO students (id, name, department, starting_year, year,
                    total_attendance, standing_rank, last_logged_time, photo_path, access_level)
                VALUES (:id, :name, :department, :starting_year, :year,
                    :total_attendance, :standing_rank, :last_logged_time, :photo_path, :access_level)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, department=excluded.department,
                    total_attendance=excluded.total_attendance,
                    last_logged_time=excluded.last_logged_time,
                    photo_path=excluded.photo_path
                """,
                data,
            )
            self._conn.commit()

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_students(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM students WHERE active = 1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def record_attendance(self, student_id: str, location: str = "Entrance") -> bool:
        """Returns True if attendance was incremented (cooldown passed)."""
        student = self.get_student(student_id)
        if not student:
            return False

        now = datetime.now()
        last_raw = student.get("last_logged_time") or "1970-01-01 00:00:00"
        try:
            last = datetime.strptime(last_raw, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            last = datetime(1970, 1, 1)
        if (now - last).total_seconds() < 30:
            return False

        new_count = student["total_attendance"] + 1
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                "UPDATE students SET total_attendance = ?, last_logged_time = ? WHERE id = ?",
                (new_count, ts, student_id),
            )
            self._conn.execute(
                """
                INSERT INTO attendance_log (student_id, event_type, location, recorded_at, metadata)
                VALUES (?, 'check_in', ?, ?, ?)
                """,
                (student_id, location, ts, json.dumps({"count": new_count})),
            )
            self._conn.commit()
        return True

    def record_access(
        self, student_id: Optional[str], granted: bool, location: str, reason: str
    ) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO access_log (student_id, granted, location, reason, recorded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, 1 if granted else 0, location, reason, ts),
            )
            self._conn.commit()

    def log_event(self, category: str, message: str, payload: Optional[dict] = None) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO system_events (category, message, payload, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (category, message, json.dumps(payload or {}), ts),
            )
            self._conn.commit()

    def update_device(self, device_id: str, status: str, metadata: Optional[dict] = None) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                """
                UPDATE iot_devices SET status = ?, last_seen = ?, metadata = ?
                WHERE id = ?
                """,
                (status, ts, json.dumps(metadata or {}), device_id),
            )
            self._conn.commit()

    def list_devices(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM iot_devices ORDER BY location").fetchall()
        return [dict(r) for r in rows]

    def recent_attendance(self, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT a.*, s.name FROM attendance_log a
            LEFT JOIN students s ON s.id = a.student_id
            ORDER BY a.id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def recent_access(self, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM access_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def recent_events(self, limit: int = 30) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM system_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def analytics_summary(self) -> Dict[str, Any]:
        students = self._conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        attendance_today = self._conn.execute(
            """
            SELECT COUNT(*) FROM attendance_log
            WHERE date(recorded_at) = date('now', 'localtime')
            """
        ).fetchone()[0]
        access_granted = self._conn.execute(
            "SELECT COUNT(*) FROM access_log WHERE granted = 1"
        ).fetchone()[0]
        access_denied = self._conn.execute(
            "SELECT COUNT(*) FROM access_log WHERE granted = 0"
        ).fetchone()[0]
        devices_online = self._conn.execute(
            "SELECT COUNT(*) FROM iot_devices WHERE status IN ('online', 'triggered', 'capturing')"
        ).fetchone()[0]
        return {
            "registered_users": students,
            "attendance_today": attendance_today,
            "access_granted": access_granted,
            "access_denied": access_denied,
            "devices_online": devices_online,
        }

    def record_metric(self, name: str, value: float) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._conn.execute(
                "INSERT INTO analytics_snapshots (metric_name, metric_value, recorded_at) VALUES (?,?,?)",
                (name, value, ts),
            )
            self._conn.commit()
