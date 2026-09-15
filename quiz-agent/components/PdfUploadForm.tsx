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

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-6 max-w-md mx-auto items-center text-center"
    >
      <div className="flex flex-col gap-3 items-center">
        <span className="font-medium text-lg">Upload a PDF to build a lesson from</span>
        {/* The native file input is visually hidden; this label is the
            actual clickable control, styled to look like a real button so
            it's obviously interactive (the raw unstyled input isn't). */}
        <label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded border border-gray-300 dark:border-gray-600 px-6 py-3 text-lg hover:bg-gray-50 dark:hover:bg-gray-800">
          Choose PDF
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={isUploading}
            className="sr-only"
          />
        </label>
        {file && <span className="text-sm text-gray-600 dark:text-gray-400">{file.name}</span>}
      </div>
      <button
        type="submit"
        disabled={!file || isUploading}
        className="rounded bg-blue-600 text-white px-6 py-3 text-lg disabled:opacity-50 w-fit"
      >
        {isUploading ? "Reading PDF and drafting a lesson plan..." : "Upload"}
      </button>
      {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
    </form>
  );
}
