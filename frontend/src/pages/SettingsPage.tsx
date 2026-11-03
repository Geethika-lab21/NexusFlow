import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings as SettingsIcon,
  Sliders,
  Sparkles,
  Database,
  RotateCcw,
  Save,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

import { apiClient } from '../api/client';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ConfirmModal } from '../components/ConfirmModal';
import { SettingItem } from '../types';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [settingsMap, setSettingsMap] = useState<Record<string, string>>({});
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);

  // Queries
  const { data: settingsList, isLoading } = useQuery({
    queryKey: ['appSettings'],
    queryFn: apiClient.getSettings,
  });

  useEffect(() => {
    if (settingsList) {
      const map: Record<string, string> = {};
      settingsList.forEach((item: SettingItem) => {
        map[item.key] = item.value;
      });
      setSettingsMap(map);
    }
  }, [settingsList]);

  // Mutations
  const updateMutation = useMutation({
    mutationFn: (updated: Record<string, string>) => apiClient.updateSettings(updated),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appSettings'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  const resetMutation = useMutation({
    mutationFn: apiClient.resetDataset,
    onSuccess: () => {
      setIsResetModalOpen(false);
      queryClient.invalidateQueries();
      alert('Dataset has been successfully reset and re-seeded from synthetic distributions.');
    },
  });

  if (isLoading) {
    return <LoadingSpinner size="lg" label="Loading application settings..." className="min-h-[400px]" />;
  }

  const handleWeightChange = (key: string, val: number) => {
    setSettingsMap((prev) => ({
      ...prev,
      [key]: val.toString(),
    }));
  };

  const weightsSum = (
    parseFloat(settingsMap.weight_engagement || '0.25') +
    parseFloat(settingsMap.weight_budget_fit || '0.20') +
    parseFloat(settingsMap.weight_timeline || '0.15') +
    parseFloat(settingsMap.weight_decision_maker || '0.15') +
    parseFloat(settingsMap.weight_product_fit || '0.15') +
    parseFloat(settingsMap.weight_recent_activity || '0.10')
  ).toFixed(2);

  return (
    <div className="page-light mx-auto max-w-4xl space-y-6">
      {/* Title & Save Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">System & Algorithm Settings</h1>
          <p className="page-description">
            Configure LLM inference, heuristic weighting distributions, and policy governance
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {saveSuccess && (
            <span className="text-xs text-emerald-400 font-semibold flex items-center space-x-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Saved!</span>
            </span>
          )}

          <button
            onClick={() => updateMutation.mutate(settingsMap)}
            disabled={updateMutation.isPending}
            className="button-primary"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{updateMutation.isPending ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
      </div>

      {/* 1. LLM Provider Configuration */}
      <div className="surface-card space-y-4 p-4 sm:p-5">
        <div className="flex items-center space-x-2 border-b border-slate-700 pb-3">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">LLM Provider & Orchestration</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Inference Engine Provider</label>
            <select
              value={settingsMap.llm_provider || 'demo'}
              onChange={(e) => setSettingsMap({ ...settingsMap, llm_provider: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
            >
              <option value="demo">Deterministic Demo Mode (Fast, zero-cost, grounded)</option>
              <option value="openai">OpenAI API (Requires OPENAI_API_KEY)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Model Name</label>
            <input
              type="text"
              value={settingsMap.openai_model || 'gpt-4o-mini'}
              onChange={(e) => setSettingsMap({ ...settingsMap, openai_model: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
          </div>
        </div>
      </div>

      {/* 2. Priority Scoring Weights */}
      <div className="surface-card space-y-4 p-4 sm:p-5">
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-teal-400" />
            <h3 className="text-sm font-semibold text-white">Lead Priority Scoring Weights</h3>
          </div>
          <span
            className={`text-xs font-bold ${
              weightsSum === '1.00' ? 'text-emerald-400' : 'text-amber-400'
            }`}
          >
            Total Weight: {weightsSum} / 1.00
          </span>
        </div>

        <div className="space-y-4 text-xs">
          {[
            { key: 'weight_engagement', label: 'Engagement Score Weight', default: 0.25 },
            { key: 'weight_budget_fit', label: 'Budget Fit Weight', default: 0.20 },
            { key: 'weight_timeline', label: 'Purchase Timeline Urgency', default: 0.15 },
            { key: 'weight_decision_maker', label: 'Decision Maker Authority', default: 0.15 },
            { key: 'weight_product_fit', label: 'Product & Pain Point Alignment', default: 0.15 },
            { key: 'weight_recent_activity', label: 'Recent Velocity Activity', default: 0.10 },
          ].map((item) => {
            const currentVal = parseFloat(settingsMap[item.key] || item.default.toString());
            return (
              <div key={item.key} className="space-y-1">
                <div className="flex justify-between text-slate-300">
                  <span>{item.label}</span>
                  <span className="font-mono text-indigo-400 font-bold">{currentVal.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.5"
                  step="0.05"
                  value={currentVal}
                  onChange={(e) => handleWeightChange(item.key, parseFloat(e.target.value))}
                  className="w-full accent-indigo-500 bg-slate-900 rounded-lg h-2 cursor-pointer"
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Priority Thresholds & Governance */}
      <div className="surface-card space-y-4 p-4 sm:p-5">
        <div className="flex items-center space-x-2 border-b border-slate-700 pb-3">
          <SettingsIcon className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">Priority Thresholds & Policy Limits</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">High Priority Threshold</label>
            <input
              type="number"
              step="1"
              value={settingsMap.high_priority_threshold || '65.0'}
              onChange={(e) => setSettingsMap({ ...settingsMap, high_priority_threshold: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Medium Priority Threshold</label>
            <input
              type="number"
              step="1"
              value={settingsMap.medium_priority_threshold || '40.0'}
              onChange={(e) => setSettingsMap({ ...settingsMap, medium_priority_threshold: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Max Follow-Ups Per Week</label>
            <input
              type="number"
              step="1"
              value={settingsMap.max_followups_per_week || '2'}
              onChange={(e) => setSettingsMap({ ...settingsMap, max_followups_per_week: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
          </div>
        </div>
      </div>

      {/* 4. Danger Zone: Reset Dataset */}
      <div className="space-y-3 rounded-2xl border border-rose-200 bg-white p-4 shadow-sm sm:p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-rose-400">Database Reset & Reseed</h3>
            <p className="text-xs text-slate-400">
              Clear all lead records, agent traces, and drafts and regenerate fresh synthetic distributions
            </p>
          </div>

          <button
            onClick={() => setIsResetModalOpen(true)}
            className="flex items-center space-x-1.5 px-4 py-2 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/40 rounded-lg text-xs font-semibold transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Dataset</span>
          </button>
        </div>
      </div>

      {/* Reset Confirmation Modal */}
      <ConfirmModal
        isOpen={isResetModalOpen}
        title="Reset Entire Dataset?"
        message="This will delete all current leads, interactions, and drafts from the SQLite database and reseed 700 fresh leads."
        confirmLabel="Yes, Reset Everything"
        variant="danger"
        onConfirm={() => resetMutation.mutate()}
        onCancel={() => setIsResetModalOpen(false)}
      />
    </div>
  );
};
