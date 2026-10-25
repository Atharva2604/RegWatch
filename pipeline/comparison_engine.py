import os
import json
from dotenv import load_dotenv
from supabase import create_client
from groq import Groq

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def seed_mock_data():
    """Helper to insert a mock company and policy if they don't exist"""
    comp = supabase.table("companies").select("id").eq("name", "FinCorp").execute()
    if not comp.data:
        inserted = supabase.table("companies").insert({"name": "FinCorp"}).execute()
        company_id = inserted.data[0]["id"]
        
        # Insert a mock policy
        supabase.table("company_policies").insert({
            "company_id": company_id,
            "category": "incident_reporting",
            "field_value": 48,
            "unit": "hours"
        }).execute()
    else:
        company_id = comp.data[0]["id"]
        
    return company_id

def run_real_comparison(company_id):
    """Fetches real policies and real regulations, then uses Groq to compare them."""
    
    # 1. Fetch Company Policies
    print("Fetching company policies...")
    policies = supabase.table("company_policies").select("*").eq("company_id", company_id).execute().data
    if not policies:
        print("No policies found for this company.")
        return
        
    # Convert policies to a string representation for the AI
    policy_text = "\n".join([f"- Category: {p['category']} | Requires: {p['field_value']} {p['unit']}" for p in policies])
    print(f"Loaded Policies:\n{policy_text}\n")

    # 2. Fetch Regulations (Let's just take the first 3 for testing so we don't blow up the API limit)
    print("Fetching latest regulations...")
    regulations = supabase.table("regulations").select("id, title, content_text").limit(3).execute().data
    
    for reg in regulations:
        print(f"--- Analyzing Regulation: {reg['title']} ---")
        
        # We only pass the first 8000 chars of the regulation text to fit in the context window
        reg_text_snippet = reg.get("content_text", "")
        if not reg_text_snippet:
            print("No text found for this regulation. Skipping...")
            continue
            
        reg_text_snippet = reg_text_snippet[:8000] 
        
        prompt = f"""
You are an expert compliance AI. 
Compare the company's internal policies against the new regulation text provided below.

Company Policies:
{policy_text}

New Regulation Text:
{reg_text_snippet}

Evaluate if the company's policies are strictly compliant with the new regulation. 
If the regulation mentions a stricter requirement (e.g. reporting within 6 hours, but company policy says 48 hours), then it is NOT compliant. If the regulation is irrelevant to the policy, assume compliant.

Respond ONLY with a valid JSON object matching this schema, without markdown formatting:
{{
    "is_compliant": true or false,
    "risk_score": integer from 0 to 100 (0 if compliant, 100 if severe violation),
    "details": "A 1-sentence explanation of the gap or compliance status"
}}
"""
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a regulatory compliance assistant. Output only JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
                response_format={"type": "json_object"}
            )
            
            result_json = chat_completion.choices[0].message.content
            result = json.loads(result_json)
            
            is_compliant = result.get("is_compliant", True)
            score = result.get("risk_score", 0)
            details = result.get("details", "")
            
            print(f"Compliant: {is_compliant} | Risk Score: {score}")
            print(f"Details: {details}\n")
            
            # 3. Write compliance check back to real table
            # (Assuming policy[0] for simplicity since we only have one policy)
            policy_id = policies[0]["id"] 
            
            supabase.table("compliance_checks").insert({
                "company_id": company_id,
                "policy_id": policy_id,
                "is_compliant": is_compliant,
                "details": details
            }).execute()
            
            # 4. Write risk score if non-compliant
            if not is_compliant:
                supabase.table("risk_scores").insert({
                    "company_id": company_id,
                    "score": score,
                    "category": policies[0]["category"],
                    "reason": details
                }).execute()
                
        except Exception as e:
            print(f"Error analyzing {reg['title']} with Groq: {e}")

# Alias for main.py compatibility
run_comparison_demo = run_real_comparison


if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("CRITICAL: GROQ_API_KEY not found in .env file! Please add it before running.")
    else:
        print("Seeding mock company data into real tables...")
        c_id = seed_mock_data()
        print("Running real database comparison engine using Groq AI...")
        run_real_comparison(c_id)
        print("Done! Check Supabase 'compliance_checks' and 'risk_scores' tables.")
