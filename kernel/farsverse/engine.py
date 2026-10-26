"""
FARSverse Authoritative Simulation Engine
Central heartbeat running the multi-agent loop, physics, battery, tasks, and telemetry broadcast.
"""
from __future__ import annotations
import math
import random
import re
import threading
import time
from typing import Any, Dict, List, Optional
from kernel.farsverse.world import FARSverseWorld
from kernel.farsverse.robot import FARSverseRobot
from kernel.farsverse.human import FARSverseHuman
from kernel.farsverse.task_manager import TaskManager
from kernel.farsverse.nlp_parser import parse_natural_language_command


class SimulationEngine:
    """The single authoritative simulation engine governing world state, robots, humans, and tasks."""

    def __init__(self, template_name: str = "hospital", robot_count: int = 5, human_count: int = 24, auto_start: bool = True):
        self._lock = threading.RLock()
        self.template_name = template_name
        self.world = FARSverseWorld(template_name)
        self.task_manager = TaskManager()

        # Lifecycle & Clock
        self.status: str = "RUNNING" if auto_start else "PAUSED"
        self.sim_time: float = 0.0
        self.speed: float = 1.0  # multiplier: 0.5x, 1.0x, 2.0x, 4.0x
        self.base_tick_hz: float = 20.0
        self.tick_dt: float = 1.0 / self.base_tick_hz

        # Entities
        self.robots: List[FARSverseRobot] = []
        self.humans: List[FARSverseHuman] = []
        self.events: List[Dict[str, Any]] = []

        # Metrics history for charts
        self.metrics_history: List[Dict[str, Any]] = []
        self._metrics_sample_timer: float = 0.0

        # Background thread
        self._running_thread: bool = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True, name="FARSverse-SimEngine")

        # Initialize fleet and population
        self.init_population(robot_count, human_count)
        if auto_start:
            self._thread.start()

    def init_population(self, robot_count: int = 5, human_count: int = 24) -> None:
        with self._lock:
            self.robots.clear()
            self.humans.clear()
            self.task_manager.reset()
            self.events.clear()
            self.metrics_history.clear()
            self.sim_time = 0.0

            # Docking and spawn positions
            dock_x, dock_z = self.world.charging_dock
            robot_types = ["hospital_assistant", "delivery_robot", "service_robot"]

            for i in range(1, robot_count + 1):
                offset_x = (i - (robot_count / 2.0)) * 1.8
                r = FARSverseRobot(
                    robot_id=f"FARS-{i:02d}",
                    name=f"CareBot-{i:02d}" if i % 2 == 1 else f"MedCourier-{i:02d}",
                    robot_type=robot_types[(i - 1) % len(robot_types)],
                    initial_pos=(dock_x + offset_x, dock_z),
                    speed=2.2,
                    battery=random.uniform(85.0, 100.0)
                )
                self.robots.append(r)

            # Spawn humans across rooms and corridors
            room_names = [r['id'] for r in self.world.rooms]
            names_first = ["Sarah", "David", "Emma", "James", "Elena", "Marcus", "Aria", "Liam", "Sophia", "Noah", "Chloe", "Lucas"]
            names_last = ["Chen", "Patel", "Miller", "Vance", "Johnson", "Davis", "Taylor", "Smith", "Wilson", "Anderson"]

            for h_idx in range(1, human_count + 1):
                role = "patient"
                home = f"Room{((h_idx - 1) % 20) + 1}" if "Room1" in self.world.nodes else "MainHall"
                if h_idx > 20:
                    role = "nurse" if h_idx % 2 == 0 else "doctor"
                    home = "Pharmacy" if role == "nurse" else "StaffOffice"
                elif h_idx > 16:
                    role = "visitor"
                    home = "WaitingHall"

                h_name = f"{names_first[(h_idx * 3) % len(names_first)]} {names_last[(h_idx * 7) % len(names_last)]}"
                pos = self.world.nodes.get(home, (0.0, 0.0))
                human = FARSverseHuman(
                    human_id=f"HUMAN-{h_idx:02d}",
                    name=h_name,
                    agent_type=role,
                    home_node=home,
                    initial_pos=(pos[0] + random.uniform(-1.0, 1.0), pos[1] + random.uniform(-1.0, 1.0))
                )
                self.humans.append(human)

            self.add_event("INFO", "system", f"Initialized FARSverse '{self.world.name}' with {len(self.robots)} robots and {len(self.humans)} agents.")

    def add_event(self, severity: str, category: str, message: str) -> None:
        evt = {
            'id': len(self.events) + 1,
            'timestamp': time.time(),
            'sim_time': round(self.sim_time, 1),
            'severity': severity,  # 'INFO', 'WARN', 'ERROR'
            'category': category,
            'message': message
        }
        self.events.append(evt)
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def _simulation_loop(self) -> None:
        """Background heartbeat ticking the authoritative state at ~20Hz."""
        while self._running_thread:
            tick_start = time.time()
            if self.status == "RUNNING":
                dt = self.tick_dt * self.speed
                with self._lock:
                    self._tick(dt)

            elapsed = time.time() - tick_start
            sleep_time = max(0.002, (1.0 / self.base_tick_hz) - elapsed)
            time.sleep(sleep_time)

    def _tick(self, dt: float) -> None:
        self.sim_time += dt

        # 1. Update human agents & collect any generated requests
        collected_events: List[Dict[str, Any]] = []
        for human in self.humans:
            req = human.update(dt, self.world)
            if req:
                # Limit background autonomous human tasks so at least 3 robots remain free for user commands
                active_human_tasks = sum(1 for t in self.task_manager.active_tasks if t.origin == "human_agent")
                if active_human_tasks < 2 and len(self.task_manager.task_queue) < 3:
                    self.task_manager.create_task(
                        task_type=req['task_type'],
                        location_node=req['location_node'],
                        priority=req['priority'],
                        description=req['description'],
                        origin="human_agent",
                        human_id=req['human_id']
                    )
                    self.add_event("INFO", "human", req['description'])
                else:
                    human.needs_help = False
                    human.status = "resting" if human.agent_type == "patient" else "walking"

        # 2. Autonomous Task Scheduler matches tasks to available robots
        self.task_manager.schedule(self.robots, self.world, collected_events)

        # 3. Update Robots
        for robot in self.robots:
            completed = robot.update(dt, self.world, collected_events)
            if completed:
                self.task_manager.on_task_completed(completed, collected_events)
                # If human was waiting for this task, mark assisted
                h_id = completed.get('human_id')
                if h_id:
                    for h in self.humans:
                        if h.id == h_id:
                            h.mark_assisted()
                            break

        # Flush collected events
        for e in collected_events:
            self.add_event(e.get('severity', 'INFO'), e.get('category', 'simulation'), e.get('message', ''))

        # 4. Periodically capture metrics snapshot (every 2.0 sim seconds)
        self._metrics_sample_timer += dt
        if self._metrics_sample_timer >= 2.0:
            self._metrics_sample_timer = 0.0
            self._record_metrics_sample()

    def _record_metrics_sample(self) -> None:
        active_cnt = sum(1 for r in self.robots if r.state in ("NAVIGATING", "ASSISTING", "DELIVERING"))
        idle_cnt = sum(1 for r in self.robots if r.state == "IDLE")
        charging_cnt = sum(1 for r in self.robots if r.state == "CHARGING")
        avg_battery = sum(r.battery for r in self.robots) / max(len(self.robots), 1)
        total_dist = sum(r.total_distance for r in self.robots)

        m = self.task_manager.get_metrics()
        sample = {
            'sim_time': round(self.sim_time, 1),
            'active_robots': active_cnt,
            'idle_robots': idle_cnt,
            'charging_robots': charging_cnt,
            'avg_battery': round(avg_battery, 1),
            'total_distance': round(total_dist, 1),
            'completed_tasks': m['completed_tasks'],
            'pending_tasks': m['pending_tasks'],
            'avg_response_time': m['avg_response_time_seconds']
        }
        self.metrics_history.append(sample)
        if len(self.metrics_history) > 60:
            self.metrics_history = self.metrics_history[-60:]

    # ------------------------------------------------------------------
    #  Controls
    # ------------------------------------------------------------------
    def play(self) -> None:
        with self._lock:
            self.status = "RUNNING"
            self.add_event("INFO", "control", "Simulation resumed (PLAY).")

    def pause(self) -> None:
        with self._lock:
            self.status = "PAUSED"
            self.add_event("INFO", "control", "Simulation paused.")

    def stop(self) -> None:
        with self._lock:
            self.status = "STOPPED"
            self.add_event("WARN", "control", "Simulation stopped.")

    def reset(self) -> None:
        with self._lock:
            self.init_population(len(self.robots) or 5, len(self.humans) or 24)
            self.status = "RUNNING"
            self.add_event("INFO", "control", "Simulation reset to initial scenario.")

    def step(self, seconds: float = 0.5) -> None:
        with self._lock:
            self.status = "PAUSED"
            self._tick(seconds)
            self.add_event("INFO", "control", f"Stepped forward by {seconds:.1f}s.")

    def set_speed(self, multiplier: float) -> None:
        with self._lock:
            self.speed = max(0.2, min(8.0, float(multiplier)))
            self.add_event("INFO", "control", f"Simulation speed set to {self.speed}x.")

    def load_environment(self, template_name: str) -> None:
        with self._lock:
            self.template_name = template_name
            self.world = FARSverseWorld(template_name)
            self.init_population(len(self.robots) or 3, 20 if template_name == 'hospital' else 12)

    def execute_command(self, cmd_text: str) -> Dict[str, Any]:
        """Process natural language command and execute on authoritative state."""
        parsed = parse_natural_language_command(cmd_text)
        action = parsed.get('action')

        with self._lock:
            if action == 'pause':
                self.pause()
            elif action == 'play':
                self.play()
            elif action == 'reset':
                self.reset()
            elif action == 'block_corridor':
                self.world.toggle_obstacle('obs_trolley_1', active=True)
                self.add_event("WARN", "environment", "Obstacle deployed: West Corridor blocked.")
            elif action == 'unblock_corridor':
                self.world.toggle_obstacle('obs_trolley_1', active=False)
                self.add_event("INFO", "environment", "West Corridor obstacle cleared.")
            elif action == 'create_task':
                target_loc = parsed.get('location', 'MainHall')
                target_robot_id = parsed.get('target_robot')

                # Match explicit robot if specified (e.g. "Rob-1", "Robot 1", "FARS-01", "CareBot-01")
                target_robot = None
                if target_robot_id:
                    clean_target = str(target_robot_id).lower().strip()
                    num_match = re.search(r'\d+', clean_target)
                    target_num = int(num_match.group(0)) if num_match else None
                    for r in self.robots:
                        if (r.id.lower() == clean_target or 
                            r.name.lower() == clean_target or 
                            (target_num is not None and f"{target_num:02d}" in r.id)):
                            target_robot = r
                            break

                task = self.task_manager.create_task(
                    task_type=parsed.get('task_type', 'assist_patient'),
                    location_node=target_loc,
                    priority=4,  # P4 = Critical Priority for user commands
                    description=parsed.get('description', cmd_text),
                    origin="llm" if parsed.get('parsed_by') == 'ollama' else "nlp_fallback"
                )

                if target_robot:
                    path_data = self.world.find_path((target_robot.x, target_robot.z), target_loc)
                    if path_data.get('success'):
                        task.status = "assigned"
                        task.assigned_robot = target_robot.id
                        task.selection_reason = f"Explicitly assigned to {target_robot.name} [{target_robot.id}] by user command"
                        target_robot.assign_task(task.to_dict(), path_data, reason=task.selection_reason)
                        if task in self.task_manager.task_queue:
                            self.task_manager.task_queue.remove(task)
                        self.task_manager.active_tasks.append(task)
                        self.add_event("INFO", "command", f"Dispatched {target_robot.name} [{target_robot.id}] directly to {target_loc}.")
                else:
                    # Multi-factor scheduling immediately dispatches nearest available robot
                    self.task_manager.schedule(self.robots, self.world, self.events)
                    self.add_event("INFO", "command", f"Dispatched Task #{task.id}: {task.description} -> {target_loc}")

                # Ensure simulation is running so the robot immediately starts moving!
                if self.status != "RUNNING":
                    self.status = "RUNNING"
                    self.add_event("INFO", "control", "Simulation automatically set to RUNNING for command execution.")

        return parsed

    # ------------------------------------------------------------------
    #  State Snapshot for Frontend Viewport & WebSockets
    # ------------------------------------------------------------------
    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            task_metrics = self.task_manager.get_metrics()
            return {
                'status': self.status,
                'sim_time': round(self.sim_time, 1),
                'speed': self.speed,
                'world': self.world.to_dict(),
                'robots': [r.to_dict() for r in self.robots],
                'humans': [h.to_dict() for h in self.humans],
                'tasks': {
                    'pending': [t.to_dict() for t in self.task_manager.task_queue],
                    'active': [t.to_dict() for t in self.task_manager.active_tasks],
                    'completed': [t.to_dict() for t in self.task_manager.completed_tasks[-10:]],
                    'failed': [t.to_dict() for t in self.task_manager.failed_tasks[-5:]],
                    'metrics': task_metrics
                },
                'events': self.events[-30:],
                'metrics_history': self.metrics_history[-30:],
            }
