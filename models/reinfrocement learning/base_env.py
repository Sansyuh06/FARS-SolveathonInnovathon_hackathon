from ursina import *

class BipedBot(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # The torso is the root physical body.
        # It sits above the ground (y=2 is standing height).
        self.torso = Entity(parent=self, model='cube', color=color.cyan, scale=(0.8, 1.0, 0.5), y=2)
        
        # Head (helps identify forward direction)
        self.head = Entity(parent=self.torso, model='cube', color=color.white, scale=(0.5, 0.5, 0.5), y=0.7, z=0.1)
        self.eye = Entity(parent=self.head, model='cube', color=color.black, scale=(0.4, 0.1, 0.1), y=0.1, z=0.26)

        # LEFT LEG
        # Hip joint is positioned relative to the torso
        self.l_hip = Entity(parent=self.torso, position=(-0.25, -0.5, 0))
        # Upper leg is drawn downwards from the hip
        self.l_upper = Entity(parent=self.l_hip, model='cube', color=color.gray, scale=(0.25, 0.9, 0.25), position=(0, -0.45, 0))
        
        # Knee joint is at the bottom of the upper leg
        self.l_knee = Entity(parent=self.l_upper, position=(0, -0.45, 0))
        # Lower leg is drawn downwards from the knee
        self.l_lower = Entity(parent=self.l_knee, model='cube', color=color.dark_gray, scale=(0.2, 0.8, 0.2), position=(0, -0.4, 0))
        # Foot
        self.l_foot = Entity(parent=self.l_lower, model='cube', color=color.black, scale=(0.25, 0.15, 0.4), position=(0, -0.4, 0.1))


        # RIGHT LEG
        self.r_hip = Entity(parent=self.torso, position=(0.25, -0.5, 0))
        self.r_upper = Entity(parent=self.r_hip, model='cube', color=color.gray, scale=(0.25, 0.9, 0.25), position=(0, -0.45, 0))
        
        self.r_knee = Entity(parent=self.r_upper, position=(0, -0.45, 0))
        self.r_lower = Entity(parent=self.r_knee, model='cube', color=color.dark_gray, scale=(0.2, 0.8, 0.2), position=(0, -0.4, 0))
        # Foot
        self.r_foot = Entity(parent=self.r_lower, model='cube', color=color.black, scale=(0.25, 0.15, 0.4), position=(0, -0.4, 0.1))

    def apply_joints(self, l_hip_x, l_knee_x, r_hip_x, r_knee_x, torso_y=2.0, torso_rot_x=0.0, torso_rot_z=0.0):
        """Apply joint rotations and torso position/rotation"""
        self.l_hip.rotation_x = l_hip_x
        self.l_knee.rotation_x = l_knee_x
        self.r_hip.rotation_x = r_hip_x
        self.r_knee.rotation_x = r_knee_x
        
        self.torso.y = torso_y
        self.torso.rotation_x = torso_rot_x
        self.torso.rotation_z = torso_rot_z

class RLHUD(Entity):
    def __init__(self, duration_text="1hr", **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        
        # Top-left HUD panel
        self.panel = Entity(parent=self, model='quad', color=color.rgba(10, 12, 18, 220), 
                            scale=(0.5, 0.2), origin=(-0.5, 0.5), position=(-0.85, 0.45))
                            
        self.dur_text = Text(parent=self.panel, text=f"TRAINING TIME: {duration_text}", position=(0.05, -0.15), scale=6, color=color.cyan)
        self.ep_text = Text(parent=self.panel, text="Episode: 0", position=(0.05, -0.45), scale=5, color=color.light_gray)
        self.rew_text = Text(parent=self.panel, text="Reward: 0.00", position=(0.05, -0.7), scale=5, color=color.light_gray)

    def update_metrics(self, episode, reward):
        self.ep_text.text = f"Episode: {int(episode)}"
        
        rew_color = color.green if reward > 0 else (color.red if reward < -5 else color.light_gray)
        self.rew_text.text = f"Reward: {reward:.2f}"
        self.rew_text.color = rew_color

def setup_environment():
    """Sets up the lighting, camera, and infinite grid floor to mimic RL environments like MuJoCo."""
    # Floor (Checkerboard pattern)
    floor = Entity(model='plane', scale=(100, 1, 100), color=color.rgba(40, 45, 55, 255), collider='box')
    
    # Draw a grid on the floor using lines (simulating PyBullet/MuJoCo floor)
    for i in range(-20, 21):
        Entity(model='cube', color=color.rgba(255,255,255,30), scale=(40, 0.01, 0.05), position=(0, 0.01, i))
        Entity(model='cube', color=color.rgba(255,255,255,30), scale=(0.05, 0.01, 40), position=(i, 0.01, 0))
    
    # Camera setup (isometric/side-following angle)
    camera.position = (8, 6, -8)
    camera.look_at((0, 1, 0))
    camera.fov = 40
    
    # Lighting
    DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
    AmbientLight(color=color.rgba(100, 100, 100, 255))
    
    # Simple sky color
    window.color = color.rgba(20, 24, 30, 255)
