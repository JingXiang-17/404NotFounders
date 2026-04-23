"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, CloudUpload, FileText, Loader2 } from "lucide-react";

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
      title="Upload your supplier quotes"
      subtitle="Drop up to five FOB PP Resin PDFs, verify the quantity request, and keep the workflow inside the actual procurement steps the backend supports."
      actions={
        <div className="rounded-full border border-border bg-surface px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-secondary-text">
          Max 5 quotes / PDF only
        </div>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section
          className="relative overflow-hidden rounded-2xl border border-border bg-surface"
          onDrop={(event) => {
            event.preventDefault();
            const droppedFiles = Array.from(event.dataTransfer.files).filter(
              (file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"),
            );
            enqueueFiles(droppedFiles);
          }}
          onDragOver={(event) => event.preventDefault()}
        >
          <div className="border-b border-border px-6 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10 text-primary">
                <CloudUpload size={22} />
              </div>
              <div>
                <h2 className="text-2xl font-semibold tracking-[-0.03em] text-foreground">Quote intake</h2>
                <p className="mt-1 text-sm text-secondary-text">Upload raw supplier PDFs and let the extractor validate them.</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <label className="relative flex min-h-[320px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-primary/40 bg-background px-6 py-10 text-center transition hover:border-primary">
              <input
                type="file"
                multiple
                accept=".pdf,application/pdf"
                className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                onChange={(event) => enqueueFiles(Array.from(event.target.files ?? []))}
                title="Drop quote PDFs here"
              />
              <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-[1.5rem] border border-primary/30 bg-primary/10 text-primary shadow-[0_0_0_1px_rgba(13,255,214,0.08),0_0_30px_rgba(13,255,214,0.08)]">
                <CloudUpload size={34} />
              </div>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-foreground">Drop quote PDFs here</h3>
              <p className="mt-3 max-w-md text-sm leading-6 text-secondary-text">
                Keep uploads within scope: PP Resin, FOB terms, and suppliers relevant to Port Klang import decisions.
              </p>
              <div className="mt-8 inline-flex rounded-full border border-border bg-surface px-5 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-secondary-text">
                Click to browse or drag files in
              </div>
            </label>
          </div>
        </section>

        <div className="flex flex-col gap-6">
          <section className="rounded-2xl border border-border bg-surface">
            <div className="border-b border-border px-6 py-4">
              <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-secondary-text">Request setup</h2>
            </div>
            <div className="space-y-5 p-6">
              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-[0.18em] text-secondary-text">Required quantity (MT)</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value === "" ? "" : Number(event.target.value))}
                  placeholder="e.g. 100"
                  className="h-12 w-full rounded-xl border border-border bg-background px-4 text-foreground outline-none transition focus:border-primary"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-[0.18em] text-secondary-text">Urgency</label>
                <select
                  value={urgency}
                  onChange={(event) => setUrgency(event.target.value as "Normal" | "Urgent")}
                  className="h-12 w-full rounded-xl border border-border bg-background px-4 text-foreground outline-none transition focus:border-primary"
                >
                  <option value="Normal">Normal</option>
                  <option value="Urgent">Urgent</option>
                </select>
              </div>
              <button
                type="button"
                disabled={!isContinueEnabled}
                onClick={handleContinue}
                className="inline-flex h-12 w-full items-center justify-center rounded-xl bg-primary px-6 text-sm font-semibold text-background transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Continue to Review
              </button>
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-surface">
            <div className="border-b border-border px-6 py-4">
              <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-secondary-text">Upload status</h2>
            </div>
            <div className="space-y-3 p-4">
              {files.length === 0 ? (
                <div className="rounded-xl border border-border bg-background p-5 text-sm leading-6 text-secondary-text">
                  No files uploaded yet. Once PDFs are processed, this panel will show supplier extraction and validation status.
                </div>
              ) : null}

              {files.map((entry) => (
                <div key={entry.id} className="rounded-xl border border-border bg-background p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl border border-border bg-surface p-3 text-secondary-text">
                        <FileText size={18} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-foreground">{entry.file.name}</div>
                        {entry.status === "success" && entry.data ? (
                          <p className="mt-1 text-sm text-secondary-text">
                            {entry.data.extracted_quote?.supplier_name ?? "Supplier pending"} /{" "}
                            {entry.data.extracted_quote?.currency ?? "-"}{" "}
                            {entry.data.extracted_quote?.unit_price?.toLocaleString() ?? "-"}
                          </p>
                        ) : null}
                        {entry.status === "error" ? <p className="mt-1 text-sm text-red-400">{entry.error}</p> : null}
                      </div>
                    </div>
                    <div className="mt-0.5">
                      {entry.status === "uploading" ? <Loader2 className="h-5 w-5 animate-spin text-primary" /> : null}
                      {entry.status === "success" ? <CheckCircle2 className="h-5 w-5 text-primary" /> : null}
                      {entry.status === "error" ? <AlertCircle className="h-5 w-5 text-red-400" /> : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </AnalysisShell>
  );
}
