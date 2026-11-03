import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  MailCheck,
  CheckCircle2,
  XCircle,
  Send,
  Edit2,
  RefreshCw,
  Building,
  Calendar,
  Layers,
  Sparkles,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

import { apiClient } from '../api/client';
import { Badge } from '../components/Badge';
import { Pagination } from '../components/Pagination';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ConfirmModal } from '../components/ConfirmModal';
import { FollowUpDraft } from '../types';

const TABS = [
  { key: 'pending_approval', label: 'Pending Approval' },
  { key: 'approved', label: 'Approved' },
  { key: 'simulated_sent', label: 'Simulated Sent' },
  { key: 'rejected', label: 'Rejected' },
  { key: 'all', label: 'All Drafts' },
];

export const FollowUpCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState('pending_approval');
  const [skip, setSkip] = useState(0);
  const [limit] = useState(10);
  const [expandedDraftId, setExpandedDraftId] = useState<string | null>(null);

  // Edit State
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);
  const [editBody, setEditBody] = useState('');

  // Reject Modal State
  const [rejectDraftId, setRejectDraftId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('Requires tone adjustment and updated pricing');

  // Queries
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['drafts', activeTab, skip, limit],
    queryFn: () =>
      apiClient.getDrafts({
        skip,
        limit,
        status: activeTab,
      }),
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id: string) => apiClient.approveDraft(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      queryClient.invalidateQueries({ queryKey: ['analyticsOverview'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      apiClient.rejectDraft(id, reason),
    onSuccess: () => {
      setRejectDraftId(null);
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
    },
  });

  const simulateSendMutation = useMutation({
    mutationFn: (id: string) => apiClient.simulateSend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      queryClient.invalidateQueries({ queryKey: ['analyticsOverview'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: string }) =>
      apiClient.updateDraft(id, { body }),
    onSuccess: () => {
      setEditingDraftId(null);
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: (leadId: string) => apiClient.startAgentRun(leadId, 'RegenerateButton'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
    },
  });

  const drafts = data?.items || [];

  return (
    <div className="page-light space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Outreach & Follow-Up Center</h1>
        <p className="page-description">
          Human-in-the-loop managerial review, AI draft approval, and sandbox simulation
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto border-b border-[#e7e9f4]">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => {
              setActiveTab(tab.key);
              setSkip(0);
            }}
            aria-pressed={activeTab === tab.key}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-all ${
              activeTab === tab.key
                ? 'border-indigo-500 text-indigo-700'
                : 'border-transparent text-[#77819d] hover:text-[#394665]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingSpinner size="md" label="Loading drafts..." className="py-16" />
      ) : drafts.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-400 bg-slate-800/40 rounded-xl border border-slate-700">
          No drafts found in the '{activeTab.replace('_', ' ')}' category.
        </div>
      ) : (
        <div className="space-y-4">
          {drafts.map((draft: FollowUpDraft) => {
            const isExpanded = expandedDraftId === draft.id;
            const isEditing = editingDraftId === draft.id;

            return (
              <div
                key={draft.id}
                className="surface-card space-y-3 p-4 transition-all sm:p-5"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-bold text-[#263251]">{draft.lead_name || 'Prospect'}</span>
                    <span className="text-xs text-slate-400">({draft.lead_company || 'Company'})</span>
                    <Badge
                      variant={
                        draft.status === 'approved'
                          ? 'success'
                          : draft.status === 'simulated_sent'
                          ? 'info'
                          : draft.status === 'rejected'
                          ? 'danger'
                          : 'warning'
                      }
                      size="sm"
                    >
                      {draft.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </div>

                  <div className="flex items-center space-x-3 text-xs text-slate-400">
                    <span>{new Date(draft.created_at).toLocaleDateString()}</span>
                    <button
                      onClick={() => setExpandedDraftId(isExpanded ? null : draft.id)}
                      aria-label={`${isExpanded ? 'Collapse' : 'Expand'} draft details`}
                      aria-expanded={isExpanded}
                      className="p-1 text-slate-400 hover:text-white"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Subject */}
                {draft.subject && (
                  <div className="text-xs font-semibold text-indigo-300">
                    Subject: {draft.subject}
                  </div>
                )}

                {/* Body Preview / Full view */}
                {isEditing ? (
                  <div className="space-y-2">
                    <textarea
                      rows={6}
                      value={editBody}
                      onChange={(e) => setEditBody(e.target.value)}
                      className="control-field w-full p-3 text-xs"
                    />
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => setEditingDraftId(null)}
                        className="px-3 py-1.5 bg-slate-700 text-xs text-slate-300 rounded"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => updateMutation.mutate({ id: draft.id, body: editBody })}
                        className="px-3 py-1.5 bg-indigo-600 text-xs text-white rounded font-medium"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                ) : (
                  <p
                    className={`text-xs text-slate-300 whitespace-pre-wrap ${
                      isExpanded ? '' : 'line-clamp-3'
                    }`}
                  >
                    {draft.body}
                  </p>
                )}

                {/* Expanded Details: RAG Evidence & Personalization */}
                {isExpanded && (
                  <div className="mt-4 pt-3 border-t border-slate-700/80 space-y-3 text-xs">
                    {draft.source_references && draft.source_references.length > 0 && (
                      <div>
                        <span className="font-semibold text-slate-300 block mb-1">
                          Knowledge Base Citations:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {draft.source_references.map((ref, idx) => (
                            <div
                              key={idx}
                              className="max-w-sm rounded-xl border border-[#e5e5f6] bg-[#f8f7ff] px-3 py-2"
                            >
                              <span className="block text-[11px] font-semibold text-[#5a55b8]">{ref.document_name}</span>
                              <span className="mt-1 block text-[10px] leading-4 text-[#74809b]">{ref.excerpt}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {draft.rationale && (
                      <p className="text-[11px] text-slate-400 italic">
                        Strategic Rationale: {draft.rationale}
                      </p>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-700/60">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => navigate(`/leads/${draft.lead_id}`)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      View Lead Context
                    </button>
                    <span>•</span>
                    <button
                      onClick={() => regenerateMutation.mutate(draft.lead_id)}
                      disabled={regenerateMutation.isPending}
                      className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>Regenerate Draft</span>
                    </button>
                  </div>

                  <div className="flex items-center space-x-2">
                    {draft.status === 'pending_approval' && (
                      <>
                        <button
                          onClick={() => {
                            setEditingDraftId(draft.id);
                            setEditBody(draft.body);
                          }}
                          className="button-secondary px-3 py-1.5 text-xs"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>
                        <button
                          onClick={() => setRejectDraftId(draft.id)}
                          className="inline-flex items-center gap-1 rounded-xl bg-rose-600 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-rose-500"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                        <button
                          onClick={() => approveMutation.mutate(draft.id)}
                          className="inline-flex items-center gap-1 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-500"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                      </>
                    )}

                    {draft.status === 'approved' && (
                      <button
                        onClick={() => simulateSendMutation.mutate(draft.id)}
                        className="button-primary"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Simulate Send (Demo Mode)</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {data && data.total > limit && (
            <Pagination
              total={data.total}
              skip={skip}
              limit={limit}
              onPageChange={(newSkip) => setSkip(newSkip)}
            />
          )}
        </div>
      )}

      {/* Reject Confirmation */}
      <ConfirmModal
        isOpen={!!rejectDraftId}
        title="Reject SDR Follow-Up Draft"
        message="Are you sure you want to reject this draft? It will be archived and flagged for the account rep."
        confirmLabel="Confirm Rejection"
        variant="danger"
        onConfirm={() => {
          if (rejectDraftId) {
            rejectMutation.mutate({ id: rejectDraftId, reason: rejectReason });
          }
        }}
        onCancel={() => setRejectDraftId(null)}
      />
    </div>
  );
};
