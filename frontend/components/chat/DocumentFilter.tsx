"use client";

import React from "react";
import { Filter, Check, FileText } from "lucide-react";
import { Document } from "@/types";

interface DocumentFilterProps {
  documents: Document[];
  selectedDocIds: string[];
  onChange: (ids: string[]) => void;
}

export const DocumentFilter: React.FC<DocumentFilterProps> = ({
  documents,
  selectedDocIds,
  onChange,
}) => {
  const isAllSelected = selectedDocIds.length === 0;

  const handleToggleDoc = (docId: string) => {
    if (selectedDocIds.includes(docId)) {
      onChange(selectedDocIds.filter((id) => id !== docId));
    } else {
      onChange([...selectedDocIds, docId]);
    }
  };

  const handleSelectAll = () => {
    onChange([]);
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="flex items-center gap-1.5 text-xs text-zinc-400 font-medium">
        <Filter className="h-3.5 w-3.5 text-zinc-500" />
        <span>Filter Scope:</span>
      </div>

      <button
        onClick={handleSelectAll}
        className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors border ${
          isAllSelected
            ? "bg-indigo-950 text-indigo-300 border-indigo-700/60 shadow-xs"
            : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200"
        }`}
      >
        All Documents ({documents.length})
      </button>

      {documents.map((doc) => {
        const isSelected = selectedDocIds.includes(doc.id);
        return (
          <button
            key={doc.id}
            onClick={() => handleToggleDoc(doc.id)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors border max-w-[200px] truncate ${
              isSelected
                ? "bg-indigo-950 text-indigo-300 border-indigo-700/60 shadow-xs"
                : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200"
            }`}
            title={doc.filename}
          >
            <FileText className="h-3 w-3 shrink-0" />
            <span className="truncate">{doc.filename}</span>
            {isSelected && <Check className="h-3 w-3 shrink-0 text-indigo-400" />}
          </button>
        );
      })}
    </div>
  );
};
