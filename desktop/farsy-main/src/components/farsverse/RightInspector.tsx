"use client";

import React, { useState } from "react";
import {
  Bot,
  Battery,
  Navigation,
  Radio,
  FileText,
  History,
  Send,
  Zap,
  AlertOctagon,
  Building,
  ShieldAlert,
  Users,
  Compass,
  CheckCircle2,
  AlertTriangle
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
  const [robotTab, setRobotTab] = useState<"overview" | "navigation" | "sensors" | "trace" | "history">("overview");
  const [quickDest, setQuickDest] = useState("Room1");

  // Lookup selected entity
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
    <aside className="w-80 bg-[#0c1018] border-l border-white/10 flex flex-col h-full select-none text-xs font-mono">
      {/* Header */}
      <div className="h-10 border-b border-white/10 bg-[#090d14] px-3 flex items-center justify-between">
        <div className="text-[11px] font-bold tracking-wider text-white/80 uppercase flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-cyan-400" />
          <span>INSPECTOR</span>
        </div>
        {selectedEntity && (
          <button
            onClick={() => onSelectEntity("", "")}
            className="text-[10px] text-white/40 hover:text-white"
          >
            Clear Selection
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* CASE 1: ROBOT INSPECTION */}
        {robot ? (
          <div className="space-y-4">
            {/* Robot Header */}
            <div className="border border-white/10 rounded-lg p-3 bg-[#111622] space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                    <Bot className="w-4 h-4 text-cyan-400" />
                    <span>{robot.name}</span>
                  </h3>
                  <div className="text-[10px] text-white/50">{robot.id} | {robot.robot_type}</div>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase border ${
                    robot.state === "NAVIGATING"
                      ? "bg-cyan-950 text-cyan-400 border-cyan-800 animate-pulse"
                      : robot.state === "CHARGING"
                      ? "bg-amber-950 text-amber-400 border-amber-800"
                      : robot.state === "ERROR"
                      ? "bg-rose-950 text-rose-400 border-rose-800"
                      : "bg-emerald-950 text-emerald-400 border-emerald-800"
                  }`}
                >
                  {robot.state}
                </span>
              </div>

              {/* Battery Meter */}
              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-white/60 flex items-center gap-1">
                    <Battery className="w-3 h-3 text-emerald-400" />
                    <span>Battery Status</span>
                  </span>
                  <span className={`font-bold ${robot.battery > 20 ? "text-emerald-400" : "text-rose-400"}`}>
                    {Math.round(robot.battery)}%
                  </span>
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      robot.state === "CHARGING"
                        ? "bg-amber-400"
                        : robot.battery > 20
                        ? "bg-emerald-400"
                        : "bg-rose-500"
                    }`}
                    style={{ width: `${Math.max(2, robot.battery)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Sub-tabs for Robot Detail */}
            <div className="flex border-b border-white/10 bg-[#090d14] rounded p-0.5 text-[10px]">
              {[
                { id: "overview", label: "Overview" },
                { id: "navigation", label: "Nav" },
                { id: "sensors", label: "Sensors" },
                { id: "trace", label: "Trace" },
                { id: "history", label: "History" },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setRobotTab(t.id as any)}
                  className={`flex-1 py-1 rounded transition-all text-center ${
                    robotTab === t.id
                      ? "bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30"
                      : "text-white/40 hover:text-white"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Sub-tab 1: Overview */}
            {robotTab === "overview" && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="bg-[#111622] p-2 rounded border border-white/5">
                    <div className="text-white/40 text-[10px]">Coordinates</div>
                    <div className="font-bold text-white">({robot.x.toFixed(1)}, {robot.z.toFixed(1)})</div>
                  </div>
                  <div className="bg-[#111622] p-2 rounded border border-white/5">
                    <div className="text-white/40 text-[10px]">Heading</div>
                    <div className="font-bold text-white">{Math.round(robot.rotation_y)}°</div>
                  </div>
                  <div className="bg-[#111622] p-2 rounded border border-white/5">
                    <div className="text-white/40 text-[10px]">Velocity</div>
                    <div className="font-bold text-white">{robot.speed} m/s</div>
                  </div>
                  <div className="bg-[#111622] p-2 rounded border border-white/5">
                    <div className="text-white/40 text-[10px]">Total Distance</div>
                    <div className="font-bold text-white">{robot.total_distance.toFixed(1)} m</div>
                  </div>
                </div>

                {/* Target & Task */}
                <div className="bg-[#111622] p-2.5 rounded border border-white/5 space-y-1">
                  <div className="text-[10px] text-white/40 uppercase">Assigned Destination</div>
                  <div className="text-cyan-400 font-bold text-xs truncate">
                    {robot.target_node ? `${robot.target_node} (${robot.destination_name})` : "None (Standing By)"}
                  </div>
                </div>

                {/* Quick Dispatch Controls */}
                <div className="border border-white/10 rounded p-2.5 bg-black/20 space-y-2">
                  <div className="text-white/80 font-bold text-[11px] flex items-center gap-1">
                    <Send className="w-3 h-3 text-cyan-400" />
                    <span>Quick Command Dispatch</span>
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={quickDest}
                      onChange={(e) => setQuickDest(e.target.value)}
                      className="flex-1 bg-[#111622] border border-white/10 rounded p-1 text-xs text-white"
                    >
                      {snapshot?.world?.rooms.map((rm) => (
                        <option key={rm.id} value={rm.id}>
                          {rm.name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => handleManualDispatch(quickDest)}
                      className="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                    >
                      Send
                    </button>
                  </div>

                  <div className="flex gap-2 pt-1">
                    <button
                      onClick={() => handleManualDispatch("ChargingDock")}
                      className="flex-1 py-1 rounded bg-amber-950/60 hover:bg-amber-900 border border-amber-800 text-amber-300 flex items-center justify-center gap-1 text-[10px]"
                    >
                      <Zap className="w-3 h-3" />
                      <span>Return to Dock</span>
                    </button>
                    <button
                      onClick={() => updateRobot(robot.id, { speed: 0.0 })}
                      className="flex-1 py-1 rounded bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-300 flex items-center justify-center gap-1 text-[10px]"
                    >
                      <AlertOctagon className="w-3 h-3" />
                      <span>E-Stop</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Sub-tab 2: Navigation */}
            {robotTab === "navigation" && (
              <div className="space-y-3">
                <div className="bg-[#111622] p-2.5 rounded border border-white/5 space-y-1">
                  <div className="text-[10px] text-white/40 uppercase">A* Waypoint Progress</div>
                  <div className="text-xs text-white">
                    Waypoint <span className="text-cyan-400 font-bold">{robot.waypoint_index}</span> of{" "}
                    <span className="text-white/60">{robot.waypoints.length}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-[10px] text-white/40 uppercase">Calculated Route Path</div>
                  <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                    {robot.waypoints.map((wp, idx) => (
                      <div
                        key={idx}
                        className={`p-1.5 rounded text-[11px] flex justify-between border ${
                          idx === robot.waypoint_index
                            ? "bg-cyan-950 text-cyan-300 border-cyan-800 font-bold"
                            : idx < robot.waypoint_index
                            ? "bg-black/20 text-white/30 border-transparent line-through"
                            : "bg-[#111622] text-white/70 border-white/5"
                        }`}
                      >
                        <span>WP #{idx + 1}</span>
                        <span>({wp[0].toFixed(1)}, {wp[1].toFixed(1)})</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Sub-tab 3: Sensors */}
            {robotTab === "sensors" && (
              <div className="space-y-3">
                <div className="bg-[#111622] p-2.5 rounded border border-white/5 space-y-2">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-white/60 flex items-center gap-1">
                      <Radio className="w-3 h-3 text-cyan-400" />
                      <span>Forward Ultrasonic Sensor</span>
                    </span>
                    <span className="text-cyan-400 font-bold">{robot.ultrasonic_distance} m</span>
                  </div>
                  <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        robot.ultrasonic_distance < 1.5 ? "bg-rose-500" : "bg-cyan-400"
                      }`}
                      style={{ width: `${Math.min(100, (robot.ultrasonic_distance / 6.0) * 100)}%` }}
                    />
                  </div>
                </div>

                <div className="bg-[#111622] p-2.5 rounded border border-white/5 space-y-1">
                  <div className="text-[10px] text-white/40 uppercase">Forward Objects in FOV</div>
                  {robot.detected_obstacles.length > 0 ? (
                    <div className="space-y-1 pt-1">
                      {robot.detected_obstacles.map((obs, i) => (
                        <div key={i} className="text-amber-400 text-[11px] flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          <span>{obs}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-white/40 text-[11px] italic pt-1">Clear corridor. No immediate obstructions.</div>
                  )}
                </div>
              </div>
            )}

            {/* Sub-tab 4: Decision Trace */}
            {robotTab === "trace" && (
              <div className="space-y-3">
                <div className="bg-[#111622] p-3 rounded border border-white/5 space-y-2">
                  <div className="text-[10px] text-cyan-400 uppercase font-bold tracking-wider">
                    Task Scheduler Decision Trace
                  </div>
                  <p className="text-white/80 text-[11px] leading-relaxed italic bg-black/30 p-2 rounded border border-white/5">
                    "{robot.decision_trace}"
                  </p>
                </div>
              </div>
            )}

            {/* Sub-tab 5: History */}
            {robotTab === "history" && (
              <div className="space-y-2">
                <div className="text-[10px] text-white/40 uppercase">Completed Task History</div>
                {robot.history.length > 0 ? (
                  robot.history.map((h, i) => (
                    <div key={i} className="p-2 rounded bg-[#111622] border border-white/5 text-[10px] space-y-1">
                      <div className="flex justify-between text-white font-medium">
                        <span>{h.destination}</span>
                        <span className="text-emerald-400 font-bold">{h.status}</span>
                      </div>
                      <div className="text-white/40">{h.task?.description || "Service request"}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-white/40 text-[11px] italic">No completed tasks yet for this robot.</div>
                )}
              </div>
            )}
          </div>
        ) : human ? (
          /* CASE 2: HUMAN INSPECTION */
          <div className="space-y-3">
            <div className="border border-white/10 rounded-lg p-3 bg-[#111622] space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-blue-400" />
                    <span>{human.name}</span>
                  </h3>
                  <div className="text-[10px] text-white/50">{human.id} | {human.agent_type.toUpperCase()}</div>
                </div>
                {human.needs_help ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800 animate-pulse">
                    NEEDS HELP
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                    OK
                  </span>
                )}
              </div>

              <div className="text-[11px] text-white/70 pt-1">
                <div>Current Location: <span className="font-bold text-white">{human.current_node}</span></div>
                <div>Status: <span className="font-bold text-cyan-400">{human.status}</span></div>
              </div>
            </div>

            {human.needs_help && (
              <button
                onClick={() => handleManualDispatch(human.current_node)}
                className="w-full py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all"
              >
                Dispatch Available Robot
              </button>
            )}
          </div>
        ) : room ? (
          /* CASE 3: ROOM INSPECTION */
          <div className="space-y-3">
            <div className="border border-white/10 rounded-lg p-3 bg-[#111622] space-y-2">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Building className="w-4 h-4 text-indigo-400" />
                <span>{room.name}</span>
              </h3>
              <div className="text-[10px] text-white/50">Room ID: {room.id} | Type: {room.type}</div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div className="bg-black/30 p-2 rounded">
                  <div className="text-white/40">Center Coord</div>
                  <div className="font-bold text-white">({room.x.toFixed(1)}, {room.z.toFixed(1)})</div>
                </div>
                <div className="bg-black/30 p-2 rounded">
                  <div className="text-white/40">Footprint</div>
                  <div className="font-bold text-white">{room.width}m × {room.depth}m</div>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleManualDispatch(room.id)}
              className="w-full py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all"
            >
              Send Available Robot Here
            </button>
          </div>
        ) : obstacle ? (
          /* CASE 4: OBSTACLE INSPECTION */
          <div className="space-y-3">
            <div className="border border-white/10 rounded-lg p-3 bg-[#111622] space-y-2">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>{obstacle.name}</span>
              </h3>
              <div className="text-[10px] text-white/50">{obstacle.id}</div>

              <div className="text-[11px] text-white/70 pt-1">
                <div>Position: ({obstacle.x.toFixed(1)}, {obstacle.z.toFixed(1)})</div>
                <div>Size: {obstacle.width}m × {obstacle.depth}m</div>
              </div>
            </div>

            <button
              onClick={() => toggleObstacle(obstacle.id)}
              className={`w-full py-2 rounded font-bold border transition-all ${
                obstacle.active
                  ? "bg-rose-950 text-rose-300 border-rose-800 hover:bg-rose-900"
                  : "bg-emerald-950 text-emerald-300 border-emerald-800 hover:bg-emerald-900"
              }`}
            >
              {obstacle.active ? "Remove Corridor Blockage" : "Deploy Corridor Blockage"}
            </button>
          </div>
        ) : (
          /* DEFAULT: FACILITY TELEMETRY SUMMARY */
          <div className="space-y-3">
            <div className="border border-white/10 rounded-lg p-3 bg-[#111622] space-y-2">
              <div className="text-white/80 font-bold text-xs">FACILITY OVERVIEW</div>
              <div className="text-[10px] text-white/50">{snapshot?.world?.name || "Digital Twin"}</div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div className="bg-black/30 p-2 rounded">
                  <div className="text-white/40">Fleet Size</div>
                  <div className="font-bold text-cyan-400 text-sm">{snapshot?.robots.length || 0} Robots</div>
                </div>
                <div className="bg-black/30 p-2 rounded">
                  <div className="text-white/40">Total People</div>
                  <div className="font-bold text-blue-400 text-sm">{snapshot?.humans.length || 0} Agents</div>
                </div>
                <div className="bg-black/30 p-2 rounded">
                  <div className="text-white/40">Patient Rooms</div>
                  <div className="font-bold text-white text-sm">20 Rooms</div>
                </div>
                <div className="bg-black/30 p-2 rounded">
                  <div className="text-white/40">Tasks Done</div>
                  <div className="font-bold text-emerald-400 text-sm">
                    {snapshot?.tasks.completed.length || 0}
                  </div>
                </div>
              </div>
            </div>

            <div className="p-3 rounded border border-white/5 bg-black/20 text-white/40 text-[11px] leading-relaxed">
              Click any robot, room, human, or obstacle in the 3D viewport or left explorer to inspect live kinematics, sensors, and task execution.
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
