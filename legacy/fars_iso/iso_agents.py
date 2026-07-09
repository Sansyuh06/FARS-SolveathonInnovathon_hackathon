"""
iso_agents.py -- Robot & Human agent classes for FARS isometric simulation.
Enhanced with smooth physics movement, trail systems, and RL visualization data.
All FSM logic preserved from original. No rendering code here -- just state.
"""
import math, random, time as _time
from iso_navigation import find_path, get_node_position, get_all_room_nodes, get_all_nodes

# ─── Robot Agent ──────────────────────────────────────────────────────────────
ROBOT_COLORS = [
    (0, 200, 255),    # Cyan
    (255, 60, 80),    # Red
    (60, 220, 120),   # Green
    (255, 200, 50),   # Gold
    (180, 100, 255),  # Purple
]

STATE_LABELS = {
    'idle': 'IDLE', 'navigating': 'NAV', 'guiding': 'GUIDE',
    'delivering': 'DELIV', 'assisting': 'ASSIST',
    'charging': 'CHRG', 'returning': 'RTN',
}

STATE_COLORS = {
    'idle': (60, 200, 80), 'navigating': (0, 180, 255),
    'guiding': (255, 220, 50), 'delivering': (255, 160, 40),
    'assisting': (255, 120, 180), 'charging': (255, 255, 60),
    'returning': (130, 130, 140),
}

MAX_TRAIL = 30  # Max trail positions stored


class RobotAgent:
    def __init__(self, robot_id):
        self.id = robot_id
        self.color = ROBOT_COLORS[robot_id % len(ROBOT_COLORS)]
        self.state = 'idle'
        self.battery = 100.0
        self.current_node = 'ChargingDock'
        self.target_node = None
        self.task = None
        self.tasks_completed = 0

        # World position
        cx, cz = get_node_position('ChargingDock')
        self.world_x = float(cx + (robot_id - 2) * 3.0)
        self.world_z = float(cz)

        # Smooth physics
        self.vel_x = 0.0
        self.vel_z = 0.0
        self.speed = 12.0

        # Path
        self.path_nodes = []
        self.path_index = 0

        # Thought log
        self.thoughts = ['> System online.', '> Awaiting dispatch.']

        # Animation
        self.anim_time = random.uniform(0, 6)
        self.task_work_timer = 0

        # Trail system — list of (world_x, world_z) positions
        self.trail_positions = [(self.world_x, self.world_z)] * 5
        self._trail_timer = 0.0
        self._trail_interval = 0.04  # Record position every 40ms

        # RL / Neural Network visualization data
        self.reward_signal = 0.0          # 0–1, spikes on task completion
        self.episode_count = 0            # = tasks_completed for RL parlance
        self.cumulative_reward = 0.0
        # 8 "neural weights" per robot — slowly drift, pulse on state change
        self.rl_weights = [random.uniform(-1, 1) for _ in range(8)]
        self._weight_targets = [random.uniform(-1, 1) for _ in range(8)]
        self._weight_timer = 0.0

        # Visual: tread animation offset
        self.tread_offset = 0.0

    # ─── Thoughts ─────────────────────────────────────────────────────────────
    def add_thought(self, msg):
        self.thoughts.append(f'> {msg}')
        if len(self.thoughts) > 10:
            self.thoughts = self.thoughts[-10:]

    # ─── Availability ─────────────────────────────────────────────────────────
    def is_available(self):
        return self.state == 'idle' and self.battery > 15

    # ─── Task Assignment ──────────────────────────────────────────────────────
    def assign_task(self, task):
        self.task = task
        self.target_node = task.location_node
        self.path_nodes = find_path(self.current_node, self.target_node)
        self.path_index = 0
        self.state = 'navigating'
        # Boost weights visually
        self._weight_targets = [random.uniform(-1, 1) for _ in range(8)]
        self.add_thought(f'Dispatched -> {task.location_node} [{task.task_type}]')

    # ─── Main Update ──────────────────────────────────────────────────────────
    def update(self, dt):
        self.anim_time += dt
        self._update_rl_data(dt)
        self._update_trail(dt)

        # Tread animation when moving
        if self.state in ('navigating', 'returning'):
            self.tread_offset = (self.tread_offset + dt * 80) % 10

        # Decay reward signal
        self.reward_signal = max(0.0, self.reward_signal - dt * 1.5)

        if self.state == 'charging':
            self.battery = min(100, self.battery + 8 * dt)
            if self.battery >= 100:
                self.state = 'idle'
                self.add_thought('Battery full. Standing by.')
            return

        if self.state == 'navigating':
            self._move(dt)
        elif self.state == 'returning':
            self._move(dt)
        elif self.state in ('guiding', 'delivering', 'assisting'):
            self.task_work_timer -= dt
            if self.task_work_timer <= 0:
                self._finish_task()

    def _update_rl_data(self, dt):
        """Slowly drift neural weights toward targets for animation."""
        self._weight_timer += dt
        if self._weight_timer > 2.0:
            self._weight_targets = [random.uniform(-1, 1) for _ in range(8)]
            self._weight_timer = 0

        for i in range(8):
            self.rl_weights[i] += (self._weight_targets[i] - self.rl_weights[i]) * min(1, dt * 1.5)

    def _update_trail(self, dt):
        """Record world position at intervals for trail rendering."""
        if self.state in ('navigating', 'returning', 'guiding', 'delivering', 'assisting'):
            self._trail_timer += dt
            if self._trail_timer >= self._trail_interval:
                self._trail_timer = 0
                pos = (self.world_x, self.world_z)
                self.trail_positions.append(pos)
                if len(self.trail_positions) > MAX_TRAIL:
                    self.trail_positions.pop(0)
        else:
            # Slowly shrink trail when stopped
            if len(self.trail_positions) > 3:
                self._trail_timer += dt
                if self._trail_timer >= 0.1:
                    self._trail_timer = 0
                    self.trail_positions.pop(0)

    # ─── Movement (smooth physics) ────────────────────────────────────────────
    def _move(self, dt):
        if not self.path_nodes or self.path_index >= len(self.path_nodes):
            self._arrive()
            return

        target = self.path_nodes[self.path_index]
        tx, tz = get_node_position(target)

        dx = tx - self.world_x
        dz = tz - self.world_z
        dist = math.hypot(dx, dz)

        if dist < 0.25:
            self.world_x, self.world_z = float(tx), float(tz)
            self.current_node = target
            self.path_index += 1
            self.vel_x *= 0.5
            self.vel_z *= 0.5
        else:
            # Smooth acceleration toward waypoint
            target_vx = (dx / dist) * self.speed
            target_vz = (dz / dist) * self.speed
            accel = 30.0
            self.vel_x += (target_vx - self.vel_x) * min(1, accel * dt)
            self.vel_z += (target_vz - self.vel_z) * min(1, accel * dt)

            step = min(self.speed * dt, dist)
            # Clamp velocity to step
            v_mag = math.hypot(self.vel_x, self.vel_z)
            if v_mag > self.speed:
                self.vel_x = (self.vel_x / v_mag) * self.speed
                self.vel_z = (self.vel_z / v_mag) * self.speed

            self.world_x += self.vel_x * dt
            self.world_z += self.vel_z * dt

        self.battery = max(0, self.battery - 0.04 * dt)
        if self.battery <= 0:
            self.add_thought('BATTERY CRITICAL!')
            self._abort_charge()

    def _arrive(self):
        if self.state == 'returning':
            self.state = 'charging'
            self.add_thought('Docked. Charging...')
            return

        if self.task:
            work_state = {
                'guide_patient': 'guiding',
                'deliver_medicine': 'delivering',
                'assist_patient': 'assisting',
            }.get(self.task.task_type, 'assisting')
            self.state = work_state
            self.task_work_timer = 3.0
            self.add_thought(f'Executing: {self.task.task_type}')
        else:
            self.state = 'idle'

    def _finish_task(self):
        if self.task:
            self.task.status = 'completed'
            self.task.completed_time = _time.time()
            self.tasks_completed += 1
            self.episode_count = self.tasks_completed
            self.cumulative_reward += 1.0
            self.reward_signal = 1.0  # Spike reward signal!
            # Randomize weights more aggressively on completion
            self._weight_targets = [random.uniform(-1, 1) for _ in range(8)]
            self.add_thought(f'Task done at {self.task.location_node}.')
            self.task = None

        if self.battery < 20:
            self._abort_charge()
        else:
            self.state = 'idle'
            self.add_thought('Ready for next dispatch.')

    def _abort_charge(self):
        if self.task:
            self.task.status = 'pending'
            self.task = None
        self.state = 'returning'
        self.target_node = 'ChargingDock'
        self.path_nodes = find_path(self.current_node, 'ChargingDock')
        self.path_index = 0
        self.add_thought('Returning to dock...')

    # ─── Helpers ──────────────────────────────────────────────────────────────
    def get_state_label(self):
        return STATE_LABELS.get(self.state, self.state.upper())

    def get_state_color(self):
        return STATE_COLORS.get(self.state, (150, 150, 150))

    def get_path_world_coords(self):
        """Return list of (x, z) for remaining path for trail rendering."""
        if not self.path_nodes:
            return []
        coords = [(self.world_x, self.world_z)]
        for i in range(self.path_index, len(self.path_nodes)):
            coords.append(get_node_position(self.path_nodes[i]))
        return coords

    def get_velocity(self):
        """Return (vx, vz) for visualizing movement direction."""
        return self.vel_x, self.vel_z


# ─── Human Agent ──────────────────────────────────────────────────────────────
HUMAN_COLORS = {
    'patient': (200, 220, 255),
    'doctor':  (60, 160, 255),
    'nurse':   (255, 140, 200),
    'visitor': (255, 180, 80),
}

HUMAN_LOCATIONS = {
    'doctor':  ['MainHall', 'ICU1', 'ICU2', 'ICU3', 'ICU4', 'EmergencyRoom'],
    'nurse':   ['Pharmacy', 'MainHall', 'WaitingHall', 'Reception'],
    'visitor': ['Reception', 'WaitingHall', 'MainHall'],
}


class HumanAgent:
    def __init__(self, agent_type, home_node=None):
        self.agent_type = agent_type
        self.color = HUMAN_COLORS.get(agent_type, (200, 200, 200))

        rooms = get_all_room_nodes()
        if home_node:
            self.home_node = home_node
        elif agent_type in HUMAN_LOCATIONS:
            self.home_node = random.choice(HUMAN_LOCATIONS[agent_type])
        else:
            self.home_node = random.choice(rooms)

        self.current_node = self.home_node

        hx, hz = get_node_position(self.current_node)
        self.world_x = hx + random.uniform(-1.5, 1.5)
        self.world_z = hz + random.uniform(-1.5, 1.5)

        # Smooth velocity
        self.vel_x = 0.0
        self.vel_z = 0.0

        self.needs_help = False
        self.help_request_type = None

        self.path_nodes = []
        self.path_index = 0

        self.idle_timer = random.uniform(4, 12)
        self.help_timer = random.uniform(15, 60) if agent_type == 'patient' else 9999
        self.anim_time = random.uniform(0, 6)

        # Position offset (slight random per human for natural clustering)
        self._offset_x = random.uniform(-0.8, 0.8)
        self._offset_z = random.uniform(-0.8, 0.8)

    def update(self, dt):
        self.anim_time += dt

        if self.path_nodes and self.path_index < len(self.path_nodes):
            self._move(dt)
        else:
            self.path_nodes = []
            self.vel_x *= 0.8
            self.vel_z *= 0.8
            self.idle_timer -= dt
            if self.idle_timer <= 0:
                self._wander()

        if self.agent_type == 'patient':
            self.help_timer -= dt
            if self.help_timer <= 0 and not self.needs_help:
                self._request_help()

    def _move(self, dt):
        target = self.path_nodes[self.path_index]
        tx, tz = get_node_position(target)
        # Add small offset for natural movement
        tx += self._offset_x * 0.5
        tz += self._offset_z * 0.5

        dx = tx - self.world_x
        dz = tz - self.world_z
        dist = math.hypot(dx, dz)

        speed = 4.5

        if dist < 0.5:
            self.current_node = target
            self.path_index += 1
        else:
            # Smooth velocity
            target_vx = (dx / dist) * speed
            target_vz = (dz / dist) * speed
            self.vel_x += (target_vx - self.vel_x) * min(1, 10 * dt)
            self.vel_z += (target_vz - self.vel_z) * min(1, 10 * dt)
            self.world_x += self.vel_x * dt
            self.world_z += self.vel_z * dt

    def _wander(self):
        all_nodes = list(get_all_nodes().keys())
        if self.agent_type in HUMAN_LOCATIONS:
            # Prefer role-appropriate locations
            candidates = HUMAN_LOCATIONS[self.agent_type] + [self.home_node]
        elif self.agent_type == 'patient':
            candidates = [self.home_node, 'WaitingHall', 'MainHall', self.home_node]
        else:
            candidates = all_nodes

        target = random.choice(candidates)
        path = find_path(self.current_node, target)
        if path and len(path) > 1:
            self.path_nodes = path
            self.path_index = 0
        self.idle_timer = random.uniform(6, 18)

    def _request_help(self):
        self.needs_help = True
        self.help_request_type = random.choice(['assist_patient', 'deliver_medicine', 'guide_patient'])
        self.help_timer = random.uniform(50, 120)

    def fulfill_help(self):
        self.needs_help = False
        self.help_request_type = None

    def get_velocity(self):
        return self.vel_x, self.vel_z
