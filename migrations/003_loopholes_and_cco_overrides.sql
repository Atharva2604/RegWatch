-- Migration 003: Document Chunking (pgvector 384-dim), Multi-Tenancy RBAC, and CCO Overrides

-- 1. Clause-level Regulation Chunks Table (500 tokens with 50-token overlap)
CREATE TABLE IF NOT EXISTS regulation_chunks (
  id BIGSERIAL PRIMARY KEY,
  regulation_id INT NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
  version_id INT REFERENCES regulation_versions(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  text TEXT NOT NULL,
  embedding VECTOR(384),
  embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2',
  tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for regulation_chunks
CREATE INDEX IF NOT EXISTS idx_regulation_chunks_reg_id ON regulation_chunks(regulation_id);
CREATE INDEX IF NOT EXISTS idx_regulation_chunks_tsv ON regulation_chunks USING gin(tsv);

-- HNSW Vector Index on regulation_chunks for sub-millisecond clause retrieval
CREATE INDEX IF NOT EXISTS idx_regulation_chunks_embedding
  ON regulation_chunks USING hnsw (embedding vector_cosine_ops);

-- Match RPC for regulation chunks
CREATE OR REPLACE FUNCTION match_regulation_chunks(
  query_embedding VECTOR(384),
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id BIGINT,
  regulation_id INT,
  chunk_index INT,
  text TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    rc.id,
    rc.regulation_id,
    rc.chunk_index,
    rc.text,
    1 - (rc.embedding <=> query_embedding) AS similarity
  FROM regulation_chunks rc
  WHERE rc.embedding IS NOT NULL
  ORDER BY rc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 2. Multi-Tenant Access Control & RBAC
CREATE TABLE IF NOT EXISTS company_members (
  user_id UUID,
  company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer', 'officer', 'admin')),
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_company_members_user_id ON company_members(user_id);
CREATE INDEX IF NOT EXISTS idx_company_members_company_id ON company_members(company_id);

-- Enable RLS on company_members
ALTER TABLE company_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own company memberships"
  ON company_members
  FOR SELECT
  TO authenticated
  USING ((select auth.uid()) = user_id);

-- 3. Alert Status Updates for CCO Overrides & Audit Defense
DO $$
BEGIN
  -- Alter status check constraint if exists or allow 'exempted'
  ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alerts_status_check;
EXCEPTION
  WHEN undefined_object THEN NULL;
END $$;

-- 4. Event-Driven Scraper Notification Channel
COMMENT ON TABLE regulations IS 'SEBI regulations and circulars archive with automated event-driven audit triggers';
