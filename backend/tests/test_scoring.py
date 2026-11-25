import pytest
from app.services.lead_scoring_service import heuristic_lead_score, matches_token, normalize_geo
from app.models.models import BusinessProfile

def test_token_matching_prevents_substring_false_positives():
    # 'ai' should not match 'training'
    assert not matches_token("Corporate Training & Seminars", ["ai"])
    assert matches_token("Enterprise AI Solutions", ["ai"])

    # 'us' should not match 'business'
    assert not matches_token("Business Bay Consulting", ["us"])
    assert matches_token("Austin, US", ["us"])

def test_normalize_geo():
    assert normalize_geo("San Francisco, CA, USA") == "united states"
    assert normalize_geo("Sydney, NSW, Australia") == "australia"
    assert normalize_geo("Bengaluru, India") == "india"
    assert normalize_geo("London, UK") == "united kingdom"
    assert normalize_geo("Toronto, Canada") == "canada"

def test_heuristic_lead_score_bounds_and_accuracy():
    profile = BusinessProfile(
        company_name="NovaTech Solutions",
        industry="Software & AI Services",
        services=["Custom AI", "Workflow Automation"],
        target_audience=["B2B SaaS", "Enterprises"],
        target_geography=["Australia", "United States"]
    )

    # High priority lead
    high_lead = {
        "name": "Sarah Connor",
        "job_title": "Chief Technology Officer",
        "company": "Cyberdyne Systems",
        "industry": "SaaS & AI Software",
        "company_size": "51-200",
        "location": "Sydney, Australia",
        "lead_source": "Website Demo Request",
        "website": "https://cyberdyne.demo"
    }
    result = heuristic_lead_score(high_lead, profile)
    assert 0 <= result["score"] <= 100
    assert result["score"] >= 75
    assert result["qualification_category"] == "High Priority"
    assert result["score_explanation"]["industry_alignment"]["score"] == 30
    assert result["score_explanation"]["decision_maker_authority"]["score"] == 25
    assert result["score_explanation"]["geographic_match"]["score"] == 20

    # Low priority lead with words that used to cause false positives
    low_lead = {
        "name": "Bob Vance",
        "job_title": "Intern",
        "company": "Vance Refrigeration",
        "industry": "Corporate Training",
        "company_size": "1-5",
        "location": "Global",
        "lead_source": "Cold List",
        "website": ""
    }
    res_low = heuristic_lead_score(low_lead, profile)
    assert 0 <= res_low["score"] <= 100
    assert res_low["score"] < 50
    assert res_low["qualification_category"] == "Low Priority"
    # Verify training didn't get 30/30 for 'ai'
    assert res_low["score_explanation"]["industry_alignment"]["score"] != 30
    # Verify location didn't get 20/20 for 'us'
    assert res_low["score_explanation"]["geographic_match"]["score"] != 20
