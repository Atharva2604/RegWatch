export interface Company {
  id: number;
  name: string;
  industry?: string;
  domain?: string;
}

export interface Regulation {
  id: number;
  title: string;
  reference_number?: string;
  published_date?: string;
  department?: string;
  legal_type?: string;
  url?: string;
  status?: string;
  last_checked_at?: string;
  content_text?: string;
}

export interface Obligation {
  id: number;
  regulation_id: number;
  category: string;
  applies_to?: string;
  requirement_text: string;
  evidence_quote?: string;
  metric_name?: string;
  threshold_value?: number;
  unit?: string;
}

export interface CompanyPolicy {
  id: number;
  company_id: number;
  title: string;
  policy_text: string;
  category: string;
  metric_name?: string;
  value?: number;
  unit?: string;
  applies_to?: string;
  effective_date?: string;
  updated_at?: string;
  created_at?: string;
}

export interface ComplianceCheck {
  id: number;
  company_id: number;
  policy_id: number;
  policy_title?: string;
  category?: string;
  verdict: 'compliant' | 'non_compliant';
  confidence: number;
  explanation: string;
  method?: string;
  created_at: string;
}

export interface Alert {
  id: string | number;
  company_id: number;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  status: 'open' | 'acknowledged' | 'resolved' | 'exempted';
  channel?: string;
  category?: string;
  policy_id?: number;
  policy_title?: string;
  compliance_check_id?: number;
  legal_opinion?: string;
  board_resolution_number?: string;
  exemption_signer?: string;
  created_at: string;
  acknowledged_at?: string;
}

export interface AlertOverrideRequest {
  legal_opinion: string;
  board_resolution_number?: string;
  rationale?: string;
  exemption_type?: string;
  signer_name?: string;
}

export interface AlertOverrideResponse {
  status: string;
  alert_id: string | number;
  compliance_check_id?: number;
  verdict: string;
  board_resolution_number?: string;
  audit_defense_signature: string;
  exempted_at: string;
}


export interface RiskScore {
  id: number;
  company_id: number;
  severity: number;
  urgency: number;
  scope: number;
  level: 'high' | 'medium' | 'low';
  category: string;
  reason: string;
  created_at: string;
}

export interface DashboardStats {
  company_id: number;
  company_name: string;
  stats: {
    compliance_score: number;
    total_policies: number;
    total_regulations: number;
    total_checks: number;
    compliant_checks: number;
    non_compliant_checks: number;
    open_alerts: number;
    risk_counts: {
      high: number;
      medium: number;
      low: number;
    };
  };
  recent_checks: ComplianceCheck[];
  recent_risks: RiskScore[];
  category_distribution: { category: string; count: number }[];
}

export interface PreCheckVerdict {
  is_compliant: boolean;
  risk_score: number;
  severity: 'high' | 'medium' | 'low';
  summary: string;
  conflicts: { regulation_title: string; issue: string }[];
  recommendations: string;
  can_proceed_safely: boolean;
}

export interface AuditStatus {
  is_running: boolean;
  status: string;
  company_id: number;
  company_name: string;
  total_policies: number;
  audited_count: number;
  compliant_count: number;
  gap_count: number;
  health_score: number;
  risk_breakdown: {
    high: number;
    medium: number;
    low: number;
  };
  gaps: {
    check_id: number;
    policy_id: number;
    policy_title: string;
    category: string;
    explanation: string;
    severity: 'high' | 'medium' | 'low';
    confidence: number;
    created_at: string;
  }[];
  last_run_at?: string;
}

export interface AuditEvent {
  id: string | number;
  entity: string;
  entity_id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: string;
}
