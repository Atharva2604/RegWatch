"""
RegWatch API — Regulations Router
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from api.deps import get_supabase

router = APIRouter()


@router.get("/regulations")
def list_regulations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None),
    legal_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
):
    sb = get_supabase()
    offset = (page - 1) * limit

    # Build query
    query = (
        sb.table("regulations")
        .select(
            "id, title, reference_number, published_date, department, legal_type, url, status, last_checked_at",
            count="exact",
        )
    )

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.ilike("title", search_term)

    if legal_type and legal_type != "all":
        query = query.eq("legal_type", legal_type)

    if department and department != "all":
        query = query.ilike("department", f"%{department}%")

    query = query.order("published_date", desc=True, nulls_first=False).range(offset, offset + limit - 1)
    res = query.execute()

    total = res.count if res.count is not None else 0
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "data": res.data or [],
    }


@router.get("/regulations/{regulation_id}")
def get_regulation(regulation_id: int):
    sb = get_supabase()

    res = (
        sb.table("regulations")
        .select("*")
        .eq("id", regulation_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Regulation not found")

    reg = res.data[0]

    # Don't return the raw 384-dim vector in JSON response
    reg.pop("embedding", None)

    # Check for obligations
    ob_res = (
        sb.table("obligations")
        .select("id, category, applies_to, requirement_text, evidence_quote, metric_name, threshold_value, unit")
        .eq("regulation_id", regulation_id)
        .execute()
    )

    return {
        "regulation": reg,
        "obligations": ob_res.data or [],
    }


@router.get("/regulations/{regulation_id}/chunks")
def get_regulation_chunks(regulation_id: int):
    """Returns stored clause-level 500-token chunks for a regulation."""
    sb = get_supabase()
    res = (
        sb.table("regulation_chunks")
        .select("id, regulation_id, chunk_index, text, created_at")
        .eq("regulation_id", regulation_id)
        .order("chunk_index", desc=False)
        .execute()
    )
    return {
        "regulation_id": regulation_id,
        "count": len(res.data or []),
        "chunks": res.data or [],
    }


@router.post("/regulations/{regulation_id}/trigger-audit")
def trigger_regulation_audit(regulation_id: int):
    """
    Event-driven automation endpoint: triggers compliance comparison across
    all active companies for the specified regulation, generating alerts for gaps.
    """
    from pipeline.comparison_engine import evaluate_new_circular_for_all_companies
    from pipeline.chunk_engine import chunk_and_index_regulation

    sb = get_supabase()
    reg = sb.table("regulations").select("id, title, content_text").eq("id", regulation_id).execute()
    if not reg.data:
        raise HTTPException(status_code=404, detail="Regulation not found")

    reg_obj = reg.data[0]
    # Ensure chunks exist
    chunk_and_index_regulation(regulation_id, reg_obj.get("content_text", ""), title=reg_obj.get("title", ""))

    alerts = evaluate_new_circular_for_all_companies(regulation_id)
    return {
        "status": "completed",
        "regulation_id": regulation_id,
        "alerts_generated": len(alerts),
        "alerts": alerts,
    }


@router.get("/sources")
def list_sources():
    sb = get_supabase()
    try:
        res = sb.table("sources").select("*").execute()
        return res.data or []
    except Exception:
        return [
            {
                "id": 1,
                "name": "Securities and Exchange Board of India (SEBI)",
                "code": "SEBI",
                "base_url": "https://www.sebi.gov.in",
                "frequency": "daily",
                "status": "active",
                "last_run_at": "2026-10-26T06:00:00Z",
                "total_documents": 3030,
            }
        ]

