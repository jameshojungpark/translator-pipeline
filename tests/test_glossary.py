from server.glossary import GLOSSARY, STYLE_RULES, build_translation_instruction


def test_instruction_contains_every_glossary_pair() -> None:
    instruction = build_translation_instruction()
    for english, korean in GLOSSARY.items():
        assert english in instruction
        assert korean in instruction


def test_instruction_contains_style_rules() -> None:
    instruction = build_translation_instruction()
    for rule in STYLE_RULES:
        assert rule in instruction
