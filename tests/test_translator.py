from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import errors

from server.translator import Translator, _retry_delay_seconds


def make_429(message: str = "Quota exceeded. Please retry in 2.5s.") -> errors.APIError:
    return errors.APIError(
        429, {"error": {"code": 429, "message": message, "status": "RESOURCE_EXHAUSTED"}}
    )


def test_retry_delay_parsed_from_error() -> None:
    assert _retry_delay_seconds(make_429()) == 2.5


def test_retry_delay_absent() -> None:
    assert _retry_delay_seconds(make_429("Quota exceeded.")) is None


class FakeModels:
    """Fails with 429 a set number of times, then succeeds."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    async def generate_content(self, **_kwargs: Any) -> Any:
        self.calls += 1
        if self.calls <= self.failures:
            raise make_429("Please retry in 0.01s.")
        return SimpleNamespace(text="은혜")


def make_translator(fake: FakeModels) -> Translator:
    translator = Translator.__new__(Translator)
    translator._model = "gemini-3.5-flash"
    translator._config = None
    translator._client = SimpleNamespace(aio=SimpleNamespace(models=fake))
    return translator


@pytest.mark.asyncio
async def test_translate_retries_past_429() -> None:
    fake = FakeModels(failures=2)
    translator = make_translator(fake)
    assert await translator.translate("Grace.") == "은혜"
    assert fake.calls == 3


@pytest.mark.asyncio
async def test_translate_gives_up_after_max_attempts() -> None:
    fake = FakeModels(failures=99)
    translator = make_translator(fake)
    with pytest.raises(errors.APIError):
        await translator.translate("Grace.")
    assert fake.calls == 4
