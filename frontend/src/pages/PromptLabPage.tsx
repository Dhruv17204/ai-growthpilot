import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { PromptTemplate, PromptExecution } from '../types';
import {
  Cpu,
  Layers,
  History,
  Sparkles,
  ArrowRight,
  Code,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ChevronDown,
  Info,
  Terminal,
  FileText,
  Search
} from 'lucide-react';

const CATEGORIES = [
  'All',
  'Business Strategy',
  'Campaign Generation',
  'Content Creation',
  'Lead Qualification',
  'Weekly Growth Recommendations'
];

export const PromptLabPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [inspectExecution, setInspectExecution] = useState<PromptExecution | null>(null);

  // Fetch Templates
  const { data: templates, isLoading: isTemplatesLoading } = useQuery({
    queryKey: ['prompt-templates'],
    queryFn: api.getPromptTemplates,
  });

  // Fetch Execution Logs
  const { data: executions, isLoading: isExecutionsLoading } = useQuery({
    queryKey: ['prompt-executions'],
    queryFn: () => api.getPromptExecutions(40),
    refetchInterval: 15000,
  });

  // Filter templates
  const filteredTemplates = (templates || []).filter((t) => {
    if (selectedCategory !== 'All' && t.category !== selectedCategory) return false;
    return true;
  });

  // Automatically select first template
  React.useEffect(() => {
    if (filteredTemplates.length > 0 && !selectedTemplate) {
      setSelectedTemplate(filteredTemplates[0]);
    }
  }, [filteredTemplates, selectedTemplate]);

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Portfolio Highlight Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/30 text-violet-200 border border-violet-400/30">
                Core Technical Assessment Feature
              </span>
              <span className="text-xs text-slate-400">Iterative Prompt Engineering Suite</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Prompt Engineering Lab & Audit Logs
            </h2>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              Transparent prompt architecture demonstrating iterative engineering from vague baseline v1.0 prompts to structured, anti-hallucinatory, production-grade v3.0 schemas.
            </p>
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200/80 pb-3">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              setSelectedCategory(cat);
              setSelectedTemplate(null);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              selectedCategory === cat
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Part 1: Documented Prompt Iteration Evolution (v1 vs v2 vs v3) */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <span>Documented Iterative Prompt Refinement (Benchmark Case Study)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Clearly documented prompt development evolution demonstrating why progressive constraints improve factual precision and schema adherence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Version 1.0 */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700">
                  Version 1.0 (Baseline)
                </span>
                <span className="text-[10px] text-rose-600 font-semibold">Unconstrained</span>
              </div>
              <h4 className="text-xs font-bold text-slate-800">Initial Vague Prompt</h4>
              <div className="p-3 bg-white rounded-xl border border-slate-200 text-[11px] font-mono text-slate-600 mt-2">
                "Create a marketing strategy for a technology company: NovaTech Solutions."
              </div>
            </div>
            <div className="pt-3 border-t border-slate-200 text-[11px] text-slate-500 leading-relaxed">
              <strong className="text-slate-700 block mb-0.5">Deficiencies Identified:</strong>
              Lacks target audience, industry vertical, geography, and budget context. Model outputs vague consumer marketing advice (e.g. "Post on Instagram") with zero B2B applicability.
            </div>
          </div>

          {/* Version 2.0 */}
          <div className="p-5 rounded-2xl bg-amber-50/40 border border-amber-200/80 space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                  Version 2.0 (Refined)
                </span>
                <span className="text-[10px] text-amber-700 font-semibold">Contextualized</span>
              </div>
              <h4 className="text-xs font-bold text-slate-800">Added Business Parameters</h4>
              <div className="p-3 bg-white rounded-xl border border-amber-200 text-[11px] font-mono text-slate-600 mt-2">
                "Create a marketing strategy for NovaTech Solutions targeting small businesses in Australia. Services: AI & Web Dev. Include customer pain points, channels, and measurable objectives."
              </div>
            </div>
            <div className="pt-3 border-t border-amber-200 text-[11px] text-slate-500 leading-relaxed">
              <strong className="text-slate-700 block mb-0.5">Improvements & Limitations:</strong>
              Added industry context and geography. However, still returned unstructured markdown, lacked strict JSON schema enforcement, and lacked anti-hallucination guardrails.
            </div>
          </div>

          {/* Version 3.0 (Production) */}
          <div className="p-5 rounded-2xl bg-indigo-50/50 border-2 border-indigo-500 space-y-3 flex flex-col justify-between shadow-md">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-600 text-white">
                  Version 3.0 (Production Grade)
                </span>
                <span className="text-[10px] text-indigo-700 font-bold">Strict Schema & Anti-Hallucination</span>
              </div>
              <h4 className="text-xs font-bold text-slate-900">Structured Role, ICP Rubric & JSON Schema</h4>
              <div className="p-3 bg-white rounded-xl border border-indigo-200 text-[11px] font-mono text-indigo-900 mt-2">
                "Act as a senior B2B growth strategist. Analyse the supplied company profile, target audience, services, geography, and budget. Generate a structured 30-day marketing strategy with specific ICPs, pain points, channel recommendations, campaign ideas, KPIs, and actionable priorities. Do NOT invent external market statistics. Return strictly valid JSON adhering to the specified schema."
              </div>
            </div>
            <div className="pt-3 border-t border-indigo-200 text-[11px] text-slate-600 leading-relaxed">
              <strong className="text-indigo-950 block mb-0.5">Production Excellence:</strong>
              100% type-safe JSON output validated by Pydantic, strict negative constraints preventing hallucinated web citations, and explainable mathematical attribution.
            </div>
          </div>
        </div>
      </div>

      {/* Part 2: Active Prompt Templates Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Template List (4 cols) */}
        <div className="lg:col-span-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
          <h4 className="text-sm font-bold text-slate-900">Registered Prompt Templates</h4>
          <div className="space-y-2">
            {filteredTemplates.map((t) => (
              <div
                key={t.id}
                onClick={() => setSelectedTemplate(t)}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  selectedTemplate?.id === t.id
                    ? 'border-indigo-500 bg-indigo-50/60 shadow-sm'
                    : 'border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">{t.category}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    t.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {t.version}
                  </span>
                </div>
                <h5 className="text-xs font-bold text-slate-900 mt-1">{t.name}</h5>
              </div>
            ))}
          </div>
        </div>

        {/* Template Detail Viewer (8 cols) */}
        <div className="lg:col-span-8 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
          {selectedTemplate ? (
            <>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h4 className="text-base font-bold text-slate-900">{selectedTemplate.name}</h4>
                  <span className="text-xs text-slate-400">Category: {selectedTemplate.category} • Version: {selectedTemplate.version}</span>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  selectedTemplate.is_active ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-100 text-slate-600'
                }`}>
                  {selectedTemplate.is_active ? 'Production Active' : 'Archived Benchmark'}
                </span>
              </div>

              {/* System Instructions */}
              <div>
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  System Instruction Prompt
                </span>
                <div className="p-3.5 rounded-xl bg-slate-900 text-indigo-300 font-mono text-xs leading-relaxed">
                  {selectedTemplate.system_instructions}
                </div>
              </div>

              {/* User Prompt Template */}
              <div>
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1">
                  User Prompt Template & Variable Tokens
                </span>
                <pre className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 font-mono text-xs whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                  {selectedTemplate.user_prompt_template}
                </pre>
              </div>

              {/* Version Notes */}
              <div className="p-3 rounded-xl bg-violet-50/70 border border-violet-200 text-xs text-violet-900">
                <strong>Engineering Revision Rationale: </strong>
                {selectedTemplate.notes}
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-400 text-xs">
              Select a prompt template from the left to inspect system instructions and schemas.
            </div>
          )}
        </div>
      </div>

      {/* Part 3: Live Generation Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <History className="w-5 h-5 text-indigo-600" />
              <span>Prompt Execution Audit History</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Every AI generation logs inputs, prompt rendered, latency, and structured outputs without exposing sensitive credentials.
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
            {executions?.length || 0} Runs Recorded
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-200/80 text-slate-500 font-semibold">
              <tr>
                <th className="pb-3">Timestamp</th>
                <th className="pb-3">Feature</th>
                <th className="pb-3">Version</th>
                <th className="pb-3">Model</th>
                <th className="pb-3">Latency</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {executions && executions.length > 0 ? (
                executions.map((exec) => (
                  <tr key={exec.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 text-slate-500 font-medium">
                      {new Date(exec.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="py-3 font-semibold text-slate-900">{exec.feature_name}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {exec.prompt_version}
                      </span>
                    </td>
                    <td className="py-3 text-slate-600 font-mono text-[11px]">{exec.model_used}</td>
                    <td className="py-3 text-slate-500">{exec.latency_ms} ms</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        exec.execution_status === 'success'
                          ? 'bg-emerald-50 text-emerald-700'
                          : exec.execution_status === 'fallback_demo'
                          ? 'bg-violet-50 text-violet-700'
                          : 'bg-rose-50 text-rose-700'
                      }`}>
                        {exec.execution_status}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => setInspectExecution(exec)}
                        className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 font-medium text-[11px]"
                      >
                        Inspect Payload
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No prompt executions logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Execution Modal */}
      {inspectExecution && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h4 className="text-base font-bold text-slate-900">
                  Execution Payload: {inspectExecution.feature_name} ({inspectExecution.prompt_version})
                </h4>
                <p className="text-xs text-slate-500">Model: {inspectExecution.model_used} • Latency: {inspectExecution.latency_ms} ms</p>
              </div>
              <button
                onClick={() => setInspectExecution(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-600"
              >
                Close
              </button>
            </div>

            <div>
              <span className="text-xs font-bold text-slate-700 block mb-1">Rendered Prompt Prompt Sent</span>
              <pre className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {inspectExecution.prompt_rendered}
              </pre>
            </div>

            <div>
              <span className="text-xs font-bold text-slate-700 block mb-1">Generated Output (Validated JSON)</span>
              <pre className="p-3 bg-slate-900 text-emerald-300 rounded-xl text-xs font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                {JSON.stringify(inspectExecution.generated_output, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
