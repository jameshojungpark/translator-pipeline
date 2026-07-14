"""Korean sentence → speech via Google Cloud Text-to-Speech (REST).

Output audio is raw little-endian 16-bit PCM, 24 kHz mono — clients build an
AudioBuffer from it directly. Cloud TTS wraps LINEAR16 output in a WAV
container, so the header is stripped here before the audio leaves the server.
"""

import base64
import logging
import httpx

from server.retry import call_with_retry

logger = logging.getLogger(__name__)

ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
VOICE = "ko-KR-Neural2-C"
SPEED = 1.1  # speakingRate: 1.0 = natural; faster keeps audio near-live
OUTPUT_SAMPLE_RATE = 24_000

class SynthesisError(Exception):
    """Non-2xx from Cloud TTS; ``code`` drives the shared retry policy."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Cloud TTS HTTP {code}: {message}")
        self.code = code


def _strip_wav_header(data: bytes) -> bytes:
    """Return the raw PCM payload of a RIFF/WAV byte string."""
    if not data.startswith(b"RIFF"):
        return data  # already raw
    offset = 12  # past RIFF header to the first chunk
    while offset + 8 <= len(data):
        chunk_id = data[offset : offset + 4]
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        if chunk_id == b"data":
            return data[offset + 8 : offset + 8 + size]
        offset += 8 + size + (size & 1)  # chunks are word-aligned
    raise ValueError("WAV response has no data chunk")


class Synthesizer:
    def __init__(self, api_key: str, voice: str = VOICE, speed: float = SPEED) -> None:
        self._api_key = api_key
        self._voice = voice
        self._language = "-".join(voice.split("-")[:2])  # ko-KR-Chirp3-HD-… → ko-KR
        self._speed = speed
        self._client = httpx.AsyncClient(timeout=30.0)

    async def synthesize(self, text: str) -> bytes:
        """Synthesize one sentence, retrying on rate limits and transient 5xx."""
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": self._language, "name": self._voice},
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": OUTPUT_SAMPLE_RATE,
                "speakingRate": self._speed,
            },
        }

        async def call() -> bytes:
            response = await self._client.post(
                ENDPOINT, params={"key": self._api_key}, json=payload
            )
            if response.status_code != 200:
                raise SynthesisError(response.status_code, response.text)
            audio = base64.b64decode(response.json()["audioContent"])
            return _strip_wav_header(audio)

        return await call_with_retry(call)
