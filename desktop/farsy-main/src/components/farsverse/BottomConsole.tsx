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
  Search,
  AlertCircle,
  Info,
  AlertTriangle,
  Sparkles
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
  const [activeTab, setActiveTab] = useState<"tasks" | "events" | "metrics" | "experiments" | "raw">("tasks");
  const [eventFilter, setEventFilter] = useState<"ALL" | "INFO" | "WARN" | "ERROR">("ALL");
  const [eventSearch, setEventSearch] = useState("");

  // New task modal
  const [showNewTaskDialog, setShowNewTaskDialog] = useState(false);
  const [newTaskType, setNewTaskType] = useState("assist_patient");
  const [newTaskDest, setNewTaskDest] = useState("Room1");
  const [newTaskPrio, setNewTaskPrio] = useState(2);
  const [newTaskDesc, setNewTaskDesc] = useState("");

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createManualTask(newTaskType, newTaskDest, newTaskPrio, newTaskDesc);
      setShowNewTaskDialog(false);
      setNewTaskDesc("");
    } catch (err) {
      console.error(err);
    }
  };

  const tasksPending = snapshot?.tasks?.pending || [];
  const tasksActive = snapshot?.tasks?.active || [];
  const tasksCompleted = snapshot?.tasks?.completed || [];
  const events = snapshot?.events || [];
  const metricsHistory = snapshot?.metrics_history || [];

  const filteredEvents = events.filter((e) => {
    if (eventFilter !== "ALL" && e.severity !== eventFilter) return false;
    if (eventSearch && !e.message.toLowerCase().includes(eventSearch.toLowerCase())) return false;
    return true;
  });

  return (
    <footer
      className={`bg-[#0a0d14] border-t border-white/10 flex flex-col select-none transition-all duration-200 z-10 ${
        isCollapsed ? "h-9" : "h-64"
      }`}
    >
      {/* Console Tab Bar */}
      <div className="h-9 bg-[#080b10] border-b border-white/10 px-3 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-1">
          {[
            { id: "tasks", label: `Tasks (${tasksActive.length + tasksPending.length})`, icon: ListTodo },
            { id: "events", label: `Events (${events.length})`, icon: Terminal },
            { id: "metrics", label: "Live Metrics", icon: LineChart },
            { id: "experiments", label: "Analysis Runs", icon: FlaskConical },
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
                    ? "bg-[#0c1018] text-cyan-400 font-bold border-t border-x border-cyan-500/30"
                    : "text-white/50 hover:text-white"
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
            <>
              {onOpenAITaskPortal && (
                <button
                  onClick={onOpenAITaskPortal}
                  className="px-2.5 py-0.5 rounded bg-[#76b900]/20 hover:bg-[#76b900]/30 text-[#76b900] text-[11px] font-bold border border-[#76b900]/40 flex items-center gap-1.5 transition-all shadow-[0_0_10px_rgba(118,185,0,0.2)]"
                  title="Dispatch tasks with natural language using local Ollama LLM"
                >
                  <Sparkles className="w-3 h-3 text-[#76b900]" />
                  <span>AI Mission Portal (Ollama)</span>
                </button>
              )}
              <button
                onClick={() => setShowNewTaskDialog(true)}
                className="px-2 py-0.5 rounded bg-cyan-600/30 hover:bg-cyan-500/40 text-cyan-300 text-[11px] font-bold border border-cyan-500/40 flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                <span>Create Task</span>
              </button>
            </>
          )}

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 text-white/50 hover:text-white rounded"
            title={isCollapsed ? "Expand Console" : "Collapse Console"}
          >
            {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Console Body */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-3 text-xs font-mono bg-[#0c1018]">
          {/* TAB 1: TASK QUEUE TABLE */}
          {activeTab === "tasks" && (
            <div className="space-y-3">
              <div className="grid grid-cols-12 text-[10px] uppercase font-bold text-white/40 border-b border-white/10 pb-1 px-2">
                <div className="col-span-1">ID</div>
                <div className="col-span-2">Type</div>
                <div className="col-span-2">Destination</div>
                <div className="col-span-1">Priority</div>
                <div className="col-span-2">Assigned Robot</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-2 text-right">Action</div>
              </div>

              {/* Tasks List */}
              <div className="space-y-1">
                {[...tasksActive, ...tasksPending].length > 0 ? (
                  [...tasksActive, ...tasksPending].map((t) => (
                    <div
                      key={t.id}
                      className="grid grid-cols-12 text-[11px] py-1.5 px-2 rounded bg-[#111622] hover:bg-white/5 border border-white/5 items-center"
                    >
                      <div className="col-span-1 font-bold text-white/60">#{t.id}</div>
                      <div className="col-span-2 text-white capitalize">{t.task_type.replace("_", " ")}</div>
                      <div className="col-span-2 text-cyan-400 font-semibold">{t.location_node}</div>
                      <div className="col-span-1">
                        <span
                          className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                            t.priority === 4
                              ? "bg-rose-950 text-rose-400 border border-rose-800"
                              : t.priority === 3
                              ? "bg-amber-950 text-amber-400 border border-amber-800"
                              : "bg-blue-950 text-blue-400 border border-blue-800"
                          }`}
                        >
                          P{t.priority}
                        </span>
                      </div>
                      <div className="col-span-2">
                        {t.assigned_robot ? (
                          <button
                            onClick={() => onSelectEntity("robot", t.assigned_robot)}
                            className="text-cyan-400 hover:underline font-semibold"
                          >
                            {t.assigned_robot}
                          </button>
                        ) : (
                          <span className="text-white/30 italic">Unassigned</span>
                        )}
                      </div>
                      <div className="col-span-2 uppercase text-[10px] font-bold text-white/70">
                        {t.status}
                      </div>
                      <div className="col-span-2 text-right">
                        {t.status === "pending" && (
                          <button
                            onClick={() => cancelTask(t.id)}
                            className="px-2 py-0.5 rounded text-[10px] bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-white/40 text-center py-6 italic">
                    Task queue idle. No pending or active robot assignments.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: SYSTEM EVENT FEED */}
          {activeTab === "events" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-white/10">
                <div className="flex gap-1.5">
                  {(["ALL", "INFO", "WARN", "ERROR"] as const).map((sev) => (
                    <button
                      key={sev}
                      onClick={() => setEventFilter(sev)}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                        eventFilter === sev
                          ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                          : "text-white/40 hover:text-white"
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>

                <div className="relative w-48">
                  <Search className="w-3 h-3 text-white/40 absolute left-2 top-1.5" />
                  <input
                    type="text"
                    value={eventSearch}
                    onChange={(e) => setEventSearch(e.target.value)}
                    placeholder="Search logs..."
                    className="w-full bg-[#111622] border border-white/10 rounded pl-7 pr-2 py-0.5 text-[10px] text-white"
                  />
                </div>
              </div>

              <div className="space-y-1 max-h-44 overflow-y-auto pr-1">
                {filteredEvents.length > 0 ? (
                  [...filteredEvents].reverse().map((evt) => (
                    <div
                      key={evt.id}
                      className="p-1.5 rounded bg-[#111622] border border-white/5 flex items-start gap-2 text-[11px]"
                    >
                      <span className="text-[10px] font-mono text-cyan-400 whitespace-nowrap pt-0.5">
                        +{evt.sim_time}s
                      </span>
                      <span
                        className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase whitespace-nowrap ${
                          evt.severity === "ERROR"
                            ? "bg-rose-950 text-rose-400 border border-rose-800"
                            : evt.severity === "WARN"
                            ? "bg-amber-950 text-amber-400 border border-amber-800"
                            : "bg-blue-950 text-blue-400 border border-blue-800"
                        }`}
                      >
                        {evt.severity}
                      </span>
                      <span className="text-white/40 text-[10px] uppercase whitespace-nowrap">
                        [{evt.category}]
                      </span>
                      <span className="text-white/80 flex-1">{evt.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-white/40 text-center py-6 italic">No event logs matching filter.</div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: LIVE METRICS CHARTS */}
          {activeTab === "metrics" && (
            <div className="h-44 grid grid-cols-2 gap-4">
              <div className="bg-[#111622] p-2 rounded border border-white/5 flex flex-col">
                <div className="text-[10px] text-white/60 font-bold uppercase mb-1">
                  Active Robots vs Completed Tasks Over Time
                </div>
                <div className="flex-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <ReLineChart data={metricsHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="sim_time" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", fontSize: "10px" }}
                      />
                      <Line type="monotone" dataKey="active_robots" stroke="#06b6d4" strokeWidth={2} dot={false} name="Active Robots" />
                      <Line type="monotone" dataKey="completed_tasks" stroke="#10b981" strokeWidth={2} dot={false} name="Completed Tasks" />
                    </ReLineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-[#111622] p-2 rounded border border-white/5 flex flex-col">
                <div className="text-[10px] text-white/60 font-bold uppercase mb-1">
                  Average Fleet Battery Drain Over Time
                </div>
                <div className="flex-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <ReLineChart data={metricsHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="sim_time" stroke="#64748b" tick={{ fontSize: 9 }} />
                      <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 9 }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", fontSize: "10px" }}
                      />
                      <Line type="monotone" dataKey="avg_battery" stroke="#f59e0b" strokeWidth={2} dot={false} name="Avg Battery %" />
                    </ReLineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: EXPERIMENT RUNS HISTORY */}
          {activeTab === "experiments" && (
            <div className="text-white/60 space-y-2">
              <div className="text-[11px] text-white/80 font-bold">Recorded Simulation Benchmark Runs</div>
              <div className="border border-white/5 rounded overflow-hidden">
                <div className="grid grid-cols-6 text-[10px] uppercase font-bold text-white/40 bg-black/40 p-2">
                  <div>Run ID</div>
                  <div>Fleet Size</div>
                  <div>Tasks Done</div>
                  <div>Completion %</div>
                  <div>Avg Response</div>
                  <div>Total Travel</div>
                </div>
                <div className="p-2 text-center text-white/40 italic">
                  Launch runs from the "Labs" tab on the left sidebar to generate comparative performance charts.
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* CREATE NEW TASK MODAL */}
      {showNewTaskDialog && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateTask}
            className="w-full max-w-md bg-[#0c1018] border border-white/10 rounded-lg p-4 font-mono space-y-3"
          >
            <div className="flex justify-between items-center border-b border-white/10 pb-2">
              <h3 className="font-bold text-sm text-white">Create New Robot Task</h3>
              <button
                type="button"
                onClick={() => setShowNewTaskDialog(false)}
                className="text-white/40 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="text-[10px] text-white/60 block mb-1">Task Type</label>
              <select
                value={newTaskType}
                onChange={(e) => setNewTaskType(e.target.value)}
                className="w-full bg-[#111622] border border-white/10 rounded p-1.5 text-xs text-white"
              >
                <option value="assist_patient">Assist Patient</option>
                <option value="deliver_medicine">Deliver Medication</option>
                <option value="guide_patient">Guide Patient / Visitor</option>
                <option value="check_room">Patrol / Check Room</option>
                <option value="return_to_charge">Return to Charging Dock</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-white/60 block mb-1">Destination</label>
              <select
                value={newTaskDest}
                onChange={(e) => setNewTaskDest(e.target.value)}
                className="w-full bg-[#111622] border border-white/10 rounded p-1.5 text-xs text-white"
              >
                {snapshot?.world?.rooms.map((rm) => (
                  <option key={rm.id} value={rm.id}>
                    {rm.name} ({rm.id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-white/60 block mb-1">Priority</label>
              <div className="flex gap-2">
                {[
                  { prio: 1, label: "P1 Low" },
                  { prio: 2, label: "P2 Normal" },
                  { prio: 3, label: "P3 High" },
                  { prio: 4, label: "P4 Critical" },
                ].map((item) => (
                  <button
                    key={item.prio}
                    type="button"
                    onClick={() => setNewTaskPrio(item.prio)}
                    className={`flex-1 py-1 rounded text-[11px] border ${
                      newTaskPrio === item.prio
                        ? "bg-cyan-500/20 text-cyan-400 border-cyan-500 font-bold"
                        : "bg-white/5 text-white/50 border-white/10"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-[10px] text-white/60 block mb-1">Description (Optional)</label>
              <input
                type="text"
                value={newTaskDesc}
                onChange={(e) => setNewTaskDesc(e.target.value)}
                placeholder="e.g. Deliver antibiotics to Room 12"
                className="w-full bg-[#111622] border border-white/10 rounded p-1.5 text-xs text-white"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
              <button
                type="button"
                onClick={() => setShowNewTaskDialog(false)}
                className="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-white/70 text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
              >
                Create Task
              </button>
            </div>
          </form>
        </div>
      )}
    </footer>
  );
}
