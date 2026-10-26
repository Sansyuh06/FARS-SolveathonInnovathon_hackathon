"""
main_simulation.py -- FARS Hospital Digital Twin Simulator
Entry point. Wires together all modules and runs the Ursina simulation loop.

Usage:
    python main_simulation.py
"""

from ursina import *
import math

class CameraController(Entity):
    def __init__(self):
        super().__init__()
        self.rotation_speed = 80
        self.pan_speed = 30
        self.distance = 90
        self.target_distance = 90
        self.angle_x = 55
        self.target_angle_x = 55
        self.angle_y = -30
        self.target_angle_y = -30
        self.target = Vec3(5, 0, 5)
        self.desired_target = Vec3(5, 0, 5)
        camera.orthographic = False
        camera.fov = 55

    def update(self):
        dt = time.dt

        # Smooth interpolation for cinematic movement
        self.target = lerp(self.target, self.desired_target, dt * 4)
        self.distance = lerp(self.distance, self.target_distance, dt * 4)
        self.angle_x = lerp(self.angle_x, self.target_angle_x, dt * 4)
        self.angle_y = lerp(self.angle_y, self.target_angle_y, dt * 4)

        # Blender style controls: Middle mouse for orbit, Shift+Middle for pan
        if mouse.middle:
            if held_keys['shift']:  
                # Pan mode
                pan_speed_multiplier = 0.5 * self.target_distance
                pan_x = -mouse.velocity[0] * pan_speed_multiplier
                pan_z = -mouse.velocity[1] * pan_speed_multiplier
                
                rad = math.radians(self.target_angle_y)
                forward = Vec3(math.sin(rad), 0, math.cos(rad))
                right = Vec3(math.cos(rad), 0, -math.sin(rad))
                
                self.desired_target += (forward * pan_z + right * pan_x)
            else:
                # Orbit mode
                self.target_angle_y += mouse.velocity[0] * self.rotation_speed
                self.target_angle_x -= mouse.velocity[1] * self.rotation_speed
                self.target_angle_x = clamp(self.target_angle_x, 10, 85)

        if held_keys['+'] or held_keys['=']:
            self.target_distance -= 40 * dt
        if held_keys['-']:
            self.target_distance += 40 * dt

        self.target_distance = clamp(self.target_distance, 15, 150)

        rad_x = math.radians(self.angle_x)
        rad_y = math.radians(self.angle_y)
        camera.position = Vec3(
            self.target.x + self.distance * math.sin(rad_y) * math.cos(rad_x),
            self.target.y + self.distance * math.sin(rad_x),
            self.target.z - self.distance * math.cos(rad_y) * math.cos(rad_x)
        )
        camera.look_at(self.target)
        camera.rotation_z = 0
        
    def go_to_node(self, node_name):
        from navigation import get_node_position
        try:
            x, z = get_node_position(node_name)
            self.desired_target = Vec3(x, 0, z)
            self.target_distance = 40
            self.target_angle_x = 45
        except Exception:
            pass

    def input(self, key):
        if not globals().get('typing_mode', False):
            if key == 'scroll up':
                self.distance -= 8
            if key == 'scroll down':
                self.distance += 8


# ======================================================================
#  Globals
# ======================================================================
robots = []
humans = []
task_mgr = None
dashboard = None
patients_assisted_count = 0
typing_mode = False
selected_robot_index = 0
pending_ollama_tasks = []
cam = None


import socket
import threading
import struct

stream_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stream_server.bind(('127.0.0.1', 8081))
stream_server.listen(1)
stream_conn = None

def accept_conn():
    global stream_conn
    while True:
        try:
            conn, addr = stream_server.accept()
            stream_conn = conn
        except:
            pass

threading.Thread(target=accept_conn, daemon=True).start()

# ======================================================================
#  Setup
# ======================================================================
def setup():
    global robots, humans, task_mgr, dashboard, cam

    from hospital_world import HospitalWorld
    from robot_agent import RobotAgent
    from human_agents import HumanAgent
    from task_manager import TaskManager
    from ui_dashboard import DashboardUI
    from navigation import get_all_room_nodes

    # --- Hospital environment ---
    hospital = HospitalWorld()

    # --- Robots ---
    RobotAgent.all_robots = []
    for i in range(5):
        robots.append(RobotAgent(i))

    # --- Humans ---
    HumanAgent.all_humans = []
    HumanAgent._id_counter = 0
    rooms = get_all_room_nodes()
    for i in range(15):
        humans.append(HumanAgent('patient', rooms[i % len(rooms)]))
    for i in range(6):
        humans.append(HumanAgent('doctor'))
    for i in range(6):
        humans.append(HumanAgent('nurse'))
    for i in range(6):
        humans.append(HumanAgent('visitor'))

    # --- Task manager ---
    task_mgr = TaskManager()

    # --- UI Dashboard ---
    dashboard = DashboardUI()

    # --- Camera ---
    cam = CameraController()



# ======================================================================
#  Main update loop
# ======================================================================
def update():
    global patients_assisted_count, stream_conn

    if stream_conn:
        try:
            tex = base.win.getDisplayRegion(0).getScreenshot()
            if tex:
                data = tex.getRamImageAs("RGBA").get_data()
                stream_conn.sendall(struct.pack("<LII", len(data), tex.getXSize(), tex.getYSize()))
                stream_conn.sendall(data)
        except Exception:
            stream_conn = None

    dt = time.dt
    if dt <= 0:
        return

    # Process async tasks from Ollama
    while pending_ollama_tasks:
        result = pending_ollama_tasks.pop(0)
        src = result.pop('_source', 'unknown')
        err = result.pop('_error', None)

        if 'error' in result:
            if dashboard:
                dashboard.show_feedback(f"[ERROR] {result['error']}", is_error=True)
                task_mgr.add_alert(f"Ollama failed: {result['error']}")
        else:
            task_mgr.create_task(
                task_type=result['task_type'],
                location_node=result['location_node'],
                priority=result['priority'],
                description=result['description'],
            )
            loc = result['location_node']
            tag = f"[AI:{src.upper()}]" if src == 'ollama' else "[FALLBACK]"
            if dashboard:
                dashboard.show_feedback(
                    f'{tag} Robot dispatched to {loc} ({result["task_type"]})'
                )
                task_mgr.add_alert(f'{tag} {result["description"]}')
            # Visual feedback: highlight room + snap camera
            _highlight_room(loc)
            if cam:
                cam.go_to_node(loc)

    # 1. Update humans
    for h in humans:
        h.update(dt)

    # 2. Auto-generate tasks from patients needing help
    task_mgr.auto_generate_from_humans(humans, dt)

    # 3. Assign tasks to available robots
    task_mgr.assign_tasks(robots)

    # 4. Update robots
    for r in robots:
        r.update(dt)

    # 5. Check completed tasks
    completed = task_mgr.check_completed(robots)
    for t in completed:
        patients_assisted_count += 1
        for h in humans:
            if h.current_node == t.location_node and h.needs_help:
                h.fulfill_help()
                break

    # 6. Update dashboard
    if dashboard:
        active_count = sum(1 for r in robots if r.state not in ('idle', 'charging'))
        metrics = task_mgr.get_metrics()
        dashboard.update_hud(active_count, len(robots), patients_assisted_count,
                             metrics['completed'], metrics['avg_response_time'])
        dashboard.update_queue(task_mgr.get_queue_display())
        dashboard.update_active(task_mgr.get_active_display())
        dashboard.update_robots([r.get_info() for r in robots])
        dashboard.update_alerts(task_mgr.get_recent_alerts())

        if dashboard.detail_visible and 0 <= selected_robot_index < len(robots):
            dashboard.show_robot_detail(robots[selected_robot_index].get_info())


# ======================================================================
#  Input handling
# ======================================================================
def input(key):
    global typing_mode, selected_robot_index

    if key == 'tab':
        typing_mode = not typing_mode
        if typing_mode:
            dashboard.cam_mode.text = 'TYPING MODE — Press TAB to exit'
        else:
            dashboard.cam_mode.text = 'CAM: Overview | Scroll=Zoom | Right-drag=Orbit | WASD=Pan'
        return

    if typing_mode:
        if key == 'enter':
            cmd = dashboard.get_and_clear_command()
            if cmd:
                handle_command(cmd)
        else:
            dashboard.handle_text_input(key)
        return

    # Click on robots
    if key == 'left mouse down':
        for i, r in enumerate(robots):
            if r.entity.hovered:
                selected_robot_index = i
                dashboard.show_robot_detail(r.get_info())
                break

    if key == 'escape':
        dashboard.hide_robot_detail()

    # Number keys to select robots
    for i in range(min(9, len(robots))):
        if key == str(i + 1):
            selected_robot_index = i
            dashboard.show_robot_detail(robots[i].get_info())


def _detect_ollama_model():
    """Auto-detect the best available Ollama model."""
    import urllib.request
    import json
    try:
        resp = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(resp.read().decode('utf-8'))
        models = [m['name'] for m in data.get('models', [])]
        # Prefer these in order
        for preferred in ['llama3.2', 'llama3.1', 'llama3', 'mistral', 'gemma2', 'phi3', 'qwen2']:
            for m in models:
                if preferred in m.lower():
                    return m
        if models:
            return models[0]
    except Exception:
        pass
    return 'llama3'

_ollama_model = _detect_ollama_model()

VALID_TASK_TYPES = {'assist_patient', 'deliver_medicine', 'guide_patient', 'security_check'}
VALID_LOCATIONS = None  # filled at runtime

def _get_valid_locations():
    global VALID_LOCATIONS
    if VALID_LOCATIONS is None:
        from navigation import get_all_nodes
        VALID_LOCATIONS = set(get_all_nodes().keys())
    return VALID_LOCATIONS

def _fallback_parse(text):
    """Keyword-based fallback when Ollama is unavailable."""
    text_lower = text.lower()
    text_nospace = text_lower.replace(" ", "")

    result = {
        'task_type': 'security_check',
        'location_node': 'MainHall',
        'priority': 2,
        'description': text,
    }

    if any(w in text_lower for w in ['medicine', 'deliver', 'pill', 'drug']):
        result['task_type'] = 'deliver_medicine'
        result['priority'] = 3
    elif any(w in text_lower for w in ['guide', 'escort', 'show', 'take']):
        result['task_type'] = 'guide_patient'
        result['priority'] = 1
    elif any(w in text_lower for w in ['emergency', 'urgent', 'stat', 'help']):
        result['task_type'] = 'assist_patient'
        result['priority'] = 4

    for node in _get_valid_locations():
        if node.lower() in text_nospace:
            result['location_node'] = node
            break
    else:
        aliases = {
            'er': 'EmergencyRoom', 'emergency': 'EmergencyRoom',
            'reception': 'Reception', 'front': 'Reception',
            'waiting': 'WaitingHall', 'hall': 'MainHall',
            'dock': 'ChargingDock', 'pharmacy': 'Pharmacy',
        }
        for alias, actual in aliases.items():
            if alias in text_lower:
                result['location_node'] = actual
                break

    return result

def _validate_ollama_response(parsed, original_text):
    """Validate and sanitize Ollama JSON response."""
    valid_locs = _get_valid_locations()

    if parsed.get('task_type') not in VALID_TASK_TYPES:
        parsed['task_type'] = 'security_check'
    if parsed.get('location_node') not in valid_locs:
        # Try to fix common issues like "Room 5" -> "Room5"
        loc = str(parsed.get('location_node', '')).replace(' ', '')
        if loc in valid_locs:
            parsed['location_node'] = loc
        else:
            fb = _fallback_parse(original_text)
            parsed['location_node'] = fb['location_node']
    if not isinstance(parsed.get('priority'), int) or parsed['priority'] < 1 or parsed['priority'] > 4:
        parsed['priority'] = 2
    if 'description' not in parsed or not parsed['description']:
        parsed['description'] = original_text

    return parsed

def _highlight_room(node_name):
    """Flash a glow ring at the target room for visual feedback."""
    from navigation import get_node_position
    try:
        x, z = get_node_position(node_name)
        ring = Entity(
            model='cube', scale=(8, 0.15, 8),
            position=(x, 0.2, z),
            color=color.rgb32(0, 255, 200), unlit=True, alpha=0.5,
        )
        ring.animate_scale((12, 0.15, 12), duration=1.0, curve=curve.out_expo)
        ring.animate('alpha', 0, duration=1.5, curve=curve.linear)
        destroy(ring, delay=2.0)
    except Exception:
        pass

def query_ollama_thread(text):
    """Run Ollama API request in a background thread."""
    import urllib.request
    import json

    prompt = f"""You are the AI brain of a hospital digital twin. Parse the user's command into JSON.

EXACT FORMAT (no other keys):
{{"task_type": "assist_patient"|"deliver_medicine"|"guide_patient"|"security_check", "location_node": "<valid node>", "priority": <1-4>, "description": "<summary>"}}

VALID LOCATIONS: Room1-Room22, ICU1-ICU4, Pharmacy, EmergencyRoom, Reception, WaitingHall, MainHall, ChargingDock, StaffOffice, Entrance
RULES:
- "go to room 5" → {{"task_type":"security_check","location_node":"Room5","priority":2,"description":"Navigate to Room 5"}}
- "emergency in ICU 2" → {{"task_type":"assist_patient","location_node":"ICU2","priority":4,"description":"Emergency response ICU 2"}}
- "deliver medicine to room 12" → {{"task_type":"deliver_medicine","location_node":"Room12","priority":3,"description":"Medicine delivery Room 12"}}
- Always combine "room" + number into "RoomN" (no space).

USER COMMAND: "{text}"

Reply with ONLY the JSON object. No markdown, no backticks, no explanation."""

    data = json.dumps({
        "model": _ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }).encode('utf-8')

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        response = urllib.request.urlopen(req, timeout=15)
        result_json = json.loads(response.read().decode('utf-8'))
        response_text = result_json.get("response", "{}")
        parsed = json.loads(response_text)
        parsed = _validate_ollama_response(parsed, text)
        parsed['_source'] = 'ollama'
        pending_ollama_tasks.append(parsed)
    except Exception as e:
        # Fallback to keyword parsing
        fb = _fallback_parse(text)
        fb['_source'] = 'fallback'
        fb['_error'] = str(e)
        pending_ollama_tasks.append(fb)

def handle_command(text):
    """Trigger background Ollama parsing for natural language commands."""
    import threading
    if dashboard:
        dashboard.show_feedback(f"[AI] Sending to {_ollama_model}...")
    threading.Thread(target=query_ollama_thread, args=(text,), daemon=True).start()


def run_integrated_simulation():
    """Launch 3D twin."""
    app = Ursina(
        title='FARS Campus Digital Twin',
        borderless=False,
        fullscreen=False,
        development_mode=False,
        size=(1920, 1080),
    )
    # NO shader — use Ursina's flat color rendering (guaranteed to work)
    window.color = color.rgb32(18, 22, 32)
    window.fps_counter.enabled = True
    setup()
    for r in robots:
        r.entity.collider = 'box'
    app.run()


# ======================================================================
#  Entry point (standalone 3D only)
# ======================================================================
if __name__ == '__main__':
    run_integrated_simulation()
