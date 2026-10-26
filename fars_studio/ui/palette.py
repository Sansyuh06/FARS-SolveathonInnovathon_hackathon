# ui/palette.py — Single source of truth for all FARS colors.
# NEVER hardcode hex values elsewhere. Import from here.
from ursina import color


class Palette:
    """NVIDIA-GTC-meets-Blade-Runner color system."""

    # Core
    BACKGROUND  = color.hex('#03060c')
    PRIMARY     = color.hex('#00ffc2')   # cyber-green
    SECONDARY   = color.hex('#00d4ff')   # cyan
    AI          = color.hex('#ff3df0')   # magenta
    WARN        = color.hex('#ffb800')   # amber
    ERR         = color.hex('#ff3860')   # red
    WHITE       = color.hex('#d2d7e1')
    BLACK       = color.hex('#03060c')

    # Panels (dark, semi-transparent) — Color(r, g, b, a) in 0-1 range
    PANEL       = color.Color(0.02, 0.03, 0.05, 0.92)
    PANEL_LIGHT = color.Color(0.03, 0.04, 0.07, 0.80)
    BAR         = color.Color(0.03, 0.04, 0.06, 1.0)

    # Glow / translucent accents
    GLOW_GREEN  = color.Color(0.0, 1.0, 0.76, 0.15)
    GLOW_CYAN   = color.Color(0.0, 0.83, 1.0, 0.15)
    HIGHLIGHT   = color.Color(0.0, 1.0, 0.76, 0.12)
