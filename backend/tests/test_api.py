import io
import pytest

def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "ai_status" in data
    assert "ai_model" in data

def test_business_profile_get(client):
    res = client.get("/api/business-profile")
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "NovaTech Solutions"
    assert "AI Development" in data["services"]

def test_business_profile_update(client):
    update_data = {
        "company_name": "NovaTech Solutions Global",
        "industry": "B2B AI Services",
        "website": "https://novatech-global.demo",
        "description": "Enterprise AI consultancy",
        "services": ["AI Dev", "Cloud Ops"],
        "target_audience": ["Startups"],
        "target_geography": ["Australia", "US"],
        "monthly_budget": 10000.0,
        "main_objective": "Scale ARR",
        "competitors": ["Rival Agency"],
        "preferred_channels": ["LinkedIn"]
    }
    res = client.post("/api/business-profile", json=update_data)
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "NovaTech Solutions Global"

def test_generate_strategy(client):
    payload = {
        "profile_override": {
            "company_name": "Acme SaaS",
            "industry": "Fintech",
            "description": "Invoice automation software",
            "services": ["Invoice AI", "Payment Routing"],
            "target_audience": ["CFOs", "Accounting Teams"],
            "target_geography": ["Australia"],
            "monthly_budget": 5000.0,
            "main_objective": "Acquire 50 paying SMB clients",
            "competitors": ["Generic Tools"],
            "preferred_channels": ["LinkedIn", "Direct Email"]
        }
    }
    res = client.post("/api/ai/strategy", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "strategy" in data
    assert "summary" in data["strategy"]
    assert len(data["strategy"]["thirty_day_plan"]) > 0

def test_campaign_lifecycle(client):
    # Create
    campaign_payload = {
        "name": "Q4 CFO Push",
        "product_service": "Automated Invoicing",
        "target_audience": "Finance Directors",
        "objective": "Lead Generation",
        "channel": "LinkedIn",
        "tone": "Authoritative",
        "key_selling_points": "Saves 10 hours/week",
        "call_to_action": "Claim Free Audit",
        "additional_instructions": "Focus on cash flow"
    }
    res = client.post("/api/ai/campaign", json=campaign_payload)
    assert res.status_code == 200
    camp = res.json()["campaign"]
    camp_id = camp["id"]
    assert len(camp["headlines"]) >= 3
    assert len(camp["content_variations"]) >= 2

    # Get
    res = client.get(f"/api/campaigns/{camp_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Q4 CFO Push"

    # Update
    res = client.put(f"/api/campaigns/{camp_id}", json={"status": "Active"})
    assert res.status_code == 200
    assert res.json()["status"] == "Active"

    # Delete
    res = client.delete(f"/api/campaigns/{camp_id}")
    assert res.status_code == 200

def test_content_plan_generation(client):
    res = client.post("/api/ai/content-plan", json={"days": 5, "focus_channel": "All Channels"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5

def test_leads_csv_import_and_duplicate_handling(client):
    csv_content = """Name,Company,Email,Industry,Job Title,Location,Company Size,Lead Source
Alice Green,Veritas Capital,alice@veritascap.com,Finance,Chief Financial Officer,Sydney,51-200,Website Form
Bob White,Solaris Health,bob@solarishealth.com,Healthcare,Director of Operations,Melbourne,11-50,LinkedIn
Alice Green,Veritas Capital,alice@veritascap.com,Finance,CFO,Sydney,51-200,Duplicate Entry
"""
    file_tuple = ("test_leads.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    res = client.post("/api/leads/import", files={"file": file_tuple})
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 3
    assert data["successful_imports"] == 2
    assert data["duplicate_count"] == 1

def test_leads_search_and_filter(client):
    res = client.get("/api/leads?search=Sarah")
    assert res.status_code == 200
    leads = res.json()
    assert len(leads) >= 1
    assert "Sarah" in leads[0]["name"]

def test_analytics_overview(client):
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_leads"] > 0
    assert data["qualification_rate"] >= 0
    assert "leads_by_category" in data
    assert "monthly_activity" in data

def test_prompt_lab_history(client):
    res = client.get("/api/prompts")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 3

    res = client.get("/api/prompts/history")
    assert res.status_code == 200
    history = res.json()
    assert len(history) >= 1

def test_csv_formula_injection_sanitization(client):
    csv_content = """Name,Company,Email,Industry,Job Title,Location,Company Size,Lead Source
=cmd|' /C calc'!A0,Acme Inc,formula_inj_1@acme.com,Technology,Founder,Sydney,11-50,LinkedIn
+123456,Plus Inc,formula_inj_2@acme.com,Finance,Director,Melbourne,51-200,Referral
"@SUM(1,2)",At Inc,formula_inj_3@acme.com,Healthcare,Manager,Brisbane,1-10,Website
"""
    file_tuple = ("injection_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    res = client.post("/api/leads/import", files={"file": file_tuple})
    assert res.status_code == 200
    assert res.json()["successful_imports"] == 3

    # Export leads to CSV
    export_res = client.get("/api/leads/export")
    assert export_res.status_code == 200
    exported_text = export_res.text

    # Verify that cells starting with =, +, @ are sanitized with leading single quote
    assert "'=cmd|' /C calc'!A0" in exported_text
    assert "'+123456" in exported_text
    assert "'@SUM(1,2)" in exported_text

def test_csv_file_size_limit_rejection(client):
    large_payload = b"A" * (5 * 1024 * 1024 + 1024)
    file_tuple = ("large.csv", io.BytesIO(large_payload), "text/csv")
    res = client.post("/api/leads/import", files={"file": file_tuple})
    assert res.status_code == 413
    assert "exceeds maximum limit of 5 MB" in res.json()["detail"]

def test_csv_case_insensitive_duplicate_email(client):
    csv_initial = """Name,Company,Email,Industry,Job Title,Location,Company Size,Lead Source
Clara Oswald,Time Corp,clara@timecorp.demo,Technology,Founder,Sydney,11-50,LinkedIn
"""
    client.post("/api/leads/import", files={"file": ("c1.csv", io.BytesIO(csv_initial.encode("utf-8")), "text/csv")})

    # Import with uppercase email
    csv_upper = """Name,Company,Email,Industry,Job Title,Location,Company Size,Lead Source
Clara Upper,Time Corp,CLARA@TIMECORP.DEMO,Technology,Founder,Sydney,11-50,LinkedIn
"""
    res = client.post("/api/leads/import", files={"file": ("c2.csv", io.BytesIO(csv_upper.encode("utf-8")), "text/csv")})
    assert res.status_code == 200
    data = res.json()
    assert data["duplicate_count"] == 1
    assert data["successful_imports"] == 0

def test_csv_invalid_email_handling(client):
    csv_invalid = """Name,Company,Email,Industry,Job Title,Location,Company Size,Lead Source
Bad Email,Broken Corp,not-an-email-at-all,Technology,CEO,Sydney,11-50,LinkedIn
"""
    res = client.post("/api/leads/import", files={"file": ("bad.csv", io.BytesIO(csv_invalid.encode("utf-8")), "text/csv")})
    assert res.status_code == 200
    data = res.json()
    assert data["error_count"] == 1
    assert len(data["errors"]) == 1
    assert "Invalid email address" in data["errors"][0]

def test_lead_scoring_heuristic_rubric_weights():
    from app.services.lead_scoring_service import heuristic_lead_score
    score_data = heuristic_lead_score({
        "industry": "B2B Technology",
        "job_title": "Founder & CEO",
        "location": "Sydney, Australia",
        "company_size": "51-200",
        "lead_source": "Referral"
    }, profile=None)

    assert score_data["score"] == 100
    assert score_data["qualification_category"] == "High Priority"
    explanation = score_data["score_explanation"]
    assert explanation["industry_alignment"]["score"] == 30
    assert explanation["decision_maker_authority"]["score"] == 25
    assert explanation["geographic_match"]["score"] == 20
    assert explanation["company_size_fit"]["score"] == 15
    assert explanation["source_intent"]["score"] == 10

    # Low alignment test
    low_data = heuristic_lead_score({
        "industry": "",
        "job_title": "",
        "location": "global",
        "company_size": "",
        "lead_source": "cold outbound"
    }, profile=None)
    assert low_data["score"] <= 40
    assert low_data["qualification_category"] == "Low Priority"

def test_ai_error_handling_when_gemini_fails(client):
    from unittest.mock import AsyncMock, patch
    with patch("app.services.gemini_client.gemini_client.generate_structured_json", new_callable=AsyncMock) as mock_gemini:
        with patch("app.services.gemini_client.gemini_client.is_configured", return_value=True):
            mock_gemini.return_value = (None, 150, "error", "API Key Invalid or Quota Exhausted")
            
            res = client.post("/api/ai/strategy", json={
                "profile_override": {
                    "company_name": "Test Enterprise",
                    "industry": "Tech",
                    "description": "Enterprise Solutions",
                    "services": ["AI Dev"],
                    "target_audience": ["Founders"],
                    "target_geography": ["Australia"],
                    "monthly_budget": 5000.0,
                    "main_objective": "Growth",
                    "competitors": [],
                    "preferred_channels": []
                },
                "force_demo_mode": False
            })
            assert res.status_code == 502
            detail = res.json()["detail"]
            assert detail["offer_demo_mode"] is True
            assert "Gemini AI generation failed" in detail["message"]

def test_demo_reset_preserves_user_leads(client):
    user_csv = """Name,Company,Email,Industry,Job Title,Location,Company Size,Lead Source
User Saved Lead,Preserve Corp,preserved@usercorp.demo,Technology,VP Engineering,Sydney,51-200,Direct
"""
    import_res = client.post("/api/leads/import", files={"file": ("user.csv", io.BytesIO(user_csv.encode("utf-8")), "text/csv")})
    assert import_res.status_code == 200

    # Trigger demo reset
    reset_res = client.post("/api/settings/reset-demo")
    assert reset_res.status_code == 200

    # Verify that the user's lead is still present
    leads_res = client.get("/api/leads?search=preserved@usercorp.demo")
    assert leads_res.status_code == 200
    leads = leads_res.json()
    assert len(leads) == 1
    assert leads[0]["email"] == "preserved@usercorp.demo"
    assert leads[0]["is_demo"] is False
