import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardCheck,
  PlayCircle,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Search,
  Filter,
  SlidersHorizontal,
} from 'lucide-react';
import { api } from '../lib/api';
import { VerdictBadge } from '../components/common/VerdictBadge';
import { getSeverityBadge, formatDate } from '../lib/utils';

export const BaselineAudit: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const { data: audit, isLoading, refetch } = useQuery({
    queryKey: ['baselineAuditStatus'],
    queryFn: () => api.getAuditStatus(),
    refetchInterval: (query) => (query.state.data?.is_running ? 3000 : 20000),
  });

  const runMutation = useMutation({
    mutationFn: (limit: number) => api.triggerBaselineAudit(limit),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['baselineAuditStatus'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Loading baseline audit matrix...</p>
      </div>
    );
  }

  const isRunning = audit?.is_running || runMutation.isPending;
  const filteredGaps = (audit?.gaps || []).filter((gap) => {
    const matchesSev = filterSeverity === 'all' || gap.severity === filterSeverity;
    const matchesSearch =
      !searchQuery ||
      gap.policy_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      gap.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      gap.explanation.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSev && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Onboarding Baseline Regulatory Audit
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              Company Onboarding Core
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Comprehensive audit of all 102 FinCorp internal policies against 3,030 SEBI circulars via pgvector semantic similarity.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Audit"
          >
            <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
          <button
            disabled={isRunning}
            onClick={() => runMutation.mutate(5)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20"
          >
            <PlayCircle className="w-4 h-4" />
            <span>{isRunning ? 'Auditing in Background...' : 'Run Quick Audit (5 Policies)'}</span>
          </button>
        </div>
      </div>

      {/* Audit Summary Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border-cyan-500/20">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Audit Status</p>
          <div className="mt-2 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span className="text-xl font-bold text-white capitalize">{audit?.status || 'Completed'}</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Last run: {formatDate(audit?.last_run_at)}</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Policies Audited</p>
          <p className="mt-2 text-2xl font-black text-white">
            {audit?.audited_count} <span className="text-sm font-medium text-slate-400">/ {audit?.total_policies}</span>
          </p>
          <p className="mt-1 text-[11px] text-emerald-400 font-medium">{audit?.compliant_count} fully compliant</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border-rose-500/20">
          <p className="text-xs font-semibold uppercase tracking-wider text-rose-400">Non-Compliant Gaps</p>
          <p className="mt-2 text-2xl font-black text-rose-400">{audit?.gap_count}</p>
          <p className="mt-1 text-[11px] text-slate-400">
            {audit?.risk_breakdown.high} High, {audit?.risk_breakdown.medium} Med
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Overall Health Score</p>
          <p className="mt-2 text-2xl font-black text-cyan-300">{audit?.health_score}%</p>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-1.5 rounded-full"
              style={{ width: `${audit?.health_score || 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search gaps, policies, or SEBI circulars..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <span className="text-xs text-slate-400 font-medium">Severity:</span>
          {(['all', 'high', 'medium', 'low'] as const).map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors capitalize ${
                filterSeverity === sev
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Gap Matrix List */}
      <div className="space-y-4">
        {filteredGaps.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-white">No compliance gaps found for this filter</h4>
            <p className="text-xs text-slate-400 mt-1">All filtered internal policies conform to SEBI circulars.</p>
          </div>
        ) : (
          filteredGaps.map((gap) => {
            const sevBadge = getSeverityBadge(gap.severity);
            return (
              <div
                key={gap.check_id}
                className="glass-card p-5 rounded-2xl border-slate-800 hover:border-slate-700 transition-all"
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-sm font-bold text-white hover:text-cyan-300 transition-colors cursor-pointer" onClick={() => navigate(`/explain/${gap.check_id}`)}>
                        {gap.policy_title}
                      </h4>
                      <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[10px] text-slate-400 font-medium">
                        {gap.category}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border text-[10px] font-semibold ${sevBadge.bg}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sevBadge.dot}`}></span>
                        {sevBadge.label}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                      <span className="font-semibold text-rose-400">Regulatory Gap: </span>
                      {gap.explanation}
                    </p>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 shrink-0">
                    <button
                      onClick={() => navigate(`/explain/${gap.check_id}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/30 text-cyan-400 text-xs font-semibold transition-all"
                    >
                      <span>Explain Audit</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Conf: {Math.round(gap.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
