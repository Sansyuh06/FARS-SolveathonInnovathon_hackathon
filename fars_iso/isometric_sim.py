"""
isometric_sim.py -- FARS Hospital Digital Twin: Cinematic Isometric AI Simulation
Main entry point. Featuring: Isaac-Sim-style dark industrial world, glowing rooms,
RL-style neural network visualizer, animated robot agents, Hollywood particle FX.

Run: python isometric_sim.py
"""
import sys
import os
import math
import random
import time as _time
import threading

# ─── Dependency Checks ────────────────────────────────────────────────────────
try:
    import pygame
except ImportError:
    print("ERROR: pygame not installed. Run: pip install pygame numpy networkx requests")
    sys.exit(1)

try:
    import networkx
except ImportError:
    print("ERROR: networkx not installed. Run: pip install networkx")
    sys.exit(1)

from iso_navigation import get_all_nodes, get_graph, get_node_position, get_nearest_node, get_all_room_nodes
from iso_agents import RobotAgent, HumanAgent
from iso_tasks import TaskManager
from iso_renderer import IsometricRenderer, world_to_iso, iso_to_world
from iso_dashboard import Dashboard, PANEL_W
from iso_particles import ParticleSystem
import iso_llm

# ─── Window Settings ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1600, 900
BG_COLOR = (6, 8, 14)
TARGET_FPS = 60

# ─── Camera ───────────────────────────────────────────────────────────────────
class Camera:
    LERP = 0.12

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 0.85
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_zoom = 0.85
        self._dragging = False
        self._drag_start = (0, 0)
        self._drag_cam_start = (0.0, 0.0)

    def update(self, dt):
        lr = min(1.0, self.LERP * 60 * dt)
        self.x    += (self.target_x    - self.x)    * lr
        self.y    += (self.target_y    - self.y)    * lr
        self.zoom += (self.target_zoom - self.zoom) * lr

    def pan_to_world(self, wx, wz):
        """Smoothly pan camera to center on world position."""
        from iso_renderer import TILE_W, TILE_H
        ix = (wx - wz) * (TILE_W / 2)
        iy = (wx + wz) * (TILE_H / 2)
        self.target_x = ix
        self.target_y = iy

    def handle_event(self, event, view_rect):
        if event.type == pygame.MOUSEWHEEL:
            factor = 1.1 if event.y > 0 else 0.9
            self.target_zoom = max(0.35, min(2.5, self.target_zoom * factor))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (2, 3):  # Middle or right drag
                self._dragging = True
                self._drag_start = event.pos
                self._drag_cam_start = (self.target_x, self.target_y)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (2, 3):
                self._dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self._dragging:
                dx = event.pos[0] - self._drag_start[0]
                dy = event.pos[1] - self._drag_start[1]
                self.target_x = self._drag_cam_start[0] - dx / self.zoom
                self.target_y = self._drag_cam_start[1] - dy / self.zoom

    def handle_keys(self, dt):
        keys = pygame.key.get_pressed()
        speed = 350.0 / self.zoom
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.target_y -= speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.target_y += speed * dt
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.target_x -= speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.target_x += speed * dt

    def reset_overview(self):
        self.target_x = 50
        self.target_y = 120
        self.target_zoom = 0.85


# ─── Boot Sequence ────────────────────────────────────────────────────────────
def boot_sequence(screen, clock):
    """Cinematic boot animation with matrix rain effect."""
    font_big  = pygame.font.SysFont('consolas', 28, bold=True)
    font_med  = pygame.font.SysFont('consolas', 14)
    font_sm   = pygame.font.SysFont('consolas', 12)

    lines = [
        ('FARS DIGITAL TWIN  v2.0', (0, 200, 255), True),
        ('', (0, 0, 0), False),
        ('NAVIGATION SYSTEM ............. OK', (50, 215, 90), False),
        ('ROBOT FLEET (5 units) ......... ONLINE', (50, 215, 90), False),
        ('TASK MANAGER .................. READY', (50, 215, 90), False),
        (f'LLM INTERFACE ................. {iso_llm.get_model_name()}',
         (50, 215, 90) if iso_llm.get_model_name() != 'FALLBACK' else (255, 200, 40), False),
        ('PARTICLE SYSTEM ............... ACTIVE', (50, 215, 90), False),
        ('NEURAL NET VISUALIZER ......... LOADED', (50, 215, 90), False),
        ('', (0, 0, 0), False),
        ('Initializing simulation...', (70, 80, 100), False),
    ]

    sw, sh = screen.get_size()

    # Matrix rain chars
    chars = [chr(random.randint(0x30A0, 0x30FF)) for _ in range(60)]  # Katakana
    rain_cols = [(random.randint(0, sw // 12), random.randint(-sh, 0), random.uniform(3, 8))
                 for _ in range(40)]

    rain_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

    start  = _time.time()
    shown  = 0
    fading = False
    fade_alpha = 0

    while _time.time() - start < 3.0:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                return  # Skip boot

        elapsed = _time.time() - start
        shown   = min(len(lines), int(elapsed * 4) + 1)

        # Fade in
        if elapsed < 0.3:
            fade_alpha = int(255 * elapsed / 0.3)
        elif elapsed > 2.5:
            fade_alpha = int(255 * (1 - (elapsed - 2.5) / 0.5))
        else:
            fade_alpha = 255

        screen.fill((2, 4, 8))

        # Matrix rain (background)
        rain_surf.fill((0, 0, 0, 0))
        for i, (cx, cy, speed) in enumerate(rain_cols):
            cy = int((cy + speed) % (sh + 40) - 40)
            rain_cols[i] = (cx, cy, speed)
            ch = chars[i % len(chars)]
            t = font_sm.render(ch, True, (0, 60, 20))
            rain_surf.blit(t, (cx * 12, int(cy)))
        screen.blit(rain_surf, (0, 0))

        # Boot text
        y0 = sh // 2 - shown * 14
        for i in range(shown):
            text, color, is_big = lines[i]
            if not text:
                continue
            f = font_big if is_big else font_med
            t = f.render(text, True, color)

            # Glow for title
            if is_big:
                gs = pygame.Surface((t.get_width() + 40, t.get_height() + 20), pygame.SRCALPHA)
                pygame.draw.rect(gs, (0, 100, 200, 40), gs.get_rect(), border_radius=6)
                screen.blit(gs, (sw // 2 - t.get_width() // 2 - 20, y0 + i * 26 - 10))

            screen.blit(t, (sw // 2 - t.get_width() // 2, y0 + i * 26))

        # Fade overlay
        if fade_alpha < 255:
            fade = pygame.Surface((sw, sh))
            fade.fill((2, 4, 8))
            fade.set_alpha(255 - fade_alpha)
            screen.blit(fade, (0, 0))

        pygame.display.flip()
        clock.tick(30)


# ─── Data Packet Emitter ──────────────────────────────────────────────────────
_packet_timer = 0.0

def _maybe_emit_packets(particles, renderer, robots, camera, view_rect, dt):
    """Periodically emit data packet particles along corridors near active robots."""
    global _packet_timer
    _packet_timer += dt
    if _packet_timer < 0.4:
        return
    _packet_timer = 0.0

    scx = view_rect[0] + view_rect[2] // 2
    scy = view_rect[1] + view_rect[3] // 2

    graph = get_graph()
    for r in robots:
        if r.state not in ('navigating', 'returning'):
            continue
        # Emit a packet along one random edge near the robot's current node
        neighbors = list(graph.neighbors(r.current_node))
        if not neighbors:
            continue
        dst = random.choice(neighbors)
        sx, sz = get_node_position(r.current_node)
        ex, ez = get_node_position(dst)
        ssx, ssy = world_to_iso(sx, sz, camera.x, camera.y, camera.zoom, scx, scy)
        eex, eey = world_to_iso(ex, ez, camera.x, camera.y, camera.zoom, scx, scy)
        particles.add_data_packet(ssx, ssy, eex, eey, r.color)


# ─── Main Simulation ─────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption('FARS Digital Twin — Cinematic Isometric AI Simulation')
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    clock  = pygame.time.Clock()

    # Boot sequence
    boot_sequence(screen, clock)

    # ── Initialize systems ──
    renderer   = IsometricRenderer()
    dashboard  = Dashboard()
    particles  = ParticleSystem()
    camera     = Camera()
    camera.reset_overview()
    task_mgr   = TaskManager()

    # ── Spawn agents ──
    robots = [RobotAgent(i) for i in range(5)]
    rooms  = get_all_room_nodes()
    humans = []
    for i in range(15):
        humans.append(HumanAgent('patient', rooms[i % len(rooms)]))
    for _ in range(6):
        humans.append(HumanAgent('doctor'))
    for _ in range(6):
        humans.append(HumanAgent('nurse'))
    for _ in range(6):
        humans.append(HumanAgent('visitor'))

    sim_speed    = 1.0    # Multiplier
    paused       = False
    running      = True
    show_tooltip = False
    tooltip_text = ''
    tooltip_pos  = (0, 0)

    print(f"\n✓ FARS Digital Twin running — {len(robots)} robots, {len(humans)} humans")
    print(f"  AI Model: {iso_llm.get_model_name()}")
    print(f"  Controls: WASD=Pan  Scroll=Zoom  1-5=Focus Robot  P=Pause  R=Reset  Home=Overview  F11=Fullscreen\n")

    while running:
        raw_dt = clock.tick(TARGET_FPS) / 1000.0
        dt = min(raw_dt * sim_speed, 0.1)
        fps = int(clock.get_fps())

        sw, sh = screen.get_size()
        view_rect = (PANEL_W, 48, sw - PANEL_W, sh - 48 - 48)

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    dashboard.selected_robot = -1
                    dashboard.command_focused = False
                    dashboard.command_text = ''

                elif event.key == pygame.K_p:
                    paused = not paused
                    task_mgr.add_alert('PAUSED' if paused else 'RESUMED')

                elif event.key == pygame.K_HOME:
                    camera.reset_overview()

                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

                elif event.key == pygame.K_r:
                    # Full reset
                    robots = [RobotAgent(i) for i in range(5)]
                    humans = []
                    for i in range(15):
                        humans.append(HumanAgent('patient', rooms[i % len(rooms)]))
                    for _ in range(6):
                        humans.append(HumanAgent('doctor'))
                    for _ in range(6):
                        humans.append(HumanAgent('nurse'))
                    for _ in range(6):
                        humans.append(HumanAgent('visitor'))
                    task_mgr.__init__()
                    particles.particles.clear()
                    task_mgr.add_alert('Simulation reset.')

                elif event.key == pygame.K_LEFTBRACKET:
                    sim_speed = max(0.25, sim_speed * 0.5)
                    task_mgr.add_alert(f'Speed: {sim_speed:.2f}x')

                elif event.key == pygame.K_RIGHTBRACKET:
                    sim_speed = min(4.0, sim_speed * 2.0)
                    task_mgr.add_alert(f'Speed: {sim_speed:.2f}x')

                # Number keys 1-5: focus camera on robot
                if not dashboard.command_focused:
                    for i in range(min(5, len(robots))):
                        if event.key == pygame.K_1 + i:
                            camera.pan_to_world(robots[i].world_x, robots[i].world_z)
                            camera.target_zoom = max(camera.target_zoom, 1.3)
                            dashboard.selected_robot = i

            # Dashboard events
            result = dashboard.handle_event(event, robots)
            if result == 'consumed':
                continue
            elif result and isinstance(result, tuple):
                if result[0] == 'focus_robot':
                    idx = result[1]
                    if idx < len(robots):
                        camera.pan_to_world(robots[idx].world_x, robots[idx].world_z)
                        camera.target_zoom = max(camera.target_zoom, 1.3)
                elif result[0] == 'command':
                    cmd = result[1]
                    iso_llm.submit_command(cmd)
                    dashboard.last_result = f'Processing: {cmd[:35]}...'
                    task_mgr.add_alert(f'CMD: {cmd[:40]}')
                continue

            # Camera events (only if not in command mode)
            if not dashboard.command_focused:
                camera.handle_event(event, view_rect)

            # Right-click world: create security_check task + hex pulse particle
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mx, my = event.pos
                vx, vy, vw, vh = view_rect
                if vx < mx < vx + vw and vy < my < vy + vh:
                    scx = view_rect[0] + view_rect[2] // 2
                    scy = view_rect[1] + view_rect[3] // 2
                    wx, wz = iso_to_world(mx, my, camera.x, camera.y, camera.zoom, scx, scy)
                    node = get_nearest_node(wx, wz)
                    if node:
                        task_mgr.create_task('security_check', node, 2, f'Manual check at {node}')
                        # Hex pulse at location
                        nx, nz = get_node_position(node)
                        nsx, nsy = world_to_iso(nx, nz, camera.x, camera.y, camera.zoom, scx, scy)
                        particles.add_hex_pulse(nsx, nsy, (0, 180, 255))

            # Left-click world: select closest robot or deselect
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                vx, vy, vw, vh = view_rect
                if vx < mx < vx + vw and vy < my < vy + vh:
                    scx = view_rect[0] + view_rect[2] // 2
                    scy = view_rect[1] + view_rect[3] // 2
                    best_r = -1
                    best_d = 35
                    for i, r in enumerate(robots):
                        rsx, rsy = world_to_iso(r.world_x, r.world_z,
                                                camera.x, camera.y, camera.zoom, scx, scy)
                        d = math.hypot(mx - rsx, my - rsy)
                        if d < best_d:
                            best_d = d
                            best_r = i

                    if best_r >= 0:
                        dashboard.selected_robot = best_r
                        camera.pan_to_world(robots[best_r].world_x, robots[best_r].world_z)
                    else:
                        dashboard.selected_robot = -1

        # Camera keys (continuous)
        if not dashboard.command_focused:
            camera.handle_keys(raw_dt)  # Use raw_dt for camera (not sim speed)

        # ── Update ────────────────────────────────────────────────────────────
        camera.update(raw_dt)
        renderer.update(dt)
        dashboard.update(raw_dt)
        particles.update(dt)

        if not paused:
            # Update robots
            for r in robots:
                try:
                    r.update(dt)
                except Exception as e:
                    task_mgr.add_alert(f'[ERROR] R{r.id + 1}: {e}')

            # Update humans
            for h in humans:
                try:
                    h.update(dt)
                except Exception:
                    pass

            # Task scheduling
            task_mgr.auto_generate_from_humans(humans, dt)
            task_mgr.assign_tasks(robots)

            # Check completed tasks
            scx = view_rect[0] + view_rect[2] // 2
            scy = view_rect[1] + view_rect[3] // 2
            completed = task_mgr.check_completed(robots)
            for t in completed:
                # Resolve patient help
                for h in humans:
                    if h.current_node == t.location_node and h.needs_help:
                        h.fulfill_help()
                        break

                # Starburst + room pulse at task location
                tx, tz = get_node_position(t.location_node)
                tsx, tsy = world_to_iso(tx, tz, camera.x, camera.y, camera.zoom, scx, scy)
                r_agent = next((r for r in robots if r.id == t.assigned_robot), None)
                col = r_agent.color if r_agent else (255, 220, 40)

                if t.priority >= 3:
                    particles.add_reward_burst(tsx, tsy, col)
                else:
                    particles.add_starburst(tsx, tsy, col)

                task_mgr.add_alert(f'[DONE] {t.task_type} @ {t.location_node}')
                particles.add_scan_line_or_hex(tsx, tsy, col)

            # Emit data packets
            _maybe_emit_packets(particles, renderer, robots, camera, view_rect, dt)

            # Poll LLM results
            for result in iso_llm.poll_results():
                src = result.get('_src', 'fallback')
                task_mgr.create_task(
                    result.get('task_type', 'security_check'),
                    result.get('location_node', 'MainHall'),
                    result.get('priority', 2),
                    result.get('description', ''),
                )
                loc = result.get('location_node', '?')
                dashboard.last_result = f'[{src.upper()}] -> {loc}'
                task_mgr.add_alert(f'[AI:{src}] {result.get("task_type")} -> {loc}')

                # Camera pan to task location
                tx, tz = get_node_position(loc)
                camera.pan_to_world(tx, tz)

                # Hex pulse at target
                tsx, tsy = world_to_iso(tx, tz, camera.x, camera.y, camera.zoom, scx, scy)
                particles.add_hex_pulse(tsx, tsy, (0, 200, 255))

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)

        # Clip to world view area
        clip = pygame.Rect(view_rect)
        screen.set_clip(clip)

        scx = view_rect[0] + view_rect[2] // 2
        scy = view_rect[1] + view_rect[3] // 2

        # 1. World (corridors → rooms)
        renderer.draw_world(screen, camera.x, camera.y, camera.zoom, view_rect)

        # 2. Path trails (behind agents)
        for r in robots:
            renderer.draw_path_trail(screen, r, camera.x, camera.y, camera.zoom, view_rect)

        # 3. All agents sorted back-to-front (painter's algorithm)
        all_agents = [(h.world_x + h.world_z, 'human', h) for h in humans]
        all_agents += [(r.world_x + r.world_z, 'robot', r) for r in robots]
        all_agents.sort(key=lambda a: a[0])

        for _, atype, agent in all_agents:
            if atype == 'human':
                renderer.draw_human(screen, agent, camera.x, camera.y, camera.zoom, view_rect)
            else:
                renderer.draw_robot(screen, agent, camera.x, camera.y, camera.zoom, view_rect)

        # 4. Particles (on top of world)
        particles.draw(screen)

        screen.set_clip(None)

        # 5. Dashboard (always on top)
        dashboard.draw(screen, sw, sh, robots, task_mgr, fps)

        # 6. Mini-map
        minimap_h = 140
        minimap_rect = (10, sh - 48 - minimap_h - 4, PANEL_W - 20, minimap_h)
        renderer.draw_minimap(screen, minimap_rect, robots, humans)

        # 7. Paused overlay
        if paused:
            f = pygame.font.SysFont('consolas', 32, bold=True)
            t = f.render('⏸  PAUSED', True, (255, 200, 40))
            ts = pygame.Surface((t.get_width() + 30, t.get_height() + 14), pygame.SRCALPHA)
            pygame.draw.rect(ts, (0, 0, 0, 180), ts.get_rect(), border_radius=8)
            screen.blit(ts, (sw // 2 - ts.get_width() // 2, 60))
            screen.blit(t, (sw // 2 - t.get_width() // 2, 67))

        # 8. Speed indicator
        if sim_speed != 1.0:
            f = pygame.font.SysFont('consolas', 12)
            spd_txt = f.render(f'SPEED: {sim_speed:.2f}x', True, (255, 200, 40))
            screen.blit(spd_txt, (PANEL_W + 12, 54))

        pygame.display.flip()

    pygame.quit()


# ─── ParticleSystem helper patch ──────────────────────────────────────────────
# Monkey-patch add_scan_line_or_hex onto ParticleSystem for cleaner call
def _add_scan_or_hex(self, sx, sy, color):
    """Add hex pulse on task completion."""
    self.add_hex_pulse(sx, sy, color)

ParticleSystem.add_scan_line_or_hex = _add_scan_or_hex


if __name__ == '__main__':
    main()
