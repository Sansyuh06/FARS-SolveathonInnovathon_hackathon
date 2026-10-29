"use client";

import React, { useState } from "react";
import {
  FileText,
  Sliders,
  Compass,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Radio,
  Zap,
  Bot
} from "lucide-react";
import { FARSverseSnapshot, createManualTask, sendNaturalCommand, toggleObstacle, updateRobot } from "@/lib/farsverse-api";

interface RightInspectorProps {
  snapshot: FARSverseSnapshot | null;
  selectedEntity: { type: string; id: string } | null;
  onSelectEntity: (type: string, id: string) => void;
  onClose?: () => void;
}

export function RightInspector({
  snapshot,
  selectedEntity,
  onSelectEntity,
  onClose,
}: RightInspectorProps) {
  const [quickDest, setQuickDest] = useState("Room1");

  // Property Collapsibles
  const [secTransform, setSecTransform] = useState(true);
  const [secKinematics, setSecKinematics] = useState(true);
  const [secSensors, setSecSensors] = useState(true);
  const [secMission, setSecMission] = useState(true);

  const robot = selectedEntity?.type === "robot"
    ? snapshot?.robots.find((r) => r.id === selectedEntity.id)
    : null;
  const human = selectedEntity?.type === "human"
    ? snapshot?.humans.find((h) => h.id === selectedEntity.id)
    : null;
  const room = selectedEntity?.type === "room"
    ? snapshot?.world?.rooms.find((rm) => rm.id === selectedEntity.id)
    : null;
  const obstacle = selectedEntity?.type === "obstacle"
    ? snapshot?.world?.obstacles.find((o) => o.id === selectedEntity.id)
    : null;

  const handleManualDispatch = async (targetNode: string) => {
    if (!robot) return;
    try {
      await sendNaturalCommand(`dispatch ${robot.id} to ${targetNode}`);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <aside className="w-80 bg-[#0a0c10] border-l border-[#222634] flex flex-col h-full select-none text-xs font-sans text-[#f4f4f5]">
      {/* Header */}
      <div className="h-10 border-b border-[#222634] bg-[#050608] px-3 flex items-center justify-between">
        <div className="text-[11px] font-bold tracking-wider text-white uppercase flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-white" />
          <span>PROPERTY INSPECTOR</span>
        </div>
        {selectedEntity && (
          <button
            onClick={() => onSelectEntity("", "")}
            className="text-[10px] text-[#64748b] hover:text-white transition-colors"
          >
            Clear Selection
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* CASE 1: FARS-AMR ROBOT SELECTED */}
        {robot ? (
          <div className="space-y-3">
            {/* Prim Identity */}
            <div className="border border-[#222634] rounded p-3 bg-[#050608]">
              <div className="text-[10px] text-[#64748b] uppercase font-bold tracking-wider">ROBOT SPECIFICATION</div>
              <div className="font-bold text-white text-sm mt-1">{robot.name} [{robot.id}]</div>
              <div className="text-[10px] text-[#94a3b8] mt-0.5">Model: FARS Autonomous Mobile Robot (AMR v2)</div>
            </div>

            {/* SECTION 1: TRANSFORM */}
            <div className="border border-[#222634] rounded bg-[#050608]">
              <button
                onClick={() => setSecTransform(!secTransform)}
                className="w-full px-3 py-2 flex items-center justify-between bg-[#121520] text-[11px] font-bold text-white"
              >
                <span>SPATIAL TRANSFORM (XYZ)</span>
                {secTransform ? <ChevronDown className="w-3.5 h-3.5 text-[#64748b]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#64748b]" />}
              </button>

              {secTransform && (
                <div className="p-3 space-y-2 text-[11px]">
                  <div className="flex items-center justify-between">
                    <span className="text-[#64748b]">Position:</span>
                    <div className="flex gap-1.5 font-mono">
                      <span className="bg-[#141722] px-2 py-0.5 rounded text-white border border-[#222634]">X {robot.x.toFixed(2)}m</span>
                      <span className="bg-[#141722] px-2 py-0.5 rounded text-white border border-[#222634]">Z {robot.z.toFixed(2)}m</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[#64748b]">Heading (Yaw):</span>
                    <span className="bg-[#141722] px-2.5 py-0.5 rounded text-white border border-[#222634] font-mono">
                      {robot.rotation_y.toFixed(1)}°
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 2: KINEMATICS & DRIVE */}
            <div className="border border-[#222634] rounded bg-[#050608]">
              <button
                onClick={() => setSecKinematics(!secKinematics)}
                className="w-full px-3 py-2 flex items-center justify-between bg-[#121520] text-[11px] font-bold text-white"
              >
                <span>KINEMATICS & CHASSIS</span>
                {secKinematics ? <ChevronDown className="w-3.5 h-3.5 text-[#64748b]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#64748b]" />}
              </button>

              {secKinematics && (
                <div className="p-3 space-y-2 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Drive System:</span>
                    <span className="text-white font-semibold">Differential 2-Wheel AGV</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Linear Speed:</span>
                    <span className="text-white font-mono">{robot.speed.toFixed(2)} m/s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Total Distance:</span>
                    <span className="text-white font-mono">{robot.total_distance.toFixed(1)} m</span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 3: SENSORS & POWER */}
            <div className="border border-[#222634] rounded bg-[#050608]">
              <button
                onClick={() => setSecSensors(!secSensors)}
                className="w-full px-3 py-2 flex items-center justify-between bg-[#121520] text-[11px] font-bold text-white"
              >
                <span>SENSORS & BATTERY</span>
                {secSensors ? <ChevronDown className="w-3.5 h-3.5 text-[#64748b]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#64748b]" />}
              </button>

              {secSensors && (
                <div className="p-3 space-y-2.5 text-[11px]">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-[#64748b]">Battery State:</span>
                      <span className="font-bold text-white">{Math.round(robot.battery)}%</span>
                    </div>
                    <div className="h-1.5 bg-[#141722] rounded-full overflow-hidden border border-[#222634]">
                      <div
                        className="h-full bg-white transition-all"
                        style={{ width: `${Math.min(100, Math.max(0, robot.battery))}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[#64748b]">360° LiDAR:</span>
                    <span className="text-white font-semibold">Online (600 RPM)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Sonar Clearance:</span>
                    <span className="text-white font-mono">{robot.ultrasonic_distance.toFixed(2)} m</span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 4: MISSION & AUTONOMOUS DISPATCH */}
            <div className="border border-[#222634] rounded bg-[#050608]">
              <button
                onClick={() => setSecMission(!secMission)}
                className="w-full px-3 py-2 flex items-center justify-between bg-[#121520] text-[11px] font-bold text-white"
              >
                <span>MISSION DISPATCH</span>
                {secMission ? <ChevronDown className="w-3.5 h-3.5 text-[#64748b]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#64748b]" />}
              </button>

              {secMission && (
                <div className="p-3 space-y-3 text-[11px]">
                  <div className="flex justify-between items-center">
                    <span className="text-[#64748b]">State Machine:</span>
                    <span className="px-2.5 py-0.5 rounded bg-white text-black font-bold text-[10px] uppercase">
                      {robot.state}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Active Target:</span>
                    <span className="text-white font-bold">{robot.target_node || "None (Idle)"}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Route Waypoints:</span>
                    <span className="text-white font-mono">
                      {Math.max(0, robot.waypoints.length - robot.waypoint_index)} remaining
                    </span>
                  </div>

                  {/* Manual Target Selector */}
                  <div className="border-t border-[#222634] pt-2.5 space-y-2">
                    <label className="text-[10px] text-[#64748b] block font-bold uppercase">Quick Destination Dispatch:</label>
                    <div className="grid grid-cols-2 gap-1.5 mb-2">
                      {[
                        { label: "Reception", id: "Reception" },
                        { label: "Pharmacy", id: "Pharmacy" },
                        { label: "Emergency", id: "EmergencyRoom" },
                        { label: "Docking", id: "ChargingDock" },
                      ].map((item) => (
                        <button
                          key={item.id}
                          onClick={() => handleManualDispatch(item.id)}
                          className="px-2 py-1.5 rounded bg-[#141722] hover:bg-[#76b900] hover:text-black text-white text-[10px] font-bold border border-[#222634] transition-all active:scale-95 text-left"
                        >
                          → {item.label}
                        </button>
                      ))}
                    </div>

                    <label className="text-[10px] text-[#64748b] block font-bold uppercase">All Facility Rooms:</label>
                    <div className="flex gap-2">
                      <select
                        value={quickDest}
                        onChange={(e) => setQuickDest(e.target.value)}
                        className="flex-1 bg-[#141722] border border-[#222634] rounded px-2.5 py-1 text-white text-xs"
                      >
                        {snapshot?.world?.rooms.map((rm) => (
                          <option key={rm.id} value={rm.id}>{rm.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleManualDispatch(quickDest)}
                        className="px-3 py-1 rounded bg-[#76b900] hover:bg-[#88d300] text-black font-bold text-xs active:scale-95"
                      >
                        Dispatch
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : room ? (
          /* CASE 2: ROOM SELECTED */
          <div className="border border-[#222634] rounded p-3 bg-[#050608] space-y-3">
            <div className="text-[10px] text-[#64748b] uppercase font-bold tracking-wider">FACILITY SPECIFICATION</div>
            <div className="font-bold text-white text-sm">{room.name}</div>
            <div className="text-[10px] text-[#94a3b8]">Node ID: {room.id}</div>

            <div className="border-t border-[#222634] pt-2.5 space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#64748b]">Room Type:</span>
                <span className="text-white uppercase font-bold">{room.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Dimensions:</span>
                <span className="text-white font-mono">{room.width}m × {room.depth}m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Coordinates:</span>
                <span className="text-white font-mono">({room.x.toFixed(1)}, {room.z.toFixed(1)})</span>
              </div>
            </div>
          </div>
        ) : human ? (
          /* CASE 3: DIGITAL TWIN AGENT */
          <div className="border border-[#222634] rounded p-3 bg-[#050608] space-y-3">
            <div className="text-[10px] text-[#64748b] uppercase font-bold tracking-wider">DIGITAL TWIN AGENT</div>
            <div className="font-bold text-white text-sm">{human.name}</div>
            <div className="text-[10px] text-[#94a3b8]">ID: {human.id}</div>

            <div className="border-t border-[#222634] pt-2.5 space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#64748b]">Classification:</span>
                <span className="text-white uppercase font-bold">{human.agent_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Current Activity:</span>
                <span className="text-white uppercase font-bold">{human.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Location Node:</span>
                <span className="text-white">{human.current_node}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Assistance Alert:</span>
                <span className="text-white">{human.needs_help ? "YES (Needs Help)" : "Nominal"}</span>
              </div>
            </div>
          </div>
        ) : obstacle ? (
          /* CASE 4: OBSTACLE */
          <div className="border border-[#222634] rounded p-3 bg-[#050608] space-y-3">
            <div className="text-[10px] text-[#64748b] uppercase font-bold tracking-wider">COLLIDER SPECIFICATION</div>
            <div className="font-bold text-white text-sm">{obstacle.name}</div>
            <div className="text-[10px] text-[#94a3b8]">ID: {obstacle.id}</div>

            <div className="border-t border-[#222634] pt-2.5 space-y-2.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#64748b]">Collision Status:</span>
                <span className="font-bold text-white">{obstacle.active ? "BLOCKING" : "CLEARED"}</span>
              </div>
              <button
                onClick={() => toggleObstacle(obstacle.id, !obstacle.active)}
                className="w-full py-2 rounded bg-white hover:bg-[#e2e8f0] text-black font-bold text-xs transition-all"
              >
                {obstacle.active ? "Clear Obstacle" : "Deploy Obstacle"}
              </button>
            </div>
          </div>
        ) : (
          /* EMPTY STATE */
          <div className="text-[#64748b] text-center py-16 px-4 space-y-2">
            <Sliders className="w-8 h-8 mx-auto text-[#33394a]" />
            <p className="text-[11px] font-bold text-white">No Entity Selected</p>
            <p className="text-[10px] text-[#475569]">Click on any robot, room, agent, or obstacle in the 3D viewport to inspect live properties.</p>
          </div>
        )}
      </div>
    </aside>
  );
}
