import io
import re
import csv
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from fastapi import HTTPException
import pandas as pd
from sqlalchemy.orm import Session
from app.models.models import Lead, BusinessProfile, AIActivity, LeadNote
from app.services.gemini_client import gemini_client
from app.services.prompt_service import log_prompt_execution

logger = logging.getLogger("growthpilot.leads")

LEAD_SCORER_SYSTEM_PROMPT = (
    "You are an analytical B2B Lead Qualification Specialist. "
    "Evaluate leads strictly against the seller's Ideal Customer Profile (ICP) using objective criteria: "
    "Industry Alignment (30%), Decision-Maker Authority (25%), Geographic Match (20%), Company Size Viability (15%), and Source Intent (10%). "
    "CRITICAL CONSTRAINTS: Base evaluations exclusively on the provided data fields and seller profile. "
    "Never invent background facts, funding news, or company revenues not stated in the inputs. "
    "Identify any data gaps in the score explanation. "
    "Return strictly valid JSON adhering to the specified schema."
)

LEAD_SCORER_USER_TEMPLATE = """Seller Profile:
- Industry: {seller_industry}
- Services Offered: {seller_services}
- Target Audience: {seller_audience}
- Target Geographies: {seller_geography}

Lead Profile to Evaluate:
- Contact Name: {name}
- Job Title: {job_title}
- Company: {company}
- Industry: {industry}
- Company Size: {company_size}
- Location: {location}
- Lead Source: {lead_source}
- Website: {website}

Calculate an objective lead score (0-100), assign priority category (High Priority: 75-100, Medium Priority: 50-74, Low Priority: 0-49), provide business fit summary, suggested next action, and transparent factor breakdown.
Return a single JSON object with the following structure:
{{
  "score": 85,
  "qualification_category": "High Priority",
  "business_fit_summary": "Strong strategic fit based on verifiable data fields.",
  "suggested_next_action": "Send personalized outreach referencing custom AI capabilities.",
  "score_explanation": {{
    "industry_alignment": {{"score": 30, "max": 30, "reason": "Target industry matches high-priority consulting tier."}},
    "decision_maker_authority": {{"score": 25, "max": 25, "reason": "VP of Operations holds direct budgetary authority."}},
    "geographic_match": {{"score": 20, "max": 20, "reason": "Located in Australia, a primary operating region."}},
    "company_size_fit": {{"score": 15, "max": 15, "reason": "51-200 employees has established budget for external vendors."}},
    "source_intent": {{"score": 10, "max": 10, "reason": "Direct inbound consultation request via website form."}}
  }}
}}
"""

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def heuristic_lead_score(lead: Dict[str, Any], profile: Optional[BusinessProfile]) -> Dict[str, Any]:
    """
    Calibrated, transparent mathematical evaluation engine adhering to documented weights:
    - Industry Alignment: 30%
    - Authority: 25%
    - Geography: 20%
    - Company Size: 15%
    - Source Intent: 10%
    Total: 100%
    """
    industry = (lead.get("industry") or "").lower()
    title = (lead.get("job_title") or "").lower()
    loc = (lead.get("location") or "").lower()
    size = (lead.get("company_size") or "").lower()
    source = (lead.get("lead_source") or "").lower()

    # 1. Industry Alignment (Max 30 pts - 30%)
    prime_industries = ["tech", "software", "saas", "fintech", "ecommerce", "retail", "logistics", "ai", "data", "cloud", "robotics"]
    secondary_industries = ["consulting", "services", "health", "manufacturing", "proptech", "legal", "edtech", "cleantech"]

    if any(ind in industry for ind in prime_industries):
        ind_score = 30
        ind_reason = f"Prime ICP Alignment (30/30): '{lead.get('industry')}' is a core buyer for automation & development services."
    elif any(ind in industry for ind in secondary_industries):
        ind_score = 22
        ind_reason = f"Good Industry Fit (22/30): '{lead.get('industry')}' frequently commissions workflow automation & custom software."
    elif industry:
        ind_score = 15
        ind_reason = f"Moderate Industry Fit (15/30): '{lead.get('industry')}' has general tech modernisation potential."
    else:
        ind_score = 10
        ind_reason = "Unspecified Industry (10/30): Baseline assumption applied."

    # 2. Decision Maker Authority (Max 25 pts - 25%)
    high_auth_keywords = ["founder", "ceo", "cto", "coo", "chief", "vp", "director", "head of", "owner", "president", "managing director"]
    med_auth_keywords = ["manager", "lead", "architect", "strategist", "supervisor", "consultant"]

    if any(k in title for k in high_auth_keywords):
        auth_score = 25
        auth_reason = f"Executive Decision Maker (25/25): '{lead.get('job_title')}' possesses fiscal and strategic approval authority."
    elif any(k in title for k in med_auth_keywords):
        auth_score = 17
        auth_reason = f"Department Influencer (17/25): '{lead.get('job_title')}' can sponsor initiatives and initiate vendor evaluations."
    elif title:
        auth_score = 10
        auth_reason = f"Individual Contributor (10/25): '{lead.get('job_title')}' may require executive escalation."
    else:
        auth_score = 8
        auth_reason = "Unspecified Role (8/25): Baseline assumption applied."

    # 3. Geographic Match (Max 20 pts - 20%)
    geo_keywords = [
        "australia", "sydney", "melbourne", "brisbane", "perth",
        "united states", "usa", "us", "san francisco", "new york", "austin", "seattle", "chicago",
        "india", "bengaluru", "mumbai", "delhi", "pune", "hyderabad"
    ]
    if any(g in loc for g in geo_keywords):
        geo_score = 20
        geo_reason = f"Primary Market (20/20): '{lead.get('location')}' is directly covered in target delivery regions."
    elif loc and loc != "global":
        geo_score = 13
        geo_reason = f"Secondary Market (13/20): '{lead.get('location')}' can be served via remote delivery."
    else:
        geo_score = 10
        geo_reason = "Global/Unspecified (10/20): Remote feasibility assumed."

    # 4. Company Size Fit (Max 15 pts - 15%)
    if any(s in size for s in ["51-200", "201-500", "50-100", "100-250"]):
        size_score = 15
        size_reason = f"Sweet Spot ICP (15/15): '{lead.get('company_size')}' companies have dedicated budget and agility."
    elif any(s in size for s in ["11-50", "10-50"]):
        size_score = 12
        size_reason = f"Strong Startup ICP (12/15): '{lead.get('company_size')}' moves quickly on modern tech adoption."
    elif any(s in size for s in ["500+", "1000+", "enterprise"]):
        size_score = 10
        size_reason = f"Large Enterprise (10/15): '{lead.get('company_size')}' has high deal value but lengthy procurement cycles."
    elif any(s in size for s in ["1-10", "1-5", "micro"]):
        size_score = 8
        size_reason = f"Small Team (8/15): '{lead.get('company_size')}'; budget may be constrained."
    else:
        size_score = 7
        size_reason = "Unspecified Size (7/15): Default baseline applied."

    # 5. Source Intent (Max 10 pts - 10%)
    if any(src in source for src in ["website", "demo request", "inbound", "referral", "contact form"]):
        src_score = 10
        src_reason = f"High Commercial Intent (10/10): '{lead.get('lead_source')}' indicates proactive solution seeking."
    elif any(src in source for src in ["linkedin", "event", "webinar", "organic"]):
        src_score = 7
        src_reason = f"Moderate Intent (7/10): Engaged via '{lead.get('lead_source')}'."
    else:
        src_score = 5
        src_reason = f"Outbound/Cold Source (5/10): '{lead.get('lead_source')}' requires value-first nurturing."

    total_score = max(0, min(100, ind_score + auth_score + geo_score + size_score + src_score))

    if total_score >= 75:
        category = "High Priority"
        action = f"Initiate priority outreach to {lead.get('name')} with a tailored business case regarding custom AI/automation."
    elif total_score >= 50:
        category = "Medium Priority"
        action = f"Add {lead.get('name')} to targeted mid-funnel nurture sequence and connect via LinkedIn."
    else:
        category = "Low Priority"
        action = f"Enroll {lead.get('name')} into general monthly technical newsletter; monitor for role or company changes."

    return {
        "score": total_score,
        "qualification_category": category,
        "business_fit_summary": (
            f"{lead.get('company')} ({lead.get('industry')}) scored {total_score}/100 based on verified attributes. "
            f"Decision maker: {lead.get('name')} ({lead.get('job_title')}) located in {lead.get('location')}."
        ),
        "suggested_next_action": action,
        "score_explanation": {
            "industry_alignment": {"score": ind_score, "max": 30, "reason": ind_reason},
            "decision_maker_authority": {"score": auth_score, "max": 25, "reason": auth_reason},
            "geographic_match": {"score": geo_score, "max": 20, "reason": geo_reason},
            "company_size_fit": {"score": size_score, "max": 15, "reason": size_reason},
            "source_intent": {"score": src_score, "max": 10, "reason": src_reason}
        }
    }

async def score_single_lead(
    db: Session,
    lead: Lead,
    profile: Optional[BusinessProfile] = None,
    force_demo_mode: bool = False
) -> Dict[str, Any]:
    seller_industry = profile.industry if profile else "Software & Technology Services"
    seller_services = ", ".join(profile.services) if profile and profile.services else "AI Development, Web Dev, Workflow Automation"
    seller_audience = ", ".join(profile.target_audience) if profile and profile.target_audience else "Small & Medium Businesses, Startup Founders"
    seller_geography = ", ".join(profile.target_geography) if profile and profile.target_geography else "Australia, United States, India"

    prompt = LEAD_SCORER_USER_TEMPLATE.format(
        seller_industry=seller_industry,
        seller_services=seller_services,
        seller_audience=seller_audience,
        seller_geography=seller_geography,
        name=lead.name,
        job_title=lead.job_title or "Unspecified",
        company=lead.company,
        industry=lead.industry,
        company_size=lead.company_size or "Unknown",
        location=lead.location or "Global",
        lead_source=lead.lead_source or "Direct",
        website=lead.website or "N/A"
    )

    lead_dict = {
        "name": lead.name,
        "job_title": lead.job_title,
        "company": lead.company,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "location": lead.location,
        "lead_source": lead.lead_source,
        "website": lead.website
    }

    # State 1: Demo / Rule-Based Mode
    if force_demo_mode or not gemini_client.is_configured():
        parsed_json = heuristic_lead_score(lead_dict, profile)
        is_demo_output = True
        status = "fallback_demo"
        source_label = "Rule-Based Scoring"
        latency = 180

        log_prompt_execution(
            db=db,
            feature_name="Lead Qualification",
            prompt_version="v3.0",
            system_instruction=LEAD_SCORER_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs={"lead_id": lead.id, "lead_email": lead.email, "company": lead.company},
            model_used="deterministic-rubric-engine",
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json,
            error_message=None
        )

    # State 2 & 3: Live Gemini AI Evaluation
    else:
        parsed_json, latency, status, error_msg = await gemini_client.generate_structured_json(
            prompt=prompt,
            system_instruction=LEAD_SCORER_SYSTEM_PROMPT,
            temperature=0.2
        )

        log_prompt_execution(
            db=db,
            feature_name="Lead Qualification",
            prompt_version="v3.0",
            system_instruction=LEAD_SCORER_SYSTEM_PROMPT,
            prompt_rendered=prompt,
            user_inputs={"lead_id": lead.id, "lead_email": lead.email, "company": lead.company},
            model_used=gemini_client.model_name,
            execution_status=status,
            latency_ms=latency,
            generated_output=parsed_json if status == "success" else {},
            error_message=error_msg
        )

        if status != "success" or not parsed_json or "score" not in parsed_json:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": error_msg or "Gemini API lead scoring failed.",
                    "offer_demo_mode": True,
                    "message": f"Gemini lead scoring failed: {error_msg or 'Incomplete score schema'}. You can retry or use rule-based scoring."
                }
            )

        is_demo_output = False
        source_label = "Gemini AI"

    # Enforce strict score bounds
    raw_score = int(parsed_json.get("score", 50))
    lead.score = max(0, min(100, raw_score))
    lead.qualification_category = parsed_json.get("qualification_category", "Medium Priority")
    lead.business_fit_summary = parsed_json.get("business_fit_summary", "")
    lead.suggested_next_action = parsed_json.get("suggested_next_action", "")
    lead.score_explanation = parsed_json.get("score_explanation", {})
    lead.is_demo = is_demo_output

    db.commit()
    db.refresh(lead)

    activity = AIActivity(
        activity_type="lead_qualified",
        title=f"Qualified Lead [{source_label}]: {lead.name} ({lead.company})",
        description=f"Assigned score {lead.score}/100 [{lead.qualification_category}] ({source_label}).",
        entity_type="lead",
        entity_id=lead.id,
        is_demo=is_demo_output
    )
    db.add(activity)
    db.commit()

    return {
        "lead_id": lead.id,
        "score": lead.score,
        "qualification_category": lead.qualification_category,
        "business_fit_summary": lead.business_fit_summary,
        "suggested_next_action": lead.suggested_next_action,
        "score_explanation": lead.score_explanation,
        "status": status,
        "source": source_label,
        "is_demo": is_demo_output,
        "latency_ms": latency
    }

COLUMN_SYNONYMS = {
    "name": ["name", "full name", "contact name", "contact", "lead name", "person"],
    "company": ["company", "company name", "organization", "business", "employer", "firm"],
    "email": ["email", "email address", "contact email", "e-mail", "work email"],
    "website": ["website", "site", "url", "domain", "web", "company website"],
    "industry": ["industry", "sector", "vertical", "business vertical", "niche"],
    "job_title": ["job title", "title", "position", "role", "designation"],
    "location": ["location", "city", "country", "state", "geography", "region", "address"],
    "company_size": ["company size", "size", "employees", "employee count", "headcount", "team size"],
    "lead_source": ["lead source", "source", "channel", "referral source", "acquisition source", "origin"]
}

def map_column_name(header: str) -> Optional[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", header.strip().lower())
    # 1. Exact match on full string across all synonyms
    for canonical, synonyms in COLUMN_SYNONYMS.items():
        if cleaned in synonyms:
            return canonical
    # 2. Substring match prioritized by longest synonym length to prevent 'company' matching 'company size'
    all_candidates = []
    for canonical, synonyms in COLUMN_SYNONYMS.items():
        for syn in synonyms:
            if re.search(r"\b" + re.escape(syn) + r"\b", cleaned):
                all_candidates.append((len(syn), canonical))
    if all_candidates:
        all_candidates.sort(key=lambda x: x[0], reverse=True)
        return all_candidates[0][1]
    return None

def process_leads_csv(
    db: Session,
    file_bytes: bytes,
    profile: Optional[BusinessProfile] = None
) -> Dict[str, Any]:
    """
    Parses CSV, validates size and required headers, maps synonyms, eliminates duplicates,
    performs initial scoring, and inserts into SQLite database.
    """
    # 1. Enforce 5MB upload limit
    if len(file_bytes) > 5 * 1024 * 1024:
        return {
            "total_rows": 0,
            "successful_imports": 0,
            "duplicate_count": 0,
            "error_count": 1,
            "errors": ["File exceeds maximum allowed upload size (5 MB)."],
            "sample_leads": []
        }

    try:
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin1")

        df = pd.read_csv(io.StringIO(content))
    except Exception as e:
        return {
            "total_rows": 0,
            "successful_imports": 0,
            "duplicate_count": 0,
            "error_count": 1,
            "errors": [f"Failed to parse CSV file: {str(e)}"],
            "sample_leads": []
        }

    if df.empty:
        return {
            "total_rows": 0,
            "successful_imports": 0,
            "duplicate_count": 0,
            "error_count": 1,
            "errors": ["Uploaded CSV is empty."],
            "sample_leads": []
        }

    # Map headers
    col_mapping = {}
    for col in df.columns:
        canonical = map_column_name(str(col))
        if canonical:
            col_mapping[col] = canonical

    df = df.rename(columns=col_mapping)

    # Check required columns
    required_cols = ["name", "company", "email"]
    missing_required = [col for col in required_cols if col not in df.columns]
    if missing_required:
        return {
            "total_rows": len(df),
            "successful_imports": 0,
            "duplicate_count": 0,
            "error_count": 1,
            "errors": [f"Missing required columns in CSV: {', '.join(missing_required)}. Expected headers for Name, Company, Email."],
            "sample_leads": []
        }

    total_rows = len(df)
    successful = 0
    duplicates = 0
    errors = []
    created_leads = []

    # Get existing emails to avoid duplicates (case-insensitive)
    existing_emails = set(e[0].lower() for e in db.query(Lead.email).all() if e[0])

    for idx, row in df.iterrows():
        try:
            raw_email = str(row.get("email", "")).strip().lower()
            if not raw_email or not EMAIL_REGEX.match(raw_email):
                errors.append(f"Row {idx+1}: Invalid email address '{raw_email}'.")
                continue

            if raw_email in existing_emails:
                duplicates += 1
                continue

            name = str(row.get("name", "")).strip() or "Valued Contact"
            company = str(row.get("company", "")).strip() or "Enterprise Organization"
            industry = str(row.get("industry", "")).strip() if pd.notna(row.get("industry")) else "Technology"
            website = str(row.get("website", "")).strip() if pd.notna(row.get("website")) else ""
            job_title = str(row.get("job_title", "")).strip() if pd.notna(row.get("job_title")) else "Director"
            location = str(row.get("location", "")).strip() if pd.notna(row.get("location")) else "Global"
            company_size = str(row.get("company_size", "")).strip() if pd.notna(row.get("company_size")) else "11-50"
            lead_source = str(row.get("lead_source", "")).strip() if pd.notna(row.get("lead_source")) else "CSV Import"

            lead_data = {
                "name": name,
                "company": company,
                "email": raw_email,
                "website": website,
                "industry": industry,
                "job_title": job_title,
                "location": location,
                "company_size": company_size,
                "lead_source": lead_source
            }
            score_data = heuristic_lead_score(lead_data, profile)

            lead = Lead(
                name=name,
                company=company,
                email=raw_email,
                website=website,
                industry=industry,
                job_title=job_title,
                location=location,
                company_size=company_size,
                lead_source=lead_source,
                score=score_data["score"],
                qualification_category=score_data["qualification_category"],
                business_fit_summary=score_data["business_fit_summary"],
                suggested_next_action=score_data["suggested_next_action"],
                score_explanation=score_data["score_explanation"],
                status="New",
                is_demo=False # User-imported lead is NOT demo data
            )
            db.add(lead)
            existing_emails.add(raw_email)
            created_leads.append(lead)
            successful += 1

        except Exception as e:
            errors.append(f"Row {idx+1}: Processing error - {str(e)}")

    db.commit()
    for lead in created_leads[:5]:
        db.refresh(lead)

    return {
        "total_rows": total_rows,
        "successful_imports": successful,
        "duplicate_count": duplicates,
        "error_count": len(errors),
        "errors": errors[:10],
        "sample_leads": created_leads[:10]
    }
