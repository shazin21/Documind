"use client";

import React, { useEffect, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { api } from "@/lib/api-client";
import { Document, PageResponse } from "@/types";

interface PdfViewerModalProps {
  document: Document | null;
  initialPage?: number;
  isOpen: boolean;
  onClose: () => void;
}

export const PdfViewerModal: React.FC<PdfViewerModalProps> = ({
  document,
  initialPage = 1,
  isOpen,
  onClose,
}) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageData, setPageData] = useState<PageResponse | null>(null);
  const [loadingText, setLoadingText] = useState(false);
  const [viewMode, setViewMode] = useState<"pdf" | "text">("pdf");

  useEffect(() => {
    setCurrentPage(initialPage);
  }, [initialPage]);

  useEffect(() => {
    if (!isOpen || !document) return;

    let mounted = true;
    const fetchPage = async () => {
      setLoadingText(true);
      try {
        const data = await api.getDocumentPage(document.id, currentPage);
        if (mounted) setPageData(data);
      } catch {
        if (mounted) setPageData(null);
      } finally {
        if (mounted) setLoadingText(false);
      }
    };

    fetchPage();
    return () => {
      mounted = false;
    };
  }, [isOpen, document, currentPage]);

  if (!document) return null;

  const pdfUrl = `${api.getDocumentFileUrl(document.id)}#page=${currentPage}`;
  const totalPages = document.page_count || 1;

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={document.filename}
      description={`Inspecting verified source document • Total Pages: ${totalPages}`}
      className="max-w-4xl h-[85vh] flex flex-col"
    >
      {/* Page Navigation Controls */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-3">
        <div className="flex items-center gap-1.5 bg-zinc-950 p-1 rounded-lg border border-zinc-800 text-xs font-medium">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
            className="h-7 px-2"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="px-2 text-zinc-300">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
            className="h-7 px-2"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-2">
          <div className="flex bg-zinc-950 p-0.5 rounded-lg border border-zinc-800 text-xs">
            <button
              onClick={() => setViewMode("pdf")}
              className={`px-3 py-1 rounded-md transition-colors ${
                viewMode === "pdf"
                  ? "bg-zinc-800 text-white font-medium"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              PDF Document
            </button>
            <button
              onClick={() => setViewMode("text")}
              className={`px-3 py-1 rounded-md transition-colors ${
                viewMode === "text"
                  ? "bg-zinc-800 text-white font-medium"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Extracted Text
            </button>
          </div>

          <a
            href={api.getDocumentFileUrl(document.id)}
            target="_blank"
            rel="noreferrer"
            className="p-1.5 text-zinc-400 hover:text-zinc-100 bg-zinc-950 rounded-lg border border-zinc-800 transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>

      {/* Viewer Canvas */}
      <div className="flex-1 w-full bg-zinc-950 rounded-xl border border-zinc-800 overflow-hidden relative min-h-[400px]">
        {viewMode === "pdf" ? (
          <iframe
            key={`${document.id}-${currentPage}`}
            src={pdfUrl}
            className="w-full h-full border-none"
            title="PDF Document Viewer"
          />
        ) : (
          <div className="p-6 h-full overflow-y-auto font-mono text-xs leading-relaxed text-zinc-300 whitespace-pre-wrap select-text">
            {loadingText ? (
              <div className="flex items-center justify-center h-full text-zinc-500">
                <span>Loading extracted page text...</span>
              </div>
            ) : pageData?.text ? (
              pageData.text
            ) : (
              <div className="flex items-center justify-center h-full text-zinc-500">
                <span>No text extractable on page {currentPage}.</span>
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};
