# FARSverse — Interactive Robotics Simulation & Digital Twin Platform

**FARSverse** is a complete, desktop-quality robotics simulation, digital twin, and experimentation platform inspired by NVIDIA Omniverse, professional 3D editor interfaces, and management simulation games. 

Accessible through a local web application without external cloud dependencies, FARSverse enables engineers and researchers to design environments, deploy autonomous multi-robot fleets, test pathfinding and obstacle avoidance, run comparative experiments, and analyze robotic behavior in real time.

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               FARSverse Studio               │
                    │        (Next.js 15, React 19, Three.js)      │
                    └──────────────────────┬───────────────────────┘
                                           │ WebSocket (15 Hz) & REST
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FARSverse Authoritative Backend Engine                          │
│                                (FastAPI & SQLite)                                      │
├─────────────────────┬──────────────────────┬────────────────────┬──────────────────────┤
│  Authoritative Loop │  World & Navigation  │   Fleet & Tasks    │  Research & Analysis │
│  • 20 Hz tick loop  │  • Multi-room layout │   • FSM Robots     │  • Benchmark runner  │
│  • Speed 0.5x - 4x  │  • A* Grid pathfind  │   • Multi-factor   │  • RL Gymnasium env  │
│  • Deterministic    │  • Dynamic obstacles │     scheduler      │  • CSV/JSON export   │
│  • Step & Pause     │  • Corridor reroutes │   • Battery models │  • Ollama & NLP rule │
└─────────────────────┴──────────────────────┴────────────────────┴──────────────────────┘
```

---

## ✨ Core Features

### 1. 3D Robotics Studio Viewport
- **Authoritative Rendering**: Interactive 3D hospital digital twin with 20 individually identifiable patient rooms, reception, waiting hall, pharmacy, emergency department, ICU wards, and charging stations.
- **Robot Kinematics & Visual Telemetry**: Mobile robot bases with real-time heading indicators, dynamic battery meters, glowing status rings, and projected A* navigation path lines.
- **Autonomous Human Agents**: Over 20 simulated patients, nurses, doctors, and visitors with behavioral routines and dynamic assistance requests.
- **Camera Presets**: Seamlessly toggle between **Isometric Angled View**, **Top-Down 2D Architectural Floorplan**, and **Follow Robot Chase Cam**.
- **Interactive Raycasting**: Click any robot, human, obstacle, or room in the 3D viewport to inspect its live simulation state.

### 2. Autonomous Task Manager & Scheduler
- **Multi-Factor Robot Scoring**:
  $$\text{Score} = (12 \times \text{Priority}) - (1.4 \times \text{Distance}) + (0.45 \times \text{Battery}) - \text{Charging Penalty}$$
- **Priority Scale**: Critical (P4), High (P3), Normal (P2), Low (P1).
- **Decision Trace Log**: Explains why a specific robot was chosen (e.g., *"Assigned FARS-02: lowest distance 6.2m, healthy battery 84%, score 68.3"*).
- **Battery Dynamics**: Realistic consumption based on distance traveled ($0.18\%/\text{m}$) and idle time, with autonomous return-to-dock behaviors when battery falls below $20\%$.

### 3. Dynamic Obstacle Avoidance & Replanning
- Place obstacles (medical carts, maintenance signs, pallets) directly into corridors.
- Dynamic obstacle toggling immediately updates the navigation graph and triggers automated A* path recalculation or blockage alerts.

### 4. Natural Language Commands (Offline & Ollama)
- Control the simulation via plain English:
  - *"Send the nearest available robot to Room 19"*
  - *"Deliver medication to ICU Ward 2"*
  - *"Block the west corridor and observe reactions"*
  - *"Pause all robots"* / *"Resume simulation"*
- Supports local Ollama 7B LLM servers with zero-latency deterministic regex fallback.

### 5. Experiment & Analysis Laboratory
- Run automated benchmarks comparing fleet sizes (e.g. 1-Robot vs 3-Robots vs 5-Robots) over identical workloads.
- Measures:
  - Task completion rate (%)
  - Average response time (s)
  - Total travel distance (m)
  - Battery consumed (%)
  - Collisions / Obstacle reroutes
  - Robot idle time (s)
- One-click **CSV / JSON Export** for research analysis.

### 6. Reinforcement Learning Laboratory
- Authentic **Gymnasium** environment (`HospitalGridNavEnv`) with Box(6) continuous observations and Discrete(4) actions.
- Real neural Q-learning training runs tracking episode rewards and comparing against classical A* shortest-path baselines.

### 7. Project Persistence & Asset Uploads
- SQLite-backed project library supporting templates:
  - **Hospital Showcase (Flagship)**
  - **Campus Quad**
  - **Logistics Fulfillment Center**
  - **Blank Sandbox Workspace**
- Secure drag-and-drop `.glb` and `.gltf` 3D model asset uploader with path traversal protection and 50MB file validation.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Launch with One Click (Windows)
Double-click [`launch_farsverse.bat`](file:///d:/fyeshi/project/rohit/launch_farsverse.bat) or run from PowerShell:
```powershell
.\launch_farsverse.bat
```

### 2. Launch on Linux / macOS
```bash
chmod +x launch_farsverse.sh
./launch_farsverse.sh
```

### 3. Launching Services Manually
In terminal 1 (Backend API & Authoritative Engine):
```bash
python fars_platform/run.py --no-3d
```
In terminal 2 (Next.js Studio Frontend):
```bash
cd desktop/farsy-main
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

---

## 🧪 Automated Acceptance Testing

FARSverse includes a comprehensive test suite validating all 10 mandatory workflows:
```bash
python tests/test_farsverse_acceptance.py
```
Test results verify:
1. Start simulation & real-time state synchronization
2. Manual task assignment & waypoint following
3. Natural language command interpretation
4. Robot inspection & pause/step controls
5. Obstacle collision detection & dynamic rerouting
6. Battery depletion & autonomous charging returns
7. Project persistence & SQLite reopening
8. 3D asset (.glb) format validation
9. Benchmark scenario execution & CSV export
10. Backend reset & system resilience

To run backend module verification:
```bash
python scripts/verify_backend.py
```

---

## 📁 Repository Structure

```
rohit/
├── desktop/
│   └── farsy-main/                 # Next.js 15 + Three.js FARSverse Studio
│       ├── src/
│       │   ├── app/                # Main simulation page & layout
│       │   ├── components/farsverse/
│       │   │   ├── FARSverseStudio.tsx  # Root studio shell
│       │   │   ├── Viewport3D.tsx       # Three.js 3D Viewport
│       │   │   ├── TopToolbar.tsx       # Transport controls & command bar
│       │   │   ├── LeftSidebar.tsx      # Hierarchy, Builder, Fleet, Labs
│       │   │   ├── RightInspector.tsx   # Contextual entity inspector
│       │   │   ├── BottomConsole.tsx    # Tasks, Events, Metrics, Charts
│       │   │   ├── AssetUploadModal.tsx # GLB/glTF 3D model uploader
│       │   │   └── ProjectsModal.tsx    # Project templates & SQLite persistence
│       │   └── lib/farsverse-api.ts     # Real-time WebSocket & REST client
│
├── kernel/
│   ├── api/app.py                  # FastAPI server with /ws/farsverse & REST endpoints
│   ├── farsverse/                  # Authoritative simulation core
│   │   ├── engine.py               # 20 Hz simulation heartbeat loop
│   │   ├── world.py                # Hospital/Campus/Warehouse geometry & A* pathfinder
│   │   ├── robot.py                # Robot kinematics, battery model & FSM
│   │   ├── human.py                # Human agents & help request routines
│   │   ├── task_manager.py         # Multi-factor priority task scheduler
│   │   ├── nlp_parser.py           # Natural language interpreter (Ollama + fallback)
│   │   ├── experiment_lab.py       # Benchmark suite & CSV exporter
│   │   ├── rl_lab.py               # Gymnasium navigation environment & policy trainer
│   │   └── persistence.py          # SQLite project & asset storage
│
├── simulation/                     # Shared navigation & coordinate models
├── tests/
│   └── test_farsverse_acceptance.py # 10/10 automated acceptance test suite
├── launch_farsverse.bat            # Single-click Windows launcher
└── launch_farsverse.sh             # Linux launcher
```

---

## 🔒 Security & Local Operation
- **100% Offline Capability**: Runs entirely on `localhost`. Does not require external cloud services, third-party databases, or internet access.
- **Secure File Ingestion**: Uploaded 3D assets are checked against strict extension allowances (`.glb`, `.gltf`), bounded to 50 MB, sanitized to prevent path traversal, and stored in isolated storage directories.
- **SQL Injection Prevention**: Parameterized queries across all database operations in SQLite with WAL mode.
