import React from 'react';
import { CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';

interface VerdictBadgeProps {
  verdict: 'compliant' | 'non_compliant' | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const VerdictBadge: React.FC<VerdictBadgeProps> = ({
  verdict,
  size = 'md',
  showIcon = true,
}) => {
  const isCompliant = verdict === 'compliant';

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  }[size];

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border transition-colors',
        sizeClasses,
        isCompliant
          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
      )}
    >
      {showIcon && (
        isCompliant ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        ) : (
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
        )
      )}
      <span>{isCompliant ? 'Compliant' : 'Non-Compliant'}</span>
    </span>
  );
};
