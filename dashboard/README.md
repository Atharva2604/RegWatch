# RegWatch dashboard

Read-only regulatory operations console for the RegWatch proof of concept.
It is built with FastAPI, Jinja2 and plain CSS, reuses the existing
`regwatch.settings` configuration, and reads the live Supabase schema directly
from the server process. The browser never receives the Supabase key.

## Run

From the repository root:

```powershell
python -m dashboard.app
```

Open <http://127.0.0.1:8000>.

Requirements: `fastapi`, `uvicorn` and `jinja2`. They are part of the
`advanced` optional dependency group:

```powershell
pip install -e ".[advanced]"
```

Supabase credentials must already be configured for the pipeline in `.env`
(`SUPABASE_URL`, `SUPABASE_KEY`). If they are missing or the database is
unreachable, every page shows an explicit error state instead of sample data.

## What it shows

- **Overview** — document, snapshot, change, compliance and risk counts;
  queue backlog; snapshot coverage; alert-delivery status; recent activity.
- **Documents** — server-side search, legal-type and snapshot filters, sortable
  columns, pagination, source links and change-history links.
- **Change review** — stored versions and hashes. A line diff is computed when
  a document has two readable versions. No change summary is invented.
- **Compliance & risk** — persisted verdicts with method and confidence, the
  risk register, and alert-delivery status. Assessment provenance is explained
  on the page.

## Boundaries

- All queries are `SELECT` statements. The dashboard does not write to Supabase.
- No Groq key is needed; assessment rows produced earlier are displayed as
  stored, with their method label.
- Notification delivery is not implemented (`FakeNotifier`); the UI says so.
- The current schema stores no review/approval status, so none is displayed.
- `regulation_versions` stores one version per document so far, so the change
  page reports zero detected revisions rather than fabricating activity.
- Only the SEBI ingestion source is populated; regulator labels are derived
  from source URLs because `regulations.source_id` is unwritten.
