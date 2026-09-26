import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

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
    """Fetches real policies from Supabase, compares against a simulated structured regulation, and writes the results back."""
    policies = supabase.table("company_policies").select("*").eq("company_id", company_id).execute()
    
    # We'll simulate a structured regulation for now, since NLP extraction (Week 3) hasn't happened.
    mock_db_regulation = {
        "category": "incident_reporting",
        "field_value": 24,
        "unit": "hours"
    }
    
    for policy in policies.data:
        # 1. Compare
        is_compliant = policy["field_value"] <= mock_db_regulation["field_value"]
        
        # 2. Risk score formula
        score = 0
        if not is_compliant and mock_db_regulation["field_value"] > 0:
            diff = policy["field_value"] - mock_db_regulation["field_value"]
            score = int((diff / mock_db_regulation["field_value"]) * 100)
            score = min(score, 100)
            
        print(f"Comparing Policy [{policy['category']}] (Value: {policy['field_value']}) vs Regulation ({mock_db_regulation['field_value']})")
        print(f"Compliant: {is_compliant} | Risk Score: {score}")
        
        # 3. Write compliance check back to real table
        supabase.table("compliance_checks").insert({
            "company_id": company_id,
            "policy_id": policy["id"],
            "is_compliant": is_compliant,
            "details": f"Policy requires {policy['field_value']} {policy['unit']}, Reg requires {mock_db_regulation['field_value']} {mock_db_regulation['unit']}"
        }).execute()
        
        # 4. Write risk score if non-compliant
        if not is_compliant:
            supabase.table("risk_scores").insert({
                "company_id": company_id,
                "score": score,
                "category": policy["category"],
                "reason": "Gap found in incident reporting timeframe"
            }).execute()

if __name__ == "__main__":
    print("Seeding mock company data into real tables...")
    try:
        c_id = seed_mock_data()
        print("Running real database comparison engine...")
        run_real_comparison(c_id)
        print("Done! Check Supabase 'compliance_checks' and 'risk_scores' tables.")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        print("Make sure your tables (companies, company_policies, compliance_checks, risk_scores) exist in Supabase!")
