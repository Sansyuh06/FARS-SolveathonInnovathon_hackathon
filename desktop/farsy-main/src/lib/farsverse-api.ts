/**
 * FARSverse Client API & WebSocket Manager
 * Provides reliable real-time state synchronization and REST communication with the backend.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8080";
export const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8080/ws/farsverse";

export interface FARSverseSnapshot {
  status: "IDLE" | "RUNNING" | "PAUSED" | "STOPPED";
  sim_time: number;
  speed: number;
  world: {
    name: string;
    environment_type: string;
    nodes: Record<string, [number, number]>;
    edges: [string, string][];
    rooms: Array<{
      id: string;
      name: string;
      type: string;
      x: number;
      z: number;
      width: number;
      depth: number;
      color: string;
    }>;
    obstacles: Array<{
      id: string;
      name: string;
      x: number;
      z: number;
      width: number;
      depth: number;
      active: boolean;
      desc?: string;
    }>;
    charging_dock: [number, number];
  };
  robots: Array<{
    id: string;
    name: string;
    robot_type: string;
    x: number;
    y: number;
    z: number;
    rotation_y: number;
    speed: number;
    total_distance: number;
    battery: number;
    battery_capacity: number;
    state: string;
    current_task: any;
    target_node: string | null;
    destination_name: string;
    waypoints: [number, number][];
    waypoint_index: number;
    ultrasonic_distance: number;
    detected_obstacles: string[];
    decision_trace: string;
    history: Array<{
      task: any;
      completed_at: number;
      destination: string;
      status: string;
    }>;
  }>;
  humans: Array<{
    id: string;
    name: string;
    agent_type: string;
    home_node: string;
    current_node: string;
    x: number;
    z: number;
    needs_help: boolean;
    help_request_type: string | null;
    assisted_by_robot: string | null;
    status: string;
  }>;
  tasks: {
    pending: any[];
    active: any[];
    completed: any[];
    failed: any[];
    metrics: {
      pending_tasks: number;
      active_tasks: number;
      completed_tasks: number;
      failed_tasks: number;
      avg_response_time_seconds: number;
    };
  };
  events: Array<{
    id: number;
    timestamp: number;
    sim_time: number;
    severity: "INFO" | "WARN" | "ERROR";
    category: string;
    message: string;
  }>;
  metrics_history: Array<{
    sim_time: number;
    active_robots: number;
    idle_robots: number;
    charging_robots: number;
    avg_battery: number;
    total_distance: number;
    completed_tasks: number;
    pending_tasks: number;
    avg_response_time: number;
  }>;
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export class FARSverseClient {
  private ws: WebSocket | null = null;
  private statusCallback: (status: ConnectionStatus) => void = () => {};
  private snapshotCallback: (snap: FARSverseSnapshot) => void = () => {};
  private reconnectTimer: any = null;
  private isDestroyed: boolean = false;

  constructor(
    onSnapshot: (snap: FARSverseSnapshot) => void,
    onStatusChange: (status: ConnectionStatus) => void
  ) {
    this.snapshotCallback = onSnapshot;
    this.statusCallback = onStatusChange;
    this.connect();
  }

  public connect(): void {
    if (this.isDestroyed) return;
    this.statusCallback("connecting");

    try {
      this.ws = new WebSocket(WS_BASE);

      this.ws.onopen = () => {
        this.statusCallback("connected");
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const snapshot = JSON.parse(event.data) as FARSverseSnapshot;
          this.snapshotCallback(snapshot);
        } catch (e) {
          console.error("[FARSverse WS] Parse error:", e);
        }
      };

      this.ws.onclose = () => {
        this.statusCallback("disconnected");
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.statusCallback("error");
        this.scheduleReconnect();
      };
    } catch (e) {
      this.statusCallback("error");
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.isDestroyed || this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2000);
  }

  public send(action: string, payload: Record<string, any> = {}): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action, ...payload }));
    }
  }

  public destroy(): void {
    this.isDestroyed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// ------------------------------------------------------------------
//  REST API Helpers
// ------------------------------------------------------------------
export async function sendControl(action: string, extra: Record<string, any> = {}) {
  const res = await fetch(`${API_BASE}/api/farsverse/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...extra }),
  });
  return res.json();
}

export async function sendNaturalCommand(text: string) {
  const res = await fetch(`${API_BASE}/api/farsverse/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return res.json();
}

export async function createManualTask(taskType: string, location: string, priority: number = 2, desc: string = "") {
  const res = await fetch(`${API_BASE}/api/farsverse/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_type: taskType, location, priority, description: desc }),
  });
  return res.json();
}

export async function cancelTask(taskId: number) {
  const res = await fetch(`${API_BASE}/api/farsverse/tasks/${taskId}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function addObstacle(obs: { id: string; name: string; x: number; z: number; width?: number; depth?: number; active?: boolean; desc?: string }) {
  const res = await fetch(`${API_BASE}/api/farsverse/obstacles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obs),
  });
  return res.json();
}

export async function toggleObstacle(obsId: string, active?: boolean) {
  const res = await fetch(`${API_BASE}/api/farsverse/obstacles/${obsId}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ active }),
  });
  return res.json();
}

export async function deleteObstacle(obsId: string) {
  const res = await fetch(`${API_BASE}/api/farsverse/obstacles/${obsId}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function updateRobot(robotId: string, data: { speed?: number; battery?: number; robot_type?: string }) {
  const res = await fetch(`${API_BASE}/api/farsverse/robots/${robotId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function listProjects() {
  const res = await fetch(`${API_BASE}/api/farsverse/projects`);
  return res.json();
}

export async function getProject(id: string) {
  const res = await fetch(`${API_BASE}/api/farsverse/projects/${id}`);
  return res.json();
}

export async function saveProject(project: { id: string; name: string; description?: string; environment_type: string; world_data?: any; robot_configs?: any[]; scenario_config?: any }) {
  const res = await fetch(`${API_BASE}/api/farsverse/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project),
  });
  return res.json();
}

export async function deleteProject(id: string) {
  const res = await fetch(`${API_BASE}/api/farsverse/projects/${id}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function runExperimentBenchmark(robotCount: number = 3, numTasks: number = 15, env: string = "hospital", seed: number = 42) {
  const res = await fetch(`${API_BASE}/api/farsverse/experiments/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ robot_count: robotCount, num_tasks: numTasks, environment: env, seed }),
  });
  return res.json();
}

export async function listExperiments() {
  const res = await fetch(`${API_BASE}/api/farsverse/experiments`);
  return res.json();
}

export async function trainRLPolicy(episodes: number = 40, lr: number = 0.01) {
  const res = await fetch(`${API_BASE}/api/farsverse/rl/train`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ episodes, learning_rate: lr }),
  });
  return res.json();
}

export async function uploadAssetFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/farsverse/assets/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function listAssets() {
  const res = await fetch(`${API_BASE}/api/farsverse/assets`);
  return res.json();
}
