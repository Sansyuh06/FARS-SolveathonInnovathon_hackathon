"use client";

import React, { useState } from "react";
import {
  ListTodo,
  Terminal,
  LineChart,
  FlaskConical,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  Download,
  Search
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart as ReLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { FARSverseSnapshot, cancelTask, createManualTask } from "@/lib/farsverse-api";

interface BottomConsoleProps {
  snapshot: FARSverseSnapshot | null;
  onSelectEntity: (type: string, id: string) => void;
  onOpenAITaskPortal?: () => void;
  onClose?: () => void;
}

export function BottomConsole({ snapshot, onSelectEntity, onOpenAITaskPortal, onClose }: BottomConsoleProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<"tasks" | "events" | "metrics" | "experiments">("tasks");
  const [eventFilter, setEventFilter] = useState<"ALL" | "INFO" | "WARN" | "ERROR">("ALL");
  const [eventSearch, setEventSearch] = useState("");

  const [showNewTaskDialog, setShowNewTaskDialog] = useState(false);
  const [newTaskType, setNewTaskType] = useState("assist_patient");
  const [newTaskDest, setNewTaskDest] = useState("Room1");
  const [newTaskPrio, setNewTaskPrio] = useState(2);
  const [newTaskDesc, setNewTaskDesc] = useState("");

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createManualTask(newTaskType, newTaskDest, newTaskPrio, newTaskDesc || `Manual ${newTaskType}`);
      setShowNewTaskDialog(false);
      setNewTaskDesc("");
    } catch (err) {
      console.error(err);
    }
  };

  const tasksActive = snapshot?.tasks.active || [];
  const tasksPending = snapshot?.tasks.pending || [];
  const events = snapshot?.events || [];
  const metrics = snapshot?.metrics || [];

  const filteredEvents = events.filter((ev) => {
    if (eventFilter !== "ALL" && ev.severity !== eventFilter) return false;
    if (eventSearch && !ev.message.toLowerCase().includes(eventSearch.toLowerCase())) return false;
    return true;
  });

  return (
    <footer
      className={`border-t border-[#27272a] bg-[#09090b] text-[#f4f4f5] font-sans flex flex-col transition-all duration-150 z-20 ${
        isCollapsed ? "h-9" : "h-64"
      }`}
    >
      {/* Console Tab Bar */}
      <div className="h-9 bg-[#000000] border-b border-[#27272a] px-3 flex items-center justify-between text-xs font-sans">
        <div className="flex items-center gap-1">
          {[
            { id: "tasks", label: `Missions (${tasksActive.length + tasksPending.length})`, icon: ListTodo },
            { id: "events", label: `Console Log (${events.length})`, icon: Terminal },
            { id: "metrics", label: "Fleet Metrics", icon: LineChart },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id && !isCollapsed;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as any);
                  setIsCollapsed(false);
                }}
                className={`px-3 py-1 rounded-t flex items-center gap-1.5 transition-all ${
                  isActive
                    ? "bg-[#18181b] text-white font-bold border-t border-x border-[#3f3f46]"
                    : "text-[#71717a] hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-2">
          {activeTab === "tasks" && !isCollapsed && (
            <button
              onClick={() => setShowNewTaskDialog(true)}
              className="px-2 py-0.5 rounded bg-white hover:bg-[#e4e4e7] text-black text-[11px] font-bold flex items-center gap-1"
            >
              <Plus className="w-3 h-3" />
              <span>Create Task</span>
            </button>
          )}

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 text-[#71717a] hover:text-white rounded"
            title={isCollapsed ? "Expand Console" : "Collapse Console"}
          >
            {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Console Body */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-3 text-xs font-sans bg-[#09090b]">
          {/* TAB 1: TASK QUEUE TABLE */}
          {activeTab === "tasks" && (
            <div className="space-y-3">
              <div className="grid grid-cols-12 text-[10px] uppercase font-bold text-[#71717a] border-b border-[#27272a] pb-1 px-2">
                <div className="col-span-1">ID</div>
                <div className="col-span-2">Task Type</div>
                <div className="col-span-2">Destination</div>
                <div className="col-span-1">Prio</div>
                <div className="col-span-2">Assigned AMR</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-2 text-right">Actions</div>
              </div>

              {tasksActive.length === 0 && tasksPending.length === 0 ? (
                <div className="text-center py-8 text-[#52525b] text-xs">
                  Mission queue is empty. Use the top command line or click '+ Mission Dispatch' to schedule a task.
                </div>
              ) : (
                <div className="space-y-1">
                  {/* Active Tasks */}
                  {tasksActive.map((t) => (
                    <div
                      key={t.id}
                      className="grid grid-cols-12 items-center px-2 py-1.5 rounded bg-[#000000] border border-[#27272a] text-[11px] text-white"
                    >
                      <div className="col-span-1 font-bold">#{t.id}</div>
                      <div className="col-span-2 font-mono">{t.task_type}</div>
                      <div className="col-span-2 text-[#a1a1aa]">{t.location_node}</div>
                      <div className="col-span-1 font-mono font-bold">P{t.priority}</div>
                      <div
                        className="col-span-2 cursor-pointer underline text-white truncate"
                        onClick={() => t.assigned_robot && onSelectEntity("robot", t.assigned_robot)}
                      >
                        {t.assigned_robot || "-"}
                      </div>
                      <div className="col-span-2">
                        <span className="px-2 py-0.5 rounded bg-white text-black font-bold text-[9px] uppercase">
                          {t.status}
                        </span>
                      </div>
                      <div className="col-span-2 text-right">
                        <button
                          onClick={() => cancelTask(t.id)}
                          className="px-2 py-0.5 text-[10px] text-[#a1a1aa] hover:text-white border border-[#27272a] hover:border-white rounded"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ))}

                  {/* Pending Tasks */}
                  {tasksPending.map((t) => (
                    <div
                      key={t.id}
                      className="grid grid-cols-12 items-center px-2 py-1.5 rounded bg-[#000000]/60 border border-[#27272a] text-[11px] text-[#a1a1aa]"
                    >
                      <div className="col-span-1 font-bold">#{t.id}</div>
                      <div className="col-span-2">{t.task_type}</div>
                      <div className="col-span-2 text-[#71717a]">{t.location_node}</div>
                      <div className="col-span-1 font-mono">P{t.priority}</div>
                      <div className="col-span-2 text-[#52525b]">-</div>
                      <div className="col-span-2">
                        <span className="px-1.5 py-0.5 rounded text-[9px] uppercase border border-[#27272a]">
                          {t.status}
                        </span>
                      </div>
                      <div className="col-span-2 text-right">
                        <button
                          onClick={() => cancelTask(t.id)}
                          className="px-2 py-0.5 text-[10px] text-[#71717a] hover:text-white border border-[#27272a] rounded"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: SYSTEM EVENT CONSOLE */}
          {activeTab === "events" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4 pb-2 border-b border-[#27272a]">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[#71717a]">SEVERITY:</span>
                  {(["ALL", "INFO", "WARN", "ERROR"] as const).map((sev) => (
                    <button
                      key={sev}
                      onClick={() => setEventFilter(sev)}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        eventFilter === sev
                          ? "bg-white text-black border-white"
                          : "text-[#71717a] border-[#27272a] hover:text-white"
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>

                <div className="relative w-64">
                  <Search className="w-3 h-3 text-[#52525b] absolute left-2 top-2" />
                  <input
                    type="text"
                    value={eventSearch}
                    onChange={(e) => setEventSearch(e.target.value)}
                    placeholder="Search logs..."
                    className="w-full bg-[#000000] border border-[#27272a] rounded pl-7 pr-2 py-1 text-xs text-white placeholder:text-[#52525b] focus:outline-none focus:border-white"
                  />
                </div>
              </div>

              <div className="space-y-1 font-mono text-[11px] max-h-44 overflow-y-auto">
                {filteredEvents.map((ev, i) => (
                  <div
                    key={ev.id || i}
                    className="flex items-start gap-2 py-0.5 px-2 rounded hover:bg-[#18181b]"
                  >
                    <span className="text-[#52525b]">[{ev.sim_time ? ev.sim_time.toFixed(1) : "0.0"}s]</span>
                    <span
                      className={`font-bold uppercase text-[9px] px-1 rounded ${
                        ev.severity === "ERROR"
                          ? "bg-white text-black"
                          : ev.severity === "WARN"
                          ? "text-white underline"
                          : "text-[#a1a1aa]"
                      }`}
                    >
                      {ev.severity}
                    </span>
                    <span className="text-[#71717a]">[{ev.category}]</span>
                    <span className="text-white flex-1">{ev.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: TELEMETRY METRICS */}
          {activeTab === "metrics" && (
            <div className="h-44 w-full">
              {metrics.length < 2 ? (
                <div className="flex items-center justify-center h-full text-[#52525b]">
                  Collecting simulation samples... (updates every 2s)
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <ReLineChart data={metrics}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="sim_time" stroke="#71717a" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#71717a" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#000000", border: "1px solid #3f3f46", fontSize: 11 }} />
                    <Line type="monotone" dataKey="active_robots" stroke="#ffffff" strokeWidth={2} name="Active AMRs" />
                    <Line type="monotone" dataKey="avg_battery" stroke="#a1a1aa" strokeWidth={1.5} name="Avg Battery %" />
                    <Line type="monotone" dataKey="completed_tasks" stroke="#71717a" strokeWidth={1.5} name="Completed" />
                  </ReLineChart>
                </ResponsiveContainer>
              )}
            </div>
          )}
        </div>
      )}

      {/* Manual Task Creator Dialog Modal */}
      {showNewTaskDialog && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="w-96 bg-[#09090b] border border-[#27272a] rounded p-4 space-y-3 font-mono">
            <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
              <span className="font-bold text-white text-xs">CREATE MANUAL TASK</span>
              <button onClick={() => setShowNewTaskDialog(false)} className="text-[#71717a] hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-3 text-xs">
              <div>
                <label className="text-[10px] text-[#71717a] block mb-1">TASK TYPE</label>
                <select
                  value={newTaskType}
                  onChange={(e) => setNewTaskType(e.target.value)}
                  className="w-full bg-[#000000] border border-[#27272a] rounded p-1.5 text-white"
                >
                  <option value="assist_patient">assist_patient</option>
                  <option value="deliver_medicine">deliver_medicine</option>
                  <option value="patrol">patrol</option>
                  <option value="decontaminate">decontaminate</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-[#71717a] block mb-1">DESTINATION ROOM</label>
                <select
                  value={newTaskDest}
                  onChange={(e) => setNewTaskDest(e.target.value)}
                  className="w-full bg-[#000000] border border-[#27272a] rounded p-1.5 text-white"
                >
                  {snapshot?.world?.rooms.map((rm) => (
                    <option key={rm.id} value={rm.id}>{rm.name} ({rm.id})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-[#71717a] block mb-1">PRIORITY (P1 Low - P4 Critical)</label>
                <select
                  value={newTaskPrio}
                  onChange={(e) => setNewTaskPrio(parseInt(e.target.value))}
                  className="w-full bg-[#000000] border border-[#27272a] rounded p-1.5 text-white"
                >
                  <option value={1}>P1 - Low / Routine</option>
                  <option value={2}>P2 - Standard</option>
                  <option value={3}>P3 - Urgent Clinical</option>
                  <option value={4}>P4 - Critical Emergency</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#27272a]">
                <button
                  type="button"
                  onClick={() => setShowNewTaskDialog(false)}
                  className="px-3 py-1 rounded border border-[#27272a] text-[#a1a1aa] hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1 rounded bg-white hover:bg-[#e4e4e7] text-black font-bold"
                >
                  Submit Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </footer>
  );
}
