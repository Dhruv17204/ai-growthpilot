import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.gemini_client import GeminiClient, categorize_gemini_error

def test_categorize_gemini_error():
    assert "Invalid or expired Gemini API key" in categorize_gemini_error(Exception("401 Unauthorized API key"))
    assert "Rate limit or quota exceeded" in categorize_gemini_error(Exception("429 Resource Exhausted"))
    assert "temporarily unavailable" in categorize_gemini_error(Exception("503 Service Unavailable"))
    assert "Network connectivity error" in categorize_gemini_error(Exception("Connection reset by peer"))

@pytest.mark.asyncio
async def test_unconfigured_client_returns_fallback_demo():
    client = GeminiClient()
    client.api_key = ""
    client._client = None
    assert not client.is_configured()

    data, latency, status, error = await client.generate_structured_json("Test prompt")
    assert status == "fallback_demo"
    assert data == {}
    assert "not configured" in error

@pytest.mark.asyncio
async def test_successful_gemini_json_generation():
    client = GeminiClient()
    client.api_key = "test_key"
    mock_sdk_client = MagicMock()
    client._client = mock_sdk_client

    mock_response = MagicMock()
    mock_response.text = '```json\n{"strategy": "Focus on high-ROI outbound", "kpis": ["ARR"]}\n```'

    with patch.object(client, "_execute_content_generation", new=AsyncMock(return_value=mock_response)):
        data, latency, status, error = await client.generate_structured_json("Generate strategy")
        assert status == "success"
        assert error is None
        assert data["strategy"] == "Focus on high-ROI outbound"
        assert "ARR" in data["kpis"]

@pytest.mark.asyncio
async def test_gemini_malformed_json_handling():
    client = GeminiClient()
    client.api_key = "test_key"
    client._client = MagicMock()

    mock_response = MagicMock()
    mock_response.text = 'This is plain text, not valid JSON { broken'

    with patch.object(client, "_execute_content_generation", new=AsyncMock(return_value=mock_response)):
        data, latency, status, error = await client.generate_structured_json("Generate strategy")
        assert status == "error"
        assert "Malformed JSON" in error

def test_lead_scoring_ai_response_validation():
    from pydantic import ValidationError
    from app.schemas.schemas import LeadScoringAIResponse, LeadScoreExplanation, ScoreFactorBreakdown

    valid_explanation = LeadScoreExplanation(
        industry_alignment=ScoreFactorBreakdown(score=30, max=30, reason="Excellent match"),
        decision_maker_authority=ScoreFactorBreakdown(score=25, max=25, reason="C-Level"),
        geographic_match=ScoreFactorBreakdown(score=20, max=20, reason="Target region"),
        company_size_fit=ScoreFactorBreakdown(score=10, max=15, reason="Mid-market"),
        source_intent=ScoreFactorBreakdown(score=10, max=10, reason="Inbound demo"),
        key_positives=["Strong ICP alignment"],
        risk_factors=[]
    )

    # Valid model instance
    valid_payload = LeadScoringAIResponse(
        score=95,
        qualification_category="High Priority",
        business_fit_summary="Ideal client profile match.",
        suggested_next_action="Schedule discovery call immediately.",
        score_explanation=valid_explanation
    )
    assert valid_payload.score == 95

    # 1. Inconsistent Category: Score 95 with "Low Priority" -> ValidationError
    with pytest.raises(ValidationError):
        LeadScoringAIResponse(
            score=95,
            qualification_category="Low Priority",
            business_fit_summary="Fit",
            suggested_next_action="Action",
            score_explanation=valid_explanation
        )

    # 2. Score 35 with "High Priority" -> ValidationError
    with pytest.raises(ValidationError):
        LeadScoringAIResponse(
            score=35,
            qualification_category="High Priority",
            business_fit_summary="Fit",
            suggested_next_action="Action",
            score_explanation=valid_explanation
        )

    # 3. Factor score exceeding max -> ValidationError
    with pytest.raises(ValidationError):
        ScoreFactorBreakdown(score=35, max=30, reason="Exceeds max bound")

def test_prompt_logging_sanitizes_system_instructions_and_errors():
    from tests.conftest import TestingSessionLocal
    from app.services.prompt_service import log_prompt_execution
    db = TestingSessionLocal()
    try:
        execution = log_prompt_execution(
            db=db,
            feature_name="strategy_generator",
            prompt_version="v3.0",
            system_instruction="Contact admin at admin@growthpilot.internal with key AIzaSyTestKeySecret1234567890",
            prompt_rendered="Evaluate lead at user@target.org",
            user_inputs={"email": "client@enterprise.com"},
            model_used="gemini-2.5-flash",
            execution_status="error",
            latency_ms=120,
            generated_output={},
            error_message="Call failed with token AIzaSySecretKey0987654321 and phone +1 (555) 000-1111"
        )
        assert "[REDACTED_SECRET]" in execution.system_instruction_used
        assert "admin@growthpilot.internal" not in execution.system_instruction_used
        assert "[REDACTED_SECRET]" in execution.error_message
        assert "(555) 000-1111" not in execution.error_message
        assert "[REDACTED_PHONE]" in execution.error_message
    finally:
        db.close()

def test_data_retention_policy_cleans_old_prompt_executions():
    from datetime import datetime, timedelta
    from tests.conftest import TestingSessionLocal
    from app.models.models import PromptExecution
    from app.services.prompt_service import clean_old_prompt_executions
    db = TestingSessionLocal()
    try:
        # Create an old record
        old_record = PromptExecution(
            feature_name="old_feature",
            prompt_version="v1.0",
            system_instruction_used="old",
            prompt_rendered="old prompt",
            user_inputs={},
            model_used="demo",
            execution_status="success",
            latency_ms=10,
            generated_output={},
            created_at=datetime.utcnow() - timedelta(days=45)
        )
        # Create a fresh record
        new_record = PromptExecution(
            feature_name="new_feature",
            prompt_version="v3.0",
            system_instruction_used="new",
            prompt_rendered="new prompt",
            user_inputs={},
            model_used="demo",
            execution_status="success",
            latency_ms=10,
            generated_output={},
            created_at=datetime.utcnow()
        )
        db.add_all([old_record, new_record])
        db.commit()

        deleted_count = clean_old_prompt_executions(db, days=30)
        assert deleted_count >= 1

        # Verify old record is gone, new record remains
        remaining_old = db.query(PromptExecution).filter(PromptExecution.feature_name == "old_feature").first()
        assert remaining_old is None
        remaining_new = db.query(PromptExecution).filter(PromptExecution.feature_name == "new_feature").first()
        assert remaining_new is not None
    finally:
        db.close()

