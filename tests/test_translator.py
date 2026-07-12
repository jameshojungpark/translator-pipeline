from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import errors

from server.retry import retry_delay_seconds
from server.translator import Translation, Translator, parse_translation


def make_429(message: str = "Quota exceeded. Please retry in 2.5s.") -> errors.APIError:
    return errors.APIError(
        429, {"error": {"code": 429, "message": message, "status": "RESOURCE_EXHAUSTED"}}
    )


def test_retry_delay_parsed_from_error() -> None:
    assert retry_delay_seconds(make_429()) == 2.5


def test_retry_delay_absent() -> None:
    assert retry_delay_seconds(make_429("Quota exceeded.")) is None


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


def test_parse_translation_plain() -> None:
    assert parse_translation("은혜입니다.") == Translation("은혜입니다.", None)


def test_parse_translation_mixed_sentence_keeps_model_quoting() -> None:
    raw = "이제 6절입니다. “그들이 모였을 때에 예수께 여쭈어 이르되 …”\n@ref 사도행전 1:6"
    assert parse_translation(raw) == Translation(
        "이제 6절입니다. “그들이 모였을 때에 예수께 여쭈어 이르되 …”", "사도행전 1:6"
    )


def test_parse_translation_wraps_unquoted_verse() -> None:
    raw = "하나님이 세상을 이처럼 사랑하사...\n@ref 요한복음 3:16"
    assert parse_translation(raw) == Translation(
        "“하나님이 세상을 이처럼 사랑하사...”", "요한복음 3:16"
    )


def test_parse_translation_reference_range_and_whitespace() -> None:
    raw = "  결코 정죄함이 없나니\n  @ref 로마서 8:1-2  \n"
    parsed = parse_translation(raw)
    assert parsed.text == "“결코 정죄함이 없나니”"
    assert parsed.reference == "로마서 8:1-2"


def test_parse_translation_rejects_marker_without_digits() -> None:
    parsed = parse_translation("은혜입니다.\n@ref none")
    assert parsed == Translation("은혜입니다.", None)


@pytest.mark.asyncio
async def test_translate_retries_past_429() -> None:
    fake = FakeModels(failures=2)
    translator = make_translator(fake)
    assert await translator.translate("Grace.") == Translation("은혜", None)
    assert fake.calls == 3


@pytest.mark.asyncio
async def test_translate_gives_up_after_max_attempts() -> None:
    fake = FakeModels(failures=99)
    translator = make_translator(fake)
    with pytest.raises(errors.APIError):
        await translator.translate("Grace.")
    assert fake.calls == 4
