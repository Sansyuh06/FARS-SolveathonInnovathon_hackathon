"""
digital_twin_3d.py -- FARS Hospital Digital Twin: Complete Single-File 3D Simulation
Powered by Ursina Engine. Premium Dark-Cyberpunk Operations Center Aesthetics.
Usage: python digital_twin_3d.py
"""
import sys, os, math, random, threading
from collections import deque
import requests
from ursina import *

# ======================================================================
# 1. HOSPITAL GRAPH DEFINITION & PATHFINDING
# ======================================================================
class HospitalGraph:
    _nodes = {}
    _edges = {}
    
    @classmethod
    def init(cls):
        # Coordinates mapped from original layout
        cls._nodes = {
            "Entrance": (0, -35), "Reception": (0, -28), "WaitingHall": (-15, -20),
            "MainHall": (0, 0), "HallNorth": (0, 10), "Pharmacy": (20, -20),
            "EmergencyRoom": (-20, -10), "StaffOffice": (20, 10), "ChargingDock": (0, 35),
            # Corridors
            "WestCorr1": (-20, 0), "WestCorr2": (-20, 10), "WestCorr3": (-20, 20),
            "EastCorr1": (20, 0), "EastCorr2": (20, 20), "RoomCorr1": (-10, 20),
            "RoomCorr2": (10, 20),
            # Rooms
            "Room1": (-30, -5), "Room2": (-30, 5), "Room3": (-30, 15), "Room4": (-30, 25),
            "Room5": (-10, 25), "Room6": (10, 25), "Room7": (30, -5), "Room8": (30, 5),
            "Room9": (30, 15), "Room10": (30, 25), "Room11": (-35, -15), "Room12": (-35, -5),
            "Room13": (35, -15), "Room14": (35, -5), "Room15": (-10, 30), "Room16": (10, 30),
            "Room17": (-35, 10), "Room18": (-35, 20), "Room19": (35, 10), "Room20": (35, 20),
            # ICU Wing
            "ICU_Corr": (0, -10), "ICU1": (-10, -15), "ICU2": (10, -15),
            "ICU3": (-10, -5), "ICU4": (10, -5)
        }
        
        cls._edges = {n: [] for n in cls._nodes}
        connections = [
            ("Entrance", "Reception"),
            ("Reception", "MainHall"), ("Reception", "WaitingHall"), ("Reception", "Pharmacy"),
            ("WaitingHall", "EmergencyRoom"), ("WaitingHall", "MainHall"),
            ("MainHall", "HallNorth"), ("MainHall", "WestCorr1"), ("MainHall", "EastCorr1"),
            ("MainHall", "ICU_Corr"),
            ("HallNorth", "RoomCorr1"), ("HallNorth", "RoomCorr2"), ("HallNorth", "StaffOffice"),
            ("HallNorth", "ChargingDock"),
            ("WestCorr1", "WestCorr2"), ("WestCorr1", "Room1"), ("WestCorr1", "Room2"),
            ("WestCorr1", "EmergencyRoom"),
            ("WestCorr2", "WestCorr3"), ("WestCorr2", "Room3"),
            ("WestCorr3", "Room4"), ("WestCorr3", "RoomCorr1"),
            ("EastCorr1", "EastCorr2"), ("EastCorr1", "Room7"), ("EastCorr1", "Room8"),
            ("EastCorr1", "Pharmacy"), ("EastCorr1", "StaffOffice"),
            ("EastCorr2", "Room9"), ("EastCorr2", "Room10"), ("EastCorr2", "RoomCorr2"),
            ("RoomCorr1", "Room5"), ("RoomCorr1", "Room15"),
            ("RoomCorr2", "Room6"), ("RoomCorr2", "Room16"),
            ("EmergencyRoom", "Room11"), ("EmergencyRoom", "Room12"),
            ("Pharmacy", "Room13"), ("Pharmacy", "Room14"),
            ("WestCorr2", "Room17"), ("WestCorr3", "Room18"),
            ("EastCorr1", "Room19"), ("EastCorr2", "Room20"),
            ("ICU_Corr", "ICU1"), ("ICU_Corr", "ICU2"),
            ("ICU_Corr", "ICU3"), ("ICU_Corr", "ICU4")
        ]
        for u, v in connections:
            if u in cls._nodes and v in cls._nodes:
                cls._edges[u].append(v)
                cls._edges[v].append(u)

    @classmethod
    def get_pos(cls, node):
        return cls._nodes.get(node, (0, 0))

    @classmethod
    def get_all_nodes(cls):
        return cls._nodes

    @classmethod
    def get_room_nodes(cls):
        return [n for n in cls._nodes if n.startswith("Room")]

    @classmethod
    def find_path(cls, start, goal):
        if start == goal: return [start]
        if start not in cls._nodes or goal not in cls._nodes: return [start]
        
        # Simple BFS / Dijkstra
        queue = [[start]]
        visited = {start}
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == goal: return path
            for neighbor in cls._edges[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return [start]

# ======================================================================
# 2. OLLAMA LLM INTEGRATION
# ======================================================================
class LLMService:
    _llm_queue = deque()
    _active_model = "fallback"
    _thread = None
    _lock = threading.Lock()
    _results = []
    
    @classmethod
    def detect_model(cls):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=1.5)
            if r.status_code == 200:
                models = [m['name'] for m in r.json().get('models', [])]
                for target in ["llama3", "llama2", "mistral", "phi3", "gemma"]:
                    if any(target in m for m in models):
                        cls._active_model = target
                        print(f"[LLM] Connected to Ollama: {target}")
                        return
                if models:
                    cls._active_model = models[0]
                    return
        except:
            pass
        cls._active_model = "fallback"
        print("[LLM] Ollama offline. Operating in pattern-matching Fallback Mode.")

    @classmethod
    def query_async(cls, prompt_text):
        if cls._active_model == "fallback":
            cls._process_fallback(prompt_text)
            return
        
        def run():
            sys_prompt = (
                "You are the hospital scheduling AI. Translate natural language into a JSON action object.\n"
                "JSON format: {\"task_type\": \"...\", \"location_node\": \"...\", \"priority\": 1-3, \"description\": \"...\"}\n"
                "Valid task_types: assist_patient, deliver_medicine, guide_patient, escort_visitor, emergency_triage\n"
                "Valid locations: Room1 to Room20, ICU1 to ICU4, Pharmacy, EmergencyRoom, WaitingHall, Reception, StaffOffice\n"
                "Examples:\n"
                "1. \"Bring morphine to room 5\" -> {\"task_type\":\"deliver_medicine\",\"location_node\":\"Room5\",\"priority\":3,\"description\":\"Deliver medication to Patient in Room5\"}\n"
                "2. \"Help the doctor in ICU 2\" -> {\"task_type\":\"assist_patient\",\"location_node\":\"ICU2\",\"priority\":2,\"description\":\"Assist clinical staff in ICU2\"}\n"
                "Respond with raw JSON only. No explanation."
            )
            try:
                r = requests.post("http://localhost:11434/api/generate", json={
                    "model": cls._active_model,
                    "prompt": f"{sys_prompt}\n\nUser request: {prompt_text}",
                    "stream": False,
                    "format": "json"
                }, timeout=5.0)
                if r.status_code == 200:
                    import json
                    data = json.loads(r.json().get('response', '{}'))
                    with cls._lock:
                        data['_src'] = cls._active_model
                        cls._results.append(data)
            except Exception as e:
                cls._process_fallback(prompt_text)

        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    @classmethod
    def _process_fallback(cls, text):
        # Dynamic keyword fallback mapping
        text = text.lower()
        task = "assist_patient"
        loc = "WaitingHall"
        priority = 1
        desc = "AI Assisting Staff"

        if "medicine" in text or "pill" in text or "drug" in text or "deliver" in text:
            task = "deliver_medicine"
            desc = "Deliver medication request"
        elif "guide" in text or "escort" in text or "show" in text:
            task = "guide_patient"
            desc = "Guide user through hallways"
        elif "emergency" in text or "triage" in text or "icu" in text:
            task = "emergency_triage"
            priority = 3
            desc = "Critical priority triage alert"

        # Match location
        for i in range(1, 21):
            if f"room {i}" in text or f"room{i}" in text:
                loc = f"Room{i}"
                break
        for i in range(1, 5):
            if f"icu {i}" in text or f"icu{i}" in text:
                loc = f"ICU{i}"
                priority = 3
                break
        if "pharmacy" in text: loc = "Pharmacy"
        elif "reception" in text: loc = "Reception"
        elif "office" in text: loc = "StaffOffice"
        elif "emergency" in text: loc = "EmergencyRoom"

        with cls._lock:
            cls._results.append({
                "task_type": task,
                "location_node": loc,
                "priority": priority,
                "description": f"Fallback: {desc} at {loc}",
                "_src": "fallback"
            })

    @classmethod
    def poll_results(cls):
        with cls._lock:
            res = list(cls._results)
            cls._results.clear()
            return res

# ======================================================================
# 3. TASK MANAGER & RL SCHEDULER
# ======================================================================
class Task:
    def __init__(self, task_type, location_node, priority, description):
        self.task_type = task_type
        self.location_node = location_node
        self.priority = priority
        self.description = description
        self.status = "pending"  # pending, active, completed
        self.assigned_robot = None
        self.created_time = time.time()
        self.completed_time = None

    def __str__(self):
        return f"[P{self.priority}] {self.task_type.upper()} @ {self.location_node}"

class TaskManager:
    def __init__(self):
        self.queue = []
        self.active_tasks = []
        self.completed_tasks = []
        self.alerts = ["Simulation live and stable."]
        self.auto_timer = 0

    def create_task(self, task_type, location_node, priority, description):
        t = Task(task_type, location_node, priority, description)
        self.queue.append(t)
        self.queue.sort(key=lambda x: x.priority, reverse=True)
        self.add_alert(f"Task Generated: {task_type} -> {location_node}")

    def assign_tasks(self, robots):
        avail = [r for r in robots if r.state == "idle" and r.battery > 15]
        while self.queue and avail:
            task = self.queue[0]
            # Find closest/best robot
            best_r = None
            best_dist = 999999
            for r in avail:
                rx, rz = HospitalGraph.get_pos(r.current_node)
                tx, tz = HospitalGraph.get_pos(task.location_node)
                d = math.hypot(rx - tx, rz - tz)
                score = d - (r.battery * 0.1) # Prefer fully charged robots
                if score < best_dist:
                    best_dist = score
                    best_r = r
            
            if best_r:
                self.queue.pop(0)
                task.status = "active"
                task.assigned_robot = best_r.robot_id
                best_r.assign_task(task)
                self.active_tasks.append(task)
                avail.remove(best_r)
            else:
                break

    def check_completed(self, robots):
        done = []
        for t in list(self.active_tasks):
            if t.status == "completed":
                self.active_tasks.remove(t)
                self.completed_tasks.append(t)
                done.append(t)
                self.add_alert(f"Success: Task completed at {t.location_node}")
        return done

    def auto_generate(self, humans, dt):
        self.auto_timer += dt
        if self.auto_timer < 3.0: return
        self.auto_timer = 0

        for h in humans:
            if h.needs_help and h.help_type:
                # Check if already queued
                q = any(x.location_node == h.current_node and x.task_type == h.help_type for x in self.queue)
                a = any(x.location_node == h.current_node and x.task_type == h.help_type for x in self.active_tasks)
                if not q and not a:
                    pri = 3 if h.help_type == "emergency_triage" else 2
                    self.create_task(h.help_type, h.current_node, pri, f"Auto-request from patient at {h.current_node}")

    def add_alert(self, msg):
        self.alerts.append(msg)
        if len(self.alerts) > 50: self.alerts.pop(0)

    def get_queue_display(self):
        return [str(t) for t in self.queue[:5]]

    def get_active_display(self):
        return [f"R{t.assigned_robot+1}: {t.task_type} -> {t.location_node}" for t in self.active_tasks[:5]]

    def get_recent_alerts(self):
        return self.alerts[-5:]

    def get_metrics(self):
        done_cnt = len(self.completed_tasks)
        avg_resp = 0
        if done_cnt > 0:
            avg_resp = sum(t.completed_time - t.created_time for t in self.completed_tasks) / done_cnt
        return {
            "completed": done_cnt,
            "pending": len(self.queue),
            "active": len(self.active_tasks),
            "avg_response": avg_resp
        }

# ======================================================================
# 4. HUGELY OVERHAULED CYBERPUNK 3D WORLD BUILDER
# ======================================================================
COLORS = {
    'floor': color.rgb32(10, 12, 18), 'grid': color.rgb32(20, 24, 35),
    'wall': color.rgba32(40, 48, 65, 140), 'wall_top': color.rgb32(20, 25, 35),
    'room': color.rgb32(20, 28, 42), 'icu': color.rgb32(45, 15, 20),
    'pharmacy': color.rgb32(15, 38, 25), 'emergency': color.rgb32(50, 28, 12),
    'waiting': color.rgb32(35, 18, 48), 'office': color.rgb32(15, 28, 48),
    'reception': color.rgb32(24, 28, 38), 'dock': color.rgb32(50, 45, 12),
    'mainhall': color.rgb32(15, 18, 24), 'entrance': color.rgb32(20, 24, 30),
    'corridor': color.rgb32(12, 14, 18),
    'led_blue': color.rgb32(0, 180, 255), 'led_red': color.rgb32(255, 30, 60),
    'led_green': color.rgb32(20, 220, 90), 'led_yellow': color.rgb32(255, 180, 30),
    'led_purple': color.rgb32(150, 60, 255), 'dim_text': color.rgb32(100, 110, 125)
}

def get_zone_colors(name):
    if name.startswith('Room'): return COLORS['room'], COLORS['led_blue']
    if name.startswith('ICU') and name != 'ICU_Corr': return COLORS['icu'], COLORS['led_red']
    if name == 'Pharmacy': return COLORS['pharmacy'], COLORS['led_green']
    if name == 'EmergencyRoom': return COLORS['emergency'], COLORS['led_purple']
    if name == 'WaitingHall': return COLORS['waiting'], COLORS['led_purple']
    if name == 'StaffOffice': return COLORS['office'], COLORS['led_blue']
    if name == 'Reception': return COLORS['reception'], COLORS['led_blue']
    if name == 'ChargingDock': return COLORS['dock'], COLORS['led_yellow']
    if name == 'MainHall': return COLORS['mainhall'], COLORS['led_blue']
    if name == 'Entrance': return COLORS['entrance'], COLORS['led_blue']
    return COLORS['corridor'], COLORS['led_blue']

def get_zone_size(name):
    sizes = {'Reception': (8, 8), 'WaitingHall': (8, 8), 'EmergencyRoom': (8, 8),
             'Pharmacy': (8, 8), 'StaffOffice': (8, 8), 'MainHall': (12, 10),
             'ChargingDock': (8, 6), 'Entrance': (8, 4), 'ICU_Corr': (20, 3)}
    if name in sizes: return sizes[name]
    if name.startswith('Room'): return (5, 4)
    if name.startswith('ICU'): return (6, 5)
    return (4, 4)

def is_corridor(name):
    return name.startswith('RoomCorr') or name.startswith('WestCorr') or name.startswith('EastCorr') or name == 'HallNorth'

class Hospital3DWorld:
    def __init__(self):
        # Procedural Floor Plane with shadows enabled
        Entity(model='cube', scale=(250, 0.1, 250), position=(0, -0.05, 0), color=COLORS['floor'], unlit=False)
        # Glow grid overlay
        for i in range(-70, 71, 5):
            Entity(model='cube', scale=(0.03, 0.015, 140), position=(i, 0.005, 0), color=COLORS['grid'], unlit=True)
            Entity(model='cube', scale=(140, 0.015, 0.03), position=(0, 0.005, i), color=COLORS['grid'], unlit=True)
            
        self._build_zones()
        self._build_corridor_paths()
        
    def _build_zones(self):
        for name, (x, z) in HospitalGraph.get_all_nodes().items():
            if is_corridor(name) or name == "ICU_Corr": continue
            w, h = get_zone_size(name)
            z_col, led_col = get_zone_colors(name)
            
            # Glowing floor tile
            Entity(model='cube', scale=(w, 0.1, h), position=(x, 0.01, z), color=z_col, unlit=True)
            
            # Bottom LED highlights
            Entity(model='cube', scale=(w, 0.04, 0.06), position=(x, 0.07, z - h/2), color=led_col, unlit=True)
            Entity(model='cube', scale=(w, 0.04, 0.06), position=(x, 0.07, z + h/2), color=led_col, unlit=True)
            Entity(model='cube', scale=(0.06, 0.04, h), position=(x - w/2, 0.07, z), color=led_col, unlit=True)
            Entity(model='cube', scale=(0.06, 0.04, h), position=(x + w/2, 0.07, z), color=led_col, unlit=True)
            
            # High 3D Walls
            wall_h = 2.5
            # North, West, East Walls
            Entity(model='cube', scale=(w + 0.2, wall_h, 0.2), position=(x, wall_h/2, z - h/2), color=COLORS['wall'], unlit=False)
            Entity(model='cube', scale=(0.2, wall_h, h + 0.2), position=(x - w/2, wall_h/2, z), color=COLORS['wall'], unlit=False)
            Entity(model='cube', scale=(0.2, wall_h, h + 0.2), position=(x + w/2, wall_h/2, z), color=COLORS['wall'], unlit=False)
            
            # Front Wall with dynamic Door cutout
            door_w = 1.8
            rem_w = (w - door_w) / 2.0
            if rem_w > 0.2:
                Entity(model='cube', scale=(rem_w, wall_h, 0.2), position=(x - w/2 + rem_w/2, wall_h/2, z + h/2), color=COLORS['wall'], unlit=False)
                Entity(model='cube', scale=(rem_w, wall_h, 0.2), position=(x + w/2 - rem_w/2, wall_h/2, z + h/2), color=COLORS['wall'], unlit=False)
                Entity(model='cube', scale=(door_w, 0.5, 0.2), position=(x, wall_h - 0.25, z + h/2), color=COLORS['wall'], unlit=False)

            # Billboards / 3D floating Room Text
            lbl = Text(text=name.upper(), scale=0.45, color=led_col, parent=scene, position=(x, wall_h + 1.2, z))
            lbl.look_at(camera)
            # Update look_at dynamically
            def update_billboard(l=lbl):
                l.rotation = camera.rotation
            lbl.update = update_billboard

    def _build_corridor_paths(self):
        nodes = HospitalGraph.get_all_nodes()
        visited = set()
        for name, (x, z) in nodes.items():
            for neighbor in HospitalGraph._edges[name]:
                edge_id = tuple(sorted([name, neighbor]))
                if edge_id in visited: continue
                visited.add(edge_id)
                
                nx, nz = HospitalGraph.get_pos(neighbor)
                mid_x = (x + nx) / 2.0
                mid_z = (z + nz) / 2.0
                length = math.hypot(x - nx, z - nz)
                angle = math.degrees(math.atan2(nx - x, nz - z))
                
                # Glowing pathway carpet
                path = Entity(model='cube', scale=(1.2, 0.05, length), position=(mid_x, 0.006, mid_z), color=COLORS['corridor'], unlit=True)
                path.rotation_y = angle
                # Tech centerline
                line = Entity(model='cube', scale=(0.06, 0.06, length), position=(mid_x, 0.015, mid_z), color=COLORS['led_blue'], alpha=0.6, unlit=True)
                line.rotation_y = angle

# ======================================================================
# 5. AGENTS: ROBOTS & HUMANS (FULL 3D MODELS)
# ======================================================================
class RobotAgent3D:
    all_robots = []
    
    def __init__(self, robot_id):
        self.robot_id = robot_id
        self.state = "idle"
        self.battery = 100.0
        self.current_node = "ChargingDock"
        self.target_node = None
        self.path = []
        self.path_idx = 0
        self.current_task = None
        self.tasks_completed = 0
        self.thoughts = ["> System online."]
        
        # Color palettes
        palettes = [COLORS['led_blue'], COLORS['led_red'], COLORS['led_green'], COLORS['led_yellow'], COLORS['led_purple']]
        self.color = palettes[robot_id % len(palettes)]
        
        # Position at charging dock initially
        dx, dz = HospitalGraph.get_pos("ChargingDock")
        spawn_pos = Vec3(dx + (robot_id - 2) * 2.0, 0.6, dz)
        
        # 3D Model Construction
        self.entity = Entity(position=spawn_pos, rotation_y=180)
        # Body
        self.body = Entity(parent=self.entity, model='cube', scale=(1.0, 1.2, 1.0), position=(0, 0, 0), color=self.color, unlit=False)
        # Dome Head
        self.head = Entity(parent=self.entity, model='sphere', scale=(0.85, 0.5, 0.85), position=(0, 0.7, 0), color=color.rgb32(80, 85, 95), unlit=False)
        # Cylindrical Eye
        self.eye = Entity(parent=self.entity, model='sphere', scale=(0.15, 0.15, 0.15), position=(0, 0.75, 0.38), color=self.color, unlit=True)
        # Antenna
        Entity(parent=self.entity, model='cube', scale=(0.04, 0.4, 0.04), position=(0, 1.05, 0), color=color.gray)
        self.antenna_tip = Entity(parent=self.entity, model='sphere', scale=(0.12, 0.12, 0.12), position=(0, 1.25, 0), color=self.color, unlit=True)
        # Tech Glow Ring under robot
        self.glow_ring = Entity(parent=self.entity, model='cube', scale=(1.5, 0.02, 1.5), position=(0, -0.58, 0), color=self.color, alpha=0.3, unlit=True)
        
        self.task_timer = 0
        self.pulse_timer = 0
        RobotAgent3D.all_robots.append(self)

    def update(self, dt):
        self.pulse_timer += dt
        # Bobbing & eye pulsing
        self.body.y = math.sin(self.pulse_timer * 6.0) * 0.03
        self.head.y = 0.7 + math.sin(self.pulse_timer * 6.0) * 0.015
        pulse = (math.sin(self.pulse_timer * 12.0) + 1.0) * 0.5
        self.eye.color = lerp(self.color, color.white, pulse * 0.4)
        self.antenna_tip.color = self.eye.color
        
        if self.state == "charging":
            self.battery = min(100.0, self.battery + 5.0 * dt)
            if self.battery >= 100.0:
                self.state = "idle"
                self.add_thought("Battery fully charged. Standing by.")
            return

        if self.state in ["navigating", "returning"]:
            self._move_along_path(dt)
        elif self.state == "working":
            self.task_timer -= dt
            if self.task_timer <= 0:
                self._finish_task()

    def _move_along_path(self, dt):
        if self.path_idx >= len(self.path):
            self._arrive_at_target()
            return
            
        target_node = self.path[self.path_idx]
        tx, tz = HospitalGraph.get_pos(target_node)
        target_pos = Vec3(tx, 0.6, tz)
        
        dir_vec = target_pos - self.entity.position
        dist = dir_vec.length()
        
        # Speed factor
        speed = 7.5
        if dist < 0.2:
            self.entity.position = target_pos
            self.current_node = target_node
            self.path_idx += 1
        else:
            step = speed * dt
            if step > dist: step = dist
            self.entity.position += (dir_vec / dist) * step
            
            # Smooth rotate to target direction
            target_rot = math.degrees(math.atan2(dir_vec.x, dir_vec.z))
            self.entity.rotation_y = lerp(self.entity.rotation_y, target_rot, dt * 10.0)
            
        self.battery = max(0.0, self.battery - 0.08 * dt)
        if self.battery <= 0.0:
            self.add_thought("BATTERY CRITICAL! Forcing emergency dock return.")
            self._abort_and_charge()

    def _arrive_at_target(self):
        if self.state == "returning":
            self.state = "charging"
            self.add_thought("Docked. Commencing inductive charging sequence.")
            return
            
        if self.current_task:
            self.state = "working"
            self.task_timer = 2.5
            self.add_thought(f"Arrived at {self.current_node}. Executing: {self.current_task.task_type}")
        else:
            self.state = "idle"

    def _finish_task(self):
        if self.current_task:
            self.current_task.status = "completed"
            self.current_task.completed_time = time.time()
            self.tasks_completed += 1
            self.current_task = None
            
        self.add_thought("Action complete. Analyzing next scheduling cue.")
        
        # Check battery level
        if self.battery < 20.0:
            self._abort_and_charge()
        else:
            self.state = "idle"

    def _abort_and_charge(self):
        if self.current_task:
            self.current_task.status = "pending"
            self.current_task = None
        self.state = "returning"
        self.path = HospitalGraph.find_path(self.current_node, "ChargingDock")
        self.path_idx = 0

    def assign_task(self, task):
        self.current_task = task
        self.state = "navigating"
        self.path = HospitalGraph.find_path(self.current_node, task.location_node)
        self.path_idx = 0
        self.add_thought(f"Dispatched -> {task.location_node} ({task.task_type})")

    def add_thought(self, msg):
        self.thoughts.append(f"> {msg}")
        if len(self.thoughts) > 5: self.thoughts.pop(0)

    def get_info(self):
        return {
            "id": f"R{self.robot_id + 1}",
            "state": self.state,
            "battery": int(self.battery),
            "location": self.current_node,
            "current_task": self.current_task.task_type if self.current_task else "None",
            "tasks_completed": self.tasks_completed,
            "thoughts": "\n".join(self.thoughts)
        }

class HumanAgent3D:
    def __init__(self, role, starting_node=None):
        self.role = role # patient, doctor, nurse, visitor
        self.state = "idle"
        self.needs_help = False
        self.help_type = None
        
        rooms = HospitalGraph.get_room_nodes()
        self.home = starting_node if starting_node else (random.choice(rooms) if role == "patient" else "Reception")
        self.current_node = self.home
        
        tx, tz = HospitalGraph.get_pos(self.current_node)
        spawn_pos = Vec3(tx + random.uniform(-1, 1), 0.5, tz + random.uniform(-1, 1))
        
        # 3D Visual Mesh construction
        self.entity = Entity(position=spawn_pos)
        
        colors = {
            "patient": color.rgb32(230, 160, 40),
            "doctor": color.rgb32(40, 200, 100),
            "nurse": color.rgb32(0, 160, 255),
            "visitor": color.rgb32(160, 80, 220)
        }
        self.color = colors.get(role, color.white)
        
        # Stylized capsule torso
        Entity(parent=self.entity, model='cube', scale=(0.5, 1.2, 0.5), position=(0, 0, 0), color=self.color, unlit=False)
        # Sphere Head
        Entity(parent=self.entity, model='sphere', scale=(0.35, 0.35, 0.35), position=(0, 0.65, 0), color=color.rgb32(220, 185, 150), unlit=False)
        # Mini glow dot for identification
        self.badge = Entity(parent=self.entity, model='sphere', scale=(0.08, 0.08, 0.08), position=(0, 0.3, 0.26), color=self.color, unlit=True)
        
        # Floating Help Icon (hidden initially)
        self.alert_icon = Entity(parent=self.entity, model='cube', scale=(0.2, 0.5, 0.2), position=(0, 1.2, 0), color=color.red, enabled=False, unlit=True)
        
        self.path = []
        self.path_idx = 0
        self.idle_timer = random.uniform(3, 10)
        self.request_timer = random.uniform(10, 40) if role == "patient" else 99999
        self.pulse = 0

    def update(self, dt):
        self.pulse += dt
        # Bobbing walk animation
        if self.state == "walking":
            self.entity.y = 0.5 + math.sin(self.pulse * 10.0) * 0.05
            self._move_along_path(dt)
        else:
            self.entity.y = 0.5
            self.idle_timer -= dt
            if self.idle_timer <= 0:
                self._wander()
                
        if self.role == "patient":
            self.request_timer -= dt
            if self.request_timer <= 0 and not self.needs_help:
                self._trigger_help_request()
                self.request_timer = random.uniform(40, 100)
                
        if self.needs_help:
            # Spin help icon
            self.alert_icon.rotation_y += dt * 150
            self.alert_icon.y = 1.2 + math.sin(self.pulse * 5.0) * 0.1

    def _wander(self):
        nodes = list(HospitalGraph.get_all_nodes().keys())
        target = random.choice(nodes)
        if is_corridor(target): return  # Stay in rooms/departments mostly
        
        self.path = HospitalGraph.find_path(self.current_node, target)
        self.path_idx = 0
        self.state = "walking"
        self.idle_timer = random.uniform(5, 15)

    def _move_along_path(self, dt):
        if self.path_idx >= len(self.path):
            self.state = "idle"
            return
            
        tx, tz = HospitalGraph.get_pos(self.path[self.path_idx])
        target_pos = Vec3(tx + random.uniform(-0.5, 0.5), 0.5, tz + random.uniform(-0.5, 0.5))
        
        dir_vec = target_pos - self.entity.position
        dist = dir_vec.length()
        
        if dist < 0.3:
            self.current_node = self.path[self.path_idx]
            self.path_idx += 1
        else:
            step = 3.5 * dt
            if step > dist: step = dist
            self.entity.position += (dir_vec / dist) * step
            
            target_rot = math.degrees(math.atan2(dir_vec.x, dir_vec.z))
            self.entity.rotation_y = lerp(self.entity.rotation_y, target_rot, dt * 8.0)

    def _trigger_help_request(self):
        self.needs_help = True
        self.help_type = random.choice(["assist_patient", "deliver_medicine", "guide_patient"])
        self.alert_icon.enabled = True
        
    def fulfill_help(self):
        self.needs_help = False
        self.help_type = None
        self.alert_icon.enabled = False
        # Brief happy pulse
        self.entity.animate_scale((1.2, 1.2, 1.2), duration=0.3, curve=curve.out_bounce)
        self.entity.animate_scale((1, 1, 1), delay=0.3, duration=0.3)

# ======================================================================
# 6. HIGH-END BENTO-BOX OPERATIONS CENTER DASHBOARD HUD
# ======================================================================
class BentoDashboard:
    def __init__(self):
        self._bg = color.rgba32(10, 12, 18, 235)
        self._panel_bg = color.rgba32(16, 20, 28, 245)
        self._border = color.rgb32(35, 45, 60)
        
        # Canvas aspect scaling
        self.aspect = window.aspect_ratio
        self.panel_w = 0.52
        self.panel_x = -0.5 * self.aspect + (self.panel_w / 2.0)
        
        # ── Left Panel (Bento Container) ──────────────────────────────
        self.panel_entity = Entity(parent=camera.ui, model='quad', scale=(self.panel_w, 1.0), position=(self.panel_x, 0), z=1, color=self._panel_bg, unlit=True)
        # Tech border edge
        Entity(parent=camera.ui, model='quad', scale=(0.002, 1.0), position=(self.panel_x + self.panel_w/2.0, 0), z=0.5, color=self._border, unlit=True)
        
        y = 0.44
        # Title Header
        Text(text='[FARS DIGITAL TWIN v2.0]', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.02, y), scale=0.8, color=COLORS['led_blue'])
        Entity(parent=camera.ui, model='circle', scale=0.015, position=(self.panel_x - self.panel_w/2.0 + 0.03, y - 0.045), color=COLORS['led_green'], unlit=True)
        Text(text='ONLINE  |  AI: ' + LLMService._active_model.upper(), parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.05, y - 0.038), scale=0.55, color=COLORS['dim_text'])
        
        # Divider
        Entity(parent=camera.ui, model='quad', scale=(self.panel_w - 0.04, 0.002), position=(self.panel_x, y - 0.075), color=self._border, unlit=True)
        
        # ── Robot Fleet list ──────────────────────────────────────────
        y_fleet = y - 0.11
        Text(text='>> ROBOT FLEET MONITOR', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.02, y_fleet), scale=0.6, color=COLORS['led_blue'])
        
        self.cards = []
        cy = y_fleet - 0.045
        for i in range(5):
            bg = Entity(parent=camera.ui, model='quad', scale=(self.panel_w - 0.04, 0.07), position=(self.panel_x, cy - i*0.075), color=color.rgba32(20,25,35,0), unlit=True)
            # Accent lead bar
            pal = [COLORS['led_blue'], COLORS['led_red'], COLORS['led_green'], COLORS['led_yellow'], COLORS['led_purple']]
            Entity(parent=camera.ui, model='quad', scale=(0.006, 0.065), position=(self.panel_x - self.panel_w/2.0 + 0.02, cy - i*0.075), color=pal[i], unlit=True)
            
            rid = Text(text=f'R{i+1}', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.03, cy - i*0.075 + 0.028), scale=0.6, color=pal[i])
            state = Text(text='IDLE', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.08, cy - i*0.075 + 0.028), scale=0.55, color=color.white)
            
            # Batt bar UI
            Entity(parent=camera.ui, model='quad', scale=(0.1, 0.012), position=(self.panel_x - self.panel_w/2.0 + 0.22, cy - i*0.075 + 0.022), color=color.rgb32(20,25,30), unlit=True, origin=(-0.5, 0))
            bar = Entity(parent=camera.ui, model='quad', scale=(0.1, 0.012), position=(self.panel_x - self.panel_w/2.0 + 0.22, cy - i*0.075 + 0.022), color=COLORS['led_green'], unlit=True, origin=(-0.5, 0))
            b_txt = Text(text='100%', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.33, cy - i*0.075 + 0.028), scale=0.55, color=COLORS['dim_text'])
            
            loc = Text(text='@ ChargingDock', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.03, cy - i*0.075 + 0.005), scale=0.5, color=COLORS['dim_text'])
            thought = Text(text='> Inductive loading complete.', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.16, cy - i*0.075 + 0.005), scale=0.5, color=color.rgb32(85,95,105))
            
            self.cards.append({"bg": bg, "state": state, "bar": bar, "b_txt": b_txt, "loc": loc, "thought": thought})
            
        # Divider
        y_div2 = cy - 4*0.075 - 0.05
        Entity(parent=camera.ui, model='quad', scale=(self.panel_w - 0.04, 0.002), position=(self.panel_x, y_div2), color=self._border, unlit=True)
        
        # ── Task Queue ────────────────────────────────────────────────
        Text(text='>> LIVE TASK QUEUE', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.02, y_div2 - 0.028), scale=0.6, color=COLORS['led_yellow'])
        self.queue_text = Text(text='(empty)', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.03, y_div2 - 0.065), scale=0.52, color=color.white)
        
        # Divider
        y_div3 = y_div2 - 0.18
        Entity(parent=camera.ui, model='quad', scale=(self.panel_w - 0.04, 0.002), position=(self.panel_x, y_div3), color=self._border, unlit=True)
        
        # ── RL Scheduler Metrics ──────────────────────────────────────
        Text(text='>> RL DECISION METRICS', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.02, y_div3 - 0.028), scale=0.6, color=COLORS['led_green'])
        self.metrics_text = Text(text='Decision Efficiency: 100%\nAvg Scheduler Latency: 0s\nUtil Rate: 0%\nAvg Fleet Battery: 100%', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.03, y_div3 - 0.065), scale=0.52, color=COLORS['dim_text'], line_height=1.4)
        
        # Divider
        y_div4 = y_div3 - 0.17
        Entity(parent=camera.ui, model='quad', scale=(self.panel_w - 0.04, 0.002), position=(self.panel_x, y_div4), color=self._border, unlit=True)
        
        # ── Log Alerts ────────────────────────────────────────────────
        Text(text='>> COMPLIANCE & SAFETY ALERTS', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.02, y_div4 - 0.028), scale=0.6, color=COLORS['led_red'])
        self.alert_text = Text(text='', parent=camera.ui, position=(self.panel_x - self.panel_w/2.0 + 0.03, y_div4 - 0.065), scale=0.48, color=COLORS['dim_text'], line_height=1.2)
        
        # ── Top Statistics Bar ────────────────────────────────────────
        bar_h = 0.055
        self.top_bar = Entity(parent=camera.ui, model='quad', scale=(self.aspect * 2, bar_h), position=(0, 0.5 - bar_h/2.0), z=1, color=color.rgba32(10, 12, 18, 225), unlit=True)
        Entity(parent=camera.ui, model='quad', scale=(self.aspect * 2, 0.002), position=(0, 0.5 - bar_h), z=0.5, color=self._border, unlit=True)
        
        Text(text='FARS CENTRAL OPERATIONS CENTER', parent=camera.ui, position=(self.panel_x + self.panel_w/2.0 + 0.02, 0.482), scale=0.68, color=color.white)
        self.top_stats = Text(text='Active Robots: 0/5  |  Tasks Resolved: 0  |  FPS: 60', parent=camera.ui, position=(self.aspect - 0.65, 0.482), scale=0.6, color=COLORS['dim_text'])
        
        # ── Bottom Command Console ────────────────────────────────────
        self.bot_bar = Entity(parent=camera.ui, model='quad', scale=(self.aspect * 2, bar_h), position=(0, -0.5 + bar_h/2.0), z=1, color=color.rgba32(10, 12, 18, 225), unlit=True)
        Entity(parent=camera.ui, model='quad', scale=(self.aspect * 2, 0.002), position=(0, -0.5 + bar_h), z=0.5, color=self._border, unlit=True)
        
        Text(text='[SYSTEM_INPUT] >', parent=camera.ui, position=(self.panel_x + self.panel_w/2.0 + 0.02, -0.485), scale=0.6, color=COLORS['led_blue'])
        self.cmd_input_text = ""
        self.cmd_display = Text(text='Press TAB to enter command terminal...', parent=camera.ui, position=(self.panel_x + self.panel_w/2.0 + 0.15, -0.485), scale=0.55, color=COLORS['dim_text'])
        self.cmd_feedback = Text(text='', parent=camera.ui, position=(self.aspect - 0.55, -0.485), scale=0.55, color=COLORS['led_green'])
        
        self.cam_mode_text = Text(text='CAMERA: Overview  |  Orbit=Middle Drag  |  Pan=Shift+Middle  |  Zoom=Scroll', parent=camera.ui, position=(-0.4, -0.42), scale=0.48, color=COLORS['dim_text'])

    def update_hud(self, active_cnt, total_cnt, resolved_cnt, metrics):
        fps = round(1.0 / max(0.0001, time.dt))
        self.top_stats.text = f'Active Robots: {active_cnt}/{total_cnt}  |  Tasks Resolved: {resolved_cnt}  |  FPS: {fps}'
        
        eff = 100
        if resolved_cnt + metrics['pending'] > 0:
            eff = min(100, int((resolved_cnt / (resolved_cnt + metrics['pending'])) * 100))
            
        self.metrics_text.text = (
            f"Decision Efficiency: {eff}%\n"
            f"Avg Scheduler Latency: {metrics['avg_response']:.1f}s\n"
            f"Util Rate: {int((active_cnt / total_cnt) * 100)}%\n"
            f"Avg Fleet Battery: --%"
        )

    def update_queue(self, q_list):
        self.queue_text.text = "\n".join(q_list) if q_list else "(No active tasks queued)"

    def update_robots(self, robot_infos):
        tot_bat = 0
        active_cnt = 0
        for i, info in enumerate(robot_infos):
            if i >= len(self.cards): break
            c = self.cards[i]
            
            c['state'].text = info['state'].upper()
            c['state'].color = COLORS['led_green'] if info['state'] == "working" else (COLORS['led_blue'] if info['state'] == "navigating" else color.white)
            
            bp = info['battery'] / 100.0
            tot_bat += info['battery']
            c['bar'].scale_x = 0.1 * bp
            c['bar'].color = COLORS['led_green'] if bp > 0.4 else (COLORS['led_yellow'] if bp > 0.18 else COLORS['led_red'])
            c['b_txt'].text = f"{info['battery']}%"
            
            c['loc'].text = f"@ {info['location']}"
            
            t = info['thoughts'].split('\n')[-1]
            c['thought'].text = t if len(t) < 32 else (t[:30] + '...')
            
            if info['state'] not in ["idle", "charging"]:
                active_cnt += 1
                
        avg_b = int(tot_bat / len(robot_infos))
        lines = self.metrics_text.text.split('\n')
        if len(lines) >= 4:
            lines[3] = f"Avg Fleet Battery: {avg_b}%"
            self.metrics_text.text = "\n".join(lines)

    def update_alerts(self, alerts):
        self.alert_text.text = "\n".join(alerts)

    def handle_character(self, key):
        if key == 'backspace':
            self.cmd_input_text = self.cmd_input_text[:-1]
        elif key == 'space':
            self.cmd_input_text += ' '
        elif len(key) == 1 and key.isprintable():
            self.cmd_input_text += key
            
        if self.cmd_input_text:
            self.cmd_display.text = self.cmd_input_text + "|"
            self.cmd_display.color = color.white
        else:
            self.cmd_display.text = "Type command + Enter..."
            self.cmd_display.color = COLORS['dim_text']

    def clear_command(self):
        cmd = self.cmd_input_text
        self.cmd_input_text = ""
        self.cmd_display.text = "Press TAB to enter command terminal..."
        self.cmd_display.color = COLORS['dim_text']
        return cmd

    def show_feedback(self, msg, error=False):
        self.cmd_feedback.text = msg
        self.cmd_feedback.color = COLORS['led_red'] if error else COLORS['led_blue']
        invoke(self._clear_feedback, delay=4.0)
        
    def _clear_feedback(self):
        self.cmd_feedback.text = ""

# ======================================================================
# 7. CAMERA INTERACTIVE ORBIT CONTROLLER
# ======================================================================
class SmoothCameraController(Entity):
    def __init__(self):
        super().__init__()
        self.dist = 85.0
        self.target_dist = 85.0
        self.angle_x = 52.0
        self.target_ax = 52.0
        self.angle_y = -35.0
        self.target_ay = -35.0
        self.focal_point = Vec3(5, 0, 5)
        self.target_focal = Vec3(5, 0, 5)
        
        camera.orthographic = False
        camera.fov = 50

    def update(self):
        dt = time.dt
        if dt <= 0: return
        
        # Smooth interpolation
        self.focal_point = lerp(self.focal_point, self.target_focal, dt * 5.0)
        self.dist = lerp(self.dist, self.target_dist, dt * 5.0)
        self.angle_x = lerp(self.angle_x, self.target_ax, dt * 5.0)
        self.angle_y = lerp(self.angle_y, self.target_ay, dt * 5.0)
        
        # Orbit & Pan via mouse drag
        if mouse.middle:
            if held_keys['shift']:
                # Panning target position
                pan_sp = 0.5 * self.target_dist
                dx = -mouse.velocity[0] * pan_sp
                dz = -mouse.velocity[1] * pan_sp
                rad = math.radians(self.target_ay)
                self.target_focal += Vec3(math.sin(rad), 0, math.cos(rad)) * dz + Vec3(math.cos(rad), 0, -math.sin(rad)) * dx
            else:
                self.target_ay += mouse.velocity[0] * 80.0
                self.target_ax -= mouse.velocity[1] * 80.0
                self.target_ax = clamp(self.target_ax, 10, 85)
                
        # Key Zooming
        if held_keys['+']: self.target_dist -= 45.0 * dt
        if held_keys['-']: self.target_dist += 45.0 * dt
        self.target_dist = clamp(self.target_dist, 15, 140)
        
        rx = math.radians(self.angle_x)
        ry = math.radians(self.angle_y)
        camera.position = Vec3(
            self.focal_point.x + self.dist * math.sin(ry) * math.cos(rx),
            self.focal_point.y + self.dist * math.sin(rx),
            self.focal_point.z - self.dist * math.cos(ry) * math.cos(rx)
        )
        camera.look_at(self.focal_point)
        camera.rotation_z = 0

    def focus_node(self, name):
        try:
            x, z = HospitalGraph.get_pos(name)
            self.target_focal = Vec3(x, 0.5, z)
            self.target_dist = 35.0
            self.target_ax = 45.0
        except:
            pass

    def input(self, key):
        if not globals().get('typing_mode', False):
            if key == 'scroll up': self.target_dist -= 6.0
            if key == 'scroll down': self.target_dist += 6.0

# ======================================================================
# 8. WORLD HIGHLIGHT ANIMATION EFFECT
# ======================================================================
def show_room_highlight(node_name):
    try:
        x, z = HospitalGraph.get_pos(node_name)
        ring = Entity(model='cube', scale=(7, 0.1, 7), position=(x, 0.1, z), color=COLORS['led_blue'], alpha=0.6, unlit=True)
        ring.animate_scale((11, 0.1, 11), duration=1.0, curve=curve.out_expo)
        ring.animate('alpha', 0, duration=1.4, curve=curve.linear)
        destroy(ring, delay=1.5)
    except:
        pass

# ======================================================================
# 9. MAIN SIMULATION SYSTEM & RUNNER
# ======================================================================
robots = []
humans = []
task_mgr = None
dashboard = None
cam = None
patients_resolved_count = 0
typing_mode = False

def init_simulation():
    global task_mgr, dashboard, cam
    
    # 0. Setup Lighting and Shadows for Isaac Sim Aesthetic
    sun = DirectionalLight(y=20, rotation=(60, -30, 0))
    sun.shadows = True
    AmbientLight(color=color.rgba(80, 80, 90, 255))
    
    # 1. Init Graph
    HospitalGraph.init()
    
    # 2. Build 3D World
    Hospital3DWorld()
    
    # 3. Spawn Robots
    for i in range(5):
        robots.append(RobotAgent3D(i))
        
    # 4. Spawn Humans (Patients + Staff)
    room_keys = HospitalGraph.get_room_nodes()
    for i in range(15):
        h = HumanAgent3D("patient", starting_node=room_keys[i % len(room_keys)])
        humans.append(h)
    for _ in range(6): humans.append(HumanAgent3D("doctor"))
    for _ in range(6): humans.append(HumanAgent3D("nurse"))
    for _ in range(6): humans.append(HumanAgent3D("visitor"))
    
    # 5. Start Sub-services
    task_mgr = TaskManager()
    dashboard = BentoDashboard()
    cam = SmoothCameraController()
    
    # Pre-detect Ollama in thread
    LLMService.detect_model()

def update():
    global patients_resolved_count
    dt = time.dt
    if dt <= 0: return
    
    # 1. Update Asynchronous LLM responses
    for result in LLMService.poll_results():
        src = result.get('_src', 'fallback')
        if 'error' in result:
            dashboard.show_feedback(f"LLM Error: {result['error']}", error=True)
        else:
            task_mgr.create_task(result['task_type'], result['location_node'], result['priority'], result['description'])
            loc = result['location_node']
            dashboard.show_feedback(f"[{src.upper()}] Robot scheduled -> {loc}")
            show_room_highlight(loc)
            cam.focus_node(loc)
            
    # 2. Update Agents
    for h in humans:
        h.update(dt)
    for r in robots:
        r.update(dt)
        
    # 3. Update Schedulers
    task_mgr.auto_generate(humans, dt)
    task_mgr.assign_tasks(robots)
    
    # 4. Check Task completion triggers
    resolved = task_mgr.check_completed(robots)
    for task in resolved:
        patients_resolved_count += 1
        # Resolve patient state
        for h in humans:
            if h.current_node == task.location_node and h.needs_help:
                h.fulfill_help()
                break
                
    # 5. Update UI values
    dashboard.update_hud(
        active_cnt=sum(1 for r in robots if r.state not in ["idle", "charging"]),
        total_cnt=len(robots),
        resolved_cnt=patients_resolved_count,
        metrics=task_mgr.get_metrics()
    )
    dashboard.update_queue(task_mgr.get_queue_display())
    dashboard.update_robots([r.get_info() for r in robots])
    dashboard.update_alerts(task_mgr.get_recent_alerts())

def input(key):
    global typing_mode
    if key == 'tab':
        typing_mode = not typing_mode
        dashboard.cam_mode_text.text = 'TYPING CONSOLE MODE  |  Press TAB to exit' if typing_mode else 'CAMERA: Overview  |  Orbit=Middle Drag  |  Pan=Shift+Middle  |  Zoom=Scroll'
        dashboard.cmd_display.text = "Type command + Enter..." if typing_mode else "Press TAB to enter command terminal..."
        dashboard.cmd_display.color = color.white if typing_mode else COLORS['dim_text']
        return
        
    if typing_mode:
        if key == 'enter':
            cmd = dashboard.clear_command()
            if cmd:
                dashboard.show_feedback(f"Querying AI Scheduler via Ollama...")
                LLMService.query_async(cmd)
            # Exit typing mode on submit
            typing_mode = False
            dashboard.cam_mode_text.text = 'CAMERA: Overview  |  Orbit=Middle Drag  |  Pan=Shift+Middle  |  Zoom=Scroll'
        else:
            dashboard.handle_character(key)
        return
        
    # Camera hotkeys
    for i in range(min(5, len(robots))):
        if key == str(i + 1):
            cam.focus_node(robots[i].current_node)
            dashboard.show_feedback(f"Focusing Robot R{i+1}")
            
    if key == 'home':
        cam.target_focal = Vec3(5, 0, 5)
        cam.target_dist = 85.0
        cam.target_ax = 52.0
        cam.target_ay = -35.0
        dashboard.show_feedback("Camera Reset to Overview")

if __name__ == '__main__':
    app = Ursina(title='FARS Cyberpunk Operations Console', borderless=False, fullscreen=False, size=(1920, 1080))
    window.color = color.rgb32(10, 12, 18)
    window.fps_counter.enabled = True
    
    init_simulation()
    
    app.run()
