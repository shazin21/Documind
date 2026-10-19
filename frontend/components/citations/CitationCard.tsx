"use client";

import React from "react";
import { Citation } from "@/types";
import { FileText, ExternalLink } from "lucide-react";

interface CitationCardProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({
  citation,
  onClick,
}) => {
  return (
    <div
      onClick={() => onClick && onClick(citation)}
      className="flex flex-col gap-1.5 p-3 rounded-xl border border-zinc-800 bg-zinc-950/60 hover:bg-zinc-900/80 hover:border-zinc-700 transition-all cursor-pointer group"
    >
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-medium text-zinc-200">
          <span className="flex h-5 w-5 items-center justify-center rounded bg-indigo-950 text-indigo-300 font-bold border border-indigo-800/60 text-[10px]">
            {citation.citation_id}
          </span>
          <FileText className="h-3.5 w-3.5 text-zinc-400 group-hover:text-indigo-400 transition-colors" />
          <span className="truncate max-w-[180px] sm:max-w-[260px]">{citation.document_name}</span>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-400 group-hover:text-zinc-200 transition-colors">
          <span className="text-[11px] font-semibold text-indigo-400 bg-indigo-950/40 px-1.5 py-0.5 rounded border border-indigo-900/40">
            Page {citation.page_number}
          </span>
          <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>

      <p className="text-[11px] text-zinc-400 leading-relaxed italic line-clamp-2 pl-6">
        &ldquo;{citation.excerpt}&rdquo;
      </p>
    </div>
  );
};
