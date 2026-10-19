"use client";

import React from "react";
import { X, Layers, FileText } from "lucide-react";
import { EvidenceItem } from "@/types";
import { Badge } from "@/components/ui/Badge";

interface EvidenceSidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceItem[];
  onSelectPassage?: (item: EvidenceItem) => void;
}

export const EvidenceSidePanel: React.FC<EvidenceSidePanelProps> = ({
  isOpen,
  onClose,
  evidence,
  onSelectPassage,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-zinc-900 border-l border-zinc-800 shadow-2xl flex flex-col text-zinc-100 animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950/60">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-950 text-indigo-400 border border-indigo-800/60">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-zinc-100">Retrieved Passages</h3>
            <p className="text-[11px] text-zinc-400">
              {evidence.length} candidate passage{evidence.length === 1 ? "" : "s"} selected
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
          aria-label="Close panel"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Passages List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {evidence.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center text-zinc-500 text-xs">
            <FileText className="h-8 w-8 mb-2 opacity-50" />
            <p>No passages retrieved yet.</p>
            <p className="text-[11px] text-zinc-600 mt-1">
              Ask a question in chat to inspect evidence selection.
            </p>
          </div>
        ) : (
          evidence.map((item, idx) => (
            <div
              key={`${item.chunk_id}-${idx}`}
              onClick={() => onSelectPassage && onSelectPassage(item)}
              className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-950/60 hover:border-zinc-700 transition-all text-xs space-y-2 cursor-pointer group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-semibold text-zinc-200">
                  <span className="flex h-5 w-5 items-center justify-center rounded bg-zinc-800 text-zinc-300 font-mono text-[10px] border border-zinc-700">
                    #{item.rank}
                  </span>
                  <span className="truncate max-w-[180px]">{item.document_name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge variant="indigo" className="text-[10px] py-0 px-1.5">
                    Page {item.page_number}
                  </Badge>
                  <span className="text-[10px] text-zinc-400 font-mono">
                    Score: {item.score}
                  </span>
                </div>
              </div>

              <div className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">
                Retriever: <span className="text-indigo-400">{item.retrieval_type}</span>
              </div>

              <p className="text-[11px] text-zinc-300 leading-relaxed bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-850 font-sans">
                {item.chunk_text}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
