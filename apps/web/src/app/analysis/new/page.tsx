"use client";

import { useState, useCallback } from "react";
import { CloudUpload, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import { ExtractedQuote } from "@/lib/types";

interface UploadedFile {
  id: string;
  file: File;
  status: "uploading" | "success" | "error";
  data?: ExtractedQuote;
  error?: string;
}

export default function NewAnalysisPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [quantity, setQuantity] = useState<number | "">("");
  const [urgency, setUrgency] = useState<"Normal" | "Urgent">("Normal");
  
  // mutation
  const uploadMutation = useMutation({
    mutationFn: async ({ file, id }: { file: File, id: string }) => {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await fetchApi<ExtractedQuote>("/quotes/upload", {
        method: "POST",
        body: formData,
      });
      return { id, response };
    },
    onSuccess: ({ id, response }) => {
      setFiles((prev) =>
        prev.map((f) => (f.id === id ? { ...f, status: "success", data: response } : f))
      );
    },
    onError: (error, variables) => {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === variables.id ? { ...f, status: "error", error: error.message } : f
        )
      );
    },
  });

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.type === "application/pdf" || f.name.endsWith('.pdf'));
    
    if (droppedFiles.length === 0) return;
    
    const newFiles = droppedFiles.slice(0, 5 - files.length).map((file) => ({
      id: Math.random().toString(36).substring(7),
      file,
      status: "uploading" as const,
    }));
    
    setFiles((prev) => [...prev, ...newFiles]);
    
    newFiles.forEach((newFile) => {
      uploadMutation.mutate({ file: newFile.file, id: newFile.id });
    });
  }, [files, uploadMutation]);

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const selectedFiles = Array.from(e.target.files);
    
    const newFiles = selectedFiles.slice(0, 5 - files.length).map((file) => ({
      id: Math.random().toString(36).substring(7),
      file,
      status: "uploading" as const,
    }));
    
    setFiles((prev) => [...prev, ...newFiles]);
    
    newFiles.forEach((newFile) => {
      uploadMutation.mutate({ file: newFile.file, id: newFile.id });
    });
  };

  const isContinueEnabled = files.filter(f => f.status === "success").length >= 2 && quantity !== "" && Number(quantity) > 0;

  return (
    <div className="flex flex-col flex-1 items-center bg-background px-4 sm:px-6 py-8 min-h-screen">
      <div className="w-full max-w-4xl space-y-8">
        {/* Stepper */}
        <div className="flex items-center justify-between border-b border-border pb-4 mb-8">
          {[
            { step: 1, label: "Upload Quotes", active: true },
            { step: 2, label: "Review", active: false },
            { step: 3, label: "Analysis", active: false },
            { step: 4, label: "Decision", active: false },
          ].map((s, idx, arr) => (
            <div key={s.step} className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold border ${
                s.active ? "bg-primary text-[#06060A] border-primary" : "bg-surface text-secondary-text border-border"
              }`}>
                {s.step}
              </div>
              <span className={`ml-3 text-sm font-medium ${s.active ? "text-foreground" : "text-secondary-text"}`}>
                {s.label}
              </span>
              {idx < arr.length - 1 && (
                <div className="hidden sm:block w-12 md:w-24 h-px bg-border mx-4" />
              )}
            </div>
          ))}
        </div>

        {/* Upload Zone */}
        <div 
          className="border-2 border-dashed border-primary/50 rounded-[12px] bg-surface p-12 text-center transition-colors hover:border-primary cursor-pointer relative"
          onDrop={onDrop}
          onDragOver={onDragOver}
        >
          <input 
            type="file" 
            multiple 
            accept=".pdf,application/pdf" 
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleFileSelect}
            title="Drop quotes here"
          />
          <CloudUpload className="mx-auto h-12 w-12 text-primary mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Drop up to 5 FOB PP Resin quote PDFs here</h3>
          <p className="text-sm text-secondary-text">Or click to browse files</p>
        </div>

        {/* File Cards */}
        {files.length > 0 && (
          <div className="space-y-4 mt-8">
            <h4 className="text-sm font-semibold text-secondary-text uppercase tracking-wider">Uploaded Quotes</h4>
            {files.map((f) => (
              <div key={f.id} className="flex items-center justify-between p-4 bg-surface border border-border rounded-[8px]">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-background rounded">
                    <FileText className="h-5 w-5 text-secondary-text" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{f.file.name}</p>
                    {f.status === "success" && f.data && (
                      <p className="text-xs text-secondary-text mt-1">
                        {f.data.supplier_name} • {f.data.currency} {f.data.price?.toLocaleString()}
                      </p>
                    )}
                    {f.status === "error" && (
                      <p className="text-xs text-red-400 mt-1">{f.error}</p>
                    )}
                  </div>
                </div>
                <div>
                  {f.status === "uploading" && <Loader2 className="h-5 w-5 text-primary animate-spin" />}
                  {f.status === "success" && <CheckCircle2 className="h-5 w-5 text-primary" />}
                  {f.status === "error" && <AlertCircle className="h-5 w-5 text-red-400" />}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8 p-6 bg-surface border border-border rounded-[12px]">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Required Quantity (MT)</label>
            <input 
              type="number" 
              value={quantity}
              onChange={(e) => setQuantity(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="e.g. 100"
              className="w-full h-10 px-3 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Urgency</label>
            <select 
              value={urgency}
              onChange={(e) => setUrgency(e.target.value as "Normal" | "Urgent")}
              className="w-full h-10 px-3 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary appearance-none"
            >
              <option value="Normal">Normal</option>
              <option value="Urgent">Urgent</option>
            </select>
          </div>
        </div>

        {/* Action */}
        <div className="flex justify-end pt-6">
          <button 
            disabled={!isContinueEnabled}
            className="h-12 px-8 rounded-[8px] bg-primary text-[#06060A] font-semibold hover:bg-[#00e0bb] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Continue to Review
          </button>
        </div>
      </div>
    </div>
  );
}
