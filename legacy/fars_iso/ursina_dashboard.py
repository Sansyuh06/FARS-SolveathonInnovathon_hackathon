"""
ursina_dashboard.py -- HUD Dashboard (Ursina 3D, left-panel bento-box operations center style)
"""
from ursina import *
import math

class DashboardUI:
    def __init__(self):
        self._bg = color.rgba32(14, 16, 22, 240)
        self._panel_bg = color.rgba32(18, 20, 28, 245)
        self._border = color.rgb32(40, 50, 70)
        self._text = color.rgb32(200, 205, 215)
        self._dim = color.rgb32(120, 125, 135)
        self._white = color.rgb32(240, 245, 255)
        self._green = color.rgb32(80, 220, 120)
        self._cyan = color.rgb32(0, 200, 255)
        self._orange = color.rgb32(255, 160, 30)
        self._red = color.rgb32(255, 70, 70)
        self._yellow = color.rgb32(255, 220, 50)
        
        aspect = window.aspect_ratio
        
        # ─── Left Panel (Bento Style) ─────────────────────────────────
        self.panel_width = 0.5  # in ui space (0.5 is 25% of screen width)
        self.panel_x = -0.5 * aspect + (self.panel_width / 2)
        
        self.left_panel = Entity(parent=camera.ui, model='quad', scale=(self.panel_width, 1.0), position=(self.panel_x, 0), z=1, color=self._panel_bg, unlit=True)
        # Right border of left panel
        Entity(parent=camera.ui, model='quad', scale=(0.002, 1.0), position=(self.panel_x + self.panel_width/2, 0), z=0.5, color=self._border, unlit=True)
        
        y_start = 0.45
        
        # Title
        Text(text='FARS DIGITAL TWIN', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.02, y_start), scale=0.9, color=self._white)
        Entity(parent=camera.ui, model='circle', scale=0.015, position=(self.panel_x - self.panel_width/2 + 0.03, y_start - 0.04), color=self._green, unlit=True)
        Text(text='LIVE  |  AI: Ollama', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.05, y_start - 0.035), scale=0.6, color=self._dim)
        
        # Divider
        Entity(parent=camera.ui, model='quad', scale=(self.panel_width - 0.04, 0.002), position=(self.panel_x, y_start - 0.07), color=self._border, unlit=True)
        
        # Robot Fleet Header
        Text(text='▸ ROBOT FLEET', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.02, y_start - 0.1), scale=0.7, color=self._cyan)
        
        self.robot_cards = []
        cy = y_start - 0.15
        for i in range(5):
            bg = Entity(parent=camera.ui, model='quad', scale=(self.panel_width - 0.04, 0.07), position=(self.panel_x, cy - i*0.075), color=color.rgba32(25, 30, 45, 0), unlit=True)
            Entity(parent=camera.ui, model='quad', scale=(0.005, 0.07), position=(self.panel_x - self.panel_width/2 + 0.02, cy - i*0.075), color=self._cyan, unlit=True)
            id_txt = Text(text=f'R{i+1}', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.03, cy - i*0.075 + 0.03), scale=0.7, color=self._cyan)
            state_txt = Text(text='IDLE', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.08, cy - i*0.075 + 0.03), scale=0.6, color=self._white)
            bat_bar = Entity(parent=camera.ui, model='quad', scale=(0.1, 0.01), position=(self.panel_x - self.panel_width/2 + 0.2, cy - i*0.075 + 0.025), color=self._green, unlit=True, origin=(-0.5, 0))
            bat_txt = Text(text='100%', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.31, cy - i*0.075 + 0.03), scale=0.6, color=self._dim)
            loc_txt = Text(text='@ Location', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.03, cy - i*0.075 + 0.005), scale=0.55, color=self._dim)
            thought_txt = Text(text='> Idle', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.15, cy - i*0.075 + 0.005), scale=0.55, color=color.rgb32(90, 95, 105))
            self.robot_cards.append({'bg': bg, 'id': id_txt, 'state': state_txt, 'bat_bar': bat_bar, 'bat_txt': bat_txt, 'loc': loc_txt, 'thought': thought_txt})
            
        # Divider
        dy = cy - 4*0.075 - 0.05
        Entity(parent=camera.ui, model='quad', scale=(self.panel_width - 0.04, 0.002), position=(self.panel_x, dy), color=self._border, unlit=True)
        
        # Task Queue Header
        Text(text='▸ TASK QUEUE', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.02, dy - 0.03), scale=0.7, color=self._orange)
        self.queue_text = Text(text='(empty)', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.03, dy - 0.07), scale=0.55, color=self._text)
        
        # Divider
        dy2 = dy - 0.18
        Entity(parent=camera.ui, model='quad', scale=(self.panel_width - 0.04, 0.002), position=(self.panel_x, dy2), color=self._border, unlit=True)
        
        # RL Metrics Header
        Text(text='▸ RL METRICS', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.02, dy2 - 0.03), scale=0.7, color=self._green)
        self.metrics_text = Text(text='Efficiency: 100%\nAvg Resp: 0s\nFleet Util: 0%\nAvg Battery: 100%', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.03, dy2 - 0.07), scale=0.6, color=self._dim, line_height=1.5)
        
        # Divider
        dy3 = dy2 - 0.18
        Entity(parent=camera.ui, model='quad', scale=(self.panel_width - 0.04, 0.002), position=(self.panel_x, dy3), color=self._border, unlit=True)
        
        # Alerts Header
        Text(text='▸ ALERTS', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.02, dy3 - 0.03), scale=0.7, color=self._red)
        self.alert_text = Text(text='', parent=camera.ui, position=(self.panel_x - self.panel_width/2 + 0.03, dy3 - 0.07), scale=0.5, color=self._dim, line_height=1.2)
        
        # ─── Top Bar ──────────────────────────────────────────────────
        top_h = 0.06
        self.top_bar = Entity(parent=camera.ui, model='quad', scale=(aspect * 2, top_h), position=(0, 0.5 - top_h/2), z=1, color=color.rgba32(14, 16, 22, 230), unlit=True)
        Entity(parent=camera.ui, model='quad', scale=(aspect * 2, 0.002), position=(0, 0.5 - top_h), z=0.5, color=self._border, unlit=True)
        
        Text(text='FARS DIGITAL TWIN v2.0', parent=camera.ui, position=(self.panel_x + self.panel_width/2 + 0.02, 0.485), scale=0.8, color=self._white)
        self.top_stats = Text(text='Robots: 0/5   |   Done: 0   |   FPS: 60', parent=camera.ui, position=(aspect - 0.6, 0.485), scale=0.7, color=self._dim)
        
        # ─── Bottom Bar (Command Input) ───────────────────────────────
        bot_h = 0.06
        self.bot_bar = Entity(parent=camera.ui, model='quad', scale=(aspect * 2, bot_h), position=(0, -0.5 + bot_h/2), z=1, color=color.rgba32(14, 16, 22, 230), unlit=True)
        Entity(parent=camera.ui, model='quad', scale=(aspect * 2, 0.002), position=(0, -0.5 + bot_h), z=0.5, color=self._border, unlit=True)
        
        Text(text='> CMD:', parent=camera.ui, position=(self.panel_x + self.panel_width/2 + 0.02, -0.485), scale=0.7, color=self._dim)
        self.cmd_input_text = ''
        self.cmd_display = Text(text='Press TAB to type a command...', parent=camera.ui, position=(self.panel_x + self.panel_width/2 + 0.1, -0.485), scale=0.6, color=self._white)
        self.cmd_feedback = Text(text='', parent=camera.ui, position=(aspect - 0.7, -0.485), scale=0.6, color=self._cyan)
        
        # Inspector (hidden by default)
        self.detail_visible = False
        self.cam_mode = Text(text='CAM: Overview | Scroll=Zoom | Middle=Orbit | Shift+Middle=Pan', parent=camera.ui, position=(-0.4, -0.42), scale=0.5, color=self._dim)

    def update_hud(self, active_robots, total_robots, patients_assisted, tasks_completed, avg_response):
        fps = round(1.0 / max(0.001, time.dt))
        self.top_stats.text = f'Robots: {active_robots}/{total_robots}   |   Done: {tasks_completed}   |   FPS: {fps}'
        eff = min(100, int((tasks_completed / max(1, tasks_completed + active_robots)) * 100))
        self.metrics_text.text = f"Efficiency: {eff}%\nAvg Resp: {avg_response:.1f}s\nFleet Util: {int(active_robots/total_robots*100)}%\nAvg Battery: --"

    def update_queue(self, queue_items):
        self.queue_text.text = '\n'.join(queue_items[:5]) if queue_items else '(empty)'

    def update_active(self, active_items):
        pass # Integrated into robot cards

    def update_robots(self, robot_infos):
        avg_bat = 0
        for i, info in enumerate(robot_infos):
            if i >= len(self.robot_cards): break
            card = self.robot_cards[i]
            card['state'].text = info['state'].upper()
            bp = info['battery'] / 100.0
            avg_bat += info['battery']
            card['bat_bar'].scale_x = 0.1 * bp
            if bp > 0.5: card['bat_bar'].color = self._green
            elif bp > 0.2: card['bat_bar'].color = self._yellow
            else: card['bat_bar'].color = self._red
            card['bat_txt'].text = f"{info['battery']}%"
            card['loc'].text = f"@ {info['location'][:12]}"
            
            thoughts = info['thoughts'].split('\n')
            last_thought = thoughts[-1] if thoughts else "> Idle"
            card['thought'].text = last_thought[:24]
        
        avg_bat = int(avg_bat / max(1, len(robot_infos)))
        lines = self.metrics_text.text.split('\n')
        if len(lines) == 4:
            lines[3] = f"Avg Battery: {avg_bat}%"
            self.metrics_text.text = '\n'.join(lines)

    def update_alerts(self, alerts):
        self.alert_text.text = '\n'.join(alerts[-6:])

    def show_robot_detail(self, info):
        self.detail_visible = True
        idx = int(info['id'].replace('R','')) - 1
        for i, card in enumerate(self.robot_cards):
            card['bg'].color = color.rgba32(40, 50, 70, 150) if i == idx else color.rgba32(25, 30, 45, 0)

    def hide_robot_detail(self):
        self.detail_visible = False
        for card in self.robot_cards: card['bg'].color = color.rgba32(25, 30, 45, 0)

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
        self.cmd_feedback.color = self._red if is_error else self._cyan
        invoke(self._clear_feedback, delay=4)

    def _clear_feedback(self):
        self.cmd_feedback.text = ''
