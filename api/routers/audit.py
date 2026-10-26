"""
RegWatch API — Baseline Onboarding Audit Router
Enforces multi-tenant authorization for regulatory baseline audits.
"""
import threading
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, BackgroundTasks, Depends
from pydantic import BaseModel
from api.deps import get_supabase, get_current_user, verify_tenant_access, require_role, AuthUser
from pipeline.baseline_audit import run_baseline_audit

router = APIRouter()

_audit_state = {
    "is_running": False,
    "started_at": None,
    "completed_at": None,
    "total": 0,
    "processed": 0,
    "status": "idle",
}


class RunAuditRequest(BaseModel):
    limit: Optional[int] = 5
    company_id: Optional[int] = None


def _background_audit_runner(company_id: int, limit: Optional[int]):
    global _audit_state
    _audit_state["is_running"] = True
    _audit_state["status"] = "running"
    _audit_state["started_at"] = datetime.now(timezone.utc).isoformat()
    try:
        run_baseline_audit(company_id=company_id, limit=limit)
        _audit_state["status"] = "completed"
    except Exception as e:
        _audit_state["status"] = f"error: {str(e)}"
    finally:
        _audit_state["is_running"] = False
        _audit_state["completed_at"] = datetime.now(timezone.utc).isoformat()


@router.get("/audit/status")
def get_audit_status(
    company_id: Optional[int] = Query(None),
    auth_user: AuthUser = Depends(get_current_user),
):
    verified_company_id = verify_tenant_access(auth_user, company_id)
    sb = get_supabase()

    # Total policies
    p_res = sb.table("company_policies").select("id", count="exact").eq("company_id", verified_company_id).execute()
    total_policies = p_res.count if p_res.count is not None else 52

    # Checks
    checks_res = (
        sb.table("compliance_checks")
        .select("id, company_policy_id, verdict, confidence, explanation, created_at")
        .eq("company_id", verified_company_id)
        .order("created_at", desc=True)
        .execute()
    )
    checks = checks_res.data or []
    total_checks = len(checks)
    compliant = sum(1 for c in checks if c.get("verdict") in ["compliant", "exempted"])
    non_compliant = sum(1 for c in checks if c.get("verdict") == "non_compliant")
    health_score = round((compliant / total_checks * 100), 1) if total_checks > 0 else 100.0

    # Risk scores
    risks_res = (
        sb.table("risk_scores")
        .select("id, level, severity, category, reason, created_at")
        .eq("company_id", verified_company_id)
        .order("created_at", desc=True)
        .execute()
    )
    risks = risks_res.data or []
    high_risks = sum(1 for r in risks if r.get("level") == "high" or (r.get("severity") or 0) >= 7)
    med_risks = sum(1 for r in risks if r.get("level") == "medium" or (4 <= (r.get("severity") or 0) < 7))
    low_risks = sum(1 for r in risks if r.get("level") == "low" or (r.get("severity") or 0) < 4)

    # Policy mapping for non-compliant gaps
    gap_checks = [c for c in checks if c.get("verdict") == "non_compliant"]
    policy_ids = [c["company_policy_id"] for c in gap_checks if c.get("company_policy_id")]
    policy_map = {}
    if policy_ids:
        p_data = (
            sb.table("company_policies")
            .select("id, title, category, metric_name, value, unit")
            .in_("id", policy_ids)
            .execute()
            .data
            or []
        )
        for p in p_data:
            policy_map[p["id"]] = p

    gaps = []
    for idx, c in enumerate(gap_checks):
        pid = c.get("company_policy_id")
        p_info = policy_map.get(pid, {})
        risk_info = risks[idx] if idx < len(risks) else {}
        gaps.append({
            "check_id": c["id"],
            "policy_id": pid,
            "policy_title": p_info.get("title", f"Policy #{pid}"),
            "category": p_info.get("category", "General"),
            "explanation": c.get("explanation"),
            "severity": risk_info.get("level", "high"),
            "confidence": float(c.get("confidence") or 0.85),
            "created_at": c.get("created_at"),
        })

    last_run_at = checks[0]["created_at"] if checks else None

    # Company name
    comp_name = "FinCorp Securities Ltd"
    try:
        c_res = sb.table("companies").select("name").eq("id", verified_company_id).execute()
        if c_res.data:
            comp_name = c_res.data[0].get("name", comp_name)
    except Exception:
        pass

    return {
        "is_running": _audit_state["is_running"],
        "status": "completed" if not _audit_state["is_running"] else "running",
        "company_id": verified_company_id,
        "company_name": comp_name,
        "total_policies": total_policies,
        "audited_count": total_checks,
        "compliant_count": compliant,
        "gap_count": non_compliant,
        "health_score": health_score,
        "risk_breakdown": {
            "high": high_risks,
            "medium": med_risks,
            "low": low_risks,
        },
        "gaps": gaps,
        "last_run_at": last_run_at,
    }


@router.post("/audit/baseline")
def trigger_baseline_audit(
    req: RunAuditRequest,
    background_tasks: BackgroundTasks,
    auth_user: AuthUser = Depends(require_role(["officer", "admin"])),
):
    global _audit_state
    if _audit_state["is_running"]:
        return {"status": "already_running", "message": "An audit is currently running."}

    verified_company_id = verify_tenant_access(auth_user, req.company_id)
    limit = req.limit or 5

    t = threading.Thread(target=_background_audit_runner, args=(verified_company_id, limit), daemon=True)
    t.start()

    return {
        "status": "started",
        "company_id": verified_company_id,
        "limit": limit,
        "message": f"Baseline audit started for {limit} policies. Polling /audit/status for progress.",
    }
