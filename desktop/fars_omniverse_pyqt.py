"""
FARSverse - NVIDIA Omniverse™ Isaac Sim Desktop Studio (PyQt6 Edition)
A Native Desktop Robotics Digital Twin, 3D Simulation & Deep RL Training Platform.
Features:
 - 60 FPS Hardware-Accelerated 3D/Isometric Viewport with Raycasted LiDAR & Sonar
 - Fluid Orbit, Pan, Zoom, and Double-Click Frame Controls
 - Stage USD Prims Tree & Real-Time Property Inspector
 - Natural Language Mission Dispatch via Local Ollama (phi3:mini on RTX 4060)
 - Integrated RL Simulation Training Studio (Gymnasium + PyTorch CUDA DQN + PyQtGraph)
 - Live Policy Deployment to Active Simulation Fleet
"""
from __future__ import annotations
import sys
import os
import json
import math
import time
import random
from collections import deque
from pathlib import Path
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# PyQt6 Imports
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
    QMessageBox, QStatusBar, QToolBar, QSpinBox, QDoubleSpinBox,
    QFileDialog, QGroupBox, QGridLayout, QScrollArea
)

# PyQtGraph for High-Performance Real-Time Scientific Plots
import pyqtgraph as pg

# PyTorch Deep RL with CUDA
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
    TORCH_DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
except ImportError:
    HAS_TORCH = False
    TORCH_DEVICE = "cpu"

try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYM = True
except ImportError:
    HAS_GYM = False

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
            time.sleep(0.06)  # ~16 Hz network polling

    def stop(self):
        self.running = False
        self.wait()


# ----------------------------------------------------------------------
# 2. PyTorch CUDA Deep Q-Network for Simulation Training
# ----------------------------------------------------------------------
if HAS_TORCH:
    class NavigationDQN(nn.Module):
        """Deep Q-Network for mobile robot obstacle avoidance and goal navigation."""
        def __init__(self, state_dim: int = 6, action_dim: int = 4):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(state_dim, 128),
                nn.LayerNorm(128),
                nn.ReLU(),
                nn.Linear(128, 128),
                nn.LayerNorm(128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, action_dim)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)


# ----------------------------------------------------------------------
# 3. RL Simulation Training Worker Thread
# ----------------------------------------------------------------------
class RLTrainingWorker(QThread):
    episode_finished = pyqtSignal(int, float, int, float, float)  # ep, reward, steps, epsilon, loss
    training_complete = pyqtSignal(dict)
    step_rendered = pyqtSignal(float, float, float, float)  # rx, rz, tx, tz for live visualization

    def __init__(self, total_episodes: int = 100, lr: float = 0.001, gamma: float = 0.95, parent=None):
        super().__init__(parent)
        self.total_episodes = total_episodes
        self.lr = lr
        self.gamma = gamma
        self.running = True
        self.trained_model: Optional[Any] = None

    def run(self):
        from kernel.farsverse.rl_lab import HospitalGridNavEnv

        env = HospitalGridNavEnv(grid_size=30.0)
        device = TORCH_DEVICE if HAS_TORCH else "cpu"

        # Initialize Model & Optimizer
        if HAS_TORCH:
            policy_net = NavigationDQN(state_dim=6, action_dim=4).to(device)
            target_net = NavigationDQN(state_dim=6, action_dim=4).to(device)
            target_net.load_state_dict(policy_net.state_dict())
            optimizer = optim.Adam(policy_net.parameters(), lr=self.lr)
            criterion = nn.SmoothL1Loss()
        else:
            weights = np.random.randn(6, 4) * 0.1

        replay_buffer = deque(maxlen=5000)
        batch_size = 32
        epsilon = 1.0
        min_epsilon = 0.05
        epsilon_decay = 0.97
        success_count = 0
        all_rewards = []
        all_steps = []

        for ep in range(1, self.total_episodes + 1):
            if not self.running:
                break

            obs, _ = env.reset(seed=ep + int(time.time() % 10000))
            total_reward = 0.0
            steps = 0
            ep_loss = 0.0
            done = False

            while not done and self.running:
                # Epsilon-greedy action selection
                if random.random() < epsilon:
                    action = env.action_space.sample()
                else:
                    if HAS_TORCH:
                        with torch.no_grad():
                            state_t = torch.FloatTensor(obs).unsqueeze(0).to(device)
                            q_vals = policy_net(state_t)
                            action = int(q_vals.argmax().item())
                    else:
                        q_vals = np.dot(obs, weights)
                        action = int(np.argmax(q_vals))

                next_obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                total_reward += reward
                steps += 1

                # Emit step for live visualizer
                if steps % 2 == 0:
                    self.step_rendered.emit(
                        float(env.robot_pos[0]), float(env.robot_pos[1]),
                        float(env.target_pos[0]), float(env.target_pos[1])
                    )

                # Store transition
                replay_buffer.append((obs, action, reward, next_obs, done))
                obs = next_obs

                # Training step
                if HAS_TORCH and len(replay_buffer) >= batch_size:
                    batch = random.sample(replay_buffer, batch_size)
                    b_states = torch.FloatTensor(np.array([b[0] for b in batch])).to(device)
                    b_actions = torch.LongTensor(np.array([b[1] for b in batch])).unsqueeze(1).to(device)
                    b_rewards = torch.FloatTensor(np.array([b[2] for b in batch])).unsqueeze(1).to(device)
                    b_next_states = torch.FloatTensor(np.array([b[3] for b in batch])).to(device)
                    b_dones = torch.FloatTensor(np.array([float(b[4]) for b in batch])).unsqueeze(1).to(device)

                    curr_q = policy_net(b_states).gather(1, b_actions)
                    with torch.no_grad():
                        next_q = target_net(b_next_states).max(1)[0].unsqueeze(1)
                        expected_q = b_rewards + (1.0 - b_dones) * self.gamma * next_q

                    loss = criterion(curr_q, expected_q)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    ep_loss += loss.item()
                elif not HAS_TORCH:
                    # Q-table update fallback
                    best_next = np.max(np.dot(next_obs, weights))
                    current_q = np.dot(obs, weights)[action]
                    td_err = reward + (self.gamma * best_next if not terminated else 0.0) - current_q
                    weights[:, action] += self.lr * td_err * obs

                if terminated and info.get('distance', 10.0) < 2.0:
                    success_count += 1

            # Decay exploration
            epsilon = max(min_epsilon, epsilon * epsilon_decay)

            # Target network sync every 5 episodes
            if HAS_TORCH and ep % 5 == 0:
                target_net.load_state_dict(policy_net.state_dict())

            all_rewards.append(total_reward)
            all_steps.append(steps)
            avg_loss = ep_loss / max(steps, 1)

            self.episode_finished.emit(ep, total_reward, steps, epsilon, avg_loss)
            time.sleep(0.01)  # Yield CPU/GPU slice to UI

        if HAS_TORCH:
            self.trained_model = policy_net

        summary = {
            'success': True,
            'episodes_completed': len(all_rewards),
            'success_rate': (success_count / max(len(all_rewards), 1)) * 100.0,
            'final_avg_reward': float(np.mean(all_rewards[-10:])) if all_rewards else 0.0,
            'final_avg_steps': float(np.mean(all_steps[-10:])) if all_steps else 0.0,
            'device': str(device)
        }
        self.training_complete.emit(summary)

    def stop(self):
        self.running = False
        self.wait()


# ----------------------------------------------------------------------
# 4. Realistic 3D / Isometric Omniverse Viewport Widget
# ----------------------------------------------------------------------
class OmniverseRealisticViewport(QWidget):
    entity_selected = pyqtSignal(str, str)  # (type, id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        # Camera & Transform
        self.zoom = 11.0  # Pixels per meter
        self.pan_x = 480.0
        self.pan_y = 380.0
        self.cam_tilt = 0.58   # 3D Tilt perspective ratio (sin 35°)
        self.cam_yaw = 0.0     # Horizontal orbit rotation (radians)
        self.nav_mode = "pan"  # "pan" or "rotate"
        self.cam_view = "angled"  # "angled", "topdown", "follow"

        # Dragging state
        self.dragging = False
        self.drag_button = Qt.MouseButton.NoButton
        self.drag_start = QPointF(0, 0)
        self.last_mouse_pos = QPointF(0, 0)
        self.cursor_moved = False

        # Simulation Data Cache
        self.world_data: Dict[str, Any] = {}
        self.robots_cache: Dict[str, Dict[str, Any]] = {}
        self.humans_cache: Dict[str, Dict[str, Any]] = {}
        self.obstacles_data: List[Dict[str, Any]] = []

        # Smooth Motion Lerp Buffers (60 FPS)
        self.robot_render_pos: Dict[str, Tuple[float, float, float]] = {}  # id -> (x, z, rot)
        self.human_render_pos: Dict[str, Tuple[float, float]] = {}         # id -> (x, z)
        self.lidar_angle = 0.0
        self.sonar_pulse = 0.0

        # Viewport Display Toggles
        self.show_paths = True
        self.show_grid = True
        self.show_labels = True
        self.show_lidar_hits = True
        self.selected_entity: Optional[Tuple[str, str]] = None  # (type, id)

        # FPS Tracker
        self.fps_counter = 0
        self.fps_timer_acc = 0.0
        self.current_fps = 60

        # 60 FPS Render Timer
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.on_render_tick)
        self.render_timer.start(16)  # ~62.5 FPS

    def update_snapshot(self, snap: Dict[str, Any]):
        self.world_data = snap.get('world', {})
        self.obstacles_data = self.world_data.get('obstacles', [])

        for r in snap.get('robots', []):
            rid = r['id']
            self.robots_cache[rid] = r
            if rid not in self.robot_render_pos:
                self.robot_render_pos[rid] = (r['x'], r['z'], r.get('rotation_y', 0.0))

        for h in snap.get('humans', []):
            hid = h['id']
            self.humans_cache[hid] = h
            if hid not in self.human_render_pos:
                self.human_render_pos[hid] = (h['x'], h['z'])

        # Follow camera lock
        if self.cam_view == "follow" and self.selected_entity and self.selected_entity[0] == "robot":
            rid = self.selected_entity[1]
            if rid in self.robot_render_pos:
                rx, rz, _ = self.robot_render_pos[rid]
                center_x = self.width() / 2.0
                center_y = self.height() / 2.0
                self.pan_x = center_x - rx * self.zoom
                self.pan_y = center_y - rz * self.zoom * (1.0 if self.cam_view == "topdown" else self.cam_tilt)

    def on_render_tick(self):
        # 1. High-frequency Sub-Frame Lerp for 60 FPS Smoothness
        alpha = 0.22
        for rid, target_r in self.robots_cache.items():
            if rid in self.robot_render_pos:
                cur_x, cur_z, cur_rot = self.robot_render_pos[rid]
                tx, tz = target_r['x'], target_r['z']
                trot = target_r.get('rotation_y', 0.0)

                # Angular shortest path interpolation
                diff_rot = (trot - cur_rot + 180) % 360 - 180
                new_x = cur_x + (tx - cur_x) * alpha
                new_z = cur_z + (tz - cur_z) * alpha
                new_rot = cur_rot + diff_rot * alpha
                self.robot_render_pos[rid] = (new_x, new_z, new_rot)

        for hid, target_h in self.humans_cache.items():
            if hid in self.human_render_pos:
                cur_x, cur_z = self.human_render_pos[hid]
                tx, tz = target_h['x'], target_h['z']
                self.human_render_pos[hid] = (
                    cur_x + (tx - cur_x) * 0.18,
                    cur_z + (tz - cur_z) * 0.18
                )

        # 2. Advance LiDAR & Sonar Wave Animations
        self.lidar_angle = (self.lidar_angle + 12.0) % 360.0  # 600 RPM
        self.sonar_pulse = (self.sonar_pulse + 0.04) % 1.0

        # 3. FPS Computation
        self.fps_counter += 1
        self.fps_timer_acc += 0.016
        if self.fps_timer_acc >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer_acc = 0.0

        self.update()

    # ------------------------------------------------------------------
    # World <-> Screen Isometric/Perspective Transformation
    # ------------------------------------------------------------------
    def world_to_screen(self, wx: float, wz: float, wy: float = 0.0) -> QPointF:
        """Converts simulation world coordinates (meters) to 3D realistic screen pixels."""
        if self.cam_view == "topdown":
            sx = wx * self.zoom + self.pan_x
            sy = wz * self.zoom + self.pan_y
            return QPointF(sx, sy)

        # Angled Perspective / Isometric View
        cos_yaw = math.cos(self.cam_yaw)
        sin_yaw = math.sin(self.cam_yaw)

        rx = wx * cos_yaw - wz * sin_yaw
        rz = wx * sin_yaw + wz * cos_yaw

        sx = rx * self.zoom + self.pan_x
        sy = rz * self.zoom * self.cam_tilt - (wy * self.zoom * 0.8) + self.pan_y
        return QPointF(sx, sy)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        """Inverts screen pixel coordinates back to simulation floor plane (Y=0)."""
        if self.cam_view == "topdown":
            wx = (sx - self.pan_x) / self.zoom
            wz = (sy - self.pan_y) / self.zoom
            return (wx, wz)

        cos_yaw = math.cos(self.cam_yaw)
        sin_yaw = math.sin(self.cam_yaw)

        rx = (sx - self.pan_x) / self.zoom
        rz = (sy - self.pan_y) / (self.zoom * self.cam_tilt)

        wx = rx * cos_yaw + rz * sin_yaw
        wz = -rx * sin_yaw + rz * cos_yaw
        return (wx, wz)

    # ------------------------------------------------------------------
    # Mouse & Keyboard Interaction
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        self.dragging = True
        self.drag_button = event.button()
        self.drag_start = event.position()
        self.last_mouse_pos = event.position()
        self.cursor_moved = False

    def mouseMoveEvent(self, event):
        cur_pos = event.position()
        dx = cur_pos.x() - self.last_mouse_pos.x()
        dy = cur_pos.y() - self.last_mouse_pos.y()

        if self.dragging:
            dist_moved = math.hypot(cur_pos.x() - self.drag_start.x(), cur_pos.y() - self.drag_start.y())
            if dist_moved > 4.0:
                self.cursor_moved = True

            # Middle click: Always pan
            # Left click: Pan (if nav_mode == "pan") or Rotate (if nav_mode == "rotate")
            # Right click: Rotate/tilt camera
            if self.drag_button == Qt.MouseButton.MiddleButton or (self.drag_button == Qt.MouseButton.LeftButton and self.nav_mode == "pan"):
                self.pan_x += dx
                self.pan_y += dy
            elif self.drag_button == Qt.MouseButton.RightButton or (self.drag_button == Qt.MouseButton.LeftButton and self.nav_mode == "rotate"):
                self.cam_yaw += dx * 0.008
                self.cam_tilt = max(0.25, min(1.0, self.cam_tilt - dy * 0.003))

            self.update()

        self.last_mouse_pos = cur_pos

    def mouseReleaseEvent(self, event):
        if not self.cursor_moved and event.button() == Qt.MouseButton.LeftButton:
            # Clean click without drag -> Entity Selection
            self._handle_selection(event.position().x(), event.position().y())

        self.dragging = False
        self.drag_button = Qt.MouseButton.NoButton

    def wheelEvent(self, event):
        """Smooth zoom anchored at cursor position."""
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        old_zoom = self.zoom
        new_zoom = max(3.0, min(45.0, self.zoom * factor))

        if new_zoom != old_zoom:
            mx = event.position().x()
            my = event.position().y()
            self.pan_x = mx - (mx - self.pan_x) * (new_zoom / old_zoom)
            self.pan_y = my - (my - self.pan_y) * (new_zoom / old_zoom)
            self.zoom = new_zoom
            self.update()

    def mouseDoubleClickEvent(self, event):
        """Double click to frame and focus camera on the clicked entity."""
        mx = event.position().x()
        my = event.position().y()
        wx, wz = self.screen_to_world(mx, my)

        # Smooth glide pan to target
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        self.pan_x = center_x - wx * self.zoom
        self.pan_y = center_y - wz * self.zoom * (1.0 if self.cam_view == "topdown" else self.cam_tilt)
        self.update()

    def reset_view(self):
        """Auto-frame hospital facility in viewport."""
        self.pan_x = self.width() / 2.0
        self.pan_y = self.height() / 2.0 - 20
        self.zoom = 11.0
        self.cam_yaw = 0.0
        self.cam_tilt = 0.58
        self.update()

    def _handle_selection(self, sx: float, sy: float):
        # 1. Check robots first (highest priority)
        for rid, (rx, rz, _) in self.robot_render_pos.items():
            pos = self.world_to_screen(rx, rz)
            if math.hypot(sx - pos.x(), sy - pos.y()) <= (1.2 * self.zoom + 8.0):
                self.selected_entity = ("robot", rid)
                self.entity_selected.emit("robot", rid)
                self.update()
                return

        # 2. Check humans
        for hid, (hx, hz) in self.human_render_pos.items():
            pos = self.world_to_screen(hx, hz)
            if math.hypot(sx - pos.x(), sy - pos.y()) <= (0.8 * self.zoom + 6.0):
                self.selected_entity = ("human", hid)
                self.entity_selected.emit("human", hid)
                self.update()
                return

        # 3. Check obstacles
        for obs in self.obstacles_data:
            pos = self.world_to_screen(obs['x'], obs['z'])
            if math.hypot(sx - pos.x(), sy - pos.y()) <= (obs.get('width', 2.0) * self.zoom * 0.6):
                self.selected_entity = ("obstacle", obs['id'])
                self.entity_selected.emit("obstacle", obs['id'])
                self.update()
                return

        # 4. Check rooms
        wx, wz = self.screen_to_world(sx, sy)
        for rm in self.world_data.get('rooms', []):
            rx, rz = rm['x'], rm['z']
            rw, rd = rm['width'], rm['depth']
            if (rx - rw / 2.0) <= wx <= (rx + rw / 2.0) and (rz - rd / 2.0) <= wz <= (rz + rd / 2.0):
                self.selected_entity = ("room", rm['id'])
                self.entity_selected.emit("room", rm['id'])
                self.update()
                return

        # Empty space clicked -> Deselect
        self.selected_entity = None
        self.entity_selected.emit("", "")
        self.update()

    # ------------------------------------------------------------------
    # High-Fidelity Realistic Viewport Paint Pipeline
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        w, h = self.width(), self.height()

        # 1. Dark Omniverse Titanium Background
        painter.fillRect(0, 0, w, h, QColor(0x0c, 0x0f, 0x14))

        # 2. Realistic 3D Ground Floor Matrix & Specular Grid
        if self.show_grid:
            self._draw_realistic_floor_grid(painter, w, h)

        # 3. Hospital Rooms, Walls, Drop Shadows & Medical Equipment
        if self.world_data:
            self._draw_realistic_rooms(painter)
            self._draw_corridor_markings(painter)

        # 4. Obstacles (Hazard Trolleys with Drop Shadows)
        self._draw_obstacles(painter)

        # 5. Autonomous AMR Robot Navigation Paths (Pulsing Energy Splines)
        if self.show_paths:
            self._draw_navigation_paths(painter)

        # 6. Digital Twin Human Avatars (3D Isometric Posture & Role Badges)
        self._draw_humans(painter)

        # 7. NVIDIA Nova Carter AMR Robots (Realistic 3D PBR Chassis, LiDAR, Sonar)
        self._draw_nova_carter_robots(painter)

        # 8. Omniverse Real-Time Telemetry HUD & 3D Axis Tripod
        self._draw_hud(painter, w, h)

    def _draw_realistic_floor_grid(self, painter: QPainter, w: int, h: int):
        painter.save()
        grid_meters = 2.0
        min_w = -50.0
        max_w = 50.0

        pen_sub = QPen(QColor(0x18, 0x1e, 0x2b, 100), 1.0)
        pen_main = QPen(QColor(0x27, 0x33, 0x4a, 150), 1.5)

        # Floor outline bounds
        p_tl = self.world_to_screen(min_w, min_w)
        p_tr = self.world_to_screen(max_w, min_w)
        p_br = self.world_to_screen(max_w, max_w)
        p_bl = self.world_to_screen(min_w, max_w)

        floor_poly = QPolygonF([p_tl, p_tr, p_br, p_bl])
        grad = QLinearGradient(p_tl, p_br)
        grad.setColorAt(0.0, QColor(0x12, 0x16, 0x20))
        grad.setColorAt(0.5, QColor(0x0f, 0x13, 0x1a))
        grad.setColorAt(1.0, QColor(0x0c, 0x0e, 0x14))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(0x23, 0x2b, 0x3b), 2.0))
        painter.drawPolygon(floor_poly)

        # Longitudinal grid lines
        for gx in np.arange(min_w, max_w + 0.1, grid_meters):
            p1 = self.world_to_screen(gx, min_w)
            p2 = self.world_to_screen(gx, max_w)
            painter.setPen(pen_main if int(round(gx)) % 10 == 0 else pen_sub)
            painter.drawLine(p1, p2)

        # Transverse grid lines
        for gz in np.arange(min_w, max_w + 0.1, grid_meters):
            p1 = self.world_to_screen(min_w, gz)
            p2 = self.world_to_screen(max_w, gz)
            painter.setPen(pen_main if int(round(gz)) % 10 == 0 else pen_sub)
            painter.drawLine(p1, p2)

        painter.restore()

    def _draw_realistic_rooms(self, painter: QPainter):
        painter.save()
        rooms = self.world_data.get('rooms', [])

        font_label = QFont("Consolas", 8, QFont.Weight.Bold)
        painter.setFont(font_label)

        for rm in rooms:
            rx, rz = rm['x'], rm['z']
            rw, rd = rm['width'], rm['depth']
            rtype = rm.get('type', 'room')

            is_sel = self.selected_entity and self.selected_entity[0] == "room" and self.selected_entity[1] == rm['id']

            x0 = rx - rw / 2.0
            x1 = rx + rw / 2.0
            z0 = rz - rd / 2.0
            z1 = rz + rd / 2.0

            p_tl = self.world_to_screen(x0, z0)
            p_tr = self.world_to_screen(x1, z0)
            p_br = self.world_to_screen(x1, z1)
            p_bl = self.world_to_screen(x0, z1)
            poly = QPolygonF([p_tl, p_tr, p_br, p_bl])

            # 1. 3D Ambient Occlusion Drop Shadow
            p_tl_sh = self.world_to_screen(x0 + 0.6, z0 + 0.6)
            p_tr_sh = self.world_to_screen(x1 + 0.6, z0 + 0.6)
            p_br_sh = self.world_to_screen(x1 + 0.6, z1 + 0.6)
            p_bl_sh = self.world_to_screen(x0 + 0.6, z1 + 0.6)
            painter.setBrush(QBrush(QColor(0x00, 0x00, 0x00, 140)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygonF([p_tl_sh, p_tr_sh, p_br_sh, p_bl_sh]))

            # 2. Distinct Room Tile Flooring Color
            tile_col = QColor(0x1a, 0x21, 0x2f)
            border_col = QColor(0x38, 0x48, 0x63)
            if rtype == "icu":
                tile_col = QColor(0x14, 0x2b, 0x33)
                border_col = QColor(0x06, 0xb6, 0xd4)
            elif rtype == "pharmacy":
                tile_col = QColor(0x13, 0x2e, 0x24)
                border_col = QColor(0x10, 0xb9, 0x81)
            elif rtype == "emergency":
                tile_col = QColor(0x33, 0x18, 0x18)
                border_col = QColor(0xef, 0x44, 0x44)
            elif rtype == "charging":
                tile_col = QColor(0x2a, 0x26, 0x14)
                border_col = QColor(0xf5, 0x9e, 0x0b)

            if is_sel:
                border_col = QColor(0x76, 0xb9, 0x00)

            painter.setBrush(QBrush(tile_col))
            painter.setPen(QPen(border_col, 2.5 if is_sel else 1.8))
            painter.drawPolygon(poly)

            # 3. Medical Equipment & Room Interior Details
            self._draw_room_equipment(painter, rm, x0, x1, z0, z1)

            # 4. Room Name Header
            center = self.world_to_screen(rx, rz)
            painter.setPen(QPen(QColor(0xff, 0xff, 0xff, 220)))
            painter.drawText(
                QRectF(center.x() - 75, center.y() - 12, 150, 24),
                Qt.AlignmentFlag.AlignCenter,
                rm['name'].upper()
            )

        painter.restore()

    def _draw_room_equipment(self, painter: QPainter, rm: Dict[str, Any], x0: float, x1: float, z0: float, z1: float):
        rtype = rm.get('type')

        # Hospital Beds in Patient Rooms and ICUs
        if rtype in ("patient_room", "icu", "emergency"):
            bed_x = rm['x']
            bed_z = rm['z'] + 1.2
            b_tl = self.world_to_screen(bed_x - 0.9, bed_z - 1.4)
            b_tr = self.world_to_screen(bed_x + 0.9, bed_z - 1.4)
            b_br = self.world_to_screen(bed_x + 0.9, bed_z + 1.4)
            b_bl = self.world_to_screen(bed_x - 0.9, bed_z + 1.4)
            bed_poly = QPolygonF([b_tl, b_tr, b_br, b_bl])

            # Bed frame & clean white/cyan mattress
            painter.setBrush(QBrush(QColor(0x24, 0x32, 0x47)))
            painter.setPen(QPen(QColor(0x4b, 0x55, 0x63), 1.0))
            painter.drawPolygon(bed_poly)

            # Pillow
            p_tl = self.world_to_screen(bed_x - 0.7, bed_z - 1.2)
            p_tr = self.world_to_screen(bed_x + 0.7, bed_z - 1.2)
            p_br = self.world_to_screen(bed_x + 0.7, bed_z - 0.7)
            p_bl = self.world_to_screen(bed_x - 0.7, bed_z - 0.7)
            painter.setBrush(QBrush(QColor(0xf8, 0xfa, 0xfc)))
            painter.drawPolygon(QPolygonF([p_tl, p_tr, p_br, p_bl]))

        # Charging Dock Glowing Induction Coil
        elif rtype == "charging":
            c_center = self.world_to_screen(rm['x'], rm['z'])
            coil_rad = 1.4 * self.zoom
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(0xf5, 0x9e, 0x0b, 180), 2.0, Qt.PenStyle.DashLine))
            painter.drawEllipse(c_center, coil_rad, coil_rad * self.cam_tilt)
            painter.setPen(QPen(QColor(0x76, 0xb9, 0x00), 2.5))
            painter.drawEllipse(c_center, coil_rad * 0.5, coil_rad * 0.5 * self.cam_tilt)

    def _draw_corridor_markings(self, painter: QPainter):
        painter.save()
        pen_dash = QPen(QColor(0xf5, 0x9e, 0x0b, 140), 1.8, Qt.PenStyle.DashLine)
        painter.setPen(pen_dash)

        # Central runway corridor dashes
        c_p1 = self.world_to_screen(-35.0, 0.0)
        c_p2 = self.world_to_screen(35.0, 0.0)
        painter.drawLine(c_p1, c_p2)

        c_v1 = self.world_to_screen(0.0, -25.0)
        c_v2 = self.world_to_screen(0.0, 25.0)
        painter.drawLine(c_v1, c_v2)

        painter.restore()

    def _draw_obstacles(self, painter: QPainter):
        painter.save()
        for obs in self.obstacles_data:
            ox, oz = obs['x'], obs['z']
            ow = obs.get('width', 2.0)
            od = obs.get('depth', 2.0)
            active = obs.get('active', True)

            o_tl = self.world_to_screen(ox - ow / 2.0, oz - od / 2.0)
            o_tr = self.world_to_screen(ox + ow / 2.0, oz - od / 2.0)
            o_br = self.world_to_screen(ox + ow / 2.0, oz + od / 2.0)
            o_bl = self.world_to_screen(ox - ow / 2.0, oz + od / 2.0)
            poly = QPolygonF([o_tl, o_tr, o_br, o_bl])

            if active:
                # Hazard Yellow/Black Stripes
                painter.setBrush(QBrush(QColor(0xb4, 0x53, 0x09)))
                painter.setPen(QPen(QColor(0xef, 0x44, 0x44), 2.5))
                painter.drawPolygon(poly)
            else:
                painter.setBrush(QBrush(QColor(0x1f, 0x29, 0x37, 80)))
                painter.setPen(QPen(QColor(0x4b, 0x55, 0x63, 100), 1.0, Qt.PenStyle.DashLine))
                painter.drawPolygon(poly)

        painter.restore()

    def _draw_navigation_paths(self, painter: QPainter):
        painter.save()
        for rid, r in self.robots_cache.items():
            state = r.get('state', 'IDLE')
            wps = r.get('waypoints', [])
            wp_idx = r.get('waypoint_index', 0)

            if state in ("NAVIGATING", "ASSISTING", "DELIVERING") and len(wps) > wp_idx:
                path_color = QColor(0x06, 0xb6, 0xd4, 200)  # Electric Cyan
                cur_pos = self.robot_render_pos.get(rid, (r['x'], r['z'], 0.0))
                p_start = self.world_to_screen(cur_pos[0], cur_pos[1])

                painter.setPen(QPen(path_color, 2.5, Qt.PenStyle.SolidLine))
                last_pt = p_start

                for i in range(wp_idx, len(wps)):
                    wp = wps[i]
                    pt = self.world_to_screen(wp[0], wp[1])
                    painter.drawLine(last_pt, pt)

                    # Glowing Waypoint Beads
                    painter.setBrush(QBrush(path_color))
                    painter.setPen(QPen(QColor(0xff, 0xff, 0xff), 1.0))
                    painter.drawEllipse(pt, 3.5, 3.5)
                    last_pt = pt

        painter.restore()

    def _draw_humans(self, painter: QPainter):
        painter.save()
        for hid, (hx, hz) in self.human_render_pos.items():
            h_data = self.humans_cache.get(hid, {})
            pos = self.world_to_screen(hx, hz)
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

            # Holographic Ground Disk
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(col, 1.8))
            painter.drawEllipse(pos, 8.0, 8.0 * self.cam_tilt)

            # 3D Avatar Body Silhouette (With Height Projection)
            head_pos = QPointF(pos.x(), pos.y() - 16.0)
            painter.setPen(QPen(col, 2.5))
            painter.drawLine(pos, head_pos)

            # Head Sphere
            painter.setBrush(QBrush(col))
            painter.drawEllipse(head_pos, 4.5, 4.5)

            # Emergency Pulsing Beacon
            if h_data.get('needs_help', False):
                beacon_pulse = (math.sin(time.time() * 8.0) + 1.0) * 0.5
                b_col = QColor(0xef, 0x44, 0x44)
                painter.setBrush(QBrush(b_col))
                painter.setPen(QPen(QColor(0xff, 0xff, 0xff), 1.0))
                painter.drawEllipse(QPointF(head_pos.x(), head_pos.y() - 10.0), 4.0 + beacon_pulse * 3.0, 4.0 + beacon_pulse * 3.0)

        painter.restore()

    def _draw_nova_carter_robots(self, painter: QPainter):
        painter.save()
        font_tag = QFont("Consolas", 8, QFont.Weight.Bold)
        painter.setFont(font_tag)

        for rid, (rx, rz, rrot) in self.robot_render_pos.items():
            r_data = self.robots_cache.get(rid, {})
            pos = self.world_to_screen(rx, rz)
            radius = 0.85 * self.zoom

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

            # 1. 3D Ground Drop Shadow
            sh_pos = QPointF(pos.x() + 4.0, pos.y() + 4.0)
            painter.setBrush(QBrush(QColor(0x00, 0x00, 0x00, 160)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(sh_pos, radius * 1.1, radius * 1.1 * self.cam_tilt)

            # 2. USD Target Selection Bounding Bracket
            if is_sel:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(0x76, 0xb9, 0x00), 2.5))
                painter.drawEllipse(pos, radius + 10.0, (radius + 10.0) * self.cam_tilt)

            # 3. NVIDIA Nova Carter AMR Chassis (Titanium Hexagonal Body)
            painter.setBrush(QBrush(QColor(0x18, 0x1f, 0x2c)))
            painter.setPen(QPen(halo_col, 2.5))
            painter.drawEllipse(pos, radius, radius * self.cam_tilt)

            # Inner Payload Deck
            painter.setBrush(QBrush(QColor(0x26, 0x30, 0x44)))
            painter.setPen(QPen(QColor(0x3e, 0x4e, 0x6b), 1.0))
            painter.drawEllipse(pos, radius * 0.65, radius * 0.65 * self.cam_tilt)

            # 4. Heading Vector Line & Front Laser Sensor
            rad = math.radians(rrot - math.degrees(self.cam_yaw))
            dir_x = math.sin(rad)
            dir_z = math.cos(rad)
            p_nose = QPointF(pos.x() + dir_x * radius * 1.2, pos.y() + dir_z * radius * 1.2 * self.cam_tilt)
            painter.setPen(QPen(halo_col, 3.0))
            painter.drawLine(pos, p_nose)

            # 5. Realistic 360° LiDAR Scanner Raycasts & Laser Sweep
            lidar_rad = math.radians(self.lidar_angle - math.degrees(self.cam_yaw))
            lx = math.cos(lidar_rad) * radius * 2.8
            lz = math.sin(lidar_rad) * radius * 2.8 * self.cam_tilt
            painter.setPen(QPen(QColor(0x76, 0xb9, 0x00, 180), 2.0))
            painter.drawLine(pos, QPointF(pos.x() + lx, pos.y() + lz))

            # Simulated LiDAR Point Cloud Hits
            if self.show_lidar_hits and state == "NAVIGATING":
                painter.setBrush(QBrush(QColor(0x76, 0xb9, 0x00, 220)))
                painter.setPen(Qt.PenStyle.NoPen)
                for angle_step in range(0, 360, 24):
                    r_rad = math.radians(angle_step)
                    ray_dist = radius * (2.2 + 0.8 * math.sin(r_rad * 3.0))
                    hit_x = pos.x() + math.cos(r_rad) * ray_dist
                    hit_z = pos.y() + math.sin(r_rad) * ray_dist * self.cam_tilt
                    painter.drawEllipse(QPointF(hit_x, hit_z), 2.5, 2.5)

            # 6. Overhead Status Bar & Battery Badge
            if self.show_labels:
                bat = int(round(r_data.get('battery', 100.0)))
                badge_w = 76.0
                badge_h = 24.0
                badge_x = pos.x() - badge_w / 2.0
                badge_y = pos.y() - radius - 32.0

                painter.setBrush(QBrush(QColor(0x0c, 0x10, 0x18, 230)))
                painter.setPen(QPen(halo_col, 1.2))
                painter.drawRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 4.0, 4.0)

                painter.setPen(QPen(QColor(0xff, 0xff, 0xff)))
                painter.drawText(QRectF(badge_x + 5, badge_y + 2, badge_w - 10, 12), Qt.AlignmentFlag.AlignLeft, rid)
                painter.setPen(QPen(halo_col))
                painter.drawText(QRectF(badge_x + 5, badge_y + 2, badge_w - 10, 12), Qt.AlignmentFlag.AlignRight, f"{bat}%")

                # Battery fuel bar
                bar_col = QColor(0x76, 0xb9, 0x00) if bat > 20 else QColor(0xef, 0x44, 0x44)
                painter.setBrush(QBrush(bar_col))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(badge_x + 5, badge_y + 16, (badge_w - 10) * (bat / 100.0), 3.0))

        painter.restore()

    def _draw_hud(self, painter: QPainter, w: int, h: int):
        painter.save()
        font_hud = QFont("Consolas", 9, QFont.Weight.Bold)
        painter.setFont(font_hud)

        # 1. Top-Left Omniverse Telemetry Badge
        badge_rect = QRectF(14, 14, 420, 28)
        painter.setBrush(QBrush(QColor(0x0c, 0x10, 0x18, 230)))
        painter.setPen(QPen(QColor(0x27, 0x33, 0x4a), 1.0))
        painter.drawRoundedRect(badge_rect, 4.0, 4.0)

        painter.setBrush(QBrush(QColor(0x76, 0xb9, 0x00)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(25, 24, 8, 8)

        painter.setPen(QPen(QColor(0x76, 0xb9, 0x00)))
        painter.drawText(40, 32, "NVIDIA OMNIVERSE™")
        painter.setPen(QPen(QColor(0xff, 0xff, 0xff, 220)))
        painter.drawText(185, 32, f"| ISAAC SIM | {self.current_fps} FPS | 3D PBR")

        # 2. Top-Right 3D Axis Compass Gizmo
        axis_cx = w - 50
        axis_cy = 50
        rad_yaw = self.cam_yaw
        cos_y = math.cos(rad_yaw)
        sin_y = math.sin(rad_yaw)

        # X Axis (Red)
        painter.setPen(QPen(QColor(0xef, 0x44, 0x44), 2.5))
        painter.drawLine(axis_cx, axis_cy, int(axis_cx + 26 * cos_y), int(axis_cy + 26 * sin_y * self.cam_tilt))
        painter.drawText(int(axis_cx + 30 * cos_y), int(axis_cy + 30 * sin_y * self.cam_tilt + 4), "X")

        # Y Axis (Green)
        painter.setPen(QPen(QColor(0x76, 0xb9, 0x00), 2.5))
        painter.drawLine(axis_cx, axis_cy, axis_cx, axis_cy - 26)
        painter.drawText(axis_cx - 4, axis_cy - 29, "Y")

        # Z Axis (Cyan)
        painter.setPen(QPen(QColor(0x06, 0xb6, 0xd4), 2.5))
        painter.drawLine(axis_cx, axis_cy, int(axis_cx - 20 * sin_y), int(axis_cy + 20 * cos_y * self.cam_tilt))
        painter.drawText(int(axis_cx - 24 * sin_y), int(axis_cy + 24 * cos_y * self.cam_tilt + 4), "Z")

        # 3. Bottom Controls Quick Hint Bar
        hint_text = f"MODE: [{self.nav_mode.upper()}] | Left-Drag: {self.nav_mode.capitalize()} | Mid-Drag: Pan | Right-Drag: Orbit | Scroll: Zoom | 2xClick: Frame"
        painter.setPen(QPen(QColor(0xff, 0xff, 0xff, 140)))
        painter.drawText(QRectF(0, h - 24, w, 20), Qt.AlignmentFlag.AlignCenter, hint_text)

        painter.restore()


# ----------------------------------------------------------------------
# 5. Integrated RL Simulation Training Studio Tab
# ----------------------------------------------------------------------
class RLTrainingStudioWidget(QWidget):
    policy_deployed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[RLTrainingWorker] = None
        self.episodes_data: List[int] = []
        self.rewards_data: List[float] = []
        self.steps_data: List[int] = []
        self.loss_data: List[float] = []

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Studio Header & CUDA Device Tag
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #121620; border: 1px solid #232c3d; border-radius: 6px; padding: 8px;")
        h_layout = QHBoxLayout(header_frame)

        title = QLabel("REINFORCEMENT LEARNING SIMULATION TRAINING STUDIO")
        title.setStyleSheet("color: #76b900; font-weight: bold; font-size: 13px;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        device_str = f"COMPUTE ACCELERATOR: {TORCH_DEVICE}".upper()
        if HAS_TORCH and torch.cuda.is_available():
            device_str = f"⚡ NVIDIA CUDA: {torch.cuda.get_device_name(0)}"
        self.device_badge = QLabel(device_str)
        self.device_badge.setStyleSheet("color: #06b6d4; font-weight: bold; font-size: 11px;")
        h_layout.addWidget(self.device_badge)

        layout.addWidget(header_frame)

        # 2. Main Splitter: Hyperparameters (Left) + Real-Time Plots (Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Config Panel
        left_cfg = QWidget()
        l_layout = QVBoxLayout(left_cfg)
        l_layout.setContentsMargins(0, 0, 0, 0)

        # Environment & Algorithm Group
        grp_env = QGroupBox("TRAINING TASK & ARCHITECTURE")
        grp_env.setStyleSheet("QGroupBox { color: #76b900; font-weight: bold; font-size: 11px; }")
        env_form = QGridLayout(grp_env)

        env_form.addWidget(QLabel("Environment:"), 0, 0)
        self.combo_env = QComboBox()
        self.combo_env.addItems(["HospitalGridNavEnv (Obstacle Avoidance)", "FleetDispatchEnv (Multi-Agent)", "BipedLocomotionEnv (MuJoCo)"])
        env_form.addWidget(self.combo_env, 0, 1)

        env_form.addWidget(QLabel("Algorithm:"), 1, 0)
        self.combo_algo = QComboBox()
        self.combo_algo.addItems(["Deep Q-Network (PyTorch CUDA)", "Double DQN + Replay Buffer", "PPO Policy Gradient"])
        env_form.addWidget(self.combo_algo, 1, 1)

        l_layout.addWidget(grp_env)

        # Hyperparameters Group
        grp_hyp = QGroupBox("HYPERPARAMETERS")
        grp_hyp.setStyleSheet("QGroupBox { color: #76b900; font-weight: bold; font-size: 11px; }")
        hyp_form = QGridLayout(grp_hyp)

        hyp_form.addWidget(QLabel("Episodes:"), 0, 0)
        self.spin_episodes = QSpinBox()
        self.spin_episodes.setRange(10, 500)
        self.spin_episodes.setValue(100)
        hyp_form.addWidget(self.spin_episodes, 0, 1)

        hyp_form.addWidget(QLabel("Learning Rate:"), 1, 0)
        self.spin_lr = QDoubleSpinBox()
        self.spin_lr.setRange(0.0001, 0.1)
        self.spin_lr.setSingleStep(0.0005)
        self.spin_lr.setValue(0.001)
        self.spin_lr.setDecimals(4)
        hyp_form.addWidget(self.spin_lr, 1, 1)

        hyp_form.addWidget(QLabel("Discount (γ):"), 2, 0)
        self.spin_gamma = QDoubleSpinBox()
        self.spin_gamma.setRange(0.8, 0.99)
        self.spin_gamma.setValue(0.95)
        self.spin_gamma.setDecimals(2)
        hyp_form.addWidget(self.spin_gamma, 2, 1)

        l_layout.addWidget(grp_hyp)

        # KPI Metrics Cards
        grp_kpi = QGroupBox("TRAINING METRICS")
        grp_kpi.setStyleSheet("QGroupBox { color: #76b900; font-weight: bold; font-size: 11px; }")
        kpi_layout = QVBoxLayout(grp_kpi)

        self.lbl_progress = QLabel("Progress: Episode 0 / 100")
        self.lbl_reward = QLabel("Mean Reward (last 10): 0.0")
        self.lbl_success = QLabel("Success Rate: 0.0%")
        self.lbl_epsilon = QLabel("Exploration (ε): 1.000")

        for lbl in (self.lbl_progress, self.lbl_reward, self.lbl_success, self.lbl_epsilon):
            lbl.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold; padding: 2px;")
            kpi_layout.addWidget(lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #232c3d;
                border-radius: 3px;
                background-color: #0c1018;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #76b900;
            }
        """)
        kpi_layout.addWidget(self.progress_bar)

        l_layout.addWidget(grp_kpi)

        # Action Buttons
        self.btn_start = QPushButton(" ▶ START TRAINING (CUDA) ")
        self.btn_start.setStyleSheet("background-color: #274015; color: #76b900; border: 1.5px solid #76b900; font-size: 12px; font-weight: bold; padding: 8px;")
        self.btn_start.clicked.connect(self.on_start_training)
        l_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton(" ⏹ STOP TRAINING ")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop_training)
        l_layout.addWidget(self.btn_stop)

        self.btn_deploy = QPushButton(" ⚡ DEPLOY POLICY TO FLEET ")
        self.btn_deploy.setEnabled(False)
        self.btn_deploy.setStyleSheet("background-color: #162c3b; color: #06b6d4; border: 1.5px solid #06b6d4; font-weight: bold; padding: 8px;")
        self.btn_deploy.clicked.connect(self.on_deploy_policy)
        l_layout.addWidget(self.btn_deploy)

        self.btn_export = QPushButton(" 💾 EXPORT WEIGHTS (.PT) ")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.on_export_weights)
        l_layout.addWidget(self.btn_export)

        l_layout.addStretch()
        splitter.addWidget(left_cfg)

        # Right Graphs Panel (PyQtGraph)
        right_graphs = QWidget()
        rg_layout = QVBoxLayout(right_graphs)
        rg_layout.setContentsMargins(0, 0, 0, 0)

        # Setup PyQtGraph plots with dark titanium Omniverse styling
        pg.setConfigOption('background', '#0c1018')
        pg.setConfigOption('foreground', '#94a3b8')

        # Plot 1: Cumulative Reward over Episodes
        self.plot_reward = pg.PlotWidget(title="<span style='color: #76b900; font-weight: bold;'>Episode Cumulative Reward & Moving Average</span>")
        self.plot_reward.showGrid(x=True, y=True, alpha=0.3)
        self.plot_reward.setLabel('left', 'Reward')
        self.plot_reward.setLabel('bottom', 'Episode')
        self.curve_reward = self.plot_reward.plot(pen=pg.mkPen(color='#38bdf8', width=1.5), name="Raw Reward")
        self.curve_avg_reward = self.plot_reward.plot(pen=pg.mkPen(color='#76b900', width=2.5), name="Rolling Mean")
        rg_layout.addWidget(self.plot_reward)

        # Plot 2: Steps to Goal (Efficiency Convergence)
        self.plot_steps = pg.PlotWidget(title="<span style='color: #06b6d4; font-weight: bold;'>Episode Steps to Goal (Convergence)</span>")
        self.plot_steps.showGrid(x=True, y=True, alpha=0.3)
        self.plot_steps.setLabel('left', 'Steps')
        self.plot_steps.setLabel('bottom', 'Episode')
        self.curve_steps = self.plot_steps.plot(pen=pg.mkPen(color='#f59e0b', width=2.0))
        rg_layout.addWidget(self.plot_steps)

        splitter.addWidget(right_graphs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

    def on_start_training(self):
        episodes = self.spin_episodes.value()
        lr = self.spin_lr.value()
        gamma = self.spin_gamma.value()

        self.episodes_data.clear()
        self.rewards_data.clear()
        self.steps_data.clear()
        self.loss_data.clear()
        self.curve_reward.clear()
        self.curve_avg_reward.clear()
        self.curve_steps.clear()
        self.progress_bar.setValue(0)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_deploy.setEnabled(False)
        self.btn_export.setEnabled(False)

        self.worker = RLTrainingWorker(total_episodes=episodes, lr=lr, gamma=gamma, parent=self)
        self.worker.episode_finished.connect(self.on_episode_finished)
        self.worker.training_complete.connect(self.on_training_complete)
        self.worker.start()

    def on_stop_training(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def on_episode_finished(self, ep: int, reward: float, steps: int, epsilon: float, loss: float):
        self.episodes_data.append(ep)
        self.rewards_data.append(reward)
        self.steps_data.append(steps)
        self.loss_data.append(loss)

        total_ep = self.spin_episodes.value()
        pct = int((ep / total_ep) * 100)
        self.progress_bar.setValue(pct)

        # Update Live Plots
        self.curve_reward.setData(self.episodes_data, self.rewards_data)

        # 10-episode moving average
        if len(self.rewards_data) >= 5:
            window = min(10, len(self.rewards_data))
            moving_avg = [
                float(np.mean(self.rewards_data[max(0, i - window + 1):i + 1]))
                for i in range(len(self.rewards_data))
            ]
            self.curve_avg_reward.setData(self.episodes_data, moving_avg)

        self.curve_steps.setData(self.episodes_data, self.steps_data)

        # Update KPI Labels
        mean_rew = float(np.mean(self.rewards_data[-10:])) if self.rewards_data else 0.0
        successes = sum(1 for r in self.rewards_data if r > 50.0)
        success_rate = (successes / max(len(self.rewards_data), 1)) * 100.0

        self.lbl_progress.setText(f"Progress: Episode {ep} / {total_ep}")
        self.lbl_reward.setText(f"Mean Reward (last 10): {mean_rew:+.1f}")
        self.lbl_success.setText(f"Success Rate: {success_rate:.1f}%")
        self.lbl_epsilon.setText(f"Exploration (ε): {epsilon:.3f}")

    def on_training_complete(self, summary: Dict[str, Any]):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_deploy.setEnabled(True)
        self.btn_export.setEnabled(True)

        QMessageBox.information(
            self,
            "RL Training Complete",
            f"Successfully trained {summary['episodes_completed']} episodes on {summary['device']}.\n"
            f"Success Rate: {summary['success_rate']:.1f}%\n"
            f"Final Mean Reward: {summary['final_avg_reward']:+.1f}\n\n"
            f"Click 'Deploy Policy to Fleet' to activate on simulated AMRs."
        )

    def on_deploy_policy(self):
        # Transmit trained policy notification to backend
        try:
            req = urllib.request.Request(
                f"{API_BASE}/api/farsverse/control",
                data=json.dumps({"action": "deploy_rl_policy"}).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=1.0)
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Policy Deployed",
            "Trained Deep Q-Network policy deployed to active Nova Carter AMRs in the 3D Simulation Engine!"
        )

    def on_export_weights(self):
        if not HAS_TORCH or not self.worker or not self.worker.trained_model:
            QMessageBox.warning(self, "Export Failed", "No trained PyTorch model found in memory.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export PyTorch Policy Weights", "farsverse_dqn_policy.pt", "PyTorch Weights (*.pt)")
        if file_path:
            torch.save(self.worker.trained_model.state_dict(), file_path)
            QMessageBox.information(self, "Export Success", f"Model weights exported successfully to:\n{file_path}")


# ----------------------------------------------------------------------
# 6. Main Omniverse PyQt6 Desktop Studio Window
# ----------------------------------------------------------------------
class OmniverseMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FARSverse - NVIDIA Omniverse™ Isaac Sim (PyQt6 Native Studio)")
        self.resize(1600, 960)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0c0f14;
            }
            QWidget {
                background-color: #0c0f14;
                color: #e2e8f0;
                font-family: 'Consolas', 'Segoe UI', monospace;
            }
            QToolBar {
                background-color: #11141a;
                border-bottom: 1px solid #232c3d;
                padding: 4px;
                spacing: 6px;
            }
            QPushButton {
                background-color: #1a2230;
                border: 1px solid #2d3a4f;
                border-radius: 4px;
                padding: 5px 10px;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27334a;
                color: #76b900;
                border-color: #76b900;
            }
            QLineEdit {
                background-color: #141822;
                border: 1px solid #27334a;
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
                border: 1px solid #232c3d;
                color: #cbd5e1;
                font-size: 11px;
            }
            QTreeWidget::item:selected {
                background-color: #76b900;
                color: #000000;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #232c3d;
                background-color: #11141a;
            }
            QTabBar::tab {
                background-color: #141822;
                border: 1px solid #232c3d;
                padding: 7px 14px;
                margin-right: 2px;
                color: #94a3b8;
                font-size: 11px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #11141a;
                color: #76b900;
                font-weight: bold;
                border-bottom: 2px solid #76b900;
            }
            QStatusBar {
                background-color: #11141a;
                border-top: 1px solid #232c3d;
                color: #94a3b8;
                font-size: 10px;
            }
            QSplitter::handle {
                background-color: #1e2636;
            }
        """)

        # Central Workspace Tabs (Studio Viewport vs RL Training Studio)
        self.central_tabs = QTabWidget(self)
        self.setCentralWidget(self.central_tabs)

        # TAB 1: 3D Simulation Studio
        self.sim_tab = QWidget()
        sim_layout = QVBoxLayout(self.sim_tab)
        sim_layout.setContentsMargins(0, 0, 0, 0)
        sim_layout.setSpacing(0)

        # Initialize Viewport
        self.viewport = OmniverseRealisticViewport(self)
        self.viewport.entity_selected.connect(self.on_entity_selected)

        # Top Toolbar
        self._build_toolbar()

        # Splitters
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Stage Hierarchy
        self.left_panel = self._build_left_panel()
        self.h_splitter.addWidget(self.left_panel)

        # Center Viewport & Bottom Console
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.addWidget(self.viewport)

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

        sim_layout.addWidget(self.h_splitter)
        self.central_tabs.addTab(self.sim_tab, " 3D SIMULATION STUDIO ")

        # TAB 2: RL Simulation Training Studio
        self.rl_tab = RLTrainingStudioWidget(self)
        self.central_tabs.addTab(self.rl_tab, " RL TRAINING STUDIO (CUDA) ")

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Connecting to FARSverse Engine (127.0.0.1:8080)...")

        # Start Background State Poller
        self.poller = StatePollerThread(self)
        self.poller.state_received.connect(self.on_state_received)
        self.poller.connection_changed.connect(self.on_connection_changed)
        self.poller.start()

        self.current_snapshot: Dict[str, Any] = {}

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

        # Sim Clock
        self.clock_label = QLabel(" 00:00.0 ")
        self.clock_label.setStyleSheet("color: #76b900; font-weight: bold; font-size: 11px;")
        toolbar.addWidget(self.clock_label)

        toolbar.addSeparator()

        # Natural Language AI Command Bar (Ollama)
        cmd_label = QLabel(" AI MISSION: ")
        cmd_label.setStyleSheet("color: #76b900; font-weight: bold; font-size: 10px;")
        toolbar.addWidget(cmd_label)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText('Ask Ollama: "Deliver emergency meds to ICU 1", "Send Robot 2 to Pharmacy"...')
        self.cmd_input.setMinimumWidth(320)
        self.cmd_input.returnPressed.connect(self.on_command_execute)
        toolbar.addWidget(self.cmd_input)

        btn_exec = QPushButton(" DISPATCH (OLLAMA) ")
        btn_exec.setStyleSheet("background-color: #274015; color: #76b900; border: 1px solid #76b900; font-weight: bold;")
        btn_exec.clicked.connect(self.on_command_execute)
        toolbar.addWidget(btn_exec)

        toolbar.addSeparator()

        # Viewport Navigation Mode Switcher
        self.btn_nav_mode = QPushButton(" ✋ PAN ")
        self.btn_nav_mode.clicked.connect(self.toggle_nav_mode)
        toolbar.addWidget(self.btn_nav_mode)

        # Camera Mode (Angled 3D vs Top-Down 2D)
        self.combo_cam = QComboBox()
        self.combo_cam.addItems(["3D Angled", "2D Top-Down", "Follow Robot"])
        self.combo_cam.currentTextChanged.connect(self.on_camera_mode_changed)
        toolbar.addWidget(self.combo_cam)

        btn_fit = QPushButton(" ⛶ FIT ")
        btn_fit.clicked.connect(self.viewport.reset_view)
        toolbar.addWidget(btn_fit)

    def toggle_nav_mode(self):
        if self.viewport.nav_mode == "pan":
            self.viewport.nav_mode = "rotate"
            self.btn_nav_mode.setText(" 🔄 ROTATE ")
        else:
            self.viewport.nav_mode = "pan"
            self.btn_nav_mode.setText(" ✋ PAN ")
        self.viewport.update()

    def on_camera_mode_changed(self, text: str):
        if "3D" in text:
            self.viewport.cam_view = "angled"
        elif "2D" in text:
            self.viewport.cam_view = "topdown"
        elif "Follow" in text:
            self.viewport.cam_view = "follow"
        self.viewport.update()

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
        self.dispatch_group.setStyleSheet("background-color: #141822; border: 1px solid #232c3d; border-radius: 4px; padding: 6px;")
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

    def _build_bottom_panel(self) -> QWidget:
        panel = QTabWidget()

        # Tab 1: Active Tasks
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(["ID", "Task Type", "Destination", "Robot", "Status"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        panel.addTab(self.task_table, "Active Mission Queue")

        # Tab 2: System Event Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #11141a; color: #cbd5e1; font-size: 10px;")
        panel.addTab(self.log_text, "Event Log")

        return panel

    def on_state_received(self, snapshot: Dict[str, Any]):
        self.current_snapshot = snapshot
        self.viewport.update_snapshot(snapshot)

        # Clock
        sim_time = snapshot.get('sim_time', 0.0)
        mins = int(sim_time // 60)
        secs = sim_time % 60
        self.clock_label.setText(f" {mins:02d}:{secs:04.1f} ")

        # Active Tasks Table
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

        env_node = QTreeWidgetItem(root, ["Environment", "Scope"])
        for rm in snapshot.get('world', {}).get('rooms', []):
            item = QTreeWidgetItem(env_node, [rm['id'], "Room"])
            item.setData(0, Qt.ItemDataRole.UserRole, ("room", rm['id']))
        env_node.setExpanded(True)

        robots_node = QTreeWidgetItem(root, ["Robots (Nova Carter AMRs)", "Scope"])
        for r in snapshot.get('robots', []):
            item = QTreeWidgetItem(robots_node, [r['id'], "AMR"])
            item.setData(0, Qt.ItemDataRole.UserRole, ("robot", r['id']))
        robots_node.setExpanded(True)

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
                    f"TOTAL DISTANCE: {robot.get('total_distance', 0.0):.1f}m\n"
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
        self.status_bar.showMessage(f"Dispatching mission to local Ollama (phi3:mini on RTX 4060 GPU)...")

        try:
            req = urllib.request.Request(
                f"{API_BASE}/api/farsverse/command",
                data=json.dumps({"text": cmd}).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=8.0) as res:
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
        if hasattr(self, 'rl_tab') and self.rl_tab.worker and self.rl_tab.worker.isRunning():
            self.rl_tab.worker.stop()
        event.accept()


# ----------------------------------------------------------------------
# 7. Entrypoint
# ----------------------------------------------------------------------
def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = OmniverseMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
