"""RegWatch dashboard — simple, gamified, layman-friendly regulatory operations.

Launch: python -m dashboard.app
Open: http://127.0.0.1:8000
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, Query, Request  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402

from dashboard import data  # noqa: E402

logger = logging.getLogger("regwatch.dashboard")
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="RegWatch",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters.update(
    num=data.fmt_num,
    dt=data.fmt_dt,
    date=data.fmt_date,
    short_hash=data.short_hash,
    pct=data.pct,
    conf=data.fmt_conf,
)
templates.env.globals.update(
    verdict_labels=data.VERDICT_LABELS,
    level_labels=data.LEVEL_LABELS,
    method_labels=data.METHOD_LABELS,
    qs=data.qs,
    pct=data.pct,
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


def _render(request: Request, template: str, **context):
    context.setdefault("active", "")
    context.setdefault("db_ok", True)
    context["rendered_at"] = datetime.now(data.IST)
    return templates.TemplateResponse(request, template, context)


@app.exception_handler(data.DashboardUnavailable)
async def supabase_unavailable(request: Request, exc: data.DashboardUnavailable):
    logger.warning("Dashboard data source unavailable: %s", exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {"active": "", "db_ok": False, "title": "Data source unavailable", "message": str(exc)},
        status_code=503,
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.exception("Dashboard request failed: %s", exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {"active": "", "db_ok": False, "title": "Dashboard error", "message": "An unexpected error occurred."},
        status_code=500,
    )


@app.get("/", response_class=HTMLResponse)
def overview(request: Request):
    ctx = data.get_overview()
    return _render(request, "index.html", active="overview", **ctx)


@app.get("/documents", response_class=HTMLResponse)
def documents(
    request: Request,
    q: str = "",
    legal_type: str = Query("", alias="type"),
    snapshot: str = "",
    sort: str = "last_seen",
    direction: str = Query("desc", alias="dir"),
    page: str = "1",
):
    current_page = max(1, int(page) if str(page).isdigit() else 1)
    ctx = data.search_documents(
        q=q if q else "",
        legal_type=legal_type if legal_type else "",
        snapshot=snapshot if snapshot else "",
        sort=sort,
        direction=direction,
        page=current_page,
    )
    return _render(request, "documents.html", active="documents", **ctx)


@app.get("/changes", response_class=HTMLResponse)
def changes(request: Request, regulation: str = ""):
    ctx = data.get_change_review(int(regulation) if regulation.isdigit() else None)
    return _render(request, "changes.html", active="changes", **ctx)


@app.get("/compliance", response_class=HTMLResponse)
def compliance(
    request: Request,
    verdict: str = "",
    company: str = "",
    page: str = "1",
):
    company_id = int(company) if company.isdigit() and int(company) > 0 else None
    ctx = data.get_compliance(verdict=verdict, company=company_id, page=max(1, int(page)))
    return _render(request, "compliance.html", active="compliance", **ctx)


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    print("RegWatch dashboard: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)