"use client";

import React, { useState } from "react";
import {
  Send,
  X,
  CheckCircle2,
  Terminal,
  ArrowRight
} from "lucide-react";
import { sendNaturalCommand, FARSverseSnapshot } from "@/lib/farsverse-api";

interface AITaskPortalModalProps {
  isOpen: boolean;
  onClose: () => void;
  snapshot: FARSverseSnapshot | null;
  onSelectEntity?: (type: string, id: string) => void;
}

const EXAMPLE_PROMPTS = [
  "Send robot 1 to Room 19 to check on the patient",
  "Deliver emergency medication to ICU 1 immediately",
  "Guide visitor from Main Entrance to Pharmacy",
  "Dispatch robot 2 to inspect Emergency Department",
  "Send nearest robot to Charging Dock to recharge",
  "Check Patient Room 5 for routine morning vitals",
];

export function AITaskPortalModal({
  isOpen,
  onClose,
  snapshot,
  onSelectEntity,
}: AITaskPortalModalProps) {
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await sendNaturalCommand(prompt.trim());
      setResult(res);
      if (res.target_robot && onSelectEntity) {
        onSelectEntity("robot", res.target_robot);
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to communicate with local Ollama runtime.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectExample = (text: string) => {
    setPrompt(text);
    setError(null);
    setResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 font-mono select-none">
      <div className="w-full max-w-2xl bg-[#09090b] border border-[#27272a] rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="h-12 border-b border-[#27272a] bg-[#000000] px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-white" />
            <span className="text-xs font-bold text-white tracking-wider uppercase">MISSION DISPATCH TERMINAL</span>
            <span className="text-[10px] text-[#71717a]">|</span>
            <span className="text-[10px] text-[#a1a1aa]">Ollama (phi3:mini / RTX 4060)</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#71717a] hover:text-white transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 overflow-y-auto space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="text-[11px] font-bold text-white block">
              Autonomous Robot Directive:
            </label>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder='Enter directive, e.g. "Deliver emergency medication to ICU 1", "Send Rob-1 to Pharmacy"...'
              rows={3}
              className="w-full bg-[#000000] border border-[#27272a] rounded p-2.5 text-xs text-white placeholder:text-[#52525b] focus:outline-none focus:border-white transition-all resize-none font-mono"
            />

            {/* Quick Directive Chips */}
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase font-bold text-[#71717a] tracking-wider">
                Preset Directives:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLE_PROMPTS.map((ex, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectExample(ex)}
                    className="text-[11px] bg-[#121214] hover:bg-white hover:text-black text-[#a1a1aa] px-2.5 py-1 rounded border border-[#27272a] transition-all text-left"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-2 flex items-center justify-between border-t border-[#27272a]">
              <span className="text-[10px] text-[#71717a]">Local GPU inference (zero cloud latency).</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-1.5 rounded bg-[#18181b] hover:bg-[#27272a] text-[#a1a1aa] text-xs transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !prompt.trim()}
                  className="px-4 py-1.5 rounded bg-white hover:bg-[#e4e4e7] text-black font-bold text-xs flex items-center gap-1.5 transition-all disabled:opacity-40"
                >
                  <span>{isLoading ? "Compiling Plan..." : "Execute Mission"}</span>
                  <Send className="w-3 h-3" />
                </button>
              </div>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="border border-[#3f3f46] rounded p-3 bg-[#18181b] text-white text-xs">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Parsed Result Card */}
          {result && (
            <div className="border border-[#27272a] rounded p-3 bg-[#000000] space-y-2 text-xs">
              <div className="flex items-center justify-between text-white font-bold border-b border-[#27272a] pb-1.5">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-white" />
                  <span>Mission Assigned to Simulation Engine</span>
                </span>
                <span className="text-[10px] text-[#71717a]">PARSED BY: {result.parsed_by?.toUpperCase()}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                  <span className="text-[#71717a] block text-[10px]">TASK TYPE</span>
                  <span className="font-bold text-white">{result.task_type || "Generic Task"}</span>
                </div>
                <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                  <span className="text-[#71717a] block text-[10px]">DESTINATION</span>
                  <span className="font-bold text-white">{result.location || "Main Corridor"}</span>
                </div>
                <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                  <span className="text-[#71717a] block text-[10px]">ASSIGNED AMR</span>
                  <span className="font-bold text-white">{result.target_robot || "Auto (Nearest Available)"}</span>
                </div>
                <div className="bg-[#121214] p-2 rounded border border-[#18181b]">
                  <span className="text-[#71717a] block text-[10px]">PRIORITY</span>
                  <span className="font-bold text-white">Priority {result.priority || 4}</span>
                </div>
              </div>

              {result.description && (
                <div className="text-[11px] text-[#a1a1aa] bg-[#121214] p-2 rounded border border-[#18181b]">
                  <span className="text-[#71717a] block text-[10px] mb-0.5">DIRECTIVE SUMMARY</span>
                  {result.description}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
