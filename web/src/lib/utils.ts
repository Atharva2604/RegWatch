import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr?: string): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }).format(d);
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  } catch {
    return dateStr;
  }
}

export function getSeverityBadge(severity?: string) {
  const s = (severity || 'low').toLowerCase();
  switch (s) {
    case 'high':
    case 'critical':
      return {
        bg: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
        dot: 'bg-rose-500',
        label: 'High Severity',
      };
    case 'medium':
      return {
        bg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
        dot: 'bg-amber-500',
        label: 'Medium Severity',
      };
    case 'low':
    default:
      return {
        bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
        dot: 'bg-emerald-500',
        label: 'Low Severity',
      };
  }
}
