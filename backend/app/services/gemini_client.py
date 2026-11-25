import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError
from app.config import settings

logger = logging.getLogger("growthpilot.gemini")

def categorize_gemini_error(exc: Exception) -> str:
    """Categorizes Gemini SDK and network exceptions into clear, actionable error messages."""
    err_str = str(exc)
    err_lower = err_str.lower()

    if "401" in err_str or "unauthenticated" in err_lower or "api_key_invalid" in err_lower or "permission_denied" in err_lower:
        return "Authentication failed: Invalid or expired Gemini API key."
    if "429" in err_str or "resource_exhausted" in err_lower or "quota" in err_lower or "rate limit" in err_lower:
        return "Rate limit or quota exceeded (429). Please retry after a brief cooldown."
    if "503" in err_str or "500" in err_str or "unavailable" in err_lower or "internal" in err_lower:
        return "Gemini upstream service temporarily unavailable (500/503). Please retry shortly."
    if "connection" in err_lower or "network" in err_lower or "dns" in err_lower:
        return f"Network connectivity error contacting Google GenAI: {err_str}"
    return f"Gemini API request failed: {err_str}"

class GeminiClient:
    def __init__(self):
        # Read from settings or environment; session updates do not persist to disk
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key and not settings.DEMO_MODE:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI client with model {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI SDK client: {e}. Running in simulation/demo mode.")
                self._client = None
        else:
            self._client = None

    def update_key(self, api_key: str, model_name: Optional[str] = None):
        """
        Updates API key in backend session memory only.
        Never written to disk, .env, or localStorage. Cleared on restart.
        """
        self.api_key = api_key.strip()
        if model_name:
            self.model_name = model_name.strip()
        self._init_client()

    def is_configured(self) -> bool:
        """True only if an API key is present and SDK client is initialized."""
        return bool(self._client and self.api_key and not settings.DEMO_MODE)

    async def _execute_content_generation(self, contents: str, config: Any = None) -> Any:
        """
        Executes content generation using native async client.aio when available,
        falling back to thread-offloaded synchronous generation.
        """
        if hasattr(self._client, "aio") and hasattr(self._client.aio, "models"):
            if config is not None:
                return await self._client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
            else:
                return await self._client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
        else:
            def _sync():
                if config is not None:
                    return self._client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=config
                    )
                else:
                    return self._client.models.generate_content(
                        model=self.model_name,
                        contents=contents
                    )
            return await asyncio.to_thread(_sync)

    async def test_connection(self) -> Dict[str, Any]:
        """
        Safe health check without leaking API keys.
        Returns status: 'connected' | 'unconfigured' | 'error'.
        """
        if not self.api_key:
            return {
                "status": "unconfigured",
                "message": "No GEMINI_API_KEY configured. Running in Demo / Simulation Mode.",
                "model": self.model_name,
                "configured": False,
                "latency_ms": 0
            }

        if not self._client:
            return {
                "status": "error",
                "message": "SDK client initialization failed. Check API key format.",
                "model": self.model_name,
                "configured": False,
                "latency_ms": 0
            }

        try:
            start_time = time.time()
            response = await asyncio.wait_for(
                self._execute_content_generation(
                    contents="Health check. Reply with strictly JSON: {\"status\": \"ok\"}"
                ),
                timeout=15.0
            )
            latency = int((time.time() - start_time) * 1000)

            if response and response.text:
                return {
                    "status": "connected",
                    "message": f"Successfully connected to Google Gemini ({self.model_name}).",
                    "model": self.model_name,
                    "configured": True,
                    "latency_ms": latency
                }
            else:
                return {
                    "status": "error",
                    "message": "Received empty response from Gemini API.",
                    "model": self.model_name,
                    "configured": False,
                    "latency_ms": latency
                }
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Connection test timed out after 15 seconds.",
                "model": self.model_name,
                "configured": False,
                "latency_ms": 15000
            }
        except Exception as e:
            categorized_err = categorize_gemini_error(e)
            logger.error(f"Gemini API test connection failed: {categorized_err}")
            return {
                "status": "error",
                "message": categorized_err,
                "model": self.model_name,
                "configured": False,
                "latency_ms": 0
            }

    async def generate_structured_json(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.3,
        response_schema: Optional[Type[BaseModel]] = None,
        timeout_seconds: float = 30.0
    ) -> Tuple[Dict[str, Any], int, str, Optional[str]]:
        """
        Executes structured JSON prompt via Gemini API with async execution, timeout,
        and optional Pydantic schema validation.
        Returns: (parsed_json, latency_ms, status ['success' | 'fallback_demo' | 'error'], error_message)
        """
        start_time = time.time()

        # State 1: Unconfigured / Demo Mode
        if not self.is_configured():
            latency = int((time.time() - start_time) * 1000)
            return {}, latency, "fallback_demo", "Gemini API key is not configured. Running in Demo Simulation Mode."

        # State 2 & 3: Attempt Live AI Execution
        try:
            from google.genai import types

            config_args = {
                "temperature": temperature,
                "response_mime_type": "application/json",
            }
            if system_instruction:
                config_args["system_instruction"] = system_instruction

            config = types.GenerateContentConfig(**config_args)

            # Native async execution with strict timeout
            response = await asyncio.wait_for(
                self._execute_content_generation(contents=prompt, config=config),
                timeout=timeout_seconds
            )
            latency = int((time.time() - start_time) * 1000)

            if not response or not response.text:
                return {}, latency, "error", "Gemini API returned an empty response."

            raw_text = response.text.strip()
            # Clean possible markdown fence wrapping if returned despite json mime type
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            # Validate against Pydantic schema if provided
            if response_schema:
                try:
                    validated = response_schema.model_validate(parsed)
                    parsed = validated.model_dump()
                except (ValidationError, ValueError) as ve:
                    latency = int((time.time() - start_time) * 1000)
                    logger.error(f"Gemini output schema validation failed: {ve}")
                    return {}, latency, "error", f"Gemini response failed strict schema validation: {str(ve)}"

            return parsed, latency, "success", None

        except asyncio.TimeoutError:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"Gemini API request timed out after {timeout_seconds}s")
            return {}, latency, "error", f"Gemini API request timed out after {timeout_seconds} seconds."
        except json.JSONDecodeError as jde:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"Malformed JSON returned by Gemini: {jde}")
            return {}, latency, "error", f"Malformed JSON from Gemini model: {str(jde)}"
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            categorized = categorize_gemini_error(e)
            logger.error(f"Gemini API call failed: {categorized}")
            return {}, latency, "error", categorized

gemini_client = GeminiClient()
