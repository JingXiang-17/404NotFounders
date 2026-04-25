"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import { AnalysisShell } from "@/components/analysis-shell";
import { fetchApi } from "@/lib/api";
import { QuoteState } from "@/lib/types";

interface UploadedFile {
  id: string;
  file: File;
  status: "uploading" | "success" | "error";
  data?: QuoteState;
  error?: string;
}

export default function NewAnalysisPage() {
  const router = useRouter();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [quantity, setQuantity] = useState<number | "">("");
  const [urgency, setUrgency] = useState<"Normal" | "Urgent">("Normal");

  const uploadMutation = useMutation({
    mutationFn: async ({ file, id }: { file: File; id: string }) => {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetchApi<QuoteState>("/quotes/upload", {
        method: "POST",
        body: formData,
      });
      return { id, response };
    },
    onSuccess: ({ id, response }) => {
      setFiles((prev) =>
        prev.map((entry) => (entry.id === id ? { ...entry, status: "success", data: response } : entry)),
      );
    },
    onError: (error, variables) => {
      setFiles((prev) =>
        prev.map((entry) =>
          entry.id === variables.id ? { ...entry, status: "error", error: error.message } : entry,
        ),
      );
    },
  });

  const enqueueFiles = (selectedFiles: File[]) => {
    if (!selectedFiles.length) {
      return;
    }

    const newFiles = selectedFiles.slice(0, Math.max(0, 5 - files.length)).map((file) => ({
      id: Math.random().toString(36).slice(2),
      file,
      status: "uploading" as const,
    }));

    if (!newFiles.length) {
      return;
    }

    setFiles((prev) => [...prev, ...newFiles]);
    newFiles.forEach((entry) => {
      uploadMutation.mutate({ file: entry.file, id: entry.id });
    });
  };

  const successfulQuoteIds = files
    .map((entry) => entry.data?.extracted_quote?.quote_id ?? null)
    .filter((quoteId): quoteId is string => Boolean(quoteId));

  const isContinueEnabled = successfulQuoteIds.length >= 1 && quantity !== "" && Number(quantity) > 0;

  const handleContinue = () => {
    if (!isContinueEnabled) {
      return;
    }
    const params = new URLSearchParams({
      quoteIds: successfulQuoteIds.join(","),
      quantity: String(quantity),
      urgency: urgency.toLowerCase(),
    });
    router.push(`/analysis/new/review?${params.toString()}`);
  };

  return (
    <AnalysisShell
      currentStep="upload"
      title="Upload Documentation"
      subtitle="Stage 1 of 4: Centralized Procurement Procurement Workflow"
      actions={
        <div className="mt-4 md:mt-0 flex items-center gap-2">
          <span className="text-label-caps font-label-caps text-secondary uppercase bg-surface-container px-3 py-1 rounded">Session ID: PRQ-2024-089</span>
        </div>
      }
    >
      <div className="grid grid-cols-12 gap-gutter">
        {/* Left Column: Parameters & Requirements */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-gutter">
          {/* Workflow Progress Card */}
          <div className="bg-white border border-outline-variant p-card-padding rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
            <h3 className="text-label-caps font-label-caps text-secondary uppercase mb-stack-md">Workflow Pipeline</h3>
            <div className="space-y-stack-md">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#004aad] text-white flex items-center justify-center text-sm font-bold">1</div>
                <div className="flex-1">
                  <p className="text-body-base font-semibold text-[#004aad]">Upload Documentation</p>
                  <p className="text-[11px] text-secondary">Active Stage</p>
                </div>
                <span className="material-symbols-outlined text-[#004aad]">pending</span>
              </div>
              <div className="flex items-center gap-3 opacity-50">
                <div className="w-8 h-8 rounded-full bg-surface-container text-secondary flex items-center justify-center text-sm font-bold">2</div>
                <div className="flex-1">
                  <p className="text-body-base font-medium">Compliance Review</p>
                </div>
              </div>
              <div className="flex items-center gap-3 opacity-50">
                <div className="w-8 h-8 rounded-full bg-surface-container text-secondary flex items-center justify-center text-sm font-bold">3</div>
                <div className="flex-1">
                  <p className="text-body-base font-medium">Cost Analysis</p>
                </div>
              </div>
              <div className="flex items-center gap-3 opacity-50">
                <div className="w-8 h-8 rounded-full bg-surface-container text-secondary flex items-center justify-center text-sm font-bold">4</div>
                <div className="flex-1">
                  <p className="text-body-base font-medium">Final Decision</p>
                </div>
              </div>
            </div>
          </div>

          {/* Mandatory Input Card */}
          <div className="bg-white border border-outline-variant p-card-padding rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
            <h3 className="text-label-caps font-label-caps text-secondary uppercase mb-stack-md">Mandatory Requirements</h3>
            <div className="space-y-stack-lg">
              <div>
                <label className="block text-body-sm font-semibold text-on-background mb-1">Required Quantity</label>
                <div className="relative">
                  <input 
                    className="w-full border border-outline-variant rounded-lg p-2.5 text-body-base focus:border-[#004aad] focus:ring-1 focus:ring-[#004aad] transition-all outline-none" 
                    placeholder="Enter units (e.g. 5000)" 
                    type="number"
                    value={quantity}
                    onChange={(event) => setQuantity(event.target.value === "" ? "" : Number(event.target.value))}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-body-sm text-secondary font-medium">UNITS</span>
                </div>
              </div>
              <div>
                <label className="block text-body-sm font-semibold text-on-background mb-3">Urgency Level</label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="cursor-pointer">
                    <input 
                      className="peer sr-only" 
                      name="urgency" 
                      type="radio" 
                      value="normal"
                      checked={urgency === "Normal"}
                      onChange={() => setUrgency("Normal")}
                    />
                    <div className="flex items-center justify-center p-3 border border-outline-variant rounded-lg text-body-sm font-medium peer-checked:bg-[#004aad] peer-checked:text-white peer-checked:border-[#004aad] transition-all">
                      Normal
                    </div>
                  </label>
                  <label className="cursor-pointer">
                    <input 
                      className="peer sr-only" 
                      name="urgency" 
                      type="radio" 
                      value="urgent"
                      checked={urgency === "Urgent"}
                      onChange={() => setUrgency("Urgent")}
                    />
                    <div className="flex items-center justify-center p-3 border border-outline-variant rounded-lg text-body-sm font-medium peer-checked:bg-[#ba1a1a] peer-checked:text-white peer-checked:border-[#ba1a1a] transition-all">
                      Urgent
                    </div>
                  </label>
                </div>
              </div>
              <div className="pt-2">
                <div className="p-3 bg-surface-container-low rounded-lg border border-dashed border-outline-variant">
                  <div className="flex gap-2">
                    <span className="material-symbols-outlined text-secondary text-sm">info</span>
                    <p className="text-[11px] leading-tight text-secondary">Inputs will be used to calibrate the AI cost analysis engine in Step 3.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Main Dropzone Area */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-gutter">
          {/* Centralized Drag & Drop Area */}
          <div className="bg-white border border-outline-variant p-gutter rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col min-h-[400px]">
            <div className="flex items-center justify-between mb-stack-md">
              <h3 className="text-h2 font-h2 text-on-background">FOB Supplier Documentation</h3>
              <span className="text-body-sm text-secondary">{files.length} / 5 Files Uploaded</span>
            </div>

            <section
              className="relative flex flex-col items-center justify-center border-2 border-dashed border-outline-variant rounded-lg bg-surface-container-lowest p-10 text-center transition hover:border-[#004aad] hover:bg-slate-50 flex-1"
              onDrop={(event) => {
                event.preventDefault();
                const droppedFiles = Array.from(event.dataTransfer.files).filter(
                  (file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"),
                );
                enqueueFiles(droppedFiles);
              }}
              onDragOver={(event) => event.preventDefault()}
            >
              <input
                type="file"
                multiple
                accept=".pdf,application/pdf"
                className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                onChange={(event) => enqueueFiles(Array.from(event.target.files ?? []))}
                title="Drop quote PDFs here"
              />
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#004aad]/10 text-[#004aad]">
                <span className="material-symbols-outlined text-3xl">upload_file</span>
              </div>
              <h3 className="text-xl font-semibold text-on-background mb-2">Drag & Drop PDFs Here</h3>
              <p className="max-w-md text-sm leading-6 text-secondary mb-6">
                Ensure quotes clearly state FOB terms, supplier details, and PP Resin product specifications.
              </p>
              <div className="inline-flex rounded-md border border-outline bg-white px-5 py-2 text-sm font-semibold text-[#004aad]">
                Browse Files
              </div>
            </section>
          </div>

          {/* Upload Status List */}
          {files.length > 0 && (
            <div className="bg-white border border-outline-variant p-gutter rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
              <h3 className="text-label-caps font-label-caps text-secondary uppercase mb-stack-md">Processing Status</h3>
              <div className="space-y-3">
                {files.map((entry) => (
                  <div key={entry.id} className="flex items-center justify-between p-3 border border-outline-variant rounded-lg bg-surface-container-lowest">
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-secondary">description</span>
                      <div>
                        <p className="text-body-sm font-semibold text-on-background">{entry.file.name}</p>
                        {entry.status === "success" && entry.data && (
                          <p className="text-[11px] text-secondary">
                            {entry.data.extracted_quote?.supplier_name ?? "Supplier pending"} /{" "}
                            {entry.data.extracted_quote?.currency ?? "-"} {entry.data.extracted_quote?.unit_price?.toLocaleString() ?? "-"}
                          </p>
                        )}
                        {entry.status === "error" && (
                          <p className="text-[11px] text-[#ba1a1a]">{entry.error}</p>
                        )}
                      </div>
                    </div>
                    <div>
                      {entry.status === "uploading" && <span className="material-symbols-outlined text-[#004aad] animate-spin">refresh</span>}
                      {entry.status === "success" && <span className="material-symbols-outlined text-[#004aad]">check_circle</span>}
                      {entry.status === "error" && <span className="material-symbols-outlined text-[#ba1a1a]">error</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Proceed Button */}
          <div className="flex justify-end mt-4">
            <button
              type="button"
              disabled={!isContinueEnabled}
              onClick={handleContinue}
              className="px-6 py-3 bg-[#004aad] text-white font-semibold text-body-sm rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue to Data Review <span className="material-symbols-outlined text-base">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </AnalysisShell>
  );
}
