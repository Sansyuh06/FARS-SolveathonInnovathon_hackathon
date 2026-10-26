"use client";

import React, { useState, useEffect } from "react";
import { X, Upload, CheckCircle2, AlertCircle, FileBox } from "lucide-react";
import { uploadAssetFile, listAssets } from "@/lib/farsverse-api";

interface AssetUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AssetUploadModal({ isOpen, onClose }: AssetUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [assets, setAssets] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen) {
      loadAssets();
    }
  }, [isOpen]);

  const loadAssets = async () => {
    try {
      const data = await listAssets();
      setAssets(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
      if (![".glb", ".gltf"].includes(ext)) {
        setErrorMsg("Only .glb and .gltf files are supported.");
        setFile(null);
        return;
      }
      setErrorMsg(null);
      setFile(f);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await uploadAssetFile(file);
      if (res.id) {
        setSuccessMsg(`Asset '${file.name}' imported successfully.`);
        setFile(null);
        loadAssets();
      } else {
        setErrorMsg(res.detail || "Upload failed.");
      }
    } catch (e: any) {
      setErrorMsg(e.message || "Network error uploading model.");
    } finally {
      setUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-[#0c1018] border border-white/10 rounded-lg p-5 font-mono text-xs space-y-4 select-none">
        <div className="flex justify-between items-center border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <FileBox className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-sm text-white">3D Asset Manager (.glb / .gltf)</h3>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Upload Drop Area */}
        <div className="border-2 border-dashed border-white/15 rounded-lg p-6 text-center space-y-2 hover:border-cyan-500/50 transition-all bg-black/20">
          <Upload className="w-8 h-8 text-cyan-400 mx-auto" />
          <div className="text-white font-medium">Select a 3D robot or environment model</div>
          <div className="text-[10px] text-white/40">Supported formats: GLB, glTF (Max size 50 MB)</div>
          <input
            type="file"
            accept=".glb,.gltf"
            onChange={handleFileChange}
            className="block w-full text-xs text-white/50 file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-cyan-600/30 file:text-cyan-300 hover:file:bg-cyan-600/40 cursor-pointer pt-2"
          />
        </div>

        {errorMsg && (
          <div className="p-2 rounded bg-rose-950/60 border border-rose-800 text-rose-300 flex items-center gap-1.5 text-[11px]">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-2 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 flex items-center gap-1.5 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Existing Assets */}
        <div className="space-y-1.5 pt-2">
          <div className="text-white/50 text-[10px] font-bold uppercase">Imported Asset Library ({assets.length})</div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
            {assets.length > 0 ? (
              assets.map((a) => (
                <div key={a.id} className="p-2 rounded bg-[#111622] border border-white/5 flex items-center justify-between text-[11px]">
                  <div>
                    <div className="text-white font-semibold truncate">{a.name}</div>
                    <div className="text-[9px] text-white/40">{(a.file_size / 1024).toFixed(0)} KB | {a.file_type}</div>
                  </div>
                  <span className="text-[9px] bg-cyan-950 text-cyan-400 px-1.5 py-0.5 rounded border border-cyan-800">
                    Ready
                  </span>
                </div>
              ))
            ) : (
              <div className="text-white/30 text-center py-4 italic">No custom assets uploaded yet.</div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-white/70 text-xs"
          >
            Close
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs disabled:opacity-40"
          >
            {uploading ? "Importing Model..." : "Import Model"}
          </button>
        </div>
      </div>
    </div>
  );
}
