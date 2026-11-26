import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- Health & Config Schemas ---
class HealthResponse(BaseModel):
    status: str
    environment: str
    database: str
    ai_status: str
    ai_model: str
    demo_mode: bool

class GeminiKeyUpdateRequest(BaseModel):
    gemini_api_key: str
    gemini_model: Optional[str] = "gemini-2.5-flash"

# --- Business Profile Schemas ---
class BusinessProfileBase(BaseModel):
    company_name: str
    industry: str
    website: Optional[str] = ""
    description: str
    services: List[str] = []
    target_audience: List[str] = []
    target_geography: List[str] = []
    monthly_budget: float = 0.0
    main_objective: str
    competitors: List[str] = []
    preferred_channels: List[str] = []

class BusinessProfileCreate(BusinessProfileBase):
    pass

class BusinessProfileResponse(BusinessProfileBase):
    id: int
    is_demo: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- Growth Strategy Schemas ---
class GenerateStrategyRequest(BaseModel):
    business_profile_id: Optional[int] = None
    profile_override: Optional[BusinessProfileBase] = None
    force_demo_mode: bool = False

class StrategySectionRegenerateRequest(BaseModel):
    strategy_id: int
    section_name: str
    force_demo_mode: bool = False

class GrowthStrategyResponse(BaseModel):
    id: int
    business_profile_id: Optional[int] = None
    title: str
    summary: str
    ideal_customer_profiles: List[Dict[str, Any]] = []
    target_market_insights: List[str] = []
    customer_pain_points: List[str] = []
    unique_value_proposition: str
    marketing_objectives: List[Dict[str, Any]] = []
    recommended_channels: List[Dict[str, Any]] = []
    campaign_recommendations: List[Dict[str, Any]] = []
    suggested_kpis: List[Dict[str, Any]] = []
    thirty_day_plan: List[Dict[str, Any]] = []
    assumptions_and_uncertainties: List[str] = []
    is_demo: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class GenerateStrategyResponse(BaseModel):
    strategy: GrowthStrategyResponse
    metadata: Dict[str, Any]

# --- Campaign Studio Schemas ---
class GenerateCampaignRequest(BaseModel):
    name: str
    product_service: str
    target_audience: str
    objective: str
    channel: str # LinkedIn, Instagram, Email, Google Ads, Landing Page
    tone: str = "Professional & Authoritative"
    key_selling_points: Optional[str] = ""
    call_to_action: Optional[str] = ""
    additional_instructions: Optional[str] = ""
    force_demo_mode: bool = False

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    overview: Optional[str] = None
    main_message: Optional[str] = None
    headlines: Optional[List[str]] = None
    content_variations: Optional[List[Dict[str, Any]]] = None
    suggested_cta: Optional[str] = None
    recommended_audience: Optional[str] = None
    hashtags: Optional[List[str]] = None
    suggested_schedule: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    product_service: str
    target_audience: str
    objective: str
    channel: str
    tone: str
    key_selling_points: Optional[str] = ""
    call_to_action: Optional[str] = ""
    additional_instructions: Optional[str] = ""
    overview: str
    main_message: str
    headlines: List[str] = []
    content_variations: List[Dict[str, Any]] = []
    suggested_cta: Optional[str] = ""
    recommended_audience: Optional[str] = ""
    hashtags: List[str] = []
    suggested_schedule: List[Dict[str, Any]] = []
    status: str = "Draft"
    is_demo: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class GenerateCampaignResponse(BaseModel):
    campaign: CampaignResponse
    metadata: Dict[str, Any]

# --- Content Calendar Schemas ---
class GenerateContentPlanRequest(BaseModel):
    days: int = 7
    focus_channel: Optional[str] = "All Channels"
    campaign_id: Optional[int] = None
    theme: Optional[str] = None
    force_demo_mode: bool = False

class ContentItemCreate(BaseModel):
    title: str
    channel: str
    publication_date: datetime.datetime
    status: str = "Draft"
    content_text: str
    target_audience: Optional[str] = ""
    tags: List[str] = []
    campaign_id: Optional[int] = None

class ContentItemUpdate(BaseModel):
    title: Optional[str] = None
    channel: Optional[str] = None
    publication_date: Optional[datetime.datetime] = None
    status: Optional[str] = None
    content_text: Optional[str] = None
    target_audience: Optional[str] = None
    tags: Optional[List[str]] = None
    campaign_id: Optional[int] = None

class ContentItemResponse(BaseModel):
    id: int
    campaign_id: Optional[int] = None
    title: str
    channel: str
    publication_date: datetime.datetime
    status: str
    content_text: str
    target_audience: Optional[str] = ""
    tags: List[str] = []
    is_demo: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class GenerateContentPlanResponse(BaseModel):
    items: List[ContentItemResponse]
    metadata: Dict[str, Any]

# --- Lead Intelligence Schemas ---
class LeadCreate(BaseModel):
    name: str
    company: str
    email: str
    website: Optional[str] = ""
    industry: str
    job_title: Optional[str] = ""
    location: Optional[str] = ""
    company_size: Optional[str] = ""
    lead_source: Optional[str] = "Direct"

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    company_size: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    qualification_category: Optional[str] = None
    business_fit_summary: Optional[str] = None
    suggested_next_action: Optional[str] = None

class LeadNoteCreate(BaseModel):
    note_text: str

class LeadNoteResponse(BaseModel):
    id: int
    lead_id: int
    note_text: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class LeadResponse(BaseModel):
    id: int
    name: str
    company: str
    email: str
    website: Optional[str] = ""
    industry: str
    job_title: Optional[str] = ""
    location: Optional[str] = ""
    company_size: Optional[str] = ""
    lead_source: Optional[str] = ""
    score: int = 0
    qualification_category: str = "Low Priority"
    business_fit_summary: Optional[str] = ""
    suggested_next_action: Optional[str] = ""
    score_explanation: Dict[str, Any] = {}
    status: str = "New"
    is_demo: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime
    notes: List[LeadNoteResponse] = []

    model_config = ConfigDict(from_attributes=True)

class CSVImportResult(BaseModel):
    total_rows: int
    successful_imports: int
    duplicate_count: int
    error_count: int
    errors: List[str] = []
    sample_leads: List[LeadResponse] = []

# --- Prompt Lab Schemas ---
class PromptTemplateResponse(BaseModel):
    id: int
    category: str
    name: str
    version: str
    system_instructions: str
    user_prompt_template: str
    notes: Optional[str] = ""
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class PromptExecutionResponse(BaseModel):
    id: int
    feature_name: str
    prompt_template_id: Optional[int] = None
    prompt_version: str
    system_instruction_used: Optional[str] = ""
    prompt_rendered: str
    user_inputs: Dict[str, Any] = {}
    model_used: str
    execution_status: str
    error_message: Optional[str] = None
    latency_ms: int
    generated_output: Dict[str, Any] = {}
    is_example: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- AI Activity Schema ---
class AIActivityResponse(BaseModel):
    id: int
    activity_type: str
    title: str
    description: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    is_demo: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- Campaign Metric Schemas ---
class CampaignMetricCreate(BaseModel):
    campaign_id: Optional[int] = None
    metric_date: datetime.date
    channel: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0

class CampaignMetricResponse(BaseModel):
    id: int
    campaign_id: Optional[int] = None
    metric_date: datetime.date
    channel: str
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    ctr: Optional[float] = None
    cpl: Optional[float] = None
    roi: Optional[float] = None
    is_demo: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class CampaignMetricsImportResult(BaseModel):
    total_rows: int
    successful_imports: int
    error_count: int
    errors: List[str] = []

# --- Analytics Overview Schema ---
class AnalyticsOverviewResponse(BaseModel):
    total_leads: int
    qualified_leads: int
    qualification_rate: float
    average_lead_score: float
    active_campaigns: int
    content_generated_count: int
    leads_by_category: Dict[str, int]
    leads_by_source: Dict[str, int]
    leads_by_industry: Dict[str, int]
    leads_by_geography: Dict[str, int]
    monthly_activity: List[Dict[str, Any]]
    lead_acquisition_trend: List[Dict[str, Any]]
    campaign_performance: List[Dict[str, Any]]
    recent_activities: List[AIActivityResponse]
    high_priority_leads: List[LeadResponse]
    upcoming_content: List[ContentItemResponse]
    is_demo_data: bool = True
    has_sufficient_history: bool = True
    total_spend: float = 0.0
    total_revenue: float = 0.0

# --- Strict AI Structured Response Models ---
class ScoreFactorBreakdown(BaseModel):
    score: int = Field(..., ge=0)
    max: int = Field(..., ge=1)
    reason: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.score > self.max:
            raise ValueError(f"Score {self.score} cannot exceed maximum allowed {self.max}.")
        return self

class LeadScoreExplanation(BaseModel):
    industry_alignment: ScoreFactorBreakdown
    decision_maker_authority: ScoreFactorBreakdown
    geographic_match: ScoreFactorBreakdown
    company_size_fit: ScoreFactorBreakdown
    source_intent: ScoreFactorBreakdown

class LeadScoringAIResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    qualification_category: str
    business_fit_summary: str = Field(..., min_length=1)
    suggested_next_action: str = Field(..., min_length=1)
    score_explanation: LeadScoreExplanation

    @model_validator(mode="after")
    def validate_category_and_bounds(self):
        cat = self.qualification_category
        valid_cats = {"High Priority", "Medium Priority", "Low Priority"}
        if cat not in valid_cats:
            raise ValueError(f"Invalid qualification_category '{cat}'. Must be one of {valid_cats}.")

        # Enforce consistency between score and category
        if self.score >= 75 and cat != "High Priority":
            raise ValueError(f"Category mismatch: score {self.score} requires 'High Priority', got '{cat}'.")
        elif 50 <= self.score < 75 and cat != "Medium Priority":
            raise ValueError(f"Category mismatch: score {self.score} requires 'Medium Priority', got '{cat}'.")
        elif self.score < 50 and cat != "Low Priority":
            raise ValueError(f"Category mismatch: score {self.score} requires 'Low Priority', got '{cat}'.")

        # Validate max bounds for individual factors
        exp = self.score_explanation
        if exp.industry_alignment.score > exp.industry_alignment.max:
            raise ValueError(f"Industry score {exp.industry_alignment.score} exceeds max {exp.industry_alignment.max}.")
        if exp.decision_maker_authority.score > exp.decision_maker_authority.max:
            raise ValueError(f"Authority score {exp.decision_maker_authority.score} exceeds max {exp.decision_maker_authority.max}.")
        if exp.geographic_match.score > exp.geographic_match.max:
            raise ValueError(f"Geography score {exp.geographic_match.score} exceeds max {exp.geographic_match.max}.")
        if exp.company_size_fit.score > exp.company_size_fit.max:
            raise ValueError(f"Company size score {exp.company_size_fit.score} exceeds max {exp.company_size_fit.max}.")
        if exp.source_intent.score > exp.source_intent.max:
            raise ValueError(f"Source intent score {exp.source_intent.score} exceeds max {exp.source_intent.max}.")

        return self

class StrategyAIResponse(BaseModel):
    summary: str = Field(..., min_length=1)
    ideal_customer_profiles: List[Dict[str, Any]] = Field(..., min_length=1)
    target_market_insights: List[str] = Field(..., min_length=1)
    customer_pain_points: List[str] = Field(..., min_length=1)
    unique_value_proposition: str = Field(..., min_length=1)
    marketing_objectives: List[Dict[str, Any]] = Field(..., min_length=1)
    recommended_channels: List[Dict[str, Any]] = Field(..., min_length=1)
    campaign_recommendations: List[Dict[str, Any]] = Field(..., min_length=1)
    suggested_kpis: List[Dict[str, Any]] = Field(..., min_length=1)
    thirty_day_plan: List[Dict[str, Any]] = Field(..., min_length=1)

class CampaignAIResponse(BaseModel):
    overview: str = Field(..., min_length=1)
    main_message: str = Field(..., min_length=1)
    headlines: List[str] = Field(..., min_length=3)
    content_variations: List[Dict[str, Any]] = Field(..., min_length=2)
    suggested_cta: str = Field(..., min_length=1)

class ContentPlanAIResponse(BaseModel):
    items: List[Dict[str, Any]] = Field(..., min_length=1)

