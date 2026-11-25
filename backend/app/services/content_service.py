import datetime
import logging
from typing import Dict, Any, List, Tuple, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.models import ContentItem, BusinessProfile, AIActivity
from app.services.gemini_client import gemini_client
from app.services.prompt_service import log_prompt_execution
from app.schemas.schemas import ContentPlanAIResponse

logger = logging.getLogger("growthpilot.content")

CONTENT_SYSTEM_PROMPT = (
    "You are an expert Content Marketing Director for B2B Technology and SaaS brands. "
    "Plan actionable, channel-specific content schedules based on the company's ICP and marketing objectives. "
    "CRITICAL CONSTRAINTS: Base content drafts only on realistic industry workflows and supplied company services. "
    "Each post must have a distinct angle (educational, case study teardown, technical insight, contrarian, or conversion CTA). "
    "Never generate filler or vague placeholder advice. Return strictly valid JSON."
)

CONTENT_USER_TEMPLATE = """Business Profile:
- Company Name: {company_name}
- Services: {services}
- Target Audience: {target_audience}
- Focus Channel: {focus_channel}
- Requested Plan Duration: {days} Days
- Campaign Theme / Topic: {theme}

Generate a comprehensive {days}-day content calendar plan.
Return a single JSON object with the following structure:
{{
  "plan_overview": "Strategic summary of the content arc",
  "content_items": [
    {{
      "day_offset": 1,
      "title": "Clear headline / title for the post",
      "channel": "LinkedIn / Instagram / Blog / Email",
      "content_text": "Complete, ready-to-publish post draft including formatting and line breaks",
      "target_audience": "Specific audience persona segment",
      "tags": ["#Tag1", "#Tag2"]
    }}
  ]
}}
"""

def generate_fallback_content_plan(data: Dict[str, Any], company_name: str, services: str, days: int = 7) -> Dict[str, Any]:
    theme = data.get("theme") or "Accelerating Tech Delivery with Custom AI"

    items = [
        {
            "day_offset": 1,
            "title": "Why Off-The-Shelf SaaS Is Failing Mid-Market Ops Teams",
            "channel": "LinkedIn",
            "content_text": (
                f"Most growing companies have a software stack that looks like a patchwork quilt.\n\n"
                f"Tool A doesn't talk to Tool B, and your team is copying and pasting data across 4 tabs.\n\n"
                f"Here is why custom {services.split(',')[0]} changes the game:\n"
                f"1. Zero recurring seat taxes\n"
                f"2. Workflows mapped 1:1 to your real business processes\n"
                f"3. Direct integration with internal proprietary data\n\n"
                f"Are you building for agility or paying for subscription bloat?\n\n"
                f"#Operations #TechStrategy #B2B"
            ),
            "target_audience": "Operations Managers & CTOs",
            "tags": ["#Operations", "#TechStrategy", "#B2B"]
        },
        {
            "day_offset": 2,
            "title": "3 Critical Lessons from Modernizing a Legacy Workflow",
            "channel": "LinkedIn",
            "content_text": (
                "When we audit client systems, the biggest risk is rarely the technology itself — it's unmapped dependencies.\n\n"
                "Three rules we follow when deploying automated intelligence pipelines:\n"
                "• Never automate an unoptimized process\n"
                "• Keep a human-in-the-loop validation threshold for critical decisions\n"
                "• Measure throughput delta weekly, not quarterly\n\n"
                "What is the single biggest bottleneck in your team's workflow right now?\n\n"
                "#WorkflowAutomation #Engineering"
            ),
            "target_audience": "Heads of Engineering & Product",
            "tags": ["#WorkflowAutomation", "#Engineering"]
        },
        {
            "day_offset": 3,
            "title": "Visualizing Real-Time Business Intelligence",
            "channel": "Instagram",
            "content_text": (
                "Dashboards shouldn't just look pretty — they should make your next business decision obvious.\n\n"
                "Swipe to see how we transform raw unstructured logs into actionable executive KPI cockpits in 14 days.\n\n"
                "💡 Save this post for your next tech planning sprint.\n\n"
                "#BusinessIntelligence #DataEngineering #DevLife"
            ),
            "target_audience": "Startup Founders & Tech Leaders",
            "tags": ["#BusinessIntelligence", "#DataEngineering"]
        },
        {
            "day_offset": 4,
            "title": "Case Study Teardown: Cutting Pipeline Latency by 65%",
            "channel": "Blog",
            "content_text": (
                "Deep-dive teardown of how modern data engineering architectures eliminate batch processing delays.\n\n"
                "Key Takeaways:\n"
                "- Architecture diagrams comparing legacy ETL vs streaming pipelines\n"
                "- Database query indexing strategies that saved 14 hours/week\n"
                "- Code snippets and performance benchmarks before and after deployment\n\n"
                "Read the full engineering post on our website."
            ),
            "target_audience": "Technical Founders & Architects",
            "tags": ["#DataEngineering", "#Architecture"]
        },
        {
            "day_offset": 5,
            "title": "Weekly Tech Pulse: The State of AI in SMBs",
            "channel": "Email",
            "content_text": (
                f"Subject: The real cost of waiting on AI automation\n\n"
                f"Hi {{FirstName}},\n\n"
                f"Over the past 6 months, the conversation has shifted from 'What can AI do?' to 'Where is our concrete ROI?'.\n\n"
                f"In this issue:\n"
                f"- The top 3 low-risk, high-return automation insertion points for 2026\n"
                f"- Why small agile teams are consistently out-shipping enterprise competitors\n"
                f"- A quick checklist to audit your technical debt\n\n"
                f"Best,\n{company_name} Strategy Team"
            ),
            "target_audience": "Subscribed Founders & Decision Makers",
            "tags": ["#Newsletter", "#Leadership"]
        },
        {
            "day_offset": 6,
            "title": "Behind the Scenes: Code Review Standards at NovaTech",
            "channel": "LinkedIn",
            "content_text": (
                f"Fast delivery without test coverage is just technical debt with good PR.\n\n"
                f"Every production build at {company_name} undergoes strict validation:\n"
                f"✓ Type-safety verification\n"
                f"✓ Automated integration regressions\n"
                f"✓ AI prompt evaluation scoring\n\n"
                f"High velocity comes from engineering discipline, not shortcuts.\n\n"
                f"#SoftwareEngineering #QualityCode"
            ),
            "target_audience": "Tech Talent & Engineering Executives",
            "tags": ["#SoftwareEngineering", "#CodeQuality"]
        },
        {
            "day_offset": 7,
            "title": "Open Invitation: Free 15-Minute Architecture Review",
            "channel": "LinkedIn",
            "content_text": (
                "Planning your Q3 software roadmap or looking to integrate AI into your core platform?\n\n"
                "We are offering 5 complimentary 15-minute technical audit sessions this week for founders and ops directors.\n\n"
                "No sales pitch. Just honest architectural feedback on your current stack and automation opportunities.\n\n"
                "👉 Link in comments to reserve a slot before they are booked.\n\n"
                "#B2B #TechConsulting #StartupGrowth"
            ),
            "target_audience": "Active Prospects & Decision Makers",
            "tags": ["#B2B", "#TechConsulting", "#StartupGrowth"]
        }
    ]

    return {
        "plan_overview": f"A multi-channel 7-day content trajectory designed to establish authority, present technical proof, and drive inbound discovery calls around {theme}.",
        "content_items": items[:days]
    }

async def generate_content_plan(
    db: Session,
    plan_data: Dict[str, Any],
    profile: Optional[BusinessProfile] = None,
    force_demo_mode: bool = False
) -> Tuple[List[ContentItem], Dict[str, Any]]:
    company_name = profile.company_name if profile else "NovaTech Solutions"
    services = ", ".join(profile.services) if profile and profile.services else "AI Development, Web Dev, Data Engineering"
    target_audience = ", ".join(profile.target_audience) if profile and profile.target_audience else "Startup Founders, Operations Managers"

    days = plan_data.get("days", 7)
    focus_channel = plan_data.get("focus_channel", "All Channels")
    theme = plan_data.get("theme", "Accelerating Business Growth with Custom AI & Automation")

    prompt = CONTENT_USER_TEMPLATE.format(
        company_name=company_name,
        services=services,
        target_audience=target_audience,
        focus_channel=focus_channel,
        days=days,
        theme=theme
    )

    # State 1: Demo Simulation Mode
    if force_demo_mode or not gemini_client.is_configured():
        logger.info("Executing Content Plan Generation in Demo Simulation Mode.")
        parsed_json = generate_fallback_content_plan(plan_data, company_name, services, days=days)
        latency = 320
        status = "fallback_demo"
        is_demo_output = True
        source_label = "Demo Simulation"

        log_prompt_execution(
            db=db,
            feature_name="Content Creation",
            prompt_version="v3.0",
            system_instruction=CONTENT_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs=plan_data,
            model_used="demo-simulation-engine",
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json,
            error_message=None
        )

    # State 2 & 3: Live Gemini AI
    else:
        logger.info("Calling Google Gemini API for live content plan generation...")
        parsed_json, latency, status, error_msg = await gemini_client.generate_structured_json(
            prompt=prompt,
            system_instruction=CONTENT_SYSTEM_PROMPT,
            temperature=0.4,
            response_schema=ContentPlanAIResponse
        )

        log_prompt_execution(
            db=db,
            feature_name="Content Creation",
            prompt_version="v3.0",
            system_instruction=CONTENT_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs=plan_data,
            model_used=gemini_client.model_name,
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json if status == "success" else {},
            error_message=error_msg
        )

        if status != "success" or not parsed_json or "content_items" not in parsed_json:
            logger.error(f"Live Gemini API content planning failed: {error_msg}")
            raise HTTPException(
                status_code=502,
                detail={
                    "error": error_msg or "Gemini API returned an incomplete content plan response.",
                    "offer_demo_mode": True,
                    "message": f"Gemini AI content planning failed: {error_msg or 'Incomplete schema'}. You can retry or switch to Demo Mode."
                }
            )

        is_demo_output = False
        source_label = "Gemini AI"

    now = datetime.datetime.utcnow()
    created_items = []
    raw_items = parsed_json.get("content_items", [])

    for idx, item in enumerate(raw_items):
        offset = item.get("day_offset", idx + 1)
        pub_date = now + datetime.timedelta(days=offset)
        pub_date = pub_date.replace(hour=9 + (idx % 8), minute=0, second=0, microsecond=0)

        c_item = ContentItem(
            campaign_id=plan_data.get("campaign_id"),
            title=item.get("title", f"Day {offset} Content Post"),
            channel=item.get("channel", "LinkedIn"),
            publication_date=pub_date,
            status="Draft",
            content_text=item.get("content_text", ""),
            target_audience=item.get("target_audience", target_audience),
            tags=item.get("tags", []),
            is_demo=is_demo_output
        )
        db.add(c_item)
        created_items.append(c_item)

    db.commit()
    for item in created_items:
        db.refresh(item)

    activity = AIActivity(
        activity_type="content_planned",
        title=f"Generated {len(created_items)}-Day Content Calendar [{source_label}]",
        description=f"Planned {len(created_items)} scheduled content items across multiple channels for {company_name} ({source_label}).",
        entity_type="content",
        entity_id=created_items[0].id if created_items else None,
        is_demo=is_demo_output
    )
    db.add(activity)
    db.commit()

    meta = {
        "status": status,
        "source": source_label,
        "is_demo": is_demo_output,
        "latency_ms": latency,
        "count": len(created_items),
        "model": gemini_client.model_name if not is_demo_output else "demo-simulation-engine"
    }
    return created_items, meta
