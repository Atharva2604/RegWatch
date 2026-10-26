"""Read-only Supabase access for the RegWatch dashboard.

Every query in this module is a SELECT. The dashboard never writes to the
pipeline tables, so it can be demonstrated safely against a live database.
"""

from __future__ import annotations

import difflib
import logging
import math
import re
from collections import Counter
from datetime import datetime
from functools import lru_cache
from typing import Any, Callable
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from regwatch.settings import get_settings

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

PAGE_SIZE = 25
CHECKS_PAGE_SIZE = 20

LEGAL_TYPES = {
    "act": "Act",
    "rule": "Rule",
    "regulation": "Regulation",
    "circular": "Circular",
    "master_circular": "Master circular",
    "guideline": "Guideline",
    "general_order": "General order",
    "other": "Other",
}
DOC_SORTS = {
    "first_seen_at": "First seen",
    "last_checked_at": "Last checked",
    "title": "Document",
    "legal_type": "Legal type",
    "published_date": "Published",
}
VERDICTS = ("compliant", "non_compliant", "needs_review", "no_policy")
VERDICT_LABELS = {
    "compliant": "Compliant",
    "non_compliant": "Non-compliant",
    "needs_review": "Needs review",
    "no_policy": "No policy",
}
LEVEL_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}
METHOD_LABELS = {
    "rule_based": "Rule-based",
    "llm_judge": "LLM judge",
    "groq_llm_vector": "LLM-assisted (Groq)",
}
SNAPSHOT_LABELS = {
    "captured": "Snapshot captured",
    "pending": "Awaiting snapshot",
}

DOC_COLUMNS = (
    "id,title,url,legal_type,published_date,reference_number,department,"
    "first_seen_at,last_checked_at,last_changed_at,status,current_version_id"
)
CHECK_COLUMNS = (
    "id,company_id,company_policy_id,obligation_id,verdict,confidence,"
    "explanation,method,triggered_by,inputs_hash,created_at"
)
RISK_COLUMNS = (
    "id,company_id,severity,urgency,scope,level,category,reason,created_at"
)


class DashboardUnavailable(RuntimeError):
    """Raised when the dashboard cannot read from its data source."""


@lru_cache(maxsize=1)
def _client() -> Any:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise DashboardUnavailable(
            "Supabase credentials are not configured. Add SUPABASE_URL and "
            "SUPABASE_KEY to the repository .env file, then restart the dashboard."
        )
    try:
        from supabase import create_client

        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:  # pragma: no cover - depends on local configuration
        logger.exception("Could not create the Supabase client")
        raise DashboardUnavailable(
            "The Supabase client could not be initialised. Check SUPABASE_URL "
            "and SUPABASE_KEY in .env."
        ) from exc


def _read(query: Any) -> Any:
    """Execute a PostgREST query and translate failures into a dashboard error."""
    try:
        return query.execute()
    except Exception as exc:
        logger.exception("Supabase read failed")
        detail = re.sub(r"\s+", " ", str(exc)).strip()[:220]
        raise DashboardUnavailable(
            f"Supabase returned an error while reading dashboard data. {detail}"
        ) from exc


def _count(client: Any, table: str, apply: Callable[[Any], Any] | None = None) -> int:
    query = client.table(table).select("id", count="exact").limit(1)
    if apply is not None:
        query = apply(query)
    return _read(query).count or 0


def _companies(client: Any, ids: list[int] | None = None) -> dict[int, str]:
    query = client.table("companies").select("id,name")
    if ids:
        query = query.in_("id", sorted({i for i in ids if i is not None}))
    rows = _read(query).data or []
    return {row["id"]: row.get("name") or f"Company {row['id']}" for row in rows}


def _docs_by_id(client: Any, ids: list[int]) -> dict[int, dict[str, Any]]:
    clean = sorted({i for i in ids if i is not None})
    if not clean:
        return {}
    rows = _read(
        client.table("regulations")
        .select("id,title,url,legal_type,content_hash")
        .in_("id", clean)
    ).data or []
    return {row["id"]: row for row in rows}


def _policies_by_id(client: Any, ids: list[int]) -> dict[int, dict[str, Any]]:
    clean = sorted({i for i in ids if i is not None})
    if not clean:
        return {}
    rows = _read(
        client.table("company_policies")
        .select("id,title,category,company_id,metric_name,value,unit")
        .in_("id", clean)
    ).data or []
    return {row["id"]: row for row in rows}


def _obligations_by_id(client: Any, ids: list[int]) -> dict[int, dict[str, Any]]:
    clean = sorted({i for i in ids if i is not None})
    if not clean:
        return {}
    rows = _read(
        client.table("obligations")
        .select("id,category,requirement_text,evidence_quote")
        .in_("id", clean)
    ).data or []
    return {row["id"]: row for row in rows}


# --------------------------------------------------------------------------- #
# Formatting helpers (also registered as Jinja filters)
# --------------------------------------------------------------------------- #


def fmt_num(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    return parsed.astimezone(IST)


def fmt_dt(value: Any) -> str:
    parsed = _parse_dt(value)
    return parsed.strftime("%d %b %Y, %H:%M IST") if parsed else "—"


def fmt_date(value: Any) -> str:
    parsed = _parse_dt(value)
    if parsed:
        return parsed.strftime("%d %b %Y")
    return str(value) if value else "—"


def short_hash(value: Any, length: int = 12) -> str:
    text = str(value or "")
    if not text:
        return "—"
    return text if len(text) <= length else f"{text[:length]}…"


def pct(part: Any, total: Any) -> int:
    try:
        total_int = int(total)
        return round(int(part) * 100 / total_int) if total_int else 0
    except (TypeError, ValueError):
        return 0


def fmt_conf(value: Any) -> str:
    """Format a stored model confidence as a percentage (not an accuracy claim)."""
    try:
        return f"{round(float(value) * 100)}%"
    except (TypeError, ValueError):
        return "—"


def regulator_for(url: str) -> str:
    """Derive the regulator label from the source URL host (no stored mapping)."""
    host = (urlparse(str(url or "")).hostname or "").lower()
    known = (
        ("sebi.gov.in", "SEBI"),
        ("rbi.org.in", "RBI"),
        ("irdai.gov.in", "IRDAI"),
        ("nseindia.com", "NSE"),
        ("bseindia.com", "BSE"),
    )
    for suffix, name in known:
        if host == suffix or host.endswith(f".{suffix}"):
            return name
    return host.removeprefix("www.") or "Unknown source"


def sanitize_search(term: str) -> str:
    """Strip characters that break PostgREST `or=(...)` filter syntax."""
    cleaned = re.sub(r'[,()%"\'\\]', " ", str(term or ""))
    return re.sub(r"\s+", " ", cleaned).strip()[:120]


def text_diff(old_text: str | None, new_text: str | None, max_lines: int = 160) -> dict[str, Any] | None:
    """Line-based comparison of two snapshots. Returns None when not comparable."""
    if not old_text or not new_text:
        return None
    if len(old_text) > 400_000 or len(new_text) > 400_000:
        return {"too_large": True}
    lines = list(
        difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile="previous version",
            tofile="current version",
            lineterm="",
            n=2,
        )
    )
    added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
    return {
        "added": added,
        "removed": removed,
        "lines": lines[:max_lines],
        "truncated": len(lines) > max_lines,
        "identical": not added and not removed,
    }


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #


def get_overview() -> dict[str, Any]:
    client = _client()

    documents = _count(client, "regulations")
    with_snapshot = _count(
        client, "regulations", lambda q: q.not_.is_("current_version_id", "null")
    )
    snapshots = _count(client, "regulation_versions")
    changes = _count(client, "regulation_versions", lambda q: q.gt("version_no", 1))

    verdict_counts = {
        verdict: _count(
            client, "compliance_checks", lambda q, v=verdict: q.eq("verdict", v)
        )
        for verdict in VERDICTS
    }
    checks_total = sum(verdict_counts.values())

    jobs_pending = _count(client, "jobs", lambda q: q.eq("status", "pending"))
    jobs_failed = _count(client, "jobs", lambda q: q.eq("status", "failed"))
    alerts = _count(client, "alerts")
    try:
        ingestion_runs: int | None = _count(client, "ingestion_runs")
    except DashboardUnavailable:
        ingestion_runs = None

    risk_total = _count(client, "risk_scores")
    recent_risks = _read(
        client.table("risk_scores")
        .select("id,company_id,level,category,created_at")
        .order("created_at", desc=True)
        .limit(4)
    ).data or []

    recent_versions = (
        _read(
            client.table("regulation_versions")
            .select("id,regulation_id,version_no,created_at,raw_sha256")
            .order("created_at", desc=True)
            .limit(8)
        ).data
        or []
    )
    docs = _docs_by_id(client, [row.get("regulation_id") for row in recent_versions])
    for version in recent_versions:
        doc = docs.get(version.get("regulation_id")) or {}
        version["title"] = doc.get("title") or "Document unavailable"
        version["url"] = doc.get("url")
        version["regulator"] = regulator_for(doc.get("url"))

    recent_checks = (
        _read(
            client.table("compliance_checks")
            .select("id,verdict,company_id,explanation,method,created_at")
            .order("created_at", desc=True)
            .limit(4)
        ).data
        or []
    )
    companies = _companies(
        client, [row.get("company_id") for row in recent_checks]
    )
    for check in recent_checks:
        check["company_name"] = companies.get(check.get("company_id"), "Unknown company")

    latest = (
        _read(
            client.table("regulations")
            .select("last_checked_at")
            .not_.is_("last_checked_at", "null")
            .order("last_checked_at", desc=True)
            .limit(1)
        ).data
        or []
    )

    return {
        "documents": documents,
        "with_snapshot": with_snapshot,
        "snapshots": snapshots,
        "changes": changes,
        "checks_total": checks_total,
        "verdict_counts": verdict_counts,
        "jobs_pending": jobs_pending,
        "jobs_failed": jobs_failed,
        "alerts": alerts,
        "ingestion_runs": ingestion_runs,
        "risk_total": risk_total,
        "recent_risks": recent_risks,
        "recent_versions": recent_versions,
        "recent_checks": recent_checks,
        "last_checked_at": latest[0].get("last_checked_at") if latest else None,
    }


def search_documents(
    *,
    q: str = "",
    legal_type: str = "",
    snapshot: str = "",
    sort: str = "first_seen_at",
    direction: str = "desc",
    page: int = 1,
) -> dict[str, Any]:
    client = _client()

    term = sanitize_search(q)
    legal_type = legal_type if legal_type in LEGAL_TYPES else ""
    snapshot = snapshot if snapshot in SNAPSHOT_LABELS else ""
    sort = sort if sort in DOC_SORTS else "first_seen_at"
    direction = "asc" if direction == "asc" else "desc"
    page = max(1, page)

    def filtered(columns: str) -> Any:
        query = client.table("regulations").select(columns, count="exact")
        if term:
            pattern = f"%{term}%"
            query = query.or_(
                f"title.ilike.{pattern},"
                f"reference_number.ilike.{pattern},"
                f"department.ilike.{pattern}"
            )
        if legal_type:
            query = query.eq("legal_type", legal_type)
        if snapshot == "captured":
            query = query.not_.is_("current_version_id", "null")
        elif snapshot == "pending":
            query = query.is_("current_version_id", "null")
        return query

    total = _read(filtered("id").limit(1)).count or 0
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(page, pages)
    result = _read(
        filtered(DOC_COLUMNS)
        .order(sort, desc=direction == "desc")
        .range((page - 1) * PAGE_SIZE, page * PAGE_SIZE - 1)
    )

    rows = result.data or []
    for row in rows:
        row["regulator"] = regulator_for(row.get("url", ""))
        row["has_snapshot"] = bool(row.get("current_version_id"))

    filters = {
        "q": term,
        "type": legal_type,
        "snapshot": snapshot,
        "sort": sort,
        "dir": direction,
    }
    return {
        "rows": rows,
        "total": total,
        "page": page,
        "pages": pages,
        "filters": filters,
        "legal_types": LEGAL_TYPES,
        "snapshot_labels": SNAPSHOT_LABELS,
        "has_filters": bool(term or legal_type or snapshot),
    }


def get_change_review(regulation_id: int | None = None) -> dict[str, Any]:
    client = _client()

    changes = _count(client, "regulation_versions", lambda q: q.gt("version_no", 1))
    snapshots = _count(client, "regulation_versions")
    recent_versions = (
        _read(
            client.table("regulation_versions")
            .select("id,regulation_id,version_no,created_at,raw_sha256,diff_summary")
            .order("created_at", desc=True)
            .limit(12)
        ).data
        or []
    )
    docs = _docs_by_id(client, [row.get("regulation_id") for row in recent_versions])
    for version in recent_versions:
        doc = docs.get(version.get("regulation_id")) or {}
        version["title"] = doc.get("title") or "Document unavailable"
        version["url"] = doc.get("url")
        version["has_diff_summary"] = bool(version.get("diff_summary"))

    detail: dict[str, Any] | None = None
    if regulation_id is not None:
        found = (
            _read(
                client.table("regulations")
                .select(
                    "id,title,url,legal_type,first_seen_at,last_checked_at,"
                    "last_changed_at,content_hash,current_version_id"
                )
                .eq("id", regulation_id)
                .limit(1)
            ).data
            or []
        )
        if not found:
            detail = {"missing": True}
        else:
            doc = found[0]
            doc["regulator"] = regulator_for(doc.get("url", ""))
            versions = (
                _read(
                    client.table("regulation_versions")
                    .select("id,version_no,content_text,raw_sha256,diff_summary,created_at")
                    .eq("regulation_id", regulation_id)
                    .order("version_no", desc=True)
                    .limit(25)
                ).data
                or []
            )
            diff = None
            if len(versions) >= 2:
                diff = text_diff(
                    versions[1].get("content_text"), versions[0].get("content_text")
                )
            for version in versions:
                version["chars"] = len(version.pop("content_text", "") or "")
            detail = {
                "doc": doc,
                "versions": versions,
                "diff": diff,
                "review_status_available": False,
            }

    latest_snapshot = recent_versions[0]["created_at"] if recent_versions else None
    return {
        "changes": changes,
        "snapshots": snapshots,
        "recent_versions": recent_versions,
        "latest_snapshot": latest_snapshot,
        "detail": detail,
    }


def get_compliance(
    *,
    verdict: str = "",
    company: int | None = None,
    page: int = 1,
) -> dict[str, Any]:
    client = _client()

    verdict = verdict if verdict in VERDICTS else ""
    page = max(1, page)

    verdict_counts = {
        item: _count(
            client, "compliance_checks", lambda q, v=item: q.eq("verdict", v)
        )
        for item in VERDICTS
    }
    checks_total = sum(verdict_counts.values())

    def filtered(columns: str) -> Any:
        query = client.table("compliance_checks").select(columns, count="exact")
        if verdict:
            query = query.eq("verdict", verdict)
        if company is not None:
            query = query.eq("company_id", company)
        return query

    total = _read(filtered("id").limit(1)).count or 0
    pages = max(1, math.ceil(total / CHECKS_PAGE_SIZE))
    page = min(page, pages)
    result = _read(
        filtered(CHECK_COLUMNS)
        .order("created_at", desc=True)
        .range((page - 1) * CHECKS_PAGE_SIZE, page * CHECKS_PAGE_SIZE - 1)
    )
    rows = result.data or []

    company_names = _companies(client)
    policies = _policies_by_id(
        client, [row.get("company_policy_id") for row in rows]
    )
    obligations = _obligations_by_id(
        client, [row.get("obligation_id") for row in rows]
    )
    for row in rows:
        row["company_name"] = company_names.get(
            row.get("company_id"), f"Company {row.get('company_id')}"
        )
        policy = policies.get(row.get("company_policy_id")) or {}
        row["policy_title"] = policy.get("title") or policy.get("category")
        row["policy_category"] = policy.get("category")
        obligation = obligations.get(row.get("obligation_id")) or {}
        row["obligation_text"] = obligation.get("requirement_text")

    risks = (
        _read(
            client.table("risk_scores")
            .select(RISK_COLUMNS)
            .order("created_at", desc=True)
            .limit(100)
        ).data
        or []
    )
    risk_total = _count(client, "risk_scores")
    for risk in risks:
        risk["company_name"] = company_names.get(
            risk.get("company_id"), f"Company {risk.get('company_id')}"
        )

    alerts = (
        _read(
            client.table("alerts")
            .select("id,company_id,channel,status,acknowledged_at,dedupe_key,created_at")
            .order("created_at", desc=True)
            .limit(20)
        ).data
        or []
    )
    alert_total = _count(client, "alerts")
    for alert in alerts:
        alert["company_name"] = company_names.get(
            alert.get("company_id"), f"Company {alert.get('company_id')}"
        )

    return {
        "rows": rows,
        "total": total,
        "page": page,
        "pages": pages,
        "verdict": verdict,
        "company": company,
        "verdict_counts": verdict_counts,
        "checks_total": checks_total,
        "companies": company_names,
        "has_obligations": any(row.get("obligation_text") for row in rows),
        "risks": risks,
        "risk_total": risk_total,
        "risk_capped": risk_total > len(risks),
        "alerts": alerts,
        "alert_total": alert_total,
    }
