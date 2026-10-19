"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  Trash2,
  Eye,
  MessageSquare,
} from "lucide-react";
import { Document } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatBytes, formatDate } from "@/lib/utils";

interface DocumentTableProps {
  documents: Document[];
  isLoading: boolean;
  onViewPdf: (doc: Document) => void;
  onDeleteDoc: (doc: Document) => void;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  isLoading,
  onViewPdf,
  onDeleteDoc,
}) => {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="success">Indexed</Badge>;
      case "processing":
        return (
          <Badge variant="warning">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse mr-1" />
            Processing
          </Badge>
        );
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">Queued</Badge>;
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Search Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
          <input
            type="text"
            placeholder="Search documents by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          />
        </div>
        <div className="text-xs text-zinc-400 font-medium">
          Showing {filteredDocs.length} of {documents.length} document{documents.length === 1 ? "" : "s"}
        </div>
      </div>

      {/* Table Container */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-900/80 border-b border-zinc-800 text-zinc-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Document Name</th>
                <th className="py-3 px-4">Pages</th>
                <th className="py-3 px-4">Size</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Uploaded</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-zinc-500">
                    <div className="flex items-center justify-center gap-2">
                      <div className="h-4 w-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
                      <span>Loading documents library...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <FileText className="h-8 w-8 text-zinc-600" />
                      <p className="text-sm font-medium text-zinc-400">
                        {searchTerm ? "No documents match your search." : "No documents uploaded yet."}
                      </p>
                      <p className="text-xs text-zinc-500 max-w-sm">
                        {searchTerm
                          ? "Try searching for a different keyword or filename."
                          : "Upload a PDF above to extract text, build embeddings, and start asking grounded questions."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-zinc-800/40 transition-colors group"
                  >
                    <td className="py-3.5 px-4 font-medium text-zinc-100">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-800 text-indigo-400 border border-zinc-700/60">
                          <FileText className="h-4 w-4" />
                        </div>
                        <span className="truncate max-w-[220px] sm:max-w-[300px]" title={doc.filename}>
                          {doc.filename}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-zinc-400">
                      {doc.page_count > 0 ? `${doc.page_count} pages` : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-zinc-400">
                      {formatBytes(doc.file_size_bytes)}
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(doc.processing_status)}
                    </td>
                    <td className="py-3.5 px-4 text-zinc-400 whitespace-nowrap">
                      {formatDate(doc.created_at)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link href={`/chat?doc=${doc.id}`}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2.5 text-indigo-400 hover:text-indigo-300"
                            title="Chat with document"
                          >
                            <MessageSquare className="h-3.5 w-3.5 mr-1" />
                            Chat
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewPdf(doc)}
                          className="h-8 px-2.5 text-zinc-300 hover:text-white"
                          title="View PDF"
                        >
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          View
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onDeleteDoc(doc)}
                          className="h-8 w-8 text-zinc-400 hover:text-rose-400 hover:bg-rose-950/40"
                          title="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
