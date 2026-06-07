"""
navigation.py -- Hospital Navigation Graph & A* Pathfinding Engine
Defines the hospital layout as a networkx graph and provides shortest-path routing.
"""

import networkx as nx
import math

# ---------------------------------------------------------------------------
# Hospital Graph Definition
# ---------------------------------------------------------------------------

def build_hospital_graph():
    """Build the hospital navigation graph. Each node has (x, z) world coords."""
    G = nx.Graph()

    # --- Node positions  (x, z) on the world plane ---
    nodes = {
        # Main spine
        'Entrance':        (0, -30),
        'Reception':       (0, -20),
        'MainHall':        (0, 0),
        'HallNorth':       (0, 15),

        # West wing
        'WestCorr1':       (-20, 0),
        'WestCorr2':       (-20, 15),
        'Pharmacy':        (-30, 0),
        'StaffOffice':     (-30, 15),

        # East wing
        'EastCorr1':       (20, 0),
        'EastCorr2':       (20, 15),
        'WaitingHall':     (30, 0),
        'EmergencyRoom':   (30, 15),

        # ICU corridor (north)
        'ICU_Corr':        (0, 28),
        'ICU1':            (-12, 32),
        'ICU2':            (-4, 32),
        'ICU3':            (4, 32),
        'ICU4':            (12, 32),

        # Charging dock
        'ChargingDock':    (0, -10),

        # --- Patient rooms (west block, rooms 1-10) ---
        'RoomCorrW1':      (-20, -10),
        'RoomCorrW2':      (-20, -20),
    }

    # Generate room nodes for west wing (rooms 1-10)
    for i in range(1, 11):
        row = (i - 1) // 2
        side = -1 if (i % 2 == 1) else 1
        x = -28 + side * 6
        z = -8 - row * 5
        nodes[f'Room{i}'] = (x, z)

    # Corridor nodes for east rooms
    nodes['RoomCorrE1'] = (20, -10)
    nodes['RoomCorrE2'] = (20, -20)

    # Generate room nodes for east wing (rooms 11-20)
    for i in range(11, 21):
        row = (i - 11) // 2
        side = -1 if (i % 2 == 1) else 1
        x = 22 + side * 6
        z = -8 - row * 5
        nodes[f'Room{i}'] = (x, z)

    # Add all nodes
    for name, pos in nodes.items():
        G.add_node(name, pos=pos)

    # --- Edges (corridors) ---
    edges = [
        # Main spine
        ('Entrance', 'Reception'),
        ('Reception', 'ChargingDock'),
        ('ChargingDock', 'MainHall'),
        ('Reception', 'MainHall'),
        ('MainHall', 'HallNorth'),

        # West wing
        ('MainHall', 'WestCorr1'),
        ('WestCorr1', 'Pharmacy'),
        ('WestCorr1', 'WestCorr2'),
        ('WestCorr2', 'StaffOffice'),
        ('HallNorth', 'WestCorr2'),

        # East wing
        ('MainHall', 'EastCorr1'),
        ('EastCorr1', 'WaitingHall'),
        ('EastCorr1', 'EastCorr2'),
        ('EastCorr2', 'EmergencyRoom'),
        ('HallNorth', 'EastCorr2'),

        # ICU
        ('HallNorth', 'ICU_Corr'),
        ('ICU_Corr', 'ICU1'),
        ('ICU_Corr', 'ICU2'),
        ('ICU_Corr', 'ICU3'),
        ('ICU_Corr', 'ICU4'),

        # West room corridors
        ('WestCorr1', 'RoomCorrW1'),
        ('RoomCorrW1', 'RoomCorrW2'),
    ]

    # Connect west rooms to their corridor
    for i in range(1, 6):
        edges.append(('RoomCorrW1', f'Room{i}'))
    for i in range(6, 11):
        edges.append(('RoomCorrW2', f'Room{i}'))

    # East room corridors
    edges.append(('EastCorr1', 'RoomCorrE1'))
    edges.append(('RoomCorrE1', 'RoomCorrE2'))

    for i in range(11, 16):
        edges.append(('RoomCorrE1', f'Room{i}'))
    for i in range(16, 21):
        edges.append(('RoomCorrE2', f'Room{i}'))

    # Compute edge weights as Euclidean distance
    for u, v in edges:
        ux, uz = nodes[u]
        vx, vz = nodes[v]
        w = math.hypot(vx - ux, vz - uz)
        G.add_edge(u, v, weight=w)

    return G


# ---------------------------------------------------------------------------
# Pathfinding utilities
# ---------------------------------------------------------------------------

_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_hospital_graph()
    return _graph


def heuristic(u, v):
    """Euclidean heuristic for A*."""
    g = get_graph()
    ux, uz = g.nodes[u]['pos']
    vx, vz = g.nodes[v]['pos']
    return math.hypot(vx - ux, vz - uz)


def find_path(start_node, goal_node):
    """Return list of node names from start to goal using A*."""
    g = get_graph()
    if start_node not in g or goal_node not in g:
        return []
    try:
        return nx.astar_path(g, start_node, goal_node, heuristic=heuristic, weight='weight')
    except nx.NetworkXNoPath:
        return []


def get_world_path(start_node, goal_node):
    """Return list of (x, z) world coords along the path."""
    g = get_graph()
    path_nodes = find_path(start_node, goal_node)
    return [g.nodes[n]['pos'] for n in path_nodes]


def get_node_position(node_name):
    """Return (x, z) world position of a node."""
    g = get_graph()
    if node_name in g:
        return g.nodes[node_name]['pos']
    return (0, 0)


def get_nearest_node(x, z):
    """Find the closest graph node to a world position."""
    g = get_graph()
    best = None
    best_dist = float('inf')
    for n in g.nodes:
        nx_, nz = g.nodes[n]['pos']
        d = math.hypot(nx_ - x, nz - z)
        if d < best_dist:
            best_dist = d
            best = n
    return best


def get_all_room_nodes():
    """Return list of room node names (Room1..Room20)."""
    return [f'Room{i}' for i in range(1, 21)]


def get_all_nodes():
    """Return dict of node_name -> (x,z)."""
    g = get_graph()
    return {n: g.nodes[n]['pos'] for n in g.nodes}


def get_location_node(location_name):
    """Map a friendly location name to a graph node name."""
    mapping = {
        'reception': 'Reception',
        'waiting hall': 'WaitingHall',
        'waiting': 'WaitingHall',
        'emergency': 'EmergencyRoom',
        'emergency room': 'EmergencyRoom',
        'er': 'EmergencyRoom',
        'pharmacy': 'Pharmacy',
        'staff office': 'StaffOffice',
        'office': 'StaffOffice',
        'icu': 'ICU_Corr',
        'icu1': 'ICU1',
        'icu2': 'ICU2',
        'icu3': 'ICU3',
        'icu4': 'ICU4',
        'charging': 'ChargingDock',
        'charging dock': 'ChargingDock',
        'main hall': 'MainHall',
        'entrance': 'Entrance',
    }

    loc = location_name.strip().lower()

    # Check direct mapping
    if loc in mapping:
        return mapping[loc]

    # Check room number
    import re
    m = re.search(r'room\s*(\d+)', loc)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 20:
            return f'Room{num}'

    # Fuzzy match
    for key, val in mapping.items():
        if key in loc:
            return val

    return None
