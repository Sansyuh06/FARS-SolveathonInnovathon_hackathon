"""
launch_FARS.py — Single entry-point for the FARS desktop application.
Usage:
    python fars_studio/launch_FARS.py
Or double-click FARS.bat (Windows) / fars.sh (Linux).
"""
import sys
import os

# Ensure fars_studio is on the import path so relative imports work.
_STUDIO_DIR = os.path.dirname(os.path.abspath(__file__))
if _STUDIO_DIR not in sys.path:
    sys.path.insert(0, _STUDIO_DIR)

from panda3d.core import loadPrcFileData

# Suppress harmless Panda3D / Ursina engine chatter
loadPrcFileData('', 'notify-level-util error')
loadPrcFileData('', 'notify-level-prc error')
loadPrcFileData('', 'notify-level-pnmimage error')
loadPrcFileData('', 'notify-level-display error')
loadPrcFileData('', 'notify-level-text error')

from ursina import Ursina, window, color


def main() -> None:
    app = Ursina(
        title='FARS - Fully Autonomous Robotic Systems',
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
    )

    window.exit_button.visible = False
    window.fps_counter.enabled = True
    window.color = color.hex('#03060c')

    # Launch the cinematic boot sequence (transitions to main menu on its own)
    from boot import BootSequence
    BootSequence()

    app.run()


if __name__ == '__main__':
    main()
