import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import PromptExecution

logger = logging.getLogger("growthpilot.prompts")

DEFAULT_PROMPT_TEMPLATES = [
    {
        "category": "Business Strategy",
        "name": "B2B Growth Strategy Generator",
        "version": "v1.0",
        "system_instructions": "You are a marketing assistant.",
        "user_prompt_template": "Create a marketing strategy for a technology company: {company_name}.",
        "notes": "Version 1.0 baseline: Overly vague, lacks industry context, output format is unstructured.",
        "is_active": False
    },
    {
        "category": "Business Strategy",
        "name": "B2B Growth Strategy Generator",
        "version": "v2.0",
        "system_instructions": "You are a professional B2B marketing consultant with expertise in IT services.",
        "user_prompt_template": "Create a marketing strategy for {company_name} targeting small businesses in {target_geography}. Services: {services}. Include customer pain points, channels, and measurable objectives.",
        "notes": "Version 2.0 revision: Added industry context, geography, and basic structure, but lacks action plans, KPIs, and strict anti-hallucination constraints.",
        "is_active": False
    },
    {
        "category": "Business Strategy",
        "name": "B2B Growth Strategy Generator",
        "version": "v3.0",
        "system_instructions": "Act as a senior B2B growth strategist and tech marketing architect. Analyse the supplied company profile, target audience, services, geography, and budget. Generate a structured 30-day marketing strategy with specific ICPs, pain points, channel recommendations, campaign ideas, KPIs, and actionable priorities. Do NOT invent external market statistics or claim live web scraping. Return strictly valid JSON adhering to the specified schema.",
        "user_prompt_template": """Company Profile:
- Company Name: {company_name}
- Industry: {industry}
- Description: {description}
- Core Services: {services}
- Target Audience: {target_audience}
- Target Geographies: {target_geography}
- Monthly Budget: ${monthly_budget}
- Primary Objective: {main_objective}
- Known Competitors: {competitors}
- Preferred Channels: {preferred_channels}

Develop an actionable, high-ROI B2B growth strategy tailored specifically to these inputs.
Return JSON with keys:
- summary: String
- ideal_customer_profiles: Array of objects (persona_title, company_profile, core_need, buying_trigger)
- target_market_insights: Array of strings
- customer_pain_points: Array of strings
- unique_value_proposition: String
- marketing_objectives: Array of objects (objective, target_metric, timeline)
- recommended_channels: Array of objects (channel, rationale, budget_allocation_pct)
- campaign_recommendations: Array of objects (campaign_name, channel, goal, tactical_description)
- suggested_kpis: Array of objects (kpi_name, target, measurement_frequency)
- thirty_day_plan: Array of objects (day_range, focus_area, actionable_tasks)""",
        "notes": "Version 3.0 (Production): Enforces structured JSON schema, strict anti-hallucination boundaries, concrete budget allocation, persona triggers, and a phased 30-day roadmap.",
        "is_active": True
    },
    {
        "category": "Campaign Generation",
        "name": "Multi-Channel Campaign Generator",
        "version": "v1.0",
        "system_instructions": "You are a copywriter.",
        "user_prompt_template": "Write an ad for {product_service} on {channel}.",
        "notes": "Version 1.0 baseline: Produces generic, single-variation copy with no audience segmentation.",
        "is_active": False
    },
    {
        "category": "Campaign Generation",
        "name": "Multi-Channel Campaign Generator",
        "version": "v2.0",
        "system_instructions": "You are an experienced direct response copywriter for B2B tech companies.",
        "user_prompt_template": "Create a {channel} campaign for {product_service} targeting {target_audience}. Tone: {tone}. Objective: {objective}. Include 3 headlines and 2 copy variants.",
        "notes": "Version 2.0 revision: Added channel tone and multiple headline variants.",
        "is_active": False
    },
    {
        "category": "Campaign Generation",
        "name": "Multi-Channel Campaign Generator",
        "version": "v3.0",
        "system_instructions": "You are an elite B2B Growth Copywriter and Campaign Strategist. Create high-converting, channel-native campaign copy adhering to platform best practices. Never invent false claims, awards, or fake testimonials. Return strictly valid JSON adhering to the specified schema.",
        "user_prompt_template": """Campaign Brief:
- Campaign Name: {name}
- Product/Service: {product_service}
- Target Audience: {target_audience}
- Campaign Objective: {objective}
- Marketing Channel: {channel}
- Tone of Voice: {tone}
- Key Value Propositions: {key_selling_points}
- Primary CTA: {call_to_action}
- Special Instructions: {additional_instructions}

Return JSON with keys:
- overview: Strategic rationale for this campaign
- main_message: Core narrative anchor
- headlines: Array of 3 distinct high-impact headlines
- content_variations: Array of 3 complete copy variations with fields (variant_name, angle, copy_text)
- suggested_cta: Primary recommended call to action
- recommended_audience: Precise audience targeting parameters
- hashtags: Array of 4-6 relevant hashtags (if channel is social)
- suggested_schedule: Array of schedule items (day, activity, purpose)""",
        "notes": "Version 3.0 (Production): Multi-angle copy variations, platform-native formatting, explicit hook angles, and schedule mapping.",
        "is_active": True
    },
    {
        "category": "Lead Qualification",
        "name": "Explainable B2B Lead Scorer",
        "version": "v1.0",
        "system_instructions": "You are a sales assistant.",
        "user_prompt_template": "Is {name} at {company} a good lead for our company?",
        "notes": "Version 1.0 baseline: Subjective, arbitrary yes/no answers without structured evaluation criteria.",
        "is_active": False
    },
    {
        "category": "Lead Qualification",
        "name": "Explainable B2B Lead Scorer",
        "version": "v2.0",
        "system_instructions": "Score leads from 0 to 100 based on fit.",
        "user_prompt_template": "Score this lead: Name: {name}, Company: {company}, Industry: {industry}, Title: {job_title}, Location: {location}. Explain why.",
        "notes": "Version 2.0 revision: Introduced numerical score, but scoring rubric is opaque and unstandardized.",
        "is_active": False
    },
    {
        "category": "Lead Qualification",
        "name": "Explainable B2B Lead Scorer",
        "version": "v3.0",
        "system_instructions": "You are an analytical B2B Lead Qualification Specialist. Evaluate leads against the business's ICP using objective criteria: Industry Alignment (30%), Decision Maker Authority (25%), Geographic Match (20%), Company Size Viability (15%), and Source Intent (10%). Never invent facts about the lead or company. Base evaluations exclusively on the provided data fields. Return strictly valid JSON.",
        "user_prompt_template": """Seller Profile:
- Industry: {seller_industry}
- Services Offered: {seller_services}
- Target Audience: {seller_audience}
- Target Geographies: {seller_geography}

Lead Profile to Evaluate:
- Contact: {name}
- Title: {job_title}
- Company: {company}
- Industry: {industry}
- Company Size: {company_size}
- Location: {location}
- Source: {lead_source}
- Website: {website}

Calculate an objective lead score (0-100), assign priority category (High Priority: 75-100, Medium Priority: 50-74, Low Priority: 0-49), provide business fit summary, suggested next action, and transparent factor breakdown.
Return JSON with keys:
- score: Integer (0-100)
- qualification_category: "High Priority" | "Medium Priority" | "Low Priority"
- business_fit_summary: String
- suggested_next_action: String
- score_explanation: Object with breakdown (industry_fit_score, authority_score, geography_score, size_score, rationale)""",
        "notes": "Version 3.0 (Production): Weighted multi-attribute scoring model, rigorous factor attribution, and concrete prescriptive next actions.",
        "is_active": True
    }
]

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'(?<![A-Za-z0-9])(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![A-Za-z0-9])')

def redact_sensitive_text(text: str) -> str:
    """Redacts API keys, emails, and phone numbers from text logs."""
    if not text:
        return text
    # 1. API Keys / Secrets first (matches Google AI keys: AIzaSy followed by 16+ chars)
    text = re.sub(r'AIzaSy[A-Za-z0-9_-]{16,}', '[REDACTED_SECRET]', text)
    # 2. Email addresses
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    # 3. Phone numbers (with strict boundary lookarounds so internal digits aren't mangled)
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    return text

def redact_structure(data: Any) -> Any:
    """Recursively redacts sensitive patterns in nested dicts/lists."""
    if isinstance(data, dict):
        return {k: redact_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_structure(item) for item in data]
    elif isinstance(data, str):
        return redact_sensitive_text(data)
    return data

def log_prompt_execution(
    db: Session,
    feature_name: str,
    prompt_version: str,
    system_instruction: str,
    prompt_rendered: str,
    user_inputs: Dict[str, Any],
    model_used: str,
    execution_status: str,
    latency_ms: int,
    generated_output: Dict[str, Any],
    error_message: Optional[str] = None,
    prompt_template_id: Optional[int] = None,
    is_example: bool = False
) -> PromptExecution:
    sanitized_prompt = redact_sensitive_text(prompt_rendered)
    sanitized_system = redact_sensitive_text(system_instruction) if system_instruction else ""
    sanitized_inputs = redact_structure(user_inputs)
    sanitized_output = redact_structure(generated_output)
    sanitized_error = redact_sensitive_text(error_message) if error_message else None

    execution = PromptExecution(
        feature_name=feature_name,
        prompt_template_id=prompt_template_id,
        prompt_version=prompt_version,
        system_instruction_used=sanitized_system,
        prompt_rendered=sanitized_prompt,
        user_inputs=sanitized_inputs,
        model_used=model_used,
        execution_status=execution_status,
        error_message=sanitized_error,
        latency_ms=latency_ms,
        generated_output=sanitized_output,
        is_example=is_example
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution

def clean_old_prompt_executions(db: Session, days: int = 30) -> int:
    """
    Data retention policy: Deletes prompt executions older than the specified days.
    Returns the count of deleted records.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(PromptExecution).filter(PromptExecution.created_at < cutoff).delete()
    db.commit()
    return deleted
