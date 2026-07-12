"""Shared retry policy for API calls (rate limits and transient 5xx).

Retries any exception exposing an HTTP status in a ``code`` attribute —
google-genai's APIError does natively; other callers raise their own such
errors (see server/tts.py).
"""

import asyncio
import logging
import re

from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 4
# 429: rate limit; 500/503/504: transient server-side failures ("high demand").
RETRYABLE_CODES = {429, 500, 503, 504}

T = TypeVar("T")


def retry_delay_seconds(error: Exception) -> float | None:
    """Pull the server-suggested retry delay out of a 429, if present."""
    match = re.search(r"retry in ([0-9.]+)\s*s", str(error), re.IGNORECASE)
    return float(match.group(1)) if match else None


async def call_with_retry(call: Callable[[], Awaitable[T]]) -> T:
    """Run an async API call, retrying on rate limits and transient 5xx."""
    backoff = 1.0
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return await call()
        except Exception as error:
            if getattr(error, "code", None) not in RETRYABLE_CODES or attempt == MAX_ATTEMPTS:
                raise
            wait = retry_delay_seconds(error) or backoff
            logger.warning(
                "retryable API error %s (attempt %d/%d), retrying in %.1fs",
                error.code, attempt, MAX_ATTEMPTS, wait,
            )
            await asyncio.sleep(wait)
            backoff *= 2
    raise RuntimeError("unreachable")
