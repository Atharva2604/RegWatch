import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  AlertOctagon,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Check,
  ArrowRight,
  Filter,
  Layers,
  Sparkles,
  FileText,
  ShieldAlert,
  X,
  Lock,
} from 'lucide-react';
import { api } from '../lib/api';
import { getSeverityBadge, formatDateTime } from '../lib/utils';
import type { Alert, AlertOverrideRequest } from '../types';

export const Alerts: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  // CCO Override Modal State
  const [selectedAlertForOverride, setSelectedAlertForOverride] = useState<Alert | null>(null);
  const [legalOpinion, setLegalOpinion] = useState<string>('');
  const [boardResolutionNumber, setBoardResolutionNumber] = useState<string>('');
  const [signerName, setSignerName] = useState<string>('Chief Compliance Officer');
  const [overrideError, setOverrideError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', statusFilter, severityFilter],
    queryFn: () =>
      api.getAlerts(
        undefined,
        statusFilter === 'all' ? undefined : statusFilter,
        severityFilter === 'all' ? undefined : severityFilter
      ),
  });

  const ackMutation = useMutation({
    mutationFn: (id: string | number) => api.acknowledgeAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (id: string | number) => api.resolveAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
    },
  });

  const overrideMutation = useMutation({
    mutationFn: (payload: { id: string | number; req: AlertOverrideRequest }) =>
      api.overrideAlert(payload.id, payload.req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      queryClient.invalidateQueries({ queryKey: ['auditEvents'] });
      setSelectedAlertForOverride(null);
      setLegalOpinion('');
      setBoardResolutionNumber('');
      setOverrideError(null);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to submit CCO override';
      setOverrideError(msg);
    },
  });

  const handleOpenOverrideModal = (alert: Alert) => {
    setSelectedAlertForOverride(alert);
    setOverrideError(null);
    setLegalOpinion(
      `Formal Legal Opinion under SEBI (Stock Brokers) Regulations: Having reviewed the governing circular and the operational controls in place under Board Oversight, an exemption is recorded based on Board Resolution ${boardResolutionNumber || 'BR-2026/04'} and verified counsel advice confirming equivalence of compensatory risk mitigation.`
    );
    setBoardResolutionNumber('BR-2026/04-A');
  };

  const handleSubmitOverride = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAlertForOverride) return;
    if (!legalOpinion.trim()) {
      setOverrideError('Legal opinion or board resolution justification is required.');
      return;
    }

    overrideMutation.mutate({
      id: selectedAlertForOverride.id,
      req: {
        legal_opinion: legalOpinion.trim(),
        board_resolution_number: boardResolutionNumber.trim() || undefined,
        signer_name: signerName.trim() || 'Chief Compliance Officer',
        exemption_type: 'board_approved_exemption',
      },
    });
  };

  const alerts = data?.alerts || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Regulatory Alert Queue
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
              Active Gaps & CCO Defense
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Triage, acknowledge, resolve, or attach CCO legal exemptions across FinCorp internal policies.
          </p>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Status Pills */}
          <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
            {(['all', 'open', 'acknowledged', 'resolved', 'exempted'] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-colors ${
                  statusFilter === s
                    ? 'bg-cyan-500/20 text-cyan-300 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Severity Pills */}
          <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
            {(['all', 'high', 'medium', 'low'] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-colors ${
                  severityFilter === sev
                    ? 'bg-rose-500/20 text-rose-300 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts Stream */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          Loading alert queue...
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass-panel p-16 rounded-2xl text-center">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white mb-1">All Clear — No Open Alerts</h3>
          <p className="text-xs text-slate-400">All evaluated policies are currently conforming or exempted under CCO defense.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => {
            const sev = getSeverityBadge(alert.severity);
            const isAck = alert.status === 'acknowledged';
            const isResolved = alert.status === 'resolved';
            const isExempted = alert.status === 'exempted';

            return (
              <div
                key={alert.id}
                className={`glass-card p-5 rounded-2xl border-slate-800 hover:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all ${
                  isExempted ? 'border-purple-500/30 bg-purple-950/10' : ''
                }`}
              >
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border text-[10px] font-semibold ${sev.bg}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${sev.dot}`}></span>
                      {sev.label}
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[10px] text-slate-400">
                      {alert.category || 'Compliance'}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {formatDateTime(alert.created_at)}
                    </span>
                    {isExempted && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-500/15 border border-purple-500/40 text-[10px] font-bold text-purple-300">
                        <ShieldCheck className="w-3 h-3 text-purple-400" />
                        CCO Exemption Signed
                      </span>
                    )}
                  </div>

                  <h4 className="text-sm font-bold text-white">
                    {alert.title}
                  </h4>

                  <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
                    {alert.description}
                  </p>

                  {alert.policy_title && (
                    <div className="flex items-center gap-2 pt-1 text-[11px] text-slate-400">
                      <span className="font-semibold text-slate-400">Impacted Policy:</span>
                      <span className="text-cyan-400 font-medium">{alert.policy_title}</span>
                    </div>
                  )}

                  {/* CCO Audit Defense Attached Callout */}
                  {isExempted && alert.legal_opinion && (
                    <div className="mt-2 p-3 rounded-xl bg-purple-900/20 border border-purple-500/20 text-xs space-y-1">
                      <div className="flex items-center gap-2 text-[11px] font-bold text-purple-300">
                        <Lock className="w-3 h-3 text-purple-400" />
                        <span>Signed CCO Legal Defense</span>
                        {alert.board_resolution_number && (
                          <span className="px-1.5 py-0.2 rounded bg-purple-950 border border-purple-700/50 text-purple-200 font-mono text-[10px]">
                            {alert.board_resolution_number}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-300 text-[11px] italic">
                        "{alert.legal_opinion}"
                      </p>
                      {alert.exemption_signer && (
                        <div className="text-[10px] text-slate-400 pt-1">
                          Signatory: <span className="text-purple-300 font-medium">{alert.exemption_signer}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap sm:flex-col items-center sm:items-end gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
                  <div className="flex items-center gap-2">
                    {!isResolved && !isExempted && !isAck && (
                      <button
                        onClick={() => ackMutation.mutate(alert.id)}
                        disabled={ackMutation.isPending}
                        className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-semibold transition-colors"
                      >
                        Acknowledge
                      </button>
                    )}
                    {!isResolved && !isExempted && (
                      <>
                        <button
                          onClick={() => resolveMutation.mutate(alert.id)}
                          disabled={resolveMutation.isPending}
                          className="px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition-colors flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Resolve</span>
                        </button>

                        {/* CCO Override Button */}
                        <button
                          onClick={() => handleOpenOverrideModal(alert)}
                          className="px-3 py-1.5 rounded-xl bg-purple-500/15 hover:bg-purple-500/25 border border-purple-500/40 text-purple-300 text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm"
                          title="Attach Chief Compliance Officer legal opinion or board resolution exemption"
                        >
                          <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                          <span>CCO Override</span>
                        </button>
                      </>
                    )}
                    {isResolved && (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-semibold px-2.5 py-1 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Resolved</span>
                      </span>
                    )}
                    {isExempted && (
                      <span className="inline-flex items-center gap-1 text-xs text-purple-300 font-semibold px-2.5 py-1 bg-purple-500/10 rounded-lg border border-purple-500/30">
                        <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                        <span>Exempted</span>
                      </span>
                    )}
                  </div>

                  {alert.compliance_check_id && (
                    <button
                      onClick={() => navigate(`/explain/${alert.compliance_check_id}`)}
                      className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold transition-colors"
                    >
                      <span>Explain Audit Trace</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* CCO Exemption Override Modal */}
      {selectedAlertForOverride && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="glass-panel w-full max-w-2xl p-6 rounded-2xl border-purple-500/40 bg-slate-900/95 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  <ShieldCheck className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Chief Compliance Officer (CCO) Override</h3>
                  <p className="text-xs text-slate-400">Attach formal legal opinion and sign immutable audit defense</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedAlertForOverride(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-slate-300">Target Gap:</div>
              <div className="text-white font-medium">{selectedAlertForOverride.title}</div>
              <div className="text-slate-400 line-clamp-2">{selectedAlertForOverride.description}</div>
            </div>

            {overrideError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span>{overrideError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Board Resolution Number / Regulatory Exemption Ref:
                </label>
                <input
                  type="text"
                  value={boardResolutionNumber}
                  onChange={(e) => setBoardResolutionNumber(e.target.value)}
                  placeholder="e.g. BR-2026/04-A or SEBI-NO-ACTION-LETTER-09"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Signatory Designation:
                </label>
                <input
                  type="text"
                  value={signerName}
                  onChange={(e) => setSignerName(e.target.value)}
                  placeholder="Chief Compliance Officer"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Legal Opinion & Justification for Exemption <span className="text-rose-400">*</span>:
                </label>
                <textarea
                  rows={4}
                  required
                  value={legalOpinion}
                  onChange={(e) => setLegalOpinion(e.target.value)}
                  placeholder="Detail the counsel advice, statutory interpretation, or compensatory controls justifying this exemption..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-purple-500 font-sans leading-relaxed"
                />
              </div>

              <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/20 text-[11px] text-purple-300 flex items-start gap-2">
                <Lock className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Legal Audit Trail:</strong> Submitting this exemption will update the AI verdict to <strong>exempted</strong>, compute an immutable SHA-256 tamper-evident digital signature, and record an indelible event in <code>audit_events</code> for regulatory inspection.
                </span>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedAlertForOverride(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideMutation.isPending}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-purple-600/30 flex items-center gap-1.5"
                >
                  {overrideMutation.isPending ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Signing Audit Defense...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4" />
                      <span>Sign Legal Defense & Exempt</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
