"""
iso_dashboard.py -- Full cinematic HUD for FARS isometric simulation.
Left panel, top bar, bottom command bar, neural network visualizer.
Dark sci-fi operations center aesthetic.
"""
import pygame
import math
import time as _time

from iso_neural import NeuralNetViz

# ─── Color Palette ────────────────────────────────────────────────────────────
C_BG     = (8,  10, 16)
C_PANEL  = (12, 14, 20)
C_BORDER = (30, 40, 55)
C_CYAN   = (0,  180, 255)
C_GREEN  = (50, 210, 90)
C_YELLOW = (255, 200, 40)
C_ORANGE = (255, 155, 35)
C_RED    = (255, 50,  65)
C_PURPLE = (155, 70,  255)
C_DIM    = (85,  95, 115)
C_WHITE  = (225, 230, 242)
C_DARK   = (16,  18,  26)

PANEL_W = 300

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


def _lerp(a, b, t):
    return a + (b - a) * t


def _draw_pill(surf, text, x, y, fg, bg, font, border=None):
    t = font.render(text, True, fg)
    tw, th = t.get_size()
    pad = 4
    r = pygame.Rect(x, y, tw + pad * 2, th + pad)
    pygame.draw.rect(surf, bg, r, border_radius=6)
    if border:
        pygame.draw.rect(surf, border, r, 1, border_radius=6)
    surf.blit(t, (x + pad, y + pad // 2))
    return r.width, r.height


def _draw_bar(surf, x, y, w, h, value, color, bg=(16, 18, 26)):
    """Draw a filled progress bar."""
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=2)
    fill = max(0, int(w * value))
    if fill > 0:
        pygame.draw.rect(surf, color, (x, y, fill, h), border_radius=2)
    pygame.draw.rect(surf, (35, 40, 55), (x, y, w, h), 1, border_radius=2)


def _draw_section_header(surf, text, x, y, color, font):
    surf.blit(font.render(f'>> {text}', True, color), (x, y))
    return y + font.get_height() + 4


def _divider(surf, y, x0=10, x1=None, color=None):
    if x1 is None:
        x1 = PANEL_W - 10
    if color is None:
        color = C_BORDER
    pygame.draw.line(surf, color, (x0, y), (x1, y), 1)
    return y + 8


# ─── FPS Sparkline ────────────────────────────────────────────────────────────
class FPSSparkline:
    def __init__(self, history=60):
        self.history = [60.0] * history
        self.max_h = history

    def update(self, fps):
        self.history.append(fps)
        if len(self.history) > self.max_h:
            self.history.pop(0)

    def draw(self, surf, x, y, w, h):
        if len(self.history) < 2:
            return
        max_v = max(max(self.history), 1)
        pts = []
        for i, v in enumerate(self.history):
            px = x + int(i * w / len(self.history))
            py = y + h - int(v / max_v * h)
            pts.append((px, py))

        if len(pts) >= 2:
            s = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
            pygame.draw.lines(s, (0, 180, 255, 140), False, pts, 1)
            # Fill under curve
            fill_pts = pts + [(pts[-1][0], y + h), (pts[0][0], y + h)]
            pygame.draw.polygon(s, (0, 100, 200, 30), fill_pts)
            surf.blit(s, (x - 1, y - 1))


# ─── Dashboard ────────────────────────────────────────────────────────────────
class Dashboard:
    def __init__(self):
        self.selected_robot = -1
        self.command_text = ''
        self.command_focused = False
        self.last_command = ''
        self.last_result = ''
        self.sim_time = 0.0

        # Smooth metric bars (lerp)
        self._bar_vals    = [0.0, 0.0, 0.0, 0.0]
        self._bar_targets = [0.0, 0.0, 0.0, 0.0]

        # Neural network visualizers (one per robot, shown for selected robot)
        self._neural_nets = [NeuralNetViz() for _ in range(5)]

        # FPS sparkline
        self._fps_spark = FPSSparkline(60)

        # Cached surfaces for panel background (avoid recreating each frame)
        self._panel_surf = None
        self._panel_h = 0

        # Card y positions (for click detection)
        self._card_rects = []

        # Tooltip
        self._tooltip_text = ''
        self._tooltip_pos = (0, 0)

    def update(self, dt):
        self.sim_time += dt
        for i in range(4):
            self._bar_vals[i] = _lerp(self._bar_vals[i], self._bar_targets[i], min(1, 6 * dt))
        for nn in self._neural_nets:
            nn.update(dt)

    def draw(self, surf, screen_w, screen_h, robots, task_mgr, fps):
        self._fps_spark.update(fps)

        # Update neural nets with robot data
        for i, nn in enumerate(self._neural_nets):
            if i < len(robots):
                nn.update(0, robot=robots[i])  # dt=0 to avoid double update

        self._draw_left_panel(surf, screen_h, robots, task_mgr)
        self._draw_top_bar(surf, screen_w, robots, task_mgr, fps)
        self._draw_bottom_bar(surf, screen_w, screen_h)

    # ─── Left Panel ──────────────────────────────────────────────────────────

    def _draw_left_panel(self, surf, screen_h, robots, task_mgr):
        # Panel background
        panel = pygame.Surface((PANEL_W, screen_h), pygame.SRCALPHA)
        panel.fill((*C_PANEL, 248))
        surf.blit(panel, (0, 0))

        # Right border glow
        pygame.draw.line(surf, C_BORDER, (PANEL_W - 1, 0), (PANEL_W - 1, screen_h), 1)
        pulse = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(self.sim_time * 1.5))
        bc = tuple(int(c * pulse) for c in C_CYAN)
        pygame.draw.line(surf, bc, (PANEL_W, 0), (PANEL_W, screen_h), 2)

        # Scanline overlay on panel (subtle)
        if int(self.sim_time * 20) % 4 == 0:
            scan_y = int(self.sim_time * 60) % screen_h
            scan = pygame.Surface((PANEL_W, 1), pygame.SRCALPHA)
            scan.fill((0, 200, 255, 8))
            surf.blit(scan, (0, scan_y))

        y = 58  # below top bar

        f_title = _get_font(15)
        f_med   = _get_font(11)
        f_small = _get_font(10)
        f_tiny  = _get_font(9)

        # ── Title ─────────────────────────────────────────────────────────────
        # FARS DIGITAL TWIN with glow
        title_txt = f_title.render('FARS DIGITAL TWIN', True, C_CYAN)
        # Glow behind title
        glow_s = pygame.Surface((title_txt.get_width() + 20, title_txt.get_height() + 8), pygame.SRCALPHA)
        glow_s.fill((0, 100, 200, 25))
        surf.blit(glow_s, (6, y - 2))
        surf.blit(title_txt, (12, y))
        y += 22

        # LIVE indicator + AI model
        dot_pulse = 0.5 + 0.5 * math.sin(self.sim_time * 3)
        dc = (int(40 + 215 * dot_pulse), int(210 * dot_pulse), int(70 * dot_pulse))
        pygame.draw.circle(surf, dc, (18, y + 6), 4)
        # Outer glow ring
        draw_outer = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(draw_outer, (*dc, int(60 * dot_pulse)), (10, 10), 7)
        surf.blit(draw_outer, (8, y - 1))

        from iso_llm import get_model_name
        model = get_model_name()
        model_c = C_CYAN if model != 'FALLBACK' else C_YELLOW
        surf.blit(f_small.render(f'LIVE  |  AI: {model}', True, model_c), (28, y + 1))
        y += 20

        y = _divider(surf, y)

        # ── Robot Fleet ───────────────────────────────────────────────────────
        y = _draw_section_header(surf, 'ROBOT FLEET', 12, y, C_CYAN, f_med)
        self._card_rects = []

        for i, r in enumerate(robots):
            is_sel = (i == self.selected_robot)
            card_h = 62 if not is_sel else 100

            # Card background
            cr = pygame.Rect(6, y, PANEL_W - 12, card_h)
            card_bg = (20, 24, 34) if not is_sel else (25, 30, 44)
            pygame.draw.rect(surf, card_bg, cr, border_radius=4)

            # Hover glow for selected
            if is_sel:
                glow_card = pygame.Surface((cr.width + 4, cr.height + 4), pygame.SRCALPHA)
                gc = (*r.color, 20)
                pygame.draw.rect(glow_card, gc, glow_card.get_rect(), border_radius=5)
                surf.blit(glow_card, (cr.x - 2, cr.y - 2))

            # Left color bar (thick)
            pygame.draw.rect(surf, r.color, (6, y, 4, card_h), border_radius=2)

            # Faint border
            pygame.draw.rect(surf, (*r.color, 40), cr, 1, border_radius=4)

            # Robot ID
            id_txt = f_med.render(f'R{r.id + 1}', True, r.color)
            surf.blit(id_txt, (16, y + 4))

            # State badge
            _draw_pill(surf, r.get_state_label(), 50, y + 4,
                       (0, 0, 0), r.get_state_color(), f_tiny)

            # Battery bar
            bar_x, bar_y = 120, y + 7
            bar_w, bar_h = 90, 8
            bc = C_GREEN if r.battery > 50 else (C_YELLOW if r.battery > 20 else C_RED)
            _draw_bar(surf, bar_x, bar_y, bar_w, bar_h, r.battery / 100, bc)
            pct_txt = f_tiny.render(f'{int(r.battery)}%', True, C_DIM)
            surf.blit(pct_txt, (bar_x + bar_w + 3, bar_y))

            # Location + tasks completed
            loc_txt = f_tiny.render(f'@ {r.current_node}', True, C_DIM)
            surf.blit(loc_txt, (14, y + 20))
            task_txt = f_tiny.render(f'Tasks: {r.tasks_completed}', True, C_DIM)
            surf.blit(task_txt, (160, y + 20))

            # Reward indicator (small dot that glows gold on task complete)
            if r.reward_signal > 0.05:
                rew_pulse = 0.6 + 0.4 * math.sin(self.sim_time * 12)
                rew_c = (int(255 * rew_pulse), int(200 * rew_pulse), int(40))
                pygame.draw.circle(surf, rew_c, (PANEL_W - 16, y + 8), 4)

            # Last thought line
            if r.thoughts:
                thought = r.thoughts[-1][:36]
                surf.blit(f_tiny.render(thought, True, (70, 80, 100)), (14, y + 34))

            # Expanded: full thought log
            if is_sel:
                ty = y + 48
                for j, th in enumerate(r.thoughts[-4:]):
                    surf.blit(f_tiny.render(th[:40], True, (90, 102, 122)), (14, ty))
                    ty += 12

            self._card_rects.append((y, y + card_h, i))
            y += card_h + 3

        y = _divider(surf, y + 4)

        # ── Task Queue ────────────────────────────────────────────────────────
        y = _draw_section_header(surf, 'TASK QUEUE', 12, y, C_YELLOW, f_med)

        q_items = task_mgr.get_queue_display(8)
        if q_items:
            for item in q_items:
                # Priority indicator + color
                if 'P4' in item:
                    pc = C_RED
                    # P4 pulse
                    if int(self.sim_time * 4) % 2:
                        pc = (255, 100, 100)
                elif 'P3' in item:
                    pc = C_ORANGE
                elif 'P2' in item:
                    pc = C_CYAN
                else:
                    pc = C_DIM

                surf.blit(f_tiny.render(item[:40], True, pc), (14, y))
                y += 14
        else:
            surf.blit(f_tiny.render('(no pending tasks)', True, C_DIM), (14, y))
            y += 14

        pending = len(task_mgr.task_queue)
        if pending > 8:
            surf.blit(f_tiny.render(f'  +{pending - 8} more...', True, C_DIM), (14, y))
            y += 14

        y = _divider(surf, y + 4)

        # ── RL Metrics ────────────────────────────────────────────────────────
        y = _draw_section_header(surf, 'RL METRICS', 12, y, C_GREEN, f_med)

        metrics   = task_mgr.get_metrics()
        total_t   = metrics['completed'] + metrics['pending'] + metrics['active']
        eff       = (metrics['completed'] / max(1, total_t)) * 100
        resp      = max(0, 100 - metrics['avg_response_time'] * 4)
        util      = sum(1 for r in robots if r.state not in ('idle', 'charging')) / max(1, len(robots)) * 100
        avg_bat   = sum(r.battery for r in robots) / max(1, len(robots))
        total_rew = sum(r.cumulative_reward for r in robots)

        self._bar_targets = [eff, resp, util, avg_bat]

        labels = ['Efficiency', 'Resp Speed', 'Fleet Util', 'Avg Battery']
        colors = [C_CYAN, C_GREEN, C_ORANGE, C_YELLOW]

        for i in range(4):
            val_txt = f_tiny.render(f'{labels[i]}: {int(self._bar_vals[i])}%', True, C_DIM)
            surf.blit(val_txt, (14, y))
            _draw_bar(surf, 135, y + 2, 140, 8, self._bar_vals[i] / 100, colors[i])
            y += 18

        # Total reward display
        rew_txt = f_tiny.render(f'Total Reward: {total_rew:.0f}', True, C_YELLOW)
        surf.blit(rew_txt, (14, y))
        y += 16

        y = _divider(surf, y + 2)

        # ── Neural Network Visualizer ─────────────────────────────────────────
        # Shows the selected robot's NN, or robot 0 by default
        nn_robot_idx = self.selected_robot if self.selected_robot >= 0 else 0
        if nn_robot_idx < len(self._neural_nets) and nn_robot_idx < len(robots):
            nn_label = f'>> NEURAL NET  R{nn_robot_idx + 1}'
            surf.blit(f_med.render(nn_label, True, robots[nn_robot_idx].color), (12, y))
            y += 18

            nn_h = 110
            nn_rect = (8, y, PANEL_W - 16, nn_h)
            self._neural_nets[nn_robot_idx].draw(surf, nn_rect,
                                                  robot_color=robots[nn_robot_idx].color)
            y += nn_h + 6
        
        y = _divider(surf, y)

        # ── Alerts Log ────────────────────────────────────────────────────────
        y = _draw_section_header(surf, 'ALERTS', 12, y, C_RED, f_med)

        alerts = task_mgr.get_recent_alerts(8)
        # Newer at top
        for alert in reversed(alerts[-8:]):
            al = alert.lower()
            if 'completed' in al or 'done' in al:
                ac = C_GREEN
            elif 'error' in al:
                ac = C_RED
            elif 'warning' in al:
                ac = C_ORANGE
            elif 'new task' in al or '[ai' in al or 'fallback' in al:
                ac = C_CYAN
            else:
                ac = C_DIM

            # Clip text to fit panel
            alert_txt = f_tiny.render(alert[:38], True, ac)
            surf.blit(alert_txt, (14, y))
            y += 13

            if y > screen_h - 160:  # Leave space for mini-map
                break

    # ─── Top Bar ──────────────────────────────────────────────────────────────

    def _draw_top_bar(self, surf, screen_w, robots, task_mgr, fps):
        bar_h = 48

        # Background with subtle gradient
        bar = pygame.Surface((screen_w, bar_h), pygame.SRCALPHA)
        for row in range(bar_h):
            alpha = int(240 - row * 2)
            bar.fill((*C_BG, alpha), (0, row, screen_w, 1))
        surf.blit(bar, (0, 0))

        # Bottom border — animated color gradient
        t = self.sim_time * 0.25
        gradient_colors = [C_CYAN, C_GREEN, C_YELLOW, C_ORANGE, C_RED, C_PURPLE]
        idx = int(t) % len(gradient_colors)
        frac = t % 1.0
        c1 = gradient_colors[idx]
        c2 = gradient_colors[(idx + 1) % len(gradient_colors)]
        gc = tuple(int(c1[j] + (c2[j] - c1[j]) * frac) for j in range(3))
        pygame.draw.line(surf, gc, (0, bar_h - 1), (screen_w, bar_h - 1), 2)

        # Small gradient dots along the line
        dot_spacing = 80
        dot_count = screen_w // dot_spacing
        for k in range(dot_count):
            dot_x = int((k + (self.sim_time * 0.5) % 1.0) * dot_spacing) % screen_w
            dot_c = gradient_colors[(int(self.sim_time * 0.5 + k * 0.3)) % len(gradient_colors)]
            pygame.draw.circle(surf, dot_c, (dot_x, bar_h - 2), 2)

        f_title = _get_font(14)
        f_stats = _get_font(11)
        f_tiny  = _get_font(9)

        # Left: Simulation title
        surf.blit(f_title.render('FARS DIGITAL TWIN  v2.0', True, C_WHITE), (PANEL_W + 12, 14))

        # Right: Stats
        active    = sum(1 for r in robots if r.state not in ('idle', 'charging'))
        completed = task_mgr.get_metrics()['completed']
        mins      = int(self.sim_time) // 60
        secs      = int(self.sim_time) % 60
        total_rew = sum(r.cumulative_reward for r in robots)

        # FPS color
        fps_c = C_DIM
        if fps < 30:
            fps_c = C_RED
        elif fps < 45:
            fps_c = C_ORANGE

        stats_str = (f'ACTIVE: {active}/{len(robots)}   '
                     f'DONE: {completed}   '
                     f'REWARD: {total_rew:.0f}   '
                     f'TIME: {mins:02d}:{secs:02d}   '
                     f'FPS: {fps}')

        stats_txt = f_stats.render(stats_str, True, fps_c)
        surf.blit(stats_txt, (screen_w - stats_txt.get_width() - 12, 16))

        # FPS sparkline (right side)
        self._fps_spark.draw(surf, screen_w - 70, 4, 60, 18)

        # PAUSED indicator
        # (handled in main loop)

    # ─── Bottom Command Bar ───────────────────────────────────────────────────

    def _draw_bottom_bar(self, surf, screen_w, screen_h):
        bar_h = 48
        by = screen_h - bar_h

        bar = pygame.Surface((screen_w, bar_h), pygame.SRCALPHA)
        bar.fill((*C_BG, 240))
        surf.blit(bar, (0, by))

        # Top border
        pygame.draw.line(surf, C_BORDER, (0, by), (screen_w, by), 1)

        f_sm = _get_font(11)
        f_tiny = _get_font(9)

        # CMD label
        surf.blit(f_sm.render('CMD >', True, C_CYAN), (PANEL_W + 10, by + 14))

        # Input field
        ix = PANEL_W + 56
        iw = 380
        ih = 26
        iy = by + 11

        border_col = C_CYAN if self.command_focused else C_BORDER
        # Glow when focused
        if self.command_focused:
            glow = pygame.Surface((iw + 10, ih + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*C_CYAN, 30), glow.get_rect(), border_radius=5)
            surf.blit(glow, (ix - 5, iy - 5))

        pygame.draw.rect(surf, C_DARK, (ix, iy, iw, ih), border_radius=4)
        pygame.draw.rect(surf, border_col, (ix, iy, iw, ih), 1, border_radius=4)

        # Text with cursor blink
        display_text = self.command_text
        if self.command_focused and int(self.sim_time * 2) % 2 == 0:
            display_text += '|'

        if not display_text and not self.command_focused:
            hint = 'Click or press TAB — type a command (e.g. "send robot to ER")'
            surf.blit(f_tiny.render(hint, True, (45, 52, 68)), (ix + 6, iy + 5))
        else:
            surf.blit(f_sm.render(display_text[:48], True, C_WHITE), (ix + 6, iy + 4))

        # Quick command buttons
        quick_cmds = [
            ('EMERGENCY', (255, 50, 60)),
            ('DELIVER',   (255, 160, 35)),
            ('GUIDE',     (255, 220, 50)),
            ('CHECK ALL', (0, 180, 255)),
        ]
        btn_x = ix + iw + 14
        for label, col in quick_cmds:
            btn_w = len(label) * 7 + 14
            btn_h = ih
            btn_rect = pygame.Rect(btn_x, iy, btn_w, btn_h)
            # Button bg
            btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(btn_surf, (*col, 25), btn_surf.get_rect(), border_radius=4)
            pygame.draw.rect(btn_surf, (*col, 120), btn_surf.get_rect(), 1, border_radius=4)
            surf.blit(btn_surf, (btn_x, iy))
            # Label
            lbl = f_tiny.render(label, True, col)
            surf.blit(lbl, (btn_x + 7, iy + 5))
            btn_x += btn_w + 6
            if btn_x > screen_w - 20:
                break

        # Last command result
        if self.last_result:
            res_txt = f_tiny.render(self.last_result[:70], True, C_GREEN)
            # Show on right side if there's space, else below
            res_x = btn_x + 10
            if res_x + res_txt.get_width() < screen_w - 5:
                surf.blit(res_txt, (res_x, iy + 5))

    # ─── Input Handling ───────────────────────────────────────────────────────

    def handle_event(self, event, robots):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            screen_h = pygame.display.get_surface().get_height()
            bar_h = 48
            by = screen_h - bar_h

            # Command bar click
            ix = PANEL_W + 56
            iy = by + 11
            if ix <= mx <= ix + 380 and iy <= my <= iy + 26:
                self.command_focused = True
                return None

            # Quick command buttons
            btn_x = ix + 380 + 14
            quick_cmds = ['emergency assist at EmergencyRoom',
                          'deliver medicine to Pharmacy',
                          'guide patient to MainHall',
                          'security check all rooms']
            for cmd in quick_cmds:
                label = cmd.split()[0].upper()
                btn_w = len(label) * 7 + 14
                if btn_x <= mx <= btn_x + btn_w and iy <= my <= iy + 26:
                    self.command_text = ''
                    self.command_focused = False
                    return ('command', cmd)
                btn_x += btn_w + 6

            # Robot card clicks
            if mx < PANEL_W:
                for top, bot, idx in self._card_rects:
                    if top <= my <= bot:
                        new_sel = idx if self.selected_robot != idx else -1
                        self.selected_robot = new_sel
                        if new_sel >= 0:
                            return ('focus_robot', new_sel)
                        return None
            else:
                self.command_focused = False

        if event.type == pygame.KEYDOWN and self.command_focused:
            if event.key == pygame.K_RETURN:
                cmd = self.command_text.strip()
                self.command_text = ''
                self.command_focused = False
                if cmd:
                    self.last_command = cmd
                    return ('command', cmd)
            elif event.key == pygame.K_BACKSPACE:
                self.command_text = self.command_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.command_focused = False
                self.command_text = ''
            elif event.unicode and event.unicode.isprintable():
                if len(self.command_text) < 80:
                    self.command_text += event.unicode
            return 'consumed'

        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.command_focused = not self.command_focused
            return 'consumed'

        return None
