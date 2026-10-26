"""
FARSverse World Builder & Navigation Model
Defines environments, room geometry, corridor graphs, dynamic obstacles, and A* pathfinding.
"""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx


def point_segment_distance(px: float, pz: float, x1: float, z1: float, x2: float, z2: float) -> float:
    """Perpendicular or endpoint distance from point (px, pz) to line segment (x1, z1)-(x2, z2)."""
    dx = x2 - x1
    dz = z2 - z1
    seg_len_sq = dx * dx + dz * dz
    if seg_len_sq < 1e-6:
        return math.hypot(px - x1, pz - z1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (pz - z1) * dz) / seg_len_sq))
    proj_x = x1 + t * dx
    proj_z = z1 + t * dz
    return math.hypot(px - proj_x, pz - proj_z)


def segment_intersects_box(x1: float, z1: float, x2: float, z2: float,
                           bx: float, bz: float, bw: float, bd: float, margin: float = 0.6) -> bool:
    """Check if the segment (x1,z1)->(x2,z2) penetrates a bounding box with a safety margin."""
    min_x = bx - (bw / 2.0) - margin
    max_x = bx + (bw / 2.0) + margin
    min_z = bz - (bd / 2.0) - margin
    max_z = bz + (bd / 2.0) + margin

    # Fast reject if segment bbox doesn't overlap
    if max(x1, x2) < min_x or min(x1, x2) > max_x:
        return False
    if max(z1, z2) < min_z or min(z1, z2) > max_z:
        return False

    # Check closest distance to box center
    dist = point_segment_distance(bx, bz, x1, z1, x2, z2)
    threshold = math.hypot(bw / 2.0 + margin, bd / 2.0 + margin)
    return dist < threshold


class EnvironmentTemplate:
    """Factory creating world layouts, room geometries, corridors, and default obstacles."""

    @staticmethod
    def get_hospital() -> Dict[str, Any]:
        nodes: Dict[str, Tuple[float, float]] = {
            'Entrance':        (0.0, -30.0),
            'Reception':       (0.0, -20.0),
            'ChargingDock':    (0.0, -10.0),
            'MainHall':        (0.0, 0.0),
            'HallNorth':       (0.0, 15.0),
            'WestCorr1':       (-20.0, 0.0),
            'WestCorr2':       (-20.0, 15.0),
            'Pharmacy':        (-30.0, 0.0),
            'StaffOffice':     (-30.0, 15.0),
            'EastCorr1':       (20.0, 0.0),
            'EastCorr2':       (20.0, 15.0),
            'WaitingHall':     (30.0, 0.0),
            'EmergencyRoom':   (30.0, 15.0),
            'ICU_Corr':        (0.0, 28.0),
            'ICU1':            (-12.0, 32.0),
            'ICU2':            (-4.0, 32.0),
            'ICU3':            (4.0, 32.0),
            'ICU4':            (12.0, 32.0),
            'RoomCorrW1':      (-20.0, -10.0),
            'RoomCorrW2':      (-20.0, -20.0),
            'RoomCorrE1':      (20.0, -10.0),
            'RoomCorrE2':      (20.0, -20.0),
        }

        # 10 West Patient Rooms
        for i in range(1, 11):
            row = (i - 1) // 2
            side = -1 if (i % 2 == 1) else 1
            x = -28.0 + side * 6.0
            z = -8.0 - row * 5.0
            nodes[f'Room{i}'] = (x, z)

        # 10 East Patient Rooms
        for i in range(11, 21):
            row = (i - 11) // 2
            side = -1 if (i % 2 == 1) else 1
            x = 22.0 + side * 6.0
            z = -8.0 - row * 5.0
            nodes[f'Room{i}'] = (x, z)

        edges: List[Tuple[str, str]] = [
            ('Entrance', 'Reception'),
            ('Reception', 'ChargingDock'),
            ('ChargingDock', 'MainHall'),
            ('Reception', 'MainHall'),
            ('MainHall', 'HallNorth'),
            ('MainHall', 'WestCorr1'),
            ('WestCorr1', 'Pharmacy'),
            ('WestCorr1', 'WestCorr2'),
            ('WestCorr2', 'StaffOffice'),
            ('HallNorth', 'WestCorr2'),
            ('MainHall', 'EastCorr1'),
            ('EastCorr1', 'WaitingHall'),
            ('EastCorr1', 'EastCorr2'),
            ('EastCorr2', 'EmergencyRoom'),
            ('HallNorth', 'EastCorr2'),
            ('HallNorth', 'ICU_Corr'),
            ('ICU_Corr', 'ICU1'),
            ('ICU_Corr', 'ICU2'),
            ('ICU_Corr', 'ICU3'),
            ('ICU_Corr', 'ICU4'),
            ('WestCorr1', 'RoomCorrW1'),
            ('RoomCorrW1', 'RoomCorrW2'),
            ('EastCorr1', 'RoomCorrE1'),
            ('RoomCorrE1', 'RoomCorrE2'),
        ]

        for i in range(1, 6):
            edges.append(('RoomCorrW1', f'Room{i}'))
        for i in range(6, 11):
            edges.append(('RoomCorrW2', f'Room{i}'))
        for i in range(11, 16):
            edges.append(('RoomCorrE1', f'Room{i}'))
        for i in range(16, 21):
            edges.append(('RoomCorrE2', f'Room{i}'))

        rooms: List[Dict[str, Any]] = [
            {'id': 'Reception', 'name': 'Main Reception', 'type': 'reception', 'x': 0.0, 'z': -20.0, 'width': 8.0, 'depth': 8.0, 'color': '#3b82f6'},
            {'id': 'WaitingHall', 'name': 'Waiting Hall', 'type': 'waiting', 'x': 30.0, 'z': 0.0, 'width': 8.0, 'depth': 8.0, 'color': '#8b5cf6'},
            {'id': 'EmergencyRoom', 'name': 'Emergency Department', 'type': 'emergency', 'x': 30.0, 'z': 15.0, 'width': 8.0, 'depth': 8.0, 'color': '#ef4444'},
            {'id': 'Pharmacy', 'name': 'Pharmacy', 'type': 'pharmacy', 'x': -30.0, 'z': 0.0, 'width': 8.0, 'depth': 8.0, 'color': '#10b981'},
            {'id': 'StaffOffice', 'name': 'Staff Office', 'type': 'office', 'x': -30.0, 'z': 15.0, 'width': 8.0, 'depth': 8.0, 'color': '#6366f1'},
            {'id': 'ChargingDock', 'name': 'Charging Dock', 'type': 'dock', 'x': 0.0, 'z': -10.0, 'width': 8.0, 'depth': 6.0, 'color': '#f59e0b'},
            {'id': 'MainHall', 'name': 'Main Central Atrium', 'type': 'mainhall', 'x': 0.0, 'z': 0.0, 'width': 12.0, 'depth': 10.0, 'color': '#64748b'},
            {'id': 'Entrance', 'name': 'Main Entrance', 'type': 'entrance', 'x': 0.0, 'z': -30.0, 'width': 8.0, 'depth': 4.0, 'color': '#475569'},
            {'id': 'ICU1', 'name': 'ICU Ward 1', 'type': 'icu', 'x': -12.0, 'z': 32.0, 'width': 6.0, 'depth': 5.0, 'color': '#dc2626'},
            {'id': 'ICU2', 'name': 'ICU Ward 2', 'type': 'icu', 'x': -4.0, 'z': 32.0, 'width': 6.0, 'depth': 5.0, 'color': '#dc2626'},
            {'id': 'ICU3', 'name': 'ICU Ward 3', 'type': 'icu', 'x': 4.0, 'z': 32.0, 'width': 6.0, 'depth': 5.0, 'color': '#dc2626'},
            {'id': 'ICU4', 'name': 'ICU Ward 4', 'type': 'icu', 'x': 12.0, 'z': 32.0, 'width': 6.0, 'depth': 5.0, 'color': '#dc2626'},
        ]

        for i in range(1, 21):
            px, pz = nodes[f'Room{i}']
            rooms.append({
                'id': f'Room{i}',
                'name': f'Patient Room {i}',
                'type': 'patient_room',
                'x': px,
                'z': pz,
                'width': 5.0,
                'depth': 4.0,
                'color': '#0284c7'
            })

        obstacles: List[Dict[str, Any]] = [
            {'id': 'obs_trolley_1', 'name': 'Medical Trolley', 'x': -10.0, 'z': 0.0, 'width': 1.6, 'depth': 1.2, 'active': False, 'desc': 'West Corridor Trolley'},
            {'id': 'obs_maintenance_1', 'name': 'Wet Floor Sign', 'x': 10.0, 'z': 0.0, 'width': 1.2, 'depth': 1.2, 'active': False, 'desc': 'East Corridor Maintenance'},
            {'id': 'obs_bench_1', 'name': 'Waiting Bench', 'x': 26.0, 'z': -3.0, 'width': 2.5, 'depth': 1.0, 'active': True, 'desc': 'Waiting Area Seating'},
            {'id': 'obs_desk_1', 'name': 'Reception Counter', 'x': 0.0, 'z': -18.0, 'width': 4.0, 'depth': 1.2, 'active': True, 'desc': 'Main Reception Desk'},
        ]

        return {
            'environment_type': 'hospital',
            'name': 'FARS General Hospital',
            'nodes': nodes,
            'edges': edges,
            'rooms': rooms,
            'obstacles': obstacles,
            'charging_dock': (0.0, -10.0)
        }

    @staticmethod
    def get_campus() -> Dict[str, Any]:
        nodes = {
            'Entrance':      (0.0, -25.0),
            'MainPlaza':     (0.0, 0.0),
            'AcademicHall':  (-20.0, 10.0),
            'Library':       (20.0, 10.0),
            'AdminBuilding': (0.0, 25.0),
            'Cafeteria':     (-20.0, -15.0),
            'TechLab':       (20.0, -15.0),
            'ChargingDock':  (0.0, -10.0),
        }
        edges = [
            ('Entrance', 'ChargingDock'),
            ('ChargingDock', 'MainPlaza'),
            ('MainPlaza', 'AcademicHall'),
            ('MainPlaza', 'Library'),
            ('MainPlaza', 'AdminBuilding'),
            ('MainPlaza', 'Cafeteria'),
            ('MainPlaza', 'TechLab'),
            ('AcademicHall', 'AdminBuilding'),
            ('Library', 'AdminBuilding'),
            ('Cafeteria', 'Entrance'),
            ('TechLab', 'Entrance'),
        ]
        rooms = [
            {'id': 'MainPlaza', 'name': 'Central Quad Plaza', 'type': 'mainhall', 'x': 0.0, 'z': 0.0, 'width': 16.0, 'depth': 16.0, 'color': '#059669'},
            {'id': 'AcademicHall', 'name': 'Academic Complex', 'type': 'office', 'x': -20.0, 'z': 10.0, 'width': 10.0, 'depth': 10.0, 'color': '#2563eb'},
            {'id': 'Library', 'name': 'Central Science Library', 'type': 'waiting', 'x': 20.0, 'z': 10.0, 'width': 10.0, 'depth': 10.0, 'color': '#7c3aed'},
            {'id': 'AdminBuilding', 'name': 'Administration Center', 'type': 'reception', 'x': 0.0, 'z': 25.0, 'width': 12.0, 'depth': 8.0, 'color': '#475569'},
            {'id': 'Cafeteria', 'name': 'Campus Dining Hall', 'type': 'pharmacy', 'x': -20.0, 'z': -15.0, 'width': 10.0, 'depth': 8.0, 'color': '#d97706'},
            {'id': 'TechLab', 'name': 'Robotics Research Lab', 'type': 'icu', 'x': 20.0, 'z': -15.0, 'width': 10.0, 'depth': 8.0, 'color': '#0891b2'},
            {'id': 'ChargingDock', 'name': 'Solar Charging Hub', 'type': 'dock', 'x': 0.0, 'z': -10.0, 'width': 6.0, 'depth': 4.0, 'color': '#eab308'},
            {'id': 'Entrance', 'name': 'South Gate Checkpoint', 'type': 'entrance', 'x': 0.0, 'z': -25.0, 'width': 8.0, 'depth': 4.0, 'color': '#334155'},
        ]
        obstacles = [
            {'id': 'obs_statue', 'name': 'Campus Fountain', 'x': 0.0, 'z': 5.0, 'width': 3.0, 'depth': 3.0, 'active': True, 'desc': 'Central Plaza Water Fountain'},
        ]
        return {
            'environment_type': 'campus',
            'name': 'FARS Innovation Campus',
            'nodes': nodes,
            'edges': edges,
            'rooms': rooms,
            'obstacles': obstacles,
            'charging_dock': (0.0, -10.0)
        }

    @staticmethod
    def get_warehouse() -> Dict[str, Any]:
        nodes = {
            'InboundDock':    (-25.0, -20.0),
            'OutboundDock':   (25.0, -20.0),
            'MainCrossway':   (0.0, -20.0),
            'ChargingDock':   (0.0, -10.0),
            'CenterHall':     (0.0, 0.0),
            'Aisle1':         (-20.0, 10.0),
            'Aisle2':         (-10.0, 10.0),
            'Aisle3':         (0.0, 10.0),
            'Aisle4':         (10.0, 10.0),
            'Aisle5':         (20.0, 10.0),
            'SortingStation': (-15.0, 25.0),
            'PackingHub':     (15.0, 25.0),
        }
        edges = [
            ('InboundDock', 'MainCrossway'),
            ('MainCrossway', 'OutboundDock'),
            ('MainCrossway', 'ChargingDock'),
            ('ChargingDock', 'CenterHall'),
            ('CenterHall', 'Aisle1'),
            ('CenterHall', 'Aisle2'),
            ('CenterHall', 'Aisle3'),
            ('CenterHall', 'Aisle4'),
            ('CenterHall', 'Aisle5'),
            ('Aisle1', 'SortingStation'),
            ('Aisle2', 'SortingStation'),
            ('Aisle4', 'PackingHub'),
            ('Aisle5', 'PackingHub'),
            ('SortingStation', 'PackingHub'),
        ]
        rooms = [
            {'id': 'InboundDock', 'name': 'Inbound Receiving Dock', 'type': 'dock', 'x': -25.0, 'z': -20.0, 'width': 10.0, 'depth': 8.0, 'color': '#0284c7'},
            {'id': 'OutboundDock', 'name': 'Outbound Dispatch Dock', 'type': 'dock', 'x': 25.0, 'z': -20.0, 'width': 10.0, 'depth': 8.0, 'color': '#0284c7'},
            {'id': 'ChargingDock', 'name': 'Automated Fleet Depot', 'type': 'dock', 'x': 0.0, 'z': -10.0, 'width': 8.0, 'depth': 6.0, 'color': '#eab308'},
            {'id': 'SortingStation', 'name': 'High-Speed Sorter', 'type': 'pharmacy', 'x': -15.0, 'z': 25.0, 'width': 12.0, 'depth': 8.0, 'color': '#16a34a'},
            {'id': 'PackingHub', 'name': 'Automated Packing Cell', 'type': 'office', 'x': 15.0, 'z': 25.0, 'width': 12.0, 'depth': 8.0, 'color': '#9333ea'},
            {'id': 'Aisle1', 'name': 'Storage Racks A1', 'type': 'mainhall', 'x': -20.0, 'z': 10.0, 'width': 6.0, 'depth': 12.0, 'color': '#475569'},
            {'id': 'Aisle2', 'name': 'Storage Racks A2', 'type': 'mainhall', 'x': -10.0, 'z': 10.0, 'width': 6.0, 'depth': 12.0, 'color': '#475569'},
            {'id': 'Aisle3', 'name': 'Storage Racks A3', 'type': 'mainhall', 'x': 0.0, 'z': 10.0, 'width': 6.0, 'depth': 12.0, 'color': '#475569'},
            {'id': 'Aisle4', 'name': 'Storage Racks A4', 'type': 'mainhall', 'x': 10.0, 'z': 10.0, 'width': 6.0, 'depth': 12.0, 'color': '#475569'},
            {'id': 'Aisle5', 'name': 'Storage Racks A5', 'type': 'mainhall', 'x': 20.0, 'z': 10.0, 'width': 6.0, 'depth': 12.0, 'color': '#475569'},
        ]
        obstacles = [
            {'id': 'obs_pallet_1', 'name': 'Staged Pallet', 'x': -5.0, 'z': -20.0, 'width': 2.0, 'depth': 2.0, 'active': False, 'desc': 'Unloaded Wooden Pallet'},
        ]
        return {
            'environment_type': 'warehouse',
            'name': 'FARS Logistics Fulfillment Center',
            'nodes': nodes,
            'edges': edges,
            'rooms': rooms,
            'obstacles': obstacles,
            'charging_dock': (0.0, -10.0)
        }

    @staticmethod
    def get_empty() -> Dict[str, Any]:
        nodes = {
            'Center':       (0.0, 0.0),
            'North':        (0.0, 20.0),
            'South':        (0.0, -20.0),
            'East':         (20.0, 0.0),
            'West':         (-20.0, 0.0),
            'ChargingDock': (0.0, -10.0),
        }
        edges = [
            ('Center', 'North'),
            ('Center', 'South'),
            ('Center', 'East'),
            ('Center', 'West'),
            ('Center', 'ChargingDock'),
        ]
        rooms = [
            {'id': 'Center', 'name': 'Central Workspace', 'type': 'mainhall', 'x': 0.0, 'z': 0.0, 'width': 20.0, 'depth': 20.0, 'color': '#334155'},
            {'id': 'ChargingDock', 'name': 'Docking Station', 'type': 'dock', 'x': 0.0, 'z': -10.0, 'width': 6.0, 'depth': 4.0, 'color': '#eab308'},
        ]
        return {
            'environment_type': 'empty',
            'name': 'Custom Sandbox Workspace',
            'nodes': nodes,
            'edges': edges,
            'rooms': rooms,
            'obstacles': [],
            'charging_dock': (0.0, -10.0)
        }


class FARSverseWorld:
    """Live world model containing navigable nodes, rooms, dynamic obstacles, and A* pathfinding."""

    def __init__(self, template_name: str = 'hospital'):
        self.template_name = template_name
        self.load_template(template_name)

    def load_template(self, template_name: str) -> None:
        if template_name == 'hospital':
            data = EnvironmentTemplate.get_hospital()
        elif template_name == 'campus':
            data = EnvironmentTemplate.get_campus()
        elif template_name == 'warehouse':
            data = EnvironmentTemplate.get_warehouse()
        else:
            data = EnvironmentTemplate.get_empty()

        self.name = data['name']
        self.environment_type = data['environment_type']
        self.nodes: Dict[str, Tuple[float, float]] = dict(data['nodes'])
        self.edges: List[Tuple[str, str]] = list(data['edges'])
        self.rooms: List[Dict[str, Any]] = list(data['rooms'])
        self.obstacles: List[Dict[str, Any]] = list(data['obstacles'])
        self.charging_dock: Tuple[float, float] = data.get('charging_dock', (0.0, -10.0))
        self._rebuild_graph()

    def _rebuild_graph(self) -> None:
        """Construct the NetworkX graph with edge weights and active obstacle filtering."""
        self.graph = nx.Graph()
        for name, pos in self.nodes.items():
            self.graph.add_node(name, pos=pos)

        active_obstacles = [obs for obs in self.obstacles if obs.get('active', True)]

        for u, v in self.edges:
            if u not in self.nodes or v not in self.nodes:
                continue
            ux, uz = self.nodes[u]
            vx, vz = self.nodes[v]

            # Check if this edge is blocked by any active obstacle
            blocked = False
            for obs in active_obstacles:
                if segment_intersects_box(ux, uz, vx, vz, obs['x'], obs['z'], obs['width'], obs['depth'], margin=0.6):
                    blocked = True
                    break

            if not blocked:
                weight = math.hypot(vx - ux, vz - uz)
                self.graph.add_edge(u, v, weight=weight)

    def add_obstacle(self, obs_id: str, name: str, x: float, z: float, width: float = 1.5, depth: float = 1.5, active: bool = True, desc: str = "") -> Dict[str, Any]:
        obs = {
            'id': obs_id,
            'name': name,
            'x': float(x),
            'z': float(z),
            'width': float(width),
            'depth': float(depth),
            'active': bool(active),
            'desc': desc
        }
        # Replace if existing
        self.obstacles = [o for o in self.obstacles if o['id'] != obs_id]
        self.obstacles.append(obs)
        self._rebuild_graph()
        return obs

    def remove_obstacle(self, obs_id: str) -> bool:
        initial_len = len(self.obstacles)
        self.obstacles = [o for o in self.obstacles if o['id'] != obs_id]
        if len(self.obstacles) != initial_len:
            self._rebuild_graph()
            return True
        return False

    def toggle_obstacle(self, obs_id: str, active: Optional[bool] = None) -> Optional[bool]:
        for obs in self.obstacles:
            if obs['id'] == obs_id:
                if active is None:
                    obs['active'] = not obs.get('active', True)
                else:
                    obs['active'] = bool(active)
                self._rebuild_graph()
                return obs['active']
        return None

    def get_closest_node(self, x: float, z: float) -> str:
        """Find the nearest graph node to coordinate (x, z)."""
        best_node = 'MainHall' if 'MainHall' in self.nodes else list(self.nodes.keys())[0]
        best_dist = float('inf')
        for node, (nx_val, nz_val) in self.nodes.items():
            dist = math.hypot(x - nx_val, z - nz_val)
            if dist < best_dist:
                best_dist = dist
                best_node = node
        return best_node

    def find_path(self, start_pos_or_node: Any, goal_pos_or_node: Any) -> Dict[str, Any]:
        """A* pathfinding from start to goal taking into account current active obstacles."""
        if isinstance(start_pos_or_node, (list, tuple)):
            start_node = self.get_closest_node(start_pos_or_node[0], start_pos_or_node[1])
        else:
            start_node = str(start_pos_or_node)

        if isinstance(goal_pos_or_node, (list, tuple)):
            goal_node = self.get_closest_node(goal_pos_or_node[0], goal_pos_or_node[1])
        else:
            goal_node = str(goal_pos_or_node)

        if start_node not in self.nodes:
            return {'success': False, 'error': f"Unknown start location '{start_node}'", 'path': [], 'waypoints': []}
        if goal_node not in self.nodes:
            return {'success': False, 'error': f"Unknown destination '{goal_node}'", 'path': [], 'waypoints': []}

        if start_node == goal_node:
            pos = self.nodes[start_node]
            return {
                'success': True,
                'path': [start_node],
                'waypoints': [[pos[0], pos[1]]],
                'distance': 0.0,
                'estimated_time': 0.0,
                'error': None
            }

        def _heuristic(u: str, v: str) -> float:
            ux, uz = self.nodes[u]
            vx, vz = self.nodes[v]
            return math.hypot(vx - ux, vz - uz)

        try:
            node_path = nx.astar_path(self.graph, start_node, goal_node, heuristic=_heuristic, weight='weight')
            waypoints = [[self.nodes[n][0], self.nodes[n][1]] for n in node_path]
            total_dist = 0.0
            for i in range(len(waypoints) - 1):
                total_dist += math.hypot(waypoints[i+1][0] - waypoints[i][0], waypoints[i+1][1] - waypoints[i][1])

            speed = 2.0  # m/s average
            est_time = total_dist / speed if speed > 0 else 0.0

            return {
                'success': True,
                'path': node_path,
                'waypoints': waypoints,
                'distance': round(total_dist, 2),
                'estimated_time': round(est_time, 1),
                'error': None
            }
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {
                'success': False,
                'path': [],
                'waypoints': [],
                'distance': 0.0,
                'estimated_time': 0.0,
                'error': f"No navigable path between '{start_node}' and '{goal_node}'. Route blocked by obstacles or disconnected."
            }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'environment_type': self.environment_type,
            'nodes': {k: list(v) for k, v in self.nodes.items()},
            'edges': [list(e) for e in self.edges],
            'rooms': self.rooms,
            'obstacles': self.obstacles,
            'charging_dock': list(self.charging_dock)
        }
