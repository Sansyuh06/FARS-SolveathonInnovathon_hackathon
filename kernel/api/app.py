"""FastAPI admin API and web dashboard for FARS."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


class CommandRequest(BaseModel):
    text: str


class VoiceRequest(BaseModel):
    text: str


class ScanRequest(BaseModel):
    location: str = "Entrance"


def create_app(db, analytics, access, device_hub, bus, state) -> FastAPI:
    app = FastAPI(title="FARS Platform", version="1.0.0")

    if WEB_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/")
    async def index():
        index_path = WEB_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "FARS API running. Place web/static/index.html for dashboard."}

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "platform": "FARS", "simulation_running": state.running}

    @app.get("/api/analytics")
    async def get_analytics():
        return analytics.dashboard_payload()

    @app.get("/api/students")
    async def list_students():
        return db.list_students()

    @app.get("/api/attendance")
    async def attendance():
        return db.recent_attendance()

    @app.get("/api/access")
    async def access_log():
        return db.recent_access()

    @app.get("/api/devices")
    async def devices():
        return db.list_devices()

    @app.get("/api/events")
    async def events():
        return db.recent_events()

    @app.post("/api/scan")
    async def manual_scan(req: ScanRequest):
        return device_hub.trigger_manual_scan(req.location)

    @app.post("/api/command")
    async def post_command(req: CommandRequest):
        from fars_platform.simulation_bridge import parse_and_enqueue_command

        ok = parse_and_enqueue_command(req.text)
        return {"ok": ok, "command": req.text}

    @app.post("/api/voice")
    async def voice_command(req: VoiceRequest):
        from fars_platform.simulation_bridge import parse_and_enqueue_command

        state.add_voice_command(req.text)
        ok = parse_and_enqueue_command(req.text)
        bus.publish("voice_command", text=req.text)
        return {"ok": ok, "text": req.text}

    @app.websocket("/ws/live")
    async def websocket_live(ws: WebSocket):
        await ws.accept()
        try:
            import asyncio

            while True:
                payload = analytics.dashboard_payload()
                await ws.send_json(payload)
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            pass

    @app.websocket("/ws/rl")
    async def websocket_rl(ws: WebSocket):
        await ws.accept()
        try:
            import asyncio
            import random
            
            episode = 45000
            while True:
                # Simulate active RL learning telemetry
                payload = {
                    "episode": episode,
                    "reward": round(random.uniform(800, 850), 2),
                    "loss": round(random.uniform(0.01, 0.05), 4),
                    "gait_stability": round(random.uniform(95, 99), 1)
                }
                episode += 1
                await ws.send_json(payload)
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            pass

    return app
