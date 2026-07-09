import math
import random
import time
from sim_navigation import find_path, get_node_position, get_all_room_nodes

MOVE_SPEED = 8.0
BATTERY_DRAIN_RATE = 0.03
BATTERY_CHARGE_RATE = 0.15
LOW_BATTERY_THRESHOLD = 15.0
TASK_EXECUTE_TIME = 3.0

class RobotAgent:
    def __init__(self, robot_id, start_node='ChargingDock'):
        self.id = robot_id
        self.state = 'idle'
        self.battery = 100.0
        self.current_task = None
        self.task_history = []
        self.current_node = start_node
        self.target_node = None
        self.thought_log = ["System initialized.", "Standing by."]
        self.path_nodes = []
        self.path_world = []
        self.path_index = 0
        self.task_timer = 0.0
        self.reward_signal = 0.0
        
        sx, sz = get_node_position(start_node)
        self.world_x = sx + (robot_id - 2) * 2.5
        self.world_z = sz

    def add_thought(self, msg):
        self.thought_log.append(f"> {msg}")
        if len(self.thought_log) > 6:
            self.thought_log.pop(0)

    def set_state(self, new_state):
        if self.state != new_state:
            self.add_thought(f"{self.state.upper()} -> {new_state.upper()}")
        self.state = new_state

    def assign_task(self, task):
        self.current_task = task
        self.target_node = task.location_node
        self.path_nodes = find_path(self.current_node, self.target_node)
        self.path_world = [get_node_position(n) for n in self.path_nodes]
        self.path_index = 0
        self.add_thought(f"Task: {task.task_type} -> {self.target_node}")

        if len(self.path_world) > 0:
            nav_state = 'navigating'
            if task.task_type in ('guide_patient', 'escort_visitor'):
                nav_state = 'guiding'
            elif task.task_type == 'deliver_medicine':
                nav_state = 'delivering'
            elif task.task_type == 'assist_patient':
                nav_state = 'assisting'
            self.set_state(nav_state)

    def update(self, dt):
        self.reward_signal = max(0.0, self.reward_signal - dt * 1.5)
        
        if self.state == 'idle':
            self._check_low_battery()
            return
        if self.state == 'charging':
            self._charge(dt)
            return
        if self.state in ('navigating', 'guiding', 'delivering', 'assisting', 'returning'):
            self._follow_path(dt)

    def _follow_path(self, dt):
        if self.path_index >= len(self.path_world):
            self._arrive()
            return

        tx, tz = self.path_world[self.path_index]
        dx = tx - self.world_x
        dz = tz - self.world_z
        dist = math.hypot(dx, dz)

        if dist < 0.3:
            self.world_x, self.world_z = tx, tz
            if self.path_index < len(self.path_nodes):
                self.current_node = self.path_nodes[self.path_index]
            self.path_index += 1
        else:
            speed = min(MOVE_SPEED * dt, dist)
            self.world_x += (dx / dist) * speed
            self.world_z += (dz / dist) * speed

        self.battery = max(0, self.battery - BATTERY_DRAIN_RATE * dt)
        if self.battery <= 0:
            self._force_return()

    def _arrive(self):
        if self.state == 'returning':
            self.add_thought("Docked. Charging.")
            self.set_state('charging')
            self.current_task = None
            return
        if self.current_task:
            if self.task_timer == 0:
                self.add_thought(f"Executing at {self.current_node}...")
            self.task_timer += 0.016 # dt approximation here since update takes dt but _arrive doesn't pass it easily
            if self.task_timer >= TASK_EXECUTE_TIME:
                self._complete_task()
                self.task_timer = 0

    def _complete_task(self):
        if self.current_task:
            self.add_thought("Task complete.")
            self.reward_signal = 1.0
            self.current_task.status = 'completed'
            self.current_task.completed_time = time.time()
            self.task_history.append(self.current_task)
            self.current_task = None
        self.target_node = None
        self.path_nodes = []
        self.path_world = []
        self.path_index = 0
        self.set_state('idle')
        self._check_low_battery()

    def _check_low_battery(self):
        if self.battery < LOW_BATTERY_THRESHOLD and self.state == 'idle':
            self._return_to_charge()

    def _return_to_charge(self):
        self.target_node = 'ChargingDock'
        self.path_nodes = find_path(self.current_node, 'ChargingDock')
        self.path_world = [get_node_position(n) for n in self.path_nodes]
        self.path_index = 0
        self.set_state('returning')

    def _force_return(self):
        if self.current_task:
            self.current_task.status = 'pending'
            self.current_task = None
        self._return_to_charge()

    def _charge(self, dt):
        self.battery += BATTERY_CHARGE_RATE * dt * 100
        if self.battery >= 100:
            self.battery = 100
            self.set_state('idle')

    def is_available(self):
        return self.state == 'idle' and self.battery > LOW_BATTERY_THRESHOLD
        
    def get_state_dict(self):
        return {
            'id': self.id,
            'world_x': self.world_x,
            'world_z': self.world_z,
            'state': self.state,
            'battery': self.battery,
            'current_node': self.current_node,
            'tasks_completed': len(self.task_history),
            'reward_signal': self.reward_signal,
            'thoughts': self.thought_log
        }


AGENT_LOCATIONS = {
    'patient': None,
    'doctor': ['MainHall', 'ICU1', 'ICU2', 'ICU3', 'ICU4', 'EmergencyRoom'],
    'nurse': ['Pharmacy', 'MainHall', 'WaitingHall'],
    'visitor': ['Reception', 'WaitingHall', 'MainHall'],
}

class HumanAgent:
    _id_counter = 0

    def __init__(self, agent_type, assigned_room=None):
        HumanAgent._id_counter += 1
        self.id = HumanAgent._id_counter
        self.agent_type = agent_type
        self.state = 'idle'
        self.assigned_room = assigned_room
        self.needs_help = False
        self.help_request_type = None

        locations = AGENT_LOCATIONS[agent_type]
        if assigned_room:
            self.home_node = assigned_room
        elif locations:
            self.home_node = random.choice(locations)
        else:
            self.home_node = random.choice(get_all_room_nodes())

        self.current_node = self.home_node
        sx, sz = get_node_position(self.home_node)
        self.world_x = sx + random.uniform(-1.5, 1.5)
        self.world_z = sz + random.uniform(-1.5, 1.5)
        self.path_world = []
        self.path_nodes = []
        self.path_index = 0

        self.idle_timer = random.uniform(3, 12)
        self.help_timer = random.uniform(15, 60) if agent_type == 'patient' else 999999

    def update(self, dt):
        if self.state == 'idle':
            self._idle(dt)
        elif self.state == 'walking':
            self._walk(dt)
        elif self.state == 'waiting':
            self._wait(dt)

    def _idle(self, dt):
        self.idle_timer -= dt
        if self.idle_timer <= 0:
            self._wander()
            self.idle_timer = random.uniform(5, 15)
        if self.agent_type == 'patient':
            self.help_timer -= dt
            if self.help_timer <= 0 and not self.needs_help:
                self._request_help()
                self.help_timer = random.uniform(30, 90)

    def _wander(self):
        locations = AGENT_LOCATIONS[self.agent_type]
        if self.agent_type == 'patient':
            target = self.home_node if random.random() < 0.7 else random.choice(
                ['WaitingHall', 'MainHall', self.home_node])
        elif locations:
            target = random.choice(locations + [self.home_node])
        else:
            target = random.choice(['MainHall', 'WaitingHall', 'Reception'])

        self.path_nodes = find_path(self.current_node, target)
        self.path_world = [get_node_position(n) for n in self.path_nodes]
        self.path_index = 0
        if len(self.path_world) > 1:
            self.state = 'walking'

    def _walk(self, dt):
        if self.path_index >= len(self.path_world):
            self.state = 'idle'
            if self.path_nodes:
                self.current_node = self.path_nodes[-1]
            return

        tx, tz = self.path_world[self.path_index]
        dx, dz = tx - self.world_x, tz - self.world_z
        dist = math.hypot(dx, dz)

        speed = 3.0 * dt
        if dist < 0.5:
            self.world_x, self.world_z = tx, tz
            if self.path_index < len(self.path_nodes):
                self.current_node = self.path_nodes[self.path_index]
            self.path_index += 1
        else:
            if speed > dist:
                speed = dist
            self.world_x += (dx / dist) * speed
            self.world_z += (dz / dist) * speed

    def _wait(self, dt):
        self.idle_timer -= dt
        if self.idle_timer <= 0:
            self.state = 'idle'

    def _request_help(self):
        self.needs_help = True
        self.help_request_type = random.choice([
            'assist_patient', 'deliver_medicine', 'guide_patient'
        ])
        self.state = 'requesting_help'

    def fulfill_help(self):
        self.needs_help = False
        self.help_request_type = None
        self.state = 'idle'
        
    def get_state_dict(self):
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'world_x': self.world_x,
            'world_z': self.world_z,
            'state': self.state,
            'needs_help': self.needs_help,
            'current_node': self.current_node
        }
