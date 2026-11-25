import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { BusinessProfile, GrowthStrategy } from '../types';
import {
  Sparkles,
  RefreshCw,
  Save,
  CheckCircle2,
  Calendar,
  Target,
  Users,
  Compass,
  ArrowRight,
  ChevronDown,
  Layers,
  Award,
  Zap,
  DollarSign,
  Cpu,
  AlertTriangle
} from 'lucide-react';

export const StrategyPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Load existing profile & strategies
  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ['business-profile'],
    queryFn: api.getBusinessProfile,
  });

  const { data: strategies, isLoading: isStrategiesLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: api.getStrategies,
  });

  // Local state for profile form
  const [formData, setFormData] = useState<Partial<BusinessProfile>>({
    company_name: 'NovaTech Solutions',
    industry: 'B2B Technology & AI Services',
    website: 'https://novatech-solutions.demo',
    description: 'NovaTech Solutions is an agile technology consultancy delivering custom AI development, modern web applications, data engineering, business intelligence, and workflow automation.',
    services: ['AI Development', 'Web Development', 'Data Engineering', 'Business Intelligence', 'Workflow Automation'],
    target_audience: ['Small & Medium Businesses', 'Startup Founders', 'Operations Managers'],
    target_geography: ['Australia', 'United States', 'India'],
    monthly_budget: 8500,
    main_objective: 'Acquire high-value B2B enterprise clients for custom AI and automation services',
    competitors: ['Legacy IT Outsourcers', 'Generic Web Agencies', 'Off-the-shelf SaaS Wrappers'],
    preferred_channels: ['LinkedIn B2B Outreach', 'Technical Case Studies & SEO', 'Google Search Ads', 'Direct Founder Email Newsletters'],
  });

  const [activeStrategy, setActiveStrategy] = useState<GrowthStrategy | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Set active strategy when loaded
  React.useEffect(() => {
    if (strategies && strategies.length > 0 && !activeStrategy) {
      setActiveStrategy(strategies[0]);
    }
  }, [strategies, activeStrategy]);

  // Set formData when profile arrives
  React.useEffect(() => {
    if (profile) {
      setFormData(profile);
    }
  }, [profile]);

  // Generate Strategy Mutation
  const generateMutation = useMutation({
    mutationFn: (opts?: { force_demo_mode?: boolean }) =>
      api.generateStrategy({ profile_override: formData, force_demo_mode: opts?.force_demo_mode ?? false }),
    onSuccess: (res) => {
      setActiveStrategy(res.strategy);
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-overview'] });
      const src = res.strategy.is_demo ? 'Demo Simulation Mode' : 'Live Gemini AI';
      setToastMessage(`Growth Strategy generated via ${src}!`);
      setTimeout(() => setToastMessage(null), 4000);
    },
    onError: (err: any) => {
      setToastMessage(`AI Generation Note: ${err.message}`);
      setTimeout(() => setToastMessage(null), 5000);
    }
  });

  // Regenerate Section Mutation
  const regenSectionMutation = useMutation({
    mutationFn: (sectionName: string) => {
      if (!activeStrategy) throw new Error('No strategy selected');
      return api.regenerateStrategySection(activeStrategy.id, sectionName);
    },
    onSuccess: (data) => {
      if (activeStrategy) {
        setActiveStrategy({
          ...activeStrategy,
          [data.section]: data.updated_content,
        });
      }
      setToastMessage(`Section "${data.section}" refreshed with updated AI analysis.`);
      setTimeout(() => setToastMessage(null), 4000);
    }
  });

  // Save Profile Mutation
  const saveProfileMutation = useMutation({
    mutationFn: () => api.saveBusinessProfile(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-profile'] });
      setToastMessage('Business Profile saved successfully.');
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">AI Growth Strategy</h2>
          <p className="text-xs text-slate-500 mt-1">
            Formulate high-ROI 30-day marketing roadmaps, ideal customer profiles, and channel allocation plans.
          </p>
        </div>

        {strategies && strategies.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Saved Playbooks:</span>
            <select
              value={activeStrategy?.id || ''}
              onChange={(e) => {
                const found = strategies.find((s) => s.id === Number(e.target.value));
                if (found) setActiveStrategy(found);
              }}
              className="text-xs bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} ({new Date(s.created_at).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Form: Business Profile Inputs (4 Cols) */}
        <div className="lg:col-span-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-5 h-fit">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600" />
              <span>Business Profile Inputs</span>
            </h3>
            <button
              onClick={() => saveProfileMutation.mutate()}
              disabled={saveProfileMutation.isPending}
              className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Profile</span>
            </button>
          </div>

          <div className="space-y-4 text-xs">
            {/* Company Name */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Company Name</label>
              <input
                type="text"
                value={formData.company_name || ''}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Industry */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Industry</label>
              <input
                type="text"
                value={formData.industry || ''}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Website */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Website URL (Optional)</label>
              <input
                type="text"
                value={formData.website || ''}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Business Description</label>
              <textarea
                rows={3}
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Services */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Services Offered (comma separated)</label>
              <input
                type="text"
                value={(formData.services || []).join(', ')}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    services: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Target Audience */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Target Audience (comma separated)</label>
              <input
                type="text"
                value={(formData.target_audience || []).join(', ')}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    target_audience: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Target Geography */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Target Geography</label>
              <input
                type="text"
                value={(formData.target_geography || []).join(', ')}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    target_geography: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Monthly Budget */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Monthly Marketing Budget ($)</label>
              <input
                type="number"
                value={formData.monthly_budget || 0}
                onChange={(e) => setFormData({ ...formData, monthly_budget: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Primary Objective */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Main Business Objective</label>
              <input
                type="text"
                value={formData.main_objective || ''}
                onChange={(e) => setFormData({ ...formData, main_objective: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {generateMutation.isError && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs space-y-2 mt-4">
                <div className="flex items-center gap-1.5 font-bold text-rose-700">
                  <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
                  <span>AI Request Failed</span>
                </div>
                <p className="text-[11px] leading-relaxed">
                  {(generateMutation.error as any)?.message || 'The Gemini API failed to generate a strategy.'}
                </p>
                <button
                  type="button"
                  onClick={() => generateMutation.mutate({ force_demo_mode: true })}
                  className="w-full mt-1 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center justify-center gap-1.5"
                >
                  <Cpu className="w-3.5 h-3.5" />
                  <span>Generate in Demo Mode Instead</span>
                </button>
              </div>
            )}

            {/* Generate Action Button */}
            <button
              onClick={() => generateMutation.mutate({ force_demo_mode: false })}
              disabled={generateMutation.isPending}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 mt-4"
            >
              {generateMutation.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Synthesizing Strategy via Gemini...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Growth Strategy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Output: 10 Structured Strategy Sections (8 Cols) */}
        <div className="lg:col-span-8 space-y-6">
          {activeStrategy ? (
            <>
              {/* Strategy Header Card */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm relative overflow-hidden">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                      B2B Growth Playbook
                    </span>
                    {activeStrategy.is_demo ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                        <Cpu className="w-3 h-3" />
                        Demo Simulation
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        Gemini AI
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-400">
                    Created {new Date(activeStrategy.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  {activeStrategy.title}
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {activeStrategy.summary}
                </p>
              </div>

              {/* Model Assumptions & Uncertainty Disclosures */}
              {activeStrategy.assumptions_and_uncertainties && activeStrategy.assumptions_and_uncertainties.length > 0 && (
                <div className="bg-amber-50/70 p-4 rounded-2xl border border-amber-200/80 shadow-sm space-y-2">
                  <h4 className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    <span>Model Assumptions & Uncertainty Disclosures</span>
                  </h4>
                  <ul className="space-y-1 text-xs text-amber-900">
                    {activeStrategy.assumptions_and_uncertainties.map((item, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-[11px]">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Unique Value Proposition */}
              <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white p-6 rounded-2xl shadow-md">
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300">
                  Unique Value Proposition (UVP)
                </span>
                <p className="text-sm font-medium mt-1 leading-relaxed">
                  "{activeStrategy.unique_value_proposition}"
                </p>
              </div>

              {/* 1. Ideal Customer Profiles (ICPs) */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Users className="w-4 h-4 text-indigo-600" />
                    <span>Ideal Customer Profiles (ICPs)</span>
                  </h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {activeStrategy.ideal_customer_profiles.map((icp, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                      <div className="font-bold text-xs text-indigo-700">{icp.persona_title}</div>
                      <p className="text-[11px] text-slate-600">
                        <strong>Target Company:</strong> {icp.company_profile}
                      </p>
                      <p className="text-[11px] text-slate-600">
                        <strong>Core Need:</strong> {icp.core_need}
                      </p>
                      <p className="text-[11px] text-slate-500 italic">
                        <strong>Trigger:</strong> {icp.buying_trigger}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 2. Market Insights & Pain Points Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Market Insights */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                    <Target className="w-4 h-4 text-violet-600" />
                    <span>Target Market Insights</span>
                  </h4>
                  <ul className="space-y-2.5 text-xs text-slate-600">
                    {activeStrategy.target_market_insights.map((ins, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-violet-600 mt-1.5 shrink-0" />
                        <span>{ins}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Customer Pain Points */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span>Core Customer Pain Points</span>
                  </h4>
                  <ul className="space-y-2.5 text-xs text-slate-600">
                    {activeStrategy.customer_pain_points.map((p, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 3. Recommended Channels & Budget Allocation */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-emerald-600" />
                    <span>Recommended Channels & Budget Allocation</span>
                  </h4>
                  <button
                    onClick={() => regenSectionMutation.mutate('recommended_channels')}
                    disabled={regenSectionMutation.isPending}
                    className="text-[11px] text-slate-500 hover:text-indigo-600 flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" /> Refresh
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {activeStrategy.recommended_channels.map((chan, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-xs text-slate-800">{chan.channel}</span>
                        <span className="text-xs font-extrabold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          {chan.budget_allocation_pct}%
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500">{chan.rationale}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 4. Strategic Objectives & Suggested KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Objectives */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 mb-3">Measurable Objectives</h4>
                  <div className="space-y-3">
                    {activeStrategy.marketing_objectives.map((obj, i) => (
                      <div key={i} className="text-xs p-3 rounded-xl bg-slate-50 border border-slate-200/70">
                        <p className="font-semibold text-slate-900">{obj.objective}</p>
                        <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                          <span className="text-indigo-600 font-medium">Target: {obj.target_metric}</span>
                          <span>{obj.timeline}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* KPIs */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 mb-3">Key Performance Indicators</h4>
                  <div className="space-y-3">
                    {activeStrategy.suggested_kpis.map((kpi, i) => (
                      <div key={i} className="text-xs p-3 rounded-xl bg-slate-50 border border-slate-200/70">
                        <p className="font-semibold text-slate-900">{kpi.kpi_name}</p>
                        <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                          <span className="text-emerald-600 font-medium">{kpi.target}</span>
                          <span>{kpi.measurement_frequency}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 5. 30-Day Phased Action Plan */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-indigo-600" />
                    <span>30-Day Phased Action Plan</span>
                  </h4>
                  <button
                    onClick={() => regenSectionMutation.mutate('thirty_day_plan')}
                    disabled={regenSectionMutation.isPending}
                    className="text-[11px] text-slate-500 hover:text-indigo-600 flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" /> Refresh
                  </button>
                </div>

                <div className="space-y-4">
                  {activeStrategy.thirty_day_plan.map((phase, pIdx) => (
                    <div key={pIdx} className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                          {phase.day_range}
                        </span>
                        <span className="text-xs font-semibold text-slate-800">{phase.focus_area}</span>
                      </div>
                      <ul className="space-y-1.5 text-xs text-slate-600 pl-1">
                        {phase.actionable_tasks.map((task, tIdx) => (
                          <li key={tIdx} className="flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 shrink-0" />
                            <span>{task}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3">
              <Compass className="w-12 h-12 text-slate-300 mx-auto" />
              <h4 className="text-base font-bold text-slate-800">No Strategy Generated Yet</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Fill in your company details in the left panel and click "Generate Growth Strategy" to build a customized 30-day playbook with Gemini.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
