import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  Plus,
  Upload,
  ArrowUpDown,
  Building,
  Mail,
  Phone,
  Sparkles,
  X
} from 'lucide-react';

import { apiClient } from '../api/client';
import { Badge } from '../components/Badge';
import { Pagination } from '../components/Pagination';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Lead } from '../types';

const INDUSTRIES = [
  'All',
  'Technology',
  'Healthcare',
  'Finance',
  'Manufacturing',
  'Retail',
  'Education',
  'Real Estate',
  'Logistics',
  'Professional Services',
  'Media'
];

const STAGES = [
  'All',
  'Lead',
  'Prospect',
  'Qualified',
  'Proposal',
  'Negotiation',
  'Closed Won',
  'Closed Lost'
];

export const LeadsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [skip, setSkip] = useState(0);
  const [limit] = useState(15);
  const [search, setSearch] = useState('');
  const [industry, setIndustry] = useState('All');
  const [stage, setStage] = useState('All');
  const [priority, setPriority] = useState<string>(searchParams.get('priority') || 'All');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Modals state
  const [isNewLeadOpen, setIsNewLeadOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);

  // New lead form state
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company: '',
    title: '',
    industry: 'Technology',
    company_size: '51-200',
    sales_stage: 'Lead',
    budget_range: '$20k-$50k',
    purchase_timeline: '1-3 months',
    decision_maker_status: false,
    pain_points: '',
    business_need: '',
    product_interest: 'NexusFlow Sales Intelligence Cloud',
    engagement_score: 60.0
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['leads', skip, limit, search, industry, stage, priority, sortBy, sortOrder],
    queryFn: () =>
      apiClient.getLeads({
        skip,
        limit,
        search: search.trim() || undefined,
        industry: industry !== 'All' ? industry : undefined,
        sales_stage: stage !== 'All' ? stage : undefined,
        priority: priority !== 'All' ? priority : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  });

  const createMutation = useMutation({
    mutationFn: apiClient.createLead,
    onSuccess: (newLead) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setIsNewLeadOpen(false);
      navigate(`/leads/${newLead.id}`);
    },
  });

  const importMutation = useMutation({
    mutationFn: apiClient.importLeadsCsv,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setImportStatus(`Successfully imported ${res.imported_count} leads (${res.skipped_count} skipped duplicates).`);
      setTimeout(() => {
        setIsImportOpen(false);
        setImportStatus(null);
        setImportFile(null);
      }, 2000);
    },
    onError: (err: any) => {
      setImportStatus(`Import failed: ${err.message || 'File processing error'}`);
    }
  });

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  return (
    <div className="page-light space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Leads & Revenue Pipeline</h1>
          <p className="page-description">
            Intelligent scoring, feature attribution, and automated qualification
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button
            onClick={() => setIsImportOpen(true)}
            className="button-secondary"
          >
            <Upload className="w-3.5 h-3.5 text-slate-400" />
            <span>Import CSV</span>
          </button>

          <button
            onClick={() => setIsNewLeadOpen(true)}
            className="button-primary"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Lead</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 shadow-md space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name, company, or email..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSkip(0);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={priority}
              onChange={(e) => {
                setPriority(e.target.value);
                setSkip(0);
              }}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              <option value="All">All Priorities</option>
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
            </select>

            <select
              value={stage}
              onChange={(e) => {
                setStage(e.target.value);
                setSkip(0);
              }}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s === 'All' ? 'All Stages' : s}
                </option>
              ))}
            </select>

            <select
              value={industry}
              onChange={(e) => {
                setIndustry(e.target.value);
                setSkip(0);
              }}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              {INDUSTRIES.map((ind) => (
                <option key={ind} value={ind}>
                  {ind === 'All' ? 'All Industries' : ind}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div className="surface-card overflow-hidden">
        {isLoading ? (
          <LoadingSpinner size="md" label="Loading leads..." className="py-16" />
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No leads found matching your search and filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-xs">
              <thead className="bg-slate-850 text-slate-400 border-b border-slate-700 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Contact & Company</th>
                  <th className="px-4 py-3" aria-sort={sortBy === 'sales_stage' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}>
                    <button type="button" onClick={() => handleSort('sales_stage')} className="inline-flex items-center gap-1.5 rounded focus:outline-none focus:ring-2 focus:ring-indigo-200" aria-label={`Sort by stage${sortBy === 'sales_stage' ? `, ${sortOrder}ending` : ''}`}>
                      <span>Stage</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </button>
                  </th>
                  <th className="px-4 py-3" aria-sort={sortBy === 'engagement_score' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}>
                    <button type="button" onClick={() => handleSort('engagement_score')} className="inline-flex items-center gap-1.5 rounded focus:outline-none focus:ring-2 focus:ring-indigo-200" aria-label={`Sort by engagement${sortBy === 'engagement_score' ? `, ${sortOrder}ending` : ''}`}>
                      <span>Engagement</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </button>
                  </th>
                  <th className="py-3 px-4">Priority Score</th>
                  <th className="py-3 px-4">ML Win Prob</th>
                  <th className="py-3 px-4">Timeline / Budget</th>
                  <th className="py-3 px-4 text-right">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {data.items.map((lead: Lead) => {
                  const probPercent = Math.round((lead.conversion_probability || 0) * 100);
                  const prio = lead.priority_category || 'low';

                  return (
                    <tr
                      key={lead.id}
                      onClick={() => navigate(`/leads/${lead.id}`)}
                      className="hover:bg-slate-750/50 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">
                          {lead.first_name} {lead.last_name}
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center space-x-1 mt-0.5">
                          <Building className="w-3 h-3" />
                          <span>{lead.company}</span>
                          <span>•</span>
                          <span>{lead.title}</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            lead.sales_stage === 'Closed Won'
                              ? 'success'
                              : lead.sales_stage === 'Closed Lost'
                              ? 'danger'
                              : lead.sales_stage === 'Negotiation' || lead.sales_stage === 'Proposal'
                              ? 'info'
                              : 'primary'
                          }
                          size="sm"
                        >
                          {lead.sales_stage}
                        </Badge>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="bg-teal-400 h-full rounded-full"
                              style={{ width: `${lead.engagement_score}%` }}
                            />
                          </div>
                          <span className="text-[11px] text-slate-300 font-medium">
                            {lead.engagement_score}
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <Badge
                          variant={prio === 'high' ? 'danger' : prio === 'medium' ? 'warning' : 'neutral'}
                          size="sm"
                        >
                          {prio.toUpperCase()} ({lead.priority_score || '--'})
                        </Badge>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <div className="h-1.5 w-14 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className={`h-full rounded-full ${
                                probPercent >= 60
                                  ? 'bg-emerald-400'
                                  : probPercent >= 40
                                  ? 'bg-amber-400'
                                  : 'bg-rose-400'
                              }`}
                              style={{ width: `${probPercent}%` }}
                            />
                          </div>
                          <span className="text-[11px] font-semibold text-slate-200">
                            {probPercent}%
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-slate-300 text-[11px]">
                        <div>{lead.purchase_timeline}</div>
                        <div className="text-slate-400">{lead.budget_range}</div>
                      </td>

                      <td className="py-3 px-4 text-right text-slate-400 text-[11px]">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data && data.total > 0 && (
          <div className="p-4 border-t border-slate-700">
            <Pagination
              total={data.total}
              skip={skip}
              limit={limit}
              onPageChange={(newSkip) => setSkip(newSkip)}
            />
          </div>
        )}
      </div>

      {/* New Lead Modal */}
      {isNewLeadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-700">
              <h3 className="text-sm font-bold text-white">Add New Inbound Lead</h3>
              <button type="button" aria-label="Close new lead form" onClick={() => setIsNewLeadOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate(formData as any);
              }}
              className="mt-4 space-y-4 text-xs"
            >
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-slate-300 mb-1">First Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Last Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-slate-300 mb-1">Email Address *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-slate-300 mb-1">Company Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Job Title *</label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div>
                  <label className="block text-slate-300 mb-1">Industry</label>
                  <select
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white"
                  >
                    {INDUSTRIES.filter((i) => i !== 'All').map((i) => (
                      <option key={i} value={i}>
                        {i}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Budget Range</label>
                  <select
                    value={formData.budget_range}
                    onChange={(e) => setFormData({ ...formData, budget_range: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white"
                  >
                    <option value="Under $5k">Under $5k</option>
                    <option value="$5k-$20k">$5k-$20k</option>
                    <option value="$20k-$50k">$20k-$50k</option>
                    <option value="$50k-$100k">$50k-$100k</option>
                    <option value="$100k+">$100k+</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Purchase Timeline</label>
                  <select
                    value={formData.purchase_timeline}
                    onChange={(e) => setFormData({ ...formData, purchase_timeline: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-white"
                  >
                    <option value="Immediate">Immediate</option>
                    <option value="1-3 months">1-3 months</option>
                    <option value="3-6 months">3-6 months</option>
                    <option value="6-12 months">6-12 months</option>
                    <option value="12+ months">12+ months</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="dm-check"
                  checked={formData.decision_maker_status}
                  onChange={(e) => setFormData({ ...formData, decision_maker_status: e.target.checked })}
                  className="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-0"
                />
                <label htmlFor="dm-check" className="text-slate-300 font-medium">
                  Contact is an authorized budget decision maker
                </label>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Pain Points Description</label>
                <textarea
                  rows={2}
                  value={formData.pain_points}
                  onChange={(e) => setFormData({ ...formData, pain_points: e.target.value })}
                  placeholder="e.g. Manual CRM data entry slows down team by 15 hours weekly..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-700">
                <button
                  type="button"
                  onClick={() => setIsNewLeadOpen(false)}
                  className="px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold"
                >
                  {createMutation.isPending ? 'Creating...' : 'Save & Analyze'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Import Modal */}
      {isImportOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-700">
              <h3 className="text-sm font-bold text-white">Import Leads via CSV</h3>
              <button type="button" aria-label="Close CSV import dialog" onClick={() => setIsImportOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <p className="text-slate-300">
                Upload a CSV containing lead attributes (first_name, last_name, email, company, title, industry, etc.).
              </p>

              <input
                type="file"
                accept=".csv"
                onChange={(e) => setImportFile(e.target.files ? e.target.files[0] : null)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-300"
              />

              {importStatus && (
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-700 text-indigo-400 font-medium">
                  {importStatus}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  onClick={() => setIsImportOpen(false)}
                  className="px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  disabled={!importFile || importMutation.isPending}
                  onClick={() => {
                    if (importFile) importMutation.mutate(importFile);
                  }}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg font-semibold"
                >
                  {importMutation.isPending ? 'Importing...' : 'Upload & Process'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
