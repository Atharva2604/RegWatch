import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BookOpen,
  Search,
  ExternalLink,
  Calendar,
  Building,
  FileText,
  ChevronLeft,
  ChevronRight,
  Filter,
  Eye,
  X,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDate } from '../lib/utils';
import type { Regulation } from '../types';

export const Regulations: React.FC = () => {
  const [page, setPage] = useState<number>(1);
  const [search, setSearch] = useState<string>('');
  const [searchInput, setSearchInput] = useState<string>('');
  const [selectedReg, setSelectedReg] = useState<Regulation | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['regulations', page, search],
    queryFn: () => api.getRegulations({ page, limit: 15, q: search }),
    placeholderData: (prev) => prev,
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  const handleViewDetails = async (id: number) => {
    try {
      const res = await api.getRegulation(id);
      setSelectedReg(res.regulation);
    } catch {
      // fallback
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            SEBI Regulatory Knowledge Base
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse and query 3,030 official SEBI circulars, master guidelines, and statutory directives with 384-dim semantic embeddings.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-400">
            Total Monitored: {data?.total?.toLocaleString() || '3,030'}
          </span>
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search circular title, reference number (e.g. SEBI/HO/MIRSD), or keywords..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
        <button
          type="submit"
          className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors shadow-sm"
        >
          Search
        </button>
        {search && (
          <button
            type="button"
            onClick={() => {
              setSearch('');
              setSearchInput('');
              setPage(1);
            }}
            className="px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white text-xs"
          >
            Clear
          </button>
        )}
      </form>

      {/* Regulations Table */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            Loading SEBI regulations...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4">Title & Reference</th>
                  <th className="py-3 px-3">Department</th>
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(data?.data || []).map((reg) => (
                  <tr
                    key={reg.id}
                    className="hover:bg-slate-900/50 transition-colors group cursor-pointer"
                    onClick={() => handleViewDetails(reg.id)}
                  >
                    <td className="py-3.5 px-4 max-w-md">
                      <p className="font-semibold text-slate-200 group-hover:text-cyan-300 transition-colors line-clamp-1">
                        {reg.title}
                      </p>
                      {reg.reference_number && (
                        <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                          {reg.reference_number}
                        </p>
                      )}
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400">
                        {reg.department || 'SEBI'}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-slate-400 whitespace-nowrap">
                      {formatDate(reg.published_date)}
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        Active
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewDetails(reg.id);
                        }}
                        className="p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors inline-flex items-center gap-1 text-[11px]"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
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
            Showing page {data?.page || 1} of {data?.pages || 1} ({data?.total || 0} circulars)
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

      {/* Regulation Inspector Modal */}
      {selectedReg && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel bg-slate-950/95 border-slate-800 w-full max-w-3xl rounded-2xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-start justify-between gap-4">
              <div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  {selectedReg.department || 'SEBI Official Circular'}
                </span>
                <h3 className="text-base font-bold text-white mt-1.5 leading-snug">
                  {selectedReg.title}
                </h3>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-400 font-mono">
                  {selectedReg.reference_number && <span>Ref: {selectedReg.reference_number}</span>}
                  <span>Date: {formatDate(selectedReg.published_date)}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedReg(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              <div>
                <h5 className="font-bold text-slate-300 uppercase tracking-wider text-[11px] mb-1.5">
                  Circular Content & Statutory Mandate
                </h5>
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800/80 font-mono text-slate-300 text-[11px] leading-relaxed max-h-72 overflow-y-auto whitespace-pre-wrap">
                  {selectedReg.content_text || 'Full statutory text indexed in vector store.'}
                </div>
              </div>

              {selectedReg.url && (
                <div className="pt-2">
                  <a
                    href={selectedReg.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-semibold transition-colors"
                  >
                    <span>View Official SEBI Gazette</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
