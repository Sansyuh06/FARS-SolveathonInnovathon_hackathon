# FARS Hospital Unity Integration

This directory contains the Unity project stub and the Python backend simulation server.
The architecture uses a **Headless Python Simulation Server** that broadcasts state via WebSockets to a **Unity C# Client**.

## Setup Instructions

### 1. Run the Python Backend
The Python backend handles all LLM integration, agent state machines, and pathfinding.
```bash
cd fars_unity/python_backend
pip install websockets networkx requests
python simulation_server.py
```
*Note: Ensure Ollama is running (`ollama serve`) if you want LLM command parsing to work.*

### 2. Set Up Unity
1. Open the `fars_unity` folder in Unity Hub (Unity 2022.3+ recommended).
2. Create an empty GameObject in your scene named `SimulationBridge`.
3. Attach `SimulationBridge.cs` to it.
4. Set the `serverUrl` in the inspector to `ws://localhost:8765`.

### 3. Add Agent Controllers
1. Create an empty GameObject named `RobotManager`. Attach `RobotController.cs`. 
2. Assign a Robot Prefab (e.g., a capsule or custom 3D robot model) in the inspector.
3. Create an empty GameObject named `HumanManager`. Attach `HumanController.cs`.
4. Assign Human Prefabs (Doctor, Nurse, Patient, Visitor) in the inspector.

### 4. Add UI (Optional)
1. Create a Unity UI Canvas.
2. Add TextMeshPro Text objects for Stats, Alerts, and Active Tasks.
3. Create an empty GameObject named `Dashboard`, attach `DashboardUI.cs`, and link the Text objects.
4. Add a TMP Input Field for commands, attach `CommandInput.cs`, and link the field.

### 5. Play
When you press Play in Unity, `SimulationBridge` will connect to the Python server. You will see your Robot and Human prefabs spawn and move around the scene in real-time, matching the python backend's state exactly.
