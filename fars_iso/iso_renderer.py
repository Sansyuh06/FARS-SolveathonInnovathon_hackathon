"""
iso_renderer.py -- Cinematic Isometric World Renderer for FARS Hospital simulation.
Full 3-face isometric boxes, LED glow strips, detailed robot sprites, hex floor grid,
animated corridor arrows, ribbon trails, Isaac-Sim-style industrial aesthetic.
"""
import pygame
import math
from iso_navigation import get_all_nodes, get_graph
from iso_particles import draw_alpha_circle, draw_glow

# ─── Isometric Projection ─────────────────────────────────────────────────────
TILE_W = 64
TILE_H = 32


def world_to_iso(wx, wz, cam_x, cam_y, zoom, screen_cx, screen_cy):
    """Convert world (x,z) to screen (sx, sy) with camera transform."""
    ix = (wx - wz) * (TILE_W / 2)
    iy = (wx + wz) * (TILE_H / 2)
    sx = (ix - cam_x) * zoom + screen_cx
    sy = (iy - cam_y) * zoom + screen_cy
    return sx, sy


def iso_to_world(sx, sy, cam_x, cam_y, zoom, screen_cx, screen_cy):
    """Convert screen pos to world (wx, wz)."""
    ix = (sx - screen_cx) / zoom + cam_x
    iy = (sy - screen_cy) / zoom + cam_y
    wx = (ix / (TILE_W / 2) + iy / (TILE_H / 2)) / 2
    wz = (iy / (TILE_H / 2) - ix / (TILE_W / 2)) / 2
    return wx, wz


# ─── Zone Styling ─────────────────────────────────────────────────────────────
ZONE_COLORS = {
    'Room':          ((16, 22, 40),   (0, 180, 255)),    # Blue — patient rooms
    'ICU':           ((40, 14, 18),   (255, 30, 55)),    # Red — ICU
    'Pharmacy':      ((14, 34, 20),   (40, 220, 100)),   # Green — pharmacy
    'EmergencyRoom': ((45, 24, 10),   (255, 155, 25)),   # Orange — ER
    'WaitingHall':   ((30, 16, 44),   (155, 70, 255)),   # Purple — waiting
    'StaffOffice':   ((14, 24, 40),   (90, 150, 215)),   # Steel blue — staff
    'ChargingDock':  ((40, 38, 10),   (255, 215, 40)),   # Yellow — charging
    'Reception':     ((20, 24, 32),   (70, 150, 195)),   # Blue-grey — reception
    'MainHall':      ((14, 16, 24),   (50, 130, 190)),   # Deep blue — hall
    'Entrance':      ((18, 22, 30),   (70, 150, 190)),   # Entry
    'HallNorth':     ((14, 16, 24),   (50, 130, 190)),
    '_corridor':     ((10, 12, 18),   (35, 70, 110)),
}

ZONE_SIZES = {
    'Reception':    (6, 5), 'WaitingHall': (7, 5), 'EmergencyRoom': (7, 5),
    'Pharmacy':     (6, 5), 'StaffOffice': (6, 5), 'MainHall':      (9, 7),
    'ChargingDock': (6, 4), 'Entrance':    (6, 3), 'HallNorth':     (5, 4),
}


def get_zone_style(name):
    for prefix, (base, led) in ZONE_COLORS.items():
        if name.startswith(prefix):
            return base, led
    return ZONE_COLORS['_corridor']


def get_zone_size(name):
    for k, v in ZONE_SIZES.items():
        if name == k:
            return v
    if name.startswith('Room'):
        return (5, 4)
    if name.startswith('ICU') and name != 'ICU_Corr':
        return (6, 5)
    return None


def is_corridor_node(name):
    return (name.startswith('RoomCorr') or name.startswith('WestCorr') or
            name.startswith('EastCorr') or name in ('HallNorth', 'ICU_Corr'))


# ─── Color Helpers ────────────────────────────────────────────────────────────
def _darken(c, f=0.6):
    return (max(0, int(c[0] * f)), max(0, int(c[1] * f)), max(0, int(c[2] * f)))


def _lighten(c, f=1.3):
    return (min(255, int(c[0] * f)), min(255, int(c[1] * f)), min(255, int(c[2] * f)))


def _mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _clamp_color(c):
    return tuple(max(0, min(255, int(v))) for v in c[:3])


def _iso_diamond(cx, cy, w, h):
    """Return 4 corners of an isometric diamond (top, right, bottom, left)."""
    hw, hh = w / 2, h / 2
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


# ─── Font Cache ───────────────────────────────────────────────────────────────
_font_cache = {}


def _get_font(size, mono=True):
    key = (size, mono)
    if key not in _font_cache:
        name = 'consolas' if mono else 'segoeui'
        try:
            _font_cache[key] = pygame.font.SysFont(name, size)
        except Exception:
            _font_cache[key] = pygame.font.SysFont(None, size)
    return _font_cache[key]


# ─── Renderer ─────────────────────────────────────────────────────────────────
class IsometricRenderer:
    def __init__(self):
        self.nodes = get_all_nodes()
        self.graph = get_graph()
        self.sim_time = 0.0
        self._bg_surf = None  # Cached background hex grid
        self._bg_size = (0, 0)

    def update(self, dt):
        self.sim_time += dt

    def draw_world(self, surf, cam_x, cam_y, zoom, view_rect):
        """Draw the full isometric world: floor grid, corridors, rooms back-to-front."""
        scx = view_rect[0] + view_rect[2] // 2
        scy = view_rect[1] + view_rect[3] // 2

        def w2s(wx, wz):
            return world_to_iso(wx, wz, cam_x, cam_y, zoom, scx, scy)

        # 1. Draw background hex grid (Isaac Sim floor style)
        self._draw_hex_grid(surf, view_rect, zoom)

        # 2. Draw corridor strips (flat)
        self._draw_corridors(surf, w2s, zoom)

        # 3. Draw rooms sorted back-to-front
        room_list = []
        for name, (wx, wz) in self.nodes.items():
            sz = get_zone_size(name)
            if sz is None:
                continue
            room_list.append((wx + wz, name, wx, wz, sz))
        room_list.sort(key=lambda r: r[0])

        for _, name, wx, wz, (sw, sh) in room_list:
            self._draw_room(surf, w2s, zoom, name, wx, wz, sw, sh)

        # 4. Vignette darkening at edges
        self._draw_vignette(surf, view_rect)

    def _draw_hex_grid(self, surf, view_rect, zoom):
        """Draw very faint hex grid pattern — Isaac Sim floor style."""
        vx, vy, vw, vh = view_rect
        # Only draw if zoom is high enough to see it
        if zoom < 0.5:
            return

        hex_size = max(12, int(20 * zoom))
        col = (18, 22, 32)  # Very dark, barely visible

        # Simple dot grid (performance-friendly alternative to full hexagon grid)
        step_x = int(hex_size * 1.7)
        step_y = int(hex_size * 1.5)

        for row in range(vh // step_y + 2):
            for col_i in range(vw // step_x + 2):
                offset_x = (step_x // 2) if (row % 2) else 0
                px = vx + col_i * step_x + offset_x
                py = vy + row * step_y
                pygame.draw.circle(surf, col, (px, py), 1)

    def _draw_corridors(self, surf, w2s, zoom):
        """Draw flat corridor strips along graph edges with animated center arrows."""
        visited = set()
        for u, v in self.graph.edges():
            eid = tuple(sorted([u, v]))
            if eid in visited:
                continue
            visited.add(eid)

            ux, uz = self.nodes[u]
            vx, vz = self.nodes[v]

            sx1, sy1 = w2s(ux, uz)
            sx2, sy2 = w2s(vx, vz)

            # Corridor width scales with zoom
            cw = max(3, int(7 * zoom))
            edge_w = max(1, int(2 * zoom))

            # Dark corridor base
            pygame.draw.line(surf, (8, 10, 15),
                             (int(sx1), int(sy1)), (int(sx2), int(sy2)), cw + 4)
            pygame.draw.line(surf, (18, 22, 32),
                             (int(sx1), int(sy1)), (int(sx2), int(sy2)), cw)

            # Edge highlight lines
            dx = sy1 - sy2  # perpendicular
            dy = sx2 - sx1
            ln = max(1, math.hypot(dx, dy))
            pdx, pdy = dx / ln * edge_w * 1.5, dy / ln * edge_w * 1.5

            pygame.draw.line(surf, (30, 38, 52),
                             (int(sx1 + pdx), int(sy1 + pdy)),
                             (int(sx2 + pdx), int(sy2 + pdy)), 1)
            pygame.draw.line(surf, (30, 38, 52),
                             (int(sx1 - pdx), int(sy1 - pdy)),
                             (int(sx2 - pdx), int(sy2 - pdy)), 1)

            # Animated dashed yellow center line
            self._draw_dashed(surf, sx1, sy1, sx2, sy2, (160, 140, 30), zoom)

            # Subtle floor glow (ellipse beneath corridor)
            mid_x = int((sx1 + sx2) / 2)
            mid_y = int((sy1 + sy2) / 2)
            length = math.hypot(sx2 - sx1, sy2 - sy1)
            if length > 20 and zoom > 0.6:
                gw = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                pygame.draw.line(gw, (20, 40, 80, 25),
                                 (int(sx1), int(sy1)), (int(sx2), int(sy2)),
                                 max(1, int(cw * 2.5)))
                surf.blit(gw, (0, 0))

    def _draw_dashed(self, surf, x1, y1, x2, y2, color, zoom):
        """Animated dashed line."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < 2:
            return
        nx_, ny = dx / length, dy / length
        dash_len = max(4, int(8 * zoom))
        gap_len  = max(3, int(5 * zoom))
        offset = (self.sim_time * 25) % (dash_len + gap_len)
        pos = -offset
        while pos < length:
            start = max(0, pos)
            end   = min(length, pos + dash_len)
            if end > start:
                sx = int(x1 + nx_ * start)
                sy = int(y1 + ny * start)
                ex = int(x1 + nx_ * end)
                ey = int(y1 + ny * end)
                pygame.draw.line(surf, color, (sx, sy), (ex, ey), max(1, int(zoom)))
            pos += dash_len + gap_len

    def _draw_room(self, surf, w2s, zoom, name, wx, wz, sw, sh):
        """Draw a raised 3-face isometric box with LED glow strip."""
        base_col, led_col = get_zone_style(name)

        # Face shading
        top_col   = _lighten(base_col, 1.5)
        left_col  = _mix(base_col, (0, 0, 0), 0.4)
        right_col = _mix(base_col, (0, 0, 0), 0.6)

        tw = sw * TILE_W * zoom / 2
        th = sh * TILE_H * zoom / 2
        wall_h = max(5, int(18 * zoom))

        cx, cy = w2s(wx, wz)
        cy_top = cy - wall_h

        # Diamond corners
        top_pts = _iso_diamond(cx, cy_top, tw, th)
        bot_pts = _iso_diamond(cx, cy, tw, th)

        # Wall faces
        left_wall  = [top_pts[3], bot_pts[3], bot_pts[2], top_pts[2]]
        right_wall = [top_pts[2], bot_pts[2], bot_pts[1], top_pts[1]]

        def ipts(pts):
            return [(int(x), int(y)) for x, y in pts]

        # Draw walls
        pygame.draw.polygon(surf, left_col,  ipts(left_wall))
        pygame.draw.polygon(surf, right_col, ipts(right_wall))

        # Wall edge lines for crisp iso look
        pygame.draw.lines(surf, _darken(base_col, 0.4), False, ipts(left_wall),  1)
        pygame.draw.lines(surf, _darken(base_col, 0.3), False, ipts(right_wall), 1)

        # Top face
        pygame.draw.polygon(surf, top_col, ipts(top_pts))

        # Top face edge highlight
        pygame.draw.polygon(surf, _lighten(top_col, 1.2), ipts(top_pts), 1)

        # LED accent strip — pulsing glow along top edge
        t_offset = hash(name) * 0.37  # unique phase per room
        pulse = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(self.sim_time * 2.0 + t_offset))
        led_alpha = int(80 + 175 * pulse)

        # Draw glow layers around the top diamond
        for gw in [3, 2, 1]:
            glow_a = led_alpha // (gw + 1)
            glow_s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(glow_s, (*led_col, glow_a), True,
                              ipts(top_pts), max(1, int((gw + 1) * zoom)))
            surf.blit(glow_s, (0, 0))

        # Room label
        self._draw_label(surf, name, cx, cy_top - max(8, int(14 * zoom)), zoom, led_col)

    def _draw_label(self, surf, text, cx, cy, zoom, color):
        """Floating label with dark pill background."""
        fsize = max(8, int(11 * zoom))
        font = _get_font(fsize)
        txt = font.render(text, True, color)
        tw, th = txt.get_size()
        lx = int(cx - tw / 2)
        ly = int(cy - th / 2)

        pad = 3
        bg = pygame.Surface((tw + pad * 2, th + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(bg, (6, 8, 14, 210), bg.get_rect(), border_radius=4)
        pygame.draw.rect(bg, (*color, 60), bg.get_rect(), 1, border_radius=4)
        surf.blit(bg, (lx - pad, ly - pad))
        surf.blit(txt, (lx, ly))

    def _draw_vignette(self, surf, view_rect):
        """Dark vignette at world edges for cinematic depth."""
        vx, vy, vw, vh = view_rect
        grad = pygame.Surface((vw, vh), pygame.SRCALPHA)
        for i, thickness in enumerate([40, 30, 20, 10]):
            alpha = (i + 1) * 18
            # Top
            pygame.draw.rect(grad, (0, 0, 0, alpha), (0, 0, vw, thickness))
            # Bottom
            pygame.draw.rect(grad, (0, 0, 0, alpha), (0, vh - thickness, vw, thickness))
            # Left
            pygame.draw.rect(grad, (0, 0, 0, alpha), (0, 0, thickness, vh))
            # Right
            pygame.draw.rect(grad, (0, 0, 0, alpha), (vw - thickness, 0, thickness, vh))
        surf.blit(grad, (vx, vy))

    # ─── Agent Drawing ────────────────────────────────────────────────────────

    def draw_robot(self, surf, robot, cam_x, cam_y, zoom, view_rect):
        scx = view_rect[0] + view_rect[2] // 2
        scy = view_rect[1] + view_rect[3] // 2
        sx, sy = world_to_iso(robot.world_x, robot.world_z, cam_x, cam_y, zoom, scx, scy)

        # Bobbing animation
        bob = math.sin(robot.anim_time * 4.5) * 2.5 * zoom
        sy += bob

        # Ground shadow — colored ellipse with pulse
        shadow_pulse = 1.0 + 0.08 * math.sin(robot.anim_time * 4)
        sr = int(13 * zoom * shadow_pulse)
        draw_glow(surf, robot.color, (int(sx), int(sy + 10 * zoom)), sr, alpha=35)

        # Spotlight cone on floor
        if robot.state in ('navigating', 'guiding', 'delivering', 'assisting'):
            self._draw_spotlight(surf, robot, sx, sy, zoom)

        # Body dimensions
        bw = int(14 * zoom)
        bh = int(20 * zoom)
        body_top = int(sy - bh)
        body_rect = pygame.Rect(int(sx - bw / 2), body_top, bw, bh)

        # Body glow (outer)
        glow_s = pygame.Surface((bw + 16, bh + 16), pygame.SRCALPHA)
        gc = (*robot.color, 30)
        pygame.draw.rect(glow_s, gc, glow_s.get_rect(), border_radius=4)
        surf.blit(glow_s, (body_rect.x - 8, body_rect.y - 8))

        # Body (gradient-shaded via two rects)
        body_base = _darken(robot.color, 0.45)
        body_top_col = _darken(robot.color, 0.65)
        # Left half darker
        pygame.draw.rect(surf, body_base, body_rect, border_radius=max(1, int(3 * zoom)))
        half_rect = pygame.Rect(body_rect.x, body_rect.y, bw // 2, bh)
        pygame.draw.rect(surf, body_top_col, half_rect,
                         border_radius=max(1, int(3 * zoom)))

        # Neon trim lines on body edges
        trim_c = robot.color
        pygame.draw.rect(surf, trim_c, body_rect, 1, border_radius=max(1, int(3 * zoom)))

        # Chest panel (darker inset)
        panel_rect = pygame.Rect(
            body_rect.x + int(3 * zoom),
            body_rect.y + int(5 * zoom),
            bw - int(6 * zoom),
            int(7 * zoom)
        )
        pygame.draw.rect(surf, (10, 12, 20), panel_rect)

        # Chest panel LED strips — 3 small colored lines
        if int(zoom * 10) > 8:  # Only draw at sufficient zoom
            strip_y = panel_rect.y + 1
            for k, sc in enumerate([(0, 200, 255), (60, 220, 80), robot.color]):
                pulse = 0.5 + 0.5 * math.sin(robot.anim_time * 3 + k * 1.5)
                strip_c = _clamp_color(tuple(int(c * pulse) for c in sc))
                if panel_rect.width > 2 + k * 2:
                    pygame.draw.line(surf, strip_c,
                                     (panel_rect.x + 2, strip_y + k * 2),
                                     (panel_rect.right - 2, strip_y + k * 2), 1)

        # Shoulder pylons (side accents)
        if zoom > 0.6:
            for side in [-1, 1]:
                pylon_x = int(sx + side * (bw / 2 + 2 * zoom))
                pylon_y = body_top + int(4 * zoom)
                pw, ph = max(2, int(3 * zoom)), max(4, int(8 * zoom))
                pygame.draw.rect(surf, _darken(robot.color, 0.7),
                                 (pylon_x - pw // 2, pylon_y, pw, ph),
                                 border_radius=1)
                # Pylon LED
                plen = max(1, int(2 * zoom))
                pulse = 0.5 + 0.5 * math.sin(robot.anim_time * 5 + side)
                pc = _clamp_color(tuple(int(c * pulse) for c in robot.color))
                pygame.draw.rect(surf, pc,
                                 (pylon_x - plen // 2, pylon_y + ph - plen, plen, plen))

        # Dome head
        head_cy = body_top - int(3 * zoom)
        head_rx = int(7 * zoom)
        head_ry = int(5 * zoom)
        head_col = (70, 80, 100)
        pygame.draw.ellipse(surf, head_col,
                            (int(sx - head_rx), head_cy - head_ry,
                             head_rx * 2, head_ry * 2))
        # Head highlight
        pygame.draw.ellipse(surf, (90, 100, 120),
                            (int(sx - head_rx + 1), head_cy - head_ry + 1,
                             head_rx - 2, head_ry - 2), 1)

        # Viewport glass (window on dome)
        if zoom > 0.7:
            vp_w = max(4, int(8 * zoom))
            vp_h = max(3, int(5 * zoom))
            vp_surf = pygame.Surface((vp_w, vp_h), pygame.SRCALPHA)
            vp_col = (*robot.color, 80)
            pygame.draw.rect(vp_surf, vp_col, vp_surf.get_rect(), border_radius=2)
            surf.blit(vp_surf, (int(sx - vp_w / 2), head_cy - vp_h // 2))

        # Eye dot
        eye_r = max(1, int(2.5 * zoom))
        pulse_eye = 0.6 + 0.4 * math.sin(robot.anim_time * 6)
        eye_c = _clamp_color(tuple(int(c * pulse_eye) for c in robot.color))
        pygame.draw.circle(surf, eye_c, (int(sx), head_cy), eye_r)

        # Antenna
        ant_base_y = head_cy - head_ry
        ant_top_y  = ant_base_y - int(8 * zoom)
        pygame.draw.line(surf, (100, 110, 120),
                         (int(sx), ant_base_y), (int(sx), ant_top_y),
                         max(1, int(zoom)))
        # Pulsing antenna light
        ant_pulse = 0.5 + 0.5 * math.sin(robot.anim_time * 8 + robot.id)
        ant_r = max(1, int(2.5 * zoom))
        ant_c = _clamp_color(tuple(min(255, int(c + (255 - c) * ant_pulse)) for c in robot.color))
        pygame.draw.circle(surf, ant_c, (int(sx), ant_top_y), ant_r)
        if ant_pulse > 0.7:
            draw_alpha_circle(surf, (*ant_c, int(60 * ant_pulse)),
                              (int(sx), ant_top_y), ant_r + 2)

        # Treads — animated scrolling texture
        tread_w = int(5 * zoom)
        tread_h = int(4 * zoom)
        for side in [-1, 1]:
            tx_center = int(sx + side * (bw / 2 + tread_w / 2 - 1 * zoom))
            ty_bot = int(sy)
            tread_rect = pygame.Rect(tx_center - tread_w // 2, ty_bot - tread_h, tread_w, tread_h)
            pygame.draw.rect(surf, (18, 22, 30), tread_rect, border_radius=1)
            # Scrolling tread lines
            tread_strip_w = max(1, int(zoom))
            for k in range(3):
                strip_x = tread_rect.x + int((robot.tread_offset + k * 3) % tread_w)
                if tread_rect.x <= strip_x < tread_rect.right:
                    pygame.draw.rect(surf, (35, 40, 50),
                                     (strip_x, tread_rect.y, tread_strip_w, tread_h))

        # HUD above robot
        self._draw_robot_hud(surf, robot, sx, ant_top_y - int(6 * zoom), zoom)

    def _draw_spotlight(self, surf, robot, sx, sy, zoom):
        """Transparent spotlight cone in front of robot."""
        vx, vz = robot.get_velocity()
        v_mag = math.hypot(vx, vz)
        if v_mag < 0.1:
            return

        # Spotlight direction in iso space
        angle = math.atan2(vz - vx, vz + vx)
        length = int(30 * zoom)
        spread = 0.4  # radians

        pts = [(int(sx), int(sy))]
        for s in [-1, 0, 1]:
            a = angle + s * spread
            pts.append((
                int(sx + math.cos(a) * length),
                int(sy + math.sin(a) * length)
            ))

        spot = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        c = (*robot.color, 15)
        if len(pts) >= 3:
            pygame.draw.polygon(spot, c, pts)
        surf.blit(spot, (0, 0))

    def _draw_robot_hud(self, surf, robot, cx, top_y, zoom):
        """Draw ID, battery bar, state badge, and thought bubble above robot."""
        fsize = max(8, int(10 * zoom))
        sfont = _get_font(max(7, int(8 * zoom)))
        font  = _get_font(fsize)

        # ID label
        id_txt = font.render(f'R{robot.id + 1}', True, (255, 255, 255))
        idw, idh = id_txt.get_size()
        surf.blit(id_txt, (int(cx - idw / 2), int(top_y - idh)))
        top_y -= idh + 2

        # Battery bar
        bar_w = max(18, int(30 * zoom))
        bar_h = max(3, int(4 * zoom))
        bx = int(cx - bar_w / 2)
        by = int(top_y - bar_h)
        pygame.draw.rect(surf, (16, 18, 26), (bx, by, bar_w, bar_h))
        fill_w = max(0, int(bar_w * robot.battery / 100))
        bc = (50, 200, 70) if robot.battery > 50 else ((255, 200, 40) if robot.battery > 20 else (255, 50, 50))
        pygame.draw.rect(surf, bc, (bx, by, fill_w, bar_h))
        # Bar border
        pygame.draw.rect(surf, (40, 45, 60), (bx, by, bar_w, bar_h), 1)
        top_y -= bar_h + 3

        # State badge pill
        state_txt = sfont.render(robot.get_state_label(), True, (0, 0, 0))
        stw, sth = state_txt.get_size()
        pad = 3
        badge_w = stw + pad * 2
        badge_h = sth + pad
        badge_rect = pygame.Rect(int(cx - badge_w / 2), int(top_y - badge_h), badge_w, badge_h)
        pygame.draw.rect(surf, robot.get_state_color(), badge_rect, border_radius=4)
        surf.blit(state_txt, (badge_rect.x + pad, badge_rect.y + pad // 2))

        # Glow on badge
        if robot.state in ('navigating', 'guiding', 'delivering', 'assisting'):
            glow_a = pygame.Surface((badge_w + 8, badge_h + 8), pygame.SRCALPHA)
            gc = (*robot.get_state_color(), 40)
            pygame.draw.rect(glow_a, gc, glow_a.get_rect(), border_radius=6)
            surf.blit(glow_a, (badge_rect.x - 4, badge_rect.y - 4))

        top_y -= badge_h + 3

        # Thinking indicator (bouncing dots) when navigating
        if robot.state == 'navigating' and zoom > 0.7:
            for k in range(3):
                dot_y = int(top_y - 4 - abs(math.sin(robot.anim_time * 5 + k * 0.8)) * 4)
                dot_x = int(cx + (k - 1) * 5)
                pygame.draw.circle(surf, robot.color, (dot_x, dot_y), max(1, int(1.5 * zoom)))
            top_y -= 12

        # Thought bubble (last 2 thoughts)
        if robot.thoughts and zoom > 0.5:
            lines = robot.thoughts[-2:]
            rendered = []
            max_tw = 0
            for line in lines:
                t = sfont.render(line[:32], True, (150, 160, 175))
                rendered.append(t)
                max_tw = max(max_tw, t.get_width())

            bub_h = len(rendered) * (sth + 2) + 8
            bub_w = max_tw + 10
            bub_x = int(cx - bub_w / 2)
            bub_y = int(top_y - bub_h)

            bs = pygame.Surface((bub_w, bub_h), pygame.SRCALPHA)
            pygame.draw.rect(bs, (10, 12, 20, 215), bs.get_rect(), border_radius=5)
            pygame.draw.rect(bs, (*robot.color, 90), bs.get_rect(), 1, border_radius=5)
            surf.blit(bs, (bub_x, bub_y))

            ty = bub_y + 4
            for t in rendered:
                surf.blit(t, (bub_x + 5, ty))
                ty += sth + 2

        # Reward signal indicator
        if robot.reward_signal > 0.05 and zoom > 0.6:
            rew_bar_w = max(18, int(30 * zoom))
            rew_bar_h = max(2, int(3 * zoom))
            rx = int(cx - rew_bar_w / 2)
            ry = top_y - bub_h - rew_bar_h - 4 if robot.thoughts else top_y - rew_bar_h - 4
            pygame.draw.rect(surf, (16, 18, 26), (rx, ry, rew_bar_w, rew_bar_h))
            fill = int(rew_bar_w * robot.reward_signal)
            pulse = 0.7 + 0.3 * math.sin(robot.anim_time * 15)
            rc = (int(255 * pulse), int(200 * pulse), int(40 * pulse))
            pygame.draw.rect(surf, rc, (rx, ry, fill, rew_bar_h))

    def draw_path_trail(self, surf, robot, cam_x, cam_y, zoom, view_rect):
        """Draw animated dashed path trail from robot to destination."""
        coords = robot.get_path_world_coords()
        if len(coords) < 2:
            return

        scx = view_rect[0] + view_rect[2] // 2
        scy = view_rect[1] + view_rect[3] // 2

        screen_pts = []
        for wx, wz in coords:
            sx, sy = world_to_iso(wx, wz, cam_x, cam_y, zoom, scx, scy)
            screen_pts.append((int(sx), int(sy)))

        # Glow trail lines
        trail_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for i in range(len(screen_pts) - 1):
            seg_a = (i + 1) / len(screen_pts)
            gw = max(1, int(3 * zoom * seg_a))
            gc = (*robot.color, int(60 * seg_a))
            pygame.draw.line(trail_surf, gc, screen_pts[i], screen_pts[i + 1], gw)
        surf.blit(trail_surf, (0, 0))

        # Animated dashes on top
        dash_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        color = (*robot.color[:3], 180)
        for i in range(len(screen_pts) - 1):
            self._draw_dashed_alpha(dash_surf, screen_pts[i], screen_pts[i + 1], color, zoom)
        surf.blit(dash_surf, (0, 0))

        # Destination pulsing ring
        if len(screen_pts) >= 2:
            dx, dy = screen_pts[-1]
            t = (self.sim_time * 0.7) % 1.0
            r = int(8 + t * 28 * zoom)
            a = int(200 * (1 - t))
            draw_alpha_circle(surf, (*robot.color, a), (dx, dy), r, width=2)
            # Inner solid dot
            pygame.draw.circle(surf, robot.color, (dx, dy), max(2, int(3 * zoom)))

    def _draw_dashed_alpha(self, surf, p1, p2, color, zoom):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length < 2:
            return
        nx_, ny = dx / length, dy / length
        dash = max(5, int(10 * zoom))
        gap  = max(4, int(6 * zoom))
        offset = (self.sim_time * 40) % (dash + gap)
        pos = -offset
        while pos < length:
            start = max(0, pos)
            end   = min(length, pos + dash)
            if end > start:
                sx = int(p1[0] + nx_ * start)
                sy = int(p1[1] + ny * start)
                ex = int(p1[0] + nx_ * end)
                ey = int(p1[1] + ny * end)
                pygame.draw.line(surf, color, (sx, sy), (ex, ey),
                                 max(1, int(2.5 * zoom)))
            pos += dash + gap

    def draw_human(self, surf, human, cam_x, cam_y, zoom, view_rect):
        scx = view_rect[0] + view_rect[2] // 2
        scy = view_rect[1] + view_rect[3] // 2
        sx, sy = world_to_iso(human.world_x, human.world_z, cam_x, cam_y, zoom, scx, scy)

        # Walking bob
        is_moving = bool(human.path_nodes and human.path_index < len(human.path_nodes))
        bob = math.sin(human.anim_time * 6) * 2 * zoom if is_moving else 0
        sy += bob

        r = max(4, int(6 * zoom))

        # Role-specific body shape
        atype = human.agent_type

        if atype == 'doctor':
            # White coat: tall rectangle + head
            bw = int(r * 1.4)
            bh = int(r * 2.2)
            # Coat body
            pygame.draw.rect(surf, _darken(human.color, 0.4),
                             (int(sx - bw / 2), int(sy - bh), bw, bh),
                             border_radius=2)
            pygame.draw.rect(surf, human.color,
                             (int(sx - bw / 2 + 1), int(sy - bh + 1), bw - 2, bh - 1),
                             border_radius=2)
            # Stethoscope accent
            pygame.draw.line(surf, (150, 160, 180),
                             (int(sx - bw / 3), int(sy - bh // 2)),
                             (int(sx + bw / 3), int(sy - bh // 2)), 1)
        elif atype == 'nurse':
            # Pink uniform
            bw = int(r * 1.3)
            bh = int(r * 2.0)
            pygame.draw.rect(surf, _darken(human.color, 0.5),
                             (int(sx - bw / 2), int(sy - bh), bw, bh), border_radius=2)
            pygame.draw.rect(surf, human.color,
                             (int(sx - bw / 2 + 1), int(sy - bh + 1), bw - 2, bh - 1),
                             border_radius=2)
            # Nurse cross
            cross_c = (255, 60, 60)
            cross_x = int(sx)
            cross_y = int(sy - bh // 2)
            pygame.draw.line(surf, cross_c, (cross_x - 2, cross_y), (cross_x + 2, cross_y), 1)
            pygame.draw.line(surf, cross_c, (cross_x, cross_y - 2), (cross_x, cross_y + 2), 1)
        elif atype == 'patient':
            # Hospital gown (blue tint circle)
            pygame.draw.circle(surf, _darken(human.color, 0.5), (int(sx), int(sy)), r + 1)
            pygame.draw.circle(surf, human.color, (int(sx), int(sy)), r)
        else:
            # Visitor — simple circle
            pygame.draw.circle(surf, _darken(human.color, 0.5), (int(sx), int(sy)), r + 1)
            pygame.draw.circle(surf, human.color, (int(sx), int(sy)), r)

        # Head dot (all types)
        head_y = int(sy - r * 2 - 3 * zoom)
        head_r = max(2, int(r * 0.6))
        pygame.draw.circle(surf, (200, 185, 165), (int(sx), head_y), head_r)

        # Role indicator dot above head
        pygame.draw.circle(surf, human.color, (int(sx), head_y - head_r - 2), max(1, int(2 * zoom)))

        # Walking arm swing
        if is_moving and zoom > 0.7:
            arm_swing = math.sin(human.anim_time * 6) * (r * 0.8)
            arm_color = _darken(human.color, 0.7)
            arm_r = max(1, int(r * 0.35))
            arm_y = int(sy - r * 0.5)
            pygame.draw.circle(surf, arm_color, (int(sx - r + arm_swing * 0.5), arm_y), arm_r)
            pygame.draw.circle(surf, arm_color, (int(sx + r - arm_swing * 0.5), arm_y), arm_r)

        # Help indicator — pulsing ring
        if human.needs_help:
            pulse = 0.5 + 0.5 * math.sin(human.anim_time * 6)
            hr = int((r + 5) * (1 + 0.15 * pulse))
            draw_alpha_circle(surf, (255, 50, 50, int(130 * pulse)),
                              (int(sx), int(sy)), hr, width=2)
            # ! exclamation
            if zoom > 0.5:
                f = _get_font(max(8, int(10 * zoom)), mono=False)
                t = f.render('!', True, (255, 80, 80))
                surf.blit(t, (int(sx - t.get_width() / 2),
                              int(sy - r - 14 * zoom)))

    # ─── Mini-Map ─────────────────────────────────────────────────────────────

    def draw_minimap(self, surf, rect, robots, humans):
        """Draw top-down mini-map with zone colors, robot trails, task markers."""
        mx, my, mw, mh = rect

        # Background
        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 12, 20, 240), bg.get_rect(), border_radius=6)
        surf.blit(bg, (mx, my))

        # Compute world bounds
        xs = [p[0] for p in self.nodes.values()]
        zs = [p[1] for p in self.nodes.values()]
        min_x = min(xs) - 5
        max_x = max(xs) + 5
        min_z = min(zs) - 5
        max_z = max(zs) + 5

        def map_pos(wx, wz):
            nx_ = (wx - min_x) / (max_x - min_x)
            nz  = (wz - min_z) / (max_z - min_z)
            return int(mx + 8 + nx_ * (mw - 16)), int(my + 8 + nz * (mh - 16))

        # Zone-colored node backgrounds (tiny filled circles for rooms)
        for name, (wx, wz) in self.nodes.items():
            sz = get_zone_size(name)
            if sz:
                _, led = get_zone_style(name)
                px, py = map_pos(wx, wz)
                r = max(3, min(7, int(sz[0] * 0.8)))
                dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(dot, (*led, 40), (r, r), r)
                surf.blit(dot, (px - r, py - r))

        # Edges
        for u, v in self.graph.edges():
            p1 = map_pos(*self.nodes[u])
            p2 = map_pos(*self.nodes[v])
            pygame.draw.line(surf, (30, 38, 55), p1, p2, 1)

        # Nodes
        for name, (wx, wz) in self.nodes.items():
            _, led = get_zone_style(name)
            px, py = map_pos(wx, wz)
            pygame.draw.circle(surf, led, (px, py), 2)

        # Robot trails on mini-map
        for r in robots:
            if len(r.trail_positions) > 1:
                for i in range(len(r.trail_positions) - 1):
                    a_frac = i / len(r.trail_positions)
                    p1 = map_pos(*r.trail_positions[i])
                    p2 = map_pos(*r.trail_positions[i + 1])
                    c = (*r.color, int(80 * a_frac))
                    s = pygame.Surface((mw + mx * 2, mh + my * 2), pygame.SRCALPHA)
                    pygame.draw.line(s, c, p1, p2, 1)
                    surf.blit(s, (0, 0))

        # Robots
        for r in robots:
            px, py = map_pos(r.world_x, r.world_z)
            pygame.draw.circle(surf, r.color, (px, py), 4)
            pygame.draw.circle(surf, (255, 255, 255), (px, py), 4, 1)

        # Humans
        for h in humans:
            px, py = map_pos(h.world_x, h.world_z)
            pygame.draw.circle(surf, h.color, (px, py), 2)

        # Mini-map border
        pygame.draw.rect(surf, (35, 45, 65), (mx, my, mw, mh), 1, border_radius=6)

        # Title
        try:
            f = _get_font(8)
        except Exception:
            f = pygame.font.SysFont(None, 8)
        lbl = f.render('HOSPITAL MAP', True, (60, 70, 90))
        surf.blit(lbl, (mx + 4, my + 2))
