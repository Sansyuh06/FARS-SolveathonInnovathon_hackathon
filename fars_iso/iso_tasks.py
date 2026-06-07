"""
task_manager.py -- Central Task Management & Priority Scheduling
Manages the task queue, auto-generates tasks from patient requests, and assigns robots.
"""

import time as _time
import math
from iso_navigation import get_node_position


class Task:
    _id_counter = 0

    def __init__(self, task_type, location_node, priority=1, description=''):
        Task._id_counter += 1
        self.id = Task._id_counter
        self.task_type = task_type
        self.location_node = location_node
        self.priority = priority           # 1=low, 2=medium, 3=high, 4=urgent
        self.description = description
        self.status = 'pending'            # pending, assigned, in_progress, completed
        self.assigned_robot = None
        self.created_time = _time.time()
        self.completed_time = None

    def __str__(self):
        return f'[{self.task_type}] -> {self.location_node} (P{self.priority})'

    def __repr__(self):
        return self.__str__()


TASK_TYPE_LABELS = {
    'guide_patient':    'Guide Patient',
    'assist_patient':   'Assist Patient',
    'deliver_medicine': 'Deliver Medicine',
    'escort_visitor':   'Escort Visitor',
    'check_room':       'Check Room',
    'return_to_charge': 'Return to Charge',
}


class TaskManager:
    def __init__(self):
        self.task_queue = []         # Pending tasks
        self.active_tasks = []       # Currently being executed
        self.completed_tasks = []    # Finished tasks
        self.total_response_time = 0
        self.system_alerts = []
        self._auto_gen_timer = 0

    # ------------------------------------------------------------------
    #  Task creation
    # ------------------------------------------------------------------
    def create_task(self, task_type, location_node, priority=1, description=''):
        """Add a new task to the queue."""
        task = Task(task_type, location_node, priority, description)
        self.task_queue.append(task)
        self.add_alert(f'New task: {task}')
        return task

    # ------------------------------------------------------------------
    #  Auto task generation
    # ------------------------------------------------------------------
    def auto_generate_from_humans(self, human_agents, dt):
        """Scan human agents for help requests and create tasks."""
        for human in human_agents:
            if human.needs_help and human.help_request_type:
                # Check if we already have a pending/active task for this human
                existing = False
                for t in self.task_queue + self.active_tasks:
                    if t.location_node == human.current_node and t.status in ('pending', 'assigned'):
                        existing = True
                        break
                if not existing:
                    desc = f'{human.agent_type.title()} in {human.current_node} needs help'
                    priority = 2 if human.help_request_type == 'assist_patient' else 1
                    if human.help_request_type == 'deliver_medicine':
                        priority = 3
                    self.create_task(
                        human.help_request_type,
                        human.current_node,
                        priority=priority,
                        description=desc,
                    )

    # ------------------------------------------------------------------
    #  Task assignment (priority scoring)
    # ------------------------------------------------------------------
    def assign_tasks(self, robots):
        """Match idle robots to highest-priority unassigned tasks."""
        # Sort tasks by priority (descending)
        pending = [t for t in self.task_queue if t.status == 'pending']
        pending.sort(key=lambda t: t.priority, reverse=True)

        available = [r for r in robots if r.is_available()]

        for task in pending:
            if not available:
                break

            best_robot = None
            best_score = float('-inf')
            tx, tz = get_node_position(task.location_node)

            for robot in available:
                rx, rz = robot.world_x, robot.world_z
                distance = math.hypot(tx - rx, tz - rz)
                score = (5 * task.priority) - (1 * distance) + (0.5 * robot.battery)

                if score > best_score:
                    best_score = score
                    best_robot = robot

            if best_robot:
                task.status = 'assigned'
                task.assigned_robot = best_robot.id
                best_robot.assign_task(task)

                self.task_queue.remove(task)
                self.active_tasks.append(task)
                available.remove(best_robot)

    # ------------------------------------------------------------------
    #  Task completion tracking
    # ------------------------------------------------------------------
    def check_completed(self, robots):
        """Move completed tasks from active list."""
        newly_completed = []
        for task in list(self.active_tasks):
            if task.status == 'completed':
                self.active_tasks.remove(task)
                self.completed_tasks.append(task)
                if task.completed_time and task.created_time:
                    self.total_response_time += (task.completed_time - task.created_time)
                newly_completed.append(task)

        return newly_completed

    # ------------------------------------------------------------------
    #  Metrics
    # ------------------------------------------------------------------
    def get_metrics(self):
        completed = len(self.completed_tasks)
        avg_time = 0
        if completed > 0:
            avg_time = self.total_response_time / completed
        return {
            'pending': len(self.task_queue),
            'active': len(self.active_tasks),
            'completed': completed,
            'avg_response_time': round(avg_time, 1),
        }

    def get_queue_display(self, max_items=8):
        """Return list of task strings for UI display."""
        items = []
        for t in self.task_queue[:max_items]:
            label = TASK_TYPE_LABELS.get(t.task_type, t.task_type)
            items.append(f'P{t.priority} {label} -> {t.location_node}')
        return items

    def get_active_display(self, max_items=5):
        items = []
        for t in self.active_tasks[:max_items]:
            label = TASK_TYPE_LABELS.get(t.task_type, t.task_type)
            rname = f'R{t.assigned_robot + 1}' if t.assigned_robot is not None else '?'
            items.append(f'{rname}: {label}')
        return items

    # ------------------------------------------------------------------
    #  Alerts
    # ------------------------------------------------------------------
    def add_alert(self, msg):
        self.system_alerts.append(msg)
        if len(self.system_alerts) > 20:
            self.system_alerts = self.system_alerts[-20:]

    def get_recent_alerts(self, count=5):
        return self.system_alerts[-count:]
