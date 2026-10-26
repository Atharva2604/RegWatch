import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  BookOpen,
  Wand2,
  Check,
  Save,
  HelpCircle,
} from 'lucide-react';
import { api } from '../lib/api';
import { getSeverityBadge } from '../lib/utils';
import type { PreCheckVerdict, Regulation } from '../types';

export const ProposeChange: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('KYC & Client Onboarding');
  const [policyText, setPolicyText] = useState('');
  const [metricName, setMetricName] = useState('');
  const [metricValue, setMetricValue] = useState('');
  const [metricUnit, setMetricUnit] = useState('');

  const [result, setResult] = useState<{
    verdict: PreCheckVerdict;
    matched_regulations: Partial<Regulation>[];
  } | null>(null);

  const preCheckMutation = useMutation({
    mutationFn: () =>
      api.preCheckPolicy({
        title,
        category,
        policy_text: policyText,
        metric_name: metricName || undefined,
        value: metricValue ? parseFloat(metricValue) : undefined,
        unit: metricUnit || undefined,
      }),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const saveMutation = useMutation({
    mutationFn: () =>
      api.createPolicy({
        title,
        category,
        policy_text: policyText,
        metric_name: metricName || undefined,
        value: metricValue ? parseFloat(metricValue) : undefined,
        unit: metricUnit || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companyPolicies'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      navigate('/policies');
    },
  });

  // Sample Scenarios for quick 1-click testing
  const loadScenario = (type: 'aadhaar' | 'scores' | 'risk_meter') => {
    if (type === 'aadhaar') {
      setTitle('Mandatory Aadhaar e-KYC Verification');
      setCategory('KYC & Client Onboarding');
      setPolicyText('All individual retail clients must compulsorily undergo Aadhaar OTP e-KYC as the primary identity verification prior to equity trade execution.');
      setMetricName('aadhaar_compulsory');
      setMetricValue('1');
      setMetricUnit('boolean');
    } else if (type === 'scores') {
      setTitle('Client Grievance Redressal SLA');
      setCategory('Investor Grievance Redressal');
      setPolicyText('Complaints received via SEBI SCORES portal must be investigated and resolved internally within a maximum of 15 calendar days from receipt.');
      setMetricName('scores_atr_days');
      setMetricValue('15');
      setMetricUnit('days');
    } else {
      setTitle('Mandatory Credit Risk-o-Meter Publication');
      setCategory('Dealing & Execution');
      setPolicyText('Display the latest SEBI Credit Risk-o-Meter badge on all offering memorandums, primary market application portals, and trading terminals for listed debt securities.');
      setMetricName('risk_meter_displayed');
      setMetricValue('1');
      setMetricUnit('boolean');
    }
  };

  const applyRecommendation = () => {
    if (result?.verdict.recommendations) {
      setPolicyText(result.verdict.recommendations);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Pre-Change Regulatory Parity Simulator
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Simulate prospective policy amendments before publishing to test against 3,030 SEBI regulations, calculate conflict risk, and receive AI-recommended compliant phrasing.
        </p>
      </div>

      {/* Preset Test Scenarios */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center gap-3">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
          Test Scenarios:
        </span>
        <button
          onClick={() => loadScenario('aadhaar')}
          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors border border-slate-700/60"
        >
          Mandatory Aadhaar KYC (High Risk Test)
        </button>
        <button
          onClick={() => loadScenario('scores')}
          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors border border-slate-700/60"
        >
          SCORES 15-Day ATR Resolution
        </button>
        <button
          onClick={() => loadScenario('risk_meter')}
          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors border border-slate-700/60"
        >
          Credit Risk-o-Meter Display
        </button>
      </div>

      {/* Simulator Form */}
      <div className="glass-panel p-6 rounded-2xl">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            preCheckMutation.mutate();
          }}
          className="space-y-4 text-xs"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-300 mb-1.5">
                Proposed Policy Title
              </label>
              <input
                required
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Identity Verification & e-KYC Mandate"
                className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-300 mb-1.5">
                Regulatory Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="KYC & Client Onboarding">KYC & Client Onboarding</option>
                <option value="Margin & Collateral Management">Margin & Collateral Management</option>
                <option value="Cyber Security & IT Risk">Cyber Security & IT Risk</option>
                <option value="Investor Grievance Redressal">Investor Grievance Redressal</option>
                <option value="Dealing & Execution">Dealing & Execution</option>
                <option value="Code of Conduct & Insider Trading">Code of Conduct & Insider Trading</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-300 mb-1.5">
              Draft Policy Text & Operational Rules
            </label>
            <textarea
              required
              rows={4}
              value={policyText}
              onChange={(e) => setPolicyText(e.target.value)}
              placeholder="Paste the proposed wording or operational amendment here..."
              className="w-full bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 text-slate-100 font-mono text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-500 leading-relaxed"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Metric Key (Optional)</label>
              <input
                type="text"
                value={metricName}
                onChange={(e) => setMetricName(e.target.value)}
                placeholder="e.g. max_incident_hours"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Threshold Value</label>
              <input
                type="number"
                value={metricValue}
                onChange={(e) => setMetricValue(e.target.value)}
                placeholder="e.g. 6"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Unit</label>
              <input
                type="text"
                value={metricUnit}
                onChange={(e) => setMetricUnit(e.target.value)}
                placeholder="e.g. hours"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={preCheckMutation.isPending || !title || !policyText}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>{preCheckMutation.isPending ? 'Simulating via Groq AI & pgvector...' : 'Run Pre-Change Impact Simulator'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Simulation Results Output */}
      {result && (
        <div className="glass-panel p-6 rounded-2xl border-cyan-500/30 space-y-6 animate-fadeIn">
          {/* Result Banner */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2 mb-1">
                {result.verdict.is_compliant ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-rose-400" />
                )}
                <h3 className="text-lg font-bold text-white">
                  {result.verdict.is_compliant ? 'Conforming Policy — Safe to Adopt' : 'Regulatory Violation Detected'}
                </h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                {result.verdict.summary}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-[10px] uppercase font-bold text-slate-400">Conflict Risk</p>
                <p className={`text-xl font-black ${result.verdict.is_compliant ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {result.verdict.risk_score} / 100
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getSeverityBadge(result.verdict.severity).bg}`}>
                {result.verdict.severity} Severity
              </span>
            </div>
          </div>

          {/* Identified Conflicts */}
          {result.verdict.conflicts.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 mb-2 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                Statutory Conflicts & Contradictions
              </h4>
              <div className="space-y-2">
                {result.verdict.conflicts.map((c, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-500/20 text-xs">
                    <p className="font-semibold text-white mb-1">{c.regulation_title}</p>
                    <p className="text-rose-300">{c.issue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Recommended Phrasing */}
          {result.verdict.recommendations && (
            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                  <Wand2 className="w-4 h-4 text-cyan-400" />
                  AI Recommended Compliant Wording
                </span>
                <button
                  type="button"
                  onClick={applyRecommendation}
                  className="px-2.5 py-1 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 font-semibold text-[11px] border border-indigo-500/40 transition-colors"
                >
                  Insert Recommendation into Form
                </button>
              </div>
              <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                {result.verdict.recommendations}
              </p>
            </div>
          )}

          {/* Matched Governing Regulations */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              Retrieved SEBI Governing Circulars
            </h4>
            <div className="space-y-2">
              {result.matched_regulations.map((r) => (
                <div key={r.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-slate-200">{r.title}</p>
                    <p className="font-mono text-[10px] text-slate-400">{r.reference_number || 'SEBI Circular'}</p>
                  </div>
                  <span className="text-[10px] text-slate-400">{r.published_date || ''}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Action to Save */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-md"
            >
              <Save className="w-4 h-4" />
              <span>{saveMutation.isPending ? 'Publishing...' : 'Save to Active FinCorp Policies'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
