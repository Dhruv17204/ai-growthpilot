import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import {
  Settings as SettingsIcon,
  Sparkles,
  Key,
  ShieldCheck,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Building2,
  ExternalLink,
  Cpu,
  Database,
  Check,
  RefreshCw,
  Sliders
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: health, isLoading: isHealthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  });

  const { data: aiConfig, isLoading: isAIConfigLoading } = useQuery({
    queryKey: ['ai-config'],
    queryFn: api.getAIConfig,
  });

  const [apiKeyInput, setApiKeyInput] = useState('');
  const [modelSelect, setModelSelect] = useState('gemini-2.5-flash');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Update Gemini Key Mutation
  const updateKeyMutation = useMutation({
    mutationFn: () => api.updateGeminiKey(apiKeyInput, modelSelect),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] });
      queryClient.invalidateQueries({ queryKey: ['health'] });
      setToastMessage(res.message);
      setApiKeyInput('');
      setTimeout(() => setToastMessage(null), 4000);
    },
    onError: (err: any) => {
      setToastMessage(`Update failed: ${err.message}`);
      setTimeout(() => setToastMessage(null), 4000);
    }
  });

  // Reset Demo Data Mutation
  const resetDemoMutation = useMutation({
    mutationFn: api.resetDemoData,
    onSuccess: () => {
      queryClient.invalidateQueries();
      setToastMessage('Database successfully reset and re-seeded with NovaTech Solutions demo dataset!');
      setTimeout(() => setToastMessage(null), 4000);
    }
  });

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-700 text-xs font-semibold animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="border-b border-slate-200/80 pb-6">
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">System & AI Settings</h2>
        <p className="text-xs text-slate-500 mt-1">
          Configure Google Gemini model parameters, verify API connection status, and manage workspace demo data.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Col: AI & API Configuration (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* AI Connection Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-600" />
                <span>Google Gemini API Service</span>
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                aiConfig?.is_configured
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-violet-50 text-violet-700 border border-violet-200'
              }`}>
                {aiConfig?.is_configured ? 'Live Gemini Key Configured' : 'Demo / Simulation Mode'}
              </span>
            </div>

            {/* Safe Status Check Diagnostic */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700">Service Status Check:</span>
                <span className="font-mono text-slate-500">
                  {aiConfig?.status_check?.status || 'Active'}
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed">
                {aiConfig?.status_check?.message || 'Ready to process prompts.'}
              </p>
              {aiConfig?.masked_key && (
                <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-200/60">
                  Active Key Mask: <span className="font-mono">{aiConfig.masked_key}</span>
                </div>
              )}
            </div>

            {/* Key Input Form */}
            <div className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Update Gemini API Key (Backend Session)
                </label>
                <div className="relative">
                  <Key className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    placeholder="Enter AI Studio API Key (AIzaSy...)"
                    className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500 font-mono"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Keys are stored exclusively on the backend server session and never logged or exposed in frontend code.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Select Gemini Model
                </label>
                <select
                  value={modelSelect}
                  onChange={(e) => setModelSelect(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none font-medium text-slate-700 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash (Recommended - High Speed & Structured JSON)</option>
                  <option value="gemini-2.5-pro">Gemini 2.5 Pro (Deep Reasoning & Strategy Synthesis)</option>
                </select>
              </div>

              <button
                onClick={() => updateKeyMutation.mutate()}
                disabled={!apiKeyInput.trim() || updateKeyMutation.isPending}
                className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2"
              >
                {updateKeyMutation.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Verifying with Google Gemini...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Save & Test API Connection</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Demonstration Mode Disclosure */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/80 rounded-2xl p-6 text-xs text-amber-900 space-y-2 shadow-sm">
            <h4 className="font-bold flex items-center gap-2 text-sm text-amber-950">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Assessment & Portfolio Compliance Note</span>
            </h4>
            <p className="leading-relaxed">
              When no Gemini API key is configured, AI GrowthPilot runs in an honest, transparent <strong>Demo Mode</strong>. Demo responses are explicitly labelled as simulation outputs and are never misrepresented as live AI completions.
            </p>
          </div>
        </div>

        {/* Right Col: Data Management & App Info (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Data Management Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-600" />
              <span>Data Management</span>
            </h3>

            <p className="text-xs text-slate-500 leading-relaxed">
              Reset the SQLite database back to the canonical NovaTech Solutions demonstration dataset including leads, campaigns, content calendar, and prompt benchmarks.
            </p>

            <button
              onClick={() => {
                if (window.confirm('Reset database to default NovaTech Solutions demonstration state?')) {
                  resetDemoMutation.mutate();
                }
              }}
              disabled={resetDemoMutation.isPending}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-700 font-bold text-xs border border-slate-200 transition-all flex items-center justify-center gap-2"
            >
              <RotateCcw className={`w-4 h-4 ${resetDemoMutation.isPending ? 'animate-spin' : ''}`} />
              <span>Reset to NovaTech Demo Data</span>
            </button>
          </div>

          {/* Application Specification Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-3 text-xs">
            <h3 className="text-sm font-bold text-slate-900">Application Architecture</h3>
            <ul className="space-y-2 text-slate-600">
              <li className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-400">Frontend Stack:</span>
                <span className="font-medium text-slate-800">React 19 • Vite • Tailwind • TypeScript</span>
              </li>
              <li className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-400">Backend Stack:</span>
                <span className="font-medium text-slate-800">FastAPI • Python 3.14 • SQLAlchemy</span>
              </li>
              <li className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-400">Database Engine:</span>
                <span className="font-medium text-slate-800">SQLite (Local ACID persistence)</span>
              </li>
              <li className="flex justify-between border-b border-slate-100 pb-1">
                <span className="text-slate-400">AI Integration:</span>
                <span className="font-medium text-slate-800">Google GenAI Official Python SDK</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-400">Human-in-the-Loop:</span>
                <span className="font-semibold text-indigo-600">Manual Approval Gate Enforced</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
