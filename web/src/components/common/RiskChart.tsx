import React from 'react';

interface RiskChartProps {
  high: number;
  medium: number;
  low: number;
}

export const RiskChart: React.FC<RiskChartProps> = ({ high, medium, low }) => {
  const total = high + medium + low || 1;
  const highPct = Math.round((high / total) * 100);
  const medPct = Math.round((medium / total) * 100);
  const lowPct = Math.round((low / total) * 100);

  // SVG circle circumference for r = 40
  const circumference = 2 * Math.PI * 40; // ~251.32

  const highOffset = circumference * (1 - high / total);
  const medOffset = circumference * (1 - (high + medium) / total);

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      {/* SVG Donut */}
      <div className="relative w-32 h-32 shrink-0 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="40"
            className="text-slate-800"
            strokeWidth="12"
            stroke="currentColor"
            fill="transparent"
          />
          {/* Low Risk segment (base) */}
          <circle
            cx="50"
            cy="50"
            r="40"
            className="text-emerald-500"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={0}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
          />
          {/* Medium Risk segment */}
          <circle
            cx="50"
            cy="50"
            r="40"
            className="text-amber-500 transition-all duration-700 ease-out"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={medOffset}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
          />
          {/* High Risk segment */}
          <circle
            cx="50"
            cy="50"
            r="40"
            className="text-rose-500 transition-all duration-700 ease-out"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={highOffset}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-black text-white">{total === 1 && high === 0 && medium === 0 && low === 0 ? 0 : total}</span>
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Findings</span>
        </div>
      </div>

      {/* Legend & Breakdown bars */}
      <div className="flex-1 space-y-3 w-full">
        {/* High Risk */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span>
              High Severity
            </span>
            <span className="font-semibold text-rose-400">{high} ({highPct}%)</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div className="bg-rose-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${highPct}%` }}></div>
          </div>
        </div>

        {/* Medium Risk */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
              Medium Severity
            </span>
            <span className="font-semibold text-amber-400">{medium} ({medPct}%)</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div className="bg-amber-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${medPct}%` }}></div>
          </div>
        </div>

        {/* Low Risk */}
        <div>
          <div className="flex justify-between items-center text-xs mb-1">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
              Low Severity
            </span>
            <span className="font-semibold text-emerald-400">{low} ({lowPct}%)</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
            <div className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${lowPct}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};
