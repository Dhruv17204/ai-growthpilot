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
