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
  Grid
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
    <header className="border-b border-[#27272a] bg-[#09090b] text-[#f4f4f5] flex flex-col select-none z-20 font-mono text-xs">
      {/* 1. OMNIVERSE CAD MENU BAR */}
      <div className="h-6 border-b border-[#18181b] bg-[#000000] px-3 flex items-center justify-between text-[11px] text-[#a1a1aa]">
        <div className="flex items-center gap-4">
          <span className="font-bold text-[#ffffff] tracking-wider uppercase">NVIDIA Omniverse™</span>
          <span className="text-[#52525b]">|</span>
          <span className="text-[#ffffff]">Isaac Sim 2026.2</span>
          <span className="text-[#52525b]">|</span>
          <span className="hover:text-white cursor-pointer">File</span>
          <span className="hover:text-white cursor-pointer">Edit</span>
          <span className="hover:text-white cursor-pointer">Create</span>
          <span className="hover:text-white cursor-pointer">Window</span>
          <span className="hover:text-white cursor-pointer">Physics</span>
          <span className="hover:text-white cursor-pointer">Tools</span>
          <span className="hover:text-white cursor-pointer">Help</span>
        </div>

        <div className="flex items-center gap-3 text-[10px]">
          <span className="text-[#71717a]">PROJECT: <strong className="text-white">{snapshot?.world?.name || "Hospital_GroundFloor.usd"}</strong></span>
          <div className="flex items-center gap-1">
            {connectionStatus === "connected" ? (
              <span className="inline-flex items-center gap-1 text-white">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                <span>ENGINE 127.0.0.1:8080</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[#71717a]">
                <WifiOff className="w-3 h-3 text-[#71717a]" />
                <span>OFFLINE</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. MAIN TOOLBAR CONTROLS */}
      <div className="h-10 px-3 flex items-center justify-between gap-4 bg-[#09090b]">
        {/* Left: Project Actions & State */}
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenProjects}
            title="USD Project Browser"
            className="text-xs bg-[#18181b] hover:bg-[#27272a] text-[#ffffff] px-2.5 py-1 rounded border border-[#27272a] flex items-center gap-1.5 transition-all"
          >
            <FolderOpen className="w-3.5 h-3.5 text-white" />
            <span>Stage</span>
          </button>

          <button
            onClick={onSaveCurrentProject}
            title="Save USD Stage"
            className="text-xs bg-[#18181b] hover:bg-[#27272a] text-[#ffffff] p-1 rounded border border-[#27272a] transition-all"
          >
            <Save className="w-3.5 h-3.5 text-white" />
          </button>

          <button
            onClick={onOpenAITaskPortal}
            title="Open Mission Dispatch Terminal"
            className="text-xs bg-[#ffffff] hover:bg-[#e4e4e7] text-[#000000] px-2.5 py-1 rounded font-bold flex items-center gap-1.5 transition-all"
          >
            <span>+ Mission Dispatch</span>
          </button>
        </div>

        {/* Center: Clean Transport Controls & Time Code */}
        <div className="flex items-center gap-2 bg-[#000000] px-3 py-1 rounded border border-[#27272a]">
          <button
            onClick={() => sendControl("play")}
            title="Play Simulation"
            className={`px-2 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 transition-all ${
              status === "RUNNING"
                ? "bg-white text-black font-bold"
                : "text-[#a1a1aa] hover:text-white hover:bg-[#18181b]"
            }`}
          >
            <Play className="w-3 h-3 fill-current" />
            <span>PLAY</span>
          </button>

          <button
            onClick={() => sendControl("pause")}
            title="Pause Simulation"
            className={`px-2 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 transition-all ${
              status === "PAUSED"
                ? "bg-white text-black font-bold"
                : "text-[#a1a1aa] hover:text-white hover:bg-[#18181b]"
            }`}
          >
            <Pause className="w-3 h-3 fill-current" />
            <span>PAUSE</span>
          </button>

          <button
            onClick={() => sendControl("stop")}
            title="Stop Simulation"
            className={`px-2 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 transition-all ${
              status === "STOPPED"
                ? "bg-[#27272a] text-white"
                : "text-[#a1a1aa] hover:text-white hover:bg-[#18181b]"
            }`}
          >
            <Square className="w-2.5 h-2.5 fill-current" />
            <span>STOP</span>
          </button>

          <button
            onClick={() => sendControl("step", { seconds: 0.5 })}
            title="Step Forward (+0.5s)"
            className="p-1 rounded text-[#a1a1aa] hover:text-white hover:bg-[#18181b] transition-all"
          >
            <StepForward className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => sendControl("reset")}
            title="Reset Simulation Scenario"
            className="p-1 rounded text-[#a1a1aa] hover:text-white hover:bg-[#18181b] transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-px bg-[#27272a] mx-1" />

          {/* Time Code */}
          <div className="font-mono text-xs font-bold text-white px-2">
            {formattedTime}
          </div>

          <div className="h-4 w-px bg-[#27272a] mx-1" />

          {/* Speed Multipliers */}
          <div className="flex items-center gap-1 text-[10px]">
            {[0.5, 1.0, 2.0, 4.0].map((s) => (
              <button
                key={s}
                onClick={() => sendControl("set_speed", { speed: s })}
                className={`px-1.5 py-0.5 rounded transition-all ${
                  speed === s
                    ? "bg-white text-black font-bold"
                    : "text-[#71717a] hover:text-white"
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
            <span className="absolute left-2.5 text-[#71717a] font-bold">&gt;</span>
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder='Direct command: "Send Rob-1 to ICU1", "Block corridor"...'
              className="w-full bg-[#000000] border border-[#27272a] rounded pl-7 pr-20 py-1 text-xs text-white placeholder:text-[#52525b] focus:outline-none focus:border-white transition-all"
            />
            <button
              type="submit"
              disabled={isSubmittingCmd || !commandInput.trim()}
              className="absolute right-1 px-2 py-0.5 rounded bg-[#27272a] hover:bg-white hover:text-black text-white text-[10px] font-bold transition-all disabled:opacity-30"
            >
              RUN
            </button>
          </div>
        </form>

        {/* Right: Camera & Viewport Tools */}
        <div className="flex items-center gap-2">
          {/* Camera Modes */}
          <div className="flex items-center bg-[#000000] p-0.5 rounded border border-[#27272a] text-xs">
            <button
              onClick={() => setCameraMode("angled")}
              title="Perspective Camera"
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                cameraMode === "angled" ? "bg-white text-black" : "text-[#71717a] hover:text-white"
              }`}
            >
              Perspective
            </button>
            <button
              onClick={() => setCameraMode("topdown")}
              title="Top CAD Camera"
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                cameraMode === "topdown" ? "bg-white text-black" : "text-[#71717a] hover:text-white"
              }`}
            >
              Top
            </button>
            <button
              onClick={() => setCameraMode("follow")}
              title="Chase AMR Camera"
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                cameraMode === "follow" ? "bg-white text-black" : "text-[#71717a] hover:text-white"
              }`}
            >
              Chase
            </button>
          </div>

          {/* Overlays */}
          <div className="flex items-center bg-[#000000] p-0.5 rounded border border-[#27272a]">
            <button
              onClick={() => setShowGrid(!showGrid)}
              title="Toggle Ground Grid"
              className={`p-1 rounded ${showGrid ? "text-white bg-[#27272a]" : "text-[#52525b]"}`}
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setShowPaths(!showPaths)}
              title="Toggle Waypoint Trajectories"
              className={`p-1 rounded ${showPaths ? "text-white bg-[#27272a]" : "text-[#52525b]"}`}
            >
              <MapPin className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Panel Toggles */}
          <div className="flex items-center bg-[#000000] p-0.5 rounded border border-[#27272a]">
            <button
              onClick={() => setShowLeftPanel(!showLeftPanel)}
              title="Toggle Stage Panel"
              className={`p-1 rounded ${showLeftPanel ? "text-white" : "text-[#52525b]"}`}
            >
              {showLeftPanel ? <PanelLeftClose className="w-3.5 h-3.5" /> : <PanelLeftOpen className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setShowBottomPanel(!showBottomPanel)}
              title="Toggle Console Panel"
              className={`p-1 rounded ${showBottomPanel ? "text-white" : "text-[#52525b]"}`}
            >
              {showBottomPanel ? <PanelBottomClose className="w-3.5 h-3.5" /> : <PanelBottomOpen className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => setShowRightPanel(!showRightPanel)}
              title="Toggle Property Inspector"
              className={`p-1 rounded ${showRightPanel ? "text-white" : "text-[#52525b]"}`}
            >
              {showRightPanel ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
