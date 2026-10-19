"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { Document } from "@/types";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentTable } from "@/components/documents/DocumentTable";
import { DeleteConfirmModal } from "@/components/documents/DeleteConfirmModal";
import { PdfViewerModal } from "@/components/pdf-viewer/PdfViewerModal";
import { FileText, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal states
  const [selectedDocForViewer, setSelectedDocForViewer] = useState<Document | null>(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  const [selectedDocForDelete, setSelectedDocForDelete] = useState<Document | null>(null);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch {
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleOpenViewer = (doc: Document) => {
    setSelectedDocForViewer(doc);
    setIsViewerOpen(true);
  };

  const handleOpenDelete = (doc: Document) => {
    setSelectedDocForDelete(doc);
    setIsDeleteOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedDocForDelete) return;
    setIsDeleting(true);
    try {
      await api.deleteDocument(selectedDocForDelete.id);
      setIsDeleteOpen(false);
      setSelectedDocForDelete(null);
      await fetchDocuments();
    } catch (err: any) {
      alert(err.message || "Failed to delete document.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex-1 py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Page Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-950 text-indigo-400 border border-indigo-800/60">
              <FileText className="h-4 w-4" />
            </div>
            <h1 className="text-2xl font-bold text-zinc-100">Document Library</h1>
          </div>
          <p className="mt-1 text-xs text-zinc-400">
            Upload, manage, inspect, and delete PDF documents indexed into pgvector.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchDocuments}
          isLoading={isLoading}
          className="self-start sm:self-auto"
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Refresh
        </Button>
      </div>

      {/* Upload Dropzone Section */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-200">Upload New PDF Document</h2>
        <UploadDropzone onUploadSuccess={fetchDocuments} />
      </div>

      {/* Document Library Table */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-zinc-200">Indexed Document Catalog</h2>
        <DocumentTable
          documents={documents}
          isLoading={isLoading}
          onViewPdf={handleOpenViewer}
          onDeleteDoc={handleOpenDelete}
        />
      </div>

      {/* PDF Viewer Modal */}
      <PdfViewerModal
        document={selectedDocForViewer}
        isOpen={isViewerOpen}
        onClose={() => {
          setIsViewerOpen(false);
          setSelectedDocForViewer(null);
        }}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        document={selectedDocForDelete}
        isOpen={isDeleteOpen}
        isDeleting={isDeleting}
        onClose={() => {
          setIsDeleteOpen(false);
          setSelectedDocForDelete(null);
        }}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
