"""
FARSverse Task Manager & Autonomous Scheduler
Multi-factor robot selection algorithm, priority queues, and decision traces.
"""
from __future__ import annotations
import math
import time
from typing import Any, Dict, List, Optional, Tuple


class FARSverseTask:
    _id_counter = 0

    def __init__(self,
                 task_type: str,
                 location_node: str,
                 priority: int = 2,
                 description: str = "",
                 origin: str = "manual",
                 human_id: Optional[str] = None):
        FARSverseTask._id_counter += 1
        self.id = FARSverseTask._id_counter
        self.task_type = task_type
        self.location_node = location_node
        self.priority = priority  # 1=Low, 2=Normal, 3=High, 4=Critical
        self.description = description or f"{task_type.replace('_', ' ').title()} at {location_node}"
        self.origin = origin
        self.human_id = human_id

        self.status = "pending"  # pending, assigned, in_progress, completed, failed
        self.assigned_robot: Optional[str] = None
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.selection_reason: str = ""
        self.failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'task_type': self.task_type,
            'location_node': self.location_node,
            'priority': self.priority,
            'description': self.description,
            'origin': self.origin,
            'human_id': self.human_id,
            'status': self.status,
            'assigned_robot': self.assigned_robot,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'selection_reason': self.selection_reason,
            'failure_reason': self.failure_reason
        }


class TaskManager:
    """Authoritative scheduler matching tasks to robots based on priority, distance, and battery."""

    def __init__(self):
        self.task_queue: List[FARSverseTask] = []
        self.active_tasks: List[FARSverseTask] = []
        self.completed_tasks: List[FARSverseTask] = []
        self.failed_tasks: List[FARSverseTask] = []
        self.total_response_time: float = 0.0

    def create_task(self,
                    task_type: str,
                    location_node: str,
                    priority: int = 2,
                    description: str = "",
                    origin: str = "manual",
                    human_id: Optional[str] = None) -> FARSverseTask:
        task = FARSverseTask(
            task_type=task_type,
            location_node=location_node,
            priority=priority,
            description=description,
            origin=origin,
            human_id=human_id
        )
        self.task_queue.append(task)
        return task

    def cancel_task(self, task_id: int) -> bool:
        for t in list(self.task_queue):
            if t.id == task_id:
                t.status = "failed"
                t.failure_reason = "Cancelled by user"
                self.task_queue.remove(t)
                self.failed_tasks.append(t)
                return True
        return False

    def schedule(self, robots: List[Any], world: Any, events_collector: List[Dict[str, Any]]) -> None:
        """Evaluate pending tasks against available robots using multi-factor optimization."""
        if not self.task_queue:
            return

        # Sort tasks by priority descending (Critical 4 first)
        self.task_queue.sort(key=lambda t: (t.priority, -t.created_at), reverse=True)

        for task in list(self.task_queue):
            if task.status != "pending":
                continue

            available_robots = [r for r in robots if r.is_available()]
            if not available_robots:
                task.selection_reason = "Pending: No robots currently available with sufficient battery."
                continue

            best_robot = None
            best_score = float('-inf')
            best_path = None
            best_explanation = ""

            for robot in available_robots:
                # Find path from robot to task location
                path_data = world.find_path((robot.x, robot.z), task.location_node)
                if not path_data.get('success'):
                    continue

                dist = path_data.get('distance', 10.0)
                # Multi-factor score
                # Higher priority = big boost
                # Shorter distance = positive
                # Higher battery = positive
                # Charging penalty = slight discouragement if actively charging
                charging_penalty = 15.0 if robot.state == "CHARGING" else 0.0
                score = (12.0 * task.priority) - (1.4 * dist) + (0.45 * robot.battery) - charging_penalty

                if score > best_score:
                    best_score = score
                    best_robot = robot
                    best_path = path_data
                    best_explanation = (
                        f"Assigned {robot.name} [{robot.id}]: score={score:.1f} "
                        f"(dist={dist:.1f}m, battery={robot.battery:.0f}%, P{task.priority})"
                    )

            if best_robot and best_path:
                task.status = "assigned"
                task.assigned_robot = best_robot.id
                task.selection_reason = best_explanation

                success = best_robot.assign_task(task.to_dict(), best_path, reason=best_explanation)
                if success:
                    self.task_queue.remove(task)
                    self.active_tasks.append(task)
                    events_collector.append({
                        'timestamp': time.time(),
                        'severity': 'INFO',
                        'category': 'task',
                        'message': f"Task #{task.id} ({task.description}) assigned to {best_robot.id}."
                    })
                else:
                    task.status = "pending"
                    task.selection_reason = f"Assignment to {best_robot.id} failed during path generation."

    def on_task_completed(self, completed_task_dict: Dict[str, Any], events_collector: List[Dict[str, Any]]) -> None:
        """Mark task as successfully executed."""
        task_id = completed_task_dict.get('id')
        for t in list(self.active_tasks):
            if t.id == task_id:
                t.status = "completed"
                t.completed_at = time.time()
                self.active_tasks.remove(t)
                self.completed_tasks.append(t)
                duration = t.completed_at - t.created_at
                self.total_response_time += duration
                events_collector.append({
                    'timestamp': time.time(),
                    'severity': 'INFO',
                    'category': 'task',
                    'message': f"Task #{t.id} completed at {t.location_node} in {duration:.1f}s."
                })
                break

    def get_metrics(self) -> Dict[str, Any]:
        completed_count = len(self.completed_tasks)
        avg_resp = round(self.total_response_time / completed_count, 1) if completed_count > 0 else 0.0
        return {
            'pending_tasks': len(self.task_queue),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': completed_count,
            'failed_tasks': len(self.failed_tasks),
            'avg_response_time_seconds': avg_resp,
        }

    def reset(self) -> None:
        self.task_queue.clear()
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.total_response_time = 0.0
