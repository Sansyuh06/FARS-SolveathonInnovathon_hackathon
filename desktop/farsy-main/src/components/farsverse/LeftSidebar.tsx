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
  Upload,
  Radio,
  Activity
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
  const [activeTab, setActiveTab] = useState<"stage" | "fleet" | "rl" | "projects">("stage");
  const [hierarchyFilter, setHierarchyFilter] = useState("");

  const [robotsOpen, setRobotsOpen] = useState(true);
  const [humansOpen, setHumansOpen] = useState(true);
  const [roomsOpen, setRoomsOpen] = useState(true);
  const [obstaclesOpen, setObstaclesOpen] = useState(true);

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

  return (
    <aside className="w-80 bg-[#0a0c10] border-r border-[#222634] flex flex-col h-full select-none text-xs font-mono text-[#f4f4f5]">
      {/* Sub-navigation Tabs */}
      <div className="flex items-center justify-between border-b border-[#222634] bg-[#050608] p-1 text-[11px]">
        {[
          { id: "stage", label: "Hierarchy", icon: Layers },
          { id: "fleet", label: "Fleet Telemetry", icon: Bot },
          { id: "rl", label: "RL Training", icon: Brain },
          { id: "projects", label: "Environments", icon: FolderOpen },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-2.5 py-1.5 rounded flex items-center gap-1.5 transition-all font-semibold ${
                isActive
                  ? "bg-white text-black font-bold shadow-sm"
                  : "text-[#94a3b8] hover:text-white hover:bg-[#141722]"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* TAB 1: STAGE HIERARCHY */}
        {activeTab === "stage" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[10px] text-[#64748b] border-b border-[#222634] pb-1 uppercase tracking-wider font-bold">
              <span>Scene Prims</span>
              <span>Classification</span>
            </div>

            <input
              type="text"
              value={hierarchyFilter}
              onChange={(e) => setHierarchyFilter(e.target.value)}
              placeholder="Search Prims (/World/Robots)..."
              className="w-full bg-[#050608] border border-[#222634] rounded px-3 py-1.5 text-xs text-white placeholder:text-[#475569] focus:outline-none focus:border-white transition-all"
            />

            {/* /World Root Scope */}
            <div className="text-[11px] font-bold text-white flex items-center gap-1.5 pt-1">
              <span className="text-[#64748b]">/</span>
              <span>World</span>
              <span className="text-[#64748b] text-[9px] font-normal ml-auto">Xform</span>
            </div>

            {/* Robots Scope */}
            <div className="border border-[#181a22] rounded bg-[#050608]">
              <button
                onClick={() => setRobotsOpen(!robotsOpen)}
                className="w-full px-2.5 py-1.5 flex items-center justify-between text-white hover:bg-[#141722] text-[11px] font-bold"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[#64748b]">└</span>
                  <span>FARS AMR Fleet ({robots.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#64748b]">
                  <span>Scope</span>
                  {robotsOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
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
                        className={`px-2.5 py-1.5 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-white text-black font-bold"
                            : "text-[#cbd5e1] hover:bg-[#141722] hover:text-white"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span className={`w-2 h-2 rounded-full ${isSelected ? "bg-black" : "bg-white"}`} />
                          <span className="truncate">{r.name} [{r.id}]</span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px]">
                          <span>{Math.round(r.battery)}%</span>
                          <span className="uppercase text-[9px] opacity-75">{r.state}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Environment Scope */}
            <div className="border border-[#181a22] rounded bg-[#050608]">
              <button
                onClick={() => setRoomsOpen(!roomsOpen)}
                className="w-full px-2.5 py-1.5 flex items-center justify-between text-white hover:bg-[#141722] text-[11px] font-bold"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[#64748b]">└</span>
                  <span>Facility Rooms ({rooms.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#64748b]">
                  <span>Scope</span>
                  {roomsOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
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
                        className={`px-2.5 py-1.5 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-white text-black font-bold"
                            : "text-[#cbd5e1] hover:bg-[#141722] hover:text-white"
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
            <div className="border border-[#181a22] rounded bg-[#050608]">
              <button
                onClick={() => setObstaclesOpen(!obstaclesOpen)}
                className="w-full px-2.5 py-1.5 flex items-center justify-between text-white hover:bg-[#141722] text-[11px] font-bold"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[#64748b]">└</span>
                  <span>Obstacles ({obstacles.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#64748b]">
                  <span>Scope</span>
                  {obstaclesOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
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
                        className={`px-2.5 py-1.5 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-white text-black font-bold"
                            : "text-[#cbd5e1] hover:bg-[#141722] hover:text-white"
                        }`}
                      >
                        <span className="truncate">{o.name}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleObstacle(o.id, !o.active);
                          }}
                          className={`text-[9px] px-2 py-0.5 rounded border transition-all ${
                            o.active ? "bg-white text-black font-bold border-white" : "text-[#64748b] border-[#222634] hover:text-white"
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

            {/* Digital Twin Agents */}
            <div className="border border-[#181a22] rounded bg-[#050608]">
              <button
                onClick={() => setHumansOpen(!humansOpen)}
                className="w-full px-2.5 py-1.5 flex items-center justify-between text-white hover:bg-[#141722] text-[11px] font-bold"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[#64748b]">└</span>
                  <span>Digital Twins ({humans.length})</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[#64748b]">
                  <span>Scope</span>
                  {humansOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
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
                        className={`px-2.5 py-1.5 rounded cursor-pointer flex items-center justify-between transition-all ${
                          isSelected
                            ? "bg-white text-black font-bold"
                            : "text-[#cbd5e1] hover:bg-[#141722] hover:text-white"
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

        {/* TAB 2: FLEET TELEMETRY */}
        {activeTab === "fleet" && (
          <div className="space-y-3">
            <div className="text-[11px] text-[#94a3b8]">
              Live status and hardware telemetry for all active FARS-AMR units.
            </div>

            <div className="space-y-2">
              {robots.map((r) => (
                <div
                  key={r.id}
                  onClick={() => onSelectEntity("robot", r.id)}
                  className="border border-[#222634] rounded p-3 bg-[#050608] hover:border-white transition-all cursor-pointer space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-xs">{r.name} [{r.id}]</span>
                    <span className="px-2 py-0.5 rounded bg-white text-black font-bold text-[9px] uppercase">
                      {r.state}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="bg-[#141722] p-2 rounded border border-[#1e2333]">
                      <div className="text-[#64748b] text-[10px]">BATTERY</div>
                      <div className="font-bold text-white">{Math.round(r.battery)}%</div>
                    </div>
                    <div className="bg-[#141722] p-2 rounded border border-[#1e2333]">
                      <div className="text-[#64748b] text-[10px]">VELOCITY</div>
                      <div className="font-bold text-white font-mono">{r.speed.toFixed(2)} m/s</div>
                    </div>
                    <div className="bg-[#141722] p-2 rounded border border-[#1e2333]">
                      <div className="text-[#64748b] text-[10px]">ODOMETER</div>
                      <div className="font-bold text-white font-mono">{r.total_distance.toFixed(1)} m</div>
                    </div>
                    <div className="bg-[#141722] p-2 rounded border border-[#1e2333]">
                      <div className="text-[#64748b] text-[10px]">LOCATION</div>
                      <div className="font-bold text-white truncate">{r.target_node || "Idle"}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: RL TRAINING STUDIO */}
        {activeTab === "rl" && (
          <div className="space-y-4">
            <div className="text-[11px] text-[#94a3b8]">
              Reinforcement learning navigation policy training in Gymnasium with PyTorch CUDA acceleration.
            </div>

            <div className="border border-[#222634] rounded p-3 bg-[#050608] space-y-3">
              <div className="font-bold text-white flex items-center gap-2">
                <Brain className="w-4 h-4 text-white" />
                <span>FARS Navigation DQN</span>
              </div>

              <div>
                <label className="text-[10px] text-[#64748b] block mb-1">TRAINING EPISODES: {rlEpisodes}</label>
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
                className="w-full py-2 rounded bg-white hover:bg-[#e2e8f0] text-black font-bold transition-all disabled:opacity-50"
              >
                {rlLoading ? "Training Neural Policy (CUDA)..." : "Start Training Session"}
              </button>
            </div>

            {rlResult && (
              <div className="border border-[#222634] rounded p-3 bg-[#050608] space-y-2">
                <div className="text-white font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Session Results</span>
                </div>
                <div className="space-y-1.5 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#94a3b8]">Success Rate:</span>
                    <span className="font-bold text-white">{rlResult.success_rate_percent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#94a3b8]">Mean Reward:</span>
                    <span className="font-bold text-white">{rlResult.final_avg_reward}</span>
                  </div>
                  <div className="border-t border-[#222634] pt-1.5">
                    <div className="text-[#64748b] text-[10px] uppercase">A* Benchmark Comparison:</div>
                    <div className="flex justify-between pt-0.5">
                      <span className="text-[#94a3b8]">Learned Policy Steps:</span>
                      <span className="text-white font-bold">{rlResult.baseline_comparison.policy_avg_steps}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#94a3b8]">A* Optimal Shortest:</span>
                      <span className="text-white font-bold">{rlResult.baseline_comparison.astar_baseline_steps}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: ENVIRONMENTS */}
        {activeTab === "projects" && (
          <div className="space-y-3">
            <div className="text-[11px] text-[#94a3b8]">
              Switch environment models and simulation scenarios.
            </div>

            <div className="space-y-2">
              {[
                { id: "hospital", name: "Hospital Complex", desc: "Corridors, ICUs, Patient Rooms, Pharmacy" },
                { id: "warehouse", name: "Logistics Fulfillment", desc: "High-bay racks, sorting conveyor zones" },
                { id: "office", name: "Corporate Campus", desc: "Workspaces, conference halls, central atrium" },
              ].map((env) => (
                <div
                  key={env.id}
                  className="border border-[#222634] rounded p-3 bg-[#050608] hover:border-white transition-all cursor-pointer"
                  onClick={() => sendControl("load_environment", { template: env.id })}
                >
                  <div className="font-bold text-white text-xs">{env.name}</div>
                  <div className="text-[10px] text-[#64748b] mt-1">{env.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
