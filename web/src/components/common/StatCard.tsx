import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  accentColor?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'indigo';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  accentColor = 'cyan',
  onClick,
}) => {
  const colorMap = {
    cyan: {
      iconBg: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
      glow: 'hover:shadow-[0_0_30px_-5px_rgba(6,182,212,0.2)]',
    },
    emerald: {
      iconBg: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      glow: 'hover:shadow-[0_0_30px_-5px_rgba(16,185,129,0.2)]',
    },
    amber: {
      iconBg: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      glow: 'hover:shadow-[0_0_30px_-5px_rgba(245,158,11,0.2)]',
    },
    rose: {
      iconBg: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
      glow: 'hover:shadow-[0_0_30px_-5px_rgba(244,63,94,0.2)]',
    },
    indigo: {
      iconBg: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
      glow: 'hover:shadow-[0_0_30px_-5px_rgba(99,102,241,0.2)]',
    },
  }[accentColor];

  return (
    <div
      onClick={onClick}
      className={cn(
        'glass-card p-5 rounded-2xl relative overflow-hidden transition-all duration-300',
        colorMap.glow,
        onClick && 'cursor-pointer hover:border-slate-600'
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {value}
            </span>
            {trend && (
              <span
                className={cn(
                  'text-xs font-semibold px-1.5 py-0.5 rounded',
                  trend.isPositive
                    ? 'text-emerald-400 bg-emerald-500/10'
                    : 'text-rose-400 bg-rose-500/10'
                )}
              >
                {trend.value}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-400 line-clamp-1">{subtitle}</p>
          )}
        </div>
        <div
          className={cn(
            'p-3 rounded-xl border flex items-center justify-center shrink-0',
            colorMap.iconBg
          )}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
