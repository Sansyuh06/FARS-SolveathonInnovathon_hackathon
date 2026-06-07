# FARS — Fully Automated Robotic Systems

Production-ready **software-only** simulation of the complete FARS project (per `FARS_2.pdf`): face recognition, access control, IoT devices, cloud database, admin web UI, and 3D campus digital twin with autonomous robots.

No physical hardware required (ESP32, cameras, IR sensors are simulated).

## Quick start

**Windows PowerShell (recommended on your PC):**

```powershell
cd D:\fyeshi\project\rohit
.\start.ps1
```

**Windows CMD or double-click:** `start.bat`

**Git Bash / WSL / Linux only** (do not use `./start.sh` in PowerShell):

```bash
chmod +x start.sh
./start.sh
```

If port 8080 is busy, FARS automatically uses 8081, 8082, etc. Check the terminal for the real URL.

**Verify backend (no GUI):**

```bash
python scripts/verify_backend.py
```

**Or run Python directly:**

```bash
cd d:\fyeshi\project\rohit
pip install -r requirements.txt
python fars_platform/run.py
```

- **3D simulation window** — campus building, robots, humans, voice/text commands (Tab to type)
- **Admin dashboard** — http://127.0.0.1:8080/
- **API docs** — http://127.0.0.1:8080/docs

API + IoT only (no 3D window):

```bash
python fars_platform/run.py --no-3d
```

## Architecture

| Layer | Role |
|--------|------|
| `fars_platform/simulated_hardware/` | Virtual ESP32, IR, camera, Wi-Fi, Bluetooth |
| `fars_platform/services/` | Face recognition, access control, analytics |
| `fars_platform/core/` | SQLite DB, event bus, shared state |
| `fars_platform/api/` | FastAPI REST + WebSocket |
| `full_simulation/` | Ursina 3D digital twin (robots, navigation, tasks) |
| `FARS/` | Legacy face images & encodings (`EncodeFile.p`, `Images/`) |

## End-to-end flow

1. Simulated IR detects motion at Entrance / MainHall / Reception.
2. Virtual camera captures frames from `FARS/Images/`.
3. Face service identifies person (ML via `EncodeFile.p` if `face_recognition` installed, else filename match).
4. Access control logs attendance (30s cooldown), grants/denies access, writes SQLite + log file.
5. Unknown faces enqueue security robot tasks into the 3D sim.
6. Web dashboard shows live analytics, devices, attendance, access log.
7. Commands from web or 3D UI route to robot task queue via A* pathfinding.

## Data

- Database: `fars_platform/data/fars.db`
- Attendance log: `fars_platform/data/attendance_log.txt`

## Legacy scripts

Original hardware-targeted scripts remain in `FARS/` (`Fars_Main.py`, `GUI.py`). Use `fars_platform/run.py` for the integrated simulation.
