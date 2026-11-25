import {
  BusinessProfile,
  GrowthStrategy,
  Campaign,
  ContentItem,
  Lead,
  LeadNote,
  CSVImportResult,
  PromptTemplate,
  PromptExecution,
  AIActivity,
  AnalyticsOverview,
  HealthStatus,
  CampaignMetric,
} from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE as string) || '/api';

export async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Normalize leading slash
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${cleanEndpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err: any) {
    throw new Error(`Network connection error: ${err?.message || 'Unable to reach backend service.'}`);
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: Request failed`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // Body was not JSON, fallback to status text
      if (response.statusText) {
        errorDetail = `HTTP ${response.status}: ${response.statusText}`;
      }
    }
    const error = new Error(errorDetail);
    (error as any).status = response.status;
    throw error;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Single authoritative API client
export const api = {
  // Health & Config
  getHealth: () => fetchJson<HealthStatus>('/health'),
  healthCheck: () => fetchJson<HealthStatus>('/health'),
  getAIConfig: () =>
    fetchJson<{
      model: string;
      is_configured: boolean;
      status_check: any;
      masked_key: string;
    }>('/settings/ai-config'),
  updateGeminiKey: (apiKey: string, model: string = 'gemini-2.5-flash') =>
    fetchJson<{ message: string; test_result: any }>('/settings/gemini-key', {
      method: 'POST',
      body: JSON.stringify({ gemini_api_key: apiKey, gemini_model: model }),
    }),
  resetDemoData: () =>
    fetchJson<{ message: string }>('/settings/reset-demo', { method: 'POST' }),

  // Business Profile (canonical + aliases)
  getBusinessProfile: () => fetchJson<BusinessProfile>('/business-profile'),
  getProfile: () => fetchJson<BusinessProfile>('/business-profile'),
  saveBusinessProfile: (profile: Partial<BusinessProfile>) =>
    fetchJson<BusinessProfile>('/business-profile', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),
  saveProfile: (profile: Partial<BusinessProfile>) =>
    fetchJson<BusinessProfile>('/business-profile', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),

  // AI Growth Strategy
  getStrategies: () => fetchJson<GrowthStrategy[]>('/strategies'),
  getStrategy: (id: number) => fetchJson<GrowthStrategy>(`/strategies/${id}`),
  generateStrategy: (payload: {
    business_profile_id?: number;
    profile_override?: Partial<BusinessProfile>;
    force_demo_mode?: boolean;
  }) =>
    fetchJson<{ strategy: GrowthStrategy; metadata: any }>('/ai/strategy', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  regenerateStrategySection: (
    strategyId: number,
    sectionName: string,
    force_demo_mode: boolean = false
  ) =>
    fetchJson<{ section: string; updated_content: any }>(
      '/ai/strategy/regenerate-section',
      {
        method: 'POST',
        body: JSON.stringify({
          strategy_id: strategyId,
          section_name: sectionName,
          force_demo_mode,
        }),
      }
    ),

  // Campaign Studio
  getCampaigns: () => fetchJson<Campaign[]>('/campaigns'),
  getCampaign: (id: number) => fetchJson<Campaign>(`/campaigns/${id}`),
  generateCampaign: (campaignData: {
    name: string;
    product_service: string;
    target_audience: string;
    objective: string;
    channel: string;
    tone: string;
    key_selling_points?: string;
    call_to_action?: string;
    additional_instructions?: string;
    force_demo_mode?: boolean;
  }) =>
    fetchJson<{ campaign: Campaign; metadata: any }>('/ai/campaign', {
      method: 'POST',
      body: JSON.stringify(campaignData),
    }),
  updateCampaign: (id: number, data: Partial<Campaign>) =>
    fetchJson<Campaign>(`/campaigns/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteCampaign: (id: number) =>
    fetchJson<{ message: string }>(`/campaigns/${id}`, { method: 'DELETE' }),

  // Content Calendar (canonical + aliases)
  getContent: () => fetchJson<ContentItem[]>('/content'),
  getContentItems: () => fetchJson<ContentItem[]>('/content'),
  generateContentPlan: (payload: {
    days: number;
    focus_channel?: string;
    campaign_id?: number;
    theme?: string;
    force_demo_mode?: boolean;
  }) =>
    fetchJson<{ items: ContentItem[]; metadata: any }>('/ai/content-plan', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  createContentItem: (item: Partial<ContentItem>) =>
    fetchJson<ContentItem>('/content', {
      method: 'POST',
      body: JSON.stringify(item),
    }),
  updateContentItem: (id: number, data: Partial<ContentItem>) =>
    fetchJson<ContentItem>(`/content/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteContentItem: (id: number) =>
    fetchJson<{ message: string }>(`/content/${id}`, { method: 'DELETE' }),

  // Lead Intelligence
  getLeads: (params?: {
    search?: string;
    category?: string;
    status?: string;
    source?: string;
    sort_by?: string;
    sort_order?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.category) q.append('category', params.category);
    if (params?.status) q.append('status', params.status);
    if (params?.source) q.append('source', params.source);
    if (params?.sort_by) q.append('sort_by', params.sort_by);
    if (params?.sort_order) q.append('sort_order', params.sort_order);
    const queryString = q.toString();
    return fetchJson<Lead[]>(`/leads${queryString ? `?${queryString}` : ''}`);
  },
  getLead: (id: number) => fetchJson<Lead>(`/leads/${id}`),
  updateLead: (id: number, data: Partial<Lead>) =>
    fetchJson<Lead>(`/leads/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  recalculateLeadScore: (id: number, force_demo_mode: boolean = false) =>
    fetchJson<{ message: string; result: any }>(
      `/leads/${id}/score?force_demo_mode=${force_demo_mode}`,
      { method: 'POST' }
    ),
  addLeadNote: (leadId: number, noteText: string) =>
    fetchJson<LeadNote>(`/leads/${leadId}/notes`, {
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
      let errDetail = 'CSV upload failed';
      try {
        const errJson = await res.json();
        errDetail = errJson.detail || errJson.message || errDetail;
      } catch {
        // fallback
      }
      throw new Error(errDetail);
    }
    return res.json();
  },
  exportLeadsCSVUrl: () => `${API_BASE}/leads/export`,
  exportLeadsUrl: `${API_BASE}/leads/export`,

  // Prompt Lab & Audit Telemetry
  getPromptTemplates: () => fetchJson<PromptTemplate[]>('/prompts'),
  getPromptHistory: () => fetchJson<PromptExecution[]>('/prompts/history'),
  getPromptExecutions: (limit: number = 50) =>
    fetchJson<PromptExecution[]>(`/prompts/history?limit=${limit}`),
  getAIActivities: (limit: number = 25) =>
    fetchJson<AIActivity[]>(`/ai/activity?limit=${limit}`),

  // Analytics Overview (canonical + aliases)
  getAnalyticsOverview: () => fetchJson<AnalyticsOverview>('/analytics/overview'),
  getAnalytics: () => fetchJson<AnalyticsOverview>('/analytics/overview'),

  // Campaign Metrics (Phase 2)
  getCampaignMetrics: (campaignId?: number) => {
    const q = campaignId ? `?campaign_id=${campaignId}` : '';
    return fetchJson<CampaignMetric[]>(`/analytics/campaign-metrics${q}`);
  },
  importCampaignMetricsCSV: async (file: File): Promise<{ message: string; rows_imported: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/analytics/campaign-metrics/import`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Metrics CSV import failed' }));
      throw new Error(err.detail || 'Metrics upload failed');
    }
    return res.json();
  },
  importCampaignMetrics: async (file: File) => api.importCampaignMetricsCSV(file),
};

export const exportLeadsCSVUrl = () => api.exportLeadsCSVUrl();
export const exportLeadsUrl = api.exportLeadsUrl;
export default api;
