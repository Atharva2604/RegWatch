# RegWatch dashboard

Read-only regulatory operations console for the RegWatch proof of concept.
It is built with FastAPI, Jinja2 and plain CSS, reuses the existing
`regwatch.settings` configuration, and reads the live Supabase schema directly
from the server process. The browser never receives the Supabase key.

## Run

Two front ends share the same read-only data layer (`dashboard/data.py`).

**FastAPI + Jinja2** (primary):

```powershell
python -m dashboard.app
```

Open <http://127.0.0.1:8000>.

**Streamlit** (for Streamlit Community Cloud or quick local viewing):

```powershell
streamlit run dashboard/streamlit_app.py
```

To deploy the Streamlit version on Streamlit Community Cloud, point the app at
this repository and set the main file to `dashboard/streamlit_app.py`. Paste the
credentials into the app's **Secrets**:

```toml
SUPABASE_URL = "https://<project>.supabase.co"
SUPABASE_KEY = "<service or anon key>"
```

Streamlit injects secrets as environment variables, which `regwatch.settings`
reads automatically. The app is public by default — use the anon key with
read-only row-level security if the URL is shared outside the team.

Requirements: `fastapi`, `uvicorn` and `jinja2`. They are part of the
`advanced` optional dependency group:

```powershell
pip install -e ".[advanced]"
```

Supabase credentials must already be configured for the pipeline in `.env`
(`SUPABASE_URL`, `SUPABASE_KEY`). If they are missing or the database is
unreachable, every page shows an explicit error state instead of sample data.

## What it shows

- **Overview** — KPI tiles (documents, snapshots, changes, non-compliant checks,
  risks), snapshot coverage, verdict distribution bars and a latest-activity rail.
- **Documents** — server-side search, legal-type and snapshot filters, sort
  controls, pagination, source links and change-history links.
- **Change review** — stored versions and hashes. A line diff is computed when
  a document has two readable versions.
- **Compliance & risk** — verdict filters with counts, persisted verdicts with
  method and confidence, the risk register, and the alert log.

## Boundaries

- All queries are `SELECT` statements. The dashboard does not write to Supabase.
- No Groq key is needed; assessment rows produced earlier are displayed as
  stored, with their method label.
- Notification delivery is not implemented (`FakeNotifier`); the alerts panel
  shows the delivery channel as not configured.
- The current schema stores no review/approval status, so none is displayed.
- `regulation_versions` stores one version per document so far, so the change
  page reports zero detected revisions rather than fabricating activity.
- Only the SEBI ingestion source is populated; regulator labels are derived
  from source URLs because `regulations.source_id` is unwritten.
