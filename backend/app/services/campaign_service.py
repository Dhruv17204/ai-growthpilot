import json
import logging
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.models import Campaign, AIActivity
from app.services.gemini_client import gemini_client
from app.services.prompt_service import log_prompt_execution
from app.schemas.schemas import CampaignAIResponse

logger = logging.getLogger("growthpilot.campaigns")

CAMPAIGN_SYSTEM_PROMPT = (
    "You are an elite B2B Growth Copywriter and Campaign Strategist. "
    "Create high-converting, channel-native marketing campaigns adhering strictly to platform best practices. "
    "CRITICAL CONSTRAINTS: Use only the supplied product/service information and explicitly stated selling points. "
    "Never invent unverified client awards, fake testimonials, fabricated customer metrics, or pricing guarantees. "
    "Ensure each of the 3 headline variations and 3 content variations adopts a distinctly different strategic angle. "
    "Return strictly valid JSON matching the requested schema."
)

CAMPAIGN_USER_TEMPLATE = """Campaign Brief:
- Campaign Name: {name}
- Product/Service: {product_service}
- Target Audience: {target_audience}
- Campaign Objective: {objective}
- Marketing Channel: {channel}
- Tone of Voice: {tone}
- Key Value Propositions: {key_selling_points}
- Primary CTA: {call_to_action}
- Special Instructions: {additional_instructions}

Generate a comprehensive, ready-to-deploy campaign package tailored to {channel}.
Return a single JSON object with the following structure:
{{
  "overview": "Strategic campaign thesis explaining why this approach matches the audience and channel",
  "main_message": "Core narrative anchor statement",
  "headlines": [
    "Headline 1 (Benefit-driven)",
    "Headline 2 (Curiosity/Pain-point)",
    "Headline 3 (Direct commercial)"
  ],
  "content_variations": [
    {{
      "variant_name": "Variation A — Problem-Agitate-Solve",
      "angle": "Direct pain point resonance",
      "copy_text": "Complete, formatted copy ready to paste"
    }},
    {{
      "variant_name": "Variation B — Value & Transformation",
      "angle": "Business outcome focus",
      "copy_text": "Complete, formatted copy ready to paste"
    }},
    {{
      "variant_name": "Variation C — Contrarian / Authority Insight",
      "angle": "Thought-leadership perspective",
      "copy_text": "Complete, formatted copy ready to paste"
    }}
  ],
  "suggested_cta": "Primary recommended call to action text",
  "recommended_audience": "Specific audience segmentation advice and targeting parameters",
  "hashtags": ["#Tag1", "#Tag2", "#Tag3", "#Tag4"],
  "suggested_schedule": [
    {{"day": "Day 1", "activity": "Initial Launch & Baseline Post", "purpose": "Establish core proposition"}},
    {{"day": "Day 3", "activity": "Follow-up Engagement / Variant B", "purpose": "Re-engage non-responders"}},
    {{"day": "Day 5", "activity": "Proof Point & Case Study Angle", "purpose": "Overcome skepticism"}},
    {{"day": "Day 7", "activity": "Direct CTA Push", "purpose": "Drive conversion before cycle closes"}}
  ]
}}
"""

def generate_fallback_campaign(data: Dict[str, Any]) -> Dict[str, Any]:
    name = data.get("name", "B2B Tech Launch")
    product = data.get("product_service", "AI Development & Automation")
    audience = data.get("target_audience", "Startup Founders & Operations Directors")
    channel = data.get("channel", "LinkedIn")
    tone = data.get("tone", "Professional & Authoritative")
    usp = data.get("key_selling_points", "Enterprise-grade AI, fast delivery, dedicated engineers")
    cta = data.get("call_to_action", "Book a Free 15-Min Discovery Session")

    return {
        "overview": (
            f"A multi-angle {channel} campaign structured for {audience}. "
            f"Positions {product} as an essential growth catalyst with an emphasis on {tone.lower()} execution."
        ),
        "main_message": f"Stop letting operational bottlenecks throttle your growth. Deploy custom {product} that scales with your ambition.",
        "headlines": [
            f"Cut Operational Overhead by 40% with Tailored {product}",
            f"Why High-Growth Startups Are Ditching Generic Software for Custom AI",
            f"The Smart Founder's Shortcut to Enterprise-Grade {product}"
        ],
        "content_variations": [
            {
                "variant_name": "Variation A — Problem-Agitate-Solve (Direct)",
                "angle": "Immediate bottleneck relief",
                "copy_text": (
                    f"Most founders spend 30% of their week solving software headaches instead of growing their business.\n\n"
                    f"You don't need a 10-person dev team to modernize your tech stack. You need strategic engineering.\n\n"
                    f"With our {product}, we help teams:\n"
                    f"• Automate mission-critical workflows in days, not months\n"
                    f"• Build scalable architectures built for enterprise security\n"
                    f"• Accelerate feature delivery without ballooning headcount\n\n"
                    f"👉 {cta}"
                )
            },
            {
                "variant_name": "Variation B — Transformation & ROI",
                "angle": "Quantifiable commercial advantage",
                "copy_text": (
                    f"What would happen to your bottom line if your core systems moved 3x faster?\n\n"
                    f"Modern businesses don't win on effort alone — they win on leverage. Our {product} provides the exact infrastructure high-growth companies rely on to outpace legacy competitors.\n\n"
                    f"Key differentiators:\n"
                    f"✓ {usp}\n"
                    f"✓ Transparent sprint velocity\n"
                    f"✓ Complete code and IP ownership from day one\n\n"
                    f"Ready to unlock higher margins? Let's talk.\n\n"
                    f"🔗 {cta}"
                )
            },
            {
                "variant_name": "Variation C — Contrarian Thought Leadership",
                "angle": "Challenging conventional industry myths",
                "copy_text": (
                    f"Unpopular opinion: Buying another SaaS subscription won't fix your operational bottlenecks.\n\n"
                    f"Off-the-shelf tools force your business to fit someone else's workflow. Custom {product} conforms to how your highest-performing team members actually operate.\n\n"
                    f"Before you commit to another 12-month software contract, see what a dedicated solution looks like.\n\n"
                    f"💬 Drop a comment below or {cta.lower()}."
                )
            }
        ],
        "suggested_cta": cta,
        "recommended_audience": f"Target: {audience}. Industry: Technology, Professional Services, Finance. Company size: 10-250 employees.",
        "hashtags": [f"#{channel.replace(' ', '')}", "#B2BGrowth", "#TechInnovation", "#BusinessAutomation"],
        "suggested_schedule": [
            {"day": "Day 1 (Tuesday 9:00 AM)", "activity": "Publish Headline 1 + Variation A", "purpose": "Establish baseline problem resonance"},
            {"day": "Day 3 (Thursday 11:30 AM)", "activity": "Publish Headline 2 + Variation B", "purpose": "Present ROI and quantitative proof"},
            {"day": "Day 5 (Monday 2:00 PM)", "activity": "Publish Headline 3 + Variation C", "purpose": "Spark contrarian discussion & comments"},
            {"day": "Day 7 (Wednesday 10:00 AM)", "activity": "Direct CTA Follow-up to engaged contacts", "purpose": "Convert warm pipeline leads"}
        ]
    }

async def generate_campaign(
    db: Session,
    campaign_data: Dict[str, Any],
    force_demo_mode: bool = False
) -> Tuple[Campaign, Dict[str, Any]]:
    prompt = CAMPAIGN_USER_TEMPLATE.format(
        name=campaign_data.get("name", "New Campaign"),
        product_service=campaign_data.get("product_service", "AI Development"),
        target_audience=campaign_data.get("target_audience", "Tech founders"),
        objective=campaign_data.get("objective", "Generate discovery calls"),
        channel=campaign_data.get("channel", "LinkedIn"),
        tone=campaign_data.get("tone", "Professional & Authoritative"),
        key_selling_points=campaign_data.get("key_selling_points", "High speed, guaranteed IP"),
        call_to_action=campaign_data.get("call_to_action", "Book a discovery call"),
        additional_instructions=campaign_data.get("additional_instructions", "Keep concise")
    )

    # State 1: Demo Simulation Mode
    if force_demo_mode or not gemini_client.is_configured():
        logger.info("Executing Campaign Generation in Demo Simulation Mode.")
        parsed_json = generate_fallback_campaign(campaign_data)
        latency = 380
        status = "fallback_demo"
        is_demo_output = True
        source_label = "Demo Simulation"

        log_prompt_execution(
            db=db,
            feature_name="Campaign Generation",
            prompt_version="v3.0",
            system_instruction=CAMPAIGN_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs=campaign_data,
            model_used="demo-simulation-engine",
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json,
            error_message=None
        )

    # State 2 & 3: Live Gemini AI
    else:
        logger.info("Calling Google Gemini API for live campaign generation...")
        parsed_json, latency, status, error_msg = await gemini_client.generate_structured_json(
            prompt=prompt,
            system_instruction=CAMPAIGN_SYSTEM_PROMPT,
            temperature=0.4,
            response_schema=CampaignAIResponse
        )

        log_prompt_execution(
            db=db,
            feature_name="Campaign Generation",
            prompt_version="v3.0",
            system_instruction=CAMPAIGN_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs=campaign_data,
            model_used=gemini_client.model_name,
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json if status == "success" else {},
            error_message=error_msg
        )

        if status != "success" or not parsed_json or "content_variations" not in parsed_json:
            logger.error(f"Live Gemini API campaign generation failed: {error_msg}")
            raise HTTPException(
                status_code=502,
                detail={
                    "error": error_msg or "Gemini API returned an incomplete campaign response.",
                    "offer_demo_mode": True,
                    "message": f"Gemini AI generation failed: {error_msg or 'Incomplete schema'}. You can retry or switch to Demo Mode."
                }
            )

        is_demo_output = False
        source_label = "Gemini AI"

    campaign = Campaign(
        name=campaign_data.get("name"),
        product_service=campaign_data.get("product_service"),
        target_audience=campaign_data.get("target_audience"),
        objective=campaign_data.get("objective"),
        channel=campaign_data.get("channel"),
        tone=campaign_data.get("tone", "Professional & Authoritative"),
        key_selling_points=campaign_data.get("key_selling_points", ""),
        call_to_action=campaign_data.get("call_to_action", ""),
        additional_instructions=campaign_data.get("additional_instructions", ""),
        overview=parsed_json.get("overview", ""),
        main_message=parsed_json.get("main_message", ""),
        headlines=parsed_json.get("headlines", []),
        content_variations=parsed_json.get("content_variations", []),
        suggested_cta=parsed_json.get("suggested_cta", ""),
        recommended_audience=parsed_json.get("recommended_audience", ""),
        hashtags=parsed_json.get("hashtags", []),
        suggested_schedule=parsed_json.get("suggested_schedule", []),
        status="Draft",
        is_demo=is_demo_output
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    activity = AIActivity(
        activity_type="campaign_created",
        title=f"Created {campaign.channel} Campaign [{source_label}]: {campaign.name}",
        description=f"Generated {len(campaign.headlines)} headlines and {len(campaign.content_variations)} copy variants ({source_label}).",
        entity_type="campaign",
        entity_id=campaign.id,
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
    return campaign, meta
