# FARS Hospital Digital Twin — Unity 3D Setup

## Quick Start

### 1. Create Unity Project
1. Open **Unity Hub** → New Project → **3D (Built-in Render Pipeline)** or **3D (URP)**
2. Name it `FARS_DigitalTwin`, save anywhere temporary

### 2. Copy Scripts
Copy the entire `Assets/Scripts/` folder from this directory into your Unity project's `Assets/` folder:

```
FARS_DigitalTwin/
└── Assets/
    └── Scripts/          ← Copy this folder
        ├── Navigation/
        │   └── HospitalGraph.cs
        ├── World/
        │   └── HospitalWorldGenerator.cs
        ├── Agents/
        │   ├── RobotAgent.cs
        │   └── HumanAgent.cs
        ├── Tasks/
        │   └── TaskManager.cs
        ├── Camera/
        │   └── CameraController.cs
        ├── UI/
        │   └── DashboardUI.cs
        └── SimulationManager.cs
```

### 3. Scene Setup
1. Open the default `SampleScene`
2. Delete everything except the **Main Camera**
3. Create an empty GameObject → name it `SimulationManager`
4. Add the `SimulationManager` script component to it
5. **Press Play** — everything auto-generates!

### 4. Controls
| Input | Action |
|---|---|
| **Scroll wheel** | Zoom in/out |
| **Middle mouse drag** | Orbit camera |
| **Shift + Middle drag** | Pan camera |
| **1-5 keys** | Select & focus robot |
| **Home** | Reset camera to overview |
| **Escape** | Deselect |
| **Left click robot** | Select robot |
| **TAB** | Toggle typing mode |

### 5. What You Get
- **40+ rooms** with LED accent strips, walls, doors, and labels
- **5 robot agents** with FSM (idle → navigating → executing → charging)
- **33 human agents** (patients, doctors, nurses, visitors) wandering and requesting help
- **Auto task generation** from patient help requests
- **A* pathfinding** on the hospital graph
- **Dark sci-fi HUD** with fleet status, task queue, metrics, alerts
- **Smooth orbital camera** with cinematic interpolation

### 6. Architecture
All code is **fully self-contained** — no external dependencies, no asset imports needed.
The entire hospital, agents, paths, and UI are generated procedurally at runtime.
