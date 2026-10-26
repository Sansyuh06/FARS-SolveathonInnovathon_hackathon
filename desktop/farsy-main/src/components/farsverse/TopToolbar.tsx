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
  Sparkles,
  Bot,
  Activity,
  Wifi,
  WifiOff,
  FolderOpen,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  PanelBottomClose,
  PanelBottomOpen,
  Sliders,
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
    <header className="h-13 bg-[#11141a] border-b border-[#232834] px-3.5 flex items-center justify-between gap-3 select-none z-20 font-mono text-xs text-white">
      {/* Brand & Project Info (Omniverse Style) */}
      <div className="flex items-center gap-2.5 min-w-[230px]">
        {/* NVIDIA Green Brand Badge */}
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-[#76b900] flex items-center justify-center text-black font-extrabold text-xs shadow-md shadow-[#76b900]/30">
            Ω
          </div>
          <div>
            <div className="text-xs font-bold tracking-wider text-white flex items-center gap-1.5">
              <span>NVIDIA OMNIVERSE™</span>
              <span className="text-[9px] bg-[#76b900]/20 text-[#76b900] px-1.5 py-0.2 rounded border border-[#76b900]/40 font-mono font-semibold">
                ISAAC SIM
              </span>
            </div>
            <div className="text-[10px] text-white/50 flex items-center gap-1">
              <span>{snapshot?.world?.name || "Digital Twin"}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onOpenProjects}
          title="Project Library"
          className="ml-2 text-xs bg-white/5 hover:bg-white/10 text-white/70 hover:text-white px-2.5 py-1 rounded border border-white/10 flex items-center gap-1.5 transition-all"
        >
          <FolderOpen className="w-3.5 h-3.5 text-[#76b900]" />
          <span>Projects</span>
        </button>

        <button
          onClick={onOpenAITaskPortal}
          title="Open AI Mission Planner & Task Creation Portal (Ollama)"
          className="text-xs bg-[#76b900]/20 hover:bg-[#76b900]/30 text-[#76b900] px-2.5 py-1 rounded border border-[#76b900]/40 flex items-center gap-1.5 transition-all font-bold shadow-md shadow-[#76b900]/20"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#76b900]" />
          <span>+ AI Mission Portal</span>
        </button>

        <button
          onClick={onSaveCurrentProject}
          title="Save USD Project"
          className="text-xs bg-white/5 hover:bg-white/10 text-white/70 hover:text-white p-1 rounded border border-white/10 transition-all"
        >
          <Save className="w-3.5 h-3.5 text-emerald-400" />
        </button>
      </div>

      {/* Center: Transport Controls & Simulation Clock */}
      <div className="flex items-center gap-2.5 bg-[#161a22] px-2.5 py-1 rounded border border-[#272d3b] shadow-inner">
        {/* Play/Pause/Stop/Reset/Step */}
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => sendControl("play")}
            title="Start Simulation (Play)"
            className={`p-1.5 rounded transition-all ${
              status === "RUNNING"
                ? "bg-[#76b900]/25 text-[#76b900] ring-1 ring-[#76b900]"
                : "text-white/60 hover:text-white hover:bg-white/10"
            }`}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
          </button>

          <button
            onClick={() => sendControl("pause")}
            title="Pause Simulation"
            className={`p-1.5 rounded transition-all ${
              status === "PAUSED"
                ? "bg-amber-500/25 text-amber-400 ring-1 ring-amber-500"
                : "text-white/60 hover:text-white hover:bg-white/10"
            }`}
          >
            <Pause className="w-3.5 h-3.5 fill-current" />
          </button>

          <button
            onClick={() => sendControl("stop")}
            title="Stop Simulation"
            className={`p-1.5 rounded transition-all ${
              status === "STOPPED"
                ? "bg-rose-500/25 text-rose-400 ring-1 ring-rose-500"
                : "text-white/60 hover:text-white hover:bg-white/10"
            }`}
          >
            <Square className="w-3 h-3 fill-current" />
          </button>

          <button
            onClick={() => sendControl("step", { seconds: 0.5 })}
            title="Step Forward (+0.5s)"
            className="p-1.5 rounded text-white/60 hover:text-[#76b900] hover:bg-white/10 transition-all"
          >
            <StepForward className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => sendControl("reset")}
            title="Reset Simulation Scenario"
            className="p-1.5 rounded text-white/60 hover:text-rose-400 hover:bg-white/10 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="h-4 w-px bg-white/10" />

        {/* Speed Selector */}
        <div className="flex items-center gap-1 text-[11px]">
          <span className="text-white/40 text-[10px]">SPEED:</span>
          {[0.5, 1.0, 2.0, 4.0].map((s) => (
            <button
              key={s}
              onClick={() => sendControl("set_speed", { speed: s })}
              className={`px-1.5 py-0.5 rounded text-[10px] transition-all ${
                speed === s
                  ? "bg-[#76b900]/25 text-[#76b900] font-bold border border-[#76b900]/50"
                  : "text-white/40 hover:text-white"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        <div className="h-4 w-px bg-white/10" />

        {/* Sim Clock */}
        <div className="flex items-center gap-1.5 text-xs text-[#76b900]">
          <Activity className="w-3.5 h-3.5" />
          <span className="font-semibold tracking-wider">{formattedTime}</span>
        </div>
      </div>

      {/* Natural Language Command Bar (Ollama Integrated) */}
      <form onSubmit={handleCommandSubmit} className="flex-1 max-w-md relative">
        <div className="relative flex items-center">
          <Cpu className="w-3.5 h-3.5 text-[#76b900] absolute left-3 pointer-events-none" />
          <input
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            placeholder='Ask: "Send robot 1 to Room 19", "Deliver meds to ICU1"...'
            className="w-full bg-[#161a22] border border-[#272d3b] rounded pl-8 pr-20 py-1.5 text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-[#76b900] focus:ring-1 focus:ring-[#76b900]/40 transition-all"
          />
          <button
            type="submit"
            disabled={isSubmittingCmd || !commandInput.trim()}
            className="absolute right-1 px-2.5 py-0.5 rounded bg-[#76b900]/30 hover:bg-[#76b900]/50 text-[#76b900] text-[10px] font-bold flex items-center gap-1 transition-all disabled:opacity-40"
          >
            <span>DISPATCH</span>
            <Send className="w-2.5 h-2.5" />
          </button>
        </div>

        {lastParsedBy && (
          <div className="absolute right-0 -bottom-4 text-[9px] text-[#76b900]/80 flex items-center gap-1">
            <span>AI PARSER:</span>
            <span className="uppercase text-white/80 font-bold">{lastParsedBy} (phi3:mini / RTX 4060)</span>
          </div>
        )}
      </form>

      {/* Viewport Modes, Panels, & Connection */}
      <div className="flex items-center gap-2">
        {/* Camera Views */}
        <div className="flex items-center gap-0.5 bg-[#161a22] p-1 rounded border border-[#272d3b] text-xs">
          <button
            onClick={() => setCameraMode("angled")}
            title="Angled Perspective"
            className={`px-2 py-0.5 rounded text-[11px] flex items-center gap-1 ${
              cameraMode === "angled" ? "bg-[#76b900] text-black font-bold" : "text-white/50 hover:text-white"
            }`}
          >
            <Compass className="w-3 h-3" />
            <span>Angled</span>
          </button>
          <button
            onClick={() => setCameraMode("topdown")}
            title="Top-Down CAD Blueprint"
            className={`px-2 py-0.5 rounded text-[11px] flex items-center gap-1 ${
              cameraMode === "topdown" ? "bg-[#76b900] text-black font-bold" : "text-white/50 hover:text-white"
            }`}
          >
            <Layers className="w-3 h-3" />
            <span>Top</span>
          </button>
          <button
            onClick={() => setCameraMode("follow")}
            title="Follow Selected AMR"
            className={`px-2 py-0.5 rounded text-[11px] flex items-center gap-1 ${
              cameraMode === "follow" ? "bg-[#76b900] text-black font-bold" : "text-white/50 hover:text-white"
            }`}
          >
            <Bot className="w-3 h-3" />
            <span>Chase</span>
          </button>
        </div>

        {/* Viewport Overlays */}
        <div className="flex items-center gap-0.5 bg-[#161a22] p-1 rounded border border-[#272d3b]">
          <button
            onClick={() => setShowPaths(!showPaths)}
            title="Toggle A* Navigation Waypoint Route Lines"
            className={`p-1 rounded ${showPaths ? "text-[#76b900] bg-[#76b900]/20" : "text-white/30"}`}
          >
            <MapPin className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setShowGrid(!showGrid)}
            title="Toggle CAD Grid"
            className={`p-1 rounded ${showGrid ? "text-[#76b900] bg-[#76b900]/20" : "text-white/30"}`}
          >
            <Layers className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Omniverse Dockable Panel Toggles */}
        <div className="flex items-center gap-0.5 bg-[#161a22] p-1 rounded border border-[#272d3b]">
          <button
            onClick={() => setShowLeftPanel(!showLeftPanel)}
            title={showLeftPanel ? "Hide Stage Explorer" : "Show Stage Explorer"}
            className={`p-1 rounded ${showLeftPanel ? "text-[#76b900] bg-[#76b900]/20" : "text-white/30"}`}
          >
            {showLeftPanel ? <PanelLeftClose className="w-3.5 h-3.5" /> : <PanelLeftOpen className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setShowRightPanel(!showRightPanel)}
            title={showRightPanel ? "Hide Property Inspector" : "Show Property Inspector"}
            className={`p-1 rounded ${showRightPanel ? "text-[#76b900] bg-[#76b900]/20" : "text-white/30"}`}
          >
            {showRightPanel ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setShowBottomPanel(!showBottomPanel)}
            title={showBottomPanel ? "Hide Timeline Console" : "Show Timeline Console"}
            className={`p-1 rounded ${showBottomPanel ? "text-[#76b900] bg-[#76b900]/20" : "text-white/30"}`}
          >
            {showBottomPanel ? <PanelBottomClose className="w-3.5 h-3.5" /> : <PanelBottomOpen className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* WebSocket Live Pill */}
        <div
          title={`Status: ${connectionStatus}`}
          className={`px-2 py-0.5 rounded text-[10px] flex items-center gap-1.5 border ${
            connectionStatus === "connected"
              ? "bg-[#76b900]/15 text-[#76b900] border-[#76b900]/40"
              : "bg-rose-950/50 text-rose-400 border-rose-800"
          }`}
        >
          {connectionStatus === "connected" ? (
            <>
              <div className="w-2 h-2 rounded-full bg-[#76b900] animate-pulse" />
              <span className="font-bold">LIVE</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3 text-rose-400" />
              <span>OFFLINE</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
