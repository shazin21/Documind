export interface HealthResponse {
  status: "healthy" | "degraded";
  service: string;
  version: string;
  environment: string;
  database: {
    connected: boolean;
    message: string;
  };
  embedding_model: {
    name: string;
    dimension: number;
  };
  llm_provider: string;
}

export interface Document {
  id: string;
  filename: string;
  page_count: number;
  file_size_bytes: number;
  processing_status: "queued" | "processing" | "completed" | "failed";
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document {
  total_chunks: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  processing_status: string;
  message: string;
}

export interface PageResponse {
  document_id: string;
  page_number: number;
  text: string;
  total_pages: number;
  has_text: boolean;
}

export interface Citation {
  citation_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
  score: number;
}

export interface EvidenceItem {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_text: string;
  score: number;
  rank: number;
  retrieval_type: string;
}

export interface ChatRequest {
  question: string;
  document_ids?: string[] | null;
  conversation_id?: string | null;
  use_reranker?: boolean;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  evidence: EvidenceItem[];
  conversation_id: string;
  message_id: string;
  insufficient_evidence: boolean;
  latency_ms: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations_json: Citation[];
  insufficient_evidence: boolean;
  latency_ms?: number | null;
  created_at: string;
}

