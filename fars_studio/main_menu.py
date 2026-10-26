"""
main_menu.py — FARS main-menu screen (game-launcher style).
Rotating wireframe city background, left nav, center scenario cards,
right neural-core widget, bottom status bar.  Everything is clickable.
"""
from __future__ import annotations
import random as _rand
import datetime as _dt
from ursina import (Entity, Text, Button, camera, color, time,
                     window, application, scene, destroy)
from ui.palette import Palette


class MainMenu(Entity):
    """Full-screen main menu shown after boot sequence."""

    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.enabled = False
        self._selected_idx: int = 0          # left-nav selected index

        # ── 3D rotating wireframe city ──────────────────────────────
        self._city = Entity(parent=scene)
        for x in range(-3, 4):
            for z in range(-3, 4):
                h = _rand.uniform(0.6, 3.5)
                Entity(
                    parent=self._city, model='cube',
                    scale=(0.7, h, 0.7),
                    position=(x * 1.8, h / 2 - 3, z * 1.8 + 12),
                    color=color.Color(0.0, 0.4, 0.3, 0.08),
                    unlit=True,
                )
                Entity(
                    parent=self._city, model='cube',
                    scale=(0.72, h + 0.02, 0.72),
                    position=(x * 1.8, h / 2 - 3, z * 1.8 + 12),
                    color=Palette.PRIMARY,
                    unlit=True, wireframe=True,
                )
        self._city.rotation_y = -30

        # ── Left panel background (non-interactive) ────────────────
        Entity(parent=self, model='quad', color=Palette.PANEL,
               scale=(0.36, 1.0), position=(-0.63, 0), z=0.5,
               collider=None)

        # ── Left nav buttons ───────────────────────────────────────
        labels = [
            'PLAY SCENARIOS', 'ROBOT GARAGE', 'NEURAL TRAINING LAB',
            'SCENARIO BUILDER', 'DATASET FORGE', 'SETTINGS', 'EXIT',
        ]
        self._nav_btns: list[Button] = []
        for i, lbl in enumerate(labels):
            btn = Button(
                parent=self,
                text=f'  > {lbl}',
                text_origin=(-0.5, 0),
                text_color=Palette.PRIMARY if i == 0 else Palette.WHITE,
                color=color.Color(0.05, 0.08, 0.12, 0.9) if i == 0 else color.Color(0.02, 0.03, 0.05, 0.7),
                highlight_color=color.Color(0.0, 0.5, 0.38, 0.4),
                pressed_color=color.Color(0.0, 0.8, 0.6, 0.5),
                scale=(0.32, 0.045),
                position=(-0.63, 0.30 - i * 0.07),
                z=0,
            )
            idx = i  # capture for closure
            btn.on_click = lambda idx=idx: self._on_nav_click(idx)
            self._nav_btns.append(btn)

        # ── Center panel background ────────────────────────────────
        Entity(parent=self, model='quad', color=Palette.PANEL_LIGHT,
               scale=(0.70, 0.78), position=(-0.04, 0.0), z=0.5,
               collider=None)

        self._center_title = Text(
            parent=self, text='PLAY SCENARIOS', color=Palette.SECONDARY,
            scale=2.0, position=(-0.35, 0.36), z=0)
        self._center_sub = Text(
            parent=self, text='Select an environment to initialize simulation core.',
            color=Palette.WHITE, scale=0.9, position=(-0.35, 0.31), z=0)

        # ── 6 scenario cards (clickable!) ──────────────────────────
        self._scenarios = [
            ('HOSPITAL WING',   'Deliver meds, assist patients',  Palette.PRIMARY),
            ('WAREHOUSE',       'Pick-and-place, sort boxes',     Palette.SECONDARY),
            ('CAMPUS PATROL',   'Night security, face recog',     Palette.AI),
            ('HOME ASSISTANT',  'Elderly care, fall detection',   Palette.WARN),
            ('MARS COLONY',     'Low-gravity, solar repair',      Palette.ERR),
            ('SMART CITY',      'Traffic, multi-robot coord',     Palette.PRIMARY),
        ]
        self._scenario_btns: list[Button] = []
        for idx, (name, desc, col) in enumerate(self._scenarios):
            row = idx // 3
            col_n = idx % 3
            bx = -0.26 + col_n * 0.21
            by = 0.16 - row * 0.24

            card = Button(
                parent=self,
                text='',
                color=color.Color(0.04, 0.05, 0.08, 0.95),
                highlight_color=color.Color(0.0, 0.3, 0.22, 0.6),
                pressed_color=color.Color(0.0, 0.5, 0.38, 0.7),
                scale=(0.19, 0.20),
                position=(bx, by),
                z=0,
            )
            # Card title
            Text(parent=card, text=name, color=col, scale=3.5,
                 position=(0, 0.3), origin=(0, 0), z=-0.01)
            # Card description
            Text(parent=card, text=desc, color=Palette.WHITE, scale=2.5,
                 position=(0, 0.05), origin=(0, 0), z=-0.01)
            # Difficulty dots
            diff = _rand.randint(1, 3)
            Text(parent=card, text='*' * diff, color=Palette.WARN, scale=3.0,
                 position=(0, -0.2), origin=(0, 0), z=-0.01)
            # Border glow (top line)
            Entity(parent=card, model='quad', color=col,
                   scale=(1.0, 0.015), position=(0, 0.49), z=-0.01,
                   collider=None)

            sidx = idx
            card.on_click = lambda sidx=sidx: self._on_scenario_click(sidx)
            self._scenario_btns.append(card)

        # ── Right panel background ─────────────────────────────────
        Entity(parent=self, model='quad', color=Palette.PANEL,
               scale=(0.34, 1.0), position=(0.63, 0), z=0.5,
               collider=None)

        Text(parent=self, text='FARS NEURAL CORE', color=Palette.AI,
             scale=1.4, position=(0.48, 0.36), z=0)

        # Neural net "diagram" — simple pulsing dots
        self._dots: list[Entity] = []
        dot_positions = [
            (0.55, 0.20), (0.65, 0.22), (0.75, 0.20),
            (0.55, 0.12), (0.65, 0.10), (0.75, 0.12),
            (0.60, 0.04), (0.70, 0.04),
        ]
        for dx, dy in dot_positions:
            d = Entity(parent=self, model='circle', color=Palette.PRIMARY,
                       scale=0.012, position=(dx, dy), z=0, collider=None)
            self._dots.append(d)

        self._stats = Text(
            parent=self, text='', color=Palette.WHITE,
            scale=0.85, position=(0.48, -0.05), z=0,
        )

        # ── Bottom bar ─────────────────────────────────────────────
        Entity(parent=self, model='quad', color=Palette.BAR,
               scale=(2.0, 0.055), position=(0, -0.47), z=0.5,
               collider=None)
        Text(parent=self, text='v1.0.0-alpha', color=Palette.WHITE,
             scale=0.7, position=(-0.90, -0.465), z=0)
        Text(parent=self, text='[ NVIDIA COSMOS COMPATIBLE ]',
             color=Palette.PRIMARY, scale=0.7,
             position=(-0.55, -0.465), z=0)
        Text(parent=self, text='[ ISAAC SIM BRIDGE: READY ]',
             color=Palette.SECONDARY, scale=0.7,
             position=(-0.10, -0.465), z=0)
        self._clock = Text(parent=self, text='00:00:00',
                           color=Palette.WHITE, scale=0.7,
                           position=(0.78, -0.465), z=0)

        # ── Feedback text (shows when you click things) ────────────
        self._feedback = Text(
            parent=self, text='', color=Palette.PRIMARY,
            scale=1.2, position=(0, -0.40), origin=(0, 0), z=0)

    # ------------------------------------------------------------------
    #  Click handlers
    # ------------------------------------------------------------------
    def _on_nav_click(self, idx: int) -> None:
        labels = [
            'PLAY SCENARIOS', 'ROBOT GARAGE', 'NEURAL TRAINING LAB',
            'SCENARIO BUILDER', 'DATASET FORGE', 'SETTINGS', 'EXIT',
        ]
        # Update selection highlight
        self._selected_idx = idx
        for i, btn in enumerate(self._nav_btns):
            if i == idx:
                btn.text_color = Palette.PRIMARY
                btn.color = color.Color(0.05, 0.08, 0.12, 0.9)
            else:
                btn.text_color = Palette.WHITE
                btn.color = color.Color(0.02, 0.03, 0.05, 0.7)

        if idx == 6:
            application.quit()
        else:
            self._feedback.text = f'[ {labels[idx]} SELECTED ]'
            self._feedback.color = Palette.PRIMARY
            self._center_title.text = labels[idx]

    def _on_scenario_click(self, idx: int) -> None:
        name = self._scenarios[idx][0]
        self._feedback.text = f'[ LOADING {name}... ]'
        self._feedback.color = Palette.SECONDARY
        print(f'[FARS] Scenario selected: {name}')

    # ------------------------------------------------------------------
    def update(self) -> None:
        self._city.rotation_y += 8 * time.dt

        # Live clock
        self._clock.text = _dt.datetime.now().strftime('%H:%M:%S')

        # Pulse neural dots
        import math
        for i, d in enumerate(self._dots):
            phase = time.time() * 3 + i * 0.8
            d.scale_x = 0.010 + 0.004 * math.sin(phase)
            d.scale_y = d.scale_x

        # Mock telemetry
        fps_val = int(1.0 / max(time.dt, 0.001))
        self._stats.text = (
            f'[ GPU  94% ]\n'
            f'[ VRAM 14.2 GB ]\n'
            f'[ FPS  {fps_val} ]\n'
            f'\n'
            f'POLICY : PPO-v14\n'
            f'ROBOTS : 0 / 0'
        )

    # ------------------------------------------------------------------
    def show(self) -> None:
        self.enabled = True
        self._city.enabled = True

    def hide(self) -> None:
        self.enabled = False
        self._city.enabled = False
