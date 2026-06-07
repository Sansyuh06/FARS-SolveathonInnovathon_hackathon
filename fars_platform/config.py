"""FARS platform configuration — all paths relative to project root."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FARS_LEGACY = PROJECT_ROOT / "FARS"
SIMULATION_DIR = PROJECT_ROOT / "full_simulation"

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "fars.db"
ENCODE_FILE = FARS_LEGACY / "EncodeFile.p"
IMAGES_DIR = FARS_LEGACY / "Images"
ATTENDANCE_LOG = DATA_DIR / "attendance_log.txt"
ALERTS_LOG = DATA_DIR / "alerts_log.txt"

API_HOST = "127.0.0.1"
API_PORT = 8080

# Simulated hardware timing (seconds)
IR_SCAN_INTERVAL = 2.5
FACE_COOLDOWN_SEC = 30
CAMERA_CYCLE_SEC = 4.0

# Access control
UNKNOWN_FACE_DENY = True
AUTO_PATROL_ON_INTRUSION = True
