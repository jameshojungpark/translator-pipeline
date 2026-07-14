"""English → target-language sentence translation via Gemini Flash Lite (text only)."""

import logging
import re

from typing import NamedTuple

from google import genai
from google.genai import types

from server.glossary import build_translation_instruction
from server.retry import call_with_retry

logger = logging.getLogger(__name__)

MODEL = "gemini-3.1-flash-lite"

# Marker the model appends when it reproduced a Bible verse (개역개정 / 和合本),
# e.g. "@ref 요한복음 3:16". Marker lines never belong in the spoken/displayed text;
# one only counts as a reference if it contains a digit (chapter/verse), so
# junk like "@ref none" is discarded entirely.
_MARKER_PATTERN = re.compile(r"^@ref\b\s*(.*)$")


class Translation(NamedTuple):
    text: str
    reference: str | None = None


def parse_translation(raw: str) -> Translation:
    """Split a model response into the translated text and an optional verse ref.

    The model is instructed to wrap the verse portion of the text in “ ”
    itself (a sentence often mixes the speaker's own words with the verse).
    If it annotated a reference but forgot the quotes, the whole text is the
    verse as far as we know, so it gets wrapped as a fallback.
    """
    text_lines: list[str] = []
    reference: str | None = None
    for line in raw.strip().splitlines():
        match = _MARKER_PATTERN.match(line.strip())
        if match:
            candidate = match.group(1).strip()
            if any(ch.isdigit() for ch in candidate):
                reference = candidate
        else:
            text_lines.append(line)
    text = "\n".join(text_lines).strip()
    if reference is not None and text and not any(q in text for q in "“”\""):
        text = f"“{text}”"
    return Translation(text, reference)


class Translator:
    def __init__(self, api_key: str, lang: str = "ko", model: str = MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self.lang = lang
        self._config = types.GenerateContentConfig(
            system_instruction=build_translation_instruction(lang),
            temperature=0.2,
            # Translation is latency-sensitive; don't spend time thinking.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            # No tools are used; also silences the per-call "AFC is enabled" log.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

    async def translate(self, sentence: str) -> Translation:
        """Translate one sentence, retrying on rate limits and transient 5xx."""

        async def call() -> Translation:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=sentence,
                config=self._config,
            )
            return parse_translation(response.text or "")

        return await call_with_retry(call)
