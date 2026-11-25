import datetime
import logging
from sqlalchemy.orm import Session
from app.models.models import (
    BusinessProfile, GrowthStrategy, Campaign, ContentItem,
    Lead, LeadNote, PromptTemplate, PromptExecution, AIActivity
)
from app.services.prompt_service import DEFAULT_PROMPT_TEMPLATES
from app.services.lead_scoring_service import heuristic_lead_score

logger = logging.getLogger("growthpilot.seed")

def seed_database(db: Session, force_reset: bool = False):
    """
    Initializes database with NovaTech Solutions demo dataset, prompt templates,
    benchmark prompt iterations, campaigns, content items, and scored leads.
    All data is clearly labelled with is_demo=True.
    """
    existing_profile = db.query(BusinessProfile).filter(BusinessProfile.is_demo == True).first()
    if existing_profile and not force_reset:
        logger.info("Database already seeded with demo profile. Skipping initial seeding.")
        return

    if force_reset:
        logger.info("Force resetting demo records for clean seed (preserving user-created data)...")
        # Only delete demo records so user leads, campaigns, content, and strategies are preserved
        demo_lead_ids = [l.id for l in db.query(Lead.id).filter(Lead.is_demo == True).all()]
        if demo_lead_ids:
            db.query(LeadNote).filter(LeadNote.lead_id.in_(demo_lead_ids)).delete(synchronize_session=False)
        db.query(Lead).filter(Lead.is_demo == True).delete(synchronize_session=False)
        db.query(ContentItem).filter(ContentItem.is_demo == True).delete(synchronize_session=False)
        db.query(Campaign).filter(Campaign.is_demo == True).delete(synchronize_session=False)
        db.query(GrowthStrategy).filter(GrowthStrategy.is_demo == True).delete(synchronize_session=False)
        db.query(BusinessProfile).filter(BusinessProfile.is_demo == True).delete(synchronize_session=False)
        db.query(PromptExecution).filter(PromptExecution.is_example == True).delete(synchronize_session=False)
        db.query(PromptTemplate).delete(synchronize_session=False)
        db.query(AIActivity).filter(AIActivity.is_demo == True).delete(synchronize_session=False)
        db.commit()

    # 1. Seed Business Profile (NovaTech Solutions)
    profile = BusinessProfile(
        company_name="NovaTech Solutions",
        industry="B2B Technology & AI Services",
        website="https://novatech-solutions.demo",
        description=(
            "NovaTech Solutions is an agile technology consultancy delivering custom AI development, "
            "modern web applications, data engineering pipelines, business intelligence dashboards, "
            "and workflow automation systems for high-growth tech enterprises."
        ),
        services=[
            "AI Development",
            "Web Development",
            "Data Engineering",
            "Business Intelligence",
            "Workflow Automation"
        ],
        target_audience=[
            "Small & Medium Businesses",
            "Startup Founders",
            "Business Owners",
            "Operations Managers"
        ],
        target_geography=[
            "Australia",
            "United States",
            "India"
        ],
        monthly_budget=8500.0,
        main_objective="Acquire high-value B2B enterprise clients for custom AI and automation services",
        competitors=[
            "Legacy IT Outsourcers",
            "Generic Web Agencies",
            "Off-the-shelf SaaS Wrappers"
        ],
        preferred_channels=[
            "LinkedIn B2B Outreach",
            "Technical Case Studies & SEO",
            "Google Search Ads",
            "Direct Founder Email Newsletters"
        ],
        is_demo=True
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 2. Seed Prompt Templates
    for t_data in DEFAULT_PROMPT_TEMPLATES:
        t = PromptTemplate(**t_data)
        db.add(t)
    db.commit()

    # 3. Seed Documented Benchmark Prompt Iterations (v1.0, v2.0, v3.0)
    # These show real engineering progress and prompt evolution
    benchmark_runs = [
        {
            "feature_name": "Business Strategy",
            "prompt_version": "v1.0",
            "system_instruction_used": "You are a marketing assistant.",
            "prompt_rendered": "Create a marketing strategy for a technology company: NovaTech Solutions.",
            "user_inputs": {"company_name": "NovaTech Solutions"},
            "model_used": "gemini-2.5-flash",
            "execution_status": "success",
            "latency_ms": 1120,
            "generated_output": {
                "general_notes": "Post regularly on social media, run Facebook ads, do cold outreach, and build a nice website.",
                "critique": "Lacks ICP segmentation, no concrete budget allocation, completely ignores B2B sales cycles."
            },
            "is_example": True
        },
        {
            "feature_name": "Business Strategy",
            "prompt_version": "v2.0",
            "system_instruction_used": "You are a professional B2B marketing consultant with expertise in IT services.",
            "prompt_rendered": "Create a marketing strategy for NovaTech Solutions targeting small businesses in Australia. Services: AI Development, Web Development. Include customer pain points, channels, and measurable objectives.",
            "user_inputs": {"company_name": "NovaTech Solutions", "target_geography": ["Australia"], "services": ["AI Development", "Web Development"]},
            "model_used": "gemini-2.5-flash",
            "execution_status": "success",
            "latency_ms": 1450,
            "generated_output": {
                "pain_points": ["High software costs", "Slow development"],
                "channels": ["LinkedIn", "Google Search"],
                "critique": "Improved structure and regional context, but lacks tactical 30-day sequencing, KPI targets, and JSON schema constraints."
            },
            "is_example": True
        },
        {
            "feature_name": "Business Strategy",
            "prompt_version": "v3.0",
            "system_instruction_used": "Act as a senior B2B growth strategist and tech marketing architect. Analyse the supplied company profile, target audience, services, geography, and budget. Generate a structured 30-day marketing strategy with specific ICPs, pain points, channel recommendations, campaign ideas, KPIs, and actionable priorities. Do NOT invent external market statistics or claim live web scraping. Return strictly valid JSON adhering to the specified schema.",
            "prompt_rendered": "Company Profile: NovaTech Solutions (AI Development, Web Dev, BI) targeting Founders & Ops in AU, US, IN with $8,500 budget...",
            "user_inputs": {"company_name": "NovaTech Solutions", "monthly_budget": 8500, "geographies": ["AU", "US", "IN"]},
            "model_used": "gemini-2.5-flash",
            "execution_status": "success",
            "latency_ms": 2340,
            "generated_output": {
                "status": "Production Grade",
                "summary": "Multi-tier consultative outbound and technical case-study inbound engine.",
                "icp_count": 2,
                "milestones": 4,
                "critique": "Optimal: Zero hallucination, strict schema adherence, transparent factor attribution, and production readiness."
            },
            "is_example": True
        }
    ]
    for b in benchmark_runs:
        db.add(PromptExecution(**b))
    db.commit()

    # 4. Seed Growth Strategy
    strategy = GrowthStrategy(
        business_profile_id=profile.id,
        title="NovaTech Solutions 30-Day B2B Growth & Acquisition Playbook",
        summary=(
            "An aggressive, consultative growth strategy focused on positioning NovaTech Solutions as the premier "
            "engineering and AI automation partner for mid-market SMBs and funded tech startups across Australia, "
            "the United States, and India."
        ),
        ideal_customer_profiles=[
            {
                "persona_title": "Non-Technical Founder / CEO",
                "company_profile": "Seed to Series A tech startups (10-50 employees, $1M-$5M ARR)",
                "core_need": "Rapid MVP delivery, scalable cloud architecture, and AI integration without full-time payroll bloat.",
                "buying_trigger": "Securing seed funding, product release deadlines, or losing internal engineering leads."
            },
            {
                "persona_title": "VP of Operations / Head of Product",
                "company_profile": "Mid-market service businesses ($5M-$25M ARR)",
                "core_need": "Workflow automation, business intelligence dashboards, and legacy modernization.",
                "buying_trigger": "Operational bottlenecks, high manual labor costs, or fragmented data silos."
            }
        ],
        target_market_insights=[
            "Mid-market enterprises in Australia and the US are actively allocating innovation budgets to custom AI automation rather than off-the-shelf wrappers.",
            "Decision makers prioritize demonstrable technical competence, referenceable case studies, and transparent milestones over generic agency promises.",
            "Cost-to-quality arbitrage across Australia and the US makes hybrid onshore/offshore delivery models highly attractive."
        ],
        customer_pain_points=[
            "Struggling to translate executive AI ambition into practical, production-ready business workflows.",
            "Excessive burn rate hiring scarce in-house machine learning and senior full-stack talent.",
            "Fragmented business data trapped in disconnected legacy software inhibiting real-time decision-making.",
            "Previous agency engagements resulted in brittle, unmaintainable code without proper documentation."
        ],
        unique_value_proposition=(
            "NovaTech Solutions delivers enterprise-grade AI automation and modern full-stack systems with the agility of a startup "
            "and the rigor of a tier-1 consultancy, backed by transparent sprint velocity and guaranteed IP ownership."
        ),
        marketing_objectives=[
            {"objective": "Qualified Sales Pipeline Generation", "target_metric": "20 ICP Discovery Calls completed", "timeline": "Days 1-30"},
            {"objective": "Authority Content Anchor", "target_metric": "2 High-Value Technical Case Studies published & distributed", "timeline": "Days 1-14"},
            {"objective": "Lead Capture Velocity", "target_metric": "75 Total Verified B2B Leads imported and enriched", "timeline": "Days 7-21"}
        ],
        recommended_channels=[
            {"channel": "Account-Based LinkedIn Outreach", "rationale": "Direct executive access to Founders and VPs of Ops with personalized value messaging.", "budget_allocation_pct": 40},
            {"channel": "Technical Case Study SEO & Organic", "rationale": "High-intent organic discovery of engineering solutions by searching tech leads.", "budget_allocation_pct": 25},
            {"channel": "Targeted Google Search (B2B Intent)", "rationale": "Captures high commercial intent searches for 'AI workflow automation consultancy'.", "budget_allocation_pct": 20},
            {"channel": "Niche B2B Email Newsletters & Sponsorships", "rationale": "Establishes institutional credibility among engineering leaders and tech founders.", "budget_allocation_pct": 15}
        ],
        campaign_recommendations=[
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
        suggested_kpis=[
            {"kpi_name": "Sales Qualified Opportunities (SQLs)", "target": "12 SQLs", "measurement_frequency": "Weekly"},
            {"kpi_name": "Cost Per Qualified Lead (CPQL)", "target": "< $170", "measurement_frequency": "Weekly"},
            {"kpi_name": "Discovery Call Show-Up Rate", "target": "> 85%", "measurement_frequency": "Monthly"}
        ],
        thirty_day_plan=[
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
        is_demo=True
    )
    db.add(strategy)
    db.commit()

    # 5. Seed Campaigns
    c1 = Campaign(
        name="Practical AI Audit — LinkedIn Outreach",
        product_service="Custom AI Development & Workflow Automation",
        target_audience="Startup Founders & VPs of Operations",
        objective="Generate 20 qualified discovery calls",
        channel="LinkedIn",
        tone="Professional, Direct & Value-First",
        key_selling_points="Zero fluff, 15-min architecture audit, identifying $50k+ in manual workflow waste",
        call_to_action="Book a 15-Minute Architecture Audit",
        overview="High-relevance outbound and thought-leadership campaign designed to address tech stack bloat.",
        main_message="Stop wasting 30% of engineering hours on repetitive manual workflows.",
        headlines=[
            "Cut Operational Overhead by 40% with Tailored AI Workflows",
            "Why High-Growth Startups Are Ditching Generic SaaS for Custom AI",
            "The 15-Minute Tech Stack Audit Every Tech Founder Needs"
        ],
        content_variations=[
            {
                "variant_name": "Problem-Agitate-Solve (Direct)",
                "angle": "Eliminating manual data transfer and engineering waste",
                "copy_text": "Most tech founders spend 30% of their week solving software headaches instead of growing their business.\n\nYou don't need a 10-person dev team to modernize your tech stack. You need strategic engineering.\n\nWith NovaTech Solutions, we help teams automate mission-critical workflows in days, not months.\n\n👉 Book your 15-min audit today."
            },
            {
                "variant_name": "Quantifiable Transformation",
                "angle": "Measurable bottom-line margin expansion",
                "copy_text": "What happens when your core systems move 3x faster?\n\nModern businesses don't win on effort alone — they win on leverage. Our custom AI automation provides the infrastructure high-growth companies rely on to outpace legacy competitors.\n\nReady to unlock higher margins? Let's talk."
            }
        ],
        suggested_cta="Book a 15-Minute Architecture Audit",
        recommended_audience="Tech Founders, Operations Directors, CTOs in AU, US, and India. Headcount 10-250.",
        hashtags=["#AIAutomation", "#B2BGrowth", "#TechStrategy", "#OperationsExcellence"],
        suggested_schedule=[
            {"day": "Day 1", "activity": "Publish Headline 1 + Variant A", "purpose": "Resonate with immediate operational pain"},
            {"day": "Day 3", "activity": "Publish Headline 2 + Variant B", "purpose": "Deliver quantifiable business proof"},
            {"day": "Day 5", "activity": "Direct CTA Follow-up to warm connections", "purpose": "Convert warm pipeline leads"}
        ],
        status="Active",
        is_demo=True
    )

    c2 = Campaign(
        name="De-Risking Your Software Roadmap — Google Ads",
        product_service="Full-Stack Web Development & Data Engineering",
        target_audience="CTOs & Engineering VPs",
        objective="Drive inbound consultation inquiries",
        channel="Google Ads",
        tone="Authoritative & Technical",
        key_selling_points="Senior full-stack architects, guaranteed sprint velocity, clean type-safe code",
        call_to_action="Claim Your Risk-Free Sprint Trial",
        overview="Commercial intent Google Search campaign targeting searchers seeking top-tier software delivery teams.",
        main_message="High-velocity software engineering without contractor roulette.",
        headlines=[
            "Hire Senior Full-Stack Engineers | Guaranteed Sprint Velocity",
            "Stalled Software Project? | We Take Over and Deliver on Time",
            "Custom Web & AI Development | Scalable Cloud Systems"
        ],
        content_variations=[
            {
                "variant_name": "Search Ad Copy 1",
                "angle": "Velocity and reliability focus",
                "copy_text": "Accelerate your product delivery. Senior engineering squads ready in 48 hours. Zero long-term lock-in. Full IP ownership. Consult with our tech lead today."
            },
            {
                "variant_name": "Search Ad Copy 2",
                "angle": "Rescuing troubled tech projects",
                "copy_text": "Struggling with slow agency sprints or buggy releases? NovaTech Solutions audits, stabilizes, and accelerates your codebase with proven modern stacks."
            }
        ],
        suggested_cta="Schedule Technical Consultation",
        recommended_audience="Search terms: 'hire AI developers', 'custom data engineering consultancy', 'B2B web development agency'.",
        hashtags=["#WebDevelopment", "#DataEngineering", "#CloudArchitecture"],
        suggested_schedule=[
            {"day": "Monday", "activity": "Keyword bid optimization", "purpose": "Maximize impression share on high-intent terms"},
            {"day": "Thursday", "activity": "Landing page A/B test review", "purpose": "Increase conversion rate on form submissions"}
        ],
        status="Active",
        is_demo=True
    )
    db.add(c1)
    db.add(c2)
    db.commit()

    # 6. Seed Content Calendar Items
    now = datetime.datetime.utcnow()
    content_samples = [
        {
            "title": "Why Off-The-Shelf SaaS Is Failing Mid-Market Ops Teams",
            "channel": "LinkedIn",
            "publication_date": now + datetime.timedelta(days=1, hours=9),
            "status": "Approved",
            "content_text": "Most growing companies have a software stack that looks like a patchwork quilt. Tool A doesn't talk to Tool B, and your team is copying and pasting data across 4 tabs.\n\nHere is why custom workflow automation changes the game:\n1. Zero recurring seat taxes\n2. Workflows mapped 1:1 to your real business processes\n3. Direct integration with internal proprietary data.\n\nAre you building for agility or paying for subscription bloat?",
            "target_audience": "Operations Managers & CTOs",
            "tags": ["#Operations", "#TechStrategy", "#B2B"]
        },
        {
            "title": "3 Critical Lessons from Modernizing a Legacy Workflow",
            "channel": "LinkedIn",
            "publication_date": now + datetime.timedelta(days=2, hours=10),
            "status": "Published",
            "content_text": "When we audit client systems, the biggest risk is rarely the technology itself — it's unmapped dependencies.\n\nThree rules we follow when deploying automated intelligence pipelines:\n• Never automate an unoptimized process\n• Keep a human-in-the-loop validation threshold for critical decisions\n• Measure throughput delta weekly, not quarterly.",
            "target_audience": "Heads of Engineering & Product",
            "tags": ["#WorkflowAutomation", "#Engineering"]
        },
        {
            "title": "Case Study Teardown: Cutting Pipeline Latency by 65%",
            "channel": "Blog",
            "publication_date": now + datetime.timedelta(days=4, hours=14),
            "status": "Pending Approval",
            "content_text": "Deep-dive teardown of how modern data engineering architectures eliminate batch processing delays with streaming event queues and indexed aggregations.",
            "target_audience": "Technical Founders & Architects",
            "tags": ["#DataEngineering", "#Architecture"]
        },
        {
            "title": "Weekly Tech Pulse: The State of AI in SMBs",
            "channel": "Email",
            "publication_date": now + datetime.timedelta(days=5, hours=8),
            "status": "Draft",
            "content_text": "Subject: The real cost of waiting on AI automation.\n\nHi {FirstName},\n\nOver the past 6 months, the conversation has shifted from 'What can AI do?' to 'Where is our concrete ROI?'. In this issue, we review 3 low-risk automation insertion points for 2026.",
            "target_audience": "Subscribed Founders & Decision Makers",
            "tags": ["#Newsletter", "#Leadership"]
        },
        {
            "title": "Behind the Scenes: Code Review Standards at NovaTech",
            "channel": "LinkedIn",
            "publication_date": now + datetime.timedelta(days=7, hours=11),
            "status": "Draft",
            "content_text": "Fast delivery without test coverage is just technical debt with good PR. Every production build at NovaTech undergoes strict validation, integration testing, and AI prompt evaluation scoring.",
            "target_audience": "Tech Talent & Engineering Executives",
            "tags": ["#SoftwareEngineering", "#CodeQuality"]
        }
    ]
    for c_data in content_samples:
        item = ContentItem(
            campaign_id=c1.id,
            title=c_data["title"],
            channel=c_data["channel"],
            publication_date=c_data["publication_date"],
            status=c_data["status"],
            content_text=c_data["content_text"],
            target_audience=c_data["target_audience"],
            tags=c_data["tags"],
            is_demo=True
        )
        db.add(item)
    db.commit()

    # 7. Seed Leads (18 realistic B2B tech leads from Australia, US, and India)
    demo_leads_raw = [
        {
            "name": "Sarah Jenkins",
            "company": "Aura Logistics Group",
            "email": "sarah.jenkins@auralogistics.com.au",
            "website": "https://auralogistics.com.au",
            "industry": "Logistics & Supply Chain",
            "job_title": "VP of Operations",
            "location": "Sydney, Australia",
            "company_size": "51-200",
            "lead_source": "Website Demo Request",
            "status": "In Discussion"
        },
        {
            "name": "Marcus Vance",
            "company": "Kinetix Health AI",
            "email": "m.vance@kinetixhealth.io",
            "website": "https://kinetixhealth.io",
            "industry": "Digital Health & SaaS",
            "job_title": "Chief Executive Officer & Founder",
            "location": "San Francisco, United States",
            "company_size": "11-50",
            "lead_source": "LinkedIn B2B Outreach",
            "status": "Qualified"
        },
        {
            "name": "Rohan Deshmukh",
            "company": "FinPulse Analytics",
            "email": "rohan@finpulse.in",
            "website": "https://finpulse.in",
            "industry": "Financial Technology",
            "job_title": "Chief Technology Officer",
            "location": "Bengaluru, India",
            "company_size": "51-200",
            "lead_source": "Referral",
            "status": "Qualified"
        },
        {
            "name": "Elena Rostova",
            "company": "OmniRetail Global",
            "email": "elena.r@omniretail.us",
            "website": "https://omniretail.us",
            "industry": "E-Commerce & Retail",
            "job_title": "Head of Digital Transformation",
            "location": "Austin, United States",
            "company_size": "201-500",
            "lead_source": "Google Search Ads",
            "status": "New"
        },
        {
            "name": "Liam Hemsworth",
            "company": "Apex Property Systems",
            "email": "liam@apexpropertysys.com.au",
            "website": "https://apexpropertysys.com.au",
            "industry": "PropTech / Real Estate",
            "job_title": "Managing Director",
            "location": "Melbourne, Australia",
            "company_size": "11-50",
            "lead_source": "Website Contact Form",
            "status": "In Discussion"
        },
        {
            "name": "Priya Sundaram",
            "company": "Nexus BioTech",
            "email": "priya.s@nexusbiotech.org",
            "website": "https://nexusbiotech.org",
            "industry": "Biotechnology",
            "job_title": "Director of Data Engineering",
            "location": "Hyderabad, India",
            "company_size": "51-200",
            "lead_source": "LinkedIn Organic",
            "status": "New"
        },
        {
            "name": "David Cho",
            "company": "HyperFlow Cloud",
            "email": "david.cho@hyperflow.dev",
            "website": "https://hyperflow.dev",
            "industry": "DevOps & Cloud Software",
            "job_title": "VP of Engineering",
            "location": "Seattle, United States",
            "company_size": "51-200",
            "lead_source": "Technical Case Study",
            "status": "Qualified"
        },
        {
            "name": "Chloe Martin",
            "company": "Sunstone Solar Tech",
            "email": "chloe@sunstonesolar.com.au",
            "website": "https://sunstonesolar.com.au",
            "industry": "CleanTech & Energy",
            "job_title": "Operations Lead",
            "location": "Brisbane, Australia",
            "company_size": "11-50",
            "lead_source": "Event",
            "status": "Contacted"
        },
        {
            "name": "Ananya Sharma",
            "company": "ZestIQ EdTech",
            "email": "ananya@zestiq.in",
            "website": "https://zestiq.in",
            "industry": "EdTech & Learning Platforms",
            "job_title": "Founder & CEO",
            "location": "Mumbai, India",
            "company_size": "11-50",
            "lead_source": "LinkedIn B2B Outreach",
            "status": "New"
        },
        {
            "name": "Bradley Cooper",
            "company": "Cobalt Industrial Solutions",
            "email": "bcooper@cobaltindustrial.com",
            "website": "https://cobaltindustrial.com",
            "industry": "Industrial Automation",
            "job_title": "Plant General Manager",
            "location": "Chicago, United States",
            "company_size": "500+",
            "lead_source": "Cold Outbound",
            "status": "Contacted"
        },
        {
            "name": "Jessica Taylor",
            "company": "Veritas Legal Tech",
            "email": "jtaylor@veritaslegal.com.au",
            "website": "https://veritaslegal.com.au",
            "industry": "Legal Services",
            "job_title": "Practice Operations Director",
            "location": "Sydney, Australia",
            "company_size": "11-50",
            "lead_source": "Website Demo Request",
            "status": "New"
        },
        {
            "name": "Vikram Patel",
            "company": "SwarmCore Robotics",
            "email": "vikram@swarmcore.ai",
            "website": "https://swarmcore.ai",
            "industry": "Robotics & Hardware",
            "job_title": "CTO",
            "location": "Pune, India",
            "company_size": "1-10",
            "lead_source": "Referral",
            "status": "Contacted"
        }
    ]

    for ld in demo_leads_raw:
        score_res = heuristic_lead_score(ld, profile)
        lead = Lead(
            name=ld["name"],
            company=ld["company"],
            email=ld["email"],
            website=ld["website"],
            industry=ld["industry"],
            job_title=ld["job_title"],
            location=ld["location"],
            company_size=ld["company_size"],
            lead_source=ld["lead_source"],
            score=score_res["score"],
            qualification_category=score_res["qualification_category"],
            business_fit_summary=score_res["business_fit_summary"],
            suggested_next_action=score_res["suggested_next_action"],
            score_explanation=score_res["score_explanation"],
            status=ld["status"],
            is_demo=True
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        # Add initial note
        note = LeadNote(
            lead_id=lead.id,
            note_text=f"Initial qualification scored {lead.score}/100. ICP fit: {lead.qualification_category}. Source: {lead.lead_source}."
        )
        db.add(note)

    db.commit()

    # 8. Seed AI Activities
    activities = [
        {
            "activity_type": "strategy_generated",
            "title": "Generated Growth Strategy: NovaTech Solutions 30-Day B2B Playbook",
            "description": "Formulated ICP personas, pain point mappings, and 30-day multi-channel roadmap.",
            "entity_type": "strategy",
            "entity_id": strategy.id,
            "is_demo": True
        },
        {
            "activity_type": "campaign_created",
            "title": "Created Campaign: Practical AI Audit — LinkedIn Outreach",
            "description": "Generated 3 headlines and 2 copy variants with scheduling for LinkedIn.",
            "entity_type": "campaign",
            "entity_id": c1.id,
            "is_demo": True
        },
        {
            "activity_type": "lead_qualified",
            "title": "Batch Qualified 12 Target Leads",
            "description": "Evaluated ICP fit, authority score, and geographic viability across AU, US, and India.",
            "entity_type": "lead",
            "entity_id": None,
            "is_demo": True
        },
        {
            "activity_type": "content_planned",
            "title": "Generated 7-Day Content Plan",
            "description": "Scheduled 5 high-converting posts across LinkedIn, Blog, and Email.",
            "entity_type": "content",
            "entity_id": None,
            "is_demo": True
        }
    ]
    for act in activities:
        db.add(AIActivity(**act))
    db.commit()
    logger.info("Successfully seeded database with NovaTech Solutions demo data.")
