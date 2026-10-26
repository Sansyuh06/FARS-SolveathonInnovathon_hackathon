"""
FARSverse - NVIDIA Omniverse™ Isaac Sim Desktop Studio (PyQt6 Edition)
Desktop-quality Robotics Digital Twin & Simulation Platform
Native Windows GUI with 60 FPS PBR Viewport, Pan/Zoom/Drag, and Local Ollama Integration.
"""
from __future__ import annotations
import sys
import os
import json
import math
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal, QThread
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QLinearGradient,
    QRadialGradient, QPainterPath, QIcon, QKeySequence, QAction
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
    QPushButton, QComboBox, QTabWidget, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QProgressBar, QCheckBox,
    QMessageBox, QStatusBar, QToolBar, QSizePolicy
)

API_BASE = "http://127.0.0.1:8080"


# ----------------------------------------------------------------------
# 1. Background State Poller (Non-blocking Thread)
# ----------------------------------------------------------------------
class StatePollerThread(QThread):
    state_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True

    def run(self):
        while self.running:
            try:
                req = urllib.request.Request(f"{API_BASE}/api/farsverse/state")
                with urllib.request.urlopen(req, timeout=0.8) as res:
                    if res.status == 200:
                        data = json.loads(res.read().decode('utf-8'))
                        self.state_received.emit(data)
                        self.connection_changed.emit(True)
            except Exception:
                self.connection_changed.emit(False)
            time.sleep(0.08)  # 12.5 Hz network polling

    def stop(self):
        self.running = False
        self.wait()


# ----------------------------------------------------------------------
# 2. Interactive Omniverse 60 FPS Viewport Widget
# ----------------------------------------------------------------------
class OmniverseViewportWidget(QWidget):
    entity_selected = pyqtSignal(str, str)  # (type, id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        # Viewport Transforms
        self.zoom = 10.0  # Pixels per meter
        self.pan_x = 450.0
        self.pan_y = 350.0
        self.dragging = False
        self.drag_start = QPointF(0, 0)
        self.last_mouse_pos = QPointF(0, 0)

        # Simulation Data Cache
        self.world_data: Dict[str, Any] = {}
        self.robots_cache: Dict[str, Dict[str, Any]] = {}
        self.humans_cache: Dict[str, Dict[str, Any]] = {}
        self.obstacles_data: List[Dict[str, Any]] = []

        # Smooth Motion Interpolation Buffers (60 FPS)
        self.robot_render_pos: Dict[str, Tuple[float, float, float]] = {}  # id -> (x, z, rot)
        self.human_render_pos: Dict[str, Tuple[float, float]] = {}         # id -> (x, z)
        self.lidar_angle = 0.0

        # Viewport Settings
        self.camera_mode = "angled"  # 'angled', 'topdown', 'follow'
        self.show_paths = True
        self.show_grid = True
        self.show_labels = True
        self.selected_entity: Optional[Tuple[str, str]] = None  # (type, id)

        # 60 FPS Render Timer
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.on_render_tick)
        self.render_timer.start(16)  # ~60 FPS

        # FPS Measurement
        self.fps_counter = 0
        self.current_fps = 60
        self.last_fps_time = time.time()

    def update_snapshot(self, snapshot: Dict[str, Any]):
        """Ingest new authoritative snapshot from backend."""
        self.world_data = snapshot.get('world', {})
        self.obstacles_data = self.world_data.get('obstacles', [])

        # Robots
        for r in snapshot.get('robots', []):
            rid = r['id']
            self.robots_cache[rid] = r
            if rid not in self.robot_render_pos:
                self.robot_render_pos[rid] = (r['x'], r['z'], r.get('rotation_y', 0.0))

        # Humans
        for h in snapshot.get('humans', []):
            hid = h['id']
            self.humans_cache[hid] = h
            if hid not in self.human_render_pos:
                self.human_render_pos[hid] = (h['x'], h['z'])

    def on_render_tick(self):
        """Continuous 60 FPS interpolation and animation loop."""
        self.lidar_angle += 8.0  # Rotate 3D LiDAR puck
        if self.lidar_angle >= 360.0:
            self.lidar_angle -= 360.0

        # FPS Calculation
        self.fps_counter += 1
        now = time.time()
        if now - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = now

        # Interpolate Robots
        pos_lerp = 0.22
        rot_lerp = 0.24
        for rid, r in self.robots_cache.items():
            if rid in self.robot_render_pos:
                cur_x, cur_z, cur_rot = self.robot_render_pos[rid]
                tx, tz = r['x'], r['z']
                trot = r.get('rotation_y', 0.0)

                # Linear interpolation for position
                nx = cur_x + (tx - cur_x) * pos_lerp
                nz = cur_z + (tz - cur_z) * pos_lerp

                # Angular lerp
                drot = (trot - cur_rot + 180.0) % 360.0 - 180.0
                nrot = cur_rot + drot * rot_lerp
                self.robot_render_pos[rid] = (nx, nz, nrot)

        # Interpolate Humans
        for hid, h in self.humans_cache.items():
            if hid in self.human_render_pos:
                cur_x, cur_z = self.human_render_pos[hid]
                tx, tz = h['x'], h['z']
                nx = cur_x + (tx - cur_x) * 0.18
                nz = cur_z + (tz - cur_z) * 0.18
                self.human_render_pos[hid] = (nx, nz)

        # Follow camera tracking
        if self.camera_mode == "follow" and self.selected_entity and self.selected_entity[0] == "robot":
            rid = self.selected_entity[1]
            if rid in self.robot_render_pos:
                rx, rz, _ = self.robot_render_pos[rid]
                target_px = self.width() / 2.0 - rx * self.zoom
                target_py = self.height() / 2.0 - rz * self.zoom
                self.pan_x += (target_px - self.pan_x) * 0.1
                self.pan_y += (target_py - self.pan_y) * 0.1

        self.update()

    def reset_view(self):
        """Center and fit hospital environment."""
        self.zoom = 11.5
        self.pan_x = self.width() / 2.0
        self.pan_y = self.height() / 2.0
        self.update()

    def world_to_screen(self, wx: float, wz: float) -> QPointF:
        sx = self.pan_x + wx * self.zoom
        sy = self.pan_y + wz * self.zoom
        return QPointF(sx, sy)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        wx = (sx - self.pan_x) / self.zoom
        wz = (sy - self.pan_y) / self.zoom
        return wx, wz

    # ------------------------------------------------------------------
    # Mouse Navigation Events (Pan, Zoom, Select)
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton, Qt.MouseButton.MiddleButton):
            self.dragging = True
            self.drag_start = event.position()
            self.last_mouse_pos = event.position()

        # Selection Hit Testing on Left Click
        if event.button() == Qt.MouseButton.LeftButton:
            wx, wz = self.screen_to_world(event.position().x(), event.position().y())

            # 1. Hit test Robots
            hit_robot = None
            for rid, (rx, rz, _) in self.robot_render_pos.items():
                if math.hypot(wx - rx, wz - rz) < 1.4:
                    hit_robot = rid
                    break
            if hit_robot:
                self.selected_entity = ("robot", hit_robot)
                self.entity_selected.emit("robot", hit_robot)
                self.update()
                return

            # 2. Hit test Humans
            hit_human = None
            for hid, (hx, hz) in self.human_render_pos.items():
                if math.hypot(wx - hx, wz - hz) < 1.0:
                    hit_human = hid
                    break
            if hit_human:
                self.selected_entity = ("human", hit_human)
                self.entity_selected.emit("human", hit_human)
                self.update()
                return

            # 3. Hit test Obstacles
            hit_obs = None
            for o in self.obstacles_data:
                ox, oz = o['x'], o['z']
                ow, od = o['width'] / 2.0, o['depth'] / 2.0
                if (ox - ow <= wx <= ox + ow) and (oz - od <= wz <= oz + od):
                    hit_obs = o['id']
                    break
            if hit_obs:
                self.selected_entity = ("obstacle", hit_obs)
                self.entity_selected.emit("obstacle", hit_obs)
                self.update()
                return

            # 4. Hit test Rooms
            hit_room = None
            for rm in self.world_data.get('rooms', []):
                rx, rz = rm['x'], rm['z']
                rw, rd = rm['width'] / 2.0, rm['depth'] / 2.0
                if (rx - rw <= wx <= rx + rw) and (rz - rd <= wz <= rz + rd):
                    hit_room = rm['id']
                    break
            if hit_room:
                self.selected_entity = ("room", hit_room)
                self.entity_selected.emit("room", hit_room)
                self.update()
                return

            # Clicked empty void -> clear selection
            self.selected_entity = None
            self.entity_selected.emit("", "")
            self.update()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.position() - self.last_mouse_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def wheelEvent(self, event):
        """Precision cursor-centered exponential zooming."""
        angle = event.angleDelta().y()
        factor = 1.15 if angle > 0 else 0.87

        cursor = event.position()
        self.pan_x = cursor.x() - (cursor.x() - self.pan_x) * factor
        self.pan_y = cursor.y() - (cursor.y() - self.pan_y) * factor
        self.zoom = max(2.0, min(50.0, self.zoom * factor))
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.reset_view()

    # ------------------------------------------------------------------
    # High-Performance NVIDIA Omniverse 2.5D Vector Drawing
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()

        # 1. Industrial Titanium Monolithic Floor
        painter.fillRect(0, 0, w, h, QColor(0x0e, 0x11, 0x17))

        # 2. Omniverse CAD Grid (Meter & 5-Meter Structural Lines)
        if self.show_grid:
            self._draw_grid(painter, w, h)

        # 3. Interconnected Corridor Runways & Painted Guidelines
        self._draw_corridors(painter)

        # 4. Architectural Rooms & Medical Furniture
        self._draw_rooms(painter)

        # 5. Dynamic Obstacles
        self._draw_obstacles(painter)

        # 6. A* Navigation Path Overlays & Destination Pins
        if self.show_paths:
            self._draw_paths(painter)

        # 7. Holographic Human Digital Twin Avatars
        self._draw_humans(painter)

        # 8. Nova Carter AMRs (Wheels, LiDAR Puck, Halo Rings)
        self._draw_robots(painter)

        # 9. Omniverse Viewport HUD & 3D Orientation Gizmo
        self._draw_hud(painter, w, h)

    def _draw_grid(self, painter: QPainter, w: int, h: int):
        painter.save()
        min_wx, min_wz = self.screen_to_world(0, 0)
        max_wx, max_wz = self.screen_to_world(w, h)

        start_x = int(math.floor(min_wx)) - 1
        end_x = int(math.ceil(max_wx)) + 1
        start_z = int(math.floor(min_wz)) - 1
        end_z = int(math.ceil(max_wz)) + 1

        pen_fine = QPen(QColor(0x1a, 0x21, 0x2d), 1.0)
        pen_major = QPen(QColor(0x2d, 0x37, 0x48), 1.5)

        for x in range(start_x, end_x + 1):
            p1 = self.world_to_screen(x, min_wz)
            p2 = self.world_to_screen(x, max_wz)
            painter.setPen(pen_major if x % 5 == 0 else pen_fine)
            painter.drawLine(p1, p2)

        for z in range(start_z, end_z + 1):
            p1 = self.world_to_screen(min_wx, z)
            p2 = self.world_to_screen(max_wx, z)
            painter.setPen(pen_major if z % 5 == 0 else pen_fine)
            painter.drawLine(p1, p2)

        painter.restore()

    def _draw_corridors(self, painter: QPainter):
        painter.save()
        # Spine Hallway
        p_top = self.world_to_screen(-3.5, -30.0)
        p_bot = self.world_to_screen(3.5, 30.0)
        rect_spine = QRectF(p_top.x(), p_top.y(), p_bot.x() - p_top.x(), p_bot.y() - p_top.y())
        painter.fillRect(rect_spine, QColor(0x14, 0x18, 0x22))

        # Cross Hallway
        p_l = self.world_to_screen(-32.0, -3.0)
        p_r = self.world_to_screen(32.0, 3.0)
        rect_cross = QRectF(p_l.x(), p_l.y(), p_r.x() - p_l.x(), p_r.y() - p_l.y())
        painter.fillRect(rect_cross, QColor(0x14, 0x18, 0x22))

        # Painted Dashed Runway Centerlines
        painter.setPen(QPen(QColor(0x47, 0x55, 0x69), 1.5, Qt.PenStyle.DashLine))
        pt1 = self.world_to_screen(0.0, -28.0)
        pt2 = self.world_to_screen(0.0, 28.0)
        painter.drawLine(pt1, pt2)

        pt3 = self.world_to_screen(-30.0, 0.0)
        pt4 = self.world_to_screen(30.0, 0.0)
        painter.drawLine(pt3, pt4)
        painter.restore()

    def _draw_rooms(self, painter: QPainter):
        painter.save()
        font_label = QFont("Monospace", 8, QFont.Weight.Bold)
        painter.setFont(font_label)

        for rm in self.world_data.get('rooms', []):
            rx, rz = rm['x'], rm['z']
            rw, rd = rm['width'], rm['depth']
            top_left = self.world_to_screen(rx - rw / 2.0, rz - rd / 2.0)
            bot_right = self.world_to_screen(rx + rw / 2.0, rz + rd / 2.0)
            rect = QRectF(top_left.x(), top_left.y(), bot_right.x() - top_left.x(), bot_right.y() - top_left.y())

            # Room Floor Tint
            rtype = rm.get('type', '')
            fill_col = QColor(0x16, 0x1d, 0x2a)
            border_col = QColor(0x33, 0x41, 0x55)
            if rtype == "icu":
                fill_col = QColor(0x10, 0x26, 0x2c)
                border_col = QColor(0x0e, 0x74, 0x90)
            elif rtype == "pharmacy":
                fill_col = QColor(0x11, 0x28, 0x20)
                border_col = QColor(0x05, 0x96, 0x69)
            elif rtype == "emergency":
                fill_col = QColor(0x2d, 0x16, 0x19)
                border_col = QColor(0xb9, 0x1c, 0x1c)
            elif rtype == "dock":
                fill_col = QColor(0x2a, 0x1e, 0x12)
                border_col = QColor(0xd9, 0x77, 0x06)

            is_sel = self.selected_entity and self.selected_entity[0] == "room" and self.selected_entity[1] == rm['id']
            if is_sel:
                border_col = QColor(0x76, 0xb9, 0x00)

            painter.setBrush(QBrush(fill_col))
            painter.setPen(QPen(border_col, 2.0 if is_sel else 1.5))
            painter.drawRoundedRect(rect, 4.0, 4.0)

            # Hazard Stripes for Charging Dock
            if rtype == "dock":
                painter.setPen(QPen(QColor(0xf5, 0x9e, 0x0b, 100), 2.0))
                p1 = self.world_to_screen(rx - rw / 2.0, rz - rd / 2.0)
                p2 = self.world_to_screen(rx + rw / 2.0, rz + rd / 2.0)
                painter.drawLine(p1, p2)

            # Architectural Door Openings
            door_p1 = self.world_to_screen(rx - 1.2, rz - rd / 2.0)
            door_p2 = self.world_to_screen(rx + 1.2, rz - rd / 2.0)
            painter.setPen(QPen(QColor(0x0e, 0x11, 0x17), 3.0))
            painter.drawLine(door_p1, door_p2)

            # Patient Bed Model
            if rtype == "patient_room":
                b_p = self.world_to_screen(rx + 0.5, rz)
                bw, bd = 1.3 * self.zoom, 2.2 * self.zoom
                bed_rect = QRectF(b_p.x() - bw / 2.0, b_p.y() - bd / 2.0, bw, bd)
                painter.setBrush(QBrush(QColor(0x02, 0x84, 0xc7)))
                painter.setPen(QPen(QColor(0x03, 0x69, 0xa1), 1.0))
                painter.drawRoundedRect(bed_rect, 2.0, 2.0)

            # Room Signboard Text
            if self.show_labels:
                painter.setPen(QPen(QColor(0x94, 0xa3, 0xb8)))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, rm.get('name', rm['id']).upper())

        painter.restore()

    def _draw_obstacles(self, painter: QPainter):
        painter.save()
        for o in self.obstacles_data:
            ox, oz = o['x'], o['z']
            ow, od = o['width'], o['depth']
            top_left = self.world_to_screen(ox - ow / 2.0, oz - od / 2.0)
            bot_right = self.world_to_screen(ox + ow / 2.0, oz + od / 2.0)
            rect = QRectF(top_left.x(), top_left.y(), bot_right.x() - top_left.x(), bot_right.y() - top_left.y())

            is_blocked = o.get('active', False)
            col = QColor(0xf5, 0x9e, 0x0b) if is_blocked else QColor(0x47, 0x55, 0x69)
            painter.setBrush(QBrush(col))
            painter.setPen(QPen(QColor(0x00, 0x00, 0x00), 1.5))
            painter.drawRect(rect)
        painter.restore()

    def _draw_paths(self, painter: QPainter):
        painter.save()
        for rid, r in self.robots_cache.items():
            waypoints = r.get('waypoints', [])
            wp_idx = r.get('waypoint_index', 0)
            if not waypoints or wp_idx >= len(waypoints):
                continue

            rx, rz, _ = self.robot_render_pos.get(rid, (r['x'], r['z'], 0))
            path_pts = [self.world_to_screen(rx, rz)]
            for i in range(wp_idx, len(waypoints)):
                path_pts.append(self.world_to_screen(waypoints[i][0], waypoints[i][1]))

            if len(path_pts) >= 2:
                # Color code
                col = QColor(0x76, 0xb9, 0x00) if r.get('state') == "NAVIGATING" else QColor(0x06, 0xb6, 0xd4)
                painter.setPen(QPen(col, 2.5, Qt.PenStyle.DashLine))
                for k in range(len(path_pts) - 1):
                    painter.drawLine(path_pts[k], path_pts[k + 1])

                # Destination Pin
                dest = path_pts[-1]
                painter.setBrush(QBrush(col))
                painter.setPen(QPen(QColor(0xff, 0xff, 0xff), 1.0))
                painter.drawEllipse(dest, 6.0, 6.0)

        painter.restore()

    def _draw_humans(self, painter: QPainter):
        painter.save()
        for hid, (hx, hz) in self.human_render_pos.items():
            h_data = self.humans_cache.get(hid, {})
            pos = self.world_to_screen(hx, hz)

            # Role Color
            role = h_data.get('agent_type', 'patient')
            col = QColor(0x38, 0xbd, 0xf8)
            if role == "doctor":
                col = QColor(0xf8, 0xfa, 0xfc)
            elif role == "nurse":
                col = QColor(0x0d, 0x94, 0x88)
            elif role == "visitor":
                col = QColor(0xa8, 0x55, 0xf7)

            is_sel = self.selected_entity and self.selected_entity[0] == "human" and self.selected_entity[1] == hid
            if is_sel:
                col = QColor(0x76, 0xb9, 0x00)

            # Ground Holographic Ring
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(col, 1.5))
            painter.drawEllipse(pos, 7.0, 7.0)

            # Human Avatar Body
            painter.setBrush(QBrush(col))
            painter.setPen(QPen(QColor(0x00, 0x00, 0x00), 1.0))
            painter.drawEllipse(pos, 4.5, 4.5)

            # Needs Help Emergency Pulsing Beacon
            if h_data.get('needs_help', False):
                painter.setBrush(QBrush(QColor(0xef, 0x44, 0x44)))
                painter.setPen(QPen(QColor(0xff, 0xff, 0xff), 1.0))
                painter.drawEllipse(QPointF(pos.x(), pos.y() - 10.0), 3.5, 3.5)

        painter.restore()

    def _draw_robots(self, painter: QPainter):
        painter.save()
        font_tag = QFont("Monospace", 8, QFont.Weight.Bold)
        painter.setFont(font_tag)

        for rid, (rx, rz, rrot) in self.robot_render_pos.items():
            r_data = self.robots_cache.get(rid, {})
            pos = self.world_to_screen(rx, rz)
            radius = 0.75 * self.zoom

            # State Color
            state = r_data.get('state', 'IDLE')
            halo_col = QColor(0x76, 0xb9, 0x00)  # NVIDIA Green
            if state == "NAVIGATING":
                halo_col = QColor(0x06, 0xb6, 0xd4)
            elif state == "CHARGING":
                halo_col = QColor(0xf5, 0x9e, 0x0b)
            elif state == "ERROR" or r_data.get('battery', 100) < 15:
                halo_col = QColor(0xef, 0x44, 0x44)
            elif state in ("ASSISTING", "DELIVERING"):
                halo_col = QColor(0xa8, 0x55, 0xf7)

            is_sel = self.selected_entity and self.selected_entity[0] == "robot" and self.selected_entity[1] == rid

            # 1. Omniverse USD Target Selection Bounding Bracket
            if is_sel:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(0x76, 0xb9, 0x00), 2.5))
                painter.drawEllipse(pos, radius + 7.0, radius + 7.0)

            # 2. NVIDIA Nova Carter Stealth Drive Base
            painter.setBrush(QBrush(QColor(0x18, 0x1a, 0x22)))
            painter.setPen(QPen(halo_col, 2.5))
            painter.drawEllipse(pos, radius, radius)

            # 3. Inner Titanium Payload Deck
            painter.setBrush(QBrush(QColor(0x27, 0x2b, 0x36)))
            painter.setPen(QPen(QColor(0x3f, 0x47, 0x56), 1.0))
            painter.drawEllipse(pos, radius * 0.65, radius * 0.65)

            # 4. Heading Vector Line & Front Sensor Aperture
            rad = math.radians(rrot)
            dir_x = math.sin(rad)
            dir_z = math.cos(rad)
            p_nose = QPointF(pos.x() + dir_x * radius, pos.y() + dir_z * radius)
            painter.setPen(QPen(halo_col, 3.0))
            painter.drawLine(pos, p_nose)

            # 5. Spinning 3D LiDAR Scanner Cone & Laser Sweep
            lidar_rad = math.radians(self.lidar_angle)
            lx = math.cos(lidar_rad) * radius * 1.8
            lz = math.sin(lidar_rad) * radius * 1.8
            painter.setPen(QPen(QColor(0x76, 0xb9, 0x00, 120), 1.5))
            painter.drawLine(pos, QPointF(pos.x() + lx, pos.y() + lz))

            # 6. Floating Overhead Label (ID + Battery Bar)
            if self.show_labels:
                bat = int(round(r_data.get('battery', 100.0)))
                badge_w = 70.0
                badge_h = 24.0
                badge_x = pos.x() - badge_w / 2.0
                badge_y = pos.y() - radius - 30.0

                painter.setBrush(QBrush(QColor(0x11, 0x14, 0x1a, 220)))
                painter.setPen(QPen(halo_col, 1.0))
                painter.drawRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 3.0, 3.0)

                painter.setPen(QPen(QColor(0xff, 0xff, 0xff)))
                painter.drawText(QRectF(badge_x + 4, badge_y + 2, badge_w - 8, 12), Qt.AlignmentFlag.AlignLeft, rid)

                painter.setPen(QPen(halo_col))
                painter.drawText(QRectF(badge_x + 4, badge_y + 2, badge_w - 8, 12), Qt.AlignmentFlag.AlignRight, f"{bat}%")

                # Battery bar line
                bar_col = QColor(0x76, 0xb9, 0x00) if bat > 20 else QColor(0xef, 0x44, 0x44)
                painter.setBrush(QBrush(bar_col))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(badge_x + 4, badge_y + 16, (badge_w - 8) * (bat / 100.0), 3.0))

        painter.restore()

    def _draw_hud(self, painter: QPainter, w: int, h: int):
        painter.save()
        font_hud = QFont("Monospace", 9, QFont.Weight.Bold)
        painter.setFont(font_hud)

        # Top-Left Telemetry Badge
        badge_rect = QRectF(12, 12, 380, 26)
        painter.setBrush(QBrush(QColor(0x11, 0x14, 0x1a, 220)))
        painter.setPen(QPen(QColor(0x27, 0x2d, 0x3b), 1.0))
        painter.drawRoundedRect(badge_rect, 4.0, 4.0)

        painter.setBrush(QBrush(QColor(0x76, 0xb9, 0x00)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(22, 21, 8, 8)

        painter.setPen(QPen(QColor(0x76, 0xb9, 0x00)))
        painter.drawText(36, 29, "NVIDIA OMNIVERSE™")
        painter.setPen(QPen(QColor(0xff, 0xff, 0xff, 200)))
        painter.drawText(175, 29, f"| ISAAC SIM | {self.current_fps} FPS")

        # Top-Right 3D Axis Compass Gizmo
        axis_cx = w - 45
        axis_cy = 45
        painter.setPen(QPen(QColor(0xef, 0x44, 0x44), 2.0))
        painter.drawLine(axis_cx, axis_cy, axis_cx + 22, axis_cy)
        painter.drawText(axis_cx + 25, axis_cy + 4, "X")

        painter.setPen(QPen(QColor(0x76, 0xb9, 0x00), 2.0))
        painter.drawLine(axis_cx, axis_cy, axis_cx, axis_cy - 22)
        painter.drawText(axis_cx - 4, axis_cy - 25, "Y")

        painter.setPen(QPen(QColor(0x06, 0xb6, 0xd4), 2.0))
        painter.drawLine(axis_cx, axis_cy, axis_cx - 15, axis_cy + 15)
        painter.drawText(axis_cx - 24, axis_cy + 22, "Z")

        # Bottom Instruction
        footer_text = "Drag: Pan | Scroll: Zoom | Click: Select Entity | Double-Click: Fit"
        painter.setPen(QPen(QColor(0xff, 0xff, 0xff, 120)))
        painter.drawText(QRectF(0, h - 24, w, 20), Qt.AlignmentFlag.AlignCenter, footer_text)

        painter.restore()


# ----------------------------------------------------------------------
# 3. Main Omniverse PyQt6 Desktop Studio Window
# ----------------------------------------------------------------------
class OmniverseMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FARSverse - NVIDIA Omniverse™ Isaac Sim (PyQt6 Desktop)")
        self.resize(1500, 920)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0e1117;
            }
            QWidget {
                background-color: #0e1117;
                color: #e2e8f0;
                font-family: 'Consolas', 'Segoe UI', monospace;
            }
            QToolBar {
                background-color: #11141a;
                border-bottom: 1px solid #232834;
                padding: 4px;
                spacing: 6px;
            }
            QPushButton {
                background-color: #1a202c;
                border: 1px solid #2d3748;
                border-radius: 4px;
                padding: 5px 10px;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d3748;
                color: #76b900;
                border-color: #76b900;
            }
            QLineEdit {
                background-color: #161a22;
                border: 1px solid #272d3b;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #76b900;
            }
            QTreeWidget {
                background-color: #11141a;
                border: 1px solid #232834;
                color: #cbd5e1;
                font-size: 11px;
            }
            QTreeWidget::item:selected {
                background-color: #76b900;
                color: #000000;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #232834;
                background-color: #11141a;
            }
            QTabBar::tab {
                background-color: #161a22;
                border: 1px solid #232834;
                padding: 6px 12px;
                margin-right: 2px;
                color: #94a3b8;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #11141a;
                color: #76b900;
                font-weight: bold;
                border-bottom: 2px solid #76b900;
            }
            QStatusBar {
                background-color: #11141a;
                border-top: 1px solid #232834;
                color: #94a3b8;
                font-size: 10px;
            }
        """)

        # Central Layout with Splitters
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Initialize Viewport First so Toolbar and Panels can bind to it
        self.viewport = OmniverseViewportWidget(self)
        self.viewport.entity_selected.connect(self.on_entity_selected)

        # 2. Build Omniverse Top Toolbar
        self._build_toolbar()

        # 3. Main Horizontal Splitter (Stage Hierarchy | Viewport | Properties Inspector)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Stage Tree
        self.left_panel = self._build_left_panel()
        self.h_splitter.addWidget(self.left_panel)

        # Center Viewport & Bottom Console Splitter
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.addWidget(self.viewport)

        # Bottom Console
        self.bottom_panel = self._build_bottom_panel()
        self.v_splitter.addWidget(self.bottom_panel)
        self.v_splitter.setStretchFactor(0, 4)
        self.v_splitter.setStretchFactor(1, 1)

        self.h_splitter.addWidget(self.v_splitter)

        # Right Property Inspector
        self.right_panel = self._build_right_panel()
        self.h_splitter.addWidget(self.right_panel)

        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 4)
        self.h_splitter.setStretchFactor(2, 1)
        main_layout.addWidget(self.h_splitter)

        # 3. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Connecting to FARSverse Engine (127.0.0.1:8080)...")

        # 4. Start Background State Polling Thread
        self.poller = StatePollerThread(self)
        self.poller.state_received.connect(self.on_state_received)
        self.poller.connection_changed.connect(self.on_connection_changed)
        self.poller.start()

        # Current snapshot cache
        self.current_snapshot: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Toolbar Construction
    # ------------------------------------------------------------------
    def _build_toolbar(self):
        toolbar = QToolBar("Main Controls", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Brand Badge
        brand_label = QLabel("  Ω NVIDIA OMNIVERSE™ ")
        brand_label.setStyleSheet("color: #76b900; font-weight: bold; font-size: 12px;")
        toolbar.addWidget(brand_label)

        isaac_tag = QLabel("ISAAC SIM  ")
        isaac_tag.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        toolbar.addWidget(isaac_tag)

        toolbar.addSeparator()

        # Transport Controls
        btn_play = QPushButton(" ▶ PLAY ")
        btn_play.setStyleSheet("background-color: #1a3320; color: #76b900; border: 1px solid #76b900;")
        btn_play.clicked.connect(lambda: self.send_control("play"))
        toolbar.addWidget(btn_play)

        btn_pause = QPushButton(" ⏸ PAUSE ")
        btn_pause.clicked.connect(lambda: self.send_control("pause"))
        toolbar.addWidget(btn_pause)

        btn_stop = QPushButton(" ⏹ STOP ")
        btn_stop.clicked.connect(lambda: self.send_control("stop"))
        toolbar.addWidget(btn_stop)

        btn_step = QPushButton(" ⏯ STEP ")
        btn_step.clicked.connect(lambda: self.send_control("step", {"seconds": 0.5}))
        toolbar.addWidget(btn_step)

        btn_reset = QPushButton(" 🔄 RESET ")
        btn_reset.clicked.connect(lambda: self.send_control("reset"))
        toolbar.addWidget(btn_reset)

        toolbar.addSeparator()

        # Speed Selector
        speed_label = QLabel(" SPEED: ")
        speed_label.setStyleSheet("color: #64748b; font-size: 10px;")
        toolbar.addWidget(speed_label)

        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.5x", "1.0x", "2.0x", "4.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.currentTextChanged.connect(self.on_speed_changed)
        toolbar.addWidget(self.combo_speed)

        toolbar.addSeparator()

        # Clock
        self.clock_label = QLabel(" 00:00.0 ")
        self.clock_label.setStyleSheet("color: #76b900; font-weight: bold; font-size: 11px;")
        toolbar.addWidget(self.clock_label)

        toolbar.addSeparator()

        # Natural Language AI Command Bar (Ollama Integrated)
        cmd_label = QLabel(" AI COMMAND: ")
        cmd_label.setStyleSheet("color: #76b900; font-weight: bold; font-size: 10px;")
        toolbar.addWidget(cmd_label)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText('Ask: "Send robot 1 to Room 19", "Deliver meds to ICU1", "Pause simulation"...')
        self.cmd_input.setMinimumWidth(340)
        self.cmd_input.returnPressed.connect(self.on_command_execute)
        toolbar.addWidget(self.cmd_input)

        btn_exec = QPushButton(" EXECUTE (OLLAMA) ")
        btn_exec.setStyleSheet("background-color: #274015; color: #76b900; border: 1px solid #76b900; font-weight: bold;")
        btn_exec.clicked.connect(self.on_command_execute)
        toolbar.addWidget(btn_exec)

        toolbar.addSeparator()

        # Overlays
        chk_paths = QCheckBox(" Paths ")
        chk_paths.setChecked(True)
        chk_paths.toggled.connect(lambda v: setattr(self.viewport, 'show_paths', v))
        toolbar.addWidget(chk_paths)

        chk_grid = QCheckBox(" Grid ")
        chk_grid.setChecked(True)
        chk_grid.toggled.connect(lambda v: setattr(self.viewport, 'show_grid', v))
        toolbar.addWidget(chk_grid)

        chk_labels = QCheckBox(" Labels ")
        chk_labels.setChecked(True)
        chk_labels.toggled.connect(lambda v: setattr(self.viewport, 'show_labels', v))
        toolbar.addWidget(chk_labels)

        btn_fit = QPushButton(" ⛶ FIT ")
        btn_fit.clicked.connect(self.viewport.reset_view)
        toolbar.addWidget(btn_fit)

    # ------------------------------------------------------------------
    # Left Stage Hierarchy Panel
    # ------------------------------------------------------------------
    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("STAGE (USD HIERARCHY)")
        header.setStyleSheet("color: #76b900; font-weight: bold; font-size: 10px; padding: 4px;")
        layout.addWidget(header)

        self.stage_tree = QTreeWidget()
        self.stage_tree.setHeaderLabels(["Primitive", "Type"])
        self.stage_tree.itemClicked.connect(self.on_tree_item_clicked)
        layout.addWidget(self.stage_tree)

        return panel

    # ------------------------------------------------------------------
    # Right Property Inspector Panel
    # ------------------------------------------------------------------
    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel("USD PROPERTY INSPECTOR")
        header.setStyleSheet("color: #76b900; font-weight: bold; font-size: 10px; padding: 4px;")
        layout.addWidget(header)

        self.inspector_label = QLabel("No entity selected.\nClick on any robot, human, room, or obstacle in the viewport.")
        self.inspector_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.inspector_label.setWordWrap(True)
        layout.addWidget(self.inspector_label)

        # Quick Dispatch Form
        self.dispatch_group = QFrame()
        self.dispatch_group.setStyleSheet("background-color: #161a22; border: 1px solid #232834; border-radius: 4px; padding: 6px;")
        disp_layout = QVBoxLayout(self.dispatch_group)

        disp_title = QLabel("QUICK TASK DISPATCH")
        disp_title.setStyleSheet("color: #76b900; font-weight: bold; font-size: 10px;")
        disp_layout.addWidget(disp_title)

        self.combo_dest = QComboBox()
        self.combo_dest.addItems(["Room19", "Room1", "Pharmacy", "ICU1", "ICU2", "EmergencyRoom", "ChargingDock", "MainHall"])
        disp_layout.addWidget(self.combo_dest)

        btn_dispatch = QPushButton("Dispatch Selected AMR")
        btn_dispatch.setStyleSheet("background-color: #274015; color: #76b900; border: 1px solid #76b900;")
        btn_dispatch.clicked.connect(self.on_manual_dispatch)
        disp_layout.addWidget(btn_dispatch)

        layout.addWidget(self.dispatch_group)
        self.dispatch_group.setVisible(False)

        layout.addStretch()
        return panel

    # ------------------------------------------------------------------
    # Bottom Console & Logs Panel
    # ------------------------------------------------------------------
    def _build_bottom_panel(self) -> QWidget:
        panel = QTabWidget()

        # Tab 1: Active Tasks
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(["ID", "Task Type", "Destination", "Robot", "Status"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        panel.addTab(self.task_table, "Active Tasks")

        # Tab 2: System Event Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #11141a; color: #cbd5e1; font-size: 10px;")
        panel.addTab(self.log_text, "Event Log")

        return panel

    # ------------------------------------------------------------------
    # State Polling Handlers
    # ------------------------------------------------------------------
    def on_state_received(self, snapshot: Dict[str, Any]):
        self.current_snapshot = snapshot
        self.viewport.update_snapshot(snapshot)

        # Update Sim Clock
        sim_time = snapshot.get('sim_time', 0.0)
        mins = int(sim_time // 60)
        secs = sim_time % 60
        self.clock_label.setText(f" {mins:02d}:{secs:04.1f} ")

        # Update Active Tasks Table
        tasks_active = snapshot.get('tasks', {}).get('active', [])
        self.task_table.setRowCount(len(tasks_active))
        for row, t in enumerate(tasks_active):
            self.task_table.setItem(row, 0, QTableWidgetItem(f"#{t.get('id')}"))
            self.task_table.setItem(row, 1, QTableWidgetItem(str(t.get('task_type'))))
            self.task_table.setItem(row, 2, QTableWidgetItem(str(t.get('location_node'))))
            self.task_table.setItem(row, 3, QTableWidgetItem(str(t.get('assigned_robot', '-'))))
            self.task_table.setItem(row, 4, QTableWidgetItem(str(t.get('status'))))

        # Populate Stage Tree Once
        if self.stage_tree.topLevelItemCount() == 0 and snapshot.get('world'):
            self._populate_stage_tree(snapshot)

        # Update Inspector if entity is selected
        if self.viewport.selected_entity:
            etype, eid = self.viewport.selected_entity
            self._update_inspector(etype, eid)

    def on_connection_changed(self, connected: bool):
        if connected:
            self.status_bar.showMessage("NVIDIA Isaac Sim Live State: Connected to 127.0.0.1:8080 | Ollama RTX GPU Ready")
        else:
            self.status_bar.showMessage("Engine Disconnected. Reconnecting to 127.0.0.1:8080...")

    def _populate_stage_tree(self, snapshot: Dict[str, Any]):
        self.stage_tree.clear()
        root = QTreeWidgetItem(self.stage_tree, ["/World", "Xform"])
        root.setExpanded(True)

        # Environment
        env_node = QTreeWidgetItem(root, ["Environment", "Scope"])
        for rm in snapshot.get('world', {}).get('rooms', []):
            item = QTreeWidgetItem(env_node, [rm['id'], "Room"])
            item.setData(0, Qt.ItemDataRole.UserRole, ("room", rm['id']))
        env_node.setExpanded(True)

        # Robots
        robots_node = QTreeWidgetItem(root, ["Robots (Nova Carter AMRs)", "Scope"])
        for r in snapshot.get('robots', []):
            item = QTreeWidgetItem(robots_node, [r['id'], "AMR"])
            item.setData(0, Qt.ItemDataRole.UserRole, ("robot", r['id']))
        robots_node.setExpanded(True)

        # Humans
        humans_node = QTreeWidgetItem(root, ["Humans (Digital Twins)", "Scope"])
        for h in snapshot.get('humans', []):
            item = QTreeWidgetItem(humans_node, [h['name'], "Avatar"])
            item.setData(0, Qt.ItemDataRole.UserRole, ("human", h['id']))

    def on_tree_item_clicked(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            etype, eid = data
            self.viewport.selected_entity = (etype, eid)
            self._update_inspector(etype, eid)
            self.viewport.update()

    def on_entity_selected(self, etype: str, eid: str):
        self._update_inspector(etype, eid)

    def _update_inspector(self, etype: str, eid: str):
        if not etype or not eid:
            self.inspector_label.setText("No entity selected.\nClick on any robot, human, room, or obstacle in the viewport.")
            self.dispatch_group.setVisible(False)
            return

        if etype == "robot":
            robot = next((r for r in self.current_snapshot.get('robots', []) if r['id'] == eid), None)
            if robot:
                text = (
                    f"ENTITY: {robot['id']} ({robot['name']})\n"
                    f"TYPE: Nova Carter AMR\n"
                    f"STATE: {robot['state']}\n"
                    f"BATTERY: {robot['battery']:.1f}%\n"
                    f"SPEED: {robot['speed']} m/s\n"
                    f"POSITION: ({robot['x']:.2f}, {robot['z']:.2f})\n"
                    f"HEADING: {robot['rotation_y']:.1f}°\n"
                    f"CURRENT TASK: {robot.get('current_task') and robot['current_task'].get('description', 'Idle')}\n"
                    f"WAYPOINTS REMAINING: {len(robot.get('waypoints', [])) - robot.get('waypoint_index', 0)}"
                )
                self.inspector_label.setText(text)
                self.dispatch_group.setVisible(True)
        elif etype == "room":
            rm = next((r for r in self.current_snapshot.get('world', {}).get('rooms', []) if r['id'] == eid), None)
            if rm:
                text = (
                    f"ENTITY: {rm['id']} ({rm['name']})\n"
                    f"TYPE: {rm.get('type')}\n"
                    f"DIMENSIONS: {rm['width']}m x {rm['depth']}m\n"
                    f"CENTER: ({rm['x']}, {rm['z']})"
                )
                self.inspector_label.setText(text)
                self.dispatch_group.setVisible(False)
        elif etype == "human":
            h = next((hm for hm in self.current_snapshot.get('humans', []) if hm['id'] == eid), None)
            if h:
                text = (
                    f"ENTITY: {h['name']} [{h['id']}]\n"
                    f"ROLE: {h.get('agent_type')}\n"
                    f"STATUS: {h.get('status')}\n"
                    f"LOCATION: {h.get('current_node')}\n"
                    f"NEEDS ASSISTANCE: {h.get('needs_help')}"
                )
                self.inspector_label.setText(text)
                self.dispatch_group.setVisible(False)
        elif etype == "obstacle":
            obs = next((o for o in self.current_snapshot.get('world', {}).get('obstacles', []) if o['id'] == eid), None)
            if obs:
                text = (
                    f"OBSTACLE: {obs['name']} [{obs['id']}]\n"
                    f"STATUS: {'DEPLOYED (BLOCKED)' if obs.get('active') else 'CLEARED'}\n"
                    f"POSITION: ({obs['x']}, {obs['z']})"
                )
                self.inspector_label.setText(text)
                self.dispatch_group.setVisible(False)

    # ------------------------------------------------------------------
    # Controls & Command Execution
    # ------------------------------------------------------------------
    def send_control(self, action: str, extra: Optional[Dict[str, Any]] = None):
        payload = {"action": action}
        if extra:
            payload.update(extra)
        try:
            req = urllib.request.Request(
                f"{API_BASE}/api/farsverse/control",
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=1.0)
        except Exception as e:
            print("Control error:", e)

    def on_speed_changed(self, text: str):
        try:
            spd = float(text.replace('x', ''))
            self.send_control("set_speed", {"speed": spd})
        except ValueError:
            pass

    def on_command_execute(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self.cmd_input.setEnabled(False)
        self.status_bar.showMessage(f"Dispatching natural language command to local Ollama (phi3:mini)...")

        try:
            req = urllib.request.Request(
                f"{API_BASE}/api/farsverse/command",
                data=json.dumps({"text": cmd}).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5.0) as res:
                if res.status == 200:
                    resp = json.loads(res.read().decode('utf-8'))
                    msg = resp.get('message', f"Command processed by {resp.get('parsed_by')}")
                    self.status_bar.showMessage(f"Ollama Result: {msg}")
                    self.log_text.append(f"[{time.strftime('%H:%M:%S')}] CMD: '{cmd}' -> {msg}")
                    self.cmd_input.clear()
        except Exception as e:
            self.status_bar.showMessage(f"Command Error: {e}")
        finally:
            self.cmd_input.setEnabled(True)

    def on_manual_dispatch(self):
        if not self.viewport.selected_entity or self.viewport.selected_entity[0] != "robot":
            return
        dest = self.combo_dest.currentText()
        rid = self.viewport.selected_entity[1]
        cmd = f"Send {rid} to {dest}"
        self.cmd_input.setText(cmd)
        self.on_command_execute()

    def closeEvent(self, event):
        self.poller.stop()
        event.accept()


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------
def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = OmniverseMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
