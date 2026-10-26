"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Bot,
  Send,
  X,
  CheckCircle2,
  Clock,
  Compass,
  MapPin,
  Cpu,
  Zap,
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
      // If robot was assigned or targeted, focus it
      if (res.target_robot && onSelectEntity) {
        onSelectEntity("robot", res.target_robot);
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to communicate with Ollama service.");
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 font-mono select-none">
      <div className="w-full max-w-2xl bg-[#11141a] border border-[#232834] rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="h-14 border-b border-[#232834] bg-[#141822] px-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-[#76b900] flex items-center justify-center text-black font-extrabold text-sm shadow-md shadow-[#76b900]/30">
              Ω
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-2">
                <span>AI MISSION PLANNER & TASK PORTAL</span>
                <span className="text-[9px] bg-[#76b900]/20 text-[#76b900] px-2 py-0.5 rounded border border-[#76b900]/40 font-semibold flex items-center gap-1">
                  <Cpu className="w-2.5 h-2.5" />
                  <span>Ollama: phi3:mini (RTX 4060 GPU)</span>
                </span>
              </div>
              <div className="text-[10px] text-white/50">
                Natural Language Autonomous Task Dispatcher
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-white/40 hover:text-white hover:bg-white/10 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {/* Natural Language Prompt Input */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="text-xs font-bold text-white/80 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#76b900]" />
              <span>Describe what you want simulated robots to do:</span>
            </label>

            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder='e.g. "Send robot 1 to Room 19", "Deliver emergency medicine to ICU 1", "Guide visitor to Pharmacy"...'
                rows={3}
                className="w-full bg-[#161a22] border border-[#272d3b] rounded-lg p-3 text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-[#76b900] focus:ring-1 focus:ring-[#76b900]/40 transition-all resize-none"
              />
            </div>

            {/* Quick Example Chips */}
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase font-bold text-white/40 tracking-wider">
                Quick-Start Mission Prompts:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLE_PROMPTS.map((ex, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectExample(ex)}
                    className="text-[11px] bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] hover:border-[#76b900]/40 text-white/70 px-2.5 py-1 rounded-md border border-white/10 transition-all text-left"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-2 flex items-center justify-between">
              <div className="text-[11px] text-white/40 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-[#76b900]" />
                <span>Runs 100% locally with zero cloud delay.</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 text-xs transition-all"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !prompt.trim()}
                  className="px-4 py-1.5 rounded-lg bg-[#76b900] hover:bg-[#68a300] text-black font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-[#76b900]/20 transition-all disabled:opacity-40"
                >
                  {isLoading ? (
                    <>
                      <div className="w-3 h-3 rounded-full border-2 border-black border-t-transparent animate-spin" />
                      <span>Interpreting via Ollama...</span>
                    </>
                  ) : (
                    <>
                      <span>Dispatch via Ollama</span>
                      <Send className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-rose-300 text-xs flex items-center gap-2">
              <X className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Real-time LLM Output Card */}
          {result && (
            <div className="p-4 bg-[#141822] border border-[#76b900]/50 rounded-xl space-y-3 animate-in fade-in duration-200">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <div className="flex items-center gap-2 text-xs font-bold text-[#76b900]">
                  <CheckCircle2 className="w-4 h-4 text-[#76b900]" />
                  <span>MISSION DISPATCHED SUCCESSFULLY</span>
                </div>
                <span className="text-[10px] bg-[#76b900]/20 text-[#76b900] px-2 py-0.5 rounded border border-[#76b900]/40 uppercase font-semibold">
                  Parsed by {result.parsed_by || "Ollama"}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="bg-[#11141a] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] text-white/40 uppercase">Task Type</div>
                  <div className="font-bold text-white capitalize mt-0.5">
                    {result.task_type ? result.task_type.replace(/_/g, " ") : "Action"}
                  </div>
                </div>

                <div className="bg-[#11141a] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] text-white/40 uppercase">Destination</div>
                  <div className="font-bold text-cyan-400 mt-0.5 flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    <span>{result.location || "Hospital"}</span>
                  </div>
                </div>

                <div className="bg-[#11141a] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] text-white/40 uppercase">Assigned AMR</div>
                  <div className="font-bold text-[#76b900] mt-0.5 flex items-center gap-1">
                    <Bot className="w-3 h-3" />
                    <span>{result.target_robot || "Nearest Available"}</span>
                  </div>
                </div>

                <div className="bg-[#11141a] p-2.5 rounded-lg border border-white/5">
                  <div className="text-[10px] text-white/40 uppercase">Priority</div>
                  <div className="font-bold text-rose-400 mt-0.5">
                    P{result.priority || 4} Critical
                  </div>
                </div>
              </div>

              {result.description && (
                <div className="text-xs text-white/70 bg-[#11141a] p-2.5 rounded-lg border border-white/5 flex items-start gap-2">
                  <ArrowRight className="w-3.5 h-3.5 text-[#76b900] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-white">Directive: </span>
                    <span>{result.description}</span>
                  </div>
                </div>
              )}

              <div className="flex justify-end pt-1">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-1 rounded bg-[#76b900]/20 hover:bg-[#76b900]/30 text-[#76b900] text-xs font-bold transition-all border border-[#76b900]/40"
                >
                  View AMR Navigation in 3D Viewport →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
