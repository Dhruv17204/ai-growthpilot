import logging
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.models import GrowthStrategy, AIActivity
from app.services.gemini_client import gemini_client
from app.services.prompt_service import log_prompt_execution
from app.schemas.schemas import StrategyAIResponse

logger = logging.getLogger("growthpilot.strategy")

STRATEGY_SYSTEM_PROMPT = (
    "Act as a senior B2B growth strategist and tech marketing architect. "
    "Analyse the supplied company profile, target audience, services, geography, and budget. "
    "Develop a structured, actionable 30-day marketing strategy with specific ICPs, pain points, "
    "channel recommendations, campaign ideas, KPIs, and actionable priorities. "
    "CRITICAL CONSTRAINTS: Use only supplied business information and explicitly stated reasonable assumptions. "
    "Never invent unverified market statistics, client awards, or claim live web scraping. "
    "If any input field is missing or ambiguous, document it under 'assumptions_and_uncertainties'. "
    "Return strictly valid JSON matching the requested schema."
)

STRATEGY_USER_TEMPLATE = """Company Profile:
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
Return a single JSON object with the following structure:
{{
  "title": "{company_name} 30-Day Growth & Acquisition Strategy",
  "summary": "Concise executive overview of the growth strategy",
  "ideal_customer_profiles": [
    {{
      "persona_title": "Title of persona (e.g. Head of Engineering / Founder)",
      "company_profile": "Target company size, type, revenue stage",
      "core_need": "Key business problem they need solved",
      "buying_trigger": "Events that prompt them to seek external help"
    }}
  ],
  "target_market_insights": ["Insight 1", "Insight 2", "Insight 3"],
  "customer_pain_points": ["Pain point 1", "Pain point 2", "Pain point 3", "Pain point 4"],
  "unique_value_proposition": "Clear, compelling UVP statement distinguishing from competitors",
  "marketing_objectives": [
    {{
      "objective": "Specific strategic goal",
      "target_metric": "Measurable KPI target (e.g. 15 qualified discovery calls)",
      "timeline": "e.g. Days 1-30"
    }}
  ],
  "recommended_channels": [
    {{
      "channel": "Channel name (e.g. LinkedIn B2B Outreach, Technical SEO)",
      "rationale": "Why this channel is optimal for this profile",
      "budget_allocation_pct": 40
    }}
  ],
  "campaign_recommendations": [
    {{
      "campaign_name": "Campaign title",
      "channel": "Channel",
      "goal": "Core outcome",
      "tactical_description": "Specific execution tactical steps"
    }}
  ],
  "suggested_kpis": [
    {{
      "kpi_name": "KPI Name",
      "target": "Target threshold",
      "measurement_frequency": "Weekly / Monthly"
    }}
  ],
  "thirty_day_plan": [
    {{
      "day_range": "Days 1-7",
      "focus_area": "Foundation & Asset Audit",
      "actionable_tasks": ["Task 1", "Task 2", "Task 3"]
    }},
    {{
      "day_range": "Days 8-14",
      "focus_area": "Outbound Engine & Lead List Activation",
      "actionable_tasks": ["Task 1", "Task 2"]
    }},
    {{
      "day_range": "Days 15-21",
      "focus_area": "Multi-Channel Distribution & Retargeting",
      "actionable_tasks": ["Task 1", "Task 2"]
    }},
    {{
      "day_range": "Days 22-30",
      "focus_area": "Pipeline Review & Optimization Loop",
      "actionable_tasks": ["Task 1", "Task 2"]
    }}
  ],
  "assumptions_and_uncertainties": [
    "Assumption regarding average contract values based on B2B tech benchmarks",
    "Assumed sales cycle duration of 30-60 days for mid-market software projects"
  ]
}}
"""

def generate_fallback_strategy(profile: Dict[str, Any]) -> Dict[str, Any]:
    company = profile.get("company_name", "Tech Company")
    services = ", ".join(profile.get("services", ["AI Development", "Software Engineering"]))
    geos = ", ".join(profile.get("target_geography", ["Australia", "United States", "India"]))
    budget = profile.get("monthly_budget", 5000)

    return {
        "title": f"{company} 30-Day B2B Growth & Acquisition Playbook (Simulation)",
        "summary": (
            f"A targeted growth strategy for {company} focused on high-intent customer acquisition across "
            f"{geos}. Prioritizes consultative outbound and thought-leadership inbound positioning for {services}."
        ),
        "ideal_customer_profiles": [
            {
                "persona_title": "Non-Technical Founder / CEO",
                "company_profile": "Seed to Series A tech startups (10-50 employees)",
                "core_need": "Rapid MVP delivery, scalable architecture, and AI integration without full-time payroll bloat.",
                "buying_trigger": "Securing seed funding, product release deadlines, or losing internal engineering leads."
            },
            {
                "persona_title": "VP of Operations / Head of Product",
                "company_profile": "Mid-market service businesses ($5M-$25M ARR)",
                "core_need": "Workflow automation, business intelligence dashboards, and legacy modernization.",
                "buying_trigger": "Operational bottlenecks, high manual labor costs, or fragmented data silos."
            }
        ],
        "target_market_insights": [
            f"Mid-market enterprises in {geos} are actively allocating innovation budgets to custom AI automation rather than off-the-shelf wrappers.",
            "Decision makers prioritize demonstrable technical competence, referenceable case studies, and transparent milestones over generic agency promises.",
            "Cost-to-quality arbitrage across Australia and the US makes hybrid onshore/offshore delivery models highly attractive."
        ],
        "customer_pain_points": [
            "Struggling to translate executive AI ambition into practical, production-ready business workflows.",
            "Excessive burn rate hiring scarce in-house machine learning and senior full-stack talent.",
            "Fragmented business data trapped in disconnected legacy software inhibiting real-time decision-making.",
            "Previous agency engagements resulted in brittle, unmaintainable code without proper documentation."
        ],
        "unique_value_proposition": (
            f"{company} delivers enterprise-grade AI automation and modern full-stack systems with the agility of a startup "
            "and the rigor of a tier-1 consultancy, backed by transparent sprint velocity and guaranteed IP ownership."
        ),
        "marketing_objectives": [
            {
                "objective": "Qualified Sales Pipeline Generation",
                "target_metric": "20 ICP Discovery Calls completed in 30 days",
                "timeline": "Days 1-30"
            },
            {
                "objective": "Authority Content Anchor",
                "target_metric": "2 High-Value Technical Case Studies published & distributed",
                "timeline": "Days 1-14"
            },
            {
                "objective": "Lead Capture Velocity",
                "target_metric": "75 Total Verified B2B Leads imported and enriched",
                "timeline": "Days 7-21"
            }
        ],
        "recommended_channels": [
            {
                "channel": "Account-Based LinkedIn Outreach",
                "rationale": "Direct executive access to Founders and VPs of Ops with personalized value messaging.",
                "budget_allocation_pct": 40
            },
            {
                "channel": "Technical Case Study SEO & Organic",
                "rationale": "High-intent organic discovery of engineering solutions by searching tech leads.",
                "budget_allocation_pct": 25
            },
            {
                "channel": "Targeted Google Search (B2B Intent)",
                "rationale": "Captures high commercial intent searches for 'AI workflow automation consultancy'.",
                "budget_allocation_pct": 20
            },
            {
                "channel": "Niche B2B Email Newsletters & Sponsorships",
                "rationale": "Establishes institutional credibility among engineering leaders and tech founders.",
                "budget_allocation_pct": 15
            }
        ],
        "campaign_recommendations": [
            {
                "campaign_name": "The Practical AI Audit Campaign",
                "channel": "LinkedIn & Cold Email",
                "goal": "Generate qualified discovery calls through a low-friction 15-minute architecture review.",
                "tactical_description": "Offer founders a free blueprint identifying 3 immediate AI automation bottlenecks in their tech stack."
            },
            {
                "campaign_name": "De-Risking Your Software Roadmap",
                "channel": "Google Search Ads & Retargeting",
                "goal": "Capture companies with stalled projects or unvetted development teams.",
                "tactical_description": "Target high-intent keywords like 'hire AI engineering agency' with guaranteed sprint trial landing pages."
            }
        ],
        "suggested_kpis": [
            {
                "kpi_name": "Sales Qualified Opportunities (SQLs)",
                "target": "12 SQLs",
                "measurement_frequency": "Weekly"
            },
            {
                "kpi_name": "Cost Per Qualified Lead (CPQL)",
                "target": f"< ${max(50, int(budget / 50))}",
                "measurement_frequency": "Weekly"
            },
            {
                "kpi_name": "Discovery Call Show-Up Rate",
                "target": "> 85%",
                "measurement_frequency": "Monthly"
            }
        ],
        "thirty_day_plan": [
            {
                "day_range": "Days 1-7",
                "focus_area": "Foundation & Messaging Alignment",
                "actionable_tasks": [
                    "Audit website UVP and publish 1 anchor case study showcasing AI workflow automation ROI.",
                    "Set up lead tracking pixel, form conversions, and CRM pipeline stages.",
                    "Build initial list of 150 target accounts matching ICP in AU, US, and India."
                ]
            },
            {
                "day_range": "Days 8-14",
                "focus_area": "Outbound Engine Activation",
                "actionable_tasks": [
                    "Launch 3-touch hyper-personalized LinkedIn outreach sequence to 75 Operations Directors.",
                    "Deploy Google Search campaign targeting commercial intent automation keywords.",
                    "Initiate bi-weekly technical thought leadership publication on LinkedIn."
                ]
            },
            {
                "day_range": "Days 15-21",
                "focus_area": "Mid-Funnel Nurturing & Retargeting",
                "actionable_tasks": [
                    "Activate retargeting campaigns for visitors of service and case study pages.",
                    "Conduct discovery calls with inbound leads using the structured qualification scorecard.",
                    "Refine messaging angles based on real objection data collected during early calls."
                ]
            },
            {
                "day_range": "Days 22-30",
                "focus_area": "Pipeline Acceleration & Scaling",
                "actionable_tasks": [
                    "Review channel performance metrics and reallocate ad budget to the highest converting source.",
                    "Deliver tailored project proposals to qualified prospects from Days 8-21.",
                    "Finalize month-2 scale plan based on CAC and deal velocity."
                ]
            }
        ],
        "assumptions_and_uncertainties": [
            "Assumed average deal size between $15,000 and $40,000 for bespoke B2B automation engagements.",
            "Assumed 3-touch outreach sequence with minimum 12% reply rate based on calibrated historical benchmarks."
        ]
    }

async def generate_growth_strategy(
    db: Session,
    profile_data: Dict[str, Any],
    profile_id: Optional[int] = None,
    force_demo_mode: bool = False
) -> Tuple[GrowthStrategy, Dict[str, Any]]:
    """
    Synthesizes a 30-day growth strategy.
    Decouples 3 distinct operational states:
      1. LIVE AI: Genuine successful Gemini API response (is_demo=False).
      2. DEMO MODE: Explicit deterministic simulation (is_demo=True).
      3. AI ERROR: Genuine Gemini request failed -> raises HTTPException (never silently fakes success).
    """
    prompt = STRATEGY_USER_TEMPLATE.format(
        company_name=profile_data.get("company_name", "Tech Startup"),
        industry=profile_data.get("industry", "Technology"),
        description=profile_data.get("description", "Software & AI Solutions"),
        services=", ".join(profile_data.get("services", [])) or "Custom AI & Web Development",
        target_audience=", ".join(profile_data.get("target_audience", [])) or "Small & Medium Businesses",
        target_geography=", ".join(profile_data.get("target_geography", [])) or "Global",
        monthly_budget=profile_data.get("monthly_budget", 5000),
        main_objective=profile_data.get("main_objective", "Acquire high-value B2B enterprise clients"),
        competitors=", ".join(profile_data.get("competitors", [])) or "Generalist IT agencies",
        preferred_channels=", ".join(profile_data.get("preferred_channels", [])) or "LinkedIn, Content, SEO"
    )

    # State 1: Explicit Demo Mode Requested or API Unconfigured
    if force_demo_mode or not gemini_client.is_configured():
        logger.info("Executing Strategy Generation in Demo Simulation Mode.")
        parsed_json = generate_fallback_strategy(profile_data)
        latency = 450
        status = "fallback_demo"
        is_demo_output = True
        source_label = "Demo Simulation"
        error_msg = None

        log_prompt_execution(
            db=db,
            feature_name="Business Strategy",
            prompt_version="v3.0",
            system_instruction=STRATEGY_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs=profile_data,
            model_used="demo-simulation-engine",
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json,
            error_message=None
        )

    # State 2 & 3: Live Gemini AI Requested
    else:
        logger.info("Calling Google Gemini API for live strategy synthesis...")
        parsed_json, latency, status, error_msg = await gemini_client.generate_structured_json(
            prompt=prompt,
            system_instruction=STRATEGY_SYSTEM_PROMPT,
            temperature=0.3,
            response_schema=StrategyAIResponse
        )

        # Log execution attempt in audit history
        log_prompt_execution(
            db=db,
            feature_name="Business Strategy",
            prompt_version="v3.0",
            system_instruction=STRATEGY_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs=profile_data,
            model_used=gemini_client.model_name,
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json if status == "success" else {},
            error_message=error_msg
        )

        # If live AI call failed, DO NOT silently convert into a successful fake output
        if status != "success" or not parsed_json or "summary" not in parsed_json:
            logger.error(f"Live Gemini API strategy generation failed: {error_msg}")
            raise HTTPException(
                status_code=502,
                detail={
                    "error": error_msg or "Gemini API returned an incomplete response.",
                    "offer_demo_mode": True,
                    "message": f"Gemini AI generation failed: {error_msg or 'Incomplete JSON schema'}. You can retry or switch to Demo Mode."
                }
            )

        is_demo_output = False
        source_label = "Gemini AI"

    # Save verified strategy to database
    strategy = GrowthStrategy(
        business_profile_id=profile_id,
        title=parsed_json.get("title", f"{profile_data.get('company_name')} Growth Strategy"),
        summary=parsed_json.get("summary", ""),
        ideal_customer_profiles=parsed_json.get("ideal_customer_profiles", []),
        target_market_insights=parsed_json.get("target_market_insights", []),
        customer_pain_points=parsed_json.get("customer_pain_points", []),
        unique_value_proposition=parsed_json.get("unique_value_proposition", ""),
        marketing_objectives=parsed_json.get("marketing_objectives", []),
        recommended_channels=parsed_json.get("recommended_channels", []),
        campaign_recommendations=parsed_json.get("campaign_recommendations", []),
        suggested_kpis=parsed_json.get("suggested_kpis", []),
        thirty_day_plan=parsed_json.get("thirty_day_plan", []),
        assumptions_and_uncertainties=parsed_json.get("assumptions_and_uncertainties", []),
        is_demo=is_demo_output
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)

    # Record activity
    activity = AIActivity(
        activity_type="strategy_generated",
        title=f"Generated Growth Strategy [{source_label}]: {strategy.title}",
        description=f"Developed 30-day multi-channel growth plan for {profile_data.get('company_name')} ({source_label}).",
        entity_type="strategy",
        entity_id=strategy.id,
        is_demo=is_demo_output
    )
    db.add(activity)
    db.commit()

    meta = {
        "status": status,
        "source": source_label,
        "is_demo": is_demo_output,
        "latency_ms": latency,
        "model": gemini_client.model_name if not is_demo_output else "demo-simulation-engine"
    }
    return strategy, meta
