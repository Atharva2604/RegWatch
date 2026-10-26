import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Building2,
  Cpu,
  Users,
  Bell,
  CheckCircle2,
  Database,
  Shield,
  Key,
} from 'lucide-react';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'general' | 'engine' | 'team' | 'alerts'>('general');
  const [savedMessage, setSavedMessage] = useState(false);

  const handleSave = () => {
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 3000);
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800/80">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">
          Platform & Engine Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage regulatory scraping cadences, AI inference parameters, team access roles, and alert webhooks.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: 'general', label: 'Organization Profile', icon: Building2 },
          { id: 'engine', label: 'AI & Vector Engine', icon: Cpu },
          { id: 'team', label: 'Access Roles', icon: Users },
          { id: 'alerts', label: 'Notification Channels', icon: Bell },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === tab.id
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {savedMessage && (
        <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Configuration saved successfully.</span>
        </div>
      )}

      {/* Tab: Organization Profile */}
      {activeTab === 'general' && (
        <div className="glass-panel p-6 rounded-2xl space-y-4 text-xs">
          <h3 className="text-sm font-bold text-white mb-2">FinCorp Securities Information</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Company Legal Entity</label>
              <input
                type="text"
                defaultValue="FinCorp Securities Ltd"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">SEBI Registration Number</label>
              <input
                type="text"
                defaultValue="INZ00018932 (Stock Broker & DP)"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Industry Sector</label>
              <input
                type="text"
                defaultValue="Capital Markets & Retail Brokerage"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Primary Exchange Memberships</label>
              <input
                type="text"
                defaultValue="NSE, BSE, MCX"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200"
              />
            </div>
          </div>
          <div className="pt-3 flex justify-end">
            <button
              onClick={handleSave}
              className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs"
            >
              Save Profile
            </button>
          </div>
        </div>
      )}

      {/* Tab: AI & Vector Engine */}
      {activeTab === 'engine' && (
        <div className="glass-panel p-6 rounded-2xl space-y-4 text-xs">
          <h3 className="text-sm font-bold text-white mb-2">RegWatch Intelligence Subsystems</h3>
          <div className="space-y-3">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <p className="font-bold text-white">LLM Legal Synthesis Engine</p>
                <p className="text-[11px] text-slate-400">Groq LPU Hardware Acceleration (qwen/qwen3.8-27b)</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/30">
                Connected & Active
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <p className="font-bold text-white">Vector Similarity Engine</p>
                <p className="text-[11px] text-slate-400">Supabase pgvector (all-MiniLM-L6-v2, 384 dimensions)</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-[10px] font-bold border border-cyan-500/30">
                3,082 Total Vectors
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <p className="font-bold text-white">SEBI Gazette Scraper Cadence</p>
                <p className="text-[11px] text-slate-400">Automated GitHub Actions worker checks daily at 06:00 UTC</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold border border-indigo-500/30">
                Daily Sync
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Access Roles */}
      {activeTab === 'team' && (
        <div className="glass-panel p-6 rounded-2xl space-y-4 text-xs">
          <h3 className="text-sm font-bold text-white mb-2">Compliance Team Roles</h3>
          <div className="divide-y divide-slate-800">
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-bold text-white">Atharva S. (You)</p>
                <p className="text-[11px] text-slate-400">atharva@fincorp.example.com</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-cyan-500/15 text-cyan-300 text-[10px] font-bold border border-cyan-500/30">
                Admin / Chief Compliance Officer
              </span>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-bold text-white">Ramesh K.</p>
                <p className="text-[11px] text-slate-400">ramesh.k@fincorp.example.com</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 text-[10px] font-medium border border-slate-700">
                Compliance Officer
              </span>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <p className="font-bold text-white">External Audit Team (KPMG)</p>
                <p className="text-[11px] text-slate-400">audit-partner@kpmg.example.com</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 text-[10px] font-medium border border-slate-700">
                Read-Only Inspector
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Alerts & Webhooks */}
      {activeTab === 'alerts' && (
        <div className="glass-panel p-6 rounded-2xl space-y-4 text-xs">
          <h3 className="text-sm font-bold text-white mb-2">Notification Webhooks</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Slack Channel Webhook (High Severity Gaps)</label>
              <input
                type="text"
                placeholder="https://hooks.slack.com/services/..."
                defaultValue="https://hooks.slack.com/services/T00/B00/FinCorpAlerts"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200 font-mono text-[11px]"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Emergency Escalation Email</label>
              <input
                type="email"
                defaultValue="compliance-board@fincorp.example.com"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200"
              />
            </div>
          </div>
          <div className="pt-3 flex justify-end">
            <button
              onClick={handleSave}
              className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs"
            >
              Update Notification Routing
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
