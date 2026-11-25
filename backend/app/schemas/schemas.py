import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

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
