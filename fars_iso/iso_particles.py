"""
iso_particles.py -- Cinematic particle system for FARS isometric simulation.
Supports: starbursts, room pulses, destination rings, trail ribbons, data packets,
footprints, hex pulses, reward bursts, and atmospheric ambient particles.
"""
import pygame, math, random


# ─── Alpha Helpers ─────────────────────────────────────────────────────────────

def draw_alpha_circle(surf, color, center, radius, width=0):
    """Draw a circle with per-pixel alpha."""
    if radius <= 0:
        return
    tmp = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(tmp, color, (radius + 1, radius + 1), radius, width)
    surf.blit(tmp, (center[0] - radius - 1, center[1] - radius - 1))


def draw_glow(surf, color, center, radius, alpha=80):
    """Draw a soft radial glow using layered alpha circles."""
    if radius <= 0:
        return
    for r in range(radius, 0, -3):
        a = int(alpha * (r / radius) ** 1.5)
        c = (*color[:3], min(255, a))
        draw_alpha_circle(surf, c, center, r)


def draw_alpha_line(surf, color, p1, p2, width=1):
    """Draw a line with alpha channel support."""
    if len(color) == 4 and color[3] < 255:
        s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.line(s, color, p1, p2, width)
        surf.blit(s, (0, 0))
    else:
        pygame.draw.line(surf, color[:3], p1, p2, width)


# ─── Particle Base ─────────────────────────────────────────────────────────────

class Particle:
    __slots__ = ('ptype', 'life', 'max_life', 'data')

    def __init__(self, ptype, life, **data):
        self.ptype = ptype
        self.life = life
        self.max_life = life
        self.data = data

    @property
    def alpha(self):
        return max(0.0, self.life / self.max_life)


# ─── Particle System ───────────────────────────────────────────────────────────

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self._ambient = []
        self._ambient_surf = None
        self._anim_time = 0.0
        self._data_packet_timer = 0.0
        self._ambient_nodes = []   # Set by renderer

    def set_ambient_nodes(self, node_positions):
        """Provide world-space corridor endpoints for data packet routing."""
        self._ambient_nodes = node_positions

    # ─── Emitters ──────────────────────────────────────────────────────────────

    def add_starburst(self, sx, sy, color, count=22):
        """Task completion starburst."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(50, 160)
            size  = random.randint(2, 6)
            life  = random.uniform(0.5, 1.0)
            self.particles.append(Particle(
                'burst', life,
                sx=float(sx), sy=float(sy),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                color=color, radius=size,
            ))
        # Also add expanding ring
        self.particles.append(Particle(
            'reward_ring', 1.0,
            sx=float(sx), sy=float(sy),
            color=color,
        ))

    def add_reward_burst(self, sx, sy, color):
        """Large golden burst for high-priority task completion."""
        self.add_starburst(sx, sy, color, count=30)
        # Extra golden particles
        for _ in range(15):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(30, 200)
            self.particles.append(Particle(
                'burst', random.uniform(0.6, 1.2),
                sx=float(sx), sy=float(sy),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                color=(255, 220, 40), radius=random.randint(2, 4),
            ))

    def add_room_pulse(self, pts, color, life=1.5):
        """Flash a room's top face polygon."""
        self.particles.append(Particle(
            'room_pulse', life,
            pts=pts, color=color,
        ))

    def add_destination_ring(self, sx, sy, color):
        """Expanding ring at path destination."""
        self.particles.append(Particle(
            'dest_ring', 1.5,
            sx=float(sx), sy=float(sy),
            color=color, radius=8,
        ))

    def add_footprint(self, sx, sy, color, alpha=80):
        """Fading footstep mark."""
        self.particles.append(Particle(
            'footprint', 1.2,
            sx=float(sx), sy=float(sy),
            color=color, alpha=alpha,
        ))

    def add_hex_pulse(self, sx, sy, color):
        """Expanding hexagon ring at a room center."""
        self.particles.append(Particle(
            'hex_pulse', 1.5,
            sx=float(sx), sy=float(sy),
            color=color,
        ))

    def add_scanline_flash(self, y_pos, surf_w, color):
        """Quick horizontal scan flash."""
        self.particles.append(Particle(
            'scan_flash', 0.3,
            y=float(y_pos), w=float(surf_w), color=color,
        ))

    def add_data_packet(self, sx, sy, ex, ey, color):
        """Small glowing packet traveling along a corridor path."""
        dx = ex - sx
        dy = ey - sy
        dist = math.hypot(dx, dy)
        if dist < 2:
            return
        speed = random.uniform(80, 160)
        self.particles.append(Particle(
            'data_packet', dist / speed,
            sx=float(sx), sy=float(sy),
            ex=float(ex), ey=float(ey),
            dist=dist, speed=speed,
            color=color, progress=0.0,
        ))

    def add_trail_ribbon(self, points, color, max_width=4):
        """Glowing ribbon trail behind a moving agent."""
        if len(points) < 2:
            return
        self.particles.append(Particle(
            'trail_ribbon', 0.8,
            points=list(points),
            color=color,
            max_width=max_width,
        ))

    # ─── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        self._anim_time += dt
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue

            if p.ptype == 'burst':
                p.data['sx'] += p.data['vx'] * dt
                p.data['sy'] += p.data['vy'] * dt
                p.data['vx'] *= 0.88
                p.data['vy'] *= 0.88

            elif p.ptype == 'data_packet':
                p.data['progress'] = min(1.0, p.data['progress'] + p.data['speed'] * dt / p.data['dist'])
                if p.data['progress'] >= 1.0:
                    p.life = 0
                    continue

            alive.append(p)
        self.particles = alive

    # ─── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf):
        for p in self.particles:
            a = max(0.0, min(1.0, p.alpha))
            d = p.data

            if p.ptype == 'burst':
                c = (*d['color'][:3], int(255 * a))
                draw_alpha_circle(surf, c, (int(d['sx']), int(d['sy'])), max(1, d['radius']))

            elif p.ptype == 'reward_ring':
                t = 1.0 - a
                r = int(10 + t * 60)
                c = (*d['color'][:3], int(200 * a))
                draw_alpha_circle(surf, c, (int(d['sx']), int(d['sy'])), r, width=2)
                # Second ring
                r2 = int(5 + t * 35)
                c2 = (255, 220, 40, int(120 * a))
                draw_alpha_circle(surf, c2, (int(d['sx']), int(d['sy'])), r2, width=1)

            elif p.ptype == 'room_pulse':
                pts = d['pts']
                if pts and len(pts) >= 3:
                    s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                    col = (*d['color'][:3], int(160 * a))
                    pygame.draw.polygon(s, col, pts)
                    surf.blit(s, (0, 0))

            elif p.ptype == 'dest_ring':
                t = 1.0 - a
                r = int(d['radius'] + t * 40)
                c = (*d['color'][:3], int(200 * a))
                draw_alpha_circle(surf, c, (int(d['sx']), int(d['sy'])), r, width=2)

            elif p.ptype == 'footprint':
                c = (*d['color'][:3], int(d['alpha'] * a))
                r = max(2, int(4 * a))
                draw_alpha_circle(surf, c, (int(d['sx']), int(d['sy'])), r)

            elif p.ptype == 'hex_pulse':
                t = 1.0 - a
                size = int(15 + t * 50)
                pts = []
                for k in range(6):
                    angle = math.pi / 6 + k * math.pi / 3
                    pts.append((
                        int(d['sx'] + size * math.cos(angle)),
                        int(d['sy'] + size * math.sin(angle))
                    ))
                s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                c = (*d['color'][:3], int(150 * a))
                pygame.draw.polygon(s, c, pts, 2)
                surf.blit(s, (0, 0))

            elif p.ptype == 'scan_flash':
                sy_pos = int(d['y'])
                s = pygame.Surface((int(d['w']), 3), pygame.SRCALPHA)
                c = (*d['color'][:3], int(200 * a))
                s.fill(c)
                surf.blit(s, (0, sy_pos))

            elif p.ptype == 'data_packet':
                prog = d['progress']
                px = d['sx'] + (d['ex'] - d['sx']) * prog
                py = d['sy'] + (d['ey'] - d['sy']) * prog
                c = (*d['color'][:3], int(200 * a))
                # Square sprite for "data packet" feel
                size = 3
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.rect(s, c, s.get_rect(), border_radius=1)
                surf.blit(s, (int(px) - size, int(py) - size))
                # Glow trail behind packet
                trail_c = (*d['color'][:3], int(60 * a))
                trail_x = d['sx'] + (d['ex'] - d['sx']) * max(0, prog - 0.1)
                trail_y = d['sy'] + (d['ey'] - d['sy']) * max(0, prog - 0.1)
                s2 = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                pygame.draw.line(s2, trail_c,
                                 (int(trail_x), int(trail_y)), (int(px), int(py)), 2)
                surf.blit(s2, (0, 0))

            elif p.ptype == 'trail_ribbon':
                pts = d['points']
                if len(pts) >= 2:
                    s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                    for i in range(len(pts) - 1):
                        seg_a = (i / max(1, len(pts) - 1))  # 0 at start, 1 at end
                        width = max(1, int(d['max_width'] * seg_a * a))
                        seg_alpha = int(140 * seg_a * a)
                        c = (*d['color'][:3], seg_alpha)
                        if isinstance(pts[i], (tuple, list)) and isinstance(pts[i+1], (tuple, list)):
                            pygame.draw.line(s, c,
                                             (int(pts[i][0]), int(pts[i][1])),
                                             (int(pts[i+1][0]), int(pts[i+1][1])), width)
                    surf.blit(s, (0, 0))
