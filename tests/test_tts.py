import base64
from typing import Any

import pytest

from server.tts import Synthesizer, SynthesisError, _strip_wav_header

PCM = b"\x01\x02\x03\x04"


def make_wav(pcm: bytes) -> bytes:
    fmt = b"fmt " + (16).to_bytes(4, "little") + b"\x00" * 16
    data = b"data" + len(pcm).to_bytes(4, "little") + pcm
    body = b"WAVE" + fmt + data
    return b"RIFF" + len(body).to_bytes(4, "little") + body


class FakeResponse:
    def __init__(self, status_code: int, audio: bytes | None = None) -> None:
        self.status_code = status_code
        # "retry in …" keeps the shared retry backoff near-zero in tests
        self.text = f"http {status_code}, retry in 0.01s"
        self._audio = audio

    def json(self) -> dict[str, Any]:
        assert self._audio is not None
        return {"audioContent": base64.b64encode(self._audio).decode("ascii")}


class FakeHttpClient:
    """Returns queued responses; records the last request payload."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls = 0
        self.last_json: dict[str, Any] | None = None

    async def post(self, _url: str, params: Any = None, json: Any = None) -> FakeResponse:
        self.calls += 1
        self.last_json = json
        return self.responses.pop(0)


def make_synthesizer(fake: FakeHttpClient, speed: float = 1.2) -> Synthesizer:
    synthesizer = Synthesizer.__new__(Synthesizer)
    synthesizer._api_key = "test-key"
    synthesizer._voice = "ko-KR-Neural2-C"
    synthesizer._language = "ko-KR"
    synthesizer._speed = speed
    synthesizer._client = fake
    return synthesizer


def test_strip_wav_header() -> None:
    assert _strip_wav_header(make_wav(PCM)) == PCM


def test_strip_wav_header_passes_raw_pcm_through() -> None:
    assert _strip_wav_header(PCM) == PCM


def test_strip_wav_header_rejects_dataless_wav() -> None:
    with pytest.raises(ValueError):
        _strip_wav_header(b"RIFF\x04\x00\x00\x00WAVE")


@pytest.mark.asyncio
async def test_synthesize_returns_pcm_and_sends_config() -> None:
    fake = FakeHttpClient([FakeResponse(200, audio=make_wav(PCM))])
    synthesizer = make_synthesizer(fake, speed=1.3)
    assert await synthesizer.synthesize("은혜.") == PCM
    assert fake.last_json is not None
    assert fake.last_json["input"] == {"text": "은혜."}
    assert fake.last_json["voice"] == {"languageCode": "ko-KR", "name": "ko-KR-Neural2-C"}
    assert fake.last_json["audioConfig"]["speakingRate"] == 1.3


@pytest.mark.asyncio
async def test_synthesize_retries_past_429() -> None:
    fake = FakeHttpClient(
        [FakeResponse(429), FakeResponse(429), FakeResponse(200, audio=make_wav(PCM))]
    )
    synthesizer = make_synthesizer(fake)
    assert await synthesizer.synthesize("은혜.") == PCM
    assert fake.calls == 3


@pytest.mark.asyncio
async def test_synthesize_gives_up_after_max_attempts() -> None:
    fake = FakeHttpClient([FakeResponse(429)] * 99)
    synthesizer = make_synthesizer(fake)
    with pytest.raises(SynthesisError):
        await synthesizer.synthesize("은혜.")
    assert fake.calls == 4


@pytest.mark.asyncio
async def test_synthesize_does_not_retry_client_errors() -> None:
    fake = FakeHttpClient([FakeResponse(400)])
    synthesizer = make_synthesizer(fake)
    with pytest.raises(SynthesisError):
        await synthesizer.synthesize("은혜.")
    assert fake.calls == 1
