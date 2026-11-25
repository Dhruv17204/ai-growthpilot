import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from app.config import settings

logger = logging.getLogger("growthpilot.gemini")

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
            
            def _sync_ping():
                return self._client.models.generate_content(
                    model=self.model_name,
                    contents="Health check. Reply with strictly JSON: {\"status\": \"ok\"}"
                )

            # Enforce 15-second timeout on connectivity test
            response = await asyncio.wait_for(asyncio.to_thread(_sync_ping), timeout=15.0)
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
            logger.error(f"Gemini API test connection failed: {e}")
            return {
                "status": "error",
                "message": f"Gemini connection failed: {str(e)}",
                "model": self.model_name,
                "configured": False,
                "latency_ms": 0
            }

    async def generate_structured_json(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.3,
        response_schema: Optional[Any] = None,
        timeout_seconds: float = 45.0
    ) -> Tuple[Dict[str, Any], int, str, Optional[str]]:
        """
        Executes structured JSON prompt via Gemini API with async offloading and timeout.
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
            if response_schema:
                config_args["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_args)

            def _sync_generate():
                return self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )

            # Execute synchronously in worker thread with timeout to avoid blocking FastAPI event loop
            response = await asyncio.wait_for(
                asyncio.to_thread(_sync_generate),
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
            logger.error(f"Gemini API call failed: {e}")
            return {}, latency, "error", str(e)

gemini_client = GeminiClient()
