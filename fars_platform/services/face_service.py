"""Face recognition service — uses EncodeFile.p when available, filename fallback otherwise."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from fars_platform.config import ENCODE_FILE, IMAGES_DIR


class FaceRecognitionService:
    def __init__(self):
        self.known_encodings: List[np.ndarray] = []
        self.student_ids: List[str] = []
        self._use_dlib = False
        self._load_encodings()

    def _load_encodings(self) -> None:
        if ENCODE_FILE.exists():
            try:
                with open(ENCODE_FILE, "rb") as f:
                    data = pickle.load(f)
                self.known_encodings, self.student_ids = data[0], data[1]
                self._use_dlib = True
                print(f"[FaceService] Loaded {len(self.student_ids)} encodings from EncodeFile.p")
                return
            except Exception as exc:
                print(f"[FaceService] EncodeFile load failed: {exc}")

        # Build roster from image filenames (simulation mode)
        if IMAGES_DIR.exists():
            for img in sorted(IMAGES_DIR.iterdir()):
                if img.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    self.student_ids.append(img.stem)
                    self.known_encodings.append(np.zeros(128))  # placeholder
        print(f"[FaceService] Simulation mode: {len(self.student_ids)} faces from Images/")

    def identify_from_image_path(self, image_path: Path) -> Dict[str, Any]:
        """Identify person from image file (simulated camera frame)."""
        stem = image_path.stem

        if self._use_dlib and len(self.known_encodings) > 0:
            try:
                import cv2
                import face_recognition

                img = cv2.imread(str(image_path))
                if img is None:
                    return self._unknown("Could not read image")
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb)
                encs = face_recognition.face_encodings(rgb, locs)
                if not encs:
                    return self._unknown("No face detected")
                enc = encs[0]
                distances = face_recognition.face_distance(self.known_encodings, enc)
                best = int(np.argmin(distances))
                if distances[best] < 0.55:
                    return {
                        "recognized": True,
                        "student_id": self.student_ids[best],
                        "confidence": float(1.0 - distances[best]),
                        "method": "face_recognition",
                    }
                return self._unknown(f"Low confidence ({distances[best]:.2f})")
            except ImportError:
                self._use_dlib = False
            except Exception as exc:
                return self._unknown(str(exc))

        # Simulation: match by filename if in roster
        if stem in self.student_ids:
            return {
                "recognized": True,
                "student_id": stem,
                "confidence": 0.92,
                "method": "simulated_camera",
            }
        return self._unknown(f"Unknown face ({stem})")

    def _unknown(self, reason: str) -> Dict[str, Any]:
        return {
            "recognized": False,
            "student_id": None,
            "confidence": 0.0,
            "method": "none",
            "reason": reason,
        }

    def list_registered_ids(self) -> List[str]:
        return list(self.student_ids)
