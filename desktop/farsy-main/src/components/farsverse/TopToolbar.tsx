"use client";

import React, { useState } from "react";
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  StepForward,
  Save,
  Compass,
  Layers,
  MapPin,
  Send,
  Bot,
  Wifi,
  WifiOff,
  FolderOpen,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  PanelBottomClose,
  PanelBottomOpen,
  Terminal,
  Grid,
  Radio,
  Cpu
} from "lucide-react";
import { ConnectionStatus, FARSverseSnapshot, sendControl, sendNaturalCommand } from "@/lib/farsverse-api";

interface TopToolbarProps {
  snapshot: FARSverseSnapshot | null;
  connectionStatus: ConnectionStatus;
  cameraMode: "angled" | "topdown" | "follow";
  setCameraMode: (mode: "angled" | "topdown" | "follow") => void;
  showPaths: boolean;
  setShowPaths: (v: boolean) => void;
  showGrid: boolean;
  setShowGrid: (v: boolean) => void;
  showLabels: boolean;
  setShowLabels: (v: boolean) => void;
  showLeftPanel: boolean;
  setShowLeftPanel: (v: boolean) => void;
  showRightPanel: boolean;
  setShowRightPanel: (v: boolean) => void;
  showBottomPanel: boolean;
  setShowBottomPanel: (v: boolean) => void;
  onOpenProjects: () => void;
  onOpenAITaskPortal: () => void;
  onSaveCurrentProject: () => void;
}

export function TopToolbar({
  snapshot,
  connectionStatus,
  cameraMode,
  setCameraMode,
  showPaths,
  setShowPaths,
  showGrid,
  setShowGrid,
  showLabels,
  setShowLabels,
  showLeftPanel,
  setShowLeftPanel,
  showRightPanel,
  setShowRightPanel,
  showBottomPanel,
  setShowBottomPanel,
  onOpenProjects,
  onOpenAITaskPortal,
  onSaveCurrentProject,
}: TopToolbarProps) {
  const [commandInput, setCommandInput] = useState("");
  const [lastParsedBy, setLastParsedBy] = useState<string | null>(null);
  const [isSubmittingCmd, setIsSubmittingCmd] = useState(false);

  const status = snapshot?.status || "STOPPED";
  const speed = snapshot?.speed || 1.0;
  const simTime = snapshot?.sim_time || 0.0;

  const mins = Math.floor(simTime / 60);
  const secs = (simTime % 60).toFixed(1).padStart(4, "0");
  const formattedTime = `${String(mins).padStart(2, "0")}:${secs}`;

  const handleCommandSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim() || isSubmittingCmd) return;
    setIsSubmittingCmd(true);
    try {
      const res = await sendNaturalCommand(commandInput.trim());
      setLastParsedBy(res.parsed_by || "ollama");
      setCommandInput("");
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmittingCmd(false);
    }
  };

  return (
    <header className="border-b border-[#222634] bg-[#0a0c10] text-[#f4f4f5] flex flex-col select-none z-20 font-mono text-xs">
      {/* 1. FARS STUDIO CAD TOP MENU BAR */}
      <div className="h-6 border-b border-[#181a22] bg-[#050608] px-3 flex items-center justify-between text-[11px] text-[#94a3b8]">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-white shadow-[0_0_6px_#ffffff]" />
            <span className="font-extrabold text-white tracking-widest uppercase">FARS STUDIO</span>
          </div>
          <span className="text-[#33394a]">|</span>
          <span className="text-[#cbd5e1] font-semibold">SIMULATION CORE v2.5</span>
          <span className="text-[#33394a]">|</span>
          <span className="hover:text-white cursor-pointer transition-colors">File</span>
          <span className="hover:text-white cursor-pointer transition-colors">Edit</span>
          <span className="hover:text-white cursor-pointer transition-colors">View</span>
          <span className="hover:text-white cursor-pointer transition-colors">Robots</span>
          <span className="hover:text-white cursor-pointer transition-colors">Sensors</span>
          <span className="hover:text-white cursor-pointer transition-colors">Missions</span>
          <span className="hover:text-white cursor-pointer transition-colors">Diagnostics</span>
          <span className="hover:text-white cursor-pointer transition-colors">Help</span>
        </div>

        <div className="flex items-center gap-3 text-[10px]">
          <span className="text-[#64748b]">FACILITY: <strong className="text-white">{snapshot?.world?.name || "Hospital_MainWing"}</strong></span>
          <span className="text-[#33394a]">|</span>
          <div className="flex items-center gap-1.5">
            {connectionStatus === "connected" ? (
              <span className="inline-flex items-center gap-1.5 text-white font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                <span>CORE 127.0.0.1:8080 [ONLINE]</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[#ef4444]">
                <WifiOff className="w-3 h-3 text-[#ef4444]" />
                <span>DISCONNECTED</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. MAIN WORKSPACE ACTION BAR */}
      <div className="h-11 px-3 flex items-center justify-between gap-4 bg-[#0a0c10]">
        {/* Left: Project Actions & Dispatch */}
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenProjects}
            title="Open Environment Project Browser"
            className="text-xs bg-[#141722] hover:bg-[#1e2333] text-white px-3 py-1.5 rounded border border-[#272d3f] flex items-center gap-1.5 transition-all font-semibold"
          >
            <FolderOpen className="w-3.5 h-3.5 text-white" />
            <span>Projects</span>
          </button>

          <button
            onClick={onSaveCurrentProject}
            title="Save Current Simulation State"
            className="text-xs bg-[#141722] hover:bg-[#1e2333] text-white p-1.5 rounded border border-[#272d3f] transition-all"
          >
            <Save className="w-3.5 h-3.5 text-white" />
          </button>

          <button
            onClick={onOpenAITaskPortal}
            title="Open Autonomous Mission Dispatch Terminal (Ollama Local GPU)"
            className="text-xs bg-white hover:bg-[#e2e8f0] text-black px-3 py-1.5 rounded font-bold flex items-center gap-1.5 transition-all shadow-sm"
          >
            <span>+ Mission Dispatch</span>
          </button>
        </div>

        {/* Center: Transport Controls & Simulation Clock */}
        <div className="flex items-center gap-2 bg-[#050608] px-3 py-1 rounded border border-[#222634]">
          <button
            onClick={() => sendControl("play")}
            title="Play Simulation"
            className={`px-2.5 py-1 rounded text-[11px] font-bold flex items-center gap-1.5 transition-all ${
              status === "RUNNING"
                ? "bg-white text-black font-bold"
                : "text-[#94a3b8] hover:text-white hover:bg-[#141722]"
            }`}
          >
            <Play className="w-3 h-3 fill-current" />
            <span>PLAY</span>
          </button>

          <button
            onClick={() => sendControl("pause")}
            title="Pause Simulation"
            className={`px-2.5 py-1 rounded text-[11px] font-bold flex items-center gap-1.5 transition-all ${
              status === "PAUSED"
                ? "bg-white text-black font-bold"
                : "text-[#94a3b8] hover:text-white hover:bg-[#141722]"
            }`}
          >
            <Pause className="w-3 h-3 fill-current" />
            <span>PAUSE</span>
          </button>

          <button
            onClick={() => sendControl("stop")}
            title="Stop Simulation"
            className={`px-2 py-1 rounded text-[11px] font-bold flex items-center gap-1 transition-all ${
              status === "STOPPED"
                ? "bg-[#272d3f] text-white"
                : "text-[#94a3b8] hover:text-white hover:bg-[#141722]"
            }`}
          >
            <Square className="w-2.5 h-2.5 fill-current" />
            <span>STOP</span>
          </button>

          <button
            onClick={() => sendControl("step", { seconds: 0.5 })}
            title="Step Forward (+0.5s)"
            className="p-1.5 rounded text-[#94a3b8] hover:text-white hover:bg-[#141722] transition-all"
          >
            <StepForward className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => sendControl("reset")}
            title="Reset Simulation Scenario"
            className="p-1.5 rounded text-[#94a3b8] hover:text-white hover:bg-[#141722] transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-px bg-[#222634] mx-1" />

          {/* Time Code */}
          <div className="font-mono text-xs font-bold text-white px-2 tracking-wider">
            {formattedTime}
          </div>

          <div className="h-4 w-px bg-[#222634] mx-1" />

          {/* Speed Multipliers */}
          <div className="flex items-center gap-1 text-[10px]">
            {[0.5, 1.0, 2.0, 4.0].map((s) => (
              <button
                key={s}
                onClick={() => sendControl("set_speed", { speed: s })}
                className={`px-1.5 py-0.5 rounded transition-all font-semibold ${
                  speed === s
                    ? "bg-white text-black font-bold"
                    : "text-[#64748b] hover:text-white"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Center-Right: Professional Terminal Command Line */}
        <form onSubmit={handleCommandSubmit} className="flex-1 max-w-md relative">
          <div className="relative flex items-center">
            <span className="absolute left-3 text-[#64748b] font-bold text-[11px]">FARS &gt;</span>
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder='Enter mission directive: "Send FARS-01 to ICU1", "Patrol Pharmacy"...'
              className="w-full bg-[#050608] border border-[#222634] rounded pl-16 pr-16 py-1.5 text-xs text-white placeholder:text-[#475569] focus:outline-none focus:border-white transition-all font-mono"
            />
            <button
              type="submit"
              disabled={isSubmittingCmd || !commandInput.trim()}
              className="absolute right-1.5 px-2.5 py-0.5 rounded bg-[#1e2333] hover:bg-white hover:text-black text-white text-[10px] font-bold transition-all disabled:opacity-30"
            >
              RUN
            </button>
          </div>
        </form>

        {/* Right: Camera & Viewport Tools */}
        <div className="flex items-center gap-2">
          {/* Camera Modes */}
          <div className="flex items-center bg-[#050608] p-0.5 rounded border border-[#222634] text-xs">
            <button
              onClick={() => setCameraMode("angled")}
              title="3D Perspective Camera"
              className={`px-2.5 py-1 rounded text-[10px] font-bold transition-all ${
                cameraMode === "angled" ? "bg-white text-black" : "text-[#94a3b8] hover:text-white"
              }`}
            >
              3D Orbit
            </button>
            <button
              onClick={() => setCameraMode("topdown")}
              title="Top 2D Blueprint View"
              className={`px-2.5 py-1 rounded text-[10px] font-bold transition-all ${
                cameraMode === "topdown" ? "bg-white text-black" : "text-[#94a3b8] hover:text-white"
              }`}
            >
              2D CAD
            </button>
            <button
              onClick={() => setCameraMode("follow")}
              title="Chase Target AMR"
              className={`px-2.5 py-1 rounded text-[10px] font-bold transition-all ${
                cameraMode === "follow" ? "bg-white text-black" : "text-[#94a3b8] hover:text-white"
              }`}
            >
              Chase
            </button>
          </div>

          {/* Overlays */}
          <div className="flex items-center bg-[#050608] p-0.5 rounded border border-[#222634]">
            <button
              onClick={() => setShowGrid(!showGrid)}
              title="Toggle Ground Grid"
              className={`p-1.5 rounded transition-all ${showGrid ? "text-white bg-[#1e2333]" : "text-[#475569]"}`}
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setShowPaths(!showPaths)}
              title="Toggle A* Path Trajectories"
              className={`p-1.5 rounded transition-all ${showPaths ? "text-white bg-[#1e2333]" : "text-[#475569]"}`}
            >
              <MapPin className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Dock Toggles */}
          <div className="flex items-center bg-[#050608] p-0.5 rounded border border-[#222634]">
            <button
              onClick={() => setShowLeftPanel(!showLeftPanel)}
              title="Toggle Hierarchy Dock"
              className={`p-1.5 rounded transition-all ${showLeftPanel ? "text-white" : "text-[#475569]"}`}
            >
              {showLeftPanel ? <PanelLeftClose className="w-3.5 h-3.5" /> : <PanelLeftOpen className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setShowBottomPanel(!showBottomPanel)}
              title="Toggle Console Dock"
              className={`p-1.5 rounded transition-all ${showBottomPanel ? "text-white" : "text-[#475569]"}`}
            >
              {showBottomPanel ? <PanelBottomClose className="w-3.5 h-3.5" /> : <PanelBottomOpen className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setShowRightPanel(!showRightPanel)}
              title="Toggle Inspector Dock"
              className={`p-1.5 rounded transition-all ${showRightPanel ? "text-white" : "text-[#475569]"}`}
            >
              {showRightPanel ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
