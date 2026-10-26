"""
RegWatch API — Audit Events & Activity Log Router
Enforces multi-tenant isolation on compliance audit trails.
"""
from typing import Optional
from fastapi import APIRouter, Query, Depends
from api.deps import get_supabase, get_current_user, verify_tenant_access, AuthUser

router = APIRouter()


@router.get("/audit-events")
def list_audit_events(
    company_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    auth_user: AuthUser = Depends(get_current_user),
):
    verified_company_id = verify_tenant_access(auth_user, company_id)
    sb = get_supabase()

    # Query audit_events table
    res = (
        sb.table("audit_events")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    all_events = res.data or []

    # Filter events for this tenant (or global events)
    filtered_events = []
    for ev in all_events:
        payload = ev.get("payload") or {}
        p_comp = payload.get("company_id")
        if p_comp is None or p_comp == verified_company_id or auth_user.role == "admin":
            filtered_events.append(ev)

    # If events list is sparse, synthesize timeline from compliance_checks & risk_scores
    if len(filtered_events) < 5:
        checks = (
            sb.table("compliance_checks")
            .select("id, verdict, created_at, company_policy_id, explanation")
            .eq("company_id", verified_company_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
            .data
            or []
        )
        for c in checks:
            filtered_events.append({
                "id": f"evt-{c['id']}",
                "entity": "compliance_check",
                "entity_id": str(c["id"]),
                "event_type": "check_evaluated",
                "payload": {
                    "verdict": c.get("verdict"),
                    "policy_id": c.get("company_policy_id"),
                    "summary": (c.get("explanation") or "")[:120],
                    "company_id": verified_company_id,
                },
                "created_at": c.get("created_at"),
            })

    # Sort all by created_at desc
    filtered_events.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    return {
        "company_id": verified_company_id,
        "count": len(filtered_events),
        "events": filtered_events[:limit],
    }
