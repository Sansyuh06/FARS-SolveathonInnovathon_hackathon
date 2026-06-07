"""Real-time analytics aggregator."""
from __future__ import annotations

from typing import Any, Dict

from fars_platform.core.database import Database
from fars_platform.core.event_bus import EventBus
from fars_platform.core.platform_state import PlatformState


class AnalyticsService:
    def __init__(self, db: Database, bus: EventBus):
        self.db = db
        self.bus = bus
        self.state = PlatformState()
        bus.subscribe("*", self._on_event)

    def _on_event(self, event) -> None:
        self.db.record_metric(f"event_{event.type}", 1.0)

    def dashboard_payload(self) -> Dict[str, Any]:
        summary = self.db.analytics_summary()
        summary["simulation"] = dict(self.state.sim_metrics)
        summary["last_face_match"] = self.state.last_face_match
        summary["recent_events"] = self.db.recent_events(15)
        return summary
