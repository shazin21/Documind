"use client";

import React from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { AlertTriangle } from "lucide-react";
import { Document } from "@/types";

interface DeleteConfirmModalProps {
  document: Document | null;
  isOpen: boolean;
  isDeleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  document,
  isOpen,
  isDeleting,
  onClose,
  onConfirm,
}) => {
  if (!document) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Document"
      description="This will permanently delete the document, all indexed text chunks, and embedding vectors."
    >
      <div className="flex items-start gap-3 p-3 bg-rose-950/30 border border-rose-900/60 rounded-xl my-4 text-xs text-rose-300">
        <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
        <div>
          <p className="font-semibold text-rose-200">{document.filename}</p>
          <p className="mt-0.5 text-zinc-400">
            {document.page_count} pages • Status: {document.processing_status}
          </p>
        </div>
      </div>

      <div className="flex justify-end gap-2.5 pt-2">
        <Button variant="outline" size="sm" onClick={onClose} disabled={isDeleting}>
          Cancel
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={onConfirm}
          isLoading={isDeleting}
        >
          Confirm Delete
        </Button>
      </div>
    </Modal>
  );
};
