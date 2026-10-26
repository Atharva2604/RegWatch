import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Bell,
  Search,
  Building2,
  ChevronDown,
  Sparkles,
  ExternalLink,
  LogOut,
} from 'lucide-react';

interface NavbarProps {
  openAlertsCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ openAlertsCount = 0 }) => {
  const navigate = useNavigate();

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Left: Branding & Status Pulse */}
      <div className="flex items-center gap-6">
        <div
          onClick={() => navigate('/')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                RegWatch
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                PRO
              </span>
            </div>
            <p className="text-[10px] font-medium text-slate-400 -mt-0.5">
              Regulatory Compliance Intelligence
            </p>
          </div>
        </div>

        {/* Live SEBI Connection Indicator */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-medium text-[11px] text-slate-300">SEBI Scraper: 3,030 Circulars Synchronized</span>
        </div>
      </div>

      {/* Center: Search / Quick Actions */}
      <div className="hidden md:flex items-center relative max-w-sm w-full mx-4">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 pointer-events-none" />
        <input
          type="text"
          placeholder="Search SEBI circulars, internal policies, or audits (Ctrl + K)..."
          className="w-full bg-slate-900/60 border border-slate-800/80 rounded-xl pl-10 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
        />
      </div>

      {/* Right: Company Selector & User Profile */}
      <div className="flex items-center gap-4">
        {/* Company Dropdown Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-colors cursor-pointer">
          <div className="w-6 h-6 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Building2 className="w-3.5 h-3.5" />
          </div>
          <div className="text-left hidden sm:block">
            <p className="text-xs font-semibold text-slate-200">FinCorp Securities</p>
            <p className="text-[10px] text-slate-400">SEBI Broker #INZ00018932</p>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
        </div>

        {/* Alerts Bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all"
          title="Open Alerts"
        >
          <Bell className="w-4 h-4" />
          {openAlertsCount > 0 && (
            <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-slate-950"></span>
          )}
        </button>

        {/* User Avatar */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-md">
            AS
          </div>
          <div className="hidden xl:block text-left">
            <p className="text-xs font-semibold text-slate-200 leading-tight">Atharva S.</p>
            <p className="text-[10px] text-emerald-400 font-medium">Compliance Officer</p>
          </div>
        </div>
      </div>
    </header>
  );
};
