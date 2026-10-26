import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldCheck,
  FileText,
  BookOpen,
  Cpu,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ExternalLink,
  Wand2,
} from 'lucide-react';
import { api } from '../lib/api';
import { VerdictBadge } from '../components/common/VerdictBadge';
import { getSeverityBadge, formatDateTime, formatDate } from '../lib/utils';

export const Explain: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ['checkExplain', id],
    queryFn: () => api.explainCheck(Number(id)),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Loading audit trail & explainability chain...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-panel p-8 rounded-2xl text-center max-w-md mx-auto my-12">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-2" />
        <h3 className="text-lg font-bold text-white mb-1">Check Not Found</h3>
        <p className="text-xs text-slate-400 mb-4">Could not retrieve check #{id}.</p>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs"
        >
          Go Back
        </button>
      </div>
    );
  }

  const { check, policy, regulation, risk_assessment, remediation_suggestion } = data;
  const isCompliant = check.verdict === 'compliant';
  const sev = getSeverityBadge(risk_assessment?.level);

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Back button & Title */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Checks</span>
        </button>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Explainable Audit Chain of Custody
              </h1>
              <span className="font-mono text-xs text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                Check #{check.id}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic verification trail linking internal policy text to governing SEBI directives.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <VerdictBadge verdict={check.verdict} size="lg" />
          </div>
        </div>
      </div>

      {/* Chain Step 1: Internal Policy */}
      <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Step 1: Internal Company Policy</h3>
            <p className="text-[10px] text-slate-400">Registered in FinCorp Securities Policy Book</p>
          </div>
        </div>

        {policy ? (
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-slate-100 text-sm">{policy.title}</h4>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-cyan-400 font-medium">
                {policy.category}
              </span>
            </div>
            <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              {policy.policy_text}
            </p>
            {policy.metric_name && (
              <div className="flex items-center gap-3 text-[11px] text-slate-400">
                <span>Operational Metric:</span>
                <span className="font-mono text-cyan-300 font-semibold">
                  {policy.metric_name} = {policy.value} {policy.unit || ''}
                </span>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-slate-400">Policy details archived.</p>
        )}
      </div>

      {/* Chain Step 2: Governing SEBI Regulation */}
      <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Step 2: Governing Regulator Directive</h3>
            <p className="text-[10px] text-slate-400">Matched via pgvector semantic vector embedding</p>
          </div>
        </div>

        {regulation ? (
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <h4 className="font-bold text-slate-100">{regulation.title}</h4>
              <span className="font-mono text-[10px] text-slate-400">
                {regulation.reference_number || 'Official Circular'}
              </span>
            </div>
            {regulation.requirement && (
              <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <span className="text-cyan-400 font-semibold">Statutory Clause: </span>
                {regulation.requirement}
              </p>
            )}
            {regulation.relevant_excerpt && (
              <p className="text-slate-400 text-[11px] line-clamp-3 font-mono bg-slate-950/40 p-2.5 rounded border border-slate-800/60">
                {regulation.relevant_excerpt}
              </p>
            )}
          </div>
        ) : (
          <p className="text-xs text-slate-400">Governing regulation details loaded.</p>
        )}
      </div>

      {/* Chain Step 3: AI Legal Evaluation & Verdict */}
      <div className={`glass-panel p-6 rounded-2xl border ${isCompliant ? 'border-emerald-500/30' : 'border-rose-500/30'}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${isCompliant ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'}`}>
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Step 3: AI Parity Synthesis & Verdict</h3>
              <p className="text-[10px] text-slate-400">Model: {check.model_used}</p>
            </div>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${sev.bg}`}>
            {sev.label}
          </span>
        </div>

        <div className="space-y-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
            <h5 className="font-bold text-slate-300 uppercase tracking-wider text-[11px]">
              Evaluation Finding
            </h5>
            <p className="text-slate-200 leading-relaxed">
              {check.explanation}
            </p>
          </div>

          {/* Remediation Advice */}
          {remediation_suggestion && (
            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-2">
              <h5 className="font-bold text-indigo-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                <Wand2 className="w-3.5 h-3.5 text-cyan-400" />
                Actionable Compliance Remediation
              </h5>
              <p className="text-slate-300 leading-relaxed font-mono text-[11px]">
                {remediation_suggestion}
              </p>
            </div>
          )}

          {/* Technical Metadata Footer */}
          <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[10px] text-slate-400 font-mono">
            <span>Method: {check.method}</span>
            <span>Vector Search: {check.retrieval_method}</span>
            <span>Evaluated At: {formatDateTime(check.created_at)}</span>
            <span>Confidence: {Math.round(check.confidence * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
