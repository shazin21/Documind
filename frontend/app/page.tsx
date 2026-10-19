"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  MessageSquare,
  Layers,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Database,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { Document, HealthResponse } from "@/types";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatBytes, formatDate } from "@/lib/utils";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [docs, h] = await Promise.all([
        api.listDocuments().catch(() => []),
        api.getHealth().catch(() => null),
      ]);
      setDocuments(docs);
      setHealth(h);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalPages = documents.reduce((acc, doc) => acc + (doc.page_count || 0), 0);
  const completedDocs = documents.filter((d) => d.processing_status === "completed").length;

  return (
    <div className="flex-1 py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-10">
      {/* Hero Welcome */}
      <div className="relative overflow-hidden rounded-3xl border border-zinc-800 bg-gradient-to-b from-zinc-900/90 to-zinc-950 p-8 sm:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
            Verified Grounded RAG Architecture
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            DocuMind AI Knowledge Retrieval
          </h1>
          <p className="text-sm sm:text-base text-zinc-400 leading-relaxed">
            High-precision document intelligence with hybrid dense-sparse search, pgvector storage,
            claim-to-evidence citation verification, and reproducible benchmark evaluation.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link href="/chat">
              <Button size="lg" className="shadow-lg shadow-indigo-600/20">
                <MessageSquare className="h-4 w-4 mr-2" />
                Start Chat & Q&A
              </Button>
            </Link>
            <Link href="/documents">
              <Button variant="outline" size="lg">
                <FileText className="h-4 w-4 mr-2" />
                Document Library
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Indexed Documents</span>
              <FileText className="h-4 w-4 text-indigo-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold mt-1">
              {isLoading ? "—" : documents.length}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-400">
              {completedDocs} ready for semantic retrieval
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Total Pages Indexed</span>
              <Layers className="h-4 w-4 text-violet-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold mt-1">
              {isLoading ? "—" : totalPages}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-400">
              Preserved 1-indexed page boundaries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Embedding Vector Model</span>
              <Cpu className="h-4 w-4 text-emerald-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold mt-1">
              384d
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-400 truncate" title="all-MiniLM-L6-v2">
              all-MiniLM-L6-v2 (Normalized)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Database & Vector Store</span>
              <Database className="h-4 w-4 text-amber-400" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold mt-1">
              {health?.database.connected ? "pgvector" : "Degraded"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-400">
              {health?.database.connected ? "PostgreSQL 16 + pgvector" : "Awaiting DB connection"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Upload & Recent Docs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Quick Upload Dropzone */}
        <div className="lg:col-span-1 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-zinc-100">Upload PDF Document</h2>
            <p className="text-xs text-zinc-400">
              Upload documents to extract text, compute embeddings, and build hybrid indexes.
            </p>
          </div>
          <UploadDropzone onUploadSuccess={fetchData} />
        </div>

        {/* Right Column: Recent Documents */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-zinc-100">Recent Documents</h2>
              <p className="text-xs text-zinc-400">
                Documents available for multi-document question answering.
              </p>
            </div>
            <Link href="/documents" className="text-xs font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800/60 overflow-hidden shadow-sm">
            {isLoading ? (
              <div className="py-12 text-center text-xs text-zinc-500">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="py-12 px-4 text-center">
                <FileText className="h-8 w-8 text-zinc-600 mx-auto mb-2" />
                <p className="text-sm font-medium text-zinc-400">No documents yet</p>
                <p className="text-xs text-zinc-500 mt-1">Upload a PDF to begin knowledge retrieval.</p>
              </div>
            ) : (
              documents.slice(0, 5).map((doc) => (
                <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-zinc-800/40 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800 text-indigo-400 border border-zinc-700/60">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-zinc-200 truncate max-w-[200px] sm:max-w-xs" title={doc.filename}>
                        {doc.filename}
                      </h4>
                      <p className="text-[11px] text-zinc-400">
                        {doc.page_count} pages • {formatBytes(doc.file_size_bytes)} • {formatDate(doc.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={doc.processing_status === "completed" ? "success" : "warning"}>
                      {doc.processing_status}
                    </Badge>
                    <Link href={`/chat?doc=${doc.id}`}>
                      <Button variant="ghost" size="sm" className="h-8 text-xs text-indigo-400">
                        <MessageSquare className="h-3.5 w-3.5 mr-1" />
                        Chat
                      </Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Architecture Highlights Section */}
      <div className="border-t border-zinc-800/80 pt-8 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-zinc-100">System Architecture Highlights</h2>
          <p className="text-xs text-zinc-400">
            Engineered with strict RAG best practices to guarantee factual groundedness and transparency.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-zinc-950 border-zinc-800/80">
            <CardHeader className="pb-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-950 text-indigo-400 mb-2 border border-indigo-800/60">
                <Search className="h-4 w-4" />
              </div>
              <CardTitle className="text-sm font-semibold">Hybrid Reciprocal Rank Fusion</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-zinc-400 leading-relaxed">
              Combines dense vector search (pgvector cosine similarity) with PostgreSQL full-text keyword search ($k=60$), ensuring exact numbers, codes, and semantic meaning are all retrieved.
            </CardContent>
          </Card>

          <Card className="bg-zinc-950 border-zinc-800/80">
            <CardHeader className="pb-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-950 text-emerald-400 mb-2 border border-emerald-800/60">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <CardTitle className="text-sm font-semibold">Groundedness & Prompt Defense</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-zinc-400 leading-relaxed">
              Every factual assertion requires an excerpted citation [1], [2]. Retrieved text is isolated as untrusted data, and the model explicitly abstains when evidence is insufficient.
            </CardContent>
          </Card>

          <Card className="bg-zinc-950 border-zinc-800/80">
            <CardHeader className="pb-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-950 text-violet-400 mb-2 border border-violet-800/60">
                <SlidersHorizontal className="h-4 w-4" />
              </div>
              <CardTitle className="text-sm font-semibold">Cross-Encoder Rescoring</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-zinc-400 leading-relaxed">
              Optional deep sentence-pair cross-encoder reranking analyzes full semantic interaction between the user query and candidate passages, filtering low-confidence noise before answer generation.
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
