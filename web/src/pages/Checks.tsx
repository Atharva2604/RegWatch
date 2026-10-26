import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  CheckSquare,
  Filter,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Cpu,
} from 'lucide-react';
import { api } from '../lib/api';
import { VerdictBadge } from '../components/common/VerdictBadge';
import { formatDateTime } from '../lib/utils';

export const Checks: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState<number>(1);
  const [verdictFilter, setVerdictFilter] = useState<string>('all');

  const { data, isLoading } = useQuery({
    queryKey: ['complianceChecks', page, verdictFilter],
    queryFn: () =>
      api.getComplianceChecks({
        page,
        limit: 15,
        verdict: verdictFilter === 'all' ? undefined : verdictFilter,
      }),
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Compliance Evaluation Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete historical audit log of every policy check executed by the RegWatch Groq LPU comparison engine.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2">
          {(['all', 'compliant', 'non_compliant'] as const).map((v) => (
            <button
              key={v}
              onClick={() => {
                setVerdictFilter(v);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-colors ${
                verdictFilter === v
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {v.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Ledger Table */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            Loading compliance checks...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4">Check ID</th>
                  <th className="py-3 px-3">Policy Evaluated</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Verdict</th>
                  <th className="py-3 px-3">Confidence</th>
                  <th className="py-3 px-3">Evaluation Method</th>
                  <th className="py-3 px-3">Timestamp</th>
                  <th className="py-3 px-4 text-right">Audit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(data?.checks || []).map((check) => (
                  <tr
                    key={check.id}
                    className="hover:bg-slate-900/50 transition-colors group cursor-pointer"
                    onClick={() => navigate(`/explain/${check.id}`)}
                  >
                    <td className="py-3.5 px-4 font-mono text-slate-400 text-[11px]">
                      #{check.id}
                    </td>
                    <td className="py-3.5 px-3 max-w-xs font-medium text-slate-200 group-hover:text-cyan-300 transition-colors line-clamp-1">
                      {check.policy_title}
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400">
                        {check.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <VerdictBadge verdict={check.verdict} size="sm" />
                    </td>
                    <td className="py-3.5 px-3 font-mono text-[11px] text-slate-400">
                      {Math.round(check.confidence * 100)}%
                    </td>
                    <td className="py-3.5 px-3 text-slate-400 font-mono text-[10px]">
                      {check.method || 'groq_llm_vector'}
                    </td>
                    <td className="py-3.5 px-3 text-slate-400 whitespace-nowrap">
                      {formatDateTime(check.created_at)}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <span className="text-[11px] text-cyan-400 group-hover:underline flex items-center justify-end gap-1 font-semibold">
                        <span>Audit</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Page {data?.page || 1} of {data?.pages || 1} ({data?.total || 0} checks)
          </span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono text-slate-300">{page}</span>
            <button
              disabled={!data?.pages || page >= data.pages}
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
