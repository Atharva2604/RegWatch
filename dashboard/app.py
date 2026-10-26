"""RegWatch dashboard web application.

Launch from the repository root:

    python -m dashboard.app

The app is deliberately read-only and talks to Supabase only from the server.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

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
    title="RegWatch Dashboard",
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


def _to_int(value: str, default: int | None = None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _url(path: str, params: dict) -> str:
    clean = {key: value for key, value in params.items() if value not in (None, "", 0)}
    query = urlencode(clean)
    return f"{path}?{query}" if query else path


def _documents_url(filters: dict, page: int = 1, **overrides) -> str:
    params = {
        "q": filters["q"],
        "type": filters["type"],
        "snapshot": filters["snapshot"],
        "sort": filters["sort"],
        "dir": filters["dir"],
        "page": page if page > 1 else None,
    }
    params.update(overrides)
    return _url("/documents", params)


def _compliance_url(
    verdict: str = "", company: int | None = None, page: int = 1
) -> str:
    return _url(
        "/compliance",
        {
            "verdict": verdict,
            "company": company,
            "page": page if page > 1 else None,
        },
    )


@app.get("/", response_class=HTMLResponse)
def overview(request: Request):
    context = data.get_overview()
    verdict_links = {
        "all": "/compliance",
        **{
            key: _compliance_url(verdict=key)
            for key in data.VERDICTS
        },
    }
    return _render(
        request,
        "overview.html",
        active="overview",
        verdict_links=verdict_links,
        **context,
    )


@app.get("/documents", response_class=HTMLResponse)
def documents(
    request: Request,
    q: str = "",
    legal_type: str = Query("", alias="type"),
    snapshot: str = "",
    sort: str = "last_checked_at",
    direction: str = Query("desc", alias="dir"),
    page: str = "1",
):
    current_page = _to_int(page, 1) or 1
    context = data.search_documents(
        q=q,
        legal_type=legal_type,
        snapshot=snapshot,
        sort=sort,
        direction=direction,
        page=current_page,
    )
    filters = context["filters"]
    sort_links = {}
    for column in data.DOC_SORTS:
        target = (
            "desc"
            if filters["sort"] == column and filters["dir"] == "asc"
            else "asc"
        )
        sort_links[column] = _documents_url(
            filters, page=context["page"], sort=column, dir=target
        )

    return _render(
        request,
        "documents.html",
        active="documents",
        sort_links=sort_links,
        prev_url=(
            _documents_url(filters, page=context["page"] - 1)
            if context["page"] > 1
            else None
        ),
        next_url=(
            _documents_url(filters, page=context["page"] + 1)
            if context["page"] < context["pages"]
            else None
        ),
        clear_url="/documents",
        sort_options=data.DOC_SORTS,
        **context,
    )


@app.get("/changes", response_class=HTMLResponse)
def changes(request: Request, regulation: str = ""):
    context = data.get_change_review(_to_int(regulation))
    return _render(request, "changes.html", active="changes", **context)


@app.get("/compliance", response_class=HTMLResponse)
def compliance(
    request: Request,
    verdict: str = "",
    company: str = "",
    page: str = "1",
):
    company_id = _to_int(company)
    context = data.get_compliance(
        verdict=verdict, company=company_id, page=_to_int(page, 1) or 1
    )
    verdict_links = {
        "all": _compliance_url(company=company_id),
        **{
            key: _compliance_url(verdict=key, company=company_id)
            for key in data.VERDICTS
        },
    }
    return _render(
        request,
        "compliance.html",
        active="compliance",
        verdict_links=verdict_links,
        company_clear_url=_compliance_url(verdict=context["verdict"]),
        prev_url=(
            _compliance_url(
                verdict=context["verdict"],
                company=company_id,
                page=context["page"] - 1,
            )
            if context["page"] > 1
            else None
        ),
        next_url=(
            _compliance_url(
                verdict=context["verdict"],
                company=company_id,
                page=context["page"] + 1,
            )
            if context["page"] < context["pages"]
            else None
        ),
        **context,
    )


@app.exception_handler(data.DashboardUnavailable)
async def supabase_unavailable(request: Request, exc: data.DashboardUnavailable):
    logger.warning("Dashboard data source unavailable: %s", exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "active": "",
            "db_ok": False,
            "title": "Data source unavailable",
            "message": str(exc),
            "hint": (
                "Check the Supabase URL and key in .env, then verify connectivity "
                "with the command below. The dashboard never substitutes demo "
                "records for production data."
            ),
        },
        status_code=503,
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.exception("Dashboard request failed: %s", exc)
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "active": "",
            "db_ok": False,
            "title": "Dashboard error",
            "message": "The dashboard hit an unexpected error while rendering this page.",
            "hint": "Check the server log for the traceback, then reload.",
        },
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    print("RegWatch dashboard: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
