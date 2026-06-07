import asyncio
import json
import time
import threading
import websockets

from sim_agents import RobotAgent, HumanAgent
from sim_tasks import TaskManager
import sim_llm
from sim_navigation import get_all_room_nodes

class SimulationServer:
    def __init__(self):
        self.robots = [RobotAgent(i) for i in range(5)]
        self.humans = []
        
        rooms = get_all_room_nodes()
        for i in range(15):
            self.humans.append(HumanAgent('patient', rooms[i % len(rooms)]))
        for _ in range(6):
            self.humans.append(HumanAgent('doctor'))
        for _ in range(6):
            self.humans.append(HumanAgent('nurse'))
        for _ in range(6):
            self.humans.append(HumanAgent('visitor'))
            
        self.task_manager = TaskManager()
        self.running = True
        self.clients = set()
        self.state_lock = threading.Lock()
        self.alerts = []
        self.sim_time = 0.0
        
    def add_alert(self, msg):
        self.alerts.append(msg)
        if len(self.alerts) > 10:
            self.alerts.pop(0)

    def simulation_loop(self):
        print("[FARS SIMULATION] Starting simulation loop (60 Hz)...")
        last_time = time.time()
        while self.running:
            now = time.time()
            dt = now - last_time
            last_time = now
            
            with self.state_lock:
                self.sim_time += dt
                for h in self.humans:
                    h.update(dt)
                
                self.task_manager.auto_generate_from_humans(self.humans, dt)
                self.task_manager.assign_tasks(self.robots)
                
                for r in self.robots:
                    r.update(dt)
                    
                completed = self.task_manager.check_completed(self.robots)
                for t in completed:
                    for h in self.humans:
                        if h.current_node == t.location_node and h.needs_help:
                            h.fulfill_help()
                            break
                    self.add_alert(f"[DONE] {t.task_type} @ {t.location_node}")
                            
                results = sim_llm.poll_results()
                for res in results:
                    self.task_manager.create_task(
                        res['task_type'],
                        res['location_node'],
                        res['priority'],
                        res['description']
                    )
                    self.add_alert(f"[AI] {res['task_type']} -> {res['location_node']}")
            
            time.sleep(max(0, (1.0 / 60.0) - (time.time() - now)))

    def get_state(self):
        with self.state_lock:
            # Format task data
            tasks_data = []
            for t in self.task_manager.task_queue:
                tasks_data.append({
                    'id': t.id,
                    'task_type': t.task_type,
                    'location_node': t.location_node,
                    'priority': t.priority,
                    'status': t.status
                })
            for t in self.task_manager.active_tasks.values():
                tasks_data.append({
                    'id': t.id,
                    'task_type': t.task_type,
                    'location_node': t.location_node,
                    'priority': t.priority,
                    'status': t.status
                })
                
            metrics_data = self.task_manager.get_metrics()
            
            return {
                "type": "state",
                "robots": [r.get_state_dict() for r in self.robots],
                "humans": [h.get_state_dict() for h in self.humans],
                "tasks": tasks_data,
                "metrics": metrics_data,
                "alerts": self.alerts,
                "sim_time": self.sim_time,
                "llm_model": sim_llm.get_model_name()
            }

    async def broadcast_state(self):
        print("[FARS SIMULATION] Starting state broadcast (20 Hz)...")
        while self.running:
            if self.clients:
                state = self.get_state()
                msg = json.dumps(state)
                websockets.broadcast(self.clients, msg)
            await asyncio.sleep(1.0 / 20.0)

    async def handler(self, websocket):
        self.clients.add(websocket)
        print(f"[WS] Client connected. Total: {len(self.clients)}")
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "command":
                    sim_llm.submit_command(data["text"])
                elif data.get("type") == "create_task":
                    with self.state_lock:
                        self.task_manager.create_task(
                            data["task_type"],
                            data["location"],
                            data.get("priority", 1),
                            data.get("description", "Manual task")
                        )
        except Exception as e:
            print(f"[WS] Error: {e}")
        finally:
            self.clients.remove(websocket)
            print(f"[WS] Client disconnected. Total: {len(self.clients)}")

    async def serve(self):
        print("[FARS SIMULATION] Starting WebSocket server on port 8765...")
        async with websockets.serve(self.handler, "localhost", 8765):
            await self.broadcast_state()

def main():
    print("=========================================")
    print(" FARS DIGITAL TWIN - PYTHON BACKEND LIVE ")
    print("=========================================")
    print(f" LLM Configured: {sim_llm.get_model_name()}")
    
    server = SimulationServer()
    
    sim_thread = threading.Thread(target=server.simulation_loop, daemon=True)
    sim_thread.start()
    
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("Shutting down...")
        server.running = False

if __name__ == "__main__":
    main()
