"""
FastAPI Backend for FARSverse Platform
Exposes authoritative simulation state, WebSockets, REST APIs, persistence, and asset uploads.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from kernel.farsverse.engine import SimulationEngine
from kernel.farsverse.experiment_lab import ExperimentLab
from kernel.farsverse.persistence import FARSversePersistence, UPLOAD_DIR
from kernel.farsverse.rl_lab import RLLaboratory

WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


class CommandRequest(BaseModel):
    text: Optional[str] = None
    command: Optional[str] = None

    def get_text(self) -> str:
        return (self.text or self.command or "").strip()


class VoiceRequest(BaseModel):
    text: str


class ScanRequest(BaseModel):
    location: str = "Entrance"


class ControlRequest(BaseModel):
    action: str  # play, pause, stop, reset, step, set_speed, load_environment
    speed: Optional[float] = None
    seconds: Optional[float] = None
    template: Optional[str] = None


class TaskCreateRequest(BaseModel):
    task_type: str = "assist_patient"
    location: str = "Room1"
    priority: int = 2
    description: str = ""


class ObstacleRequest(BaseModel):
    id: str
    name: str
    x: float
    z: float
    width: float = 1.5
    depth: float = 1.5
    active: bool = True
    desc: str = ""


class ObstacleToggleRequest(BaseModel):
    active: Optional[bool] = None


class ProjectSaveRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    environment_type: str = "hospital"
    world_data: Dict[str, Any] = {}
    robot_configs: List[Dict[str, Any]] = []
    scenario_config: Dict[str, Any] = {}


class ExperimentRunRequest(BaseModel):
    robot_count: int = 3
    num_tasks: int = 15
    environment: str = "hospital"
    seed: int = 42


class RLTrainRequest(BaseModel):
    episodes: int = 40
    learning_rate: float = 0.01


class RobotUpdateRequest(BaseModel):
    speed: Optional[float] = None
    battery: Optional[float] = None
    robot_type: Optional[str] = None


class TeleopRequest(BaseModel):
    robot_id: str = "FARS-01"
    linear: float = 0.0
    angular: float = 0.0


# Authoritative Global Simulation Engine Singleton
_global_engine: Optional[SimulationEngine] = None


def get_simulation_engine() -> SimulationEngine:
    global _global_engine
    if _global_engine is None:
        _global_engine = SimulationEngine(template_name="hospital", robot_count=5, human_count=24)
    return _global_engine


def create_app(db, analytics, access, device_hub, bus, state) -> FastAPI:
    app = FastAPI(title="FARSverse Interactive Robotics Platform", version="2.0.0")

    # Enable CORS for Next.js and frontend dev servers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Persistence layer
    persistence = FARSversePersistence(db._conn)
    engine = get_simulation_engine()

    # Static mounts
    if WEB_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/assets/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # ------------------------------------------------------------------
    #  Base Platform & Legacy Endpoints
    # ------------------------------------------------------------------
    @app.get("/")
    async def index():
        index_path = WEB_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {
            "name": "FARSverse Interactive Robotics Platform",
            "version": "2.0.0",
            "status": "operational",
            "docs": "/docs",
            "farsverse_state": "/api/farsverse/state"
        }

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "platform": "FARSverse",
            "sim_status": engine.status,
            "sim_time": engine.sim_time,
            "robots_online": len(engine.robots),
            "engine_active": True
        }

    @app.get("/api/analytics")
    async def get_analytics():
        return analytics.dashboard_payload()

    @app.get("/api/students")
    async def list_students():
        return db.list_students()

    @app.get("/api/events")
    async def events():
        return db.recent_events()

    @app.post("/api/scan")
    async def manual_scan(req: ScanRequest):
        return device_hub.trigger_manual_scan(req.location)

    # ------------------------------------------------------------------
    #  FARSverse Authoritative State & Simulation APIs
    # ------------------------------------------------------------------
    @app.get("/api/farsverse/state")
    async def farsverse_get_state():
        return engine.get_snapshot()

    @app.post("/api/farsverse/control")
    async def farsverse_control(req: ControlRequest):
        action = req.action.lower()
        if action == "play":
            engine.play()
        elif action == "pause":
            engine.pause()
        elif action == "stop":
            engine.stop()
        elif action == "reset":
            engine.reset()
        elif action == "step":
            engine.step(req.seconds or 0.5)
        elif action == "set_speed":
            if req.speed is not None:
                engine.set_speed(req.speed)
        elif action == "load_environment":
            if req.template:
                engine.load_environment(req.template)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action '{action}'")

        return {"status": "ok", "action": action, "sim_status": engine.status, "speed": engine.speed}

    @app.post("/api/farsverse/command")
    async def farsverse_command(req: CommandRequest):
        cmd = req.get_text()
        result = engine.execute_command(cmd)
        return result

    @app.post("/api/farsverse/teleop")
    async def farsverse_teleop(req: TeleopRequest):
        ok = engine.teleop_robot(req.robot_id, req.linear, req.angular)
        return {"status": "ok" if ok else "not_found", "robot_id": req.robot_id}

    @app.post("/api/farsverse/tasks")
    async def farsverse_create_task(req: TaskCreateRequest):
        task = engine.task_manager.create_task(
            task_type=req.task_type,
            location_node=req.location,
            priority=req.priority,
            description=req.description or f"Manual {req.task_type} at {req.location}",
            origin="manual"
        )
        if engine.status != "RUNNING":
            engine.play()
        engine.task_manager.schedule(engine.robots, engine.world, engine.events)
        engine.add_event("INFO", "task", f"Manual Task #{task.id} created for {req.location}.")
        return task.to_dict()

    @app.delete("/api/farsverse/tasks/{task_id}")
    async def farsverse_cancel_task(task_id: int):
        ok = engine.task_manager.cancel_task(task_id)
        if ok:
            engine.add_event("WARN", "task", f"Task #{task_id} was cancelled by user.")
            return {"status": "cancelled", "task_id": task_id}
        raise HTTPException(status_code=404, detail="Task not found in pending queue.")

    @app.post("/api/farsverse/obstacles")
    async def farsverse_add_obstacle(req: ObstacleRequest):
        obs = engine.world.add_obstacle(
            obs_id=req.id,
            name=req.name,
            x=req.x,
            z=req.z,
            width=req.width,
            depth=req.depth,
            active=req.active,
            desc=req.desc
        )
        engine.add_event("INFO", "world", f"Obstacle '{req.name}' updated at ({req.x:.1f}, {req.z:.1f}).")
        return obs

    @app.post("/api/farsverse/obstacles/{obs_id}/toggle")
    async def farsverse_toggle_obstacle(obs_id: str, req: ObstacleToggleRequest):
        new_state = engine.world.toggle_obstacle(obs_id, active=req.active)
        if new_state is None:
            raise HTTPException(status_code=404, detail="Obstacle not found.")
        engine.add_event("WARN" if new_state else "INFO", "world", f"Obstacle '{obs_id}' active set to {new_state}.")
        return {"id": obs_id, "active": new_state}

    @app.delete("/api/farsverse/obstacles/{obs_id}")
    async def farsverse_delete_obstacle(obs_id: str):
        ok = engine.world.remove_obstacle(obs_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Obstacle not found.")
        engine.add_event("INFO", "world", f"Obstacle '{obs_id}' removed from world.")
        return {"id": obs_id, "status": "deleted"}

    @app.post("/api/farsverse/robots/{robot_id}")
    async def farsverse_update_robot(robot_id: str, req: RobotUpdateRequest):
        for r in engine.robots:
            if r.id == robot_id:
                if req.speed is not None:
                    r.speed = max(0.5, min(8.0, req.speed))
                if req.battery is not None:
                    r.battery = max(0.0, min(100.0, req.battery))
                if req.robot_type:
                    r.robot_type = req.robot_type
                engine.add_event("INFO", "robot", f"Robot {robot_id} properties updated.")
                return r.to_dict()
        raise HTTPException(status_code=404, detail="Robot not found.")

    # ------------------------------------------------------------------
    #  Project Library & Persistence APIs
    # ------------------------------------------------------------------
    @app.get("/api/farsverse/projects")
    async def farsverse_list_projects():
        return persistence.list_projects()

    @app.get("/api/farsverse/projects/{project_id}")
    async def farsverse_get_project(project_id: str):
        proj = persistence.get_project(project_id)
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found.")
        return proj

    @app.post("/api/farsverse/projects")
    async def farsverse_save_project(req: ProjectSaveRequest):
        res = persistence.save_project(
            project_id=req.id,
            name=req.name,
            description=req.description,
            environment_type=req.environment_type,
            world_data=req.world_data,
            robot_configs=req.robot_configs,
            scenario_config=req.scenario_config
        )
        engine.add_event("INFO", "project", f"Project '{req.name}' saved to disk.")
        return res

    @app.delete("/api/farsverse/projects/{project_id}")
    async def farsverse_delete_project(project_id: str):
        ok = persistence.delete_project(project_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Project not found.")
        return {"id": project_id, "status": "deleted"}

    # ------------------------------------------------------------------
    #  Experimentation & RL Lab APIs
    # ------------------------------------------------------------------
    @app.post("/api/farsverse/experiments/run")
    async def farsverse_run_experiment(req: ExperimentRunRequest):
        bench_result = ExperimentLab.run_benchmark(
            robot_count=req.robot_count,
            num_tasks=req.num_tasks,
            environment_type=req.environment,
            seed_id=req.seed
        )
        persistence.record_experiment(bench_result)
        engine.add_event("INFO", "experiment", f"Experiment completed: {bench_result['completion_rate_percent']}% tasks in {bench_result['simulation_duration_seconds']}s.")
        return bench_result

    @app.get("/api/farsverse/experiments")
    async def farsverse_list_experiments():
        return persistence.list_experiments()

    @app.post("/api/farsverse/rl/train")
    async def farsverse_train_rl(req: RLTrainRequest):
        result = RLLaboratory.train_policy(episodes=req.episodes, learning_rate=req.learning_rate)
        engine.add_event("INFO", "rl", f"RL Training finished: {result.get('success_rate_percent', 0)}% success over {req.episodes} episodes.")
        return result

    # ------------------------------------------------------------------
    #  Asset Management & GLB Uploads
    # ------------------------------------------------------------------
    @app.get("/api/farsverse/assets")
    async def farsverse_list_assets():
        return persistence.list_assets()

    @app.post("/api/farsverse/assets/upload")
    async def farsverse_upload_asset(file: UploadFile = File(...)):
        filename = file.filename or "model.glb"
        ext = os.path.splitext(filename)[1].lower()

        # Validate file type
        if ext not in [".glb", ".gltf"]:
            raise HTTPException(status_code=400, detail="Invalid file format. Only .glb and .gltf 3D assets are supported.")

        # Safe unique filename to prevent path traversal
        safe_id = f"asset_{uuid.uuid4().hex[:8]}"
        safe_filename = f"{safe_id}_{re_sub_alphanumeric(filename)}"
        target_path = UPLOAD_DIR / safe_filename

        # Write with file size limit (50 MB)
        size = 0
        max_bytes = 50 * 1024 * 1024
        with open(target_path, "wb") as f:
            while chunk := await file.read(65536):
                size += len(chunk)
                if size > max_bytes:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="File too large (exceeds 50MB limit).")
                f.write(chunk)

        registered = persistence.register_asset(
            asset_id=safe_id,
            original_name=filename,
            filename=safe_filename,
            file_type=ext,
            file_size=size,
            storage_path=str(target_path)
        )
        engine.add_event("INFO", "asset", f"Asset '{filename}' ({size // 1024} KB) uploaded successfully.")
        return registered

    # ------------------------------------------------------------------
    #  Authoritative Real-Time WebSocket Channel
    # ------------------------------------------------------------------
    @app.websocket("/ws/farsverse")
    async def websocket_farsverse(ws: WebSocket):
        await ws.accept()

        async def _client_receiver():
            try:
                while True:
                    data = await ws.receive_json()
                    action = data.get("action", "")
                    if action == "play":
                        engine.play()
                    elif action == "pause":
                        engine.pause()
                    elif action == "stop":
                        engine.stop()
                    elif action == "reset":
                        engine.reset()
                    elif action == "step":
                        engine.step(float(data.get("seconds", 0.5)))
                    elif action == "set_speed":
                        engine.set_speed(float(data.get("speed", 1.0)))
                    elif action == "command":
                        engine.execute_command(data.get("text", ""))
                    elif action in ("teleop", "drive"):
                        engine.teleop_robot(
                            data.get("robot_id", "FARS-01"),
                            float(data.get("linear", 0.0)),
                            float(data.get("angular", 0.0))
                        )
                    elif action == "create_task":
                        engine.task_manager.create_task(
                            task_type=data.get("task_type", "assist_patient"),
                            location_node=data.get("location", "Room1"),
                            priority=int(data.get("priority", 2)),
                            description=data.get("description", ""),
                            origin="manual"
                        )
                    elif action == "cancel_task":
                        engine.task_manager.cancel_task(int(data.get("task_id", 0)))
                    elif action == "toggle_obstacle":
                        engine.world.toggle_obstacle(data.get("obs_id", ""), data.get("active"))
                    elif action == "load_environment":
                        engine.load_environment(data.get("template", "hospital"))
            except (WebSocketDisconnect, asyncio.CancelledError):
                pass

        async def _state_broadcaster():
            try:
                # Stream snapshot at ~12 Hz
                while True:
                    snapshot = engine.get_snapshot()
                    await ws.send_json(snapshot)
                    await asyncio.sleep(0.08)
            except (WebSocketDisconnect, asyncio.CancelledError):
                pass

        receiver_task = asyncio.create_task(_client_receiver())
        broadcaster_task = asyncio.create_task(_state_broadcaster())

        done, pending = await asyncio.wait(
            [receiver_task, broadcaster_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    return app


def re_sub_alphanumeric(filename: str) -> str:
    import re
    return re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
