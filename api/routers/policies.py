"""
RegWatch API — Company Policies Router
Enforces multi-tenant authorization and RBAC role checks for policy modifications.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from api.deps import get_supabase, get_current_user, verify_tenant_access, require_role, AuthUser

router = APIRouter()

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


class PolicyCreate(BaseModel):
    title: str
    category: str
    policy_text: str
    metric_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    applies_to: Optional[str] = "All Employees & Brokers"
    effective_date: Optional[str] = None


class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    policy_text: Optional[str] = None
    metric_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    applies_to: Optional[str] = None
    effective_date: Optional[str] = None


@router.get("/policies")
def list_policies(
    company_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    auth_user: AuthUser = Depends(get_current_user),
):
    verified_company_id = verify_tenant_access(auth_user, company_id)
    sb = get_supabase()
    query = (
        sb.table("company_policies")
        .select("id, company_id, title, policy_text, category, metric_name, value, unit, applies_to, effective_date, updated_at, created_at")
        .eq("company_id", verified_company_id)
    )

    if category and category != "all":
        query = query.eq("category", category)

    if q and q.strip():
        query = query.ilike("title", f"%{q.strip()}%")

    res = query.order("id", desc=False).execute()
    policies = res.data or []

    # Get distinct categories
    cats = sorted(list(set(p.get("category") for p in policies if p.get("category"))))

    return {
        "company_id": verified_company_id,
        "count": len(policies),
        "categories": cats,
        "policies": policies,
    }


@router.get("/policies/{policy_id}")
def get_policy(
    policy_id: int,
    auth_user: AuthUser = Depends(get_current_user),
):
    sb = get_supabase()
    res = (
        sb.table("company_policies")
        .select("id, company_id, title, policy_text, category, metric_name, value, unit, applies_to, effective_date, updated_at, created_at")
        .eq("id", policy_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy = res.data[0]
    verify_tenant_access(auth_user, policy.get("company_id"))

    # Get recent checks for this policy
    checks = (
        sb.table("compliance_checks")
        .select("id, verdict, confidence, explanation, created_at, method")
        .eq("company_policy_id", policy_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
        .data
        or []
    )

    return {
        "policy": policy,
        "recent_checks": checks,
    }


@router.post("/policies")
def create_policy(
    data: PolicyCreate,
    company_id: Optional[int] = Query(None),
    auth_user: AuthUser = Depends(require_role(["officer", "admin"])),
):
    verified_company_id = verify_tenant_access(auth_user, company_id)
    sb = get_supabase()

    # Generate vector embedding for semantic search
    model = get_embedding_model()
    text_to_embed = f"{data.title}. {data.category}. {data.policy_text}"
    embedding = model.encode(text_to_embed[:1000], normalize_embeddings=True).tolist()

    row = {
        "company_id": verified_company_id,
        "title": data.title,
        "category": data.category,
        "policy_text": data.policy_text,
        "metric_name": data.metric_name,
        "value": data.value,
        "unit": data.unit,
        "applies_to": data.applies_to,
        "effective_date": data.effective_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "embedding": embedding,
    }

    insert_res = sb.table("company_policies").insert(row).execute()
    created = insert_res.data[0] if insert_res.data else row

    # Log audit event
    try:
        sb.table("audit_events").insert({
            "entity": "company_policy",
            "entity_id": str(created.get("id")),
            "event_type": "policy_created",
            "payload": {
                "title": data.title,
                "category": data.category,
                "company_id": verified_company_id,
                "created_by": auth_user.user_id,
            },
        }).execute()
    except Exception:
        pass

    return {"status": "created", "policy": created}


@router.put("/policies/{policy_id}")
def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    auth_user: AuthUser = Depends(require_role(["officer", "admin"])),
):
    sb = get_supabase()

    # Check ownership
    curr = sb.table("company_policies").select("id, company_id, title, category, policy_text").eq("id", policy_id).execute().data
    if not curr:
        raise HTTPException(status_code=404, detail="Policy not found")

    curr_obj = curr[0]
    verify_tenant_access(auth_user, curr_obj.get("company_id"))

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        return {"status": "no_changes"}

    # If policy text or title changed, recompute embedding
    if "policy_text" in update_data or "title" in update_data:
        title = update_data.get("title", curr_obj.get("title", ""))
        cat = update_data.get("category", curr_obj.get("category", ""))
        text = update_data.get("policy_text", curr_obj.get("policy_text", ""))

        model = get_embedding_model()
        text_to_embed = f"{title}. {cat}. {text}"
        update_data["embedding"] = model.encode(text_to_embed[:1000], normalize_embeddings=True).tolist()

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    sb.table("company_policies").update(update_data).eq("id", policy_id).execute()

    # Log audit event
    try:
        sb.table("audit_events").insert({
            "entity": "company_policy",
            "entity_id": str(policy_id),
            "event_type": "policy_updated",
            "payload": {
                **update_data,
                "updated_by": auth_user.user_id,
                "company_id": auth_user.company_id,
            },
        }).execute()
    except Exception:
        pass

    return {"status": "updated", "policy_id": policy_id}
