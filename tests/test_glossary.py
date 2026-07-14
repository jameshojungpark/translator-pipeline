import pytest

from server.glossary import LANGUAGES, SOURCE_LANGUAGES, build_translation_instruction


@pytest.mark.parametrize("lang", sorted(LANGUAGES))
def test_instruction_contains_every_glossary_pair(lang: str) -> None:
    instruction = build_translation_instruction(lang)
    for english, target in LANGUAGES[lang].glossary.items():
        assert english in instruction
        assert target in instruction


@pytest.mark.parametrize("lang", sorted(LANGUAGES))
@pytest.mark.parametrize("source", sorted(SOURCE_LANGUAGES))
def test_instruction_contains_style_rules(lang: str, source: str) -> None:
    instruction = build_translation_instruction(lang, source)
    source_name = SOURCE_LANGUAGES[source]
    for rule in LANGUAGES[lang].style_rules:
        assert rule.format(source=source_name) in instruction


def test_default_instruction_is_korean_from_english() -> None:
    assert build_translation_instruction() == build_translation_instruction("ko", "en")


def test_instructions_differ_per_language() -> None:
    assert build_translation_instruction("ko") != build_translation_instruction("zh")


def test_instructions_differ_per_source_language() -> None:
    assert build_translation_instruction("zh", "en") != build_translation_instruction(
        "zh", "fr"
    )


def test_source_language_names_the_input_language() -> None:
    instruction = build_translation_instruction("ko", "fr")
    assert "French" in instruction
    assert "{source}" not in instruction


def test_non_english_source_explains_glossary_keys() -> None:
    instruction = build_translation_instruction("ko", "fr")
    assert "Each entry names a concept in English" in instruction


def test_every_language_defines_the_same_glossary_terms() -> None:
    expected = set(LANGUAGES["ko"].glossary)
    for config in LANGUAGES.values():
        assert set(config.glossary) == expected


def test_every_source_language_is_also_a_target() -> None:
    # Passthrough relies on the speaker's language being a selectable target.
    assert set(SOURCE_LANGUAGES) <= set(LANGUAGES)
