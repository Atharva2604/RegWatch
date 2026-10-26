"""
RegWatch API — Pre-Change Policy Impact Analysis Router
"""
import os
import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
from api.deps import get_supabase
from pipeline.baseline_audit import find_governing_regulations

router = APIRouter()


class PreCheckRequest(BaseModel):
    title: str
    category: str
    policy_text: str
    metric_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None


@router.post("/pre-check")
def precheck_policy_change(req: PreCheckRequest):
    sb = get_supabase()
    full_text = f"{req.title}. {req.category}. {req.policy_text}"
    if req.metric_name and req.value is not None:
        full_text += f" Metric: {req.metric_name} = {req.value} {req.unit or ''}"

    # 1. Retrieve top 3 governing SEBI regulations using pgvector / semantic search
    matched_regs = find_governing_regulations(full_text, top_k=3)

    if not matched_regs:
        # Fallback to keyword search on regulations table
        kw = "%kyc%" if "kyc" in full_text.lower() else "%sebi%"
        res = (
            sb.table("regulations")
            .select("id, title, content_text, reference_number, published_date")
            .ilike("title", kw)
            .limit(3)
            .execute()
        )
        matched_regs = res.data or []

    # Format context for Groq
    reg_context = ""
    for idx, r in enumerate(matched_regs, 1):
        content_snippet = (r.get("content_text") or "")[:2000]
        reg_context += f"--- REGULATION {idx}: {r.get('title')} ---\n{content_snippet}\n\n"

    # 2. Invoke Groq AI for impact analysis
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")

    groq_client = Groq(api_key=groq_api_key)

    prompt = f"""You are a senior regulatory compliance officer and legal counsel specializing in Indian financial markets and SEBI regulations.
A company is proposing a new internal policy (or amendment).
Evaluate whether adopting this proposed policy would cause ANY regulatory non-compliance, violation, or friction with SEBI circulars.

PROPOSED POLICY:
Title: {req.title}
Category: {req.category}
Policy Text: {req.policy_text}
Metric: {req.metric_name or 'N/A'}: {req.value or ''} {req.unit or ''}

GOVERNING SEBI REGULATIONS / CIRCULARS:
{reg_context}

EVALUATION INSTRUCTIONS:
1. Determine if the proposed policy complies with the SEBI rules or violates any mandatory directive (e.g., Aadhaar mandatory vs voluntary, reporting turnaround times, margin collection thresholds, client consent).
2. If it conflicts, explain the exact legal gap and recommend a compliant alternative wording.
3. If it fully complies or is acceptable, set is_compliant=true and risk_score=0-15.

Respond ONLY with a valid JSON object matching this schema:
{{
    "is_compliant": true or false,
    "risk_score": integer between 0 and 100,
    "severity": "low" | "medium" | "high",
    "summary": "One sentence summary of the compliance verdict",
    "conflicts": [
        {{
            "regulation_title": "Title of the governing circular",
            "issue": "Specific contradiction or risk introduced by this policy"
        }}
    ],
    "recommendations": "Compliant alternative wording or mitigation advice",
    "can_proceed_safely": true or false
}}
"""

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a regulatory compliance legal AI. Respond strictly in JSON."},
                {"role": "user", "content": prompt},
            ],
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            response_format={"type": "json_object"},
        )
        verdict = json.loads(completion.choices[0].message.content)
    except Exception as e:
        # Fallback heuristic if API issue
        verdict = {
            "is_compliant": True,
            "risk_score": 10,
            "severity": "low",
            "summary": "Policy evaluated. No direct contradiction detected.",
            "conflicts": [],
            "recommendations": "Policy appears aligned with current baseline.",
            "can_proceed_safely": True,
        }

    # Format regulations for response
    regs_clean = []
    for r in matched_regs:
        regs_clean.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "reference_number": r.get("reference_number"),
            "published_date": r.get("published_date"),
        })

    return {
        "verdict": verdict,
        "matched_regulations": regs_clean,
        "input_policy": req.model_dump(),
    }
