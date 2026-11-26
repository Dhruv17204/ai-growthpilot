import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { Campaign, ContentVariation } from '../types';
import {
  Megaphone,
  Sparkles,
  Copy,
  Check,
  Calendar,
  Share2,
  Trash2,
  Edit3,
  Clock,
  Layers,
  CheckCircle2,
  Send,
  RefreshCw,
  Hash,
  Target,
  Cpu,
  AlertTriangle
} from 'lucide-react';

const CHANNELS = ['LinkedIn', 'Instagram', 'Email', 'Google Ads', 'Landing Page'];
const TONES = [
  'Professional & Authoritative',
  'Consultative & Value-First',
  'Direct-Response & Commercial',
  'Conversational & Technical',
  'Contrarian & Thought-Provoking'
];

export const CampaignStudioPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: api.getCampaigns,
  });

  const [formData, setFormData] = useState({
    name: 'Practical AI Audit Outreach',
    product_service: 'Custom AI Development & Workflow Automation',
    target_audience: 'Startup Founders & VPs of Operations in AU, US, and India',
    objective: 'Generate 20 qualified architecture discovery calls',
    channel: 'LinkedIn',
    tone: 'Professional & Authoritative',
    key_selling_points: '15-min architecture blueprint, identify $50k+ manual process waste, guaranteed IP ownership',
    call_to_action: 'Book a 15-Minute Technical Audit',
    additional_instructions: 'Keep copy concise, punchy, and highlight measurable ROI.',
  });

  const [activeCampaign, setActiveCampaign] = useState<Campaign | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [editingVariation, setEditingVariation] = useState<{ index: number; text: string } | null>(null);

  // Set active campaign on load
  React.useEffect(() => {
    if (campaigns && campaigns.length > 0 && !activeCampaign) {
      setActiveCampaign(campaigns[0]);
    }
  }, [campaigns, activeCampaign]);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setToastMessage('Copied to clipboard!');
    setTimeout(() => {
      setCopiedKey(null);
      setToastMessage(null);
    }, 2500);
  };

  // Generate Mutation
  const generateMutation = useMutation({
    mutationFn: (opts?: { force_demo_mode?: boolean }) =>
      api.generateCampaign({ ...formData, force_demo_mode: opts?.force_demo_mode ?? false }),
    onSuccess: (res) => {
      setActiveCampaign(res.campaign);
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-overview'] });
      const src = res.campaign.is_demo ? 'Demo Simulation' : 'Gemini AI';
      setToastMessage(`Multi-variation campaign successfully created via ${src}!`);
      setTimeout(() => setToastMessage(null), 4000);
    },
    onError: (err: any) => {
      setToastMessage(`AI Generation Note: ${err.message}`);
      setTimeout(() => setToastMessage(null), 5000);
    }
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteCampaign(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setActiveCampaign(null);
      setToastMessage('Campaign deleted.');
      setTimeout(() => setToastMessage(null), 3000);
    }
  });

  // Update variation text locally & in DB
  const handleSaveVariationEdit = async () => {
    if (!activeCampaign || editingVariation === null) return;
    const updatedVariations = [...activeCampaign.content_variations];
    updatedVariations[editingVariation.index].copy_text = editingVariation.text;

    try {
      const updated = await api.updateCampaign(activeCampaign.id, {
        content_variations: updatedVariations,
      });
      setActiveCampaign(updated);
      setEditingVariation(null);
      setToastMessage('Variation updated successfully.');
      setTimeout(() => setToastMessage(null), 3000);
    } catch (e: any) {
      setToastMessage(`Failed to update variation: ${e.message}`);
    }
  };

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
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Campaign Studio</h2>
          <p className="text-xs text-slate-500 mt-1">
            Build multi-angle, platform-native campaigns for LinkedIn, Instagram, Email, Google Ads, and Landing Pages.
          </p>
        </div>

        {campaigns && campaigns.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">History:</span>
            <select
              value={activeCampaign?.id || ''}
              onChange={(e) => {
                const found = campaigns.find((c) => c.id === Number(e.target.value));
                if (found) setActiveCampaign(found);
              }}
              className="text-xs bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.channel})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Form: Inputs (4 Cols) */}
        <div className="lg:col-span-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4 h-fit">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Megaphone className="w-4 h-4 text-indigo-600" />
              <span>Campaign Brief</span>
            </h3>
          </div>

          <div className="space-y-3.5 text-xs">
            {/* Campaign Name */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Campaign Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Channel & Tone in 2 cols */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Channel</label>
                <select
                  value={formData.channel}
                  onChange={(e) => setFormData({ ...formData, channel: e.target.value })}
                  className="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
                >
                  {CHANNELS.map((ch) => (
                    <option key={ch} value={ch}>{ch}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Tone</label>
                <select
                  value={formData.tone}
                  onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
                  className="w-full px-2 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none truncate"
                >
                  {TONES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Product / Service */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Product or Service</label>
              <input
                type="text"
                value={formData.product_service}
                onChange={(e) => setFormData({ ...formData, product_service: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Target Audience */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Target Audience</label>
              <input
                type="text"
                value={formData.target_audience}
                onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Campaign Objective */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Objective</label>
              <input
                type="text"
                value={formData.objective}
                onChange={(e) => setFormData({ ...formData, objective: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Key Selling Points */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Key Selling Points</label>
              <textarea
                rows={2}
                value={formData.key_selling_points}
                onChange={(e) => setFormData({ ...formData, key_selling_points: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Call to Action */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Call to Action (CTA)</label>
              <input
                type="text"
                value={formData.call_to_action}
                onChange={(e) => setFormData({ ...formData, call_to_action: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            {/* Additional Instructions */}
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Special Instructions (Optional)</label>
              <input
                type="text"
                value={formData.additional_instructions}
                onChange={(e) => setFormData({ ...formData, additional_instructions: e.target.value })}
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
                  {(generateMutation.error as any)?.message || 'The Gemini API failed to generate a campaign package.'}
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

            {/* Generate Button */}
            <button
              onClick={() => generateMutation.mutate({ force_demo_mode: false })}
              disabled={generateMutation.isPending}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 mt-4"
            >
              {generateMutation.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Drafting Copy Package via Gemini...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Campaign Package</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Output: Generated Package (8 Cols) */}
        <div className="lg:col-span-8 space-y-6">
          {activeCampaign ? (
            <>
              {/* Campaign Top Meta Card */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm relative">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {activeCampaign.channel}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600">
                      Tone: {activeCampaign.tone}
                    </span>
                    {activeCampaign.is_demo ? (
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
                  <button
                    onClick={() => deleteMutation.mutate(activeCampaign.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all"
                    title="Delete Campaign"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  {activeCampaign.name}
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {activeCampaign.overview}
                </p>

                {/* Core Narrative Anchor */}
                <div className="mt-4 p-3 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs">
                  <span className="font-bold text-indigo-900">Main Message Anchor: </span>
                  <span className="text-indigo-800">{activeCampaign.main_message}</span>
                </div>
              </div>

              {/* 3 Headline Variations */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4 text-violet-600" />
                  <span>3 Headline Variations</span>
                </h4>
                <div className="space-y-2.5">
                  {activeCampaign.headlines.map((hl, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between gap-3 text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 font-bold text-[10px] flex items-center justify-center shrink-0">
                          {i + 1}
                        </span>
                        <span className="font-semibold text-slate-800">{hl}</span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(hl, `headline-${i}`)}
                        className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:bg-indigo-50 hover:text-indigo-600 text-slate-600 font-medium text-[11px] shrink-0 flex items-center gap-1 transition-all"
                      >
                        {copiedKey === `headline-${i}` ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-600" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3 Content Variations with Copy and Edit */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <h4 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  <span>3 Multi-Angle Content Variations</span>
                </h4>

                <div className="space-y-4">
                  {activeCampaign.content_variations.map((variant, vIdx) => (
                    <div key={vIdx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-bold text-xs text-indigo-700">{variant.variant_name}</span>
                          <span className="text-[11px] text-slate-500 ml-2">({variant.angle})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setEditingVariation({ index: vIdx, text: variant.copy_text })}
                            className="p-1 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-200/60"
                            title="Edit Variation"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => copyToClipboard(variant.copy_text, `var-${vIdx}`)}
                            className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 font-medium text-[11px] flex items-center gap-1"
                          >
                            {copiedKey === `var-${vIdx}` ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-600" />
                                <span>Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                <span>Copy Draft</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Edit Modal / Inline edit or preview */}
                      {editingVariation && editingVariation.index === vIdx ? (
                        <div className="space-y-2">
                          <textarea
                            rows={6}
                            value={editingVariation.text}
                            onChange={(e) => setEditingVariation({ ...editingVariation, text: e.target.value })}
                            className="w-full p-3 bg-white border border-indigo-300 rounded-xl text-xs font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => setEditingVariation(null)}
                              className="px-3 py-1 rounded-lg text-xs text-slate-600 hover:bg-slate-200"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={handleSaveVariationEdit}
                              className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500"
                            >
                              Save Edit
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3.5 rounded-xl bg-white border border-slate-200/80 text-xs text-slate-800 whitespace-pre-line leading-relaxed font-sans">
                          {variant.copy_text}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Audience Targeting & Hashtags */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Recommended Audience
                  </span>
                  <p className="text-xs text-slate-700 mt-1.5 leading-relaxed">
                    {activeCampaign.recommended_audience || 'Target: Founders, Operations Directors, and Engineering VPs in AU, US, and India.'}
                  </p>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Suggested Hashtags
                  </span>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {activeCampaign.hashtags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        onClick={() => copyToClipboard(tag, `tag-${tIdx}`)}
                        className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 text-xs font-medium cursor-pointer transition-all"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Suggested Campaign Schedule */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-600" />
                  <span>Suggested Campaign Schedule</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {activeCampaign.suggested_schedule.map((sch, sIdx) => (
                    <div key={sIdx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
                      <div className="font-bold text-indigo-700 mb-1">{sch.day}</div>
                      <div className="font-semibold text-slate-800">{sch.activity}</div>
                      <div className="text-[11px] text-slate-500 mt-1">{sch.purpose}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3">
              <Megaphone className="w-12 h-12 text-slate-300 mx-auto" />
              <h4 className="text-base font-bold text-slate-800">No Campaign Selected</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Fill in the brief on the left and click "Generate Campaign Package" to draft platform-native multi-angle copy.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
