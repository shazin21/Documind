"use client";

import React, { useState } from "react";
import { Citation } from "@/types";

interface CitationBadgeProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({
  citation,
  onClick,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span className="relative inline-block mx-0.5 align-baseline">
      <button
        onClick={() => onClick && onClick(citation)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="inline-flex items-center justify-center px-1.5 py-0.2 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-700/60 text-[11px] font-semibold hover:bg-indigo-900 hover:text-white transition-all cursor-pointer shadow-xs active:scale-95"
        title={`Click to view ${citation.document_name} at Page ${citation.page_number}`}
      >
        {citation.citation_id}
      </button>

      {/* Hover preview tooltip */}
      {showTooltip && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2.5 bg-zinc-900 border border-zinc-700 rounded-xl shadow-xl text-left z-50 text-[11px] pointer-events-none animate-in fade-in zoom-in-95 duration-150 block">
          <span className="flex items-center justify-between font-semibold text-zinc-200 border-b border-zinc-800 pb-1 mb-1.5">
            <span className="truncate max-w-[140px]">{citation.document_name}</span>
            <span className="text-indigo-400">Page {citation.page_number}</span>
          </span>
          <span className="block text-zinc-400 leading-snug line-clamp-3 italic">
            &ldquo;{citation.excerpt}&rdquo;
          </span>
          <span className="block mt-1.5 text-[9px] text-zinc-500 text-right">
            Click badge to open PDF page
          </span>
        </span>
      )}
    </span>
  );
};
