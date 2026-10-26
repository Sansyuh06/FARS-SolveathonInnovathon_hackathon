"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  FARSverseClient,
  FARSverseSnapshot,
  ConnectionStatus,
  saveProject,
} from "@/lib/farsverse-api";
import { TopToolbar } from "./TopToolbar";
import { LeftSidebar } from "./LeftSidebar";
import { Viewport3D } from "./Viewport3D";
import { RightInspector } from "./RightInspector";
import { BottomConsole } from "./BottomConsole";
import { AssetUploadModal } from "./AssetUploadModal";
import { ProjectsModal } from "./ProjectsModal";
import { AITaskPortalModal } from "./AITaskPortalModal";
import { WifiOff, RefreshCw } from "lucide-react";

export default function FARSverseStudio() {
  const [snapshot, setSnapshot] = useState<FARSverseSnapshot | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [selectedEntity, setSelectedEntity] = useState<{ type: string; id: string } | null>(null);

  // Viewport Settings
  const [cameraMode, setCameraMode] = useState<"angled" | "topdown" | "follow">("angled");
  const [showPaths, setShowPaths] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // FARS Studio Dockable Panels Visibility
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [showBottomPanel, setShowBottomPanel] = useState(true);

  // Modals
  const [isAssetUploadOpen, setIsAssetUploadOpen] = useState(false);
  const [isProjectsModalOpen, setIsProjectsModalOpen] = useState(false);
  const [isAITaskPortalOpen, setIsAITaskPortalOpen] = useState(false);
  const [currentProject, setCurrentProject] = useState<any>({
    id: "proj_hospital_flagship",
    name: "FARS General Hospital",
    environment_type: "hospital",
  });

  const clientRef = useRef<FARSverseClient | null>(null);
  const lastUpdateRef = useRef<number>(0);

  useEffect(() => {
    const client = new FARSverseClient(
      (snap) => {
        const now = performance.now();
        // Throttle React DOM reconciliation to ~12 FPS so UI inputs and button clicks are 100% responsive
        if (now - lastUpdateRef.current >= 80) {
          lastUpdateRef.current = now;
          setSnapshot(snap);
        }
      },
      (status) => setConnectionStatus(status)
    );
    clientRef.current = client;

    return () => {
      client.destroy();
    };
  }, []);

  const handleSelectEntity = useCallback((type: string, id: string) => {
    if (!type || !id) {
      setSelectedEntity(null);
    } else {
      setSelectedEntity({ type, id });
    }
  }, []);

  const handleSaveCurrentProject = async () => {
    if (!snapshot) return;
    try {
      await saveProject({
        id: currentProject.id || "proj_custom",
        name: snapshot.world.name,
        description: `Saved project configuration (${snapshot.world.environment_type})`,
        environment_type: snapshot.world.environment_type,
        world_data: snapshot.world,
        robot_configs: snapshot.robots.map((r) => ({
          id: r.id,
          name: r.name,
          robot_type: r.robot_type,
          speed: r.speed,
          battery: r.battery,
        })),
        scenario_config: { human_count: snapshot.humans.length },
      });
      alert(`Project '${snapshot.world.name}' successfully saved.`);
    } catch (e) {
      console.error(e);
      alert("Error saving project to backend.");
    }
  };

  return (
    <div className="h-screen w-screen bg-[#000000] flex flex-col overflow-hidden text-[#f4f4f5] font-mono select-none">
      {/* Disconnection Warning Bar */}
      {connectionStatus !== "connected" && (
        <div className="bg-rose-950/80 border-b border-rose-800 text-rose-200 px-4 py-1 text-xs flex items-center justify-between z-30">
          <div className="flex items-center gap-2">
            <WifiOff className="w-4 h-4 text-rose-400" />
            <span>FARSverse backend server disconnected (attempting auto-reconnect to 127.0.0.1:8080)...</span>
          </div>
          <button
            onClick={() => clientRef.current?.connect()}
            className="flex items-center gap-1 bg-rose-900 hover:bg-rose-800 text-white px-2 py-0.5 rounded text-[10px] font-bold"
          >
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Reconnect</span>
          </button>
        </div>
      )}

      {/* 1. TOP TOOLBAR */}
      <TopToolbar
        snapshot={snapshot}
        connectionStatus={connectionStatus}
        cameraMode={cameraMode}
        setCameraMode={setCameraMode}
        showPaths={showPaths}
        setShowPaths={setShowPaths}
        showGrid={showGrid}
        setShowGrid={setShowGrid}
        showLabels={showLabels}
        setShowLabels={setShowLabels}
        showLeftPanel={showLeftPanel}
        setShowLeftPanel={setShowLeftPanel}
        showRightPanel={showRightPanel}
        setShowRightPanel={setShowRightPanel}
        showBottomPanel={showBottomPanel}
        setShowBottomPanel={setShowBottomPanel}
        onOpenProjects={() => setIsProjectsModalOpen(true)}
        onOpenAITaskPortal={() => setIsAITaskPortalOpen(true)}
        onSaveCurrentProject={handleSaveCurrentProject}
      />

      {/* 2. MIDDLE WORKSPACE: LEFT SIDEBAR + 3D VIEWPORT + RIGHT INSPECTOR */}
      <div className="flex-1 flex overflow-hidden relative">
        {showLeftPanel && (
          <LeftSidebar
            snapshot={snapshot}
            selectedEntity={selectedEntity}
            onSelectEntity={handleSelectEntity}
            onOpenAssetUpload={() => setIsAssetUploadOpen(true)}
            onClose={() => setShowLeftPanel(false)}
          />
        )}

        <main className="flex-1 relative h-full">
          <Viewport3D
            snapshot={snapshot}
            selectedEntity={selectedEntity}
            onSelectEntity={handleSelectEntity}
            cameraMode={cameraMode}
            showPaths={showPaths}
            showGrid={showGrid}
            showLabels={showLabels}
          />
        </main>

        {showRightPanel && (
          <RightInspector
            snapshot={snapshot}
            selectedEntity={selectedEntity}
            onSelectEntity={handleSelectEntity}
            onClose={() => setShowRightPanel(false)}
          />
        )}
      </div>

      {/* 3. BOTTOM SIMULATION CONSOLE */}
      {showBottomPanel && (
        <BottomConsole
          snapshot={snapshot}
          onSelectEntity={handleSelectEntity}
          onOpenAITaskPortal={() => setIsAITaskPortalOpen(true)}
          onClose={() => setShowBottomPanel(false)}
        />
      )}

      {/* 4. MODALS */}
      <AITaskPortalModal
        isOpen={isAITaskPortalOpen}
        onClose={() => setIsAITaskPortalOpen(false)}
        snapshot={snapshot}
        onSelectEntity={handleSelectEntity}
      />

      <AssetUploadModal
        isOpen={isAssetUploadOpen}
        onClose={() => setIsAssetUploadOpen(false)}
      />

      <ProjectsModal
        isOpen={isProjectsModalOpen}
        onClose={() => setIsProjectsModalOpen(false)}
        currentProject={currentProject}
        onLoadProject={(proj) => setCurrentProject(proj)}
      />
    </div>
  );
}
