import math
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.models import Lead, Campaign, ContentItem, AIActivity, CampaignMetric

def get_analytics_overview(db: Session) -> Dict[str, Any]:
    total_leads = db.query(Lead).count()
    qualified_leads = db.query(Lead).filter(
        (Lead.qualification_category == "High Priority") | (Lead.status == "Qualified")
    ).count()

    qualification_rate = round((qualified_leads / total_leads * 100), 1) if total_leads > 0 else 0.0

    avg_score_res = db.query(func.avg(Lead.score)).scalar()
    avg_lead_score = round(float(avg_score_res or 0), 1)

    active_campaigns = db.query(Campaign).filter(Campaign.status.in_(["Active", "Draft", "Published"])).count()
    content_generated_count = db.query(ContentItem).count()

    # Leads by category
    category_counts = {}
    for cat in ["High Priority", "Medium Priority", "Low Priority"]:
        category_counts[cat] = db.query(Lead).filter(Lead.qualification_category == cat).count()

    # Leads by source
    source_counts = {}
    for src, count in db.query(Lead.lead_source, func.count(Lead.id)).group_by(Lead.lead_source).all():
        source_counts[src or "Direct"] = count

    # Leads by industry
    industry_counts = {}
    for ind, count in db.query(Lead.industry, func.count(Lead.id)).group_by(Lead.industry).all():
        industry_counts[ind or "Other"] = count

    # Leads by geography
    geo_counts = {}
    for loc, count in db.query(Lead.location, func.count(Lead.id)).group_by(Lead.location).all():
        geo_counts[loc or "Global"] = count

    # Recent AI activities
    recent_activities = db.query(AIActivity).order_by(AIActivity.created_at.desc()).limit(8).all()

    # High priority leads
    top_leads = db.query(Lead).filter(Lead.qualification_category == "High Priority").order_by(Lead.score.desc()).limit(6).all()

    # Upcoming content
    upcoming = db.query(ContentItem).filter(
        ContentItem.status.in_(["Draft", "Pending Approval", "Approved"])
    ).order_by(ContentItem.publication_date.asc()).limit(6).all()

    # Authentic Lead Acquisition Trend derived from database creation dates (Zero Fabrication)
    trend_dict: Dict[str, Dict[str, Any]] = {}
    all_leads = db.query(Lead.created_at, Lead.qualification_category, Lead.status).order_by(Lead.created_at.asc()).all()

    for created_at, cat, status in all_leads:
        if not created_at:
            continue
        period_key = created_at.strftime("%Y-%m")
        display_month = created_at.strftime("%b")
        if period_key not in trend_dict:
            trend_dict[period_key] = {"period": period_key, "month": display_month, "leads": 0, "qualified": 0}
        trend_dict[period_key]["leads"] += 1
        if cat == "High Priority" or status == "Qualified":
            trend_dict[period_key]["qualified"] += 1

    trend = sorted(trend_dict.values(), key=lambda x: x["period"])
    has_sufficient_history = len(trend) >= 2

    # If all leads share a single creation period (e.g. initial demo load), present authentic baseline
    if len(trend) == 1:
        trend[0]["has_sufficient_data"] = False
    elif len(trend) == 0 and total_leads > 0:
        trend = [{"period": datetime.date.today().strftime("%Y-%m"), "month": datetime.date.today().strftime("%b"), "leads": total_leads, "qualified": qualified_leads, "has_sufficient_data": False}]

    # Authentic Campaign Performance from CampaignMetric records (Zero Fabrication)
    # Standard Marketing Metrics Formula Documentation:
    # - Click-Through Rate (CTR): (clicks / impressions) * 100
    # - Cost Per Lead (CPL): spend / conversions (where conversions denote leads acquired)
    # - Return On Investment (ROI): ((revenue - spend) / spend) * 100
    campaigns = db.query(Campaign).all()
    campaign_perf = []

    for c in campaigns:
        # Aggregate persisted metrics for this specific campaign
        metrics = db.query(CampaignMetric).filter(CampaignMetric.campaign_id == c.id).all()

        if metrics:
            imp = sum(m.impressions for m in metrics)
            clk = sum(m.clicks for m in metrics)
            conv = sum(m.conversions for m in metrics)
            sp = sum(m.spend for m in metrics)
            rev = sum(m.revenue for m in metrics)

            ctr = round((clk / imp * 100), 2) if imp > 0 else None
            cpl = round((sp / conv), 2) if conv > 0 else None
            roi = round(((rev - sp) / sp * 100), 1) if sp > 0 else None

            campaign_perf.append({
                "campaign_id": c.id,
                "name": c.name[:28],
                "channel": c.channel,
                "impressions": imp,
                "clicks": clk,
                "conversions": conv,
                "leads": conv,
                "spend": round(sp, 2),
                "revenue": round(rev, 2),
                "ctr": ctr,
                "cpl": cpl,
                "roi": roi,
                "status": c.status,
                "has_data": True
            })
        else:
            # Explicitly mark that no metric data exists yet for this campaign
            campaign_perf.append({
                "campaign_id": c.id,
                "name": c.name[:28],
                "channel": c.channel,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "leads": 0,
                "spend": 0.0,
                "revenue": 0.0,
                "ctr": None,
                "cpl": None,
                "roi": None,
                "status": c.status,
                "has_data": False
            })

    # Include unassigned channel-level metrics (campaign_id is None)
    unassigned_metrics = db.query(CampaignMetric).filter(CampaignMetric.campaign_id.is_(None)).all()
    channel_groups: Dict[str, List[CampaignMetric]] = {}
    for m in unassigned_metrics:
        ch = m.channel or "Unassigned"
        if ch not in channel_groups:
            channel_groups[ch] = []
        channel_groups[ch].append(m)

    for ch, ch_mets in sorted(channel_groups.items(), key=lambda x: x[0]):
        imp = sum(m.impressions for m in ch_mets)
        clk = sum(m.clicks for m in ch_mets)
        conv = sum(m.conversions for m in ch_mets)
        sp = sum(m.spend for m in ch_mets)
        rev = sum(m.revenue for m in ch_mets)

        ctr = round((clk / imp * 100), 2) if imp > 0 else None
        cpl = round((sp / conv), 2) if conv > 0 else None
        roi = round(((rev - sp) / sp * 100), 1) if sp > 0 else None

        campaign_perf.append({
            "campaign_id": None,
            "name": f"[Channel] {ch}",
            "channel": ch,
            "impressions": imp,
            "clicks": clk,
            "conversions": conv,
            "leads": conv,
            "spend": round(sp, 2),
            "revenue": round(rev, 2),
            "ctr": ctr,
            "cpl": cpl,
            "roi": roi,
            "status": "Channel Only",
            "has_data": True
        })

    # Global total spend and revenue aggregated across ALL metrics (both campaign-linked and channel-only)
    total_spend_raw = db.query(func.sum(CampaignMetric.spend)).scalar()
    total_rev_raw = db.query(func.sum(CampaignMetric.revenue)).scalar()
    total_spend = float(total_spend_raw or 0.0)
    total_revenue = float(total_rev_raw or 0.0)

    # Monthly activity breakdown
    monthly_activity = [
        {"activity": "AI Strategies Generated", "count": db.query(AIActivity).filter(AIActivity.activity_type == "strategy_generated").count()},
        {"activity": "Campaigns Launched", "count": db.query(Campaign).count()},
        {"activity": "Content Calendar Posts", "count": db.query(ContentItem).count()},
        {"activity": "Lead Scoring Evaluations", "count": total_leads}
    ]

    # Authentic demonstration data determination
    demo_count = db.query(Lead).filter(Lead.is_demo.is_(True)).count()
    is_demo_data = (demo_count / total_leads > 0.5) if total_leads > 0 else True

    return {
        "total_leads": total_leads,
        "qualified_leads": qualified_leads,
        "qualification_rate": qualification_rate,
        "average_lead_score": avg_lead_score,
        "active_campaigns": active_campaigns,
        "content_generated_count": content_generated_count,
        "leads_by_category": category_counts,
        "leads_by_source": source_counts,
        "leads_by_industry": industry_counts,
        "leads_by_geography": geo_counts,
        "monthly_activity": monthly_activity,
        "lead_acquisition_trend": trend,
        "campaign_performance": campaign_perf,
        "recent_activities": recent_activities,
        "high_priority_leads": top_leads,
        "upcoming_content": upcoming,
        "is_demo_data": is_demo_data,
        "has_sufficient_history": has_sufficient_history,
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2)
    }

def import_campaign_metrics(db: Session, df: pd.DataFrame, is_demo: bool = False) -> Dict[str, Any]:
    """
    Imports and strictly validates campaign metrics CSV data into CampaignMetric persistence.

    Validation Rules:
    - Required columns: metric_date, channel, impressions, clicks, conversions, spend, revenue.
    - Dates must be parseable YYYY-MM-DD (no silent fallback to today).
    - Numeric values must be non-negative, finite numbers (no NaN or Inf, no silent zero-clamping).
    - Campaign lookup: if campaign_id or campaign_name is specified, it must exist in DB.
      If neither is specified, records are imported as channel-level metrics (campaign_id = None).
    - Duplicate prevention: rejects rows whose (metric_date, channel, campaign_id) matches
      another row in the batch or an existing database entry.
    """
    synonym_map = {
        "campaign": "campaign_name",
        "campaign_name": "campaign_name",
        "campaign_id": "campaign_id",
        "date": "metric_date",
        "metric_date": "metric_date",
        "channel": "channel",
        "impressions": "impressions",
        "clicks": "clicks",
        "conversions": "conversions",
        "spend": "spend",
        "cost": "spend",
        "revenue": "revenue"
    }

    # Normalize columns
    normalized_cols = {}
    for col in df.columns:
        clean = str(col).strip().lower().replace(" ", "_")
        if clean in synonym_map:
            normalized_cols[col] = synonym_map[clean]
    df = df.rename(columns=normalized_cols)

    required_columns = ["metric_date", "channel", "impressions", "clicks", "conversions", "spend", "revenue"]
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        return {
            "total_rows": len(df),
            "successful_imports": 0,
            "error_count": 1,
            "errors": [f"Missing required CSV columns: {', '.join(sorted(missing_cols))}"]
        }

    successful = 0
    errors = []
    seen_in_batch = set()

    # Map existing campaigns for lookup
    campaigns = db.query(Campaign).all()
    campaigns_by_name = {c.name.strip().lower(): c.id for c in campaigns}
    campaign_ids = {c.id for c in campaigns}

    staged_records: List[CampaignMetric] = []

    for idx, row in df.iterrows():
        line_num = idx + 2
        try:
            # 1. Resolve campaign id if specified
            camp_id: Optional[int] = None
            has_camp_id = "campaign_id" in row and pd.notna(row["campaign_id"]) and str(row["campaign_id"]).strip() != ""
            has_camp_name = "campaign_name" in row and pd.notna(row["campaign_name"]) and str(row["campaign_name"]).strip() != ""

            if has_camp_id:
                try:
                    c_id_candidate = int(float(str(row["campaign_id"]).strip()))
                    if c_id_candidate not in campaign_ids:
                        errors.append(f"Row {line_num}: Specified campaign_id '{row['campaign_id']}' does not exist.")
                        continue
                    camp_id = c_id_candidate
                except (ValueError, TypeError):
                    errors.append(f"Row {line_num}: Invalid campaign_id '{row['campaign_id']}'. Must be an integer.")
                    continue
            elif has_camp_name:
                name_key = str(row["campaign_name"]).strip().lower()
                if name_key not in campaigns_by_name:
                    errors.append(f"Row {line_num}: Specified campaign_name '{row['campaign_name']}' does not exist.")
                    continue
                camp_id = campaigns_by_name[name_key]

            # 2. Date validation (Strict parse, no fallback)
            raw_date = row.get("metric_date")
            if pd.isna(raw_date) or str(raw_date).strip() == "":
                errors.append(f"Row {line_num}: metric_date is required.")
                continue
            try:
                parsed_dt = pd.to_datetime(str(raw_date).strip())
                date_val = parsed_dt.date()
            except Exception:
                errors.append(f"Row {line_num}: Invalid date format '{raw_date}'. Expected valid date (YYYY-MM-DD).")
                continue

            # 3. Channel validation
            raw_channel = row.get("channel")
            if pd.isna(raw_channel) or str(raw_channel).strip() == "" or str(raw_channel).strip().lower() == "nan":
                errors.append(f"Row {line_num}: channel is required.")
                continue
            channel = str(raw_channel).strip()

            # 4. Strict numeric validations (Integers)
            def parse_non_neg_int(val: Any, field_name: str) -> int:
                if pd.isna(val) or str(val).strip() == "":
                    raise ValueError(f"{field_name} is required and cannot be empty.")
                try:
                    f = float(str(val).strip())
                except ValueError:
                    raise ValueError(f"{field_name} must be a number, got '{val}'.")
                if math.isnan(f) or math.isinf(f):
                    raise ValueError(f"{field_name} cannot be NaN or infinite.")
                if f < 0:
                    raise ValueError(f"{field_name} cannot be negative ({val}).")
                if not f.is_integer():
                    raise ValueError(f"{field_name} must be an integer, got {val}.")
                return int(f)

            # Strict numeric validations (Floats)
            def parse_non_neg_float(val: Any, field_name: str) -> float:
                if pd.isna(val) or str(val).strip() == "":
                    raise ValueError(f"{field_name} is required and cannot be empty.")
                try:
                    f = float(str(val).strip())
                except ValueError:
                    raise ValueError(f"{field_name} must be a number, got '{val}'.")
                if math.isnan(f) or math.isinf(f):
                    raise ValueError(f"{field_name} cannot be NaN or infinite.")
                if f < 0:
                    raise ValueError(f"{field_name} cannot be negative ({val}).")
                return round(f, 2)

            impressions = parse_non_neg_int(row.get("impressions"), "impressions")
            clicks = parse_non_neg_int(row.get("clicks"), "clicks")
            conversions = parse_non_neg_int(row.get("conversions"), "conversions")
            spend = parse_non_neg_float(row.get("spend"), "spend")
            revenue = parse_non_neg_float(row.get("revenue"), "revenue")

            if clicks > impressions:
                errors.append(f"Row {line_num}: clicks ({clicks}) cannot exceed impressions ({impressions}).")
                continue
            if conversions > clicks and clicks > 0:
                errors.append(f"Row {line_num}: conversions ({conversions}) cannot exceed clicks ({clicks}).")
                continue

            # 5. Duplicate prevention
            dup_key = (date_val, channel.lower(), camp_id)
            if dup_key in seen_in_batch:
                errors.append(f"Row {line_num}: Duplicate metric entry for date {date_val}, channel '{channel}', and campaign {camp_id} in this file.")
                continue

            existing_db = db.query(CampaignMetric).filter(
                CampaignMetric.metric_date == date_val,
                func.lower(CampaignMetric.channel) == channel.lower(),
                CampaignMetric.campaign_id == camp_id
            ).first()
            if existing_db:
                errors.append(f"Row {line_num}: Metric record already exists in database for date {date_val}, channel '{channel}', and campaign {camp_id}.")
                continue

            seen_in_batch.add(dup_key)

            metric_record = CampaignMetric(
                campaign_id=camp_id,
                metric_date=date_val,
                channel=channel,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                spend=spend,
                revenue=revenue,
                is_demo=is_demo
            )
            staged_records.append(metric_record)
            successful += 1

        except ValueError as ve:
            errors.append(f"Row {line_num}: {str(ve)}")
        except Exception as e:
            errors.append(f"Row {line_num}: Unexpected error: {str(e)}")

    if staged_records:
        db.add_all(staged_records)
        db.commit()

    return {
        "total_rows": len(df),
        "successful_imports": successful,
        "error_count": len(errors),
        "errors": errors
    }
