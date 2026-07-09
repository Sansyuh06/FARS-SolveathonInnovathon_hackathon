import pygame
import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors - Modern aesthetic palette
BACKGROUND = (20, 25, 35)
FLOOR_COLOR = (35, 42, 55)
GRID_COLOR = (45, 55, 70)
SHADOW_COLOR = (15, 18, 25)

# R2D2 Colors
R2D2_COLORS = [
    {'body': (70, 130, 200), 'accent': (200, 220, 255), 'light': (100, 200, 255)},  # Classic Blue
    {'body': (200, 80, 80), 'accent': (255, 180, 180), 'light': (255, 100, 100)},   # Red
    {'body': (80, 180, 80), 'accent': (180, 255, 180), 'light': (100, 255, 100)},   # Green
    {'body': (200, 150, 50), 'accent': (255, 220, 150), 'light': (255, 200, 50)},   # Gold
    {'body': (150, 80, 180), 'accent': (220, 180, 255), 'light': (200, 100, 255)},  # Purple
]

# Objects in environment
OBSTACLE_COLOR = (60, 70, 85)
RESOURCE_COLOR = (80, 200, 150)
SELECTED_GLOW = (100, 200, 255)

@dataclass
class Vec2:
    x: float
    y: float
    
    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vec2(self.x * scalar, self.y * scalar)
    
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self):
        length = self.length()
        if length > 0:
            return Vec2(self.x / length, self.y / length)
        return Vec2(0, 0)
    
    def to_tuple(self):
        return (int(self.x), int(self.y))

class RoboticArm:
    def __init__(self):
        self.base_angle = 0
        self.elbow_angle = 45
        self.gripper_open = 1.0
        self.target_base_angle = 0
        self.target_elbow_angle = 45
        self.carrying_resource = False
        self.arm_length1 = 25
        self.arm_length2 = 20
        
    def update(self, dt):
        # Smooth arm movement
        self.base_angle += (self.target_base_angle - self.base_angle) * 5 * dt
        self.elbow_angle += (self.target_elbow_angle - self.elbow_angle) * 5 * dt
        
    def set_target(self, base_angle, elbow_angle):
        self.target_base_angle = base_angle
        self.target_elbow_angle = elbow_angle
        
    def draw(self, surface, base_pos, facing_angle, color_scheme):
        # Calculate arm positions
        arm_base = Vec2(
            base_pos.x + math.cos(math.radians(facing_angle)) * 15,
            base_pos.y + math.sin(math.radians(facing_angle)) * 15
        )
        
        total_angle1 = facing_angle + self.base_angle
        joint1 = Vec2(
            arm_base.x + math.cos(math.radians(total_angle1)) * self.arm_length1,
            arm_base.y + math.sin(math.radians(total_angle1)) * self.arm_length1
        )
        
        total_angle2 = total_angle1 + self.elbow_angle
        end_effector = Vec2(
            joint1.x + math.cos(math.radians(total_angle2)) * self.arm_length2,
            joint1.y + math.sin(math.radians(total_angle2)) * self.arm_length2
        )
        
        # Draw arm segments
        pygame.draw.line(surface, (80, 90, 100), arm_base.to_tuple(), joint1.to_tuple(), 6)
        pygame.draw.line(surface, (100, 110, 120), joint1.to_tuple(), end_effector.to_tuple(), 4)
        
        # Draw joints
        pygame.draw.circle(surface, color_scheme['accent'], arm_base.to_tuple(), 5)
        pygame.draw.circle(surface, (120, 130, 140), joint1.to_tuple(), 4)
        
        # Draw gripper
        gripper_angle1 = total_angle2 + 30 * self.gripper_open
        gripper_angle2 = total_angle2 - 30 * self.gripper_open
        gripper_len = 8
        
        g1 = Vec2(
            end_effector.x + math.cos(math.radians(gripper_angle1)) * gripper_len,
            end_effector.y + math.sin(math.radians(gripper_angle1)) * gripper_len
        )
        g2 = Vec2(
            end_effector.x + math.cos(math.radians(gripper_angle2)) * gripper_len,
            end_effector.y + math.sin(math.radians(gripper_angle2)) * gripper_len
        )
        
        pygame.draw.line(surface, (150, 160, 170), end_effector.to_tuple(), g1.to_tuple(), 3)
        pygame.draw.line(surface, (150, 160, 170), end_effector.to_tuple(), g2.to_tuple(), 3)
        
        # Draw carried resource
        if self.carrying_resource:
            pygame.draw.circle(surface, RESOURCE_COLOR, end_effector.to_tuple(), 6)
        
        return end_effector

class R2D2:
    def __init__(self, x: float, y: float, bot_id: int):
        self.pos = Vec2(x, y)
        self.velocity = Vec2(0, 0)
        self.facing_angle = random.uniform(0, 360)
        self.bot_id = bot_id
        self.colors = R2D2_COLORS[bot_id]
        self.speed = 120
        self.turn_speed = 180
        
        # Body dimensions
        self.body_width = 30
        self.body_height = 45
        self.head_radius = 18
        
        # Animation
        self.wheel_rotation = 0
        self.head_rotation = 0
        self.blink_timer = 0
        self.is_blinking = False
        self.beep_timer = 0
        self.antenna_bob = 0
        
        # Robotic arm
        self.arm = RoboticArm()
        
        # AI behavior
        self.state = 'wandering'
        self.target_pos = None
        self.state_timer = 0
        self.work_progress = 0
        
        # Selection
        self.is_selected = False
        self.selection_pulse = 0
        
    def update(self, dt: float, is_controlled: bool, keys, obstacles: List, resources: List, other_bots: List):
        self.selection_pulse += dt * 3
        self.blink_timer += dt
        self.beep_timer += dt
        self.antenna_bob = math.sin(pygame.time.get_ticks() * 0.01) * 3
        
        # Blinking animation
        if self.blink_timer > random.uniform(2, 5):
            self.is_blinking = True
            self.blink_timer = 0
        if self.is_blinking and self.blink_timer > 0.1:
            self.is_blinking = False
            
        self.arm.update(dt)
        
        if is_controlled:
            self._handle_player_input(dt, keys)
        else:
            self._autonomous_behavior(dt, obstacles, resources, other_bots)
        
        # Apply velocity with collision detection
        new_pos = self.pos + self.velocity * dt
        
        # Check boundaries
        margin = 40
        new_pos.x = max(margin, min(SCREEN_WIDTH - margin, new_pos.x))
        new_pos.y = max(margin, min(SCREEN_HEIGHT - margin, new_pos.y))
        
        # Check obstacle collisions
        can_move = True
        for obs in obstacles:
            if self._check_obstacle_collision(new_pos, obs):
                can_move = False
                break
        
        # Check bot collisions
        for bot in other_bots:
            if bot != self:
                dist = (new_pos - bot.pos).length()
                if dist < 50:
                    can_move = False
                    # Push away
                    push_dir = (self.pos - bot.pos).normalize()
                    self.pos = self.pos + push_dir * 2
                    break
        
        if can_move:
            self.pos = new_pos
        
        # Wheel rotation based on movement
        if self.velocity.length() > 0:
            self.wheel_rotation += self.velocity.length() * dt * 2
            
    def _handle_player_input(self, dt: float, keys):
        self.velocity = Vec2(0, 0)
        
        # Movement
        if keys[pygame.K_UP]:
            self.velocity.x = math.cos(math.radians(self.facing_angle)) * self.speed
            self.velocity.y = math.sin(math.radians(self.facing_angle)) * self.speed
        if keys[pygame.K_DOWN]:
            self.velocity.x = -math.cos(math.radians(self.facing_angle)) * self.speed * 0.5
            self.velocity.y = -math.sin(math.radians(self.facing_angle)) * self.speed * 0.5
        if keys[pygame.K_LEFT]:
            self.facing_angle -= self.turn_speed * dt
        if keys[pygame.K_RIGHT]:
            self.facing_angle += self.turn_speed * dt
            
        # Arm control with WASD
        if keys[pygame.K_w]:
            self.arm.target_elbow_angle = max(-60, self.arm.target_elbow_angle - 90 * dt)
        if keys[pygame.K_s]:
            self.arm.target_elbow_angle = min(90, self.arm.target_elbow_angle + 90 * dt)
        if keys[pygame.K_a]:
            self.arm.target_base_angle = max(-90, self.arm.target_base_angle - 90 * dt)
        if keys[pygame.K_d]:
            self.arm.target_base_angle = min(90, self.arm.target_base_angle + 90 * dt)
        if keys[pygame.K_SPACE]:
            self.arm.gripper_open = 0.2
        else:
            self.arm.gripper_open = 1.0
            
    def _autonomous_behavior(self, dt: float, obstacles: List, resources: List, other_bots: List):
        self.state_timer += dt
        
        if self.state == 'wandering':
            # Random wandering behavior
            if self.target_pos is None or (self.pos - self.target_pos).length() < 30 or self.state_timer > 5:
                self.target_pos = Vec2(
                    random.uniform(100, SCREEN_WIDTH - 100),
                    random.uniform(100, SCREEN_HEIGHT - 100)
                )
                self.state_timer = 0
                
                # Chance to switch to working state
                if random.random() < 0.3 and resources:
                    self.state = 'seeking_resource'
                    self.target_pos = random.choice(resources).copy()
            
            self._move_towards_target(dt)
            
            # Idle arm animation
            self.arm.target_base_angle = math.sin(pygame.time.get_ticks() * 0.002) * 20
            self.arm.target_elbow_angle = 30 + math.cos(pygame.time.get_ticks() * 0.003) * 15
            
        elif self.state == 'seeking_resource':
            if self.target_pos:
                self._move_towards_target(dt)
                dist = (self.pos - self.target_pos).length()
                
                # Working animation - reach towards resource
                self.arm.target_base_angle = 0
                self.arm.target_elbow_angle = -30
                
                if dist < 50:
                    self.state = 'working'
                    self.state_timer = 0
                    self.work_progress = 0
                    
            if self.state_timer > 10:
                self.state = 'wandering'
                self.state_timer = 0
                
        elif self.state == 'working':
            self.velocity = Vec2(0, 0)
            self.work_progress += dt
            
            # Working arm animation - grabbing motion
            phase = (self.work_progress * 2) % 2
            if phase < 1:
                self.arm.target_elbow_angle = -40
                self.arm.gripper_open = 1.0
            else:
                self.arm.target_elbow_angle = -20
                self.arm.gripper_open = 0.2
            
            self.arm.target_base_angle = math.sin(self.work_progress * 3) * 30
            
            if self.work_progress > 3:
                self.state = 'wandering'
                self.state_timer = 0
                
        elif self.state == 'interacting':
            # Social behavior with other bots
            if self.target_pos:
                dist = (self.pos - self.target_pos).length()
                if dist > 80:
                    self._move_towards_target(dt)
                else:
                    self.velocity = Vec2(0, 0)
                    # Wave arm!
                    self.arm.target_base_angle = math.sin(pygame.time.get_ticks() * 0.01) * 45
                    self.arm.target_elbow_angle = -30
                    
            if self.state_timer > 4:
                self.state = 'wandering'
                self.state_timer = 0
                
    def _move_towards_target(self, dt: float):
        if self.target_pos is None:
            return
            
        direction = self.target_pos - self.pos
        distance = direction.length()
        
        if distance > 5:
            # Calculate target angle
            target_angle = math.degrees(math.atan2(direction.y, direction.x))
            
            # Smooth turn towards target
            angle_diff = (target_angle - self.facing_angle + 180) % 360 - 180
            turn_amount = min(abs(angle_diff), self.turn_speed * dt)
            if angle_diff > 0:
                self.facing_angle += turn_amount
            else:
                self.facing_angle -= turn_amount
                
            # Move forward if roughly facing target
            if abs(angle_diff) < 45:
                speed_factor = 1.0 if abs(angle_diff) < 15 else 0.5
                self.velocity = Vec2(
                    math.cos(math.radians(self.facing_angle)) * self.speed * speed_factor,
                    math.sin(math.radians(self.facing_angle)) * self.speed * speed_factor
                )
            else:
                self.velocity = Vec2(0, 0)
                
    def _check_obstacle_collision(self, pos: Vec2, obstacle: pygame.Rect) -> bool:
        # Simple circle-rect collision
        closest_x = max(obstacle.left, min(pos.x, obstacle.right))
        closest_y = max(obstacle.top, min(pos.y, obstacle.bottom))
        
        distance = math.sqrt((pos.x - closest_x) ** 2 + (pos.y - closest_y) ** 2)
        return distance < 25
        
    def draw(self, surface: pygame.Surface):
        # Draw shadow
        shadow_offset = Vec2(5, 8)
        shadow_pos = self.pos + shadow_offset
        pygame.draw.ellipse(surface, SHADOW_COLOR, 
                          (shadow_pos.x - 20, shadow_pos.y - 10, 40, 20))
        
        # Draw selection glow if selected
        if self.is_selected:
            glow_radius = 50 + math.sin(self.selection_pulse) * 5
            glow_surface = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
            for i in range(3):
                alpha = 100 - i * 30
                pygame.draw.circle(glow_surface, (*SELECTED_GLOW, alpha), 
                                 (int(glow_radius), int(glow_radius)), int(glow_radius - i * 10))
            surface.blit(glow_surface, (self.pos.x - glow_radius, self.pos.y - glow_radius))
        
        # Draw robotic arm (behind body)
        self.arm.draw(surface, self.pos, self.facing_angle, self.colors)
        
        # Draw legs/wheels
        wheel_offset = 18
        for side in [-1, 1]:
            wheel_x = self.pos.x + math.cos(math.radians(self.facing_angle + 90)) * wheel_offset * side
            wheel_y = self.pos.y + math.sin(math.radians(self.facing_angle + 90)) * wheel_offset * side
            
            # Draw wheel
            pygame.draw.ellipse(surface, (50, 55, 65), 
                              (wheel_x - 8, wheel_y - 15, 16, 30))
            pygame.draw.ellipse(surface, (70, 75, 85), 
                              (wheel_x - 6, wheel_y - 12, 12, 24))
            
            # Wheel treads
            for i in range(3):
                tread_y = wheel_y - 10 + i * 8 + (self.wheel_rotation % 8)
                pygame.draw.line(surface, (40, 45, 55), 
                               (wheel_x - 5, tread_y), (wheel_x + 5, tread_y), 2)
        
        # Draw body (cylinder shape - represented as rounded rect)
        body_rect = pygame.Rect(0, 0, self.body_width, self.body_height)
        body_rect.center = self.pos.to_tuple()
        
        # Body base color
        pygame.draw.rect(surface, self.colors['body'], body_rect, border_radius=8)
        
        # Body details - panels
        panel_rect = pygame.Rect(body_rect.x + 5, body_rect.y + 10, body_rect.width - 10, 15)
        pygame.draw.rect(surface, self.colors['accent'], panel_rect, border_radius=3)
        
        # Body stripe
        stripe_rect = pygame.Rect(body_rect.x + 3, body_rect.y + 30, body_rect.width - 6, 4)
        pygame.draw.rect(surface, (40, 50, 60), stripe_rect)
        
        # Draw dome head
        head_y = self.pos.y - self.body_height // 2 + 5
        
        # Head shadow
        pygame.draw.ellipse(surface, (self.colors['body'][0] - 20, 
                                      self.colors['body'][1] - 20, 
                                      self.colors['body'][2] - 20),
                          (self.pos.x - self.head_radius, head_y - self.head_radius // 2,
                           self.head_radius * 2, self.head_radius))
        
        # Head dome
        pygame.draw.circle(surface, self.colors['accent'], 
                          (int(self.pos.x), int(head_y)), self.head_radius)
        pygame.draw.circle(surface, self.colors['body'], 
                          (int(self.pos.x), int(head_y)), self.head_radius - 3)
        
        # Eye / photoreceptor
        eye_x = self.pos.x + math.cos(math.radians(self.facing_angle)) * 8
        eye_y = head_y + math.sin(math.radians(self.facing_angle)) * 4 - 2
        
        if not self.is_blinking:
            # Outer eye
            pygame.draw.circle(surface, (20, 25, 35), (int(eye_x), int(eye_y)), 7)
            # Inner eye glow
            pygame.draw.circle(surface, self.colors['light'], (int(eye_x), int(eye_y)), 5)
            # Eye highlight
            pygame.draw.circle(surface, (255, 255, 255), (int(eye_x) - 2, int(eye_y) - 2), 2)
        else:
            # Closed eye
            pygame.draw.line(surface, (20, 25, 35), 
                           (eye_x - 5, eye_y), (eye_x + 5, eye_y), 3)
        
        # Antenna
        antenna_x = self.pos.x
        antenna_y = head_y - self.head_radius
        antenna_top_y = antenna_y - 12 + self.antenna_bob
        pygame.draw.line(surface, (100, 110, 120), 
                        (antenna_x, antenna_y), (antenna_x, antenna_top_y), 2)
        pygame.draw.circle(surface, self.colors['light'], (int(antenna_x), int(antenna_top_y)), 4)
        
        # Status indicator based on state
        if self.state == 'working':
            # Busy indicator
            pygame.draw.circle(surface, (255, 200, 50), 
                             (int(self.pos.x + 12), int(head_y - 5)), 3)
        elif self.state == 'interacting':
            # Social indicator
            pygame.draw.circle(surface, (100, 255, 100), 
                             (int(self.pos.x + 12), int(head_y - 5)), 3)
        
        # Bot ID label
        font = pygame.font.Font(None, 20)
        label = font.render(f"R2-D{self.bot_id + 2}", True, self.colors['accent'])
        label_rect = label.get_rect(center=(self.pos.x, self.pos.y + 35))
        surface.blit(label, label_rect)
        
    def contains_point(self, point: Tuple[int, int]) -> bool:
        dist = math.sqrt((point[0] - self.pos.x) ** 2 + (point[1] - self.pos.y) ** 2)
        return dist < 40

class Obstacle:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = OBSTACLE_COLOR
        
    def draw(self, surface: pygame.Surface):
        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        pygame.draw.rect(surface, SHADOW_COLOR, shadow_rect, border_radius=5)
        
        # Main obstacle
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        
        # Highlight
        highlight_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3, 
                                    self.rect.width - 6, 5)
        pygame.draw.rect(surface, (80, 90, 105), highlight_rect, border_radius=2)

class Resource:
    def __init__(self, x: int, y: int):
        self.pos = Vec2(x, y)
        self.pulse = random.uniform(0, math.pi * 2)
        
    def copy(self):
        return Vec2(self.pos.x, self.pos.y)
        
    def draw(self, surface: pygame.Surface):
        self.pulse += 0.05
        size = 12 + math.sin(self.pulse) * 3
        
        # Glow effect
        glow_surface = pygame.Surface((50, 50), pygame.SRCALPHA)
        for i in range(3):
            alpha = 80 - i * 25
            pygame.draw.circle(glow_surface, (*RESOURCE_COLOR, alpha), (25, 25), 20 - i * 5)
        surface.blit(glow_surface, (self.pos.x - 25, self.pos.y - 25))
        
        # Core
        pygame.draw.circle(surface, RESOURCE_COLOR, self.pos.to_tuple(), int(size))
        pygame.draw.circle(surface, (150, 255, 220), self.pos.to_tuple(), int(size - 4))

class Simulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🤖 R2D2 Multi-Agent Simulation - Click to Select, Arrow Keys to Control")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Create bots
        self.bots: List[R2D2] = []
        positions = [
            (200, 200), (400, 300), (600, 500), (900, 200), (800, 600)
        ]
        for i, pos in enumerate(positions):
            self.bots.append(R2D2(pos[0], pos[1], i))
        
        self.selected_bot: Optional[R2D2] = None
        
        # Create obstacles
        self.obstacles: List[Obstacle] = [
            Obstacle(350, 350, 100, 80),
            Obstacle(700, 200, 80, 120),
            Obstacle(150, 500, 120, 60),
            Obstacle(550, 600, 90, 90),
            Obstacle(950, 450, 70, 100),
        ]
        
        # Create resources (work stations)
        self.resources: List[Resource] = [
            Resource(250, 350),
            Resource(500, 150),
            Resource(750, 450),
            Resource(1000, 300),
            Resource(400, 650),
            Resource(850, 700),
        ]
        
        # UI
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Deselect bot
                    if self.selected_bot:
                        self.selected_bot.is_selected = False
                        self.selected_bot = None
                elif event.key == pygame.K_TAB:
                    # Cycle through bots
                    if self.selected_bot:
                        current_idx = self.bots.index(self.selected_bot)
                        self.selected_bot.is_selected = False
                        next_idx = (current_idx + 1) % len(self.bots)
                        self.selected_bot = self.bots[next_idx]
                        self.selected_bot.is_selected = True
                    else:
                        self.selected_bot = self.bots[0]
                        self.selected_bot.is_selected = True
                        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    clicked_bot = None
                    
                    for bot in self.bots:
                        if bot.contains_point(mouse_pos):
                            clicked_bot = bot
                            break
                    
                    # Update selection
                    if self.selected_bot:
                        self.selected_bot.is_selected = False
                        
                    if clicked_bot:
                        self.selected_bot = clicked_bot
                        self.selected_bot.is_selected = True
                    else:
                        self.selected_bot = None
                        
    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        
        for bot in self.bots:
            is_controlled = (bot == self.selected_bot)
            bot.update(dt, is_controlled, keys, 
                      [obs.rect for obs in self.obstacles],
                      self.resources,
                      self.bots)
            
    def draw_floor(self):
        self.screen.fill(BACKGROUND)
        
        # Draw grid pattern
        grid_size = 50
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
            
        # Draw subtle floor gradient
        for y in range(0, SCREEN_HEIGHT, 100):
            alpha = 20 + y // 20
            floor_surface = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
            floor_surface.fill((30, 38, 50, min(alpha, 40)))
            self.screen.blit(floor_surface, (0, y))
            
    def draw_ui(self):
        # Header
        title = self.font.render("🤖 R2D2 AUTONOMOUS SWARM SIMULATION", True, (200, 210, 230))
        self.screen.blit(title, (20, 15))
        
        # Instructions panel
        panel_rect = pygame.Rect(SCREEN_WIDTH - 320, 10, 310, 140)
        pygame.draw.rect(self.screen, (30, 38, 50), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (60, 70, 85), panel_rect, 2, border_radius=10)
        
        instructions = [
            "🖱️ Click robot to select",
            "⬆️⬇️⬅️➡️ Arrow keys: Move selected",
            "WASD: Control robotic arm",
            "SPACE: Close gripper",
            "TAB: Cycle selection | ESC: Deselect"
        ]
        
        for i, text in enumerate(instructions):
            label = self.small_font.render(text, True, (180, 190, 210))
            self.screen.blit(label, (SCREEN_WIDTH - 310, 20 + i * 24))
        
        # Selected bot info
        if self.selected_bot:
            info_panel = pygame.Rect(20, SCREEN_HEIGHT - 80, 280, 65)
            pygame.draw.rect(self.screen, (30, 38, 50), info_panel, border_radius=10)
            pygame.draw.rect(self.screen, self.selected_bot.colors['light'], info_panel, 2, border_radius=10)
            
            bot_name = self.font.render(f"CONTROLLING: R2-D{self.selected_bot.bot_id + 2}", 
                                       True, self.selected_bot.colors['light'])
            self.screen.blit(bot_name, (35, SCREEN_HEIGHT - 70))
            
            state_text = self.small_font.render(f"State: {self.selected_bot.state.upper()}", 
                                               True, (180, 190, 210))
            self.screen.blit(state_text, (35, SCREEN_HEIGHT - 45))
        else:
            # Autonomous mode indicator
            auto_text = self.font.render("🔄 ALL BOTS AUTONOMOUS", True, (100, 200, 150))
            self.screen.blit(auto_text, (20, SCREEN_HEIGHT - 40))
            
        # Bot status panel
        status_x = 20
        status_y = 60
        for bot in self.bots:
            color = bot.colors['light'] if bot.is_selected else bot.colors['body']
            status = "👆 SELECTED" if bot.is_selected else bot.state.upper()
            
            dot_color = bot.colors['light']
            pygame.draw.circle(self.screen, dot_color, (status_x + 8, status_y + 10), 6)
            
            name = self.small_font.render(f"R2-D{bot.bot_id + 2}: {status}", True, color)
            self.screen.blit(name, (status_x + 20, status_y))
            status_y += 25
            
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            
            # Draw everything
            self.draw_floor()
            
            # Draw obstacles
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
                
            # Draw resources
            for resource in self.resources:
                resource.draw(self.screen)
            
            # Draw bots (selected bot last so it's on top)
            for bot in self.bots:
                if bot != self.selected_bot:
                    bot.draw(self.screen)
            if self.selected_bot:
                self.selected_bot.draw(self.screen)
            
            # Draw UI
            self.draw_ui()
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("=" * 50)
    print("R2D2 MULTI-AGENT SIMULATION")
    print("=" * 50)
    print("\nControls:")
    print("  🖱️  Click on a robot to select it")
    print("  ⬆️⬇️⬅️➡️  Arrow keys to move selected robot")
    print("  WASD    Control the robotic arm")
    print("  SPACE   Close the gripper")
    print("  TAB     Cycle through robots")
    print("  ESC     Deselect (all autonomous)")
    print("\nStarting simulation...")
    print("=" * 50)
    
    sim = Simulation()
    sim.run()
