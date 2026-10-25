-- Migration 001: Baseline schema for RegWatch

CREATE EXTENSION IF NOT EXISTS vector;

-- Regulatory Sources (SEBI, RBI, etc.)
CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  key TEXT UNIQUE,
  jurisdiction TEXT DEFAULT 'IN',
  enabled BOOLEAN DEFAULT true,
  config JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Regulatory Documents
CREATE TABLE IF NOT EXISTS regulations (
  id SERIAL PRIMARY KEY,
  source_id INT REFERENCES sources(id),
  title TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  legal_type TEXT DEFAULT 'circular',
  published_date DATE,
  reference_number TEXT,
  department TEXT,
  content_text TEXT,
  content_hash TEXT,
  first_seen_at TIMESTAMPTZ DEFAULT now(),
  last_checked_at TIMESTAMPTZ,
  last_changed_at TIMESTAMPTZ,
  status TEXT DEFAULT 'active'
);

-- Versioned Content Snapshots
CREATE TABLE IF NOT EXISTS regulation_versions (
  id SERIAL PRIMARY KEY,
  regulation_id INT REFERENCES regulations(id) ON DELETE CASCADE,
  version_no INT DEFAULT 1,
  content_text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  diff_summary TEXT,
  raw_sha256 TEXT,
  raw_storage_path TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Regulated Entities / Tenants
CREATE TABLE IF NOT EXISTS companies (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  industry TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Internal Policies
CREATE TABLE IF NOT EXISTS company_policies (
  id SERIAL PRIMARY KEY,
  company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  title TEXT,
  category TEXT NOT NULL,
  policy_text TEXT,
  metric_name TEXT,
  value NUMERIC,
  unit TEXT,
  embedding VECTOR(384),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Extracted Obligations
CREATE TABLE IF NOT EXISTS obligations (
  id BIGSERIAL PRIMARY KEY,
  regulation_id INT REFERENCES regulations(id) ON DELETE CASCADE,
  version_id INT REFERENCES regulation_versions(id),
  category TEXT NOT NULL,
  applies_to TEXT DEFAULT 'all_entities',
  requirement_text TEXT NOT NULL,
  evidence_quote TEXT,
  metric_name TEXT,
  operator TEXT,
  threshold_value NUMERIC,
  unit TEXT,
  effective_date DATE,
  confidence NUMERIC DEFAULT 1.0,
  model TEXT,
  prompt_version TEXT DEFAULT 'v1',
  status TEXT DEFAULT 'active',
  embedding VECTOR(384),
  extracted_at TIMESTAMPTZ DEFAULT now()
);

-- Compliance Evaluation Verdicts
CREATE TABLE IF NOT EXISTS compliance_checks (
  id BIGSERIAL PRIMARY KEY,
  obligation_id BIGINT REFERENCES obligations(id) ON DELETE CASCADE,
  company_policy_id INT REFERENCES company_policies(id),
  company_id INT REFERENCES companies(id),
  verdict TEXT NOT NULL,
  confidence NUMERIC DEFAULT 1.0,
  explanation TEXT,
  method TEXT DEFAULT 'rule_based',
  triggered_by TEXT DEFAULT 'regulation_change',
  inputs_hash TEXT,
  checked_at TIMESTAMPTZ DEFAULT now()
);

-- Risk Scores
CREATE TABLE IF NOT EXISTS risk_scores (
  id BIGSERIAL PRIMARY KEY,
  compliance_check_id BIGINT REFERENCES compliance_checks(id) ON DELETE CASCADE,
  severity INT NOT NULL,
  urgency INT NOT NULL,
  scope INT NOT NULL,
  level TEXT NOT NULL,
  score_value NUMERIC NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Incident Alerts
CREATE TABLE IF NOT EXISTS alerts (
  id BIGSERIAL PRIMARY KEY,
  compliance_check_id BIGINT REFERENCES compliance_checks(id) ON DELETE CASCADE,
  company_id INT REFERENCES companies(id),
  channel TEXT DEFAULT 'email',
  dedupe_key TEXT UNIQUE,
  status TEXT DEFAULT 'pending',
  lifecycle TEXT DEFAULT 'open',
  acknowledged_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
