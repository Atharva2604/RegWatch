# RegWatch: End-to-End Roadmap (Start → Production-Ready)

This document is written to be given to an AI coding agent (Antigravity) and followed phase by phase.

---

## 0. Working Rules for the Coding Agent (read first)

1. Work on **one phase at a time**. Do not start the next phase until the current phase's acceptance criteria pass.
2. Before coding a phase, post a short plan (files to create or change, new tables, new dependencies). Wait for approval.
3. Never commit secrets. All keys come from `.env`. Keep `.env.example` up to date.
4. Any database change goes in a numbered SQL file under `migrations/` (e.g. `003_add_chunks.sql`). Never edit the live schema silently, and never drop existing columns or data.
5. Every module gets at least a few `pytest` tests (pure logic first: hashing, parsing, scoring, validation).
6. Be polite to SEBI's servers: custom User-Agent, 1-2 second delay between requests, retries with backoff, respect `robots.txt`.
7. All LLM output must be validated with Pydantic before it touches the database. Invalid output is retried once, then logged and skipped. It is never stored as-is.
8. Do not add infrastructure that is not in the current phase (no Kafka, Spark or Docker before their phase).
9. After each phase, run the pipeline and show real output (row counts, sample rows) as proof.
10. Keep functions small, typed, and logged. Use the `logging` module, not `print`.
11. Before each phase, read its row in section 4B.19 and treat those system-design items (reliability, consistency, security, observability, cost) as part of that phase's acceptance criteria, not extras.
12. Respect the dependency rule from section 4A: `domain` imports nothing from other layers; `application` imports only `domain`; vendor and source specifics stay in `infrastructure`. **Adding a source must never require edits to `domain/` or `application/`.**

---

## 1. Core Idea (never lose sight of this)

RegWatch watches regulators (starting with **SEBI**), detects when a legal instrument is **published or changed** (Acts, Rules, Regulations, Circulars, Master Circulars, Guidelines), extracts the **obligations** inside it, checks them against a **company's internal policies**, and raises a **risk-scored, explained alert** when the company falls out of compliance. Every version and every check is stored for an **audit trail**.

```
Watch regulator → Detect change → Extract obligations → Compare with company policy
→ Verdict (compliant / non-compliant / needs review) → Risk score → Alert + audit trail
```

**Non-goals:** not legal advice; not multi-tenant SaaS with billing; not covering every regulator at launch; not replacing a compliance officer. Low-confidence results go to human review.

**Demo domain:** SEBI, with emphasis on cybersecurity/cyber-resilience (CSCRF) obligations because they contain concrete, comparable values (timelines, thresholds). The design must stay domain-agnostic.

**Data honesty:** company policies in the demo are mock data. State this in the README and the report.

---

## 2. Current State (already done)

- Python project, venv, Git, `.env` + `.gitignore`.
- Supabase project with tables: `sources`, `regulations`, `regulation_versions`, `companies`, `company_policies`, `compliance_checks`, `risk_scores`, `alerts`.
- `regulations` has extra columns added: `content_hash`, `content_text`, `legal_type`.
- `scrapers/sebi_scraper.py`: scrapes the SEBI circulars listing (first 25), dedupes by URL, fetches each page's text, hashes it, inserts or updates.
- `scrapers/circular_fetcher.py`: fetches HTML text, being extended for PDFs via `pdfplumber`.
- Groq API key obtained (free tier).

Known limitations to fix: only first page (25 rows) of circulars; only circulars (not Acts/Rules/Regulations); no structured extraction; no comparison, scoring, alerting, dashboard, scheduling or tests.

---

## 3. Target Architecture

```
          ┌────────────────────────── SEBI website ──────────────────────────┐
          │ Acts · Rules · Regulations · Circulars · Master Circulars · Guidelines │
          └───────────────────────────────┬─────────────────────────────────┘
                                          ▼
 [1 INGESTION]  requests/BeautifulSoup + Playwright (pagination) + pdfplumber (+OCR fallback)
                  │  polite fetching, retries, ingestion_runs logging
                  ▼
 [2 CHANGE DETECTION]  normalize text → SHA-256 → compare with stored hash
                  │  changed/new only → save version + diff
                  ▼
 [3 PROCESSING]  clean text → chunk → embed (sentence-transformers) → pgvector
                  ▼
 [4 EXTRACTION]  Groq LLM (+Pydantic validation) → obligations table
                  ▼
 [5 COMPANY POLICIES]  mock company + policy records (text + structured fields + embeddings)
                  ▼
 [6 COMPARISON]  candidate retrieval (category filter + vector similarity)
                  → LLM judge → verdict + confidence + explanation
                  ▼
 [7 RISK + ALERTS]  score = severity/urgency/scope → alert (email/Telegram) → review queue
                  ▼
 [8 API + DASHBOARD]  FastAPI + Streamlit  ·  audit trail everywhere (audit_events)

 Orchestration: GitHub Actions (cron)  ·  Storage: Supabase Postgres + pgvector + Storage
```

---

## 4. Final Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.11+ | Type hints everywhere |
| HTTP/parse | `requests`, `beautifulsoup4`, `lxml` | Listing and detail pages |
| Browser automation | `playwright` | Only for JS-driven pagination |
| PDF | `pdfplumber`; `pytesseract` as OCR fallback | Fallback only if text extraction returns near-empty text |
| Retries | `tenacity` | Backoff on network and LLM calls |
| Database | Supabase Postgres | Relational joins power comparison |
| Vector search | `pgvector` in Supabase | Embedding dim **384** |
| Embeddings | `sentence-transformers` with `BAAI/bge-small-en-v1.5` (local, free) | No API limits |
| LLM | **Groq** (Llama-family model, set via `GROQ_MODEL` env var) | Free tier, JSON output |
| LLM fallback | Google Gemini API (free tier) | Switch via a provider interface |
| Validation | `pydantic` v2 | Schemas for extraction and judge output |
| Config | `pydantic-settings` + `.env` | One `Settings` class |
| Logging | `logging` (JSON-ish format) | Plus `ingestion_runs` table |
| API | **FastAPI** + `uvicorn` | Read endpoints plus a few actions |
| Dashboard | **Streamlit** | Fast; Next.js only if polish is needed later |
| Alerts | SMTP email and/or Telegram bot | Both free |
| Scheduling | **GitHub Actions** cron | Free |
| Tests/quality | `pytest`, `ruff`, `mypy` (light) | Run in CI |
| Packaging/deploy | Docker (Phase 9), Streamlit Community Cloud / Render / Railway | Free tiers |
| Optional scale-out | Kafka, PySpark, dbt, MinIO | Phase 9 only |

LLM abstraction: create `llm/client.py` with one interface `generate_json(prompt, schema)`. Groq is the default implementation; Gemini is a drop-in alternative. No LangChain.

---

## 4A. Code Architecture and Extensibility (modular monolith, plugins, job queue)

### 4A.1 Design goals
| Goal | Meaning for RegWatch |
|---|---|
| **Extensibility** | New regulator = one YAML config (+ at most one small adapter). **Zero edits** to detection, processing, extraction, comparison, scoring, alerts, API or dashboard. |
| **Replaceability** | Swap Supabase, Groq, the embedding model, the queue or the notifier without touching business logic. |
| **Reliability** | Every step idempotent, retryable and resumable. |
| **Testability** | Business logic runs against fakes; no network or LLM needed for unit tests. |
| **Observability and cost control** | Every run traceable; LLM calls cached and budgeted. |
| **Simplicity** | Modular monolith: one repo, one deployable. No microservices, no speculative abstractions (see 4A.17). |

### 4A.2 Architectural style: Modular Monolith + Ports and Adapters (Hexagonal / Clean)
```
interfaces  (CLI, API, dashboard)         ← entry points
     ↓ depends on
application (use-cases / pipeline stages) ← business workflow
     ↓ depends on
domain      (models, ports, events, scoring) ← pure Python, depends on NOTHING
     ↑ implemented by
infrastructure (Supabase repos, Groq, SEBI adapters, fetchers, queue, notifiers)
```
**Dependency rule:** arrows point inward only. `domain` imports nothing from other layers. `application` imports only `domain`. Source-specific or vendor-specific code lives only in `infrastructure`. Enforce this automatically with **import-linter** contracts in CI, so a violation fails the build.

### 4A.3 Package layout
The authoritative layout is in section 6. It replaces any earlier `ingestion/`-style layout.

### 4A.4 Canonical data model (Anti-Corruption Layer)
Every source adapter translates its messy local format into canonical models. Nothing downstream ever sees a source-specific field.

```python
@dataclass(frozen=True)
class ListingItem:
    source_key: str                 # "sebi"
    external_id: str | None         # regulator's own reference number, if any
    url: str
    title: str
    published_date: date | None
    legal_type: str                 # canonical: act|rule|regulation|circular|master_circular|guideline|general_order|other
    metadata: dict                  # source-specific extras, stored as JSONB, never read by core logic

@dataclass(frozen=True)
class FetchedContent:
    url: str
    text: str
    content_type: str               # html | pdf
    needs_ocr: bool
    raw_ref: str | None             # pointer to stored raw file
```
- Each source YAML has a `legal_type_map` that maps local labels (e.g. "Master Circular") to canonical types.
- The category taxonomy lives in a **`categories` table**, not in a hard-coded enum, so new domains and regulators add categories as data.

### 4A.5 Source plugin system (the key to "add a source without changing code")
Three levels, use the lowest that works:

| Level | When | What you write |
|---|---|---|
| 1. Declarative | Site is a table, list, RSS, sitemap or JSON API | Only a YAML file |
| 2. Hybrid | Mostly standard, one odd page | YAML + one custom parse function |
| 3. Custom adapter | Truly unusual site | A class extending `BaseAdapter` |

**Interface (Strategy + Template Method):**
```python
class SourceAdapter(Protocol):
    key: str
    def listings(self) -> list[ListingDefinition]: ...
    def iter_items(self, listing: ListingDefinition, mode: Mode) -> Iterator[ListingItem]: ...  # handles pagination
    def fetch_content(self, item: ListingItem) -> FetchedContent: ...
```
`BaseAdapter` implements the shared parts (pagination loop, polite fetching, HTML-vs-PDF switch, checkpointing) and exposes two hooks, `parse_listing_page(html)` and `extract_main_content(html)`. The YAML-driven `DeclarativeAdapter` is a ready-made `BaseAdapter` that reads selectors from config.

**Registry + auto-discovery (Factory):**
```python
@register("rbi")
class RbiAdapter(BaseAdapter): ...        # only if YAML alone is not enough
```
At startup: load every `sources/config/*.yaml`, import every module in `sources/adapters/`, build adapters through the registry. A source with `enabled: false` is skipped.

**Example `sources/config/sebi.yaml`:**
```yaml
key: sebi
name: Securities and Exchange Board of India
jurisdiction: IN
base_url: https://www.sebi.gov.in
allowed_domains: [www.sebi.gov.in]
robots_respected: true
rate_limit: { requests_per_second: 0.5, max_concurrency: 2 }
enabled: true
legal_type_map: { "Circular": circular, "Master Circular": master_circular, "Regulation": regulation }
listings:
  - name: circulars
    legal_type: circular
    url: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0
    parser: html_table
    selectors: { row: "table tr", date: "td:nth-child(1)", title: "td:nth-child(2)", link: "td:nth-child(2) a" }
    pagination: { type: playwright_click, next_selector: "<find in DevTools>", max_pages: null }
    content: { main_selector: "<inspect page>", follow_pdf: true }
  - name: regulations
    legal_type: regulation
    url: https://www.sebi.gov.in/sebi_data/commondocs/Regulations.html
    parser: html_table
    pagination: { type: none }
```
**Built-in parsers:** `html_table`, `html_list`, `json_api`, `rss`, `sitemap`. **Built-in paginators:** `none`, `query_param`, `next_link`, `json_cursor`, `playwright_click`. New parser or paginator types are added once and then reused by every source.

### 4A.6 Ports (interfaces) and dependency injection
Ports are `typing.Protocol` classes in `domain/ports.py`. Implementations live in `infrastructure/`. `bootstrap.py` is the **composition root**, the only place that picks concrete classes and wires them in. Tests pass fakes.

| Port | Default implementation | Fake for tests | To swap, change only |
|---|---|---|---|
| `DocumentRepository`, `ObligationRepository`, `PolicyRepository`, `CheckRepository` | Supabase | In-memory | `infrastructure/db/` |
| `Fetcher` | requests + Playwright | Fixture reader | `infrastructure/fetch/` |
| `LLMClient` | Groq (Gemini fallback) | Canned JSON | `infrastructure/llm/` |
| `Embedder` | bge-small local | Hash-based vectors | `infrastructure/embeddings/` |
| `Notifier` | Email, Telegram | List collector | `infrastructure/notify/` |
| `JobQueue` | Postgres table | In-memory queue | `infrastructure/db/queue.py` |
| `Clock` | System time | Frozen time | `infrastructure/` |

**API design:** version every route (`/v1/...`), paginate and filter list endpoints, publish OpenAPI, and keep POST actions idempotent.

### 4A.7 Pipeline design: stateful stages on a job queue (Pipes and Filters)
Each stage is a small use-case function `handle(job)`. Stages are decoupled by a **Postgres-backed job queue**. This gives queue behaviour (retries, scaling, backpressure) without Kafka, behind a `JobQueue` port so Kafka or SQS can replace it later with no business-logic change.

```
ingest_listing → fetch_document → detect_change → chunk_embed
   → extract_obligations → compare → score_alert → send_alert
```
Each stage finishes by enqueuing the next job (domain events such as `DocumentChanged`, `ObligationsExtracted`, `PolicyChanged` map to the next job type).

```sql
CREATE TABLE jobs (
  id BIGSERIAL PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  dedupe_key TEXT,
  status TEXT NOT NULL DEFAULT 'pending',     -- pending|running|done|failed|dead
  attempts INT NOT NULL DEFAULT 0,
  max_attempts INT NOT NULL DEFAULT 5,
  run_after TIMESTAMPTZ NOT NULL DEFAULT now(),
  locked_at TIMESTAMPTZ,
  last_error TEXT,
  run_id BIGINT REFERENCES ingestion_runs(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX jobs_dedupe_active_uq ON jobs(dedupe_key)
  WHERE status IN ('pending','running');

-- claim_job(): SQL function called through supabase.rpc, safe for many workers
-- UPDATE jobs SET status='running', locked_at=now(), attempts=attempts+1
-- WHERE id = (SELECT id FROM jobs WHERE status='pending' AND run_after<=now()
--             ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *;
```
- **Retries:** on failure, set `run_after = now() + backoff(attempts)` with jitter; after `max_attempts` mark `dead` (dead-letter). A dashboard page lists dead jobs for manual retry.
- **Stale locks:** a janitor step resets `running` jobs locked for more than 15 minutes.
- **Outbox principle:** insert the next job in the same DB transaction as the state change that caused it, so a crash never leaves work half-triggered.
- **Scaling:** run N identical workers (`regwatch worker`). Each pulls whatever job is available.

### 4A.8 Reliability patterns
| Pattern | Where applied |
|---|---|
| **Idempotency** | Upserts on natural keys; `UNIQUE(source_id, url)`; job `dedupe_key`; check dedupe via `inputs_hash` (4A.9) |
| **Retry with exponential backoff + jitter** | HTTP fetches, LLM calls, notifications (`tenacity`) |
| **Timeouts** | Every network call has an explicit timeout |
| **Rate limiting (token bucket)** | Per source host, from YAML `rate_limit` |
| **Bulkhead** | Per-source concurrency cap so one slow source cannot starve the others |
| **Circuit breaker** | Per source and per LLM provider: after N consecutive failures, pause calls for a cool-down period |
| **Graceful degradation** | LLM provider fallback (Groq → Gemini); OCR optional; extraction skipped, not fatal, when the LLM budget is exhausted |
| **Dead-letter queue** | Jobs that exhaust retries move to `dead` with the error recorded |
| **Checkpointing** | Backfill saves `(source, listing, last_page)` and resumes after a crash |
| **Backpressure** | Queue depth limits how fast upstream stages enqueue (cap pending extract jobs) |

### 4A.9 Data design principles
- **Natural keys and upserts** so re-runs never duplicate.
- **Append-only history** (`regulation_versions`, `audit_events`); change state with `status` columns instead of deleting rows (event-sourcing-lite, which gives a free audit trail).
- **JSONB `metadata`** for source-specific data the core never reads.
- **Taxonomy as data** (`categories` table).
- **Read models (CQRS-lite):** the pipeline is the write path; the API and dashboard read from SQL views.
- **Tenant-ready:** every company-scoped table carries `company_id`, protected by Row Level Security.
- **Forward-only migrations** in `migrations/`. Plan for table partitioning on `regulation_chunks` and `audit_events` only if they grow large.

```sql
-- Schema additions for the design above
ALTER TABLE sources
  ADD COLUMN IF NOT EXISTS key TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS jurisdiction TEXT,
  ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS config JSONB;

ALTER TABLE regulations
  ADD COLUMN IF NOT EXISTS external_id TEXT,
  ADD COLUMN IF NOT EXISTS parent_regulation_id INT REFERENCES regulations(id),
  ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
CREATE UNIQUE INDEX IF NOT EXISTS regulations_source_url_uq ON regulations(source_id, url);

CREATE TABLE IF NOT EXISTS categories (
  key TEXT PRIMARY KEY, label TEXT, description TEXT, active BOOLEAN DEFAULT true);

CREATE TABLE IF NOT EXISTS llm_cache (
  cache_key TEXT PRIMARY KEY,            -- hash(content_hash + prompt_version + model)
  response JSONB NOT NULL, model TEXT, prompt_version TEXT,
  created_at TIMESTAMPTZ DEFAULT now());

ALTER TABLE compliance_checks ADD COLUMN IF NOT EXISTS inputs_hash TEXT;  -- hash(obligation text + policy text + prompt_version)
CREATE UNIQUE INDEX IF NOT EXISTS compliance_checks_dedupe_uq
  ON compliance_checks(obligation_id, company_policy_id, inputs_hash);

CREATE OR REPLACE VIEW v_compliance_summary AS   -- implementation: take the latest check per pair (DISTINCT ON)
SELECT cp.company_id, cc.verdict, count(*) AS n
FROM compliance_checks cc JOIN company_policies cp ON cp.id = cc.company_policy_id
GROUP BY cp.company_id, cc.verdict;
```

### 4A.10 Caching
- **LLM cache** (`llm_cache`): key = hash(content_hash, prompt_version, model). An unchanged document never triggers an LLM call.
- **HTTP conditional requests** (`ETag`, `If-Modified-Since`) where the server supports them, to skip downloads.
- **Embeddings** are keyed by content hash and recomputed only for new versions.

### 4A.11 Configuration and feature flags
12-factor settings via `pydantic-settings`; no config in code. Flags and per-source switches: `enabled` per source, `OCR_ENABLED`, `LLM_PROVIDER`, `EXTRACTION_PRIORITY_CATEGORIES`, `DAILY_LLM_BUDGET`, `MAX_PAGES`.

### 4A.12 Observability
- A `run_id` correlation ID appears in every log line and job.
- Metrics live in `ingestion_runs` and `jobs` (counts, durations, failures, queue depth).
- `GET /v1/health` plus a Pipeline Health dashboard page.
- **Anomaly alert:** a source returning 0 items, or a sudden drop versus its recent average, usually means the site layout changed, so alert on it.

### 4A.13 Testing the architecture
- **Adapter contract tests:** one parametrized suite run against *every* registered adapter using saved fixtures in `tests/fixtures/<source>/`. A new source must pass the same suite, which guarantees it behaves like the others.
- **Fakes** for every port; unit tests use them, so nothing needs the network or an LLM.
- **import-linter contracts** guard the dependency rule.
- **FakeRegulator:** a fixture-only test source used to prove that adding a source needs no core changes.

### 4A.14 Security design
- **Domain allowlist per source** (`allowed_domains`) so the fetcher cannot be steered to arbitrary hosts (SSRF protection); respect `robots.txt`.
- **Scraped text is untrusted input.** Treat it as data when prompting the LLM: wrap it in clear delimiters, instruct the model to ignore any instructions found inside it, validate output against Pydantic schemas, and never let LLM output trigger actions directly.
- Least-privilege keys; the service-role key only in backend and CI; Row Level Security on all tables.
- Secrets only in env or CI secrets; dependency pinning and `pip-audit`.

### 4A.15 Scalability path (no rewrite needed)
| Pressure | Change | Code affected |
|---|---|---|
| More documents | Run more workers | None |
| Queue outgrows Postgres | Implement `JobQueue` with Kafka or SQS | `infrastructure/db/queue.py` only |
| Heavy backfill parsing | Run the parse/extract handler on Spark | New infrastructure runner |
| LLM provider change | New `LLMClient` implementation | `infrastructure/llm/` only |
| Many regulators | Add YAML files | Config only |
| Many tenants | Use the existing `company_id` + RLS | Policies only |
| Slow reads | Materialized views or read replica | DB only |

### 4A.16 How to add a new source (the extensibility acceptance test)
1. Create `sources/config/<key>.yaml` (listings, selectors, pagination, rate limit, `legal_type_map`).
2. Only if the layout is unusual: add `sources/adapters/<key>.py` with the two hooks.
3. Save 2-3 real pages under `tests/fixtures/<key>/` and run the adapter contract suite.
4. Seed any new rows in `categories` if the domain needs them.
5. Run `regwatch backfill --source <key>`, then let the scheduler handle incremental runs.

**Pass condition:** the diff touches only `sources/` and `tests/fixtures/`. No edits in `domain/`, `application/`, `interfaces/` or any other infrastructure folder. Target time: under 1 hour for a Level 1 source.

### 4A.17 YAGNI guardrails (do not build these)
- No microservices, service mesh or API gateway.
- No Kafka, Spark or dbt before Phase 11, since the `JobQueue` port keeps the door open.
- No generic plugin framework beyond the registry described above.
- No abstraction without at least two real implementations or a test fake that needs it.
- No premature optimization of the vector index or partitioning.

---

## 4B. System Design for RegWatch (requirements, capacity, consistency, reliability, security, operations)

Section 4A covers how the code is organised. This section covers how the *system* must behave, and it is derived from RegWatch's own features: scheduled ingestion of a slow external site, versioned legal text, a rate-limited LLM, vector and keyword search, a compliance verdict workflow, alerting, and confidential company policies. Section 4B.19 maps every item to the phase that implements it. Numbers marked *(assumption)* must be verified during the phase named next to them.

### 4B.1 Requirements

**Functional:** ingest all seven SEBI legal types; detect new and changed documents; keep full version history; extract obligations; compare against company policies; produce verdicts; score risk; alert; human review; search; dashboard and API; audit trail.

**Non-functional targets (SLOs):**
| Quality | Target | How it is measured |
|---|---|---|
| Freshness | A new SEBI document is detected within 6 hours (p95) of appearing | `now() - first_seen_at` vs published date, per run |
| Alert latency | High and critical alerts delivered within 30 minutes of the verdict | `alerts.sent_at - compliance_checks.checked_at` |
| Completeness | ≥98% of items SEBI lists are ingested | Reconciliation against SEBI's displayed totals (`crawl_state`) |
| Pipeline reliability | ≥95% of scheduled runs succeed; oldest pending job under 2 hours | `ingestion_runs`, `jobs` |
| Extraction quality | ≥99% of LLM outputs schema-valid; ≥80% obligations correct on the gold set | Evaluation harness |
| Verdict quality | Numeric cases 100% correct; overall ≥85% on the gold set | Evaluation harness |
| Read latency | API p95 under 500 ms on indexed queries | API logs |
| Dashboard availability | 99% best-effort (free-tier hosting) | Health checks |
| Durability | No loss of primary data; RPO ≤ 24 h, RTO ≤ 4 h | Backup and restore drill |
| Auditability | Every verdict traceable to regulation version, obligation, policy version, model and prompt version | "Explain this verdict" API |

**Asymmetric error cost:** missing a real non-compliance is worse than raising a false alarm. The system therefore defaults to `needs_review` whenever it is unsure, and never auto-marks something compliant on low confidence.

### 4B.2 Capacity estimation and what it forces in the design *(assumptions, verify in Phase 1 reconciliation)*
| Quantity | Estimate | Design consequence |
|---|---|---|
| Total SEBI legal documents | roughly 5k-15k (circulars alone list 2,800+) | Ingestion must be resumable and run in batches |
| Text per document | ~30-100 KB text; PDFs ~0.2-2 MB; master circulars far larger | Store raw files outside the main DB |
| New or changed documents per week | roughly 5-30 | Incremental load is trivial; only backfill is heavy |
| Chunks per document | ~20 | 100k-300k chunks if everything is chunked |
| Vector size | 384 floats × 4 bytes ≈ 1.5 KB each | 150-450 MB of vectors alone if everything is embedded |
| Free database limit | verify Supabase free limits (historically ~500 MB database, ~1 GB file storage) | **Storage tiering is mandatory (4B.4)** |
| Backfill duration | 10k docs × ~2 requests ÷ 0.5 requests/s ≈ 11 hours | Exceeds one GitHub Actions job (6 h max): use checkpointed, chained batches |
| LLM load | extraction ≈ documents × tokens per document; judging ≈ obligations × top-k × companies | Priority queue, caching, daily budget, local rule-based checks first |

### 4B.3 Consistency, ordering and concurrency
- **Source of truth:** one Postgres primary. Strong consistency inside a transaction; stages are linked by the job queue, so the pipeline is **eventually consistent** (dashboard may lag by minutes, which is acceptable).
- **Delivery semantics:** at-least-once job processing plus idempotent handlers gives an effectively-once result.
- **Per-document ordering:** versions are numbered (`UNIQUE(regulation_id, version_no)`) and detect/extract jobs for the same document share a `dedupe_key`, so two versions are never processed out of order.
- **Races and their fixes:**
  | Race | Fix |
  |---|---|
  | Document changes while extraction of the old version is running | Results carry `version_id`; if it is no longer current, the result is stored as stale and not used |
  | Policy edited during a comparison | `inputs_hash` mismatch triggers recomputation |
  | Two workers claim the same job | `FOR UPDATE SKIP LOCKED` plus `dedupe_key` |
  | Duplicate alerts | `alerts.dedupe_key` unique index |
  | Backfill re-run | Upserts on `(source_id, url)` |
- **Time:** store UTC `timestamptz`; keep the regulator's `published_date` and `effective_date` as dates in IST; compute urgency using IST dates. Cover with tests around day boundaries.
- **Outbox:** the next job is inserted in the same transaction as the state change that triggers it.

### 4B.4 Storage design: tiering and data lifecycle
- **Content-addressable raw storage:** save each raw PDF or HTML in object storage under its SHA-256. Identical content is stored once and is immutable. `regulation_versions.raw_sha256` and `raw_storage_path` point to it.
- **Single copy of text:** full text lives in `regulation_versions`; `regulations` keeps `current_version_id` and only a short preview. Do not duplicate `content_text` in both tables.
- **Selective embedding:** embed obligations always (a few thousand). Embed document chunks only for priority documents (the cybersecurity demo domain first) and lazily for others on first search. Drop chunk embeddings of superseded versions after a retention window; keep their text and obligations for audit.
- **Compact vectors:** record `embedding_model` on every vector; consider `halfvec` if storage is tight.
- **Hot vs cold:** hot = metadata, current text of active documents, obligations, checks, alerts. Cold = raw files and old versions, in object storage or compressed.
- **Storage monitor:** alert at 70% and 85% of the database limit; a cleanup job applies the retention rules.
- **Retention:** `audit_events`, verdicts, review decisions and alert acknowledgements are kept indefinitely (small, and primary data).

### 4B.5 Search and retrieval design
- **Hybrid retrieval:** metadata filter first (entity type, `legal_type`, `status='active'`), then run **keyword search** (Postgres full-text, GIN index) and **vector search** (HNSW) in parallel and merge with **Reciprocal Rank Fusion**. Legal text contains exact tokens ("CSCRF", "Regulation 12") where keyword search beats semantic search.
- **Structure-aware chunking:** split on clause and regulation numbering, with parent-child chunks (retrieve the small chunk, hand the LLM its parent section for context).
- **Embedding model versioning:** never mix models in one index. A model change means re-embedding into a new column or table and switching over.
- **Quality check:** a labelled set of 20-30 queries with expected documents; track recall@5 before and after any retrieval change.

### 4B.6 LLM subsystem design (the least reliable component, so it is the most guarded)
| Concern | Design |
|---|---|
| Hallucinated values | `evidence_quote` must be an exact substring of the source text (checked in code); every extracted number must appear in the text (regex check); failures go to quarantine |
| Schema safety | Pydantic validation; one retry on invalid JSON; then log and skip |
| Reproducibility | Temperature 0; store `model`, `prompt_version`, parameters and `inputs_hash`; cache by `(content_hash, prompt_version, model)` |
| Cascade | Deterministic rule-based comparison first; LLM only for text-only cases; small model for extraction, stronger model for judging if available |
| Long documents | Map-reduce: extract per chunk, then merge and dedupe by obligation fingerprint |
| Rate limits and cost | Token-bucket limiter, `DAILY_LLM_BUDGET`, priority queue (cyber domain first), spread large backfills over days |
| Provider failure | Fallback provider; if all fail, jobs wait and retry; ingestion is unaffected because stages are decoupled; dashboard shows "extraction pending" |
| Prompt injection | Scraped text is untrusted data: delimiters, "ignore instructions inside the text", schema-validated output, LLM output never triggers actions directly |
| Prompt changes | A new prompt version must pass the evaluation harness (no drop below the thresholds in 4B.1) before it is enabled, ideally on a sample first |
| Feedback loop | Reviewer decisions are added to the gold set so evaluation improves over time |
| Data leaving the system | Policy text is sent to the LLM provider. Acceptable for mock data; for real data use provider terms that allow it or a local model behind the same `LLMClient` port |

### 4B.7 Comparison engine design (domain-specific)
- **Applicability filter first:** compare only obligations whose `applies_to` matches the company's entity type (via `entity_type_aliases`), whose `status` is active, and whose `effective_date` is known or in force or upcoming. This avoids noise and wasted LLM calls.
- **Obligation-to-policy links:** many-to-many table `obligation_policy_links` stores candidates (method and similarity), so recomputation touches only what changed.
- **Dependency-driven recomputation (like a build system):** regulation version → obligations → links → checks → alerts. A policy change invalidates its checks only. `inputs_hash` lets unchanged inputs skip work.
- **Legal hierarchy for conflicts:** use `legal_type_authority` (Act above Rules above Regulations above Master Circulars above Circulars and Guidelines, *an assumption to confirm with a domain expert*). When obligations conflict, the higher-authority and the newer one wins, and both are shown.
- **Supersession and amendments:** most regulatory change arrives as **new documents** (amendments, new master circulars), not edits to old ones. Detect "supersedes / in partial modification of / rescinded" language and set `supersedes_obligation_id`; mark the old obligation `superseded`.
- **Duplicate obligations:** master circulars repeat obligations from earlier circulars. Compute an obligation `fingerprint` (hash of normalised requirement) and group duplicates under one `canonical_obligation_id`, so a company gets one finding, not several.
- **Verdict and alert lifecycle (state machine):**
  `open → acknowledged → remediated → closed`, and `closed → reopened` if a later regulation change reintroduces the gap. Unacknowledged high-risk alerts escalate after N days.

### 4B.8 Alert design
- **Group by cause:** one alert per regulation change per company, listing all affected obligations, to prevent alert fatigue.
- **Severity routing:** critical and high are sent immediately; medium and low go into a daily digest.
- **Dedupe and idempotency:** `alerts.dedupe_key` (company + regulation version + channel). Sending is at-least-once from an outbox, deduped to effectively-once.
- **Channel fallback and tracking:** email, then Telegram on failure; delivery status and retries recorded; failures raise an ops alert.
- **Content:** regulation title and link, obligation, company's current value, required value, explanation, deadline, risk level, and a link to "explain this verdict".

### 4B.9 API, authentication and authorisation
- **AuthN:** Supabase Auth (JWT) for dashboard users; API keys for service-to-service calls.
- **AuthZ:** roles `viewer`, `officer`, `admin` in `company_members`; **Row Level Security** isolates company data. Regulations are global and read-only to all authenticated users.
- **API conventions:** `/v1` versioning, cursor pagination, filters, `ETag` on GET, `Idempotency-Key` header on POST, errors as RFC 7807 `problem+json`, per-key rate limiting, OpenAPI docs.
- **Audit of user actions:** acknowledge, override and resolve actions write `audit_events` with the user ID.
- **Explainability endpoint:** `GET /v1/checks/{id}/explain` returns the full chain: verdict → obligation (with evidence quote) → chunk → regulation version → raw file hash, plus the policy version, model and prompt version.

### 4B.10 Multi-tenancy and privacy
Regulations are shared data. Policies, checks, alerts and reviews are tenant-private and carry `company_id`, protected by RLS. Redact obvious secrets before LLM calls. For real deployments, document which provider sees company text, or use a local model.

### 4B.11 Observability and SLO monitoring
- **Metrics:** jobs by type and status, queue depth, **age of the oldest pending job**, LLM calls, tokens, cache hit rate and spend, ingestion items by outcome, per-source error rate, embedding backlog, storage use.
- **Logs:** structured JSON with `run_id`, `job_id`, `document_id`.
- **Alerts to ops (Telegram):** oldest pending job above threshold, run failure rate, **zero-items anomaly**, storage at 70%/85%, dead-letter jobs present, LLM budget exhausted.
- **Pipeline Health page** in the dashboard shows these. Distributed tracing is skipped (YAGNI); correlation IDs are enough.

### 4B.12 Failure mode analysis
| Failure | Impact | Detection | Mitigation |
|---|---|---|---|
| SEBI site down or slow | No new documents | HTTP errors, zero items | Retry with backoff, circuit breaker, next run catches up (idempotent), dashboard shows a staleness banner |
| SEBI layout change | Empty or garbage parse | Zero-item anomaly, sanity checks (minimum text length, required fields present) | Fail loudly, quarantine, fixture-based parser tests, per-source parser versions |
| Blocked or rate-limited (429/403) | Ingestion halts | Status codes | Back off, lower rate, circuit opens, descriptive User-Agent |
| Scanned or garbled PDF | Empty text | Text quality score (share of alphabetic characters, length) | `needs_ocr` flag, OCR fallback, else `unextractable` plus alert |
| LLM outage or rate limit | Extraction delayed | Queue age, errors | Fallback provider, backlog shown on dashboard, ingestion unaffected |
| LLM wrong output | Bad obligations or verdicts | Schema and substring checks, evaluation harness | Quarantine, confidence thresholds, review queue |
| Database nearly full | Writes fail | Storage monitor | Tiering, retention cleanup, alerts at 70%/85% |
| GitHub Actions 6 h timeout | Partial backfill | Job duration | Checkpointed, chained batches |
| Worker crash mid-job | Stuck job | Stale lock check | Lock timeout recovery, idempotent handlers |
| Poison document that always fails | Blocks queue | Attempts count | `max_attempts` then dead-letter; others continue |
| Duplicate alerts | User fatigue | Unique index violations | `dedupe_key` |
| Date or timezone bug | Wrong urgency | Day-boundary tests | Explicit IST dates, tests |
| Bad migration | Outage or data loss | CI on staging | Forward-only migrations tested on a staging project, backup before migrating |
| Secret leaked | Account compromise | Secret scanning in CI (gitleaks) | Rotate keys, least privilege |

### 4B.13 Backup and disaster recovery
- **Derived vs primary data:** regulation text is *re-fetchable* from SEBI (derived), so recovery means re-running the idempotent backfill. **Primary data cannot be recreated:** company policies, review decisions, alert acknowledgements, audit events. These get the strongest protection.
- Enable Supabase backups (verify what the free plan includes; it may not include point-in-time recovery) and add a **weekly `pg_dump` of primary tables** via a scheduled workflow to private storage.
- **Restore drill:** restore into a staging project once before production sign-off and record the time against the RTO.

### 4B.14 Environments, CI/CD and release
- **Environments:** local, staging (a second Supabase project), production. Config differs only through environment variables.
- **CI pipeline:** lint → unit tests → adapter contract tests → integration tests on fixtures → import-linter → secret scan → build image → deploy (production only from the main branch).
- **Migrations:** forward-only, applied by CI, tested on staging first.
- **Rollback:** redeploy the previous image; fix data issues with a forward migration.
- **Versioned artefacts:** prompts, taxonomy and the obligation schema carry version numbers; job payloads and events include `schema_version` so older jobs still process after a code change.

### 4B.15 Data quality, lineage and governance
- **Quality gates per stage:** minimum text length, plausible dates, URL on the domain allowlist, duplicate detection by hash, language check, orphan-row check. Failing items go to `quarantine_items` instead of being dropped silently.
- **Reconciliation job:** compares ingested counts to SEBI's reported totals and writes the gap to `crawl_state`.
- **Lineage:** verdict → obligation → chunk → version → raw file hash. Nothing in the chain is overwritten.
- **Schema evolution:** additive changes first; remove a column only after code no longer reads it.

### 4B.16 Scheduling design (tailored to how SEBI publishes)
Most regulatory change arrives as **new documents**, and old circulars are rarely edited. So spend effort on discovering new items quickly and only sample old ones.
| Class | Examples | Re-check |
|---|---|---|
| New-item discovery | First 1-2 pages of every listing | Every 6 hours (hourly during 09:00-21:00 IST if desired) |
| Fresh documents | Published in the last 90 days | Daily content hash check |
| Standing documents | Older circulars and master circulars | Rotating sweep, about 1/30 per day (full pass monthly) |
| Foundational | Acts, Rules, Regulations and their amendment lists | Weekly listing check |

Use `If-None-Match` / `If-Modified-Since` when the server supports them, add jitter to cron times, and use the listing's reported total to detect additions or removals. Each regulation stores `check_class` and `next_check_at` so the scheduler simply picks what is due.

### 4B.17 Resource and cost budget (free tiers; verify current limits)
| Resource | Constraint | Design response |
|---|---|---|
| Supabase database | ~500 MB historically | Tiering, selective embedding (4B.4) |
| Supabase file storage | ~1 GB historically | Content-addressable storage, compress, retention |
| GitHub Actions | 6 h per job; monthly minutes limit for private repos | Chained batches; public repo or minute budgeting |
| Groq or Gemini free tier | Per-minute and per-day token limits | Token bucket, daily budget, cache, priority queue |
| Free API hosting | May sleep when idle | Accept cold starts; keep the dashboard read-only against the DB |
| Local embeddings | CPU time | Batch, embed lazily, measure throughput in Phase 3 |

### 4B.18 Additional test types for these properties
- **Property-based tests** (Hypothesis) for text normalisation and hashing (whitespace-insensitive, content-sensitive).
- **Chaos-lite tests:** kill a worker mid-job, return HTTP 429, make the LLM return garbage; assert recovery with no duplicates.
- **Queue load test:** 10k fake jobs through two workers.
- **Evaluation gate:** prompt or model changes must pass the evaluation harness.
- **Migration tests** on a staging database; **day-boundary tests** for urgency.

### 4B.19 Where each design concern is implemented
| Phase | System design items to implement and verify |
|---|---|
| 0 Foundation | 4A (ports, layers, plugins, job queue), CI with import-linter and secret scan, staging project, `crawl_state`, versioned job payloads |
| 1 Ingestion | Rate limit, circuit breaker, checkpointed and chained backfill, reconciliation, quality gates and quarantine, tiered scheduling classes (4B.16), domain allowlist |
| 2 Change detection | Version numbering and per-document ordering, content-addressable raw storage, single text copy, `current_version_id`, outbox, audit events |
| 3 Chunks and embeddings | Selective and lazy embedding, structure-aware chunking, hybrid search (keyword + vector + rank fusion), embedding model versioning, retrieval recall check |
| 4 Extraction | LLM guardrails (substring and number checks), cache, token bucket and daily budget, priority queue, evaluation harness, prompt versioning, injection defence |
| 5 Policies | Tenant columns, RLS, entity type aliases, policy versioning |
| 6 Comparison | Applicability filter, link table, dependency-driven recomputation, `inputs_hash` dedupe, legal hierarchy, supersession, obligation fingerprints, asymmetric-error defaults |
| 7 Risk and alerts | Alert grouping, severity routing and digest, dedupe keys, lifecycle state machine and escalation, channel fallback |
| 8 API and dashboard | AuthN/AuthZ, RLS-backed reads, API conventions, explainability endpoint, pipeline health page, staleness banner |
| 9 Production | SLO monitoring and ops alerts, storage monitor, backups and restore drill, staging-to-production release, failure-mode drills from 4B.12 |
| 10 Evaluation | Gold sets, SLO measurements against the 4B.1 targets, chaos-lite results |

---

## 5. Data Model (target)

Existing tables stay. Add or alter via migrations. `VECTOR(384)` matches `bge-small-en-v1.5`.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Operational log of every pipeline run
CREATE TABLE ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  source_id INT REFERENCES sources(id),
  legal_type TEXT,
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status TEXT,                -- running | success | partial | failed
  items_seen INT DEFAULT 0,
  items_new INT DEFAULT 0,
  items_changed INT DEFAULT 0,
  items_failed INT DEFAULT 0,
  error TEXT
);

-- regulations: keep existing columns, ensure these exist
ALTER TABLE regulations
  ADD COLUMN IF NOT EXISTS legal_type TEXT,         -- act|rule|regulation|circular|master_circular|guideline
  ADD COLUMN IF NOT EXISTS published_date DATE,
  ADD COLUMN IF NOT EXISTS reference_number TEXT,
  ADD COLUMN IF NOT EXISTS department TEXT,
  ADD COLUMN IF NOT EXISTS content_text TEXT,
  ADD COLUMN IF NOT EXISTS content_hash TEXT,
  ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ DEFAULT now(),
  ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_changed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
CREATE UNIQUE INDEX IF NOT EXISTS regulations_url_uq ON regulations(url);

-- Full history of content
ALTER TABLE regulation_versions
  ADD COLUMN IF NOT EXISTS content_text TEXT,
  ADD COLUMN IF NOT EXISTS diff_summary TEXT;

-- Chunks + embeddings for semantic search
CREATE TABLE regulation_chunks (
  id BIGSERIAL PRIMARY KEY,
  regulation_id INT REFERENCES regulations(id) ON DELETE CASCADE,
  version_id INT REFERENCES regulation_versions(id),
  chunk_index INT,
  text TEXT NOT NULL,
  embedding VECTOR(384)
);
CREATE INDEX ON regulation_chunks USING hnsw (embedding vector_cosine_ops);

-- Extracted, comparable obligations (the heart of the comparison)
CREATE TABLE obligations (
  id BIGSERIAL PRIMARY KEY,
  regulation_id INT REFERENCES regulations(id) ON DELETE CASCADE,
  version_id INT REFERENCES regulation_versions(id),
  category TEXT,                 -- e.g. incident_reporting, kyc, data_retention
  applies_to TEXT,               -- e.g. stock_broker, market_intermediary
  requirement_text TEXT NOT NULL,
  evidence_quote TEXT,           -- short quote from source for traceability
  metric_name TEXT,              -- e.g. incident_report_hours (nullable)
  operator TEXT,                 -- <=, >=, =, must, must_not (nullable)
  threshold_value NUMERIC,
  unit TEXT,
  effective_date DATE,
  confidence NUMERIC,
  model TEXT,
  prompt_version TEXT,
  status TEXT DEFAULT 'active',  -- active | superseded
  embedding VECTOR(384),
  extracted_at TIMESTAMPTZ DEFAULT now()
);

-- company_policies: extend the existing table
ALTER TABLE company_policies
  ADD COLUMN IF NOT EXISTS title TEXT,
  ADD COLUMN IF NOT EXISTS policy_text TEXT,
  ADD COLUMN IF NOT EXISTS metric_name TEXT,
  ADD COLUMN IF NOT EXISTS value NUMERIC,
  ADD COLUMN IF NOT EXISTS unit TEXT,
  ADD COLUMN IF NOT EXISTS embedding VECTOR(384),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- compliance_checks: verdicts with confidence + explanation
ALTER TABLE compliance_checks
  ADD COLUMN IF NOT EXISTS obligation_id BIGINT REFERENCES obligations(id),
  ADD COLUMN IF NOT EXISTS verdict TEXT,          -- compliant|non_compliant|needs_review|no_policy
  ADD COLUMN IF NOT EXISTS confidence NUMERIC,
  ADD COLUMN IF NOT EXISTS explanation TEXT,
  ADD COLUMN IF NOT EXISTS method TEXT,           -- rule_based | llm_judge
  ADD COLUMN IF NOT EXISTS triggered_by TEXT;     -- onboarding | regulation_change | policy_change

ALTER TABLE risk_scores
  ADD COLUMN IF NOT EXISTS severity INT,
  ADD COLUMN IF NOT EXISTS urgency INT,
  ADD COLUMN IF NOT EXISTS scope INT,
  ADD COLUMN IF NOT EXISTS level TEXT;            -- low|medium|high|critical

ALTER TABLE alerts
  ADD COLUMN IF NOT EXISTS channel TEXT,
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending',   -- pending|sent|failed
  ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;

CREATE TABLE review_queue (
  id BIGSERIAL PRIMARY KEY,
  compliance_check_id INT REFERENCES compliance_checks(id),
  status TEXT DEFAULT 'open',    -- open | confirmed | overridden
  final_verdict TEXT,
  reviewer_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

CREATE TABLE audit_events (
  id BIGSERIAL PRIMARY KEY,
  entity TEXT, entity_id TEXT, event_type TEXT,
  payload JSONB, created_at TIMESTAMPTZ DEFAULT now()
);

-- Similarity search helper (call via supabase.rpc)
CREATE OR REPLACE FUNCTION match_obligations_to_policies(
  query_embedding VECTOR(384), match_count INT, p_company_id INT)
RETURNS TABLE (policy_id INT, similarity FLOAT) LANGUAGE sql STABLE AS $$
  SELECT id, 1 - (embedding <=> query_embedding)
  FROM company_policies
  WHERE company_id = p_company_id AND embedding IS NOT NULL
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

---


### 5A. Schema additions required by section 4B

```sql
-- versioning, content-addressable raw storage, scheduling classes
ALTER TABLE regulation_versions
  ADD COLUMN IF NOT EXISTS version_no INT,
  ADD COLUMN IF NOT EXISTS raw_sha256 TEXT,
  ADD COLUMN IF NOT EXISTS raw_storage_path TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS regulation_versions_no_uq ON regulation_versions(regulation_id, version_no);
ALTER TABLE regulations
  ADD COLUMN IF NOT EXISTS current_version_id INT REFERENCES regulation_versions(id),
  ADD COLUMN IF NOT EXISTS check_class TEXT,          -- fresh | standing | foundational
  ADD COLUMN IF NOT EXISTS next_check_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS quality_score NUMERIC;

-- hybrid search (keyword + vector)
ALTER TABLE regulation_chunks
  ADD COLUMN IF NOT EXISTS embedding_model TEXT,
  ADD COLUMN IF NOT EXISTS tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED;
CREATE INDEX IF NOT EXISTS regulation_chunks_tsv_idx ON regulation_chunks USING gin(tsv);

-- obligations: duplicates, supersession, embedding model
ALTER TABLE obligations
  ADD COLUMN IF NOT EXISTS fingerprint TEXT,
  ADD COLUMN IF NOT EXISTS canonical_obligation_id BIGINT REFERENCES obligations(id),
  ADD COLUMN IF NOT EXISTS supersedes_obligation_id BIGINT REFERENCES obligations(id),
  ADD COLUMN IF NOT EXISTS embedding_model TEXT;
CREATE INDEX IF NOT EXISTS obligations_fingerprint_idx ON obligations(fingerprint);

-- reference data
CREATE TABLE IF NOT EXISTS legal_type_authority (legal_type TEXT PRIMARY KEY, authority_level INT);  -- lower = higher authority; confirm with a domain expert
CREATE TABLE IF NOT EXISTS entity_type_aliases (alias TEXT PRIMARY KEY, canonical_entity_type TEXT);

-- candidate links for incremental recomputation
CREATE TABLE IF NOT EXISTS obligation_policy_links (
  obligation_id BIGINT REFERENCES obligations(id) ON DELETE CASCADE,
  company_policy_id INT REFERENCES company_policies(id) ON DELETE CASCADE,
  method TEXT, similarity NUMERIC, created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (obligation_id, company_policy_id));

-- alert lifecycle and dedupe
ALTER TABLE alerts
  ADD COLUMN IF NOT EXISTS dedupe_key TEXT,            -- company + regulation version + channel
  ADD COLUMN IF NOT EXISTS lifecycle TEXT DEFAULT 'open',  -- open|acknowledged|remediated|closed|reopened
  ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ;
CREATE UNIQUE INDEX IF NOT EXISTS alerts_dedupe_uq ON alerts(dedupe_key);

-- crawl checkpoints, reconciliation, quarantine
CREATE TABLE IF NOT EXISTS crawl_state (
  source_key TEXT, listing TEXT, last_page INT, total_reported INT, total_ingested INT,
  etag TEXT, last_modified TEXT, updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (source_key, listing));
CREATE TABLE IF NOT EXISTS quarantine_items (
  id BIGSERIAL PRIMARY KEY, source_key TEXT, url TEXT, reason TEXT, payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now(), resolved BOOLEAN DEFAULT false);

-- access control (tenant isolation with Row Level Security)
CREATE TABLE IF NOT EXISTS company_members (
  user_id UUID, company_id INT REFERENCES companies(id), role TEXT,   -- viewer | officer | admin
  PRIMARY KEY (user_id, company_id));
ALTER TABLE company_policies ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON company_policies
  USING (company_id IN (SELECT company_id FROM company_members WHERE user_id = auth.uid()));
-- repeat the same pattern for alerts, review_queue and any table joined to company_id
```

---

## 6. Repository Structure

Layered per section 4A. The dependency rule is enforced by import-linter.

```
regwatch/
├── README.md
├── .env.example
├── pyproject.toml                       # deps, ruff, pytest, import-linter contracts
├── migrations/                          # 001_*.sql, 002_*.sql ... (forward-only)
├── src/regwatch/
│   ├── domain/                          # PURE Python: no I/O, no vendor SDKs
│   │   ├── models.py                    # ListingItem, FetchedContent, LegalDocument, Obligation, Policy, Check
│   │   ├── ports.py                     # Protocols: repositories, Fetcher, LLMClient, Embedder, Notifier, JobQueue, Clock
│   │   ├── events.py                    # DocumentChanged, ObligationsExtracted, PolicyChanged
│   │   ├── scoring.py                   # risk formula as a pure function
│   │   └── errors.py
│   ├── application/                     # use-cases; depend only on domain
│   │   ├── ingest.py  detect.py  process.py  extract.py
│   │   ├── compare.py  alert.py
│   │   └── handlers.py                  # job_type -> use-case mapping
│   ├── infrastructure/
│   │   ├── db/        repositories.py  queue.py  migrate.py
│   │   ├── sources/   base.py  registry.py  declarative.py
│   │   │              parsers/  paginators/  adapters/  config/*.yaml
│   │   ├── fetch/     http.py  browser.py  pdf.py  ratelimit.py  circuit_breaker.py
│   │   ├── llm/       groq.py  gemini.py  fake.py  cache.py  prompts.py
│   │   ├── embeddings/ bge_local.py  fake.py
│   │   └── notify/    email.py  telegram.py
│   ├── interfaces/
│   │   ├── cli.py                       # typer: ingest | backfill | worker | run-all | compare | seed-company
│   │   ├── api/       main.py  v1/
│   │   └── dashboard/ app.py
│   ├── bootstrap.py                     # composition root: builds adapters, wires dependencies
│   └── settings.py                      # pydantic-settings
├── tests/
│   ├── unit/  contract/  integration/
│   └── fixtures/<source>/               # saved real pages per source
├── .github/workflows/                   # ci.yml, ingest.yml
├── Dockerfile
└── docker-compose.yml                   # Phase 9
```

---

## 7. Roadmap by Phase

Each phase lists **goal → tasks → deliverables → acceptance criteria**.

### Phase 0: Foundation Hardening (0.5-1 week)
**Goal:** turn the working scripts into a clean, testable package.
- Create the layered package from section 6 (domain / application / infrastructure / interfaces) and the composition root `bootstrap.py`.
- Implement the canonical models (`domain/models.py`) and ports (`domain/ports.py`) from sections 4A.4 and 4A.6.
- Implement the source plugin system: `BaseAdapter`, registry, `DeclarativeAdapter` (YAML loader), and **port the existing SEBI circulars scraper into `sources/config/sebi.yaml`** (add a custom adapter only if YAML cannot express something).
- Implement the Postgres job queue (`jobs` table, `claim_job()` function, `JobQueue` port) and one worker loop (4A.7).
- Add the schema additions from 4A.9 as migrations.
- Add import-linter contracts for the layer rules and adapter contract tests (4A.13).
- Add a fixture-only `FakeRegulator` source to prove extensibility.
- `settings.py` (Settings from `.env`: Supabase, Groq, Gemini, SMTP, Telegram, `GROQ_MODEL`).
- `logging_setup.py`; replace `print` with logging.
- `ingestion_runs` table + helper that opens and closes a run record.
- Add `migrations/` with the SQL above split into numbered files.
- Add `pytest`, `ruff`, and a CI workflow that runs both.
- README with setup steps.

**Acceptance:** `regwatch ingest --source sebi --listing circulars` runs the existing circulars scrape through the new layers and writes an `ingestion_runs` row; `pytest` (unit + contract) and import-linter pass in CI; adding the `FakeRegulator` test source required changes only under `sources/` and `tests/fixtures/`, with no edits to `domain/` or `application/`.

### Phase 1: Complete Ingestion (1-1.5 weeks)
**Goal:** ingest *all* SEBI legal categories with full history, reliably.
- **Source registry** (YAML configs + adapters, see section 4A.5): entries for circular, master_circular, regulation, rule, act, guideline, general_order. Each has `legal_type`, listing URL, and parser name. Find the Acts, Rules and Guidelines listing URLs by browsing SEBI's LEGAL menu. Known: circulars listing (`HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0`), master circulars (`ssid=6`), regulations (`sebi_data/commondocs/Regulations.html`, a static table).
- **Per-layout listing parsers** (don't assume one `table tr` fits all). Output a common record: `{title, url, published_date, legal_type, reference_number?}`.
- **Pagination:** first try finding the underlying request in DevTools (Network tab) and call it with `requests`; if not feasible, use Playwright to click "next" up to N pages. Make `MAX_PAGES` configurable. Support an initial **backfill** mode (deep) and a normal **incremental** mode (first 1-2 pages only).
- **Fetcher:** HTML → main content text (inspect SEBI pages to pick the right container, with fallback); PDF → `pdfplumber`; if extracted text is under ~200 characters, mark `needs_ocr` and run OCR fallback if enabled. Detail pages that embed or link a PDF: follow the PDF link.
- **Politeness and resilience:** User-Agent, delay, `tenacity` retries, per-item try/except so one failure doesn't kill the run, counters written to `ingestion_runs`.
- Populate `published_date`, `legal_type`, `department` where parseable.
- **Full coverage is the goal, not a sample.** Backfill must walk *every* page of *every* category until the listing is exhausted (no fixed page cap in backfill mode).
- **Add `general_order` as a legal type.** SEBI's LEGAL menu lists Acts, Rules, Regulations, General Orders, Guidelines, Master Circulars and Circulars, so all seven are in scope.
- **Completeness check:** SEBI listing pages show a total record count (the circulars page showed 2,800+). After each backfill, compare rows ingested per `legal_type` against the total SEBI displays, and log any gap in `ingestion_runs.error`.
- **Resumable backfill:** save a checkpoint (`legal_type`, last page done) so a crash or rate limit resumes instead of restarting. Thousands of documents will not finish in one run.
- **Amendments and repealed items:** Regulations and Rules have amendment lists and some are marked repealed or omitted. Store these as separate rows, set `status` to `repealed` where the text says so, and link amendments to their parent via a `parent_regulation_id` column.
- **Separate ingestion from extraction.** Ingest and store *everything* (text, hash, versions). LLM extraction (Phase 4) runs on a priority queue instead of on all documents at once, so ingestion completeness never depends on LLM limits.

**Acceptance:** after a backfill run, every one of the seven `legal_type` values has rows; for each type, the ingested count is within 2% of the total SEBI displays (or the gap is explained in the run log); ≥90% have non-empty `content_text`; re-running inserts 0 duplicates; an interrupted backfill resumes from its checkpoint; an `ingestion_runs` row shows accurate counts.

### Phase 2: Change Detection and Versioning (0.5-1 week)
**Goal:** detect real content changes, keep full history.
- `normalize.py`: strip whitespace noise, page numbers/headers/footers, dynamic strings, normalize unicode, lowercase for hashing only.
- `versioning.py`: hash normalized text; if hash differs from `regulations.content_hash`, insert into `regulation_versions` (text + hash + `diff_summary` from `difflib`), update `regulations.last_changed_at`, mark downstream data stale (obligations get re-extracted).
- Write an `audit_events` row for `new_regulation` and `regulation_changed`.
- Tests: identical text with different whitespace → same hash; one changed number → different hash and a diff that shows it.

**Acceptance:** manually editing a stored text in the DB and re-running produces a new version row, a diff, and an audit event; unchanged items produce none.

### Phase 3: Chunking and Embeddings (0.5-1 week)
**Goal:** make documents searchable by meaning.
- `chunking.py`: split by headings/numbered clauses when present, else by ~500-800 tokens with ~100 overlap. Keep `chunk_index`.
- `embeddings.py`: load `bge-small-en-v1.5` once; batch-encode; store in `regulation_chunks.embedding` (384-dim). Re-chunk only when a new version exists.
- Helper `search_chunks(query, k)` using a Supabase RPC (add the match function in a migration).

**Acceptance:** query "incident reporting timeline for brokers" returns relevant chunks from real circulars in the top 5 (manually spot-check 5 queries).

### Phase 4: Obligation Extraction (1-1.5 weeks)
**Goal:** turn legal text into structured, comparable obligations.
- `llm/client.py` with `generate_json`; JSON mode; retry once on invalid JSON.
- `extraction/schemas.py`: Pydantic `Obligation` (category, applies_to, requirement_text, evidence_quote, metric_name, operator, threshold_value, unit, effective_date, confidence) and `ExtractionResult(obligations: list[Obligation])`.
- Prompt (versioned `prompt_version`), rules: only extract explicit requirements; never invent numbers; use null when unknown; include a short verbatim `evidence_quote`; classify `category` from a controlled list (see §8).
- Process chunk by chunk (or by section) for long documents; dedupe near-identical obligations; embed each obligation.
- **Cache** by `(content_hash, prompt_version, model)` so unchanged documents never call the LLM again. Respect Groq rate limits (sleep/backoff).
- Mark older obligations `superseded` when a regulation changes.
- Priority order for cost control: cyber/security-related instruments first (the demo domain), then the rest.

**Acceptance:** on a hand-labelled set of ≥20 circulars, ≥80% of extracted obligations are judged correct (metric/threshold/applies_to match the text); zero stored rows fail Pydantic validation; unchanged docs trigger zero LLM calls on re-run.

### Phase 5: Company and Policies (0.5 week)
**Goal:** a believable company profile to compare against (mock, clearly labelled).
- `seed_company.py`: create "FinCorp Securities" (entity_type e.g. stock_broker) and 10-15 policies across categories: some compliant, some deliberately non-compliant, some vague (to exercise review). Each policy has free-text `policy_text` plus optional `metric_name/value/unit`.
- Embed `policy_text` into `company_policies.embedding`.
- `policy_service.py`: add/update policy (updating triggers re-comparison; write an `audit_events` row).

**Acceptance:** policies exist with embeddings; changing a policy value triggers a new comparison run.

### Phase 6: Comparison Engine (1-1.5 weeks): the core
**Goal:** produce explained verdicts.
1. **Candidate retrieval** (`candidates.py`): for each active obligation relevant to the company's entity type, find policies by (a) same `category`, then (b) vector similarity (top-k) as a fallback or supplement.
2. **Rule-based check first** (`judge.py`): if the obligation has `metric_name + operator + threshold_value` and a policy has the same `metric_name + value + unit`, compare numerically (normalize units, e.g. hours/days). Result: `compliant` or `non_compliant`, `method=rule_based`, confidence 1.0.
3. **LLM judge second:** for text-only cases, prompt with obligation + policy, return `{verdict, confidence, explanation, gap}` validated by Pydantic. If `confidence < 0.7` → `needs_review` and add to `review_queue`.
4. **No candidate found** → verdict `no_policy` (a gap in itself; flagged).
5. Store in `compliance_checks` with `triggered_by`. Triggers: `onboarding` (full sweep), `regulation_change` (only affected obligations), `policy_change` (only that policy).
6. Idempotency: don't duplicate a check if obligation + policy + versions are unchanged.

**Acceptance:** on the seeded company, the engine yields the expected verdicts for a prepared answer key (≥85% match, with every disagreement explained); numeric cases are 100% correct; vague cases land in `needs_review`.

### Phase 7: Risk Scoring and Alerts (1 week)
**Goal:** prioritize and notify.
- `scoring/risk.py`:
  - `severity` 1-5: non-compliant with large gap or "must/must_not" = high; partial/needs_review = medium; `no_policy` = 3-4.
  - `urgency` 1-5 from days to `effective_date` (past due or <7 days = 5, ≤30 = 4, ≤60 = 3, ≤90 = 2, else 1; unknown = 2).
  - `scope` 1-5 from how many policies or products the obligation touches.
  - `final = round((0.4*severity + 0.4*urgency + 0.2*scope) / 5 * 100)`; level: <30 low, 30-59 medium, 60-79 high, ≥80 critical.
- Alert message template: regulation title + link, obligation text, company's current value, required value, explanation, deadline, risk score + level.
- `notifier.py` sends via email and/or Telegram, with dedupe (don't re-alert for the same unresolved check) and a `status` update.
- Review queue actions: confirm or override a verdict (recomputes score), with notes and an audit event.

**Acceptance:** a seeded non-compliant check produces one alert with a correct score and a readable message; re-running produces no duplicate alert; overriding a verdict updates the score and logs an event.

### Phase 8: API and Dashboard (1-1.5 weeks)
**Goal:** a usable product surface.
- **FastAPI** endpoints (read-mostly): `GET /regulations` (filter by type/date/source), `GET /regulations/{id}` (+ versions + obligations), `GET /companies/{id}/compliance` (summary by verdict), `GET /alerts`, `POST /alerts/{id}/acknowledge`, `GET /review-queue`, `POST /review-queue/{id}/resolve`, `GET /ingestion-runs`, `GET /health`.
- **Streamlit** pages: Overview (compliance %, open alerts by level, last ingestion), Regulations explorer (search, filters, version diff viewer), Obligations, Compliance matrix (policy × obligation with verdict colors), Alerts, Review queue, Pipeline health (ingestion runs).
- Semantic search box (uses `search_chunks`).
- Add a disclaimer banner: "Informational tool. Not legal advice. Demo uses mock company data."

**Acceptance:** all pages load against real data; the diff viewer shows an actual changed version; review actions persist.

### Phase 9: Automation and Production Readiness (1-1.5 weeks)
**Goal:** run unattended, safely and observably.
- **Scheduling:** `.github/workflows/ingest.yml` runs ingestion → processing → extraction → comparison → alerts on a cron (e.g. every 6 hours), with secrets in GitHub Secrets. A second manual-dispatch workflow handles backfill.
- **Reliability:** idempotent steps, `tenacity` retries, timeouts, per-item failure isolation, a dead-letter log table or a `failed` flag with reason, graceful LLM-provider fallback (Groq → Gemini).
- **Observability:** structured logs, `ingestion_runs` health, failure alert to Telegram if a run fails or yields 0 items unexpectedly (a sign SEBI changed its layout).
- **Security:** service-role key only in backend/CI, never in the dashboard client; enable Supabase RLS on all tables with policies; for the dashboard use a backend API or read-only access; dependency pinning; `pip-audit`.
- **Cost and limits:** LLM cache, batching, rate limiter, a daily LLM call budget setting.
- **Packaging:** `Dockerfile` for the API and dashboard; `docker-compose.yml` for local full-stack run.
- **Deployment:** API on Render/Railway (free tier), dashboard on Streamlit Community Cloud, DB on Supabase. Document environment variables.
- **Backups and data hygiene:** Supabase backups on, a documented restore step, a retention note for `content_text`.
- **Docs:** README (architecture diagram, setup, run, deploy), `docs/` with data dictionary and prompt versions.

**Acceptance:** two consecutive scheduled runs complete without manual action; a deliberately broken parser triggers a failure alert; the deployed dashboard is reachable and works; CI is green; a restore drill into staging succeeds within the 4 h RTO; the failure-mode drills in 4B.12 (worker crash, HTTP 429, LLM garbage output, zero-item parse) each recover without duplicates; SLO measurements from 4B.1 are recorded.

### Phase 10: Evaluation and Report Material (0.5-1 week, can overlap)
**Goal:** prove it works with numbers (important for a BE panel).
- Build a small **gold set**: 20-30 obligations hand-labelled, and 30-40 obligation-policy pairs with correct verdicts.
- Report: extraction precision/recall, verdict accuracy (rule-based vs LLM judge), % sent to review, average time per document, LLM calls saved by caching, ingestion success rate.
- Include an honest limitations section (mock policies, scanned PDFs, ambiguous legal language, SEBI layout changes).
- Prepare demo script: show a real new/changed circular flowing through to an alert.

### Phase 11 (Optional): Big-Data Extensions (only if time remains or your guide requires it)
Add in this order, each as an independent, explainable upgrade:
1. **Second regulator** (RBI) as another source in the registry, which proves the architecture generalizes.
2. **Medallion layout** in object storage (raw → parsed → curated Parquet) for the historical backfill.
3. **PySpark** to parallelize parsing/extraction across the large backfill.
4. **Kafka** topic `document-detected` between ingestion and processing, once there are 2+ sources.
5. **dbt** for versioned transformations into analytics tables; **DuckDB** for trend analytics ("compliance over time").

---

## 8. Prompts and Controlled Vocabulary

**Category list (start small, extend as needed):** `incident_reporting`, `cyber_resilience`, `access_control`, `data_retention`, `kyc_aml`, `disclosure`, `fees_charges`, `investor_grievance`, `outsourcing`, `business_continuity`, `audit_reporting`, `other`.

**Extraction prompt (v1) skeleton:**
```
You extract compliance obligations from Indian securities-regulation text.
Return ONLY JSON matching the schema. Rules:
- Extract only explicit requirements ("shall", "must", "required to", prohibitions).
- Never invent values. Use null if a field is not stated.
- evidence_quote: a short exact quote (<=200 chars) from the text.
- category must be one of: [list]. applies_to: the regulated entity type as stated.
- metric_name/operator/threshold_value/unit only when a measurable limit exists
  (e.g. "within 6 hours" -> metric_name=incident_report_hours, operator="<=", value=6, unit="hours").
- effective_date in ISO format if stated.
TEXT:
{chunk}
```

**Judge prompt (v1) skeleton:**
```
Obligation: {requirement_text}
Company policy: {policy_text}
Decide if the policy satisfies the obligation.
Return JSON: {verdict: "compliant"|"non_compliant"|"unclear",
confidence: 0-1, gap: string|null, explanation: <=2 sentences, citing both texts}.
If the policy does not address the obligation, verdict is "non_compliant".
If information is insufficient, verdict is "unclear".
```

Store `prompt_version` and `model` on every LLM-derived row.

---

## 9. Testing Strategy

- **Unit:** normalize/hash, diff, chunking, unit conversion, numeric comparison, risk formula, Pydantic validation (including malformed LLM output).
- **Integration:** run the pipeline against saved HTML/PDF fixtures (store a few real SEBI pages in `tests/fixtures/`) so tests don't depend on the live site.
- **LLM tests:** mock the LLM client for unit tests; keep a small, separate "live" test marked `@pytest.mark.live`.
- **Evaluation scripts** (Phase 10) are separate from unit tests.
- CI: `ruff`, `pytest` (non-live), on every push.

---

## 10. Production Checklist (Definition of Done)

- [ ] All six SEBI legal types ingested; incremental runs on schedule
- [ ] Versioning + diff + audit trail working
- [ ] Obligations extracted with validation, caching, and measured accuracy
- [ ] Comparison yields verdicts with confidence and explanation; review queue works
- [ ] Risk score and alerts delivered without duplicates
- [ ] API + dashboard deployed; disclaimer shown
- [ ] Secrets only in env/CI; RLS enabled; service key not exposed to clients
- [ ] CI green; fixtures-based tests; README + architecture diagram
- [ ] Failure alerts and pipeline-health page
- [ ] Evaluation numbers recorded for the report
- [ ] SLOs from 4B.1 measured and met (or gaps documented)
- [ ] Failure-mode drills from 4B.12 passed
- [ ] Backups configured and a restore drill completed
- [ ] Storage monitor, queue-age and zero-item alerts live
- [ ] "Explain this verdict" endpoint returns the full lineage
- [ ] RLS verified: one company cannot read another company's rows

---

## 11. Timeline (solo, realistic)

| Phase | Duration |
|---|---|
| 0 Foundation + architecture skeleton | 1-1.5 wk |
| 1 Ingestion (all types, backfill) | 1-1.5 wk |
| 2 Change detection | 0.5-1 wk |
| 3 Chunks + embeddings | 0.5-1 wk |
| 4 Extraction | 1-1.5 wk |
| 5 Company policies | 0.5 wk |
| 6 Comparison | 1-1.5 wk |
| 7 Risk + alerts | 1 wk |
| 8 API + dashboard | 1-1.5 wk |
| 9 Automation + production hardening | 1.5-2 wk |
| 10 Evaluation | 0.5-1 wk |
| **Total** | **~12-16 weeks** |

Cut order if time runs short: Phase 11 → polish in Phase 8 → OCR fallback → LLM fallback provider. Never cut: versioning, extraction validation, comparison with explanations, risk scoring, audit trail, tests.

---

## 12. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| SEBI changes page layout | Per-source parsers, fixture tests, zero-item failure alert |
| Scanned PDFs without text | OCR fallback, flag `needs_ocr` |
| LLM hallucinated values | Evidence quote required, Pydantic validation, rule-based check where numeric, review queue |
| Free-tier rate limits | Cache, batch, backoff, provider fallback, daily budget |
| Ambiguous legal language | `needs_review` path, show evidence quotes, "not legal advice" notice |
| Mock policies look unrealistic | Label as mock; include compliant, non-compliant and vague cases |
| Scope creep | Phase gates and the cut order above |

---

## 13. First Message to Give the Agent

> Read `RegWatch-End-To-End-Roadmap.md` fully. Follow the Working Rules in section 0 and the system design in sections 4A and 4B. We are starting at **Phase 0**. Inspect my current repo (`scrapers/sebi_scraper.py`, `scrapers/circular_fetcher.py`, `.env`), then propose a plan for Phase 0: the new package layout, how you'll move existing code without breaking it, and the migrations you'd write. Do not write code until I approve the plan.
