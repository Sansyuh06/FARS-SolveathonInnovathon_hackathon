"""Bridge between fars_platform and full_simulation 3D twin."""
from __future__ import annotations

import sys

from fars_platform.config import SIMULATION_DIR
from kernel.core.platform_state import PendingSimTask, PlatformState

# Ensure simulation package importable
if str(SIMULATION_DIR) not in sys.path:
    sys.path.insert(0, str(SIMULATION_DIR))


def parse_and_enqueue_command(text: str) -> bool:
    try:
        from llm_command_parser import parse_command
    except ImportError:
        return False

    result = parse_command(text)
    if not result:
        return False

    PlatformState().enqueue_task(
        PendingSimTask(
            task_type=result["task_type"],
            location_node=result["location_node"],
            priority=result["priority"],
            description=result["description"],
        )
    )
    return True


def drain_tasks_to_manager(task_mgr) -> int:
    """Called each frame from Ursina update — injects platform tasks."""
    state = PlatformState()
    tasks = state.drain_tasks()
    for t in tasks:
        task_mgr.create_task(
            task_type=t.task_type,
            location_node=t.location_node,
            priority=t.priority,
            description=t.description,
        )
        task_mgr.add_alert(f"[Platform] {t.description or t.task_type}")
    return len(tasks)


def sync_metrics(task_mgr, robots, patients_assisted: int) -> None:
    metrics = task_mgr.get_metrics()
    PlatformState().update_sim_metrics(
        {
            "robots_active": sum(1 for r in robots if r.state not in ("idle", "charging")),
            "robots_total": len(robots),
            "tasks_pending": metrics["pending"],
            "tasks_active": metrics["active"],
            "tasks_completed": metrics["completed"],
            "patients_assisted": patients_assisted,
            "avg_response_sec": metrics["avg_response_time"],
        }
    )
