import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  History,
  FileText,
  AlertOctagon,
  ClipboardCheck,
  ShieldCheck,
  Filter,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDateTime } from '../lib/utils';
import type { AuditEvent } from '../types';

export const Events: React.FC = () => {
  const [filterEntity, setFilterEntity] = useState<string>('all');

  const { data, isLoading } = useQuery({
    queryKey: ['auditEvents'],
    queryFn: () => api.getAuditEvents(50),
    refetchInterval: 15000,
  });

  const events = (data?.events || []).filter((e) =>
    filterEntity === 'all' ? true : e.entity === filterEntity
  );

  const getEntityIcon = (entity: string) => {
    switch (entity) {
      case 'company_policy':
        return <FileText className="w-4 h-4 text-indigo-400" />;
      case 'alert':
        return <AlertOctagon className="w-4 h-4 text-rose-400" />;
      case 'baseline_audit':
        return <ClipboardCheck className="w-4 h-4 text-cyan-400" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-5 h-5 text-cyan-400" />
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Immutable Audit Trail
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Cryptographically tracked operational events, policy modifications, and compliance verdicts for regulatory inspections.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          {(['all', 'company_policy', 'alert', 'baseline_audit', 'compliance_check'] as const).map(
            (ent) => (
              <button
                key={ent}
                onClick={() => setFilterEntity(ent)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-colors ${
                  filterEntity === ent
                    ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {ent.replace('_', ' ')}
              </button>
            )
          )}
        </div>
      </div>

      {/* Timeline Stream */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          Loading audit trail...
        </div>
      ) : events.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl text-center">
          <Clock className="w-10 h-10 text-slate-500 mx-auto mb-2" />
          <p className="text-xs text-slate-400">No events found for this filter.</p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
          {events.map((evt) => (
            <div key={evt.id} className="relative group">
              {/* Dot */}
              <div className="absolute -left-[27px] top-1.5 w-6 h-6 rounded-full bg-slate-950 border-2 border-slate-700 flex items-center justify-center group-hover:border-cyan-400 transition-colors">
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              </div>

              {/* Event Card */}
              <div className="glass-panel p-4 rounded-2xl border-slate-800/80 hover:border-slate-700 transition-colors space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                      {getEntityIcon(evt.entity)}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white uppercase tracking-wider">
                        {evt.event_type.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] text-slate-500 ml-2 font-mono">
                        {evt.entity} #{evt.entity_id}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {formatDateTime(evt.created_at)}
                  </span>
                </div>

                {evt.payload && (
                  <pre className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-900 text-[11px] text-slate-300 font-mono overflow-x-auto">
                    {JSON.stringify(evt.payload, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
