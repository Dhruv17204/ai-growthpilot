import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=False)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=False)
    services = Column(JSON, default=list)            # List[str]
    target_audience = Column(JSON, default=list)     # List[str]
    target_geography = Column(JSON, default=list)    # List[str]
    monthly_budget = Column(Float, default=0.0)
    main_objective = Column(String(255), nullable=False)
    competitors = Column(JSON, default=list)         # List[str]
    preferred_channels = Column(JSON, default=list)  # List[str]
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    strategies = relationship("GrowthStrategy", back_populates="business_profile", cascade="all, delete-orphan")


class GrowthStrategy(Base):
    __tablename__ = "growth_strategies"

    id = Column(Integer, primary_key=True, index=True)
    business_profile_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    ideal_customer_profiles = Column(JSON, default=list)
    target_market_insights = Column(JSON, default=list)
    customer_pain_points = Column(JSON, default=list)
    unique_value_proposition = Column(Text, nullable=False)
    marketing_objectives = Column(JSON, default=list)
    recommended_channels = Column(JSON, default=list)
    campaign_recommendations = Column(JSON, default=list)
    suggested_kpis = Column(JSON, default=list)
    thirty_day_plan = Column(JSON, default=list)
    assumptions_and_uncertainties = Column(JSON, default=list)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    business_profile = relationship("BusinessProfile", back_populates="strategies")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    product_service = Column(String(255), nullable=False)
    target_audience = Column(String(255), nullable=False)
    objective = Column(String(255), nullable=False)
    channel = Column(String(100), nullable=False)  # LinkedIn, Instagram, Email, Google Ads, Landing Page
    tone = Column(String(100), default="Professional & Authoritative")
    key_selling_points = Column(Text, nullable=True)
    call_to_action = Column(String(255), nullable=True)
    additional_instructions = Column(Text, nullable=True)
    overview = Column(Text, nullable=False)
    main_message = Column(Text, nullable=False)
    headlines = Column(JSON, default=list)              # List[str]
    content_variations = Column(JSON, default=list)     # List[dict(title, text)]
    suggested_cta = Column(String(255), nullable=True)
    recommended_audience = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list)               # List[str]
    suggested_schedule = Column(JSON, default=list)     # List[dict(day, action)]
    status = Column(String(50), default="Draft")        # Draft, Active, Completed, Paused
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    content_items = relationship("ContentItem", back_populates="campaign")


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    title = Column(String(255), nullable=False)
    channel = Column(String(100), nullable=False)       # LinkedIn, Instagram, Email, Blog, Google Ads
    publication_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="Draft")        # Draft, Pending Approval, Approved, Published
    content_text = Column(Text, nullable=False)
    target_audience = Column(String(255), nullable=True)
    tags = Column(JSON, default=list)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    campaign = relationship("Campaign", back_populates="content_items")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    company_size = Column(String(100), nullable=True)   # e.g., "11-50", "51-200"
    lead_source = Column(String(100), nullable=True)    # LinkedIn, Website, Referral, Event
    score = Column(Integer, default=0)                  # 0 to 100
    qualification_category = Column(String(50), default="Low Priority") # High Priority, Medium Priority, Low Priority
    business_fit_summary = Column(Text, nullable=True)
    suggested_next_action = Column(Text, nullable=True)
    score_explanation = Column(JSON, default=dict)      # Explainable breakdown
    status = Column(String(50), default="New")          # New, Contacted, In Discussion, Qualified, Disqualified
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    notes = relationship("LeadNote", back_populates="lead", cascade="all, delete-orphan")


class LeadNote(Base):
    __tablename__ = "lead_notes"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="notes")


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)       # Business Strategy, Campaign Generation, Content Creation, Lead Qualification, Weekly Growth Recommendations
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)         # e.g., "v1.0", "v2.0", "v3.0"
    system_instructions = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PromptExecution(Base):
    __tablename__ = "prompt_executions"

    id = Column(Integer, primary_key=True, index=True)
    feature_name = Column(String(100), nullable=False)
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    prompt_version = Column(String(50), nullable=False)
    system_instruction_used = Column(Text, nullable=True)
    prompt_rendered = Column(Text, nullable=False)
    user_inputs = Column(JSON, default=dict)
    model_used = Column(String(100), nullable=False)
    execution_status = Column(String(50), nullable=False) # success, fallback_demo, error
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    generated_output = Column(JSON, default=dict)
    is_example = Column(Boolean, default=False)           # Flag for documented benchmark examples vs live runs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AIActivity(Base):
    __tablename__ = "ai_activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_type = Column(String(100), nullable=False)  # strategy_generated, campaign_created, content_planned, lead_qualified
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    entity_type = Column(String(50), nullable=True)       # strategy, campaign, content, lead
    entity_id = Column(Integer, nullable=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CampaignMetric(Base):
    __tablename__ = "campaign_metrics"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    metric_date = Column(Date, nullable=False, default=datetime.date.today)
    channel = Column(String(50), nullable=False)
    impressions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    spend = Column(Float, default=0.0, nullable=False)
    revenue = Column(Float, default=0.0, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    campaign = relationship("Campaign", backref="metrics")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    role = Column(String(20), default="admin", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

