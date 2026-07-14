"""Per-language TTS voice/speed resolution from env and LanguageConfig."""

import pytest

from server.glossary import LANGUAGES
from server.main import _tts_speed, _tts_voice


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("TTS_VOICE", "TTS_VOICE_KO", "TTS_VOICE_ZH",
                "TTS_SPEED", "TTS_SPEED_KO", "TTS_SPEED_ZH"):
        monkeypatch.delenv(var, raising=False)


def test_voice_defaults_come_from_language_config() -> None:
    assert _tts_voice("ko") == LANGUAGES["ko"].tts_voice
    assert _tts_voice("zh") == LANGUAGES["zh"].tts_voice


def test_voice_per_language_env_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_VOICE_ZH", "cmn-CN-Chirp3-HD-Kore")
    assert _tts_voice("zh") == "cmn-CN-Chirp3-HD-Kore"
    assert _tts_voice("ko") == LANGUAGES["ko"].tts_voice


def test_voice_legacy_env_applies_to_korean_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TTS_VOICE", "ko-KR-Chirp3-HD-Charon")
    assert _tts_voice("ko") == "ko-KR-Chirp3-HD-Charon"
    assert _tts_voice("zh") == LANGUAGES["zh"].tts_voice


def test_text_only_language_has_no_voice() -> None:
    assert _tts_voice("fa") is None


def test_text_only_language_env_override_enables_a_voice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TTS_VOICE_FA", "some-future-fa-voice")
    assert _tts_voice("fa") == "some-future-fa-voice"


def test_speed_defaults_come_from_language_config() -> None:
    assert _tts_speed("ko") == LANGUAGES["ko"].tts_speed
    assert _tts_speed("zh") == LANGUAGES["zh"].tts_speed


def test_speed_shared_env_applies_to_all_languages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TTS_SPEED", "1.3")
    assert _tts_speed("ko") == 1.3
    assert _tts_speed("zh") == 1.3


def test_speed_per_language_env_beats_shared(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TTS_SPEED", "1.3")
    monkeypatch.setenv("TTS_SPEED_ZH", "1.0")
    assert _tts_speed("zh") == 1.0
    assert _tts_speed("ko") == 1.3
