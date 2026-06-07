"""
ui_dashboard.py -- Unity-Style Simulation HUD Dashboard
Premium transparent HUD with glassmorphism panels, neon accents, and live data readouts.
All text ASCII-safe to avoid font warnings.
"""

from ursina import *


class DashboardUI:
    """Premium simulation HUD dashboard."""

    def __init__(self):
        # ─── Color Palette ─────────────────────────────────────────────
        self._bg        = color.rgba32(8, 12, 24, 220)
        self._bg_light  = color.rgba32(15, 20, 35, 200)
        self._accent    = color.rgb32(0, 200, 255)
        self._success   = color.rgb32(80, 220, 120)
        self._warning   = color.rgb32(255, 200, 50)
        self._danger    = color.rgb32(255, 80, 80)
        self._text      = color.rgb32(210, 215, 225)
        self._muted     = color.rgb32(100, 110, 130)

        # ─── Top HUD Bar ──────────────────────────────────────────────
        self.hud_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 0.075),
            position=(0, 0.462),
            z=1,
            color=self._bg,
            unlit=True,
        )
        # Accent line under HUD
        Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 0.002),
            position=(0, 0.424),
            z=0.5,
            color=self._accent,
            unlit=True,
            alpha=0.6,
        )

        # ── Title ──
        self.hud_title = Text(
            text='FARS DIGITAL TWIN',
            parent=camera.ui,
            position=(-0.88, 0.475),
            scale=0.9,
            color=self._accent,
        )
        Text(
            text='Autonomous Hospital Simulation',
            parent=camera.ui,
            position=(-0.88, 0.45),
            scale=0.5,
            color=self._muted,
        )

        # ── KPI readouts ──
        self.hud_robots = Text(
            text='ROBOTS  0/5',
            parent=camera.ui,
            position=(-0.45, 0.468),
            scale=0.7,
            color=self._accent,
        )
        self.hud_patients = Text(
            text='ASSISTED  0',
            parent=camera.ui,
            position=(-0.15, 0.468),
            scale=0.7,
            color=self._success,
        )
        self.hud_tasks = Text(
            text='COMPLETED  0',
            parent=camera.ui,
            position=(0.13, 0.468),
            scale=0.7,
            color=self._warning,
        )
        self.hud_response = Text(
            text='AVG  0s',
            parent=camera.ui,
            position=(0.4, 0.468),
            scale=0.7,
            color=color.rgb32(255, 160, 100),
        )

        # ── LIVE indicator ──
        Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.008, 0.008),
            position=(0.6, 0.468),
            color=self._success,
            unlit=True,
        )
        Text(
            text='LIVE',
            parent=camera.ui,
            position=(0.615, 0.475),
            scale=0.6,
            color=self._success,
        )

        # ─── Side Panel (right) ───────────────────────────────────────
        self.side_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.44, 0.82),
            position=(0.68, 0.0),
            z=1,
            color=self._bg,
            unlit=True,
        )
        # Side panel accent border
        Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.002, 0.82),
            position=(0.46, 0.0),
            z=0.5,
            color=self._accent,
            unlit=True,
            alpha=0.3,
        )

        self.side_title = Text(
            text='--- CONTROL PANEL ---',
            parent=camera.ui,
            position=(0.5, 0.375),
            scale=0.65,
            color=self._accent,
        )

        # ── Task queue ──
        self.queue_label = Text(
            text='TASK QUEUE',
            parent=camera.ui,
            position=(0.5, 0.31),
            scale=0.55,
            color=self._warning,
        )
        self.queue_text = Text(
            text='(empty)',
            parent=camera.ui,
            position=(0.5, 0.27),
            scale=0.5,
            color=self._text,
        )

        # ── Active tasks ──
        self.active_label = Text(
            text='ACTIVE TASKS',
            parent=camera.ui,
            position=(0.5, 0.10),
            scale=0.55,
            color=self._success,
        )
        self.active_text = Text(
            text='(none)',
            parent=camera.ui,
            position=(0.5, 0.06),
            scale=0.5,
            color=self._text,
        )

        # ── Robot fleet ──
        self.robot_label = Text(
            text='FLEET STATUS',
            parent=camera.ui,
            position=(0.5, -0.08),
            scale=0.55,
            color=self._accent,
        )
        self.robot_text = Text(
            text='',
            parent=camera.ui,
            position=(0.5, -0.12),
            scale=0.45,
            color=self._text,
        )

        # ── System alerts ──
        self.alert_label = Text(
            text='SYSTEM LOG',
            parent=camera.ui,
            position=(0.5, -0.28),
            scale=0.55,
            color=self._danger,
        )
        self.alert_text = Text(
            text='',
            parent=camera.ui,
            position=(0.5, -0.32),
            scale=0.4,
            color=self._muted,
        )

        # ─── Command Input (bottom) ──────────────────────────────────
        self.cmd_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.2, 0.055),
            position=(0, -0.452),
            z=1,
            color=self._bg,
            unlit=True,
        )
        # Bottom accent line
        Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.2, 0.002),
            position=(0, -0.424),
            z=0.5,
            color=self._accent,
            unlit=True,
            alpha=0.3,
        )
        self.cmd_prompt = Text(
            text='> CMD:',
            parent=camera.ui,
            position=(-0.58, -0.443),
            scale=0.65,
            color=self._accent,
        )

        self.cmd_input_text = ''
        self.cmd_display = Text(
            text='Press TAB to type a command...',
            parent=camera.ui,
            position=(-0.45, -0.443),
            scale=0.55,
            color=self._muted,
        )

        self.cmd_feedback = Text(
            text='',
            parent=camera.ui,
            position=(-0.45, -0.41),
            scale=0.5,
            color=self._success,
        )

        # ─── Robot Inspector Panel ────────────────────────────────────
        self.detail_visible = False

        self.detail_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.52, 0.72),
            position=(-0.62, 0.04),
            z=1,
            color=self._bg,
            unlit=True,
            enabled=False,
        )

        # Inspector accent border
        self.detail_border = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.002, 0.72),
            position=(-0.36, 0.04),
            z=0.5,
            color=self._accent,
            unlit=True,
            alpha=0.3,
            enabled=False,
        )

        self.detail_header = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.52, 0.055),
            position=(-0.62, 0.375),
            z=0.5,
            color=color.rgba32(0, 100, 180, 180),
            unlit=True,
            enabled=False,
        )
        self.detail_title = Text(
            text='ROBOT INSPECTOR',
            parent=camera.ui,
            position=(-0.87, 0.385),
            scale=0.75,
            color=color.white,
            enabled=False,
        )
        self.detail_text = Text(
            text='',
            parent=camera.ui,
            position=(-0.87, 0.31),
            scale=0.55,
            color=self._text,
            enabled=False,
        )

        self.thought_label = Text(
            text='--- AI THOUGHT STREAM ---',
            parent=camera.ui,
            position=(-0.87, 0.05),
            scale=0.55,
            color=self._accent,
            enabled=False,
        )

        self.thought_text = Text(
            text='> Initializing...',
            parent=camera.ui,
            position=(-0.87, 0.0),
            scale=0.5,
            color=self._success,
            enabled=False,
        )

        # Camera mode indicator
        self.cam_mode = Text(
            text='CAM: Overview | Scroll=Zoom | Right-drag=Orbit | WASD=Pan',
            parent=camera.ui,
            position=(-0.65, -0.48),
            scale=0.45,
            color=self._muted,
        )

    # ─── Update Methods ───────────────────────────────────────────────
    def update_hud(self, active_robots, total_robots, patients_assisted, tasks_completed, avg_response):
        self.hud_robots.text = f'ROBOTS  {active_robots}/{total_robots}'
        self.hud_patients.text = f'ASSISTED  {patients_assisted}'
        self.hud_tasks.text = f'COMPLETED  {tasks_completed}'
        self.hud_response.text = f'AVG  {avg_response}s'

    def update_queue(self, queue_items):
        self.queue_text.text = '\n'.join(queue_items[:6]) if queue_items else '(empty)'

    def update_active(self, active_items):
        self.active_text.text = '\n'.join(active_items[:5]) if active_items else '(none)'

    def update_robots(self, robot_infos):
        lines = []
        for info in robot_infos:
            filled = int(info['battery'] / 10)
            bat_bar = '#' * filled + '-' * (10 - filled)
            lines.append(f"{info['id']} [{info['state'].upper():5s}] {bat_bar} {info['battery']}%")
        self.robot_text.text = '\n'.join(lines)

    def update_alerts(self, alerts):
        self.alert_text.text = '\n'.join(alerts[-4:])

    def show_robot_detail(self, info):
        self.detail_visible = True
        self.detail_bg.enabled = True
        self.detail_border.enabled = True
        self.detail_header.enabled = True
        self.detail_title.enabled = True
        self.detail_text.enabled = True
        self.thought_label.enabled = True
        self.thought_text.enabled = True

        self.detail_title.text = f"= {info['id']} INSPECTOR ="

        self.detail_text.text = (
            f"State:     {info['state'].upper()}\n"
            f"Battery:   {info['battery']}%\n"
            f"Location:  {info['location']}\n"
            f"Task:      {info['current_task']}\n\n"
            f"Tasks completed: {info['tasks_completed']}"
        )

        self.thought_text.text = info.get('thoughts', '> No thoughts yet.')

    def hide_robot_detail(self):
        self.detail_visible = False
        self.detail_bg.enabled = False
        self.detail_border.enabled = False
        self.detail_header.enabled = False
        self.detail_title.enabled = False
        self.detail_text.enabled = False
        self.thought_label.enabled = False
        self.thought_text.enabled = False

    # ─── Command Input ─────────────────────────────────────────────────
    def handle_text_input(self, key):
        if key == 'backspace':
            self.cmd_input_text = self.cmd_input_text[:-1]
        elif key == 'space':
            self.cmd_input_text += ' '
        elif len(key) == 1 and key.isprintable():
            self.cmd_input_text += key

        if self.cmd_input_text:
            self.cmd_display.text = self.cmd_input_text + '|'
        else:
            self.cmd_display.text = 'Press TAB to type a command...'

    def get_and_clear_command(self):
        cmd = self.cmd_input_text.strip()
        self.cmd_input_text = ''
        self.cmd_display.text = 'Press TAB to type a command...'
        return cmd

    def show_feedback(self, msg, is_error=False):
        self.cmd_feedback.text = msg
        self.cmd_feedback.color = self._danger if is_error else self._success
        invoke(self._clear_feedback, delay=4)

    def _clear_feedback(self):
        self.cmd_feedback.text = ''

    def set_camera_mode(self, mode_text):
        self.cam_mode.text = mode_text
