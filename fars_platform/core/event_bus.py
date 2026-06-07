"""Thread-safe pub/sub event bus for all FARS subsystems."""
from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


@dataclass
class Event:
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._subs = defaultdict(list)
                cls._instance._history: List[Event] = []
                cls._instance._hist_lock = threading.Lock()
            return cls._instance

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to a specific event type, or '*' for all events."""
        self._subs[event_type].append(handler)

    def publish(self, event_type: str, **payload: Any) -> Event:
        event = Event(type=event_type, payload=payload)
        with self._hist_lock:
            self._history.append(event)
            if len(self._history) > 500:
                self._history = self._history[-500:]

        for handler in list(self._subs.get(event_type, [])):
            try:
                handler(event)
            except Exception as exc:
                print(f"[EventBus] handler error ({event_type}): {exc}")
        for handler in list(self._subs.get("*", [])):
            try:
                handler(event)
            except Exception as exc:
                print(f"[EventBus] wildcard handler error: {exc}")
        return event

    def recent(self, limit: int = 50) -> List[Event]:
        with self._hist_lock:
            return list(self._history[-limit:])
