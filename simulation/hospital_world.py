"""
hospital_world.py -- Industrial Digital Twin Hospital Environment
Inspired by NVIDIA Isaac Sim warehouse digital twins.
Concrete floors, visible walls, industrial lighting strips, 
furniture, equipment, and clear zone demarcation.
"""

from ursina import *
from navigation import get_all_nodes, get_graph
import math

FLOOR_Y = 0

# Industrial color palette
COLORS = {
    'floor':       color.rgb32(50, 52, 58),
    'floor_grid':  color.rgb32(60, 63, 70),
    'wall':        color.rgb32(70, 75, 85),
    'wall_top':    color.rgb32(55, 60, 70),
    'room':        color.rgb32(40, 65, 100),
    'icu':         color.rgb32(100, 35, 35),
    'pharmacy':    color.rgb32(35, 90, 55),
    'emergency':   color.rgb32(140, 70, 10),
    'waiting':     color.rgb32(80, 45, 110),
    'office':      color.rgb32(45, 70, 120),
    'reception':   color.rgb32(75, 80, 90),
    'dock':        color.rgb32(120, 105, 15),
    'mainhall':    color.rgb32(55, 58, 65),
    'entrance':    color.rgb32(65, 70, 78),
    'corridor':    color.rgb32(45, 48, 55),
    'led_blue':    color.rgb32(0, 150, 255),
    'led_red':     color.rgb32(255, 40, 40),
    'led_green':   color.rgb32(40, 255, 100),
    'led_yellow':  color.rgb32(255, 200, 40),
    'led_orange':  color.rgb32(255, 140, 20),
    'led_purple':  color.rgb32(180, 80, 255),
    'white_dim':   color.rgb32(180, 185, 195),
    'dark':        color.rgb32(25, 28, 35),
}


def _zone_color(name):
    if name.startswith('Room'): return COLORS['room'], COLORS['led_blue']
    if name.startswith('ICU') and name != 'ICU_Corr': return COLORS['icu'], COLORS['led_red']
    if name == 'Pharmacy': return COLORS['pharmacy'], COLORS['led_green']
    if name == 'EmergencyRoom': return COLORS['emergency'], COLORS['led_orange']
    if name == 'WaitingHall': return COLORS['waiting'], COLORS['led_purple']
    if name == 'StaffOffice': return COLORS['office'], COLORS['led_blue']
    if name == 'Reception': return COLORS['reception'], COLORS['led_blue']
    if name == 'ChargingDock': return COLORS['dock'], COLORS['led_yellow']
    if name == 'MainHall': return COLORS['mainhall'], COLORS['led_blue']
    if name == 'Entrance': return COLORS['entrance'], COLORS['led_blue']
    return COLORS['corridor'], COLORS['led_blue']


def _zone_size(name):
    sizes = {
        'Reception': (8, 8), 'WaitingHall': (8, 8), 'EmergencyRoom': (8, 8),
        'Pharmacy': (8, 8), 'StaffOffice': (8, 8), 'MainHall': (12, 10),
        'ChargingDock': (8, 6), 'Entrance': (8, 4), 'ICU_Corr': (20, 3),
    }
    if name in sizes: return sizes[name]
    if name.startswith('Room'): return (5, 4)
    if name.startswith('ICU'): return (6, 5)
    return (4, 4)


def _is_corridor(name):
    return (name.startswith('RoomCorr') or name.startswith('WestCorr')
            or name.startswith('EastCorr') or name == 'HallNorth')


class HospitalWorld:
    def __init__(self):
        self.room_entities = {}
        self._build()

    def _build(self):
        self._build_ground()
        self._build_zones()
        self._build_path_network()
        self._build_room_details()
        self._build_dock()
        self._build_boundary()

    # ─── Ground Plane ──────────────────────────────────────────────────
    def _build_ground(self):
        # Main concrete floor
        Entity(model='cube', scale=(200, 0.1, 200), position=(0, -0.05, 0),
               color=COLORS['floor'], unlit=True)

        # Grid lines (warehouse floor markings)
        for i in range(-50, 51, 5):
            Entity(model='cube', scale=(0.04, 0.02, 100), position=(i, 0.01, 0),
                   color=COLORS['floor_grid'], unlit=True, alpha=0.5)
            Entity(model='cube', scale=(100, 0.02, 0.04), position=(0, 0.01, i),
                   color=COLORS['floor_grid'], unlit=True, alpha=0.5)

    # ─── Zone Tiles + Walls + Labels ──────────────────────────────────
    def _build_zones(self):
        nodes = get_all_nodes()

        for name, (x, z) in nodes.items():
            zc, led = _zone_color(name)
            sx, sz = _zone_size(name)
            corr = _is_corridor(name)

            if corr:
                sx, sz = 4, 4

            # ── Floor tile ──
            tile = Entity(model='cube', scale=(sx, 0.12, sz), position=(x, 0, z),
                          color=zc, unlit=True)
            self.room_entities[name] = tile

            if corr:
                continue

            # ── LED border (4 edges) ──
            for dx, dz, lx, lz in [(0, -sz/2, sx, 0.1), (0, sz/2, sx, 0.1),
                                     (-sx/2, 0, 0.1, sz), (sx/2, 0, 0.1, sz)]:
                Entity(model='cube', scale=(lx, 0.06, lz),
                       position=(x+dx, 0.1, z+dz), color=led, unlit=True, alpha=0.85)

            # ── Walls (3 sides — leave one open as doorway) ──
            wh = 2.5
            walls = [
                (0, -sz/2, sx+0.2, 0.2),   # back
                (-sx/2, 0, 0.2, sz+0.2),   # left
                (sx/2, 0, 0.2, sz+0.2),    # right
            ]
            for dx, dz, wx, wz in walls:
                Entity(model='cube', scale=(wx, wh, wz),
                       position=(x+dx, wh/2, z+dz),
                       color=COLORS['wall'], unlit=True, alpha=0.5)

            # Front wall with doorway gap
            door_w = 2.0
            front_half = (sx - door_w) / 2
            if front_half > 0.3:
                Entity(model='cube', scale=(front_half, wh, 0.2),
                       position=(x - sx/2 + front_half/2, wh/2, z + sz/2),
                       color=COLORS['wall'], unlit=True, alpha=0.5)
                Entity(model='cube', scale=(front_half, wh, 0.2),
                       position=(x + sx/2 - front_half/2, wh/2, z + sz/2),
                       color=COLORS['wall'], unlit=True, alpha=0.5)
                # Door header
                Entity(model='cube', scale=(door_w, 0.3, 0.2),
                       position=(x, wh - 0.15, z + sz/2),
                       color=COLORS['wall'], unlit=True, alpha=0.5)

            # ── Wall top LED strip ──
            Entity(model='cube', scale=(sx+0.4, 0.06, 0.06),
                   position=(x, wh + 0.03, z - sz/2),
                   color=led, unlit=True, alpha=0.6)

            # ── Ceiling light bar ──
            Entity(model='cube', scale=(sx * 0.6, 0.04, 0.15),
                   position=(x, wh + 0.5, z),
                   color=COLORS['white_dim'], unlit=True, alpha=0.4)

            # ── Label (RCT Style Floating Badge) ──
            label = name
            bg_width = 1.8
            if name.startswith('Room'): 
                label = f"ROOM {name[4:]}"
                bg_width = 1.4
            elif name.startswith('ICU') and len(name) > 3: 
                label = f"ICU {name[3:]}"
                bg_width = 1.2
            elif name == 'ChargingDock': 
                label = 'CHARGING DOCK'
                bg_width = 2.5
            elif name == 'EmergencyRoom': 
                label = 'EMERGENCY'
                bg_width = 2.0
            elif name == 'Pharmacy':
                label = 'PHARMACY'
                bg_width = 1.8
            elif name == 'Reception':
                label = 'RECEPTION'
                bg_width = 1.8
            elif name == 'WaitingHall':
                label = 'WAITING HALL'
                bg_width = 2.0
            elif name == 'MainHall':
                label = 'MAIN HALL'
                bg_width = 1.8
            
            # Badge anchor
            badge_anchor = Entity(position=(x, wh + 1.5, z), billboard=True)
            
            # Badge background
            Entity(parent=badge_anchor, model='quad', scale=(bg_width, 0.4), 
                   color=color.rgba32(20, 25, 30, 220), unlit=True, position=(0,0,0.01))
            
            # Badge border/accent
            Entity(parent=badge_anchor, model='quad', scale=(bg_width+0.04, 0.44), 
                   color=led, unlit=True, position=(0,0,0.02), alpha=0.8)
            
            # Badge text
            Text(parent=badge_anchor, text=label, scale=3.5, 
                 color=color.rgba32(255, 255, 255, 255), 
                 origin=(0, 0), position=(0, 0, -0.01), unlit=True)

            # Post connecting badge to room
            Entity(model='cube', scale=(0.04, 1.0, 0.04), 
                   position=(x, wh + 0.5, z), color=color.rgba32(100, 100, 100, 150), unlit=True)

    # ─── Navigation Path Network ──────────────────────────────────────
    def _build_path_network(self):
        g = get_graph()
        for u, v in g.edges:
            ux, uz = g.nodes[u]['pos']
            vx, vz = g.nodes[v]['pos']
            mx, mz = (ux+vx)/2, (uz+vz)/2
            length = math.hypot(vx-ux, vz-uz)
            angle = math.degrees(math.atan2(vx-ux, vz-uz))

            # Corridor floor
            Entity(model='cube', scale=(1.5, 0.06, length),
                   position=(mx, 0.01, mz), rotation_y=angle,
                   color=COLORS['corridor'], unlit=True, alpha=0.7)

            # Center guide line
            Entity(model='cube', scale=(0.08, 0.04, length),
                   position=(mx, 0.08, mz), rotation_y=angle,
                   color=COLORS['led_blue'], unlit=True, alpha=0.4)

            # Navigation node markers
            for nx, nz in [(ux, uz), (vx, vz)]:
                Entity(model='cube', scale=(0.3, 0.04, 0.3),
                       position=(nx, 0.08, nz),
                       color=COLORS['led_blue'], unlit=True, alpha=0.3)

    # ─── Room Details (Furniture) ─────────────────────────────────────
    def _build_room_details(self):
        nodes = get_all_nodes()
        for name, (x, z) in nodes.items():
            if name.startswith('Room'):
                # Hospital bed
                Entity(model='cube', scale=(1.5, 0.35, 2.4),
                       position=(x-0.6, 0.25, z), color=COLORS['white_dim'], unlit=True)
                Entity(model='cube', scale=(1.7, 0.1, 2.6),
                       position=(x-0.6, 0.06, z), color=COLORS['dark'], unlit=True)
                # Pillow
                Entity(model='cube', scale=(1.2, 0.2, 0.5),
                       position=(x-0.6, 0.45, z+0.9), color=color.rgb32(200, 205, 215), unlit=True)
                # Side table
                Entity(model='cube', scale=(0.5, 0.6, 0.5),
                       position=(x+0.9, 0.3, z+0.4), color=COLORS['dark'], unlit=True)
                # Monitor (glowing screen)
                Entity(model='cube', scale=(0.3, 0.25, 0.04),
                       position=(x+0.9, 0.75, z+0.4), color=color.rgb32(20, 180, 220), unlit=True)

            elif name.startswith('ICU') and name != 'ICU_Corr':
                Entity(model='cube', scale=(1.3, 0.35, 2.2),
                       position=(x, 0.25, z), color=COLORS['white_dim'], unlit=True)
                # Monitor tower
                Entity(model='cube', scale=(0.2, 1.4, 0.2),
                       position=(x+1.2, 0.7, z), color=COLORS['dark'], unlit=True)
                # Vitals screen
                Entity(model='cube', scale=(0.45, 0.3, 0.04),
                       position=(x+1.2, 1.3, z), color=color.rgb32(0, 200, 80), unlit=True)
                # IV stand
                Entity(model='cube', scale=(0.06, 1.6, 0.06),
                       position=(x-1.0, 0.8, z+0.5), color=color.rgb32(150, 155, 165), unlit=True)

    # ─── Charging Dock ────────────────────────────────────────────────
    def _build_dock(self):
        nodes = get_all_nodes()
        if 'ChargingDock' not in nodes:
            return
        cx, cz = nodes['ChargingDock']

        # 5 charging pads
        for i in range(5):
            px = cx + (i-2) * 2.5
            # Pad base
            Entity(model='cube', scale=(1.8, 0.08, 2.0),
                   position=(px, 0.04, cz), color=COLORS['dark'], unlit=True)
            # Pad border
            for dx, dz, lx, lz in [(0, -1.0, 1.8, 0.06), (0, 1.0, 1.8, 0.06),
                                     (-0.9, 0, 0.06, 2.0), (0.9, 0, 0.06, 2.0)]:
                Entity(model='cube', scale=(lx, 0.04, lz),
                       position=(px+dx, 0.1, cz+dz),
                       color=COLORS['led_yellow'], unlit=True, alpha=0.7)
            # Dock number
            Text(text=f'{i+1}', scale=14, color=COLORS['led_yellow'],
                 billboard=True, unlit=True,
                 position=(px, 0.5, cz-1.2), origin=(0, 0))
            # Connector post
            Entity(model='cube', scale=(0.25, 0.5, 0.25),
                   position=(px, 0.25, cz+0.9), color=COLORS['wall'], unlit=True)

    # ─── Boundary Walls ───────────────────────────────────────────────
    def _build_boundary(self):
        bh = 4.0
        bounds = [
            (0, 42, 90, 0.3),    # north
            (0, -37, 90, 0.3),   # south
            (-45, 2, 0.3, 82),   # west
            (45, 2, 0.3, 82),    # east
        ]
        for bx, bz, bsx, bsz in bounds:
            Entity(model='cube', scale=(bsx, bh, bsz),
                   position=(bx, bh/2, bz),
                   color=COLORS['wall_top'], unlit=True, alpha=0.35)
            # Top edge glow
            Entity(model='cube', scale=(bsx+0.2, 0.05, bsz+0.2),
                   position=(bx, bh, bz),
                   color=COLORS['led_blue'], unlit=True, alpha=0.25)

        # Corner pillars with beacon lights
        for sx in [-1, 1]:
            for sz in [-1, 1]:
                px, pz = sx * 44, sz * 40 + (2 if sz == 1 else -35 + 3)
                Entity(model='cube', scale=(0.5, bh+1, 0.5),
                       position=(px, (bh+1)/2, pz),
                       color=COLORS['wall'], unlit=True)
                Entity(model='sphere', scale=0.35,
                       position=(px, bh+1.5, pz),
                       color=COLORS['led_blue'], unlit=True, alpha=0.6)

    def get_room_entity(self, room_name):
        return self.room_entities.get(room_name)
