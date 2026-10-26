"""
FARSverse Human Agents Model
Simulates patients, visitors, nurses, and doctors with autonomous routines and assistance requests.
"""
from __future__ import annotations
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple


class FARSverseHuman:
    """Simulated human agent with realistic behavioral routines, destinations, and help triggers."""

    def __init__(self,
                 human_id: str,
                 name: str,
                 agent_type: str = "patient",
                 home_node: str = "Room1",
                 initial_pos: Tuple[float, float] = (0.0, 0.0)):
        self.id = human_id
        self.name = name
        self.agent_type = agent_type  # 'patient', 'visitor', 'nurse', 'doctor'
        self.home_node = home_node
        self.current_node = home_node

        self.x = float(initial_pos[0])
        self.z = float(initial_pos[1])
        self.target_x = self.x
        self.target_z = self.z
        self.speed = 1.0 if agent_type in ('patient', 'visitor') else 1.4

        self.needs_help = False
        self.help_request_type: Optional[str] = None  # 'assist_patient', 'deliver_medicine', 'guide_patient'
        self.assisted_by_robot: Optional[str] = None
        self.status = "resting" if agent_type == "patient" else "walking"

        self.routine_timer = random.uniform(5.0, 20.0)
        self.help_cooldown = random.uniform(40.0, 90.0)

    def trigger_help_request(self) -> Optional[Dict[str, Any]]:
        """Trigger an assistance request if eligible."""
        if self.needs_help or self.assisted_by_robot is not None:
            return None

        if self.agent_type == "patient":
            req_type = "deliver_medicine" if random.random() < 0.4 else "assist_patient"
            priority = 3 if req_type == "deliver_medicine" else 2
            desc = f"{self.name} in {self.current_node} requests {req_type.replace('_', ' ')}"
        elif self.agent_type == "visitor":
            req_type = "guide_patient"
            priority = 1
            desc = f"Visitor {self.name} at {self.current_node} needs guidance"
        else:
            req_type = "check_room"
            priority = 2
            desc = f"Staff call from {self.name} at {self.current_node}"

        self.needs_help = True
        self.help_request_type = req_type
        self.status = "awaiting_assistance"

        return {
            'task_type': req_type,
            'location_node': self.current_node,
            'priority': priority,
            'description': desc,
            'human_id': self.id,
            'human_name': self.name
        }

    def update(self, dt: float, world: Any) -> Optional[Dict[str, Any]]:
        if dt <= 0.0:
            return None

        # Movement interpolation towards target_x, target_z
        dx = self.target_x - self.x
        dz = self.target_z - self.z
        dist = math.hypot(dx, dz)
        if dist > 0.1:
            step = min(dist, self.speed * dt)
            self.x += (dx / dist) * step
            self.z += (dz / dist) * step

        # Help request timer
        self.help_cooldown -= dt
        generated_req = None
        if self.help_cooldown <= 0.0 and not self.needs_help:
            self.help_cooldown = random.uniform(30.0, 70.0)
            generated_req = self.trigger_help_request()

        # Routine behavior
        self.routine_timer -= dt
        if self.routine_timer <= 0.0:
            self.routine_timer = random.uniform(15.0, 35.0)
            self._execute_routine(world)

        return generated_req

    def _execute_routine(self, world: Any) -> None:
        """Select next behavioral goal depending on agent role."""
        if self.needs_help or self.assisted_by_robot:
            return

        nodes = world.nodes
        if self.agent_type == "nurse":
            # Nurse visits pharmacy or patient rooms
            possible = ["Pharmacy", "StaffOffice", "ICU_Corr", "RoomCorrW1", "RoomCorrE1"]
            dest = random.choice(possible)
            if dest in nodes:
                self.current_node = dest
                self.target_x, self.target_z = nodes[dest]
                self.status = f"patrolling ({dest})"
        elif self.agent_type == "doctor":
            possible = ["EmergencyRoom", "StaffOffice", "ICU1", "ICU2", "MainHall"]
            dest = random.choice(possible)
            if dest in nodes:
                self.current_node = dest
                self.target_x, self.target_z = nodes[dest]
                self.status = f"rounds ({dest})"
        elif self.agent_type == "visitor":
            possible = ["Reception", "WaitingHall", "Entrance", "MainHall"]
            dest = random.choice(possible)
            if dest in nodes:
                self.current_node = dest
                self.target_x, self.target_z = nodes[dest]
                self.status = f"walking ({dest})"
        else:
            # Patient mostly stays in home room, occasionally visits waiting area
            if random.random() < 0.25 and "WaitingHall" in nodes:
                self.current_node = "WaitingHall"
                self.target_x, self.target_z = nodes["WaitingHall"]
                self.status = "visiting waiting hall"
            else:
                self.current_node = self.home_node
                if self.home_node in nodes:
                    self.target_x, self.target_z = nodes[self.home_node]
                self.status = "resting in room"

    def mark_assisted(self) -> None:
        self.needs_help = False
        self.help_request_type = None
        self.assisted_by_robot = None
        self.status = "assisted"
        self.help_cooldown = random.uniform(40.0, 90.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'agent_type': self.agent_type,
            'home_node': self.home_node,
            'current_node': self.current_node,
            'x': round(self.x, 2),
            'z': round(self.z, 2),
            'needs_help': self.needs_help,
            'help_request_type': self.help_request_type,
            'assisted_by_robot': self.assisted_by_robot,
            'status': self.status
        }
