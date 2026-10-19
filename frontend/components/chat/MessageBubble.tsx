"use client";

import React from "react";
import { Message, Citation } from "@/types";
import { CitationBadge } from "@/components/citations/CitationBadge";
import { CitationCard } from "@/components/citations/CitationCard";
import {
  Sparkles,
  User,
  AlertTriangle,
  Clock,
  Layers,
} from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  onCitationClick?: (citation: Citation) => void;
  onOpenEvidence?: () => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onCitationClick,
  onOpenEvidence,
}) => {
  const isUser = message.role === "user";

  // Function to render text with clickable citation badges
  const renderFormattedText = (text: string, citations: Citation[]) => {
    // Regex splits text preserving citation markers like [1], [2], [1, 2]
    const parts = text.split(/(\[\d+(?:\s*,\s*\d+)*\])/g);

    return parts.map((part, index) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const citationId = part;
        const matchedCitation = citations.find((c) => c.citation_id === citationId);
        if (matchedCitation) {
          return (
            <CitationBadge
              key={index}
              citation={matchedCitation}
              onClick={onCitationClick}
            />
          );
        }
      }
      return <span key={index}>{part}</span>;
    });
  };

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 max-w-3xl ml-auto">
        <div className="bg-indigo-600 text-white p-4 rounded-2xl rounded-tr-sm shadow-md text-sm leading-relaxed max-w-2xl">
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-zinc-800 text-zinc-300 border border-zinc-700">
          <User className="h-4 w-4" />
        </div>
      </div>
    );
  }

  const citations = (message.citations_json as Citation[]) || [];

  return (
    <div className="flex justify-start gap-3 max-w-4xl mr-auto">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20">
        <Sparkles className="h-4 w-4" />
      </div>

      <div className="flex-1 space-y-3">
        {/* Insufficient Evidence Warning Banner */}
        {message.insufficient_evidence && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/40 border border-amber-800/60 text-xs text-amber-200">
            <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-300">Insufficient Evidence</p>
              <p className="text-zinc-400 mt-0.5">
                The retrieved passages do not contain verified factual evidence to answer this question.
              </p>
            </div>
          </div>
        )}

        {/* Answer Content */}
        <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-2xl rounded-tl-sm text-zinc-100 text-sm leading-relaxed shadow-sm">
          <div className="whitespace-pre-wrap">
            {renderFormattedText(message.content, citations)}
          </div>

          {/* Latency and Inspect Evidence bar */}
          <div className="mt-3 pt-2.5 border-t border-zinc-800 flex items-center justify-between text-[11px] text-zinc-500">
            <div className="flex items-center gap-1.5">
              {message.latency_ms !== null && message.latency_ms !== undefined && (
                <span className="flex items-center gap-1 font-mono">
                  <Clock className="h-3 w-3" />
                  {message.latency_ms} ms
                </span>
              )}
            </div>

            {onOpenEvidence && (
              <button
                onClick={onOpenEvidence}
                className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition-colors font-medium cursor-pointer"
              >
                <Layers className="h-3 w-3" />
                <span>Inspect Passages</span>
              </button>
            )}
          </div>
        </div>

        {/* Citations list */}
        {citations.length > 0 && (
          <div className="space-y-1.5 pt-1">
            <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider px-1">
              Verified Sources ({citations.length})
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {citations.map((citation) => (
                <CitationCard
                  key={citation.citation_id}
                  citation={citation}
                  onClick={onCitationClick}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
