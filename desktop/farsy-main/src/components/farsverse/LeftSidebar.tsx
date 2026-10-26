"use client";

import React, { useState } from "react";
import {
  Layers,
  Bot,
  Users,
  Building,
  ShieldAlert,
  Play,
  RotateCcw,
  Plus,
  Sliders,
  FolderOpen,
  FlaskConical,
  Brain,
  Download,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  Upload
} from "lucide-react";
import {
  FARSverseSnapshot,
  addObstacle,
  toggleObstacle,
  updateRobot,
  runExperimentBenchmark,
  trainRLPolicy,
  sendControl
} from "@/lib/farsverse-api";

interface LeftSidebarProps {
  snapshot: FARSverseSnapshot | null;
  selectedEntity: { type: string; id: string } | null;
  onSelectEntity: (type: string, id: string) => void;
  onOpenAssetUpload: () => void;
  onClose?: () => void;
}

export function LeftSidebar({
  snapshot,
  selectedEntity,
  onSelectEntity,
  onOpenAssetUpload,
  onClose,
}: LeftSidebarProps) {
  const [activeTab, setActiveTab] = useState<"hierarchy" | "builder" | "fleet" | "experiments" | "rl" | "projects">("hierarchy");
  const [hierarchyFilter, setHierarchyFilter] = useState("");

  // Hierarchy tree toggles
  const [robotsOpen, setRobotsOpen] = useState(true);
  const [humansOpen, setHumansOpen] = useState(true);
  const [roomsOpen, setRoomsOpen] = useState(true);
  const [obstaclesOpen, setObstaclesOpen] = useState(true);

  // Experiment state
  const [expRobotCount, setExpRobotCount] = useState(3);
  const [expNumTasks, setExpNumTasks] = useState(15);
  const [expLoading, setExpLoading] = useState(false);
  const [expResult, setExpResult] = useState<any>(null);

  // RL state
  const [rlEpisodes, setRlEpisodes] = useState(40);
  const [rlLoading, setRlLoading] = useState(false);
  const [rlResult, setRlResult] = useState<any>(null);

  // Filtered lists
  const filter = hierarchyFilter.toLowerCase();
  const robots = (snapshot?.robots || []).filter(
    (r) => r.id.toLowerCase().includes(filter) || r.name.toLowerCase().includes(filter)
  );
  const humans = (snapshot?.humans || []).filter(
    (h) => h.id.toLowerCase().includes(filter) || h.name.toLowerCase().includes(filter) || h.current_node.toLowerCase().includes(filter)
  );
  const rooms = (snapshot?.world?.rooms || []).filter(
    (rm) => rm.id.toLowerCase().includes(filter) || rm.name.toLowerCase().includes(filter)
  );
  const obstacles = (snapshot?.world?.obstacles || []).filter(
    (o) => o.id.toLowerCase().includes(filter) || o.name.toLowerCase().includes(filter)
  );

  const handleRunExperiment = async () => {
    setExpLoading(true);
    try {
      const res = await runExperimentBenchmark(
        expRobotCount,
        expNumTasks,
        snapshot?.world?.environment_type || "hospital"
      );
      setExpResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setExpLoading(false);
    }
  };

  const handleTrainRL = async () => {
    setRlLoading(true);
    try {
      const res = await trainRLPolicy(rlEpisodes);
      setRlResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setRlLoading(false);
    }
  };

  const handleDownloadExperimentCSV = () => {
    if (!expResult) return;
    const headers = Object.keys(expResult).join(",");
    const values = Object.values(expResult).join(",");
    const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + values;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `farsverse_experiment_${expResult.run_id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <aside className="w-72 bg-[#0c1018] border-r border-white/10 flex flex-col h-full select-none text-xs font-mono">
      {/* Sub-navigation Tabs */}
      <div className="flex items-center justify-between border-b border-white/10 bg-[#090d14] p-1 overflow-x-auto text-[11px]">
        {[
          { id: "hierarchy", label: "Scene", icon: Layers },
          { id: "builder", label: "Builder", icon: Building },
          { id: "fleet", label: "Fleet", icon: Bot },
          { id: "experiments", label: "Labs", icon: FlaskConical },
          { id: "rl", label: "RL", icon: Brain },
          { id: "projects", label: "Projects", icon: FolderOpen },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-2 py-1.5 rounded flex items-center gap-1 transition-all ${
                isActive
                  ? "bg-cyan-500/20 text-cyan-400 font-semibold border border-cyan-500/30"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* TAB 1: SCENE HIERARCHY */}
        {activeTab === "hierarchy" && (
          <div className="space-y-3">
            <input
              type="text"
              value={hierarchyFilter}
              onChange={(e) => setHierarchyFilter(e.target.value)}
              placeholder="Search objects, robots, rooms..."
              className="w-full bg-[#111622] border border-white/10 rounded px-2.5 py-1 text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-500"
            />

            {/* Robots Group */}
            <div className="border border-white/5 rounded bg-black/20">
              <button
                onClick={() => setRobotsOpen(!robotsOpen)}
                className="w-full px-2 py-1.5 flex items-center justify-between text-white/80 hover:text-white bg-white/5"
              >
                <div className="flex items-center gap-1.5">
                  <Bot className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="font-semibold">ROBOTS ({robots.length})</span>
                </div>
                {robotsOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>

              {robotsOpen && (
                <div className="p-1 space-y-0.5">
                  {robots.map((r) => {
                    const isSelected = selectedEntity?.type === "robot" && selectedEntity?.id === r.id;
                    return (
                      <div
                        key={r.id}
                        onClick={() => onSelectEntity("robot", r.id)}
                        className={`px-2 py-1 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-cyan-600/30 text-cyan-300 font-bold border border-cyan-500/50"
                            : "text-white/70 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span className={`w-1.5 h-1.5 rounded-full ${r.state === "NAVIGATING" ? "bg-cyan-400 animate-pulse" : r.state === "CHARGING" ? "bg-amber-400" : "bg-emerald-400"}`} />
                          <span className="truncate">{r.name}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px]">
                          <span className={`${r.battery > 20 ? "text-emerald-400" : "text-rose-400"}`}>
                            {Math.round(r.battery)}%
                          </span>
                          <span className="text-white/40 uppercase text-[9px]">{r.state}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Humans Group */}
            <div className="border border-white/5 rounded bg-black/20">
              <button
                onClick={() => setHumansOpen(!humansOpen)}
                className="w-full px-2 py-1.5 flex items-center justify-between text-white/80 hover:text-white bg-white/5"
              >
                <div className="flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-blue-400" />
                  <span className="font-semibold">PEOPLE & AGENTS ({humans.length})</span>
                </div>
                {humansOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>

              {humansOpen && (
                <div className="p-1 space-y-0.5 max-h-48 overflow-y-auto">
                  {humans.map((h) => {
                    const isSelected = selectedEntity?.type === "human" && selectedEntity?.id === h.id;
                    return (
                      <div
                        key={h.id}
                        onClick={() => onSelectEntity("human", h.id)}
                        className={`px-2 py-1 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-blue-600/30 text-blue-300 font-bold border border-blue-500/50"
                            : "text-white/70 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span className="text-[10px] text-white/40 uppercase">{h.agent_type[0]}</span>
                          <span className="truncate">{h.name}</span>
                        </div>
                        {h.needs_help ? (
                          <span className="text-[9px] bg-rose-950 text-rose-400 px-1 py-0.2 rounded border border-rose-800 animate-pulse font-bold">
                            HELP REQ
                          </span>
                        ) : (
                          <span className="text-white/40 text-[10px] truncate">{h.current_node}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Rooms Group */}
            <div className="border border-white/5 rounded bg-black/20">
              <button
                onClick={() => setRoomsOpen(!roomsOpen)}
                className="w-full px-2 py-1.5 flex items-center justify-between text-white/80 hover:text-white bg-white/5"
              >
                <div className="flex items-center gap-1.5">
                  <Building className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="font-semibold">ROOMS & WARDS ({rooms.length})</span>
                </div>
                {roomsOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>

              {roomsOpen && (
                <div className="p-1 space-y-0.5 max-h-48 overflow-y-auto">
                  {rooms.map((rm) => {
                    const isSelected = selectedEntity?.type === "room" && selectedEntity?.id === rm.id;
                    return (
                      <div
                        key={rm.id}
                        onClick={() => onSelectEntity("room", rm.id)}
                        className={`px-2 py-1 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-indigo-600/30 text-indigo-300 font-bold border border-indigo-500/50"
                            : "text-white/70 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <span className="truncate">{rm.name}</span>
                        <span className="text-white/40 text-[10px]">({rm.x.toFixed(0)}, {rm.z.toFixed(0)})</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Obstacles Group */}
            <div className="border border-white/5 rounded bg-black/20">
              <button
                onClick={() => setObstaclesOpen(!obstaclesOpen)}
                className="w-full px-2 py-1.5 flex items-center justify-between text-white/80 hover:text-white bg-white/5"
              >
                <div className="flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                  <span className="font-semibold">OBSTACLES ({obstacles.length})</span>
                </div>
                {obstaclesOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>

              {obstaclesOpen && (
                <div className="p-1 space-y-0.5">
                  {obstacles.map((o) => {
                    const isSelected = selectedEntity?.type === "obstacle" && selectedEntity?.id === o.id;
                    return (
                      <div
                        key={o.id}
                        onClick={() => onSelectEntity("obstacle", o.id)}
                        className={`px-2 py-1 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-amber-600/30 text-amber-300 font-bold border border-amber-500/50"
                            : "text-white/70 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <span className="truncate">{o.name}</span>
                        <span
                          className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                            o.active ? "bg-rose-950 text-rose-400 border border-rose-800" : "bg-white/10 text-white/40"
                          }`}
                        >
                          {o.active ? "ACTIVE" : "CLEARED"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: WORLD BUILDER */}
        {activeTab === "builder" && (
          <div className="space-y-4">
            <div className="text-[11px] text-white/60">
              Create, place, and toggle obstacles. The A* pathfinder dynamically reroutes around active obstacles.
            </div>

            {/* Quick Obstacle Placement */}
            <div className="border border-white/10 rounded p-2.5 bg-black/20 space-y-2">
              <div className="text-white/80 font-bold flex items-center gap-1">
                <Plus className="w-3 h-3 text-cyan-400" />
                <span>Add Corridor Obstacle</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                <button
                  onClick={() =>
                    addObstacle({
                      id: `obs_${Date.now()}`,
                      name: "Medical Equipment Cart",
                      x: -10,
                      z: 0,
                      width: 1.8,
                      depth: 1.2,
                      active: true,
                      desc: "West Corridor blockage",
                    })
                  }
                  className="p-1.5 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white text-center"
                >
                  Block West Corr
                </button>
                <button
                  onClick={() =>
                    addObstacle({
                      id: `obs_${Date.now()}`,
                      name: "Maintenance Hazard",
                      x: 10,
                      z: 0,
                      width: 1.8,
                      depth: 1.2,
                      active: true,
                      desc: "East Corridor blockage",
                    })
                  }
                  className="p-1.5 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white text-center"
                >
                  Block East Corr
                </button>
              </div>
            </div>

            {/* Active Obstacles Management */}
            <div className="space-y-1.5">
              <div className="text-white/60 text-[10px] font-bold uppercase tracking-wider">
                Current World Obstacles
              </div>
              {snapshot?.world?.obstacles.map((obs) => (
                <div key={obs.id} className="p-2 rounded bg-[#111622] border border-white/5 flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">{obs.name}</div>
                    <div className="text-[10px] text-white/40">({obs.x.toFixed(1)}, {obs.z.toFixed(1)})</div>
                  </div>
                  <button
                    onClick={() => toggleObstacle(obs.id)}
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${
                      obs.active
                        ? "bg-rose-950 text-rose-400 border-rose-800"
                        : "bg-emerald-950 text-emerald-400 border-emerald-800"
                    }`}
                  >
                    {obs.active ? "BLOCKING" : "PASSABLE"}
                  </button>
                </div>
              ))}
            </div>

            {/* Asset Import */}
            <div className="border border-white/10 rounded p-2.5 bg-black/20 space-y-2">
              <div className="text-white/80 font-bold flex items-center gap-1">
                <Upload className="w-3 h-3 text-cyan-400" />
                <span>Import 3D Asset (.glb)</span>
              </div>
              <p className="text-[10px] text-white/50">
                Upload supported .glb/.gltf 3D robot models or environment fixtures.
              </p>
              <button
                onClick={onOpenAssetUpload}
                className="w-full py-1.5 rounded bg-cyan-600/30 hover:bg-cyan-500/40 text-cyan-300 font-bold border border-cyan-500/40"
              >
                Upload Model
              </button>
            </div>
          </div>
        )}

        {/* TAB 3: FLEET STUDIO */}
        {activeTab === "fleet" && (
          <div className="space-y-4">
            <div className="text-[11px] text-white/60">
              Configure robot fleet parameters. Updates immediately propagate to the authoritative simulation.
            </div>

            {snapshot?.robots.map((robot) => (
              <div key={robot.id} className="border border-white/10 rounded p-2.5 bg-[#111622] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-white flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    <span>{robot.name}</span>
                    <span className="text-[10px] text-white/40">({robot.id})</span>
                  </div>
                  <span className="text-[10px] uppercase text-cyan-400">{robot.state}</span>
                </div>

                {/* Speed Slider */}
                <div>
                  <div className="flex justify-between text-[10px] text-white/60 mb-1">
                    <span>Speed: {robot.speed} m/s</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="4.0"
                    step="0.1"
                    value={robot.speed}
                    onChange={(e) => updateRobot(robot.id, { speed: parseFloat(e.target.value) })}
                    className="w-full accent-cyan-400"
                  />
                </div>

                {/* Battery Recharge Action */}
                <div className="flex items-center justify-between pt-1">
                  <div className="text-[10px] text-emerald-400 font-semibold">
                    Battery: {Math.round(robot.battery)}%
                  </div>
                  <button
                    onClick={() => updateRobot(robot.id, { battery: 100.0 })}
                    className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] hover:bg-emerald-900"
                  >
                    Set 100%
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 4: EXPERIMENTS LAB */}
        {activeTab === "experiments" && (
          <div className="space-y-4">
            <div className="text-[11px] text-white/60">
              Run comparative benchmark simulations. Evaluates fleet throughput, travel distance, and response times.
            </div>

            <div className="border border-white/10 rounded p-3 bg-[#111622] space-y-3">
              <div className="font-bold text-white">Configure Benchmark Run</div>

              <div>
                <label className="text-[10px] text-white/60 block mb-1">Fleet Size: {expRobotCount} Robots</label>
                <div className="flex gap-2">
                  {[1, 3, 5].map((cnt) => (
                    <button
                      key={cnt}
                      onClick={() => setExpRobotCount(cnt)}
                      className={`flex-1 py-1 rounded text-xs border ${
                        expRobotCount === cnt
                          ? "bg-cyan-500/20 text-cyan-400 border-cyan-500 font-bold"
                          : "bg-white/5 text-white/50 border-white/10"
                      }`}
                    >
                      {cnt} {cnt === 1 ? "Robot" : "Robots"}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[10px] text-white/60 block mb-1">Task Workload: {expNumTasks} Tasks</label>
                <select
                  value={expNumTasks}
                  onChange={(e) => setExpNumTasks(parseInt(e.target.value))}
                  className="w-full bg-[#0a0d14] border border-white/10 rounded p-1.5 text-xs text-white"
                >
                  <option value={10}>10 Clinical Tasks (Quick)</option>
                  <option value={15}>15 Clinical Tasks (Standard)</option>
                  <option value={25}>25 Clinical Tasks (Stress Test)</option>
                </select>
              </div>

              <button
                onClick={handleRunExperiment}
                disabled={expLoading}
                className="w-full py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all disabled:opacity-50"
              >
                {expLoading ? "Running Simulation Run..." : "Execute Experiment Run"}
              </button>
            </div>

            {/* Experiment Results */}
            {expResult && (
              <div className="border border-emerald-500/30 rounded p-3 bg-emerald-950/20 space-y-2">
                <div className="flex items-center justify-between text-emerald-400 font-bold">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Run Completed</span>
                  </span>
                  <button
                    onClick={handleDownloadExperimentCSV}
                    title="Export CSV"
                    className="flex items-center gap-1 text-[10px] bg-emerald-900/60 px-2 py-0.5 rounded text-white hover:bg-emerald-800"
                  >
                    <Download className="w-3 h-3" />
                    <span>CSV</span>
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                  <div className="bg-black/30 p-2 rounded">
                    <div className="text-white/40">Completion Rate</div>
                    <div className="text-emerald-400 font-bold text-sm">{expResult.completion_rate_percent}%</div>
                  </div>
                  <div className="bg-black/30 p-2 rounded">
                    <div className="text-white/40">Avg Response Time</div>
                    <div className="text-white font-bold text-sm">{expResult.avg_response_time_seconds}s</div>
                  </div>
                  <div className="bg-black/30 p-2 rounded">
                    <div className="text-white/40">Total Distance</div>
                    <div className="text-white font-bold text-sm">{expResult.total_distance_meters}m</div>
                  </div>
                  <div className="bg-black/30 p-2 rounded">
                    <div className="text-white/40">Battery Consumed</div>
                    <div className="text-white font-bold text-sm">{expResult.battery_consumed_percent}%</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: RL LAB */}
        {activeTab === "rl" && (
          <div className="space-y-4">
            <div className="text-[11px] text-white/60">
              Train an authentic Gymnasium grid navigation environment and evaluate against classical A* pathfinding.
            </div>

            <div className="border border-white/10 rounded p-3 bg-[#111622] space-y-3">
              <div className="font-bold text-white flex items-center gap-1.5">
                <Brain className="w-4 h-4 text-purple-400" />
                <span>Gymnasium RL Policy</span>
              </div>

              <div>
                <label className="text-[10px] text-white/60 block mb-1">Training Episodes: {rlEpisodes}</label>
                <input
                  type="range"
                  min="20"
                  max="100"
                  step="10"
                  value={rlEpisodes}
                  onChange={(e) => setRlEpisodes(parseInt(e.target.value))}
                  className="w-full accent-purple-400"
                />
              </div>

              <button
                onClick={handleTrainRL}
                disabled={rlLoading}
                className="w-full py-2 rounded bg-purple-600 hover:bg-purple-500 text-white font-bold transition-all disabled:opacity-50"
              >
                {rlLoading ? "Training Neural Policy..." : "Train Policy Network"}
              </button>
            </div>

            {rlResult && (
              <div className="border border-purple-500/30 rounded p-3 bg-purple-950/20 space-y-2">
                <div className="text-purple-400 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Training Results</span>
                </div>
                <div className="space-y-1.5 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-white/60">Success Rate:</span>
                    <span className="font-bold text-purple-300">{rlResult.success_rate_percent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Final Avg Reward:</span>
                    <span className="font-bold text-white">{rlResult.final_avg_reward}</span>
                  </div>
                  <div className="border-t border-white/10 pt-1.5">
                    <div className="text-white/40 text-[10px] uppercase">A* Baseline Comparison:</div>
                    <div className="flex justify-between pt-0.5">
                      <span className="text-white/60">Policy Avg Steps:</span>
                      <span className="text-white font-bold">{rlResult.baseline_comparison.policy_avg_steps}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">A* Optimal Steps:</span>
                      <span className="text-cyan-400 font-bold">{rlResult.baseline_comparison.astar_baseline_steps}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: PROJECTS LIBRARY */}
        {activeTab === "projects" && (
          <div className="space-y-3">
            <div className="text-[11px] text-white/60">
              Select an environment template or restore saved project states.
            </div>

            <div className="space-y-2">
              {[
                { id: "hospital", title: "Hospital Digital Twin", desc: "20 patient rooms, ICU, ER, pharmacy" },
                { id: "campus", title: "Campus Quad", desc: "Plaza, science library, labs, cafeteria" },
                { id: "warehouse", title: "Logistics Fulfillment", desc: "Docks, storage aisles, packing cell" },
                { id: "empty", title: "Sandbox Workspace", desc: "Blank environment for custom layouts" },
              ].map((tmpl) => (
                <div
                  key={tmpl.id}
                  onClick={() => sendControl("load_environment", { template: tmpl.id })}
                  className="p-2.5 rounded bg-[#111622] hover:bg-cyan-950/40 border border-white/10 hover:border-cyan-500/50 cursor-pointer transition-all"
                >
                  <div className="font-bold text-white">{tmpl.title}</div>
                  <div className="text-[10px] text-white/50 mt-0.5">{tmpl.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
