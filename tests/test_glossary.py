import pytest

from server.glossary import LANGUAGES, build_translation_instruction


@pytest.mark.parametrize("lang", sorted(LANGUAGES))
def test_instruction_contains_every_glossary_pair(lang: str) -> None:
    instruction = build_translation_instruction(lang)
    for english, target in LANGUAGES[lang].glossary.items():
        assert english in instruction
        assert target in instruction


@pytest.mark.parametrize("lang", sorted(LANGUAGES))
def test_instruction_contains_style_rules(lang: str) -> None:
    instruction = build_translation_instruction(lang)
    for rule in LANGUAGES[lang].style_rules:
        assert rule in instruction


def test_default_instruction_is_korean() -> None:
    assert build_translation_instruction() == build_translation_instruction("ko")


def test_instructions_differ_per_language() -> None:
    assert build_translation_instruction("ko") != build_translation_instruction("zh")


def test_every_language_defines_the_same_glossary_terms() -> None:
    expected = set(LANGUAGES["ko"].glossary)
    for config in LANGUAGES.values():
        assert set(config.glossary) == expected
