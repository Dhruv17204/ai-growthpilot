export interface BusinessProfile {
  id: number;
  company_name: string;
  industry: string;
  website?: string;
  description: string;
  services: string[];
  target_audience: string[];
  target_geography: string[];
  monthly_budget: number;
  main_objective: string;
  competitors: string[];
  preferred_channels: string[];
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface IdealCustomerProfile {
  persona_title: string;
  company_profile: string;
  core_need: string;
  buying_trigger: string;
}

export interface MarketingObjective {
  objective: string;
  target_metric: string;
  timeline: string;
}

export interface RecommendedChannel {
  channel: string;
  rationale: string;
  budget_allocation_pct: number;
}

export interface CampaignRecommendation {
  campaign_name: string;
  channel: string;
  goal: string;
  tactical_description: string;
}

export interface SuggestedKPI {
  kpi_name: string;
  target: string;
  measurement_frequency: string;
}

export interface ThirtyDayPlanItem {
  day_range: string;
  focus_area: string;
  actionable_tasks: string[];
}

export interface GrowthStrategy {
  id: number;
  business_profile_id?: number;
  title: string;
  summary: string;
  ideal_customer_profiles: IdealCustomerProfile[];
  target_market_insights: string[];
  customer_pain_points: string[];
  unique_value_proposition: string;
  marketing_objectives: MarketingObjective[];
  recommended_channels: RecommendedChannel[];
  campaign_recommendations: CampaignRecommendation[];
  suggested_kpis: SuggestedKPI[];
  thirty_day_plan: ThirtyDayPlanItem[];
  assumptions_and_uncertainties?: string[];
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContentVariation {
  variant_name: string;
  angle: string;
  copy_text: string;
}

export interface ScheduleItem {
  day: string;
  activity: string;
  purpose: string;
}

export interface Campaign {
  id: number;
  name: string;
  product_service: string;
  target_audience: string;
  objective: string;
  channel: string;
  tone: string;
  key_selling_points?: string;
  call_to_action?: string;
  additional_instructions?: string;
  overview: string;
  main_message: string;
  headlines: string[];
  content_variations: ContentVariation[];
  suggested_cta?: string;
  recommended_audience?: string;
  hashtags: string[];
  suggested_schedule: ScheduleItem[];
  status: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContentItem {
  id: number;
  campaign_id?: number;
  title: string;
  channel: string;
  publication_date: string;
  status: 'Draft' | 'Pending Approval' | 'Approved' | 'Published';
  content_text: string;
  target_audience?: string;
  tags: string[];
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScoreExplanationItem {
  score: number;
  max: number;
  reason: string;
}

export interface ScoreExplanation {
  industry_alignment?: ScoreExplanationItem;
  decision_maker_authority?: ScoreExplanationItem;
  geographic_match?: ScoreExplanationItem;
  company_size_fit?: ScoreExplanationItem;
  source_intent?: ScoreExplanationItem;
}

export interface LeadNote {
  id: number;
  lead_id: number;
  note_text: string;
  created_at: string;
}

export interface Lead {
  id: number;
  name: string;
  company: string;
  email: string;
  website?: string;
  industry: string;
  job_title?: string;
  location?: string;
  company_size?: string;
  lead_source?: string;
  score: number;
  qualification_category: 'High Priority' | 'Medium Priority' | 'Low Priority';
  business_fit_summary?: string;
  suggested_next_action?: string;
  score_explanation: ScoreExplanation;
  status: 'New' | 'Contacted' | 'In Discussion' | 'Qualified' | 'Disqualified';
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  notes: LeadNote[];
}

export interface CSVImportResult {
  total_rows: number;
  successful_imports: number;
  duplicate_count: number;
  error_count: number;
  errors: string[];
  sample_leads: Lead[];
}

export interface PromptTemplate {
  id: number;
  category: string;
  name: string;
  version: string;
  system_instructions: string;
  user_prompt_template: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
}

export interface PromptExecution {
  id: number;
  feature_name: string;
  prompt_template_id?: number;
  prompt_version: string;
  system_instruction_used?: string;
  prompt_rendered: string;
  user_inputs: Record<string, any>;
  model_used: string;
  execution_status: 'success' | 'fallback_demo' | 'error';
  error_message?: string;
  latency_ms: number;
  generated_output: Record<string, any>;
  is_example: boolean;
  created_at: string;
}

export interface AIActivity {
  id: number;
  activity_type: string;
  title: string;
  description: string;
  entity_type?: string;
  entity_id?: number;
  is_demo: boolean;
  created_at: string;
}

export interface AnalyticsOverview {
  total_leads: number;
  qualified_leads: number;
  qualification_rate: number;
  average_lead_score: number;
  active_campaigns: number;
  content_generated_count: number;
  leads_by_category: Record<string, number>;
  leads_by_source: Record<string, number>;
  leads_by_industry: Record<string, number>;
  leads_by_geography: Record<string, number>;
  monthly_activity: { activity: string; count: number }[];
  lead_acquisition_trend: { month: string; leads: number; qualified: number }[];
  campaign_performance: {
    name: string;
    channel: string;
    impressions: number;
    clicks: number;
    leads: number;
    status: string;
  }[];
  recent_activities: AIActivity[];
  high_priority_leads: Lead[];
  upcoming_content: ContentItem[];
  is_demo_data: boolean;
}

export interface HealthInfo {
  status: string;
  environment: string;
  database: string;
  ai_status: string;
  ai_model: string;
  demo_mode: boolean;
}

export type HealthStatus = HealthInfo;

export interface CampaignMetric {
  id: number;
  campaign_id?: number;
  date: string;
  channel: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  ctr?: number;
  cpl?: number;
  roi?: number;
  is_demo: boolean;
  created_at: string;
}

