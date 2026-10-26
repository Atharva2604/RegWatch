"""
RegWatch Baseline Onboarding Audit Engine
Audits ALL company policies against the entire corpus of 3,030 SEBI regulations.
Uses pgvector semantic retrieval to find governing regulations for each policy,
then evaluates legal compliance with Groq AI.
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model ready.\n")
    return _model


def find_governing_regulations(policy_text, policy_embedding=None, top_k=3):
    """
    Searches governing regulations using paragraph/clause-level chunk retrieval
    (regulation_chunks) and falls back to whole-document match_regulations RPC.
    Solves the 1,000-character truncation loophole.
    """
    model = get_model()
    if policy_embedding is None:
        policy_embedding = model.encode(policy_text[:1500], normalize_embeddings=True).tolist()
    elif hasattr(policy_embedding, "tolist"):
        policy_embedding = policy_embedding.tolist()

    # 1. First attempt clause-level retrieval from regulation_chunks
    try:
        from pipeline.chunk_engine import find_governing_chunks
        chunks = find_governing_chunks(policy_text, top_k=top_k, query_embedding=policy_embedding)
        if chunks:
            formatted = []
            for c in chunks:
                reg = c.get("regulation", {})
                formatted.append({
                    "id": reg.get("id") or c.get("regulation_id"),
                    "title": reg.get("title") or f"SEBI Regulation #{c.get('regulation_id')}",
                    "content_text": c.get("text"), # The exact governing clause!
                    "reference_number": reg.get("reference_number"),
                    "published_date": reg.get("published_date"),
                    "department": reg.get("department"),
                    "similarity": c.get("similarity"),
                    "is_chunk": True,
                })
            return formatted
    except Exception as e:
        print(f"  [Notice: regulation_chunks fallback to match_regulations RPC: {e}]")

    # 2. Standard document-level match_regulations RPC fallback
    try:
        results = supabase.rpc("match_regulations", {
            "query_embedding": policy_embedding,
            "match_count": top_k
        }).execute()
        return results.data or []
    except Exception as e:
        print(f"  [Error querying match_regulations RPC: {e}]")
        return []


def run_baseline_audit(company_id=10, limit=None):
    """
    Performs a complete baseline audit for all policies of the specified company.
    """
    get_model()

    # 1. Fetch company policies
    comp_res = supabase.table("companies").select("name").eq("id", company_id).execute().data
    company_name = comp_res[0]["name"] if comp_res else f"Company #{company_id}"

    print(f"================================================================")
    print(f"       REGWATCH BASELINE REGULATORY AUDIT: {company_name.upper()}")
    print(f"================================================================")

    policies = (
        supabase.table("company_policies")
        .select("id, title, policy_text, category, metric_name, value, unit, embedding")
        .eq("company_id", company_id)
        .execute()
        .data
    )

    if limit:
        policies = policies[:limit]

    total_policies = len(policies)
    print(f"Total internal policies queued for audit: {total_policies}\n")

    compliant_count = 0
    non_compliant_count = 0
    high_risks = 0
    medium_risks = 0
    low_risks = 0

    audit_summary = []

    for idx, policy in enumerate(policies, 1):
        p_id = policy["id"]
        p_title = policy.get("title", "Untitled Policy")
        p_cat = policy.get("category", "General")
        p_text = policy.get("policy_text") or f"{policy.get('metric_name')}: {policy.get('value')} {policy.get('unit')}"

        print(f"[{idx}/{total_policies}] Auditing: '{p_title}' [{p_cat}]")

        # 2. Retrieve top governing regulations using pgvector
        matched_regs = find_governing_regulations(p_text, policy.get("embedding"), top_k=3)

        if not matched_regs:
            print("  No governing regulations returned. Marked compliant by default.\n")
            compliant_count += 1
            continue

        regs_context = ""
        for r_i, r in enumerate(matched_regs, 1):
            sim = r.get("similarity", 0)
            regs_context += f"Regulation #{r_i}: {r.get('title')} (sim: {sim:.2f})\nExcerpt: {(r.get('content_text') or '')[:1500]}\n\n"

        # 3. LLM evaluation prompt
        prompt = f"""You are a Senior Regulatory Compliance Auditor conducting a Baseline Regulatory Audit for a SEBI-registered stock broker.
Compare the internal company policy against the governing SEBI circulars retrieved from the regulatory archive.

INTERNAL COMPANY POLICY:
Title: {p_title}
Category: {p_cat}
Policy Text: {p_text}

GOVERNING SEBI CIRCULARS:
{regs_context}

EVALUATION RULES:
1. Determine whether this company policy satisfies all obligations in the governing circulars.
2. If an internal policy sets a weaker standard, violates a SEBI mandate (e.g. voluntary Aadhaar made mandatory, 45-day KYC vs 30-day mandate, 72-hour cyber reporting vs 6-hour SEBI rule), mark is_compliant = false.
3. If the regulations do not prohibit or conflict with the company policy, mark is_compliant = true.

Respond ONLY with a valid JSON object matching this schema, without any markdown formatting:
{{
    "is_compliant": true or false,
    "risk_score": integer from 0 to 100 (0=fully compliant, 100=critical violation),
    "details": "One concise sentence summarizing the compliance verdict and any gap.",
    "conflicting_circular": "Exact title of the conflicting circular or null if compliant"
}}
"""
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a regulatory compliance assistant. Output only JSON."},
                    {"role": "user", "content": prompt},
                ],
                model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
                response_format={"type": "json_object"}
            )
            result = json.loads(chat_completion.choices[0].message.content)

            is_compliant = result.get("is_compliant", True)
            score = result.get("risk_score", 0)
            details = result.get("details", "")
            conflict = result.get("conflicting_circular")
            sev = min(10, max(1, score // 10)) if not is_compliant else 0

            status_str = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
            print(f"  Verdict: {status_str} | Risk Score: {score}")
            print(f"  Audit Findings: {details}")
            if conflict:
                print(f"  Governing Rule Breached: {conflict}")
            print()

            if is_compliant:
                compliant_count += 1
            else:
                non_compliant_count += 1
                if score >= 70:
                    high_risks += 1
                    level = "high"
                elif score >= 40:
                    medium_risks += 1
                    level = "medium"
                else:
                    low_risks += 1
                    level = "low"

                # Record non-compliance risk score
                supabase.table("risk_scores").insert({
                    "company_id": company_id,
                    "severity": sev,
                    "urgency": sev,
                    "scope": max(1, sev - 2),
                    "level": level,
                    "category": p_cat,
                    "reason": details
                }).execute()

            # Record audit check
            supabase.table("compliance_checks").insert({
                "company_id": company_id,
                "company_policy_id": p_id,
                "verdict": "compliant" if is_compliant else "non_compliant",
                "explanation": details,
                "method": "baseline_audit_pgvector",
                "triggered_by": "onboarding_audit",
                "confidence": 0.90,
            }).execute()

            audit_summary.append({
                "policy": p_title,
                "category": p_cat,
                "verdict": status_str,
                "score": score,
                "details": details
            })

        except Exception as e:
            print(f"  Error auditing policy '{p_title}': {e}\n")

    health_percentage = (compliant_count / total_policies * 100) if total_policies > 0 else 100

    print("================================================================")
    print("                 BASELINE AUDIT COMPLETE                        ")
    print("================================================================")
    print(f"Total Policies Audited : {total_policies}")
    print(f"Compliant Policies     : {compliant_count} ({health_percentage:.1f}%)")
    print(f"Non-Compliant Violations: {non_compliant_count}")
    print(f"  - High Severity Violations   : {high_risks}")
    print(f"  - Medium Severity Violations : {medium_risks}")
    print(f"  - Low Severity Violations    : {low_risks}")
    print("================================================================")


if __name__ == "__main__":
    import sys
    # Optional limit argument, e.g. python baseline_audit.py 10
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_baseline_audit(company_id=10, limit=limit_arg)
