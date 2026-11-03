import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Building,
  Mail,
  Phone,
  Calendar,
  Sparkles,
  Bot,
  CheckCircle2,
  XCircle,
  Send,
  FileText,
  Clock,
  Layers,
  Award,
  ChevronDown,
  ChevronUp,
  AlertTriangle
} from 'lucide-react';

import { apiClient } from '../api/client';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ConfirmModal } from '../components/ConfirmModal';

export const LeadDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraftBody, setEditedDraftBody] = useState('');
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [isRunsOpen, setIsRunsOpen] = useState(false);

  // Queries
  const { data: lead, isLoading: isLeadLoading } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => apiClient.getLead(id!),
    enabled: !!id,
  });

  const { data: analysis, refetch: refetchAnalysis } = useQuery({
    queryKey: ['leadAnalysis', id],
    queryFn: () => apiClient.getLeadAnalysis(id!),
    enabled: !!id,
  });

  const { data: draftsData, refetch: refetchDrafts } = useQuery({
    queryKey: ['leadDrafts', id],
    queryFn: () => apiClient.getDrafts({ lead_id: id, limit: 1 }),
    enabled: !!id,
  });

  const { data: runsData, refetch: refetchRuns } = useQuery({
    queryKey: ['leadRuns', id],
    queryFn: () => apiClient.getAgentRuns({ lead_id: id, limit: 5 }),
    enabled: !!id,
  });

  // Start Agent Workflow Mutation
  const agentRunMutation = useMutation({
    mutationFn: () => apiClient.startAgentRun(id!, 'LeadDetailView'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      refetchAnalysis();
      refetchDrafts();
      refetchRuns();
    },
  });

  // Approve Draft Mutation
  const approveMutation = useMutation({
    mutationFn: (draftId: string) => apiClient.approveDraft(draftId),
    onSuccess: () => {
      refetchDrafts();
    },
  });

  // Reject Draft Mutation
  const rejectMutation = useMutation({
    mutationFn: ({ draftId, reason }: { draftId: string; reason: string }) =>
      apiClient.rejectDraft(draftId, reason),
    onSuccess: () => {
      setIsRejectModalOpen(false);
      refetchDrafts();
    },
  });

  // Simulate Send Mutation
  const simulateSendMutation = useMutation({
    mutationFn: (draftId: string) => apiClient.simulateSend(draftId),
    onSuccess: () => {
      refetchDrafts();
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
    },
  });

  // Update Draft Mutation
  const updateDraftMutation = useMutation({
    mutationFn: ({ draftId, body }: { draftId: string; body: string }) =>
      apiClient.updateDraft(draftId, { body }),
    onSuccess: () => {
      setIsEditingDraft(false);
      refetchDrafts();
    },
  });

  if (isLeadLoading || !lead) {
    return <LoadingSpinner size="lg" label="Loading lead intelligence profile..." className="min-h-[400px]" />;
  }

  const latestDraft = draftsData?.items && draftsData.items.length > 0 ? draftsData.items[0] : null;
  const probDisplay = lead.conversion_probability == null
    ? 'N/A'
    : `${Math.round(lead.conversion_probability * 100)}%`;

  return (
    <div className="space-y-6">
      {/* Back button & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/leads')}
          className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Leads</span>
        </button>

        <button
          onClick={() => agentRunMutation.mutate()}
          disabled={agentRunMutation.isPending}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-teal-500 hover:from-indigo-500 hover:to-teal-400 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/30 transition-all"
        >
          <Sparkles className="w-4 h-4" />
          <span>{agentRunMutation.isPending ? 'Running Agent State Machine...' : 'Analyze Lead with AI'}</span>
        </button>
      </div>

      {/* 3 Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (4 cols): Contact, Company, Engagement */}
        <div className="lg:col-span-4 space-y-6">
          {/* Contact Card */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 shadow-lg space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-base font-bold text-white">
                  {lead.first_name} {lead.last_name}
                </h2>
                <p className="text-xs text-indigo-400 font-medium">{lead.title}</p>
              </div>
              <Badge variant={lead.decision_maker_status ? 'success' : 'neutral'} size="sm">
                {lead.decision_maker_status ? 'Decision Maker' : 'Influencer'}
              </Badge>
            </div>

            <div className="space-y-2.5 text-xs border-t border-slate-700/60 pt-3 text-slate-300">
              <div className="flex items-center space-x-2.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span className="truncate">{lead.email}</span>
              </div>
              <div className="flex items-center space-x-2.5">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>{lead.phone || 'No phone recorded'}</span>
              </div>
              <div className="flex items-center space-x-2.5">
                <Building className="w-3.5 h-3.5 text-slate-400" />
                <span>{lead.company}</span>
              </div>
            </div>
          </div>

          {/* Company & Deal Profile */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 shadow-lg space-y-3 text-xs">
            <h3 className="font-semibold text-white border-b border-slate-700/60 pb-2">
              Commercial Deal Profile
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-slate-400 block text-[11px]">Industry</span>
                <span className="font-medium text-slate-200">{lead.industry}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Company Size</span>
                <span className="font-medium text-slate-200">{lead.company_size} emp</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Budget Tier</span>
                <span className="font-medium text-teal-400">{lead.budget_range}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Purchase Timeline</span>
                <span className="font-medium text-amber-400">{lead.purchase_timeline}</span>
              </div>
            </div>

            {lead.pain_points && (
              <div className="pt-2 border-t border-slate-700/60">
                <span className="text-slate-400 block text-[11px]">Identified Pain Points</span>
                <p className="mt-1 text-slate-300 italic">{lead.pain_points}</p>
              </div>
            )}
          </div>

          {/* Engagement Metrics */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-white">Engagement Telemetry</h3>
              <span className="text-xs font-bold text-teal-400">{lead.engagement_score} / 100</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                <div className="text-lg font-bold text-white">{lead.website_visits}</div>
                <div className="text-[10px] text-slate-400 uppercase">Web Visits</div>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                <div className="text-lg font-bold text-white">{lead.email_opens}</div>
                <div className="text-[10px] text-slate-400 uppercase">Email Opens</div>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                <div className="text-lg font-bold text-white">{lead.email_clicks}</div>
                <div className="text-[10px] text-slate-400 uppercase">Email Clicks</div>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
                <div className="text-lg font-bold text-white">{lead.meeting_count}</div>
                <div className="text-[10px] text-slate-400 uppercase">Meetings Held</div>
              </div>
            </div>
          </div>
        </div>

        {/* Center Column (4 cols): Chronological Interaction Timeline */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 shadow-lg flex flex-col h-full">
            <div className="flex items-center justify-between mb-4 border-b border-slate-700/60 pb-3">
              <h3 className="text-sm font-semibold text-white">Interaction History</h3>
              <span className="text-xs text-slate-400">
                {lead.interactions?.length || 0} Events Logged
              </span>
            </div>

            <div className="space-y-4 overflow-y-auto max-h-[700px] pr-2">
              {!lead.interactions || lead.interactions.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-10">
                  No previous interactions found for this lead.
                </p>
              ) : (
                lead.interactions.map((event, idx) => (
                  <div key={event.id || idx} className="relative pl-6 pb-2 border-l border-slate-700">
                    <span className="absolute -left-1.5 top-0 w-3 h-3 rounded-full bg-indigo-500 border-2 border-slate-900" />
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">
                          {event.interaction_type}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(event.occurred_at).toLocaleDateString()}
                        </span>
                      </div>
                      {event.subject && (
                        <p className="text-xs text-indigo-300 font-medium">{event.subject}</p>
                      )}
                      <p className="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded-lg border border-slate-700/40">
                        {event.content}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Intelligence Panel, RAG Evidence, Generated Draft */}
        <div className="lg:col-span-4 space-y-6">
          {/* Intelligence Panel */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-1.5">
              <Bot className="w-4 h-4 text-teal-400" />
              <span>Predictive Intelligence</span>
            </h3>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                <span className="text-[10px] text-slate-400 uppercase">ML Conversion Prob</span>
                <div className="text-2xl font-black text-emerald-400 mt-1">{probDisplay}</div>
              </div>
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                <span className="text-[10px] text-slate-400 uppercase">Priority Score</span>
                <div className="text-2xl font-black text-indigo-400 mt-1">
                  {lead.priority_score || '--'}
                </div>
              </div>
            </div>

            {analysis && (
              <div className="space-y-3 text-xs pt-2">
                <div>
                  <span className="font-semibold text-emerald-400 block mb-1">Positive Signals</span>
                  <ul className="list-disc pl-4 space-y-1 text-slate-300">
                    {analysis.positive_indicators.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>

                {analysis.negative_indicators.length > 0 && (
                  <div>
                    <span className="font-semibold text-rose-400 block mb-1">Risk Factors</span>
                    <ul className="list-disc pl-4 space-y-1 text-slate-300">
                      {analysis.negative_indicators.map((n, i) => (
                        <li key={i}>{n}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Generated Follow-Up Draft Card */}
          {latestDraft ? (
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 shadow-lg space-y-3">
              <div className="flex items-center justify-between border-b border-slate-700/60 pb-2">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    {latestDraft.channel} Draft
                  </span>
                </div>
                <Badge
                  variant={
                    latestDraft.status === 'approved'
                      ? 'success'
                      : latestDraft.status === 'simulated_sent'
                      ? 'info'
                      : latestDraft.status === 'rejected'
                      ? 'danger'
                      : 'warning'
                  }
                  size="sm"
                >
                  {latestDraft.status.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>

              {latestDraft.subject && (
                <div className="text-xs font-semibold text-indigo-300">
                  Subj: {latestDraft.subject}
                </div>
              )}

              {isEditingDraft ? (
                <div className="space-y-2">
                  <textarea
                    rows={8}
                    value={editedDraftBody}
                    onChange={(e) => setEditedDraftBody(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-white"
                  />
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => setIsEditingDraft(false)}
                      className="px-3 py-1.5 bg-slate-700 text-xs rounded text-slate-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() =>
                        updateDraftMutation.mutate({ draftId: latestDraft.id, body: editedDraftBody })
                      }
                      className="px-3 py-1.5 bg-indigo-600 text-xs rounded text-white font-medium"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-700/60 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                  {latestDraft.body}
                </div>
              )}

              {/* RAG Source Evidence Badges */}
              {latestDraft.source_references && latestDraft.source_references.length > 0 && (
                <div className="pt-2 border-t border-slate-700/60 space-y-1.5">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                    Grounded Collateral Sources:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {latestDraft.source_references.map((ref, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800"
                      >
                        {ref.document_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Draft Actions */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-700/60">
                {latestDraft.status === 'pending_approval' && (
                  <>
                    <button
                      onClick={() => approveMutation.mutate(latestDraft.id)}
                      className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center justify-center space-x-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={() => setIsRejectModalOpen(true)}
                      className="flex-1 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold flex items-center justify-center space-x-1"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                    <button
                      onClick={() => {
                        setEditedDraftBody(latestDraft.body);
                        setIsEditingDraft(true);
                      }}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs font-medium"
                    >
                      Edit
                    </button>
                  </>
                )}

                {latestDraft.status === 'approved' && (
                  <button
                    onClick={() => simulateSendMutation.mutate(latestDraft.id)}
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-bold flex items-center justify-center space-x-2 shadow-md shadow-indigo-600/30"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Simulate Send (Demo Sandbox)</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-slate-800 rounded-xl border border-dashed border-slate-700 p-6 text-center text-xs text-slate-400">
              No follow-up draft generated yet. Click "Analyze Lead with AI" above to run the SDR agent.
            </div>
          )}

          {/* Previous Runs Accordion */}
          {runsData && runsData.items.length > 0 && (
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 shadow-lg">
              <button
                onClick={() => setIsRunsOpen(!isRunsOpen)}
                className="w-full flex items-center justify-between text-xs font-semibold text-white"
              >
                <span>Previous Agent Runs ({runsData.items.length})</span>
                {isRunsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {isRunsOpen && (
                <div className="mt-3 space-y-2 text-xs border-t border-slate-700 pt-3">
                  {runsData.items.map((run) => (
                    <div
                      key={run.id}
                      onClick={() => navigate('/agent-runs')}
                      className="p-2.5 rounded bg-slate-900/60 hover:bg-slate-900 cursor-pointer flex items-center justify-between border border-slate-700/40"
                    >
                      <div>
                        <div className="font-medium text-slate-200">
                          {new Date(run.started_at).toLocaleTimeString()} ({run.duration_seconds || 0}s)
                        </div>
                        <div className="text-[10px] text-slate-400">Node: {run.current_node}</div>
                      </div>
                      <Badge variant={run.status === 'completed' ? 'success' : 'warning'} size="sm">
                        {run.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      <ConfirmModal
        isOpen={isRejectModalOpen}
        title="Reject Follow-Up Draft"
        message="Please provide a feedback reason for rejecting this AI generated draft:"
        variant="danger"
        confirmLabel="Confirm Rejection"
        onConfirm={() => {
          if (latestDraft) {
            rejectMutation.mutate({ draftId: latestDraft.id, reason: rejectReason || 'Needs revision' });
          }
        }}
        onCancel={() => setIsRejectModalOpen(false)}
      />
    </div>
  );
};
