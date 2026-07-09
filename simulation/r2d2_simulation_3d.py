from ursina import *
from ursina.shaders import lit_with_shadows_shader
from ursina.shaders.screenspace_shaders.ssao import ssao_shader
import random
import math

app = Ursina(title='R2D2 Multi-Agent Simulation', borderless=False)
Entity.default_shader = lit_with_shadows_shader

# Lighting
# Scene Setup
Sky()
sun = DirectionalLight(y=10, rotation=(45, -45, 45), shadows=True)
AmbientLight(color=color.rgba(100, 100, 120, 255) * 0.2)
camera.shader = ssao_shader # Apply SSAO for realism
lit_with_shadows_shader.default_input['shadow_color'] = color.rgba(0,0,0,100) # Softer shadows
sun.look_at(Vec3(1, -1, 1))

# Environment
Sky()

# Camera setup - isometric-like view
camera.orthographic = False
camera.fov = 60
camera.position = (0, 25, -30)
camera.rotation_x = 45

# Colors for R2D2s
R2D2_COLORS = [
    color.rgb(70/255, 130/255, 200/255),   # Blue
    color.rgb(200/255, 80/255, 80/255),    # Red
    color.rgb(80/255, 180/255, 80/255),    # Green
    color.rgb(200/255, 150/255, 50/255),   # Gold
    color.rgb(150/255, 80/255, 180/255),   # Purple
]

class RoboticArm(Entity):
    def __init__(self, parent_bot, bot_color, **kwargs):
        super().__init__(parent=parent_bot, **kwargs)
        self.parent_bot = parent_bot
        
        # Arm segments using cubes
        self.shoulder = Entity(
            parent=self,
            model='cube',
            color=color.gray,
            scale=(0.12, 0.12, 0.35),
            position=(0.35, 0.3, 0),
            rotation=(0, 0, 45)
        )
        
        self.forearm = Entity(
            parent=self.shoulder,
            model='cube',
            color=color.dark_gray,
            scale=(0.7, 0.7, 0.7),
            position=(0, 0, 0.4),
        )
        
        self.gripper_left = Entity(
            parent=self.forearm,
            model='cube',
            color=bot_color,
            scale=(0.25, 0.4, 0.25),
            position=(0.12, 0, 0.4)
        )
        
        self.gripper_right = Entity(
            parent=self.forearm,
            model='cube',
            color=bot_color,
            scale=(0.25, 0.4, 0.25),
            position=(-0.12, 0, 0.4)
        )
        
        self.target_shoulder_angle = 45
        self.target_forearm_angle = 0
        self.gripper_open = True
        
    def update(self):
        # Smooth arm movement
        self.shoulder.rotation_z = lerp(self.shoulder.rotation_z, self.target_shoulder_angle, time.dt * 5)
        self.forearm.rotation_x = lerp(self.forearm.rotation_x, self.target_forearm_angle, time.dt * 5)
        
        # Gripper animation
        target_offset = 0.18 if self.gripper_open else 0.06
        self.gripper_left.x = lerp(self.gripper_left.x, target_offset, time.dt * 8)
        self.gripper_right.x = lerp(self.gripper_right.x, -target_offset, time.dt * 8)

class R2D2(Entity):
    def __init__(self, position, bot_id, **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.bot_id = bot_id
        self.bot_color = R2D2_COLORS[bot_id]
        self.is_selected = False
        self.speed = 5
        self.turn_speed = 120
        
        # AI behavior
        self.state = 'wandering'
        self.target_pos = None
        self.state_timer = 0
        self.work_timer = 0
        
        # Body parts
        self._create_body()
        
        # Robotic arm
        self.arm = RoboticArm(self, self.bot_color)
        
        # Selection indicator (flat box on ground)
        self.selection_ring = Entity(
            parent=self,
            model='cube',
            color=color.rgba(100/255, 200/255, 255/255, 150/255),
            scale=(2.2, 0.05, 2.2),
            y=0.03,
            visible=False
        )
        
        # Name tag
        self.name_tag = Text(
            text=f'R2-D{bot_id + 2}',
            parent=self,
            y=2.8,
            scale=12,
            billboard=True,
            color=self.bot_color
        )
        
        # Eye glow
        self.eye_glow_time = random.random() * 6.28
        
        # Make clickable
        self.collider = 'box'
        self.collider = BoxCollider(self, size=(1.2, 2, 1.2))
        
    def _create_body(self):
        # Visual parts
        self.body = Entity(parent=self, model='cube', scale=(1, 1.2, 1), color=color.white, specular=0.8, shininess=32)
        self.dome = Entity(parent=self, model='sphere', scale=(1.2, 0.6, 1.2), position=(0, 0.6, 0), color=color.gray, specular=1.0, shininess=64)
        
        # Add "Legs"
        for side in [-1, 1]:
            Entity(parent=self, model='cube', scale=(0.2, 1.0, 0.4), position=(side*0.5, 0, 0), color=color.white, specular=0.5)
        
        # Add "Eye"
        self.eye = Entity(parent=self, model='sphere', scale=0.15, position=(0, 0.8, 0.5), color=color.red, unlit=True)
        
        self.eye_lens = Entity(
            parent=self.eye,
            model='sphere',
            color=self.bot_color,
            scale=0.6,
            z=0.25
        )
        
        # Antenna - using cubes instead of cylinder
        self.antenna_base = Entity(
            parent=self.dome,
            model='cube',
            color=color.gray,
            scale=(0.06, 0.25, 0.06),
            y=0.35
        )
        
        self.antenna_tip = Entity(
            parent=self.antenna_base,
            model='sphere',
            color=self.bot_color,
            scale=1.8,
            y=0.6
        )
        
        # Legs/treads - using cubes
        for side in [-1, 1]:
            # Main leg
            leg = Entity(
                parent=self,
                model='cube',
                color=color.dark_gray,
                scale=(0.18, 1.0, 0.45),
                position=(side * 0.45, 0.5, 0)
            )
            
            # Wheel details - small cubes as treads
            for wy in [-0.3, 0, 0.3]:
                Entity(
                    parent=leg,
                    model='cube',
                    color=color.gray,
                    scale=(1.3, 0.25, 0.9),
                    y=wy
                )
    
    def update(self):
        
        self.eye_glow_time += time.dt * 2
        glow = (math.sin(self.eye_glow_time) + 1) * 0.3 + 0.4
        self.eye_lens.color = color.rgb(
            self.bot_color.r * glow,
            self.bot_color.g * glow,
            self.bot_color.b * glow
        )
        
        # Antenna bob
        self.antenna_tip.y = 0.6 + math.sin(time.time() * 3 + self.bot_id) * 0.08
        
        # Selection ring
        self.selection_ring.visible = self.is_selected
        if self.is_selected:
            pulse = 2.2 + math.sin(time.time() * 4) * 0.15
            self.selection_ring.scale_x = pulse
            self.selection_ring.scale_z = pulse
        
        if self.is_selected:
            self._handle_input()
        else:
            self._autonomous_behavior()
            
        # Keep within bounds
        self.x = clamp(self.x, -18, 18)
        self.z = clamp(self.z, -18, 18)
        
    def _handle_input(self):
        # Movement
        move_dir = Vec3(0, 0, 0)
        
        if held_keys['up arrow'] or held_keys['w']:
            move_dir += self.forward
        if held_keys['down arrow'] or held_keys['s']:
            move_dir -= self.forward * 0.5
        if held_keys['left arrow'] or held_keys['a']:
            self.rotation_y -= self.turn_speed * time.dt
        if held_keys['right arrow'] or held_keys['d']:
            self.rotation_y += self.turn_speed * time.dt
            
        # Apply movement
        if move_dir.length() > 0:
            self.position += move_dir.normalized() * self.speed * time.dt
            
        # Arm control
        if held_keys['i']:
            self.arm.target_forearm_angle = clamp(self.arm.target_forearm_angle - 60 * time.dt, -45, 45)
        if held_keys['k']:
            self.arm.target_forearm_angle = clamp(self.arm.target_forearm_angle + 60 * time.dt, -45, 45)
        if held_keys['j']:
            self.arm.target_shoulder_angle = clamp(self.arm.target_shoulder_angle + 60 * time.dt, 0, 90)
        if held_keys['l']:
            self.arm.target_shoulder_angle = clamp(self.arm.target_shoulder_angle - 60 * time.dt, 0, 90)
        if held_keys['space']:
            self.arm.gripper_open = False
        else:
            self.arm.gripper_open = True
            
    def _autonomous_behavior(self):
        self.state_timer += time.dt
        
        if self.state == 'wandering':
            if self.target_pos is None or distance(self.position, self.target_pos) < 1.5 or self.state_timer > 6:
                self.target_pos = Vec3(
                    random.uniform(-15, 15),
                    0,
                    random.uniform(-15, 15)
                )
                self.state_timer = 0
                
                # Chance to work
                if random.random() < 0.25:
                    self.state = 'working'
                    self.work_timer = 0
                    
            self._move_towards_target()
            
            # Idle arm animation
            self.arm.target_shoulder_angle = 45 + math.sin(time.time() * 2 + self.bot_id) * 15
            self.arm.target_forearm_angle = math.sin(time.time() * 1.5 + self.bot_id) * 20
            
        elif self.state == 'working':
            self.work_timer += time.dt
            
            # Working arm animation
            self.arm.target_shoulder_angle = 30 + math.sin(self.work_timer * 4) * 20
            self.arm.target_forearm_angle = -20 + math.sin(self.work_timer * 3) * 15
            self.arm.gripper_open = math.sin(self.work_timer * 2) > 0
            
            # Slight rotation while working
            self.rotation_y += math.sin(self.work_timer * 2) * 25 * time.dt
            
            if self.work_timer > 4:
                self.state = 'wandering'
                self.state_timer = 0
                self.arm.gripper_open = True
                
    def _move_towards_target(self):
        if self.target_pos is None:
            return
            
        # Calculate direction to target
        direction = self.target_pos - self.position
        direction.y = 0
        
        if direction.length() > 0.5:
            # Calculate target angle
            target_angle = math.degrees(math.atan2(direction.x, direction.z))
            
            # Smooth rotation
            angle_diff = (target_angle - self.rotation_y + 180) % 360 - 180
            turn_amount = min(abs(angle_diff), self.turn_speed * time.dt)
            if angle_diff > 0:
                self.rotation_y += turn_amount
            else:
                self.rotation_y -= turn_amount
                
            # Move forward if roughly facing target
            if abs(angle_diff) < 30:
                self.position += self.forward * self.speed * time.dt * 0.7
                
    def on_click(self):
        global selected_bot
        
        # Deselect previous
        if selected_bot:
            selected_bot.is_selected = False
            
        # Select this one
        self.is_selected = True
        selected_bot = self

class Obstacle(Entity):
    def __init__(self, position, size, **kwargs):
        super().__init__(**kwargs)
        self.position = position
        
        # Main block
        self.model = 'cube'
        self.color = color.rgb(60/255, 70/255, 85/255)
        self.scale = size
        self.collider = 'box'
        self.specular = 0.2
        
        # Top highlight
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(90/255, 100/255, 120/255), # Lighter highlight
            scale=(0.98, 0.08, 0.98),
            y=0.5
        )

class Resource(Entity):
    def __init__(self, position, **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.phase = random.random() * 6.28
        
        # Glowing orb
        self.orb = Entity(
            parent=self,
            model='sphere',
            color=color.rgb(100/255, 255/255, 180/255),
            scale=0.35,
            unlit=True # Keep it glowing regardless of light
        )
        
        # Outer glow - slightly transparent
        self.glow = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(100/255, 255/255, 180/255, 50/255),
            scale=0.7,
            unlit=True
        )
        
        # Ground marker - flat cube
        self.ring = Entity(
            parent=self,
            model='cube',
            color=color.rgba(100/255, 255/255, 180/255, 100/255),
            scale=(1.2, 0.02, 1.2),
            y=0.01,
            unlit=True
        )
        
    def update(self):
        self.phase += time.dt * 2
        self.orb.y = 0.5 + math.sin(self.phase) * 0.15
        self.glow.scale = 0.7 + math.sin(self.phase * 1.5) * 0.15
        self.orb.rotation_y += 25 * time.dt

# Global selected bot
selected_bot = None

# Create ground with click-to-deselect
def deselect_bot():
    global selected_bot
    if selected_bot:
        selected_bot.is_selected = False
        selected_bot = None

ground = Entity(
    model='plane',
    scale=50,
    color=color.rgb(30/255, 35/255, 45/255),
    texture='white_cube',
    texture_scale=(25, 25),
    collider='box',
    receive_shadows=True
)
ground.on_click = deselect_bot

# Grid lines on ground using a grid of cubes
for i in range(-20, 21, 2):
    # X lines
    Entity(
        model='cube',
        scale=(0.02, 0.01, 40),
        position=(i, 0.005, 0),
        color=color.rgba(60/255, 70/255, 90/255, 150/255)
    )
    # Z lines
    Entity(
        model='cube',
        scale=(40, 0.01, 0.02),
        position=(0, 0.005, i),
        color=color.rgba(60/255, 70/255, 90/255, 150/255)
    )

# Create walls (arena boundaries)
wall_color = color.rgb(50/255, 60/255, 75/255)
wall_height = 2
wall_thickness = 0.5
arena_size = 20

# Walls
Entity(model='cube', scale=(arena_size*2+1, wall_height, wall_thickness), position=(0, wall_height/2, arena_size), color=wall_color)
Entity(model='cube', scale=(arena_size*2+1, wall_height, wall_thickness), position=(0, wall_height/2, -arena_size), color=wall_color)
Entity(model='cube', scale=(wall_thickness, wall_height, arena_size*2+1), position=(arena_size, wall_height/2, 0), color=wall_color)
Entity(model='cube', scale=(wall_thickness, wall_height, arena_size*2+1), position=(-arena_size, wall_height/2, 0), color=wall_color)

# Create R2D2 bots
bots = []
spawn_positions = [
    Vec3(-8, 0, -8),
    Vec3(8, 0, -8),
    Vec3(0, 0, 0),
    Vec3(-8, 0, 8),
    Vec3(8, 0, 8),
]

for i, pos in enumerate(spawn_positions):
    bot = R2D2(position=pos, bot_id=i)
    bots.append(bot)

# Create obstacles
obstacles = [
    Obstacle(position=Vec3(-5, 1, 5), size=(3, 2, 3)),
    Obstacle(position=Vec3(7, 0.75, -3), size=(2, 1.5, 4)),
    Obstacle(position=Vec3(-10, 1.25, -10), size=(4, 2.5, 2)),
    Obstacle(position=Vec3(12, 0.5, 10), size=(3, 1, 3)),
    Obstacle(position=Vec3(0, 0.75, -12), size=(5, 1.5, 2)),
]

# Create resources
resources = [
    Resource(position=Vec3(-12, 0, 0)),
    Resource(position=Vec3(12, 0, 5)),
    Resource(position=Vec3(0, 0, 12)),
    Resource(position=Vec3(-6, 0, -15)),
    Resource(position=Vec3(15, 0, -10)),
    Resource(position=Vec3(5, 0, 8)),
]

# UI Panel
class UI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        
        # Title
        self.title = Text(
            text='R2D2 MULTI-AGENT 3D SIMULATION',
            position=(-0.85, 0.45),
            scale=1.3,
            color=color.rgba(200/255, 210/255, 230/255, 255/255)
        )
        
        # Instructions panel background
        self.panel_bg = Entity(
            parent=self,
            model='quad',
            color=color.rgba(30/255, 38/255, 50/255, 200/255),
            scale=(0.38, 0.22),
            position=(0.65, 0.37)
        )
        
        # Instructions
        instructions = [
            "Click robot to select",
            "Arrow keys: Move robot",
            "I/J/K/L: Control arm",
            "SPACE: Close gripper",
            "TAB: Cycle | ESC: Deselect",
            "Right-drag: Orbit camera"
        ]
        
        for i, text in enumerate(instructions):
            Text(
                text=text,
                parent=self,
                position=(0.49, 0.43 - i * 0.04),
                scale=0.75,
                color=color.rgba(180/255, 190/255, 210/255, 255/255)
            )
        
        # Status text
        self.status = Text(
            text='ALL BOTS AUTONOMOUS',
            position=(-0.85, -0.42),
            scale=1.1,
            color=color.rgba(100/255, 200/255, 150/255, 255/255)
        )
        
        # Bot status list
        self.bot_status_texts = []
        for i in range(5):
            txt = Text(
                text=f'R2-D{i+2}: WANDERING',
                parent=self,
                position=(-0.85, 0.35 - i * 0.05),
                scale=0.85,
                color=R2D2_COLORS[i]
            )
            self.bot_status_texts.append(txt)
            
    def update(self):
        
        if selected_bot:
            self.status.text = f'CONTROLLING: R2-D{selected_bot.bot_id + 2}'
            self.status.color = selected_bot.bot_color
        else:
            self.status.text = 'ALL BOTS AUTONOMOUS'
            self.status.color = color.rgba(100/255, 200/255, 150/255, 255/255)
            
        # Update bot status
        for i, bot in enumerate(bots):
            state = "SELECTED" if bot.is_selected else bot.state.upper()
            self.bot_status_texts[i].text = f'R2-D{i+2}: {state}'

ui = UI()

# Camera controller for orbiting
class CameraController(Entity):
    def __init__(self):
        super().__init__()
        self.rotation_speed = 80
        self.distance = 35
        self.angle_x = 45
        self.angle_y = 0
        self.target = Vec3(0, 0, 0)
        
    def update(self):
        # Mouse orbit when right-click held
        if mouse.right:
            self.angle_y += mouse.velocity[0] * self.rotation_speed
            self.angle_x -= mouse.velocity[1] * self.rotation_speed
            self.angle_x = clamp(self.angle_x, 15, 75)
        
        # Zoom with +/- keys
        if held_keys['='] or held_keys['+']:
            self.distance -= 15 * time.dt
        if held_keys['-']:
            self.distance += 15 * time.dt
        self.distance = clamp(self.distance, 15, 55)
        
        # Calculate camera position
        rad_x = math.radians(self.angle_x)
        rad_y = math.radians(self.angle_y)
        
        camera.position = Vec3(
            self.target.x + self.distance * math.sin(rad_y) * math.cos(rad_x),
            self.target.y + self.distance * math.sin(rad_x),
            self.target.z + self.distance * math.cos(rad_y) * math.cos(rad_x)
        )
        camera.look_at(self.target)

cam_controller = CameraController()

def input(key):
    global selected_bot
    
    if key == 'escape':
        if selected_bot:
            selected_bot.is_selected = False
            selected_bot = None
        else:
            application.quit()
            
    if key == 'tab':
        if selected_bot:
            current_idx = bots.index(selected_bot)
            selected_bot.is_selected = False
            next_idx = (current_idx + 1) % len(bots)
            bots[next_idx].is_selected = True
            selected_bot = bots[next_idx]
        else:
            bots[0].is_selected = True
            selected_bot = bots[0]

# Sky color
window.color = color.rgb(18/255, 22/255, 32/255)

# Print controls
print("=" * 60)
print("R2D2 3D MULTI-AGENT SIMULATION")
print("=" * 60)
print("\nControls:")
print("  Left-click on a robot to select it")
print("  Right-click + drag to orbit camera")
print("  Arrow keys or WASD: Move selected robot")
print("  I/K: Arm up/down | J/L: Arm rotate")
print("  SPACE: Close gripper")
print("  TAB: Cycle through robots")
print("  Scroll: Zoom in/out")
print("  ESC: Deselect (or quit if none selected)")
print("\nStarting 3D simulation...")
print("=" * 60)

app.run()
