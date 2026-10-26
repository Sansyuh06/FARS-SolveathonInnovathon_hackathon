"""
boot.py — FARS cinematic boot / splash sequence.
Black screen -> FARS logo letter-by-letter -> diagnostics cascade -> menu.
Skippable with SPACE / ENTER / click.
"""
from ursina import Entity, Text, camera, color, time, invoke, destroy
from ui.palette import Palette


class BootSequence(Entity):
    """Runs the cold-boot intro, then hands off to MainMenu."""

    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)

        self._timer: float = 0.0
        self._phase: int = 0
        self._done: bool = False
        self._char1: int = 0
        self._char2: int = 0
        self._diag_idx: int = 0

        # --- full-screen black backdrop ---
        self._bg = Entity(parent=self, model='quad', scale=(3, 2),
                          color=color.black, z=1)

        # --- FARS letters (hidden until phase 1) ---
        self._logo = Entity(parent=self, y=0.12)
        letter_colors = [Palette.PRIMARY, Palette.SECONDARY,
                         Palette.SECONDARY, Palette.AI]
        self._letters = []
        for i, ch in enumerate("FARS"):
            glow = Text(parent=self._logo, text=ch, origin=(0, 0),
                        x=-0.15 + i * 0.10, color=Palette.GLOW_GREEN,
                        scale=6, z=0.1, enabled=False)
            main = Text(parent=self._logo, text=ch, origin=(0, 0),
                        x=-0.15 + i * 0.10, color=letter_colors[i],
                        scale=6, z=0, enabled=False)
            self._letters.append((main, glow))

        # --- subtitles (typed on) ---
        self._sub1 = Text(parent=self, text='', origin=(0, 0),
                          y=-0.06, color=Palette.WHITE, scale=1.5)
        self._sub2 = Text(parent=self, text='', origin=(0, 0),
                          y=-0.12, color=Palette.SECONDARY, scale=1.1)

        # --- diagnostic lines ---
        self._diag_parent = Entity(parent=self, y=-0.22, x=-0.38)
        self._diag_lines = [
            '[ OK ] Physics engine ............... Ursina/Panda3D',
            '[ OK ] GPU acceleration ............. CUDA detected',
            '[ OK ] Neural policy network ........ loaded (87M params)',
            '[ OK ] Scenario library ............. 6 environments',
            '[ OK ] Synthetic data pipeline ...... Cosmos-ready',
            '[ OK ] Robot fleet mesh ............. connected',
            '[ OK ] Digital twin kernel .......... online',
        ]
        self._diag_texts = []
        for i in range(len(self._diag_lines)):
            t = Text(parent=self._diag_parent, text='', origin=(-0.5, 0),
                     y=-i * 0.04, color=Palette.PRIMARY, scale=0.9)
            self._diag_texts.append(t)

        self._TXT1 = 'FULLY AUTONOMOUS ROBOTIC SYSTEMS'
        self._TXT2 = '[ INITIALIZING NEURAL CORE... ]'

    # ------------------------------------------------------------------
    def input(self, key: str) -> None:
        if not self._done and key in ('space', 'enter', 'left mouse down'):
            self._skip()

    # ------------------------------------------------------------------
    def update(self) -> None:
        if self._done:
            return

        self._timer += time.dt
        t = self._timer

        # Phase 0 → 1 : black hold
        if self._phase == 0 and t > 0.8:
            self._phase = 1

        # Phase 1 : reveal letters one by one
        if self._phase == 1:
            for i, (main, glow) in enumerate(self._letters):
                if t > 0.8 + i * 0.15 and not main.enabled:
                    main.enabled = True
                    glow.enabled = True
            if t > 1.5:
                self._phase = 2

        # Phase 2 : type subtitle 1
        if self._phase == 2:
            n = int((t - 1.5) * 30)
            if n > self._char1:
                self._char1 = min(n, len(self._TXT1))
                self._sub1.text = self._TXT1[:self._char1]
                if self._char1 >= len(self._TXT1):
                    self._phase = 3

        # Phase 3 : type subtitle 2
        if self._phase == 3:
            n = int((t - 2.5) * 30)
            if n > self._char2:
                self._char2 = min(n, len(self._TXT2))
                self._sub2.text = self._TXT2[:self._char2]
                if self._char2 >= len(self._TXT2):
                    self._phase = 4

        # Phase 4 : cascade diagnostics
        if self._phase == 4:
            idx = int((t - 3.2) * 8)
            if idx > self._diag_idx and idx <= len(self._diag_lines):
                self._diag_idx = idx
                self._diag_texts[idx - 1].text = self._diag_lines[idx - 1]
            if self._diag_idx >= len(self._diag_lines) and t > 4.5:
                self._phase = 5

        # Phase 5 : transition to menu
        if self._phase == 5:
            self._skip()

    # ------------------------------------------------------------------
    def _skip(self) -> None:
        if self._done:
            return
        self._done = True
        # fade backdrop to transparent then launch menu
        self._bg.animate_color(color.clear, duration=0.4)
        self._logo.animate('alpha', 0, duration=0.3)
        self._sub1.animate('alpha', 0, duration=0.3)
        self._sub2.animate('alpha', 0, duration=0.3)
        self._diag_parent.animate('alpha', 0, duration=0.3)
        invoke(self._launch_menu, delay=0.5)

    def _launch_menu(self) -> None:
        from main_menu import MainMenu
        menu = MainMenu()
        menu.show()
        destroy(self)
