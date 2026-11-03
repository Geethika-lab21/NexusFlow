export interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  company: string;
  title: string;
  industry: string;
  company_size: string;
  country: string;
  lead_source: string;
  lead_status: string;
  sales_stage: string;
  budget_range: string;
  purchase_timeline: string;
  decision_maker_status: boolean;
  pain_points?: string | null;
  product_interest: string;
  business_need?: string | null;
  engagement_score: number;
  website_visits: number;
  email_opens: number;
  email_clicks: number;
  meeting_count: number;
  is_converted: boolean;
  priority_score?: number | null;
  priority_category?: 'high' | 'medium' | 'low' | null;
  conversion_probability?: number | null;
  created_at: string;
  updated_at: string;
  interactions?: Interaction[];
}

export interface Interaction {
  id: string;
  lead_id: string;
  interaction_type: string;
  direction: string;
  subject?: string | null;
  content: string;
  occurred_at: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface LeadAnalysis {
  id: string;
  lead_id: string;
  conversion_probability: number;
  priority_score: number;
  priority_category: 'high' | 'medium' | 'low';
  positive_indicators: string[];
  negative_indicators: string[];
  missing_information: string[];
  feature_contributions: Array<{
    feature: string;
    value: any;
    direction: string;
    weight: number;
  }>;
  recommended_action: string;
  action_rationale: string;
  model_version: string;
  created_at: string;
}

export interface FollowUpDraft {
  id: string;
  lead_id: string;
  agent_run_id?: string | null;
  channel: string;
  subject?: string | null;
  body: string;
  personalization_points: string[];
  rationale: string;
  source_references: Array<{
    document_name: string;
    chunk_id: string;
    excerpt: string;
  }>;
  call_to_action?: string | null;
  status: 'pending_approval' | 'approved' | 'rejected' | 'simulated_sent';
  approved_by?: string | null;
  approval_decision_at?: string | null;
  rejection_reason?: string | null;
  simulated_sent_at?: string | null;
  created_at: string;
  updated_at: string;
  lead_name?: string | null;
  lead_company?: string | null;
}

export interface AgentStep {
  id: string;
  run_id: string;
  step_order: number;
  node_name: string;
  tool_name?: string | null;
  status: string;
  input_summary?: string | null;
  output_summary?: string | null;
  duration_ms?: number | null;
  created_at: string;
}

export interface AgentRun {
  id: string;
  lead_id: string;
  requested_by: string;
  status: 'pending' | 'running' | 'awaiting_approval' | 'completed' | 'failed' | 'skipped';
  current_node?: string | null;
  trigger_source: string;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  skip_reason?: string | null;
  error_message?: string | null;
  metadata_json?: string | null;
  steps: AgentStep[];
  lead_name?: string | null;
  lead_company?: string | null;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  document_name: string;
  category: string;
  text: string;
  semantic_score?: number | null;
  bm25_score?: number | null;
  rrf_score: number;
  retrieval_method: string;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  file_path: string;
  category: string;
  content_hash: string;
  chunk_count: number;
  status: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsOverview {
  total_leads: number;
  conversion_rate: number;
  open_pipeline_count: number;
  high_priority_count: number;
  overdue_followups_count: number;
  pending_approvals_count: number;
  leads_by_stage: Array<{ stage: string; count: number; percentage: number }>;
  leads_by_source: Array<{ source: string; count: number; percentage: number }>;
  conversion_trend: Array<{ month: string; converted: number; lost: number; conversion_rate: number }>;
  recent_agent_activity: Array<{
    id: string;
    run_id?: string;
    lead_id: string;
    lead_name: string;
    company: string;
    action: string;
    status: string;
    timestamp: string;
  }>;
  leads_needing_attention: Array<{
    id: string;
    name: string;
    company: string;
    priority_score: number;
    priority_category: string;
    conversion_probability: number;
    sales_stage: string;
    reason: string;
  }>;
}

export interface EvaluationRun {
  id: string;
  evaluation_type: string;
  model_version: string;
  dataset_name: string;
  sample_count: number;
  metrics: {
    ml?: {
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
      roc_auc: number;
      confusion_matrix?: {
        true_negatives: number;
        false_positives: number;
        false_negatives: number;
        true_positives: number;
      };
      class_distribution?: {
        negative_samples: number;
        positive_samples: number;
      };
    };
    rag?: {
      recall_at_5: number;
      mrr: number;
      avg_latency_ms: number;
      benchmark_queries: number;
    };
    agent?: {
      total_runs: number;
      completed_runs: number;
      awaiting_approval_runs: number;
      failed_runs: number;
      workflow_completion_rate: number;
      avg_run_duration_seconds: number;
      total_steps_executed: number;
      tool_failure_rate: number;
      approval_compliance_rate: number;
    };
  };
  feature_importance?: Array<{ feature: string; importance: number }>;
  confusion_matrix?: Record<string, number>;
  status: string;
  error_message?: string | null;
  created_at: string;
}

export interface SettingItem {
  key: string;
  value: string;
  description?: string | null;
  category: string;
}
