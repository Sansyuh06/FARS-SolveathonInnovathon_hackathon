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
  const [activeTab, setActiveTab] = useState<"stage" | "rl" | "experiments" | "projects">("stage");
  const [hierarchyFilter, setHierarchyFilter] = useState("");

  const [robotsOpen, setRobotsOpen] = useState(true);
  const [humansOpen, setHumansOpen] = useState(true);
  const [roomsOpen, setRoomsOpen] = useState(true);
  const [obstaclesOpen, setObstaclesOpen] = useState(true);

  // Experiment state
  const [expRobotCount, setExpRobotCount] = useState(3);
  const [expNumTasks, setExpNumTasks] = useState(15);
  const [expLoading, setExpLoading] = useState(false);
  const [expResult, setExpResult] = useState<any>(null);

  // RL Training state
  const [rlEpisodes, setRlEpisodes] = useState(40);
  const [rlLoading, setRlLoading] = useState(false);
  const [rlResult, setRlResult] = useState<any>(null);

  const filter = hierarchyFilter.toLowerCase();
  const robots = (snapshot?.robots || []).filter(
    (r) => r.id.toLowerCase().includes(filter) || r.name.toLowerCase().includes(filter)
  );
  const humans = (snapshot?.humans || []).filter(
    (h) => h.id.toLowerCase().includes(filter) || h.name.toLowerCase().includes(filter)
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
    <aside className="w-80 bg-[#09090b] border-r border-[#27272a] flex flex-col h-full select-none text-xs font-mono text-[#f4f4f5]">
      {/* Tab Switcher */}
      <div className="flex items-center justify-between border-b border-[#27272a] bg-[#000000] p-1 text-[11px]">
        {[
          { id: "stage", label: "USD Stage", icon: Layers },
          { id: "rl", label: "RL Training", icon: Brain },
          { id: "experiments", label: "Benchmark", icon: FlaskConical },
          { id: "projects", label: "Projects", icon: FolderOpen },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-2 py-1 rounded flex items-center gap-1.5 transition-all ${
                isActive
                  ? "bg-[#27272a] text-[#ffffff] font-bold border border-[#3f3f46]"
                  : "text-[#71717a] hover:text-white"
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* TAB 1: USD STAGE HIERARCHY */}
        {activeTab === "stage" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[10px] text-[#71717a] border-b border-[#27272a] pb-1 uppercase tracking-wider">
              <span>Stage Prims</span>
              <span>Type</span>
            </div>

            <input
              type="text"
              value={hierarchyFilter}
              onChange={(e) => setHierarchyFilter(e.target.value)}
              placeholder="Filter Prims (e.g. /World/Robots)..."
              className="w-full bg-[#000000] border border-[#27272a] rounded px-2.5 py-1 text-xs text-white placeholder:text-[#52525b] focus:outline-none focus:border-white"
            />

            {/* /World Root Scope */}
            <div className="text-[11px] font-bold text-white flex items-center gap-1.5 pt-1">
              <span className="text-[#71717a]">/</span>
              <span>World</span>
              <span className="text-[#52525b] text-[9px] font-normal ml-auto">Xform</span>
            </div>

            {/* Robots Scope */}
            <div className="border border-[#18181b] rounded bg-[#000000]">
              <button
                onClick={() => setRobotsOpen(!robotsOpen)}
                className="w-full px-2 py-1 flex items-center justify-between text-white/90 hover:text-white bg-[#121214] text-[11px]"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[#71717a]">└</span>
                  <span className="font-semibold">Robots ({robots.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#71717a]">
                  <span>Scope</span>
                  {robotsOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </div>
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
                            ? "bg-white text-black font-bold"
                            : "text-[#a1a1aa] hover:bg-[#18181b] hover:text-white"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? "bg-black" : "bg-white"}`} />
                          <span className="truncate">{r.name} [{r.id}]</span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px]">
                          <span>{Math.round(r.battery)}%</span>
                          <span className="uppercase text-[9px] opacity-70">{r.state}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Rooms Scope */}
            <div className="border border-[#18181b] rounded bg-[#000000]">
              <button
                onClick={() => setRoomsOpen(!roomsOpen)}
                className="w-full px-2 py-1 flex items-center justify-between text-white/90 hover:text-white bg-[#121214] text-[11px]"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[#71717a]">└</span>
                  <span className="font-semibold">Environment ({rooms.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#71717a]">
                  <span>Scope</span>
                  {roomsOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </div>
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
                            ? "bg-white text-black font-bold"
                            : "text-[#a1a1aa] hover:bg-[#18181b] hover:text-white"
                        }`}
                      >
                        <span className="truncate">{rm.name}</span>
                        <span className="text-[10px] opacity-60 uppercase">{rm.type}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Obstacles Scope */}
            <div className="border border-[#18181b] rounded bg-[#000000]">
              <button
                onClick={() => setObstaclesOpen(!obstaclesOpen)}
                className="w-full px-2 py-1 flex items-center justify-between text-white/90 hover:text-white bg-[#121214] text-[11px]"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[#71717a]">└</span>
                  <span className="font-semibold">Obstacles ({obstacles.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#71717a]">
                  <span>Scope</span>
                  {obstaclesOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </div>
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
                            ? "bg-white text-black font-bold"
                            : "text-[#a1a1aa] hover:bg-[#18181b] hover:text-white"
                        }`}
                      >
                        <span className="truncate">{o.name}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleObstacle(o.id, !o.active);
                          }}
                          className={`text-[9px] px-1.5 py-0.5 rounded border ${
                            o.active ? "bg-white text-black font-bold border-white" : "text-[#71717a] border-[#27272a]"
                          }`}
                        >
                          {o.active ? "BLOCKING" : "CLEAR"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Humans Scope */}
            <div className="border border-[#18181b] rounded bg-[#000000]">
              <button
                onClick={() => setHumansOpen(!humansOpen)}
                className="w-full px-2 py-1 flex items-center justify-between text-white/90 hover:text-white bg-[#121214] text-[11px]"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[#71717a]">└</span>
                  <span className="font-semibold">Agents / Avatars ({humans.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#71717a]">
                  <span>Scope</span>
                  {humansOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </div>
              </button>

              {humansOpen && (
                <div className="p-1 space-y-0.5 max-h-40 overflow-y-auto">
                  {humans.map((h) => {
                    const isSelected = selectedEntity?.type === "human" && selectedEntity?.id === h.id;
                    return (
                      <div
                        key={h.id}
                        onClick={() => onSelectEntity("human", h.id)}
                        className={`px-2 py-1 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-white text-black font-bold"
                            : "text-[#a1a1aa] hover:bg-[#18181b] hover:text-white"
                        }`}
                      >
                        <span className="truncate">{h.name}</span>
                        <span className="text-[10px] opacity-60 uppercase">{h.agent_type}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: RL TRAINING STUDIO */}
        {activeTab === "rl" && (
          <div className="space-y-4">
            <div className="text-[11px] text-[#a1a1aa]">
              Reinforcement learning simulation training in Gymnasium with PyTorch CUDA acceleration.
            </div>

            <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-3">
              <div className="font-bold text-white flex items-center gap-1.5">
                <Brain className="w-4 h-4 text-white" />
                <span>Gymnasium Navigation DQN</span>
              </div>

              <div>
                <label className="text-[10px] text-[#71717a] block mb-1">Training Episodes: {rlEpisodes}</label>
                <input
                  type="range"
                  min="20"
                  max="100"
                  step="10"
                  value={rlEpisodes}
                  onChange={(e) => setRlEpisodes(parseInt(e.target.value))}
                  className="w-full accent-white"
                />
              </div>

              <button
                onClick={handleTrainRL}
                disabled={rlLoading}
                className="w-full py-2 rounded bg-white hover:bg-[#e4e4e7] text-black font-bold transition-all disabled:opacity-50"
              >
                {rlLoading ? "Training Policy Network (CUDA)..." : "Start Training Session"}
              </button>
            </div>

            {rlResult && (
              <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-2">
                <div className="text-white font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Session Results</span>
                </div>
                <div className="space-y-1.5 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#a1a1aa]">Success Rate:</span>
                    <span className="font-bold text-white">{rlResult.success_rate_percent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#a1a1aa]">Final Avg Reward:</span>
                    <span className="font-bold text-white">{rlResult.final_avg_reward}</span>
                  </div>
                  <div className="border-t border-[#27272a] pt-1.5">
                    <div className="text-[#71717a] text-[10px] uppercase">A* Benchmark Comparison:</div>
                    <div className="flex justify-between pt-0.5">
                      <span className="text-[#a1a1aa]">Policy Avg Steps:</span>
                      <span className="text-white font-bold">{rlResult.baseline_comparison.policy_avg_steps}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#a1a1aa]">A* Optimal Steps:</span>
                      <span className="text-white font-bold">{rlResult.baseline_comparison.astar_baseline_steps}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: BENCHMARK LAB */}
        {activeTab === "experiments" && (
          <div className="space-y-4">
            <div className="text-[11px] text-[#a1a1aa]">
              Monte Carlo Fleet Throughput & Stress Testing Benchmark.
            </div>

            <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-3">
              <div>
                <label className="text-[10px] text-[#71717a] block mb-1">Fleet Configuration:</label>
                <div className="flex gap-2">
                  {[1, 3, 5].map((cnt) => (
                    <button
                      key={cnt}
                      onClick={() => setExpRobotCount(cnt)}
                      className={`flex-1 py-1 rounded text-xs border ${
                        expRobotCount === cnt
                          ? "bg-white text-black border-white font-bold"
                          : "bg-[#18181b] text-[#71717a] border-[#27272a]"
                      }`}
                    >
                      {cnt} AMR
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[10px] text-[#71717a] block mb-1">Task Workload: {expNumTasks} Tasks</label>
                <select
                  value={expNumTasks}
                  onChange={(e) => setExpNumTasks(parseInt(e.target.value))}
                  className="w-full bg-[#000000] border border-[#27272a] rounded p-1.5 text-xs text-white"
                >
                  <option value={10}>10 Clinical Tasks (Quick)</option>
                  <option value={15}>15 Clinical Tasks (Standard)</option>
                  <option value={25}>25 Clinical Tasks (Stress Test)</option>
                </select>
              </div>

              <button
                onClick={handleRunExperiment}
                disabled={expLoading}
                className="w-full py-2 rounded bg-white hover:bg-[#e4e4e7] text-black font-bold transition-all disabled:opacity-50"
              >
                {expLoading ? "Executing Simulation Run..." : "Run Benchmark Run"}
              </button>
            </div>

            {expResult && (
              <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-2">
                <div className="flex items-center justify-between text-white font-bold">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Run Complete</span>
                  </span>
                  <button
                    onClick={handleDownloadExperimentCSV}
                    title="Export CSV"
                    className="flex items-center gap-1 text-[10px] bg-[#27272a] px-2 py-0.5 rounded text-white hover:bg-[#3f3f46]"
                  >
                    <Download className="w-3 h-3" />
                    <span>CSV</span>
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                  <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                    <div className="text-[#71717a]">Completion Rate</div>
                    <div className="text-white font-bold text-sm">{expResult.completion_rate_percent}%</div>
                  </div>
                  <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                    <div className="text-[#71717a]">Avg Response</div>
                    <div className="text-white font-bold text-sm">{expResult.avg_response_time_seconds}s</div>
                  </div>
                  <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                    <div className="text-[#71717a]">Total Distance</div>
                    <div className="text-white font-bold text-sm">{expResult.total_distance_meters}m</div>
                  </div>
                  <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                    <div className="text-[#71717a]">Battery Consumed</div>
                    <div className="text-white font-bold text-sm">{expResult.battery_consumed_percent}%</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: PROJECTS */}
        {activeTab === "projects" && (
          <div className="space-y-3">
            <div className="text-[11px] text-[#a1a1aa]">
              USD Environment Templates and Stage Checkpoints.
            </div>

            <div className="space-y-2">
              {[
                { id: "hospital", name: "Hospital Digital Twin", desc: "Corridors, ICUs, Patient Rooms, Pharmacy" },
                { id: "warehouse", name: "Logistics Warehouse", desc: "Pallet racking, sorting bays, loading docks" },
                { id: "office", name: "Corporate Campus", desc: "Cubicles, conference rooms, reception hall" },
              ].map((env) => (
                <div
                  key={env.id}
                  className="border border-[#27272a] rounded p-2.5 bg-[#000000] hover:border-white transition-all cursor-pointer"
                  onClick={() => sendControl("load_environment", { template: env.id })}
                >
                  <div className="font-bold text-white text-[11px]">{env.name}</div>
                  <div className="text-[10px] text-[#71717a] mt-0.5">{env.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
