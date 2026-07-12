"""English → Korean sentence translation via Gemini Flash Lite (text only)."""

import asyncio
import logging
import re

from google import genai
from google.genai import errors, types

from server.glossary import build_translation_instruction

logger = logging.getLogger(__name__)

MODEL = "gemini-3.1-flash-lite"
MAX_ATTEMPTS = 4
# 429: rate limit; 500/503/504: transient server-side failures ("high demand").
RETRYABLE_CODES = {429, 500, 503, 504}


def _retry_delay_seconds(error: errors.APIError) -> float | None:
    """Pull the server-suggested retry delay out of a 429, if present."""
    match = re.search(r"retry in ([0-9.]+)\s*s", str(error), re.IGNORECASE)
    return float(match.group(1)) if match else None


class Translator:
    def __init__(self, api_key: str, model: str = MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._config = types.GenerateContentConfig(
            system_instruction=build_translation_instruction(),
            temperature=0.2,
            # Translation is latency-sensitive; don't spend time thinking.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            # No tools are used; also silences the per-call "AFC is enabled" log.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

    async def translate(self, sentence: str) -> str:
        """Translate one sentence, retrying on rate limits and transient 5xx."""
        backoff = 1.0
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=sentence,
                    config=self._config,
                )
                return (response.text or "").strip()
            except errors.APIError as error:
                if error.code not in RETRYABLE_CODES or attempt == MAX_ATTEMPTS:
                    raise
                wait = _retry_delay_seconds(error) or backoff
                logger.warning(
                    "retryable API error %s (attempt %d/%d), retrying in %.1fs",
                    error.code, attempt, MAX_ATTEMPTS, wait,
                )
                await asyncio.sleep(wait)
                backoff *= 2
        raise RuntimeError("unreachable")
