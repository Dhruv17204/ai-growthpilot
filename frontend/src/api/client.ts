import {
  BusinessProfile,
  GrowthStrategy,
  Campaign,
  ContentItem,
  Lead,
  CSVImportResult,
  PromptTemplate,
  PromptExecution,
  AIActivity,
  AnalyticsOverview,
  HealthInfo,
} from '../types';

const API_BASE = '/api';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetail = 'Network request failed';
    try {
      const err = await res.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Health & Config
  getHealth: () => fetchJson<HealthInfo>('/health'),
  getAIConfig: () => fetchJson<{ model: string; is_configured: boolean; status_check: any; masked_key: string }>('/settings/ai-config'),
  updateGeminiKey: (apiKey: string, model: string) =>
    fetchJson<{ message: string; test_result: any }>('/settings/gemini-key', {
      method: 'POST',
      body: JSON.stringify({ gemini_api_key: apiKey, gemini_model: model }),
    }),
  resetDemoData: () => fetchJson<{ message: string }>('/settings/reset-demo', { method: 'POST' }),

  // Business Profile
  getProfile: () => fetchJson<BusinessProfile>('/business-profile'),
  saveProfile: (profile: Partial<BusinessProfile>) =>
    fetchJson<BusinessProfile>('/business-profile', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),

  // AI Strategy
  getStrategies: () => fetchJson<GrowthStrategy[]>('/strategies'),
  getStrategy: (id: number) => fetchJson<GrowthStrategy>(`/strategies/${id}`),
  generateStrategy: (params: { business_profile_id?: number; profile_override?: any }) =>
    fetchJson<{ strategy: GrowthStrategy; metadata: any }>('/ai/strategy', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  regenerateStrategySection: (strategyId: number, sectionName: string) =>
    fetchJson<{ section: string; updated_content: any }>('/ai/strategy/regenerate-section', {
      method: 'POST',
      body: JSON.stringify({ strategy_id: strategyId, section_name: sectionName }),
    }),

  // Campaigns
  getCampaigns: () => fetchJson<Campaign[]>('/campaigns'),
  getCampaign: (id: number) => fetchJson<Campaign>(`/campaigns/${id}`),
  generateCampaign: (params: {
    name: string;
    product_service: string;
    target_audience: string;
    objective: string;
    channel: string;
    tone: string;
    key_selling_points?: string;
    call_to_action?: string;
    additional_instructions?: string;
  }) =>
    fetchJson<{ campaign: Campaign; metadata: any }>('/ai/campaign', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  updateCampaign: (id: number, data: Partial<Campaign>) =>
    fetchJson<Campaign>(`/campaigns/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteCampaign: (id: number) =>
    fetchJson<{ message: string }>(`/campaigns/${id}`, { method: 'DELETE' }),

  // Content Calendar
  getContentItems: () => fetchJson<ContentItem[]>('/content'),
  generateContentPlan: (params: { days: number; focus_channel?: string; theme?: string; campaign_id?: number }) =>
    fetchJson<{ items: ContentItem[]; metadata: any }>('/ai/content-plan', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  createContentItem: (item: Partial<ContentItem>) =>
    fetchJson<ContentItem>('/content', {
      method: 'POST',
      body: JSON.stringify(item),
    }),
  updateContentItem: (id: number, item: Partial<ContentItem>) =>
    fetchJson<ContentItem>(`/content/${id}`, {
      method: 'PUT',
      body: JSON.stringify(item),
    }),
  deleteContentItem: (id: number) =>
    fetchJson<{ message: string }>(`/content/${id}`, { method: 'DELETE' }),

  // Lead Intelligence
  getLeads: (params?: { search?: string; category?: string; status?: string; source?: string; sort_by?: string; sort_order?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set('search', params.search);
    if (params?.category) q.set('category', params.category);
    if (params?.status) q.set('status', params.status);
    if (params?.source) q.set('source', params.source);
    if (params?.sort_by) q.set('sort_by', params.sort_by);
    if (params?.sort_order) q.set('sort_order', params.sort_order);
    return fetchJson<Lead[]>(`/leads?${q.toString()}`);
  },
  getLead: (id: number) => fetchJson<Lead>(`/leads/${id}`),
  updateLead: (id: number, data: Partial<Lead>) =>
    fetchJson<Lead>(`/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  recalculateLeadScore: (id: number) =>
    fetchJson<{ message: string; result: any }>(`/leads/${id}/score`, { method: 'POST' }),
  addLeadNote: (leadId: number, noteText: string) =>
    fetchJson<any>(`/leads/${leadId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ note_text: noteText }),
    }),
  importLeadsCSV: async (file: File): Promise<CSVImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/leads/import`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to upload CSV' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  // Analytics
  getAnalytics: () => fetchJson<AnalyticsOverview>('/analytics/overview'),

  // Prompt Lab
  getPromptTemplates: () => fetchJson<PromptTemplate[]>('/prompts'),
  getPromptExecutions: (limit: number = 50) =>
    fetchJson<PromptExecution[]>(`/prompts/history?limit=${limit}`),
  getAIActivities: (limit: number = 25) =>
    fetchJson<AIActivity[]>(`/ai/activity?limit=${limit}`),
};
