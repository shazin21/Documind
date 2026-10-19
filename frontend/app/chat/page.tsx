"use client";

import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  MessageSquare,
  Send,
  Plus,
  Layers,
  Sparkles,
  SlidersHorizontal,
  Bot,
} from "lucide-react";
import { api } from "@/lib/api-client";
import {
  Citation,
  Conversation,
  Document,
  EvidenceItem,
  Message,
} from "@/types";
import { DocumentFilter } from "@/components/chat/DocumentFilter";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { EvidenceSidePanel } from "@/components/chat/EvidenceSidePanel";
import { PdfViewerModal } from "@/components/pdf-viewer/PdfViewerModal";
import { Button } from "@/components/ui/Button";

function ChatWorkspaceContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("doc");

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>(
    initialDocId ? [initialDocId] : []
  );
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    null
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [useReranker, setUseReranker] = useState(false);

  // Evidence panel state
  const [currentEvidence, setCurrentEvidence] = useState<EvidenceItem[]>([]);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);

  // PDF Viewer modal state
  const [pdfViewerDoc, setPdfViewerDoc] = useState<Document | null>(null);
  const [pdfViewerPage, setPdfViewerPage] = useState<number>(1);
  const [isPdfViewerOpen, setIsPdfViewerOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initial load: documents and conversations
  useEffect(() => {
    const init = async () => {
      try {
        const [docs, convs] = await Promise.all([
          api.listDocuments(),
          api.listConversations(),
        ]);
        setDocuments(docs);
        setConversations(convs);

        if (convs.length > 0 && !activeConversationId) {
          setActiveConversationId(convs[0].id);
        }
      } catch {
        // Handle initial load error gracefully
      }
    };
    init();
  }, []);

  // Load messages when activeConversationId changes
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }
    const loadMessages = async () => {
      try {
        const msgs = await api.getConversationMessages(activeConversationId);
        setMessages(msgs);
      } catch {
        setMessages([]);
      }
    };
    loadMessages();
  }, [activeConversationId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setCurrentEvidence([]);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuestion.trim();
    if (!query || isSending) return;

    setInputQuestion("");
    setIsSending(true);

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: "temp-user-" + Date.now(),
      role: "user",
      content: query,
      citations_json: [],
      insufficient_evidence: false,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await api.sendMessage({
        question: query,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : null,
        conversation_id: activeConversationId || undefined,
        use_reranker: useReranker,
        top_k: 5,
      });

      // Update active conversation
      setActiveConversationId(response.conversation_id);
      setCurrentEvidence(response.evidence || []);

      const assistantMsg: Message = {
        id: response.message_id,
        role: "assistant",
        content: response.answer,
        citations_json: response.citations,
        insufficient_evidence: response.insufficient_evidence,
        latency_ms: response.latency_ms,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh conversations list in background
      api.listConversations().then(setConversations).catch(() => {});
    } catch (err: any) {
      const errorMsg: Message = {
        id: "error-" + Date.now(),
        role: "assistant",
        content: `Error: ${err.message || "Failed to generate answer."}`,
        citations_json: [],
        insufficient_evidence: true,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const handleCitationClick = (citation: Citation) => {
    const doc = documents.find((d) => d.id === citation.document_id);
    if (doc) {
      setPdfViewerDoc(doc);
      setPdfViewerPage(citation.page_number);
      setIsPdfViewerOpen(true);
    } else {
      // Create minimal document stub if not found in list
      setPdfViewerDoc({
        id: citation.document_id,
        filename: citation.document_name,
        page_count: citation.page_number,
        file_size_bytes: 0,
        processing_status: "completed",
        created_at: "",
        updated_at: "",
      });
      setPdfViewerPage(citation.page_number);
      setIsPdfViewerOpen(true);
    }
  };

  const handleSelectPassageFromPanel = (item: EvidenceItem) => {
    const doc = documents.find((d) => d.id === item.document_id);
    if (doc) {
      setPdfViewerDoc(doc);
      setPdfViewerPage(item.page_number);
      setIsPdfViewerOpen(true);
    }
  };

  const sampleQuestions = [
    "What are the approval requirements for annual leave?",
    "How often do company vehicles require maintenance?",
    "Summarize the key compliance procedures across documents.",
    "What is the policy for carrying forward unused vacation days?",
  ];

  return (
    <div className="flex-1 flex h-[calc(100vh-4rem)] overflow-hidden bg-zinc-950">
      {/* Left Sidebar: Conversations */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/50 flex flex-col shrink-0 hidden md:flex">
        <div className="p-4 border-b border-zinc-800">
          <Button
            onClick={handleStartNewConversation}
            className="w-full justify-start gap-2 shadow-xs"
            size="sm"
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 px-3 py-1.5">
            History
          </div>
          {conversations.length === 0 ? (
            <p className="px-3 py-2 text-xs text-zinc-500">No conversations yet.</p>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setActiveConversationId(conv.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-left transition-colors truncate ${
                  activeConversationId === conv.id
                    ? "bg-zinc-800 text-white font-medium shadow-xs"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850"
                }`}
                title={conv.title}
              >
                <MessageSquare className="h-3.5 w-3.5 shrink-0 text-zinc-400" />
                <span className="truncate flex-1">{conv.title}</span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Filter and Controls Bar */}
        <div className="border-b border-zinc-800 bg-zinc-900/40 p-3 sm:px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <DocumentFilter
            documents={documents}
            selectedDocIds={selectedDocIds}
            onChange={setSelectedDocIds}
          />

          <div className="flex items-center gap-2 self-end sm:self-auto">
            {/* Reranker toggle */}
            <button
              onClick={() => setUseReranker(!useReranker)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                useReranker
                  ? "bg-indigo-950 text-indigo-300 border-indigo-700/60"
                  : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200"
              }`}
              title="Toggle Cross-Encoder Reranker for higher precision"
            >
              <SlidersHorizontal className="h-3 w-3" />
              <span>Reranker: {useReranker ? "ON" : "OFF"}</span>
            </button>

            {/* Inspect evidence button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEvidenceOpen(true)}
              className="h-7 text-xs px-2.5"
            >
              <Layers className="h-3.5 w-3.5 mr-1 text-indigo-400" />
              Evidence ({currentEvidence.length})
            </Button>
          </div>
        </div>

        {/* Messages Stream Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="max-w-2xl mx-auto py-12 text-center space-y-6">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-900 text-indigo-400 border border-zinc-800 shadow-inner mx-auto">
                <Bot className="h-7 w-7" />
              </div>

              <div>
                <h3 className="text-lg font-bold text-zinc-100">
                  Ask DocuMind AI
                </h3>
                <p className="text-xs text-zinc-400 max-w-md mx-auto mt-1 leading-relaxed">
                  Every answer is strictly grounded in your indexed documents, complete with verified
                  page excerpts [1], [2] and an explicit refusal if evidence is missing.
                </p>
              </div>

              {/* Sample Questions */}
              <div className="space-y-2 pt-2">
                <p className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">
                  Suggested Questions
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                  {sampleQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputQuestion(q)}
                      className="p-3 rounded-xl border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-850 hover:border-zinc-700 text-xs text-zinc-300 transition-colors cursor-pointer"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onCitationClick={handleCitationClick}
                onOpenEvidence={() => setIsEvidenceOpen(true)}
              />
            ))
          )}

          {isSending && (
            <div className="flex items-center gap-3 max-w-3xl mr-auto text-xs text-zinc-400 animate-pulse py-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-indigo-950 text-indigo-400 border border-indigo-800/60">
                <Sparkles className="h-4 w-4" />
              </div>
              <span>Retrieving hybrid passages and generating grounded answer...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/40">
          <form
            onSubmit={handleSendMessage}
            className="max-w-4xl mx-auto relative flex items-center"
          >
            <input
              type="text"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={isSending}
              className="w-full pl-4 pr-24 py-3 bg-zinc-900 border border-zinc-800 rounded-2xl text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-inner"
            />
            <Button
              type="submit"
              size="sm"
              disabled={!inputQuestion.trim() || isSending}
              isLoading={isSending}
              className="absolute right-2 h-8 px-3 rounded-xl shadow-xs"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </form>
          <p className="text-[10px] text-zinc-500 text-center mt-2">
            Answers are verified against indexed PDF pages. Unverified claims are abstained.
          </p>
        </div>
      </div>

      {/* Retrieved Passages Side Panel */}
      <EvidenceSidePanel
        isOpen={isEvidenceOpen}
        onClose={() => setIsEvidenceOpen(false)}
        evidence={currentEvidence}
        onSelectPassage={handleSelectPassageFromPanel}
      />

      {/* PDF Viewer Modal */}
      <PdfViewerModal
        document={pdfViewerDoc}
        initialPage={pdfViewerPage}
        isOpen={isPdfViewerOpen}
        onClose={() => {
          setIsPdfViewerOpen(false);
          setPdfViewerDoc(null);
        }}
      />
    </div>
  );
}

export default function ChatPage() {
  return (
    <React.Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center text-xs text-zinc-500 bg-zinc-950">
          Loading workspace...
        </div>
      }
    >
      <ChatWorkspaceContent />
    </React.Suspense>
  );
}
