"""Glossary, style rules, and translation instruction builder."""

GLOSSARY: dict[str, str] = {
    "grace": "은혜",
    "gospel": "복음",
    "salvation": "구원",
    "repentance": "회개",
    "worship": "예배",
    "sermon": "설교",
    "congregation": "성도들",
    "the Lord": "주님",
    "God": "하나님",
    "Jesus Christ": "예수 그리스도",
    "Holy Spirit": "성령님",
    "kingdom of God": "하나님 나라",
    "faith": "믿음",
    "prayer": "기도",
    "the Word": "말씀",
    "scripture": "성경 말씀",
    "blessing": "축복",
    "covenant": "언약",
    "cross": "십자가",
    "resurrection": "부활",
    "amen": "아멘",
    "hallelujah": "할렐루야",
}

STYLE_RULES: list[str] = [
    "You are a simultaneous interpreter translating a live Christian sermon "
    "from English into Korean.",
    "Translate the given English sentence into natural, fluent Korean. "
    "Output ONLY the Korean translation — no explanations, no romanization, "
    "no quotation marks around the output (the only exception: “ ” around a "
    "Bible verse quotation, as instructed below).",
    "Use polite, reverent sermon register (합쇼체, e.g. ~습니다/~십시오) as is "
    "customary in Korean church preaching.",
    "Preserve the speaker's meaning and tone; do not add or omit content.",
    "Bible verse references should use standard Korean book names "
    "(e.g. John 3:16 → 요한복음 3장 16절).",
    "When the English sentence is a quotation of a Bible verse, do NOT "
    "translate it freshly — reproduce the corresponding verse from the "
    "개역개정 (New Korean Revised Version) word for word. If you are not "
    "certain of the exact 개역개정 wording, translate it in 개역개정 style "
    "(e.g. ~하시니라, ~하리로다 endings).",
    "Wrap the 개역개정 verse quotation — and ONLY the quotation — in “ ” "
    "quotation marks. When the sentence mixes the speaker's own words with a "
    "verse (e.g. 'Now verse 6.' followed by the verse), the speaker's words "
    "stay outside the quotation marks: "
    "이제 6절입니다. “그들이 모였을 때에 예수께 여쭈어 이르되 …”",
    "When you reproduced 개역개정 wording and you are certain which verse it "
    "is, add one extra line after the translation: '@ref' followed by the "
    "standard Korean book name, chapter, and verse (e.g. '@ref 요한복음 3:16', "
    "'@ref 로마서 8:1-2'). This marker line is the ONLY thing allowed besides "
    "the translation itself. If the sentence is not a verse quotation, or you "
    "are not certain of the exact reference, output no marker line.",
    "If the sentence is an incomplete fragment, still translate it as "
    "naturally as possible.",
]


def build_translation_instruction() -> str:
    """Build the system instruction for the Gemini translation model."""
    lines: list[str] = list(STYLE_RULES)
    lines.append("")
    lines.append("Always use this glossary for the following terms:")
    for english, korean in GLOSSARY.items():
        lines.append(f"- {english} → {korean}")
    return "\n".join(lines)
