"use client";

import React, { useState } from "react";
import {
  FileText,
  Sliders,
  Compass,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronRight
} from "lucide-react";
import { FARSverseSnapshot, createManualTask, toggleObstacle, updateRobot } from "@/lib/farsverse-api";

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

  // USD Collapsibles
  const [secTransform, setSecTransform] = useState(true);
  const [secPhysics, setSecPhysics] = useState(true);
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
      await createManualTask("assist_patient", targetNode, 3, `Manual dispatch ${robot.id} to ${targetNode}`);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <aside className="w-80 bg-[#09090b] border-l border-[#27272a] flex flex-col h-full select-none text-xs font-mono text-[#f4f4f5]">
      {/* Header */}
      <div className="h-10 border-b border-[#27272a] bg-[#000000] px-3 flex items-center justify-between">
        <div className="text-[11px] font-bold tracking-wider text-white uppercase flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-white" />
          <span>PROPERTY INSPECTOR</span>
        </div>
        {selectedEntity && (
          <button
            onClick={() => onSelectEntity("", "")}
            className="text-[10px] text-[#71717a] hover:text-white"
          >
            Deselect
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* CASE 1: ROBOT SELECTED */}
        {robot ? (
          <div className="space-y-3">
            {/* Prim Identity */}
            <div className="border border-[#27272a] rounded p-2.5 bg-[#000000]">
              <div className="text-[10px] text-[#71717a] uppercase font-bold">USD Prim Identifier</div>
              <div className="font-bold text-white text-sm mt-0.5">{robot.name} [{robot.id}]</div>
              <div className="text-[10px] text-[#a1a1aa] mt-0.5">/World/Robots/{robot.id} (ArticulationRoot)</div>
            </div>

            {/* SECTION 1: TRANSFORM */}
            <div className="border border-[#27272a] rounded bg-[#000000]">
              <button
                onClick={() => setSecTransform(!secTransform)}
                className="w-full px-2 py-1.5 flex items-center justify-between bg-[#121214] text-[11px] font-bold text-white"
              >
                <span>TRANSFORM</span>
                {secTransform ? <ChevronDown className="w-3.5 h-3.5 text-[#71717a]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#71717a]" />}
              </button>

              {secTransform && (
                <div className="p-2 space-y-1.5 text-[11px]">
                  <div className="flex items-center justify-between">
                    <span className="text-[#71717a]">Translate:</span>
                    <div className="flex gap-1 font-mono">
                      <span className="bg-[#18181b] px-1.5 py-0.5 rounded text-white border border-[#27272a]">X {robot.x.toFixed(2)}</span>
                      <span className="bg-[#18181b] px-1.5 py-0.5 rounded text-white border border-[#27272a]">Y 0.00</span>
                      <span className="bg-[#18181b] px-1.5 py-0.5 rounded text-white border border-[#27272a]">Z {robot.z.toFixed(2)}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[#71717a]">Rotate (Yaw):</span>
                    <span className="bg-[#18181b] px-2 py-0.5 rounded text-white border border-[#27272a] font-mono">
                      {robot.rotation_y.toFixed(1)}°
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[#71717a]">Scale:</span>
                    <span className="text-[#a1a1aa] font-mono">(1.00, 1.00, 1.00)</span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 2: DYNAMICS & PHYSICS */}
            <div className="border border-[#27272a] rounded bg-[#000000]">
              <button
                onClick={() => setSecPhysics(!secPhysics)}
                className="w-full px-2 py-1.5 flex items-center justify-between bg-[#121214] text-[11px] font-bold text-white"
              >
                <span>PHYSICS & DYNAMICS</span>
                {secPhysics ? <ChevronDown className="w-3.5 h-3.5 text-[#71717a]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#71717a]" />}
              </button>

              {secPhysics && (
                <div className="p-2 space-y-1.5 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Chassis Model:</span>
                    <span className="text-white font-bold">{robot.robot_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Drive System:</span>
                    <span className="text-white">Differential 2-Wheel</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Linear Velocity:</span>
                    <span className="text-white font-mono">{robot.speed.toFixed(2)} m/s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Odometer Distance:</span>
                    <span className="text-white font-mono">{robot.total_distance.toFixed(1)} m</span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 3: SENSORS & POWER */}
            <div className="border border-[#27272a] rounded bg-[#000000]">
              <button
                onClick={() => setSecSensors(!secSensors)}
                className="w-full px-2 py-1.5 flex items-center justify-between bg-[#121214] text-[11px] font-bold text-white"
              >
                <span>SENSORS & TELEMETRY</span>
                {secSensors ? <ChevronDown className="w-3.5 h-3.5 text-[#71717a]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#71717a]" />}
              </button>

              {secSensors && (
                <div className="p-2 space-y-2 text-[11px]">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-[#71717a]">Battery State:</span>
                      <span className="font-bold text-white">{Math.round(robot.battery)}%</span>
                    </div>
                    <div className="h-1.5 bg-[#18181b] rounded-full overflow-hidden border border-[#27272a]">
                      <div
                        className="h-full bg-white transition-all"
                        style={{ width: `${Math.min(100, Math.max(0, robot.battery))}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[#71717a]">360° LiDAR:</span>
                    <span className="text-white">Active (600 RPM)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Sonar Proximity:</span>
                    <span className="text-white font-mono">{robot.ultrasonic_distance.toFixed(2)} m</span>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 4: MISSION & AUTONOMOUS DISPATCH */}
            <div className="border border-[#27272a] rounded bg-[#000000]">
              <button
                onClick={() => setSecMission(!secMission)}
                className="w-full px-2 py-1.5 flex items-center justify-between bg-[#121214] text-[11px] font-bold text-white"
              >
                <span>MISSION EXECUTION</span>
                {secMission ? <ChevronDown className="w-3.5 h-3.5 text-[#71717a]" /> : <ChevronRight className="w-3.5 h-3.5 text-[#71717a]" />}
              </button>

              {secMission && (
                <div className="p-2 space-y-2.5 text-[11px]">
                  <div className="flex justify-between items-center">
                    <span className="text-[#71717a]">State Machine:</span>
                    <span className="px-2 py-0.5 rounded bg-white text-black font-bold text-[10px] uppercase">
                      {robot.state}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Target Node:</span>
                    <span className="text-white font-bold">{robot.target_node || "None (Idle)"}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[#71717a]">Route Waypoints:</span>
                    <span className="text-white font-mono">
                      {Math.max(0, robot.waypoints.length - robot.waypoint_index)} remaining
                    </span>
                  </div>

                  {/* Manual Target Selector */}
                  <div className="border-t border-[#27272a] pt-2 space-y-1.5">
                    <label className="text-[10px] text-[#71717a] block">Direct Mission Waypoint:</label>
                    <div className="flex gap-1.5">
                      <select
                        value={quickDest}
                        onChange={(e) => setQuickDest(e.target.value)}
                        className="flex-1 bg-[#121214] border border-[#27272a] rounded px-2 py-1 text-white text-xs"
                      >
                        {snapshot?.world?.rooms.map((rm) => (
                          <option key={rm.id} value={rm.id}>{rm.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleManualDispatch(quickDest)}
                        className="px-2.5 py-1 rounded bg-white hover:bg-[#e4e4e7] text-black font-bold text-xs"
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
          <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-2.5">
            <div className="text-[10px] text-[#71717a] uppercase font-bold">USD Facility Prim</div>
            <div className="font-bold text-white text-sm">{room.name}</div>
            <div className="text-[10px] text-[#a1a1aa]">/World/Environment/Rooms/{room.id}</div>

            <div className="border-t border-[#27272a] pt-2 space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#71717a]">Room Type:</span>
                <span className="text-white uppercase font-bold">{room.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#71717a]">Dimensions:</span>
                <span className="text-white font-mono">{room.width}m × {room.depth}m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#71717a]">Center Position:</span>
                <span className="text-white font-mono">({room.x.toFixed(1)}, {room.z.toFixed(1)})</span>
              </div>
            </div>
          </div>
        ) : human ? (
          /* CASE 3: HUMAN AGENT SELECTED */
          <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-2.5">
            <div className="text-[10px] text-[#71717a] uppercase font-bold">USD Digital Twin Avatar</div>
            <div className="font-bold text-white text-sm">{human.name}</div>
            <div className="text-[10px] text-[#a1a1aa]">/World/Agents/{human.id}</div>

            <div className="border-t border-[#27272a] pt-2 space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#71717a]">Role:</span>
                <span className="text-white uppercase font-bold">{human.agent_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#71717a]">Status:</span>
                <span className="text-white uppercase font-bold">{human.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#71717a]">Location Node:</span>
                <span className="text-white">{human.current_node}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#71717a]">Assistance Flag:</span>
                <span className="text-white">{human.needs_help ? "YES (Needs Help)" : "Nominal"}</span>
              </div>
            </div>
          </div>
        ) : obstacle ? (
          /* CASE 4: OBSTACLE SELECTED */
          <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-2.5">
            <div className="text-[10px] text-[#71717a] uppercase font-bold">USD Static Collider</div>
            <div className="font-bold text-white text-sm">{obstacle.name}</div>
            <div className="text-[10px] text-[#a1a1aa]">/World/Obstacles/{obstacle.id}</div>

            <div className="border-t border-[#27272a] pt-2 space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#71717a]">Collision Active:</span>
                <span className="font-bold text-white">{obstacle.active ? "BLOCKING" : "CLEARED"}</span>
              </div>
              <button
                onClick={() => toggleObstacle(obstacle.id, !obstacle.active)}
                className="w-full py-1.5 rounded bg-white hover:bg-[#e4e4e7] text-black font-bold text-xs"
              >
                {obstacle.active ? "Clear Obstacle" : "Deploy Obstacle"}
              </button>
            </div>
          </div>
        ) : (
          /* EMPTY STATE */
          <div className="text-[#71717a] text-center py-12 px-4 space-y-2">
            <Sliders className="w-8 h-8 mx-auto text-[#3f3f46]" />
            <p className="text-[11px]">No USD Prim Selected</p>
            <p className="text-[10px] text-[#52525b]">Click on any robot, room, agent, or collider in the 3D viewport to inspect its properties.</p>
          </div>
        )}
      </div>
    </aside>
  );
}
