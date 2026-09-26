# MOCK DATA
MOCK_REGULATION = {
    "category": "incident_reporting", 
    "field_value": 24, 
    "unit": "hours"
}

MOCK_POLICY = {
    "category": "incident_reporting", 
    "field_value": 48, 
    "unit": "hours"
}

def compare(regulation: dict, policy: dict) -> dict:
    """
    Checks if the company policy meets the regulation's requirement.
    For this 'must report within X hours' case, policy value should be <= regulation value.
    """
    is_compliant = policy["field_value"] <= regulation["field_value"]
    
    if is_compliant:
        message = f"Compliant: company reports within {policy['field_value']} {policy['unit']}, which meets the {regulation['field_value']} {regulation['unit']} requirement."
    else:
        message = f"Gap found: company reports within {policy['field_value']} {policy['unit']}, but regulation requires {regulation['field_value']} {regulation['unit']}."
        
    return {
        "is_compliant": is_compliant,
        "message": message
    }

def calculate_risk_score(regulation: dict, policy: dict) -> int:
    """
    Calculates a simple score from 0-100 based on how far the policy value is from the regulation value.
    """
    reg_val = regulation["field_value"]
    pol_val = policy["field_value"]
    
    if pol_val <= reg_val:
        return 0 # No risk if compliant
        
    # Simple formula: percentage difference scaled to 0-100, maxing out at 100
    # For example, if reg is 24 and policy is 48, diff is 24. 
    # (24 / 24) * 100 = 100 risk score.
    diff = pol_val - reg_val
    score = int((diff / reg_val) * 100)
    
    return min(score, 100) # Cap at 100

def run_comparison_demo():
    print("Comparing MOCK DATA:")
    print(f"Regulation: {MOCK_REGULATION}")
    print(f"Policy:     {MOCK_POLICY}\n")
    
    comparison_result = compare(MOCK_REGULATION, MOCK_POLICY)
    risk_score = calculate_risk_score(MOCK_REGULATION, MOCK_POLICY)
    
    if not comparison_result["is_compliant"]:
        print(f"ALERT: {comparison_result['message']} (Risk Score: {risk_score}/100)")
    else:
        print(f"SUCCESS: {comparison_result['message']} (Risk Score: {risk_score}/100)")

if __name__ == "__main__":
    run_comparison_demo()
