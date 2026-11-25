import io
import datetime
import pytest
import pandas as pd
from app.models.models import Campaign, CampaignMetric
from app.services.analytics_service import get_analytics_overview, import_campaign_metrics

def test_analytics_overview_empty_metrics(monkeypatch):
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        # Clear metrics
        db.query(CampaignMetric).delete()
        db.commit()

        overview = get_analytics_overview(db)
        assert overview["total_spend"] == 0.0
        assert overview["total_revenue"] == 0.0
        assert isinstance(overview["campaign_performance"], list)
        for perf in overview["campaign_performance"]:
            assert perf["spend"] == 0.0
            assert perf["ctr"] is None
            assert perf["cpl"] is None
            assert perf["roi"] is None
    finally:
        db.close()

def test_analytics_overview_aggregates_channel_only_and_campaign_metrics():
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        # Clean existing
        db.query(CampaignMetric).delete()
        db.commit()

        # Create a campaign
        camp = Campaign(
            name="Q1 Product Launch",
            product_service="Workflow AI",
            target_audience="CTOs & Tech Leaders",
            objective="Lead Generation",
            overview="Strategic Q1 push",
            main_message="Automate your growth",
            channel="Google Search",
            status="Active"
        )
        db.add(camp)
        db.commit()
        db.refresh(camp)

        # 1. Metric attached to campaign
        m1 = CampaignMetric(
            campaign_id=camp.id,
            metric_date=datetime.date(2026, 2, 1),
            channel="Google Search",
            impressions=1000,
            clicks=100,
            conversions=10,
            spend=500.0,
            revenue=1500.0
        )

        # 2. Channel-only metric (campaign_id is None)
        m2 = CampaignMetric(
            campaign_id=None,
            metric_date=datetime.date(2026, 2, 2),
            channel="LinkedIn Ads",
            impressions=2000,
            clicks=80,
            conversions=4,
            spend=400.0,
            revenue=800.0
        )
        db.add_all([m1, m2])
        db.commit()

        overview = get_analytics_overview(db)

        # Total spend: 500 + 400 = 900
        assert overview["total_spend"] == 900.0
        # Total revenue: 1500 + 800 = 2300
        assert overview["total_revenue"] == 2300.0

        # Check performance items
        names = [p["name"] for p in overview["campaign_performance"]]
        assert "Q1 Product Launch" in names
        assert "[Channel] LinkedIn Ads" in names

        # Find campaign performance item
        camp_perf = next(p for p in overview["campaign_performance"] if p["campaign_id"] == camp.id)
        assert camp_perf["impressions"] == 1000
        assert camp_perf["clicks"] == 100
        assert camp_perf["conversions"] == 10
        assert camp_perf["ctr"] == 10.0 # (100 / 1000) * 100
        assert camp_perf["cpl"] == 50.0 # 500 / 10
        assert camp_perf["roi"] == 200.0 # ((1500 - 500) / 500) * 100

        # Find channel-only performance item
        ch_perf = next(p for p in overview["campaign_performance"] if p["campaign_id"] is None)
        assert ch_perf["channel"] == "LinkedIn Ads"
        assert ch_perf["ctr"] == 4.0 # (80 / 2000) * 100
        assert ch_perf["cpl"] == 100.0 # 400 / 4
        assert ch_perf["roi"] == 100.0 # ((800 - 400) / 400) * 100
    finally:
        db.close()

def test_campaign_deletion_disassociates_metrics():
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        camp = Campaign(
            name="Temporary Promo",
            product_service="Workflow AI",
            target_audience="CTOs & Tech Leaders",
            objective="Lead Generation",
            overview="Promo overview",
            main_message="Promo message",
            channel="Email",
            status="Draft"
        )
        db.add(camp)
        db.commit()
        db.refresh(camp)
        camp_id = camp.id

        metric = CampaignMetric(
            campaign_id=camp_id,
            metric_date=datetime.date(2026, 3, 1),
            channel="Email",
            impressions=500,
            clicks=50,
            conversions=5,
            spend=50.0,
            revenue=200.0
        )
        db.add(metric)
        db.commit()

        # Delete campaign via API or logic: verify disassociation
        db.query(CampaignMetric).filter(CampaignMetric.campaign_id == camp_id).update({"campaign_id": None})
        db.delete(camp)
        db.commit()

        # Metric should still exist in database with campaign_id None
        persisted = db.query(CampaignMetric).filter(CampaignMetric.channel == "Email").first()
        assert persisted is not None
        assert persisted.campaign_id is None
        assert persisted.impressions == 500
    finally:
        db.close()

def test_import_campaign_metrics_missing_required_columns():
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        df = pd.DataFrame([{
            "channel": "Search",
            "impressions": 100
            # missing date, clicks, conversions, spend, revenue
        }])
        res = import_campaign_metrics(db, df)
        assert res["successful_imports"] == 0
        assert res["error_count"] >= 1
        assert "Missing required CSV columns" in res["errors"][0]
    finally:
        db.close()

def test_import_campaign_metrics_strict_validations():
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        # Clear metrics
        db.query(CampaignMetric).delete()
        db.commit()

        # Bad rows:
        # Row 2: Invalid date format
        # Row 3: Negative spend
        # Row 4: Non-existent campaign_id
        # Row 5: Clicks > Impressions
        # Row 6: Valid row (channel-only)
        df = pd.DataFrame([
            {"metric_date": "not-a-date", "channel": "Social", "impressions": 100, "clicks": 10, "conversions": 1, "spend": 10.0, "revenue": 20.0},
            {"metric_date": "2026-03-01", "channel": "Social", "impressions": 100, "clicks": 10, "conversions": 1, "spend": -50.0, "revenue": 20.0},
            {"metric_date": "2026-03-02", "channel": "Social", "campaign_id": 99999, "impressions": 100, "clicks": 10, "conversions": 1, "spend": 50.0, "revenue": 20.0},
            {"metric_date": "2026-03-03", "channel": "Social", "impressions": 10, "clicks": 50, "conversions": 1, "spend": 50.0, "revenue": 20.0},
            {"metric_date": "2026-03-04", "channel": "Display", "impressions": 100, "clicks": 10, "conversions": 1, "spend": 50.0, "revenue": 100.0},
        ])

        res = import_campaign_metrics(db, df)
        assert res["total_rows"] == 5
        assert res["successful_imports"] == 1
        assert res["error_count"] == 4
        assert any("Invalid date" in err for err in res["errors"])
        assert any("cannot be negative" in err for err in res["errors"])
        assert any("does not exist" in err for err in res["errors"])
        assert any("cannot exceed impressions" in err for err in res["errors"])
    finally:
        db.close()

def test_import_campaign_metrics_duplicate_rejection():
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        db.query(CampaignMetric).delete()
        db.commit()

        # 1. In-batch duplicate test
        df_batch = pd.DataFrame([
            {"metric_date": "2026-04-01", "channel": "Search", "impressions": 100, "clicks": 10, "conversions": 1, "spend": 20.0, "revenue": 50.0},
            {"metric_date": "2026-04-01", "channel": "Search", "impressions": 200, "clicks": 20, "conversions": 2, "spend": 40.0, "revenue": 100.0},
        ])
        res_batch = import_campaign_metrics(db, df_batch)
        assert res_batch["successful_imports"] == 1
        assert res_batch["error_count"] == 1
        assert any("Duplicate metric entry" in err for err in res_batch["errors"])

        # 2. Existing database duplicate test
        df_second = pd.DataFrame([
            {"metric_date": "2026-04-01", "channel": "Search", "impressions": 300, "clicks": 30, "conversions": 3, "spend": 60.0, "revenue": 150.0},
        ])
        res_db = import_campaign_metrics(db, df_second)
        assert res_db["successful_imports"] == 0
        assert res_db["error_count"] == 1
        assert any("already exists in database" in err for err in res_db["errors"])
    finally:
        db.close()
