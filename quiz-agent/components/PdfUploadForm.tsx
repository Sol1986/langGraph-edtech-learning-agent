"use client";

import { useState } from "react";

import { uploadPdf } from "@/lib/api";
import type { UploadPdfResponse } from "@/lib/types";

interface PdfUploadFormProps {
  onUploaded: (response: UploadPdfResponse) => void;
}

export function PdfUploadForm({ onUploaded }: PdfUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      const response = await uploadPdf(file);
      onUploaded(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  function handleDrop(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-6">
      <label
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`group flex w-full cursor-pointer flex-col items-center gap-3 rounded-3xl border px-8 py-14 text-center transition ${
          isDragging
            ? "border-(--color-accent) bg-(--color-accent)/5"
            : "border-dashed border-(--color-border) bg-(--color-surface) hover:border-(--color-accent)/50 hover:bg-(--color-accent)/[0.03]"
        }`}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white shadow-[0_1px_4px_rgba(0,0,0,0.08)] transition group-hover:scale-105">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            className="h-6 w-6 text-(--color-accent)"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V4.5m0 0 4 4m-4-4-4 4" />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4.5 16.5v2.25A2.25 2.25 0 0 0 6.75 21h10.5a2.25 2.25 0 0 0 2.25-2.25V16.5"
            />
          </svg>
        </div>
        <p className="text-[17px] font-medium">
          {file ? file.name : "Drop a PDF here, or click to choose one"}
        </p>
        <p className="text-sm text-(--color-ink-muted)">PDF only</p>
        <input
          type="file"
          accept="application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          disabled={isUploading}
          className="sr-only"
        />
      </label>

      <button
        type="submit"
        disabled={!file || isUploading}
        className="w-full max-w-xs rounded-full bg-(--color-accent) px-6 py-3.5 text-[15px] font-medium text-white transition hover:bg-(--color-accent-hover) active:scale-[0.98] active:bg-(--color-accent-active) disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isUploading ? "Reading PDF and drafting a lesson plan…" : "Build my lesson"}
      </button>

      {error && <p className="text-sm text-(--color-danger)">{error}</p>}
    </form>
  );
}
