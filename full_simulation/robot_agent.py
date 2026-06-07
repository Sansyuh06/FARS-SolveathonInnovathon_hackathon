"""
robot_agent.py -- Robot Agent System (Flat-Shaded, Guaranteed Render)
All entities use unlit=True for consistent rendering.
"""

from ursina import *
import math
import time as _time
from navigation import find_path, get_node_position

ROBOT_COLORS = [
    color.rgb32(0, 200, 255),
    color.rgb32(255, 100, 100),
    color.rgb32(100, 255, 100),
    color.rgb32(255, 200, 50),
    color.rgb32(200, 100, 255),
]

GLOW_COLORS = [
    color.rgb32(50, 220, 255),
    color.rgb32(255, 130, 130),
    color.rgb32(130, 255, 130),
    color.rgb32(255, 220, 80),
    color.rgb32(220, 130, 255),
]

STATE_ICONS = {
    'idle': 'IDLE', 'navigating': 'NAV', 'guiding': 'GUIDE',
    'delivering': 'DELIV', 'assisting': 'ASSIST',
    'charging': 'CHRG', 'returning': 'RTN',
}

STATE_COLORS = {
    'idle':       color.rgb32(80, 220, 120),
    'navigating': color.rgb32(0, 200, 255),
    'guiding':    color.rgb32(255, 215, 0),
    'delivering': color.rgb32(255, 160, 30),
    'assisting':  color.rgb32(255, 100, 180),
    'charging':   color.rgb32(255, 220, 50),
    'returning':  color.rgb32(160, 160, 170),
}

MOVE_SPEED = 8.0
BATTERY_DRAIN_RATE = 0.03
BATTERY_CHARGE_RATE = 0.15
LOW_BATTERY_THRESHOLD = 15.0
TASK_EXECUTE_TIME = 3.0
FLOOR_Y = -0.35


class RobotAgent:
    all_robots = []

    def __init__(self, robot_id, start_node='ChargingDock'):
        self.id = robot_id
        self.state = 'idle'
        self.battery = 100.0
        self.current_task = None
        self.task_history = []
        self.current_node = start_node
        self.target_node = None
        self.thought_log = ["System initialized."]
        self.path_nodes = []
        self.path_world = []
        self.path_index = 0
        self.task_timer = 0.0
        self._last_dt = 0.016
        self._anim_time = 0

        sx, sz = get_node_position(start_node)
        self.world_x = sx + (robot_id - 2) * 2.5
        self.world_z = sz

        col = ROBOT_COLORS[robot_id % len(ROBOT_COLORS)]
        glow = GLOW_COLORS[robot_id % len(GLOW_COLORS)]

        # Body
        self.entity = Entity(
            model='cube', scale=(1.4, 2.0, 1.4),
            position=(self.world_x, 0.6, self.world_z),
            color=col, unlit=True,
        )

        # Dark chest panel
        Entity(
            model='cube', scale=(0.8, 0.5, 0.04),
            position=(0, 0.1, 0.48),
            color=color.rgb32(20, 25, 35), unlit=True,
            parent=self.entity,
        )

        # Dome head
        self.dome = Entity(
            model='sphere', scale=(1.2, 0.65, 1.2),
            position=(0, 1.1, 0),
            color=color.rgb32(140, 150, 170), unlit=True,
            parent=self.entity,
        )

        # Eye sensor
        self.eye = Entity(
            model='sphere', scale=0.18,
            position=(0, 1.25, 0.5),
            color=glow, unlit=True,
            parent=self.entity,
        )

        # Antenna
        Entity(
            model='cube', scale=(0.07, 0.7, 0.07),
            position=(0, 1.6, 0),
            color=color.rgb32(100, 105, 115), unlit=True,
            parent=self.entity,
        )
        self.antenna_light = Entity(
            model='sphere', scale=0.16,
            position=(0, 2.0, 0),
            color=glow, unlit=True,
            parent=self.entity,
        )

        # Side accents
        for side in [-1, 1]:
            Entity(
                model='cube', scale=(0.04, 0.08, 0.6),
                position=(side * 0.68, 0.15, 0),
                color=glow, unlit=True, alpha=0.7,
                parent=self.entity,
            )

        # Treads
        for offset in [-0.4, 0.4]:
            Entity(
                model='cube', scale=(0.8, 0.4, 0.3),
                position=(0, -0.4, offset),
                color=color.rgb32(25, 28, 35), unlit=True,
                parent=self.entity,
            )

        # Ground glow
        self.ground_glow = Entity(
            model='cube', scale=(2.2, 0.03, 2.2),
            position=(self.world_x, FLOOR_Y + 0.05, self.world_z),
            color=STATE_COLORS['idle'], unlit=True, alpha=0.3,
        )

        # State beacon
        self.light = Entity(
            model='sphere', scale=0.3,
            position=(0, 2.3, 0),
            color=STATE_COLORS['idle'], unlit=True,
            parent=self.entity,
        )

        # ID label
        self.label = Text(
            text=f'R{robot_id + 1}', scale=2.5,
            color=color.white, billboard=True, unlit=True,
            parent=self.entity, position=(0, 2.8, 0), origin=(0, 0),
        )

        # Status text
        self.status_text = Text(
            text='IDLE', scale=12,
            color=color.white, billboard=True, unlit=True,
            parent=self.entity, position=(0, 3.5, 0), origin=(0, 0),
        )

        # Battery bar
        self.bat_bg = Entity(
            model='cube', scale=(1.8, 0.1, 0.03),
            position=(0, 3.2, 0),
            color=color.rgb32(25, 28, 35), unlit=True,
            parent=self.entity, billboard=True,
        )
        self.bat_fill = Entity(
            model='cube', scale=(1.76, 0.07, 0.02),
            position=(0, 3.2, 0.01),
            color=color.rgb32(80, 220, 120), unlit=True,
            parent=self.entity, billboard=True,
        )

        self.path_entities = []
        self.color = col
        self.glow = glow
        RobotAgent.all_robots.append(self)

    @property
    def stateIcon(self):
        return STATE_ICONS.get(self.state, '?')

    def add_thought(self, msg):
        self.thought_log.append(f"> {msg}")
        if len(self.thought_log) > 6:
            self.thought_log.pop(0)

    def set_state(self, new_state):
        if self.state != new_state:
            self.add_thought(f"{self.state.upper()} -> {new_state.upper()}")
        self.state = new_state
        self.status_text.text = STATE_ICONS.get(new_state, '?')
        sc = STATE_COLORS.get(new_state, color.white)
        self.light.color = sc
        self.ground_glow.color = sc

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
            self._draw_path()

    def _draw_path(self):
        self._clear_path()
        for i in range(len(self.path_world) - 1):
            x1, z1 = self.path_world[i]
            x2, z2 = self.path_world[i + 1]
            mx, mz = (x1 + x2) / 2, (z1 + z2) / 2
            length = math.hypot(x2 - x1, z2 - z1)
            angle = math.degrees(math.atan2(x2 - x1, z2 - z1))
            seg = Entity(
                model='cube', scale=(0.3, 0.05, length),
                position=(mx, FLOOR_Y, mz), rotation_y=angle,
                color=self.color, unlit=True, alpha=0.5,
            )
            self.path_entities.append(seg)

    def _clear_path(self):
        for e in self.path_entities:
            destroy(e)
        self.path_entities.clear()

    def update(self, dt):
        self._last_dt = dt
        self._anim_time += dt

        # Antenna pulse
        pulse = (math.sin(self._anim_time * 3 + self.id) + 1) * 0.5
        self.antenna_light.alpha = 0.4 + pulse * 0.6

        # Ground glow pulse
        if self.state not in ('idle', 'charging'):
            gp = (math.sin(self._anim_time * 2 + self.id) + 1) * 0.5
            self.ground_glow.alpha = 0.15 + gp * 0.25
        else:
            self.ground_glow.alpha = 0.12

        # Battery bar
        bp = self.battery / 100.0
        self.bat_fill.scale_x = 1.76 * bp
        if bp > 0.5:
            self.bat_fill.color = color.rgb32(80, 220, 120)
        elif bp > 0.2:
            self.bat_fill.color = color.rgb32(255, 200, 50)
        else:
            self.bat_fill.color = color.rgb32(255, 80, 80)

        self.ground_glow.position = (self.world_x, FLOOR_Y + 0.05, self.world_z)

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
            angle = math.degrees(math.atan2(dx, dz))
            cur = self.entity.rotation_y
            diff = (angle - cur + 180) % 360 - 180
            self.entity.rotation_y += diff * min(1, dt * 8)

        self.entity.position = (self.world_x, 0.6, self.world_z)
        self.battery = max(0, self.battery - BATTERY_DRAIN_RATE * dt)
        if self.battery <= 0:
            self._force_return()

    def _arrive(self):
        self._clear_path()
        if self.state == 'returning':
            self.add_thought("Docked. Charging.")
            self.set_state('charging')
            self.current_task = None
            return
        if self.current_task:
            if self.task_timer == 0:
                self.add_thought(f"Executing at {self.current_node}...")
            self.task_timer += self._last_dt
            if self.task_timer >= TASK_EXECUTE_TIME:
                self._complete_task()
                self.task_timer = 0

    def _complete_task(self):
        if self.current_task:
            self.add_thought("Task complete.")
            self.current_task.status = 'completed'
            self.current_task.completed_time = _time.time()
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
        self._draw_path()

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

    def get_info(self):
        return {
            'id': f'R{self.id + 1}',
            'state': self.state,
            'battery': round(self.battery, 1),
            'current_task': str(self.current_task) if self.current_task else 'None',
            'location': self.current_node,
            'tasks_completed': len(self.task_history),
            'thoughts': '\n'.join(self.thought_log),
        }
