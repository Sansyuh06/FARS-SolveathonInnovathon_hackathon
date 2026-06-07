"""Shared runtime state between API, hardware sim, and 3D simulation."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PendingSimTask:
    task_type: str
    location_node: str
    priority: int = 2
    description: str = ""


class PlatformState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.pending_tasks: List[PendingSimTask] = []
                cls._instance.task_lock = threading.Lock()
                cls._instance.running = False
                cls._instance.last_face_match: Optional[Dict[str, Any]] = None
                cls._instance.sim_metrics: Dict[str, Any] = {}
                cls._instance.voice_commands: List[str] = []
            return cls._instance

    def enqueue_task(self, task: PendingSimTask) -> None:
        with self.task_lock:
            self.pending_tasks.append(task)

    def drain_tasks(self) -> List[PendingSimTask]:
        with self.task_lock:
            tasks = list(self.pending_tasks)
            self.pending_tasks.clear()
            return tasks

    def set_face_match(self, info: Optional[Dict[str, Any]]) -> None:
        self.last_face_match = info

    def update_sim_metrics(self, metrics: Dict[str, Any]) -> None:
        self.sim_metrics = metrics

    def add_voice_command(self, text: str) -> None:
        self.voice_commands.append(text)
        if len(self.voice_commands) > 50:
            self.voice_commands = self.voice_commands[-50:]
