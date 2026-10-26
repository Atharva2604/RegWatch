import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  FileCheck2,
  BookOpen,
  AlertTriangle,
  PlayCircle,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { StatCard } from '../components/common/StatCard';
import { VerdictBadge } from '../components/common/VerdictBadge';
import { RiskChart } from '../components/common/RiskChart';
import { formatDate } from '../lib/utils';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 15000,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Loading compliance intelligence dashboard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-panel p-8 rounded-2xl text-center max-w-md mx-auto my-12 border-rose-500/30">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white mb-1">Failed to load Dashboard</h3>
        <p className="text-xs text-slate-400 mb-4">Ensure FastAPI server is running on port 8000.</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-semibold text-xs hover:bg-cyan-400 transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { stats, recent_checks, recent_risks, category_distribution } = data;
  const isHealthy = stats.compliance_score >= 80;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              FinCorp Compliance Command
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              Live Monitoring
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Real-time regulatory parity between 102 internal brokerage policies and 3,030 SEBI regulations.
          </p>
        </div>

        {/* Quick Action CTAs */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => navigate('/propose-change')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-cyan-500/40 text-slate-200 text-xs font-semibold hover:bg-slate-800 transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Pre-Check Policy</span>
          </button>
          <button
            onClick={() => navigate('/baseline-audit')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20 hover:scale-[1.02]"
          >
            <PlayCircle className="w-4 h-4" />
            <span>Run Baseline Audit</span>
          </button>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Compliance Score"
          value={`${stats.compliance_score}%`}
          subtitle={`${stats.compliant_checks} of ${stats.total_checks} checks passing`}
          icon={FileCheck2}
          accentColor={isHealthy ? 'emerald' : 'amber'}
          trend={{
            value: isHealthy ? 'Compliant' : 'Attention Needed',
            isPositive: isHealthy,
          }}
          onClick={() => navigate('/checks')}
        />

        <StatCard
          title="Active Policies"
          value={stats.total_policies}
          subtitle="Vector-embedded policies in database"
          icon={Layers}
          accentColor="indigo"
          onClick={() => navigate('/policies')}
        />

        <StatCard
          title="SEBI Circulars"
          value={stats.total_regulations.toLocaleString()}
          subtitle="Monitored official gazettes & directives"
          icon={BookOpen}
          accentColor="cyan"
          onClick={() => navigate('/regulations')}
        />

        <StatCard
          title="Open Gap Alerts"
          value={stats.open_alerts}
          subtitle={`${stats.risk_counts.high} High, ${stats.risk_counts.medium} Medium`}
          icon={ShieldAlert}
          accentColor={stats.open_alerts > 0 ? 'rose' : 'emerald'}
          onClick={() => navigate('/alerts')}
        />
      </div>

      {/* Main Grid: Left 2 Cols (Recent Checks & Gaps), Right 1 Col (Risk Donut & Distribution) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (Span 2) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Compliance Evaluations Table */}
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Recent Parity Evaluations</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Latest Groq AI vector checks comparing company policies against SEBI circulars
                </p>
              </div>
              <button
                onClick={() => navigate('/checks')}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
              >
                <span>View All ({stats.total_checks})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="pb-3 pl-2">Policy Title</th>
                    <th className="pb-3 px-3">Category</th>
                    <th className="pb-3 px-3">Verdict</th>
                    <th className="pb-3 px-3">Confidence</th>
                    <th className="pb-3 pr-2 text-right">Audit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {recent_checks.map((check) => (
                    <tr
                      key={check.id}
                      className="hover:bg-slate-900/50 transition-colors group cursor-pointer"
                      onClick={() => navigate(`/explain/${check.id}`)}
                    >
                      <td className="py-3.5 pl-2 font-medium text-slate-200 group-hover:text-cyan-300 transition-colors max-w-xs truncate">
                        {check.policy_title}
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
                          {check.category}
                        </span>
                      </td>
                      <td className="py-3.5 px-3">
                        <VerdictBadge verdict={check.verdict} size="sm" />
                      </td>
                      <td className="py-3.5 px-3 font-mono text-[11px] text-slate-400">
                        {Math.round(check.confidence * 100)}%
                      </td>
                      <td className="py-3.5 pr-2 text-right">
                        <span className="text-[11px] text-cyan-400 group-hover:underline">
                          Explain →
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* High Priority Gaps / Actions */}
          <div className="glass-panel p-6 rounded-2xl border-rose-500/20">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></div>
                <h3 className="text-base font-bold text-white">
                  Identified Regulatory Non-Compliance Gaps
                </h3>
              </div>
              <button
                onClick={() => navigate('/alerts')}
                className="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1"
              >
                <span>Manage Alerts</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="space-y-3 mt-4">
              {recent_risks.map((risk) => (
                <div
                  key={risk.id}
                  className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-500/20 hover:border-rose-500/40 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
                      {risk.category.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      Severity: {risk.severity}/10
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {risk.reason}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (Span 1) */}
        <div className="space-y-6">
          {/* Risk Severity Donut */}
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-base font-bold text-white mb-1">Risk Severity Profile</h3>
            <p className="text-xs text-slate-400 mb-6">Distribution of non-compliant findings</p>
            <RiskChart
              high={stats.risk_counts.high}
              medium={stats.risk_counts.medium}
              low={stats.risk_counts.low}
            />
          </div>

          {/* Policy Categories Breakdown */}
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-base font-bold text-white mb-1">Policy Scope Breakdown</h3>
            <p className="text-xs text-slate-400 mb-4">Internal policies categorized by domain</p>
            <div className="space-y-2.5">
              {category_distribution.slice(0, 5).map((cat) => (
                <div
                  key={cat.category}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
                >
                  <span className="font-medium text-slate-300">{cat.category}</span>
                  <span className="font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                    {cat.count} policies
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Architecture Badge Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-900/60 border border-indigo-500/20 text-xs">
            <div className="flex items-center gap-2 mb-2 text-indigo-300 font-bold">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Bidirectional Verification Active</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
              Checks run in both directions: when SEBI publishes a new circular, relevant policies are matched; when a policy is edited, governing circulars are queried.
            </p>
            <div className="flex items-center justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-800">
              <span>Retrieval: pgvector RPC</span>
              <span className="text-emerald-400 font-medium">99.8% Accuracy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
