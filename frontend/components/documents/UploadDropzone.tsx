"use client";

import React, { useRef, useState } from "react";
import { UploadCloud, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api-client";
import { formatBytes } from "@/lib/utils";

interface UploadDropzoneProps {
  onUploadSuccess?: () => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({
  onUploadSuccess,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20 MB

  const validateAndUpload = async (file: File) => {
    setError(null);
    setSuccessMessage(null);

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a valid PDF file (.pdf).");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError(
        `File size (${formatBytes(file.size)}) exceeds the maximum limit of 20 MB.`
      );
      return;
    }

    setSelectedFile(file);
    setIsUploading(true);

    try {
      const result = await api.uploadDocument(file);
      setSuccessMessage(`"${result.filename}" indexed and ready for retrieval!`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to upload and index document.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndUpload(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center p-8 sm:p-10 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-200 text-center ${
          isDragging
            ? "border-indigo-500 bg-indigo-950/20 scale-[0.99]"
            : "border-zinc-700/80 hover:border-zinc-500 bg-zinc-900/40 hover:bg-zinc-900/70"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
          disabled={isUploading}
        />

        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-800/80 text-indigo-400 border border-zinc-700/60 shadow-inner mb-4">
          <UploadCloud className="h-7 w-7" />
        </div>

        <h3 className="text-base font-semibold text-zinc-100 mb-1">
          {isUploading ? "Processing & Indexing PDF..." : "Drop PDF here or click to browse"}
        </h3>
        <p className="text-xs text-zinc-400 max-w-sm">
          Supports native PDFs up to 20 MB. Chunks, embeddings, and full-text indexes will be generated automatically.
        </p>

        {isUploading && selectedFile && (
          <div className="mt-4 flex items-center gap-2 text-xs text-indigo-300 bg-indigo-950/60 px-3 py-1.5 rounded-lg border border-indigo-800/60">
            <div className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
            <span>Extracting pages and generating vectors for {selectedFile.name}...</span>
          </div>
        )}
      </div>

      {/* Error Notice */}
      {error && (
        <div className="mt-3 flex items-start gap-2 text-xs text-rose-300 bg-rose-950/50 p-3 rounded-xl border border-rose-800/60 animate-in fade-in">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Success Notice */}
      {successMessage && (
        <div className="mt-3 flex items-start gap-2 text-xs text-emerald-300 bg-emerald-950/50 p-3 rounded-xl border border-emerald-800/60 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{successMessage}</span>
        </div>
      )}
    </div>
  );
};
