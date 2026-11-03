import axios from 'axios';
import {
  Lead,
  PaginatedResponse,
  LeadAnalysis,
  FollowUpDraft,
  AgentRun,
  KnowledgeDocument,
  RetrievedChunk,
  AnalyticsOverview,
  EvaluationRun,
  SettingItem
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Leads
  async getLeads(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    industry?: string;
    sales_stage?: string;
    lead_source?: string;
    priority?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse<Lead>> {
    const { data } = await api.get('/leads', { params });
    return data;
  },

  async getLead(id: string): Promise<Lead> {
    const { data } = await api.get(`/leads/${id}`);
    return data;
  },

  async createLead(leadData: Partial<Lead>): Promise<Lead> {
    const { data } = await api.post('/leads', leadData);
    return data;
  },

  async updateLead(id: string, leadData: Partial<Lead>): Promise<Lead> {
    const { data } = await api.patch(`/leads/${id}`, leadData);
    return data;
  },

  async deleteLead(id: string): Promise<void> {
    await api.delete(`/leads/${id}`);
  },

  async importLeadsCsv(file: File): Promise<{ imported_count: number; skipped_count: number; errors: string[] }> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/leads/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  // Analyses
  async getLeadAnalysis(leadId: string): Promise<LeadAnalysis | null> {
    const { data } = await api.get(`/analyses/leads/${leadId}`);
    return data;
  },

  async scoreLead(leadId: string): Promise<any> {
    const { data } = await api.post(`/analyses/leads/${leadId}/score`);
    return data;
  },

  async predictLead(leadId: string): Promise<any> {
    const { data } = await api.post(`/analyses/leads/${leadId}/predict`);
    return data;
  },

  // Agent Runs
  async startAgentRun(leadId: string, requestedBy: string = 'dashboard'): Promise<AgentRun> {
    const { data } = await api.post('/agent-runs', {
      lead_id: leadId,
      requested_by: requestedBy,
      trigger_source: 'manual',
    });
    return data;
  },

  async getAgentRun(runId: string): Promise<AgentRun> {
    const { data } = await api.get(`/agent-runs/${runId}`);
    return data;
  },

  async getAgentRuns(params?: { skip?: number; limit?: number; lead_id?: string; status_filter?: string }): Promise<PaginatedResponse<AgentRun>> {
    const { data } = await api.get('/agent-runs', { params });
    return data;
  },

  // Follow-Up Center
  async getDrafts(params?: { skip?: number; limit?: number; status?: string; lead_id?: string }): Promise<PaginatedResponse<FollowUpDraft>> {
    const { data } = await api.get('/follow-ups', { params });
    return data;
  },

  async getDraft(draftId: string): Promise<FollowUpDraft> {
    const { data } = await api.get(`/follow-ups/${draftId}`);
    return data;
  },

  async updateDraft(draftId: string, updates: Partial<FollowUpDraft>): Promise<FollowUpDraft> {
    const { data } = await api.patch(`/follow-ups/${draftId}`, updates);
    return data;
  },

  async approveDraft(draftId: string, approvedBy: string = 'Sales Director'): Promise<any> {
    const { data } = await api.post(`/follow-ups/${draftId}/approve`, { approved_by: approvedBy });
    return data;
  },

  async rejectDraft(draftId: string, reason: string): Promise<any> {
    const { data } = await api.post(`/follow-ups/${draftId}/reject`, { reason });
    return data;
  },

  async simulateSend(draftId: string): Promise<any> {
    const { data } = await api.post(`/follow-ups/${draftId}/simulate-send`);
    return data;
  },

  // Knowledge Base
  async searchKnowledge(query: string, top_k: number = 5, category?: string): Promise<{ query: string; results: RetrievedChunk[]; total_found: number }> {
    const { data } = await api.post('/knowledge/search', { query, top_k, category });
    return data;
  },

  async getDocuments(): Promise<KnowledgeDocument[]> {
    const { data } = await api.get('/knowledge/documents');
    return data;
  },

  async uploadDocument(file: File, category: string = 'General'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    const { data } = await api.post('/knowledge/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  async deleteDocument(docId: string): Promise<void> {
    await api.delete(`/knowledge/documents/${docId}`);
  },

  // Analytics
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    const { data } = await api.get('/analytics/overview');
    return data;
  },

  // Evaluation
  async runEvaluation(): Promise<EvaluationRun> {
    const { data } = await api.post('/evaluation/run');
    return data;
  },

  async getLatestEvaluation(): Promise<EvaluationRun> {
    const { data } = await api.get('/evaluation/latest');
    return data;
  },

  async getEvaluationHistory(limit: number = 10): Promise<EvaluationRun[]> {
    const { data } = await api.get('/evaluation/history', { params: { limit } });
    return data;
  },

  // Settings
  async getSettings(): Promise<SettingItem[]> {
    const { data } = await api.get('/settings');
    return data;
  },

  async updateSettings(settings: Record<string, string>): Promise<any> {
    const { data } = await api.patch('/settings', { settings });
    return data;
  },

  async resetDataset(): Promise<any> {
    const { data } = await api.post('/settings/reset-dataset');
    return data;
  },
};
