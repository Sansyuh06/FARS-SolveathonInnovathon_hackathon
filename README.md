# FARS — Fully Automated Robotic Systems

FARS is a comprehensive, production-ready, software-only simulation of a complete facility security and automation ecosystem. By bridging simulated IoT edge hardware, modern web dashboards, a 3D digital twin, and autonomous robotic pathfinding, FARS serves as a robust prototype for next-generation automated surveillance and facility management.

The system is designed to eliminate the high startup cost of physical hardware prototyping while remaining architecturally identical to a real-world deployment.

---

## 📌 Problem Statement

In modern commercial, educational, and medical campuses, security and operational management face several critical vulnerabilities:
1. **Manual Surveillance & Logging**: Security personnel are prone to fatigue, distraction, and cognitive overload. Traditional CCTV monitoring is passive—relying on post-incident analysis rather than proactive threat mitigation.
2. **Access Control Flaws**: Standard authentication methods (magnetic swipe cards, PIN codes, barcodes) are easily bypassed via card-sharing, loss, theft, or duplication.
3. **Response Latency**: When a security breach or unknown individual is detected, the latency between detection, notification, and dispatch of security forces can range from minutes to hours.
4. **Data Silos**: IoT sensors, access control databases, and robot fleets operate on separate platforms, making it difficult for administrators to gain unified real-time operational awareness.

---

## 💡 The FARS Solution

FARS solves these issues by establishing a fully integrated, software-simulated ecosystem:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              FARS ECOSYSTEM                            │
├───────────────────────┬──────────────────────┬─────────────────────────┤
│    Simulated Edge     │  Central Backend &   │    3D Digital Twin      │
│     IoT Hardware      │     REST/WS APIs     │     & Robot Fleet       │
│  (Virtual ESP32, IR,  │  (FastAPI, SQLite,   │   (Ursina 3D Engine,    │
│    Cameras, Wi-Fi)    │   Face Recognition)  │  A* Pathfinding, LLM)   │
└───────────┬───────────┴──────────┬───────────┴────────────┬────────────┘
            │                      │                        │
            └───────────────► [ EVENT BUS ] ◄───────────────┘
```

1. **Simulated Hardware Loop**: Emulates physical NodeMCU ESP32 boards, Infrared (IR) motion sensors, and camera modules. When motion is detected, simulated camera frames are captured and streamed to the backend.
2. **AI-Driven Facial Recognition**: Identifies individuals at campus checkpoints using OpenCV and pre-trained face-encoding models. If an unknown face is detected, a security event is logged.
3. **Autonomous Robot Dispatch**: Unknown faces or security anomalies trigger the automated creation of security patrols in the **3D Digital Twin**. Robots use A* pathfinding to navigate campus corridors to investigate the event.
4. **Admin Telemetry Dashboard**: A unified web-based dashboard utilizing WebSockets for real-time logs, live camera streams, system status telemetry, and remote robot command dispatch.
5. **Reinforcement Learning Sandbox**: A dedicated Gym-based training environment for training bipedal robot locomotion controllers using PyTorch, preparing robot models for physical gait simulation.

---

## 🛠️ Tech Stack

### Backend & Core Services
- **Language**: Python 3.10+
- **API Framework**: FastAPI (REST endpoints & real-time WebSockets)
- **Database**: SQLite (SQLAlchemy ORM for local state persistence) / Firebase integration support
- **Computer Vision**: OpenCV (`opencv-python`) & `face_recognition` (dlib-based high-accuracy encodings)

### 3D Digital Twin & Simulation
- **3D Engine**: Ursina Engine (built on top of Panda3D) for the 3D campus twin.
- **Pathfinding**: A* Search Algorithm mapped onto a grid representation of the environment.
- **Command Parser**: Custom NLP / LLM Command Parser translating voice or text strings (e.g., *"Go to Room 101"*) into structured JSON instructions for the robot task queues.

### Admin Dashboard & Frontend
- **Frontend Stack**: Semantic HTML5, Vanilla CSS3 (glassmorphism UI layout), Modern JavaScript (Fetch API, WebSocket streams).
- **Visualization**: Chart.js for real-time analytics.

### Reinforcement Learning
- **Environments**: OpenAI Gym
- **Framework**: PyTorch (Deep Q-Networks / Policy Gradients for robot locomotion training)
- **Visualization**: Pygame / Custom rendering for physical gait steps.

---

## 🏗️ System Architecture & Component Breakdown

```
rohit/
├── fars_platform/             # Backend, APIs, Database & Virtual Edge Devices
│   ├── api/                   # FastAPI routes (WebSockets, analytics, robot control)
│   ├── core/                  # Event bus, database connection, shared state
│   ├── services/              # AI Face Recognition, Access Control registry
│   ├── simulated_hardware/    # Virtual ESP32, camera feeds, IR sensors
│   └── web/                   # HTML/CSS/JS files for Admin Web UI dashboard
│
├── full_simulation/           # 3D Digital Twin and Robot Fleet Simulation
│   ├── agents/                # Human and robot entity models
│   ├── hospital_world.py      # Campus layout, grids, walls, rooms setup
│   ├── navigation.py          # A* pathfinding implementation
│   ├── task_manager.py        # Task queuing and priority scheduler
│   └── main_simulation.py     # Main Ursina game loop & renderer
│
├── reinfrocement learning/    # Locomotion & walker training environment (PyTorch)
│   ├── base_env.py            # Custom Gym Walker environment
│   └── walker_sim.py          # Physics and walking simulation
│
└── fars_iso/                  # Particle & isometric rendering experiments
```

---

## 🚀 How to Run FARS Locally

FARS runs out of the box with zero external hardware requirements. It simulates the entire campus ecosystem in-memory.

### Prerequisites
Make sure you have Python 3.10+ installed on your computer.

### Step 1: Install Dependencies
Open a terminal in the project directory and install the required Python libraries:
```bash
pip install -r requirements.txt
```

### Step 2: Start the Integrated Simulation
To launch the backend API, the web dashboard, and the 3D digital twin simultaneously, use the launcher scripts:

* **Windows (PowerShell - Recommended)**:
  ```powershell
  .\start.ps1
  ```
* **Windows (CMD or Double-Click)**:
  ```cmd
  start.bat
  ```
* **Linux / WSL / Git Bash**:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

### Step 3: Access the Control Centers
- **3D digital twin window**: Displays the campus lobby, classrooms, autonomous security robots, and moving human agents. Use the `Tab` key to open the text interface to type natural language commands to the robots.
- **Admin Dashboard**: Open [http://127.0.0.1:8080/](http://127.0.0.1:8080/) in your web browser to view logs, check sensor states, examine authentication history, and send test triggers.
- **API Documentation**: Interactive OpenAPI swagger docs are accessible at [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs).

---

## 📈 Impact & SDG Alignment

This project aligns directly with three of the United Nations Sustainable Development Goals (SDGs):

### 1. SDG 9: Industry, Innovation, and Infrastructure
- **Objective**: Foster innovation and build resilient infrastructure.
- **Impact**: FARS introduces a blueprint for smart campus and workplace infrastructure. By utilizing digital twin technology, facility managers can optimize layout planning and security operations digitally before deploying physical hardware, reducing manufacturing waste and material costs.

### 2. SDG 16: Peace, Justice, and Strong Institutions
- **Objective**: Promote transparent, safe, and accountable institutions.
- **Impact**: The automated face-recognition-based logging system ensures accurate, tamper-proof record-keeping of access control history. This eliminates proxy attendance and unauthorized entry, reducing human errors in security management.

### 3. SDG 8: Decent Work and Economic Growth
- **Objective**: Increase workplace productivity and operational efficiency.
- **Impact**: By automating repetitive surveillance tasks, security staff can transition from monitoring screens to handling escalated responses. It maximizes campus safety, making workplaces safer and operations more cost-efficient.
