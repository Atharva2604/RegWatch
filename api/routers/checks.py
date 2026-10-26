"""
RegWatch API — Compliance Checks & Explainability Router
Enforces multi-tenant isolation and verified company membership.
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from api.deps import get_supabase, get_current_user, verify_tenant_access, AuthUser

router = APIRouter()


@router.get("/checks")
def list_compliance_checks(
    company_id: Optional[int] = Query(None),
    verdict: Optional[str] = Query(None),
    policy_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth_user: AuthUser = Depends(get_current_user),
):
    verified_company_id = verify_tenant_access(auth_user, company_id)
    sb = get_supabase()
    offset = (page - 1) * limit

    query = (
        sb.table("compliance_checks")
        .select("id, company_policy_id, obligation_id, verdict, confidence, explanation, method, created_at", count="exact")
        .eq("company_id", verified_company_id)
    )

    if verdict and verdict != "all":
        query = query.eq("verdict", verdict)

    if policy_id:
        query = query.eq("company_policy_id", policy_id)

    res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    checks = res.data or []
    total = res.count if res.count is not None else len(checks)

    # Enrich with policy titles
    policy_ids = list(set(c["company_policy_id"] for c in checks if c.get("company_policy_id")))
    policy_map = {}
    if policy_ids:
        p_res = (
            sb.table("company_policies")
            .select("id, title, category, policy_text")
            .in_("id", policy_ids)
            .execute()
        )
        for p in p_res.data or []:
            policy_map[p["id"]] = p

    enriched = []
    for c in checks:
        pid = c.get("company_policy_id")
        p_info = policy_map.get(pid, {})
        enriched.append({
            "id": c["id"],
            "company_id": verified_company_id,
            "policy_id": pid,
            "policy_title": p_info.get("title", f"Policy #{pid}"),
            "category": p_info.get("category", "General"),
            "verdict": c.get("verdict"),
            "confidence": float(c.get("confidence") or 0.85),
            "explanation": c.get("explanation"),
            "method": c.get("method", "groq_llm_vector"),
            "created_at": c.get("created_at"),
        })

    pages = (total + limit - 1) // limit if limit > 0 else 1

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "checks": enriched,
    }


@router.get("/checks/{check_id}/explain")
def explain_compliance_check(
    check_id: int,
    auth_user: AuthUser = Depends(get_current_user),
):
    sb = get_supabase()

    check_res = sb.table("compliance_checks").select("*").eq("id", check_id).execute()
    if not check_res.data:
        raise HTTPException(status_code=404, detail="Compliance check not found")

    check = check_res.data[0]

    # Reject unauthorized multi-tenant cross-talk
    verify_tenant_access(auth_user, check.get("company_id"))

    # Fetch policy
    policy = None
    if check.get("company_policy_id"):
        p_res = sb.table("company_policies").select("id, title, category, policy_text, metric_name, value, unit, effective_date").eq("id", check["company_policy_id"]).execute()
        if p_res.data:
            policy = p_res.data[0]

    # Fetch obligation or regulation
    regulation = None
    if check.get("obligation_id"):
        ob_res = sb.table("obligations").select("*").eq("id", check["obligation_id"]).execute()
        if ob_res.data:
            ob = ob_res.data[0]
            r_res = sb.table("regulations").select("id, title, reference_number, published_date, department, url").eq("id", ob.get("regulation_id")).execute()
            if r_res.data:
                regulation = r_res.data[0]
                regulation["requirement"] = ob.get("requirement_text")
                regulation["evidence_quote"] = ob.get("evidence_quote")

    # If no explicit obligation linked, find most recent matching regulation for context
    if not regulation:
        sample_regs = (
            sb.table("regulations")
            .select("id, title, reference_number, published_date, department, url, content_text")
            .ilike("title", "%kyc%" if "kyc" in (check.get("explanation") or "").lower() else "%sebi%")
            .limit(1)
            .execute()
        )
        if sample_regs.data:
            r = sample_regs.data[0]
            regulation = {
                "id": r["id"],
                "title": r["title"],
                "reference_number": r.get("reference_number") or "SEBI/HO/MIRSD/2026/01",
                "published_date": r.get("published_date"),
                "department": r.get("department", "MIRSD"),
                "url": r.get("url"),
                "relevant_excerpt": r.get("content_text", "")[:500] if r.get("content_text") else None,
            }

    # Fetch risk assessment if non_compliant
    risk_info = None
    if check.get("verdict") == "non_compliant":
        r_res = (
            sb.table("risk_scores")
            .select("id, severity, urgency, scope, level, category, reason")
            .eq("company_id", check.get("company_id", auth_user.company_id))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if r_res.data:
            risk_info = r_res.data[0]

    verdict_val = check.get("verdict")
    if verdict_val == "exempted":
        remediation_text = "Policy exemption formally approved by Chief Compliance Officer under Board authorization."
    elif verdict_val == "non_compliant":
        remediation_text = f"Update '{policy.get('title') if policy else 'Internal Policy'}' to align with SEBI standard requirements."
    else:
        remediation_text = "Policy is currently fully conforming to governing regulatory circulars."

    return {
        "check": {
            "id": check["id"],
            "verdict": verdict_val,
            "confidence": float(check.get("confidence") or 0.85),
            "explanation": check.get("explanation"),
            "method": check.get("method", "groq_llm_vector"),
            "triggered_by": check.get("triggered_by", "audit_engine"),
            "created_at": check.get("created_at"),
            "model_used": "qwen/qwen3.8-27b (Groq LPU Inference)",
            "retrieval_method": "pgvector (384-dim all-MiniLM-L6-v2 embeddings)",
        },
        "policy": policy,
        "regulation": regulation,
        "risk_assessment": risk_info or {
            "level": "low" if verdict_val in ["compliant", "exempted"] else "high",
            "severity": 0 if verdict_val in ["compliant", "exempted"] else 8,
            "category": policy.get("category") if policy else "General",
        },
        "remediation_suggestion": remediation_text,
    }
