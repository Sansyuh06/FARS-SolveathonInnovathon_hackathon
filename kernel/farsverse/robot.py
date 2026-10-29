"""
FARSverse Robot Agent Model
Autonomous state machine, battery dynamics, path following, sensor raycasting, and decision traces.
"""
from __future__ import annotations
import math
import time
from typing import Any, Dict, List, Optional, Tuple


class FARSverseRobot:
    """Simulated autonomous mobile robot with authentic kinematics, battery, sensors, and task execution."""

    def __init__(self,
                 robot_id: str,
                 name: str,
                 robot_type: str = "hospital_assistant",
                 initial_pos: Tuple[float, float] = (0.0, -10.0),
                 speed: float = 2.0,
                 battery_capacity: float = 100.0,
                 battery: float = 100.0):
        self.id = robot_id
        self.name = name
        self.robot_type = robot_type

        # Kinematics
        self.x = float(initial_pos[0])
        self.y = 0.0
        self.z = float(initial_pos[1])
        self.rotation_y = 0.0  # degrees (0 = facing +Z)
        self.speed = float(speed)
        self.total_distance = 0.0

        # Battery
        self.battery_capacity = float(battery_capacity)
        self.battery = float(battery)
        self.drain_rate_moving = 0.18  # % per meter traveled
        self.drain_rate_idle = 0.015   # % per simulation second
        self.charge_rate = 3.5         # % per simulation second at dock

        # State Machine: IDLE, ASSIGNED, NAVIGATING, ASSISTING, DELIVERING, CHARGING, ERROR, EMERGENCY_STOP
        self.state = "IDLE"
        self.current_task: Optional[Dict[str, Any]] = None
        self.target_node: Optional[str] = None
        self.destination_name: str = "Charging Dock"

        # Navigation
        self.path_nodes: List[str] = []
        self.waypoints: List[List[float]] = []
        self.waypoint_index: int = 0
        self.execution_timer: float = 0.0  # timer spent assisting / delivering
        self.required_work_duration: float = 3.0

        # Sensors
        self.ultrasonic_range: float = 6.0  # max sensor reach in meters
        self.ultrasonic_distance: float = 6.0
        self.detected_obstacles: List[str] = []
        self.camera_fov_degrees: float = 90.0

        # Diagnostics & Trace
        self.decision_trace: str = f"Initialized {name} [{robot_id}] at docking station in standby mode."
        self.history: List[Dict[str, Any]] = []

    def is_available(self) -> bool:
        """Robot is free if IDLE and battery > 20%."""
        return self.state in ("IDLE", "CHARGING") and self.battery > 20.0 and self.current_task is None

    def assign_task(self, task: Dict[str, Any], path_data: Dict[str, Any], reason: str = "") -> bool:
        if not path_data.get('success'):
            self.state = "ERROR"
            self.decision_trace = f"Assignment rejected: {path_data.get('error', 'No route')}"
            return False

        self.current_task = task
        self.target_node = task.get('location_node')
        self.destination_name = task.get('description', self.target_node)
        self.path_nodes = list(path_data.get('path', []))
        self.waypoints = [list(wp) for wp in path_data.get('waypoints', [])]
        self.waypoint_index = 0
        self.execution_timer = 0.0

        task_type = task.get('task_type', 'assist_patient')
        if task_type == 'deliver_medicine':
            self.required_work_duration = 3.5
        elif task_type == 'guide_patient':
            self.required_work_duration = 4.0
        elif task_type == 'check_room':
            self.required_work_duration = 2.0
        else:
            self.required_work_duration = 3.0

        self.state = "NAVIGATING"
        self.decision_trace = reason or f"Assigned to {task.get('description', self.target_node)}. Planned {len(self.waypoints)} waypoints ({path_data.get('distance')}m)."
        return True

    def teleop(self, linear: float, angular: float, world: Any) -> None:
        """Direct manual drive teleoperation."""
        self.rotation_y = (self.rotation_y + angular * 12.0) % 360
        rad = math.radians(self.rotation_y)
        step = linear * self.speed * 0.45
        new_x = self.x + math.sin(rad) * step
        new_z = self.z + math.cos(rad) * step

        # Clamp to bounds
        self.x = max(-42.0, min(42.0, new_x))
        self.z = max(-35.0, min(35.0, new_z))
        self.total_distance += abs(step)
        self.battery = max(0.0, self.battery - abs(step) * self.drain_rate_moving)
        self.waypoints = []
        self.waypoint_index = 0
        self.state = "NAVIGATING" if (abs(linear) > 0.05 or abs(angular) > 0.05) else "IDLE"
        self.target_node = "Manual Teleop"
        self.destination_name = "Manual Teleop"
        self.decision_trace = f"Manual teleoperation: linear={linear:+.1f}, angular={angular:+.1f}"

    def update(self, dt: float, world: Any, events_collector: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Advance the robot simulation state by dt simulation seconds."""
        if dt <= 0.0:
            return None

        # Battery dynamics
        if self.state == "CHARGING":
            self.battery = min(100.0, self.battery + self.charge_rate * dt)
            if self.battery >= 98.0 and self.current_task is None:
                self.state = "IDLE"
                self.decision_trace = f"Battery replenished ({self.battery:.1f}%). Standing by for fleet assignments."
                events_collector.append({
                    'timestamp': time.time(),
                    'severity': 'INFO',
                    'category': 'robot',
                    'message': f"{self.id} finished charging ({self.battery:.0f}%) and is ready."
                })
        else:
            idle_drain = self.drain_rate_idle * dt
            self.battery = max(0.0, self.battery - idle_drain)

        # Emergency low battery check
        if self.battery <= 1.0 and self.state != "ERROR":
            self.state = "ERROR"
            self.decision_trace = f"EMERGENCY: Battery depleted (0%). Critical system shutdown."
            events_collector.append({
                'timestamp': time.time(),
                'severity': 'ERROR',
                'category': 'battery',
                'message': f"{self.id} depleted battery completely. Manual retrieval required."
            })
            return None

        # Auto-return to charging if low battery and idle
        if self.battery < 20.0 and self.state == "IDLE" and self.target_node != "ChargingDock":
            charge_path = world.find_path((self.x, self.z), "ChargingDock")
            if charge_path.get('success'):
                self.state = "NAVIGATING"
                self.target_node = "ChargingDock"
                self.destination_name = "Auto Charging Dock"
                self.path_nodes = charge_path.get('path', [])
                self.waypoints = charge_path.get('waypoints', [])
                self.waypoint_index = 0
                self.decision_trace = f"Battery low ({self.battery:.1f}%). Autonomous return to Charging Dock initiated."
                events_collector.append({
                    'timestamp': time.time(),
                    'severity': 'WARN',
                    'category': 'battery',
                    'message': f"{self.id} battery low ({self.battery:.0f}%). Returning to Charging Dock."
                })

        # Update forward ultrasonic sensor
        self._update_sensors(world)

        # State: NAVIGATING
        completed_task = None
        if self.state == "NAVIGATING":
            if self.waypoint_index < len(self.waypoints):
                target_wp = self.waypoints[self.waypoint_index]
                dx = target_wp[0] - self.x
                dz = target_wp[1] - self.z
                dist_to_wp = math.hypot(dx, dz)

                # Skip start node immediately if robot is already at it
                if dist_to_wp < 0.05 and self.waypoint_index < len(self.waypoints) - 1:
                    self.waypoint_index += 1
                    target_wp = self.waypoints[self.waypoint_index]
                    dx = target_wp[0] - self.x
                    dz = target_wp[1] - self.z
                    dist_to_wp = math.hypot(dx, dz)

                # Heading rotation
                if dist_to_wp > 0.05:
                    target_rot = math.degrees(math.atan2(dx, dz))
                    # Smooth heading interpolation
                    rot_diff = (target_rot - self.rotation_y + 180) % 360 - 180
                    self.rotation_y += rot_diff * min(1.0, dt * 6.0)

                # Check if forward path is unexpectedly blocked by newly activated obstacle
                if self.ultrasonic_distance < 1.2:
                    # Trigger dynamic replanning
                    if self.target_node:
                        replan = world.find_path((self.x, self.z), self.target_node)
                        if replan.get('success') and len(replan.get('waypoints', [])) > 1:
                            self.waypoints = replan.get('waypoints', [])
                            self.path_nodes = replan.get('path', [])
                            self.waypoint_index = 0
                            self.decision_trace = f"Obstacle encountered at {self.ultrasonic_distance:.1f}m. Recalculated dynamic route ({len(self.waypoints)} waypoints)."
                            events_collector.append({
                                'timestamp': time.time(),
                                'severity': 'WARN',
                                'category': 'navigation',
                                'message': f"{self.id} detected corridor obstruction. Path recalculated to {self.target_node}."
                            })
                            return None
                        else:
                            self.state = "ERROR"
                            self.decision_trace = f"Path obstructed and no alternate route found to {self.target_node}."
                            events_collector.append({
                                'timestamp': time.time(),
                                'severity': 'ERROR',
                                'category': 'navigation',
                                'message': f"{self.id} route blocked to {self.target_node}. Task halted."
                            })
                            return None

                step_dist = self.speed * dt
                if dist_to_wp <= step_dist:
                    self.x = target_wp[0]
                    self.z = target_wp[1]
                    self.total_distance += dist_to_wp
                    self.battery = max(0.0, self.battery - dist_to_wp * self.drain_rate_moving)
                    self.waypoint_index += 1
                else:
                    self.x += (dx / dist_to_wp) * step_dist
                    self.z += (dz / dist_to_wp) * step_dist
                    self.total_distance += step_dist
                    self.battery = max(0.0, self.battery - step_dist * self.drain_rate_moving)
            else:
                # Reached final waypoint
                if self.target_node == "ChargingDock":
                    self.state = "CHARGING"
                    self.decision_trace = f"Docked at Charging Station. Commencing power replenishment."
                elif self.current_task:
                    task_type = self.current_task.get('task_type', 'assist_patient')
                    self.state = "DELIVERING" if task_type == 'deliver_medicine' else "ASSISTING"
                    self.execution_timer = 0.0
                    self.decision_trace = f"Arrived at {self.target_node}. Executing '{task_type}' procedure."
                else:
                    self.state = "IDLE"
                    self.decision_trace = f"Arrived at destination {self.target_node}. Standing by."

        # State: ASSISTING / DELIVERING
        elif self.state in ("ASSISTING", "DELIVERING"):
            self.execution_timer += dt
            if self.execution_timer >= self.required_work_duration:
                # Task finished
                completed_task = self.current_task
                self.history.append({
                    'task': self.current_task,
                    'completed_at': time.time(),
                    'destination': self.target_node,
                    'status': 'SUCCESS'
                })
                self.current_task = None
                self.decision_trace = f"Task completed successfully at {self.target_node}. Transitioning to IDLE."
                self.state = "IDLE"

        return completed_task

    def _update_sensors(self, world: Any) -> None:
        """Raycast forward ultrasonic sensor against active obstacles and walls."""
        rad = math.radians(self.rotation_y)
        dir_x = math.sin(rad)
        dir_z = math.cos(rad)

        min_dist = self.ultrasonic_range
        detected: List[str] = []

        active_obstacles = [obs for obs in world.obstacles if obs.get('active', True)]
        for obs in active_obstacles:
            dx = obs['x'] - self.x
            dz = obs['z'] - self.z
            dist = math.hypot(dx, dz)
            if dist < self.ultrasonic_range:
                # Check angle relative to robot forward heading
                dot = (dx * dir_x + dz * dir_z) / max(dist, 0.001)
                if dot > 0.6:  # within ~53 degrees forward cone
                    if dist < min_dist:
                        min_dist = dist
                    detected.append(obs.get('name', obs.get('id', 'Obstacle')))

        self.ultrasonic_distance = round(min_dist, 2)
        self.detected_obstacles = detected

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'robot_type': self.robot_type,
            'x': round(self.x, 2),
            'y': round(self.y, 2),
            'z': round(self.z, 2),
            'rotation_y': round(self.rotation_y, 1),
            'speed': self.speed,
            'total_distance': round(self.total_distance, 1),
            'battery': round(self.battery, 1),
            'battery_capacity': self.battery_capacity,
            'state': self.state,
            'current_task': self.current_task,
            'target_node': self.target_node,
            'destination_name': self.destination_name,
            'waypoints': self.waypoints,
            'waypoint_index': self.waypoint_index,
            'ultrasonic_distance': self.ultrasonic_distance,
            'detected_obstacles': self.detected_obstacles,
            'decision_trace': self.decision_trace,
            'history': self.history[-10:],
        }
