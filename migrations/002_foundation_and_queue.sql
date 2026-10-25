-- Migration 002: System Design Resilience, Distributed Job Queue, and RLS

-- Operational log of every pipeline run
CREATE TABLE IF NOT EXISTS ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  source_id INT REFERENCES sources(id),
  legal_type TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status TEXT DEFAULT 'running',  -- running | success | partial | failed
  items_seen INT DEFAULT 0,
  items_new INT DEFAULT 0,
  items_changed INT DEFAULT 0,
  items_failed INT DEFAULT 0,
  error TEXT
);

-- Distributed Persistent Job Queue (Pipes & Filters)
CREATE TABLE IF NOT EXISTS jobs (
  id BIGSERIAL PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  dedupe_key TEXT,
  status TEXT NOT NULL DEFAULT 'pending',     -- pending | running | done | failed | dead
  attempts INT NOT NULL DEFAULT 0,
  max_attempts INT NOT NULL DEFAULT 5,
  run_after TIMESTAMPTZ NOT NULL DEFAULT now(),
  locked_at TIMESTAMPTZ,
  last_error TEXT,
  run_id BIGINT REFERENCES ingestion_runs(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Prevent duplicate active jobs for the same target
CREATE UNIQUE INDEX IF NOT EXISTS jobs_dedupe_active_uq ON jobs(dedupe_key)
  WHERE status IN ('pending', 'running');

-- Atomic job claim function with SKIP LOCKED for safe concurrent worker execution
CREATE OR REPLACE FUNCTION claim_job(p_worker_id TEXT DEFAULT 'worker')
RETURNS TABLE (
  id BIGINT,
  job_type TEXT,
  payload JSONB,
  dedupe_key TEXT,
  status TEXT,
  attempts INT
) LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  UPDATE jobs j
  SET status = 'running',
      locked_at = now(),
      attempts = j.attempts + 1
  WHERE j.id = (
    SELECT q.id FROM jobs q
    WHERE q.status = 'pending' AND q.run_after <= now()
    ORDER BY q.id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  )
  RETURNING j.id, j.job_type, j.payload, j.dedupe_key, j.status, j.attempts;
END;
$$;

-- Checkpoints for resumable deep crawling and reconciliation
CREATE TABLE IF NOT EXISTS crawl_state (
  source_key TEXT,
  listing TEXT,
  last_page INT DEFAULT 1,
  total_reported INT DEFAULT 0,
  total_ingested INT DEFAULT 0,
  etag TEXT,
  last_modified TEXT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (source_key, listing)
);

-- Quarantine for malformed items failing quality gates
CREATE TABLE IF NOT EXISTS quarantine_items (
  id BIGSERIAL PRIMARY KEY,
  source_key TEXT NOT NULL,
  url TEXT NOT NULL,
  reason TEXT NOT NULL,
  payload JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved BOOLEAN DEFAULT false
);

-- Categorical taxonomy as data (extensible without code changes)
CREATE TABLE IF NOT EXISTS categories (
  key TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  description TEXT,
  active BOOLEAN DEFAULT true
);

-- Two-tier LLM response cache
CREATE TABLE IF NOT EXISTS llm_cache (
  cache_key TEXT PRIMARY KEY,
  response JSONB NOT NULL,
  model TEXT,
  prompt_version TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Candidate links for incremental compliance recomputation
CREATE TABLE IF NOT EXISTS obligation_policy_links (
  obligation_id BIGINT REFERENCES obligations(id) ON DELETE CASCADE,
  company_policy_id INT REFERENCES company_policies(id) ON DELETE CASCADE,
  method TEXT,
  similarity NUMERIC,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (obligation_id, company_policy_id)
);

-- Immutable audit events log
CREATE TABLE IF NOT EXISTS audit_events (
  id BIGSERIAL PRIMARY KEY,
  entity TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Multi-tenant Access Control & Row Level Security
CREATE TABLE IF NOT EXISTS company_members (
  user_id UUID,
  company_id INT REFERENCES companies(id),
  role TEXT DEFAULT 'viewer',  -- viewer | officer | admin
  PRIMARY KEY (user_id, company_id)
);

-- Deduplication index for compliance check pairs
CREATE UNIQUE INDEX IF NOT EXISTS compliance_checks_dedupe_uq
  ON compliance_checks(obligation_id, company_policy_id, inputs_hash);
