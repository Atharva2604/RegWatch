import axios from 'axios';
import { supabase } from './supabase';
import type {
  DashboardStats,
  Regulation,
  CompanyPolicy,
  ComplianceCheck,
  Alert,
  AlertOverrideRequest,
  AlertOverrideResponse,
  PreCheckVerdict,
  AuditStatus,
  AuditEvent,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically inject Supabase Auth Bearer JWT token into API requests
apiClient.interceptors.request.use(async (config) => {
  try {
    const { data } = await supabase.auth.getSession();
    const token = data?.session?.access_token;
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    // Proceed without header for local dev fallback
  }
  return config;
});

export const api = {
  // Dashboard
  getDashboardStats: async (companyId?: number): Promise<DashboardStats> => {
    const res = await apiClient.get('/dashboard/stats', { params: { company_id: companyId } });
    return res.data;
  },

  // Alerts
  getAlerts: async (companyId?: number, status?: string, severity?: string): Promise<{ count: number; alerts: Alert[] }> => {
    const res = await apiClient.get('/alerts', {
      params: { company_id: companyId, status, severity },
    });
    return res.data;
  },

  acknowledgeAlert: async (alertId: string | number, note?: string) => {
    const res = await apiClient.post(`/alerts/${alertId}/acknowledge`, { note });
    return res.data;
  },

  resolveAlert: async (alertId: string | number) => {
    const res = await apiClient.post(`/alerts/${alertId}/resolve`);
    return res.data;
  },

  overrideAlert: async (alertId: string | number, data: AlertOverrideRequest): Promise<AlertOverrideResponse> => {
    const res = await apiClient.post(`/alerts/${alertId}/override`, data);
    return res.data;
  },

  // Regulations
  getRegulations: async (params?: { page?: number; limit?: number; q?: string; legal_type?: string; department?: string }) => {
    const res = await apiClient.get('/regulations', { params });
    return res.data as {
      page: number;
      limit: number;
      total: number;
      pages: number;
      data: Regulation[];
    };
  },

  getRegulation: async (id: number) => {
    const res = await apiClient.get(`/regulations/${id}`);
    return res.data as {
      regulation: Regulation;
      obligations: any[];
    };
  },

  getRegulationChunks: async (id: number) => {
    const res = await apiClient.get(`/regulations/${id}/chunks`);
    return res.data as {
      regulation_id: number;
      count: number;
      chunks: any[];
    };
  },

  triggerRegulationAudit: async (id: number) => {
    const res = await apiClient.post(`/regulations/${id}/trigger-audit`);
    return res.data;
  },

  getSources: async () => {
    const res = await apiClient.get('/sources');
    return res.data;
  },

  // Policies
  getPolicies: async (companyId?: number, category?: string, q?: string) => {
    const res = await apiClient.get('/policies', {
      params: { company_id: companyId, category, q },
    });
    return res.data as {
      company_id: number;
      count: number;
      categories: string[];
      policies: CompanyPolicy[];
    };
  },

  getPolicy: async (id: number) => {
    const res = await apiClient.get(`/policies/${id}`);
    return res.data as {
      policy: CompanyPolicy;
      recent_checks: ComplianceCheck[];
    };
  },

  createPolicy: async (policy: Partial<CompanyPolicy>, companyId?: number) => {
    const res = await apiClient.post('/policies', policy, {
      params: { company_id: companyId },
    });
    return res.data;
  },

  updatePolicy: async (id: number, policy: Partial<CompanyPolicy>) => {
    const res = await apiClient.put(`/policies/${id}`, policy);
    return res.data;
  },

  // Compliance Checks
  getComplianceChecks: async (params?: { page?: number; limit?: number; verdict?: string; policy_id?: number; company_id?: number }) => {
    const res = await apiClient.get('/checks', { params });
    return res.data as {
      page: number;
      limit: number;
      total: number;
      pages: number;
      checks: ComplianceCheck[];
    };
  },

  explainCheck: async (checkId: number) => {
    const res = await apiClient.get(`/checks/${checkId}/explain`);
    return res.data as {
      check: any;
      policy: CompanyPolicy;
      regulation: any;
      risk_assessment: any;
      remediation_suggestion: string;
    };
  },

  // Pre-Check Impact Simulator
  preCheckPolicy: async (draft: {
    title: string;
    category: string;
    policy_text: string;
    metric_name?: string;
    value?: number;
    unit?: string;
  }) => {
    const res = await apiClient.post('/pre-check', draft);
    return res.data as {
      verdict: PreCheckVerdict;
      matched_regulations: Partial<Regulation>[];
      input_policy: any;
    };
  },

  // Baseline Audit
  getAuditStatus: async (companyId?: number): Promise<AuditStatus> => {
    const res = await apiClient.get('/audit/status', { params: { company_id: companyId } });
    return res.data;
  },

  triggerBaselineAudit: async (limit: number = 5, companyId?: number) => {
    const res = await apiClient.post('/audit/baseline', { limit, company_id: companyId });
    return res.data;
  },

  // Audit Events
  getAuditEvents: async (limit: number = 50, companyId?: number) => {
    const res = await apiClient.get('/audit-events', { params: { limit, company_id: companyId } });
    return res.data as { count: number; events: AuditEvent[] };
  },
};
