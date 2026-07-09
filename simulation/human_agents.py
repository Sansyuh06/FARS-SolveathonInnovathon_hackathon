"""
human_agents.py -- Human Agent System (Flat-Shaded, Guaranteed Render)
All entities use unlit=True for consistent rendering.
"""

from ursina import *
import random
import math
from navigation import get_node_position, get_all_room_nodes, find_path

AGENT_CONFIG = {
    'patient': {
        'body_color':  color.rgb32(200, 170, 50),
        'head_color':  color.rgb32(220, 190, 150),
        'scale': (0.6, 1.4, 0.6),
        'locations': None,
    },
    'doctor': {
        'body_color':  color.rgb32(50, 170, 90),
        'head_color':  color.rgb32(220, 190, 150),
        'scale': (0.6, 1.5, 0.6),
        'locations': ['MainHall', 'ICU1', 'ICU2', 'ICU3', 'ICU4', 'EmergencyRoom'],
    },
    'nurse': {
        'body_color':  color.rgb32(60, 140, 230),
        'head_color':  color.rgb32(220, 190, 150),
        'scale': (0.6, 1.45, 0.6),
        'locations': ['Pharmacy', 'MainHall', 'WaitingHall'],
    },
    'visitor': {
        'body_color':  color.rgb32(160, 100, 220),
        'head_color':  color.rgb32(220, 190, 150),
        'scale': (0.6, 1.4, 0.6),
        'locations': ['Reception', 'WaitingHall', 'MainHall'],
    },
}

TYPE_COLORS = {
    'patient': color.rgb32(255, 210, 90),
    'doctor':  color.rgb32(60, 220, 120),
    'nurse':   color.rgb32(80, 170, 255),
    'visitor': color.rgb32(190, 130, 255),
}


class HumanAgent:
    all_humans = []
    _id_counter = 0

    def __init__(self, agent_type, assigned_room=None):
        HumanAgent._id_counter += 1
        self.id = HumanAgent._id_counter
        self.agent_type = agent_type
        self.state = 'idle'
        self.assigned_room = assigned_room
        self.needs_help = False
        self.help_request_type = None

        config = AGENT_CONFIG[agent_type]
        if assigned_room:
            self.home_node = assigned_room
        elif config['locations']:
            self.home_node = random.choice(config['locations'])
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
        self._anim_time = random.uniform(0, 10)

        body_y = config['scale'][1] / 2 - 0.3

        # Body
        self.entity = Entity(
            model='cube', scale=config['scale'],
            position=(self.world_x, body_y, self.world_z),
            color=config['body_color'], unlit=True, alpha=0.85,
        )

        # Head
        Entity(
            model='sphere', scale=0.38,
            position=(0, 0.68, 0),
            color=config['head_color'], unlit=True,
            parent=self.entity,
        )

        # Type badge
        Entity(
            model='sphere', scale=0.1,
            position=(0, 0.3, 0.22),
            color=TYPE_COLORS[agent_type], unlit=True,
            parent=self.entity,
        )

        # Doctor stethoscope
        if agent_type == 'doctor':
            Entity(
                model='cube', scale=(0.4, 0.04, 0.04),
                position=(0, 0.45, 0.2),
                color=color.rgb32(180, 185, 195), unlit=True,
                parent=self.entity,
            )

        # Nurse cross
        if agent_type == 'nurse':
            Entity(
                model='cube', scale=(0.12, 0.04, 0.04),
                position=(0.12, 0.35, 0.2),
                color=color.rgb32(255, 60, 60), unlit=True,
                parent=self.entity,
            )
            Entity(
                model='cube', scale=(0.04, 0.12, 0.04),
                position=(0.12, 0.35, 0.2),
                color=color.rgb32(255, 60, 60), unlit=True,
                parent=self.entity,
            )

        # Shadow disc
        Entity(
            model='cube', scale=(1.0, 0.015, 1.0),
            position=(0, -body_y + 0.01, 0),
            color=color.rgb32(0, 0, 0), unlit=True, alpha=0.15,
            parent=self.entity,
        )

        # Name
        self.name_text = Text(
            text=f"{agent_type[:3].upper()}_{self.id}",
            scale=12, color=TYPE_COLORS[agent_type],
            billboard=True, unlit=True,
            parent=self.entity, position=(0, 1.5, 0), origin=(0, 0),
        )

        # Status icon
        self.status_text = Text(
            text='', scale=18, color=color.rgb32(255, 50, 50),
            billboard=True, unlit=True,
            parent=self.entity, position=(0, 2.0, 0), origin=(0, 0),
        )

        # Help glow ring
        self.help_glow = Entity(
            model='cube', scale=(1.8, 0.03, 1.8),
            position=(0, -body_y + 0.03, 0),
            color=color.rgb32(255, 50, 50), unlit=True, alpha=0,
            parent=self.entity,
        )

        HumanAgent.all_humans.append(self)

    def update(self, dt):
        self._anim_time += dt

        if self.needs_help:
            pulse = (math.sin(self._anim_time * 4) + 1) * 0.5
            self.help_glow.alpha = 0.15 + pulse * 0.25
        else:
            self.help_glow.alpha = 0

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
        config = AGENT_CONFIG[self.agent_type]
        if self.agent_type == 'patient':
            target = self.home_node if random.random() < 0.7 else random.choice(
                ['WaitingHall', 'MainHall', self.home_node])
        elif config['locations']:
            target = random.choice(config['locations'] + [self.home_node])
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
            angle = math.degrees(math.atan2(dx, dz))
            cur = self.entity.rotation_y
            diff = (angle - cur + 180) % 360 - 180
            self.entity.rotation_y += diff * min(1, dt * 6)

        bob = math.sin(self._anim_time * 8) * 0.06
        cfg = AGENT_CONFIG[self.agent_type]
        self.entity.position = (self.world_x, cfg['scale'][1] / 2 - 0.3 + bob, self.world_z)

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
        self.status_text.text = '!'

    def fulfill_help(self):
        self.needs_help = False
        self.help_request_type = None
        self.state = 'idle'
        self.status_text.text = 'OK'
        self.status_text.color = color.rgb32(80, 255, 120)
        invoke(self._clear_status, delay=3)

    def _clear_status(self):
        self.status_text.text = ''
        self.status_text.color = color.rgb32(255, 50, 50)

    def get_info(self):
        return {
            'id': self.id, 'type': self.agent_type,
            'state': self.state, 'location': self.current_node,
            'needs_help': self.needs_help,
        }
