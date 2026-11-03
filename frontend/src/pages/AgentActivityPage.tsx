import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Bot,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  Layers,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

import { apiClient } from '../api/client';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AgentRun, AgentStep } from '../types';

const WORKFLOW_NODES = [
  'load_lead',
  'gather_context',
  'analyze_intelligence',
  'determine_retrieval_needs',
  'retrieve_knowledge',
  'decide_next_action',
  'generate_draft',
  'validate_output',
  'human_approval',
  'execute_action',
  'completed'
];

export const AgentActivityPage: React.FC = () => {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const { data: runsData, isLoading } = useQuery({
    queryKey: ['allAgentRuns'],
    queryFn: () => apiClient.getAgentRuns({ limit: 30 }),
    refetchInterval: 10000,
  });

  const { data: selectedRun } = useQuery({
    queryKey: ['agentRunDetail', selectedRunId],
    queryFn: () => apiClient.getAgentRun(selectedRunId!),
    enabled: !!selectedRunId,
  });

  const runs = runsData?.items || [];
  const activeRun = selectedRun || (runs.length > 0 ? runs[0] : null);

  return (
    <div className="page-light space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Autonomous Agent Telemetry</h1>
        <p className="page-description">
          LangGraph state machine executions, step traces, and decision pathways
        </p>
      </div>

      {/* Visual Workflow Diagram */}
      <div className="surface-card space-y-3 p-4 sm:p-5">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span>LangGraph 11-Node Architecture</span>
        </h3>

        <div className="flex items-center overflow-x-auto py-3 space-x-2 scrollbar-thin">
          {WORKFLOW_NODES.map((node, idx) => {
            const isCompleted =
              activeRun &&
              activeRun.steps?.some((s) => s.node_name === node && s.status === 'success');
            const isCurrent = activeRun && activeRun.current_node === node;

            return (
              <React.Fragment key={node}>
                <div
                  className={`flex-shrink-0 px-3 py-2 rounded-lg border text-center transition-all ${
                    isCurrent
                      ? 'bg-indigo-50 border-indigo-300 text-indigo-700 shadow-sm'
                      : isCompleted
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                      : 'bg-[#f8f9fd] border-[#e6e9f3] text-[#8992aa]'
                  }`}
                >
                  <div className="text-[11px] font-mono font-semibold capitalize">
                    {node.replace(/_/g, ' ')}
                  </div>
                </div>

                {idx < WORKFLOW_NODES.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Two Column Layout: Run History & Trace Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Runs Table */}
        <div className="surface-card overflow-hidden lg:col-span-5">
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-sm font-semibold text-white">Execution History</h3>
          </div>

          {isLoading ? (
            <LoadingSpinner size="md" label="Loading run logs..." className="py-12" />
          ) : runs.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">
              No agent runs logged yet. Initiate an AI analysis on any lead to see trace data.
            </div>
          ) : (
            <div className="max-h-[600px] divide-y divide-[#edf0f6] overflow-y-auto">
              {runs.map((run) => {
                const isSelected = (selectedRunId || activeRun?.id) === run.id;
                return (
                  <div
                    key={run.id}
                    onClick={() => setSelectedRunId(run.id)}
                    role="button"
                    tabIndex={0}
                    aria-pressed={isSelected}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        setSelectedRunId(run.id);
                      }
                    }}
                    className={`cursor-pointer p-4 transition-colors ${
                      isSelected ? 'border-l-4 border-indigo-500 bg-indigo-50/70' : 'hover:bg-[#f8f9fd]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white">
                        Run {run.id.slice(0, 8)}...
                      </span>
                      <Badge
                        variant={
                          run.status === 'completed'
                            ? 'success'
                            : run.status === 'awaiting_approval'
                            ? 'warning'
                            : run.status === 'failed'
                            ? 'danger'
                            : 'primary'
                        }
                        size="sm"
                      >
                        {run.status}
                      </Badge>
                    </div>

                    <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Node: {run.current_node || 'Done'}</span>
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{run.duration_seconds || 0}s</span>
                      </span>
                    </div>

                    <div className="mt-1 text-[10px] text-slate-500">
                      Started: {new Date(run.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column (7 cols): Step Traces Timeline */}
        <div className="surface-card space-y-4 p-4 sm:p-5 lg:col-span-7">
          <div className="flex items-center justify-between border-b border-slate-700 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-white">Step Trace Inspection</h3>
              <p className="text-xs text-slate-400">
                Run ID: {activeRun?.id || 'None Selected'}
              </p>
            </div>
            {activeRun && (
              <Badge
                variant={
                  activeRun.status === 'completed'
                    ? 'success'
                    : activeRun.status === 'awaiting_approval'
                    ? 'warning'
                    : 'primary'
                }
                size="sm"
              >
                {activeRun.status}
              </Badge>
            )}
          </div>

          {!activeRun || !activeRun.steps || activeRun.steps.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-16">
              Select an agent run to view granular node and tool invocation traces.
            </p>
          ) : (
            <div className="space-y-4 overflow-y-auto max-h-[550px] pr-2">
              {activeRun.steps.map((step: AgentStep) => (
                <div
                  key={step.id || step.step_order}
                  className="space-y-2 rounded-xl border border-[#e8eaf4] bg-[#fafbfe] p-3.5 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-50 text-[10px] font-bold text-indigo-700">
                        {step.step_order}
                      </span>
                      <span className="font-bold uppercase tracking-wide text-[#303b5c]">
                        {step.node_name.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {step.duration_ms} ms
                    </span>
                  </div>

                  {step.tool_name && (
                    <div className="text-[11px] text-teal-400 font-medium">
                      Tool Invoked: <span className="font-mono bg-teal-950/60 px-1.5 py-0.5 rounded border border-teal-800">{step.tool_name}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 gap-2 pt-1 text-[11px] sm:grid-cols-2">
                    {step.input_summary && (
                      <div className="rounded-lg border border-[#e9ebf4] bg-white p-2">
                        <span className="text-[9px] text-slate-500 font-bold uppercase block">Input:</span>
                        <p className="break-words text-slate-300">{step.input_summary}</p>
                      </div>
                    )}
                    {step.output_summary && (
                      <div className="rounded-lg border border-[#e9ebf4] bg-white p-2">
                        <span className="text-[9px] text-slate-500 font-bold uppercase block">Output:</span>
                        <p className="break-words text-slate-300">{step.output_summary}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
