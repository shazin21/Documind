-- Enable pgvector extension for persistent vector storage and similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Ensure schema permissions
GRANT ALL ON SCHEMA public TO PUBLIC;
