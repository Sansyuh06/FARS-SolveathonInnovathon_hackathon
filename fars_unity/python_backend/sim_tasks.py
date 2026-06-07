import time
import math
from sim_navigation import get_node_position

class Task:
    _id_counter = 0

    def __init__(self, task_type, location_node, priority=1, description=''):
        Task._id_counter += 1
        self.id = Task._id_counter
        self.task_type = task_type
        self.location_node = location_node
        self.priority = priority
        self.description = description
        self.status = 'pending'
        self.assigned_robot = None
        self.created_time = time.time()
        self.completed_time = None

    def __str__(self):
        return f'[{self.task_type}] -> {self.location_node} (P{self.priority})'

    def get_state_dict(self):
        return {
            'id': self.id,
            'type': self.task_type,
            'node': self.location_node,
            'priority': self.priority,
            'status': self.status,
            'robot': self.assigned_robot
        }

class TaskManager:
    def __init__(self):
        self.task_queue = []
        self.active_tasks = []
        self.completed_tasks = []
        self.total_response_time = 0
        self.system_alerts = []

    def create_task(self, task_type, location_node, priority=1, description=''):
        task = Task(task_type, location_node, priority, description)
        self.task_queue.append(task)
        self.add_alert(f'New task: {task}')
        return task

    def auto_generate_from_humans(self, human_agents, dt):
        for human in human_agents:
            if human.needs_help and human.help_request_type:
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

    def assign_tasks(self, robots):
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

    def check_completed(self, robots):
        newly_completed = []
        for task in list(self.active_tasks):
            if task.status == 'completed':
                self.active_tasks.remove(task)
                self.completed_tasks.append(task)
                if task.completed_time and task.created_time:
                    self.total_response_time += (task.completed_time - task.created_time)
                newly_completed.append(task)

        return newly_completed

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

    def add_alert(self, msg):
        self.system_alerts.append(msg)
        if len(self.system_alerts) > 20:
            self.system_alerts = self.system_alerts[-20:]

    def get_state_dict(self):
        return {
            'queue': [t.get_state_dict() for t in self.task_queue],
            'active': [t.get_state_dict() for t in self.active_tasks],
            'alerts': self.system_alerts[-10:],
            'metrics': self.get_metrics()
        }
