"use client";

import React, { useState, useEffect } from "react";
import { X, FolderOpen, Plus, Save, Trash2, CheckCircle2 } from "lucide-react";
import { listProjects, getProject, saveProject, deleteProject, sendControl } from "@/lib/farsverse-api";

interface ProjectsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentProject: any;
  onLoadProject: (project: any) => void;
}

export function ProjectsModal({ isOpen, onClose, currentProject, onLoadProject }: ProjectsModalProps) {
  const [projects, setProjects] = useState<any[]>([]);
  const [newProjName, setNewProjName] = useState("");
  const [newProjEnv, setNewProjEnv] = useState("hospital");
  const [isCreating, setIsCreating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadList();
    }
  }, [isOpen]);

  const loadList = async () => {
    try {
      const data = await listProjects();
      setProjects(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelect = async (id: string) => {
    try {
      const proj = await getProject(id);
      if (proj) {
        onLoadProject(proj);
        sendControl("load_environment", { template: proj.environment_type });
        onClose();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjName.trim()) return;
    const newId = `proj_${Date.now()}`;
    try {
      await saveProject({
        id: newId,
        name: newProjName.trim(),
        description: `Custom ${newProjEnv} project`,
        environment_type: newProjEnv,
        world_data: {},
        robot_configs: [],
        scenario_config: { human_count: 15 },
      });
      setStatusMsg(`Project '${newProjName}' created.`);
      setNewProjName("");
      setIsCreating(false);
      loadList();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      await deleteProject(id);
      loadList();
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-xl bg-[#0c1018] border border-white/10 rounded-lg p-5 font-mono text-xs space-y-4 select-none">
        <div className="flex justify-between items-center border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-sm text-white">Project Library & Templates</h3>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {statusMsg && (
          <div className="p-2 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 flex items-center gap-1.5 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{statusMsg}</span>
          </div>
        )}

        {/* Existing Projects List */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <span className="text-white/50 text-[10px] font-bold uppercase">Saved Projects ({projects.length})</span>
            <button
              onClick={() => setIsCreating(!isCreating)}
              className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 text-[11px]"
            >
              <Plus className="w-3 h-3" />
              <span>New Project</span>
            </button>
          </div>

          {isCreating && (
            <form onSubmit={handleCreateNew} className="p-3 rounded bg-[#111622] border border-cyan-500/30 space-y-2">
              <div className="text-white font-bold text-xs">Create New Project</div>
              <input
                type="text"
                value={newProjName}
                onChange={(e) => setNewProjName(e.target.value)}
                placeholder="Project Name (e.g. City Hospital Wing B)"
                className="w-full bg-[#0a0d14] border border-white/10 rounded p-1.5 text-xs text-white"
              />
              <div className="flex gap-2">
                <select
                  value={newProjEnv}
                  onChange={(e) => setNewProjEnv(e.target.value)}
                  className="flex-1 bg-[#0a0d14] border border-white/10 rounded p-1.5 text-xs text-white"
                >
                  <option value="hospital">Hospital Environment</option>
                  <option value="campus">Campus Quad Environment</option>
                  <option value="warehouse">Warehouse Environment</option>
                  <option value="empty">Blank Sandbox Workspace</option>
                </select>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
                >
                  Create
                </button>
              </div>
            </form>
          )}

          <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1">
            {projects.map((p) => (
              <div
                key={p.id}
                onClick={() => handleSelect(p.id)}
                className="p-3 rounded bg-[#111622] hover:bg-cyan-950/40 border border-white/5 hover:border-cyan-500/40 cursor-pointer flex items-center justify-between transition-all"
              >
                <div>
                  <div className="font-bold text-white text-xs flex items-center gap-2">
                    <span>{p.name}</span>
                    <span className="text-[10px] bg-white/10 text-white/50 px-1.5 py-0.2 rounded uppercase">
                      {p.environment_type}
                    </span>
                  </div>
                  <div className="text-[10px] text-white/40 mt-0.5">{p.description}</div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-cyan-400 font-semibold">{p.robot_count} Robots</span>
                  {!p.id.startsWith("proj_hospital_flagship") && (
                    <button
                      onClick={(e) => handleDelete(p.id, e)}
                      title="Delete Project"
                      className="p-1 rounded text-white/20 hover:text-rose-400 hover:bg-rose-950/40"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end pt-3 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-white/5 hover:bg-white/10 text-white/70 text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
