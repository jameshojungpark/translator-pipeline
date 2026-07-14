"""Deepgram live STT wrapper: raw 16 kHz PCM in, transcript callbacks out."""

import logging
from typing import Any, Awaitable, Callable

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveTranscriptionEvents,
)

logger = logging.getLogger(__name__)

TranscriptHandler = Callable[[str, bool], Awaitable[None]]  # (text, is_final)

# Deepgram (model, language) per speaker language. English gets nova-3;
# French and Korean are not available on nova-3 monolingual, so they run
# on nova-2, which supports both for live transcription.
INPUT_STT: dict[str, tuple[str, str]] = {
    "en": ("nova-3", "en-US"),
    "fr": ("nova-2", "fr"),
    "ko": ("nova-2", "ko"),
}


def live_options(input_lang: str) -> LiveOptions:
    """Deepgram live options for one speaker language (INPUT_STT key)."""
    model, language = INPUT_STT[input_lang]
    return LiveOptions(
        model=model,
        language=language,
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        smart_format=True,   # punctuation drives sentence detection
        interim_results=True,
    )


class DeepgramTranscriber:
    """One live Deepgram connection for one host session."""

    def __init__(
        self,
        api_key: str,
        on_transcript: TranscriptHandler,
        input_lang: str = "en",
    ) -> None:
        client = DeepgramClient(
            api_key,
            DeepgramClientOptions(options={"keepalive": "true"}),
        )
        self._options = live_options(input_lang)
        self._connection = client.listen.asyncwebsocket.v("1")
        self._on_transcript = on_transcript
        self._connection.on(LiveTranscriptionEvents.Transcript, self._handle_transcript)
        self._connection.on(LiveTranscriptionEvents.Error, self._handle_error)

    async def _handle_transcript(self, _client: Any, result: Any, **_kwargs: Any) -> None:
        text: str = result.channel.alternatives[0].transcript
        if text.strip():
            await self._on_transcript(text, bool(result.is_final))

    async def _handle_error(self, _client: Any, error: Any, **_kwargs: Any) -> None:
        logger.error("deepgram error: %s", error)

    async def start(self) -> None:
        started = await self._connection.start(self._options)
        if not started:
            raise RuntimeError("failed to open Deepgram live connection")
        logger.info("deepgram connection opened")

    async def send(self, audio_chunk: bytes) -> None:
        await self._connection.send(audio_chunk)

    async def stop(self) -> None:
        await self._connection.finish()
        logger.info("deepgram connection closed")
