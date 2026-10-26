import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  Plus,
  Search,
  Filter,
  Layers,
  Calendar,
  CheckCircle2,
  X,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { formatDate } from '../lib/utils';
import type { CompanyPolicy } from '../types';

export const Policies: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [search, setSearch] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Form State
  const [formTitle, setFormTitle] = useState('');
  const [formCategory, setFormCategory] = useState('KYC & Client Onboarding');
  const [formText, setFormText] = useState('');
  const [formMetric, setFormMetric] = useState('');
  const [formValue, setFormValue] = useState<string>('');
  const [formUnit, setFormUnit] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['companyPolicies', selectedCategory, search],
    queryFn: () => api.getPolicies(undefined, selectedCategory, search),
  });

  const createMutation = useMutation({
    mutationFn: (newPolicy: Partial<CompanyPolicy>) => api.createPolicy(newPolicy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companyPolicies'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setIsModalOpen(false);
      // Reset form
      setFormTitle('');
      setFormText('');
      setFormMetric('');
      setFormValue('');
      setFormUnit('');
    },
  });

  const handleCreatePolicy = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      title: formTitle,
      category: formCategory,
      policy_text: formText,
      metric_name: formMetric || undefined,
      value: formValue ? parseFloat(formValue) : undefined,
      unit: formUnit || undefined,
    });
  };

  const categories = data?.categories || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Internal Company Policies
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
              FinCorp Securities
            </span>
          </div>
          <p className="text-xs text-slate-400">
            102 active policies continuously cross-referenced against SEBI directives with pgvector embeddings.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-cyan-500/20 shrink-0 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add Internal Policy</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search policy title or clauses..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
              selectedCategory === 'all'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Policies Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          Loading internal policies...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(data?.policies || []).map((policy) => (
            <div
              key={policy.id}
              className="glass-card p-5 rounded-2xl flex flex-col justify-between border-slate-800 hover:border-slate-700"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[10px] text-cyan-400 font-medium">
                    {policy.category}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    ID #{policy.id}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white mb-2 line-clamp-1">
                  {policy.title}
                </h4>
                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4">
                  {policy.policy_text}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                {policy.metric_name ? (
                  <span className="font-mono text-cyan-300 font-medium">
                    {policy.metric_name}: {policy.value} {policy.unit || ''}
                  </span>
                ) : (
                  <span className="text-slate-400">{policy.applies_to || 'General'}</span>
                )}
                <span className="text-slate-400">{formatDate(policy.effective_date)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Policy Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel bg-slate-950/95 border-slate-800 w-full max-w-lg rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white">Create Internal Policy</h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePolicy} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Policy Title</label>
                <input
                  required
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="e.g. Voluntary Aadhaar e-KYC and OVD Policy"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Category</label>
                <select
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="KYC & Client Onboarding">KYC & Client Onboarding</option>
                  <option value="Margin & Collateral Management">Margin & Collateral Management</option>
                  <option value="Cyber Security & IT Risk">Cyber Security & IT Risk</option>
                  <option value="Investor Grievance Redressal">Investor Grievance Redressal</option>
                  <option value="Dealing & Execution">Dealing & Execution</option>
                  <option value="Code of Conduct & Insider Trading">Code of Conduct & Insider Trading</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Policy Directive Text</label>
                <textarea
                  required
                  rows={4}
                  value={formText}
                  onChange={(e) => setFormText(e.target.value)}
                  placeholder="Describe the mandatory compliance requirement, procedures, and operational thresholds..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Metric Key</label>
                  <input
                    type="text"
                    value={formMetric}
                    onChange={(e) => setFormMetric(e.target.value)}
                    placeholder="e.g. scores_atr_days"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Value</label>
                  <input
                    type="number"
                    value={formValue}
                    onChange={(e) => setFormValue(e.target.value)}
                    placeholder="e.g. 21"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">Unit</label>
                  <input
                    type="text"
                    value={formUnit}
                    onChange={(e) => setFormUnit(e.target.value)}
                    placeholder="e.g. days / %"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Generating Embedding...' : 'Save & Vectorize'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
