import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ClipboardCheck,
  BookOpen,
  FileText,
  Sparkles,
  CheckSquare,
  AlertOctagon,
  History,
  Settings,
  Cpu,
  Layers,
  Database,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  openAlertsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ openAlertsCount = 0 }) => {
  const navItems = [
    {
      to: '/',
      label: 'Overview',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      to: '/baseline-audit',
      label: 'Baseline Audit',
      icon: ClipboardCheck,
      badge: 'Core',
      badgeColor: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    },
    {
      to: '/regulations',
      label: 'SEBI Circulars',
      icon: BookOpen,
      badge: '3,030',
      badgeColor: 'bg-slate-800 text-slate-300',
    },
    {
      to: '/policies',
      label: 'Internal Policies',
      icon: FileText,
      badge: '102',
      badgeColor: 'bg-slate-800 text-slate-300',
    },
    {
      to: '/propose-change',
      label: 'Pre-Change Impact',
      icon: Sparkles,
      badge: 'AI Precheck',
      badgeColor: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    },
    {
      to: '/checks',
      label: 'Compliance Checks',
      icon: CheckSquare,
      badge: null,
    },
    {
      to: '/alerts',
      label: 'Alert Queue',
      icon: AlertOctagon,
      badge: openAlertsCount > 0 ? `${openAlertsCount} Open` : null,
      badgeColor: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    },
    {
      to: '/events',
      label: 'Audit Trail',
      icon: History,
      badge: null,
    },
    {
      to: '/settings',
      label: 'Platform Settings',
      icon: Settings,
      badge: null,
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/60 backdrop-blur-xl shrink-0 flex flex-col justify-between p-4 hidden md:flex">
      {/* Navigation Group */}
      <div className="space-y-6">
        <div>
          <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Monitoring & Audit
          </p>
          <nav className="space-y-1">
            {navItems.slice(0, 4).map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group',
                      isActive
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_-3px_rgba(6,182,212,0.2)]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                    )
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 shrink-0 transition-colors group-hover:text-cyan-400" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={cn(
                        'text-[10px] font-semibold px-2 py-0.5 rounded-full border border-transparent',
                        item.badgeColor
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div>
          <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Intelligence & Risk
          </p>
          <nav className="space-y-1">
            {navItems.slice(4).map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group',
                      isActive
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_-3px_rgba(6,182,212,0.2)]'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                    )
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 shrink-0 transition-colors group-hover:text-cyan-400" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={cn(
                        'text-[10px] font-semibold px-2 py-0.5 rounded-full border border-transparent',
                        item.badgeColor
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Engine Status Card in Sidebar Footer */}
      <div className="p-3.5 rounded-2xl bg-gradient-to-br from-slate-900/90 to-slate-950/80 border border-slate-800 text-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="flex items-center gap-1.5 font-bold text-slate-300 text-[11px]">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            Groq LPU Engine
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
        </div>
        <p className="text-[10px] text-slate-400 mb-2">
          Model: <span className="text-slate-300 font-mono">qwen-27b</span>
        </p>
        <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-800/80">
          <span className="flex items-center gap-1">
            <Database className="w-3 h-3 text-indigo-400" />
            pgvector
          </span>
          <span className="font-mono text-cyan-300 font-semibold">384 dims</span>
        </div>
      </div>
    </aside>
  );
};
