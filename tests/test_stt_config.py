"""Deepgram live-option selection per speaker language."""

from server.glossary import SOURCE_LANGUAGES
from server.stt import INPUT_STT, live_options


def test_every_source_language_has_stt_options() -> None:
    assert set(INPUT_STT) == set(SOURCE_LANGUAGES)
    for code in SOURCE_LANGUAGES:
        options = live_options(code)
        assert options.encoding == "linear16"
        assert options.sample_rate == 16000


def test_english_stays_on_nova3() -> None:
    options = live_options("en")
    assert options.model == "nova-3"
    assert options.language == "en-US"


def test_french_and_korean_use_a_model_that_supports_them() -> None:
    assert live_options("fr").language == "fr"
    assert live_options("ko").language == "ko"
