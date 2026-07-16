"""Per-language glossaries, style rules, and translation instruction builder."""

from dataclasses import dataclass

# Languages the speaker (host) can preach in: code → English name.
# The code doubles as the target-language code skipped via passthrough
# when a viewer selects the same language the sermon is preached in.
SOURCE_LANGUAGES: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "ko": "Korean",
}


@dataclass(frozen=True)
class LanguageConfig:
    """Everything language-specific the pipeline needs for one target language.

    style_rules may reference the speaker's language with a ``{source}``
    placeholder — build_translation_instruction() fills it in with the
    session's input-language name.
    """

    code: str  # wire code used in messages and the client's ?lang= param
    name: str  # English name, for logs
    tts_voice: str | None  # default Cloud TTS voice; None = text-only (no TTS)
    tts_speed: float  # default speakingRate, 1.0 = natural (override via env)
    glossary: dict[str, str]
    style_rules: list[str]


KOREAN = LanguageConfig(
    code="ko",
    name="Korean",
    tts_voice="ko-KR-Neural2-C",
    tts_speed=1.1,
    glossary={
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
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into Korean.",
        "Translate the given {source} sentence into natural, fluent Korean. "
        "Output ONLY the Korean translation — no explanations, no romanization, "
        "no quotation marks around the output (the only exception: “ ” around a "
        "Bible verse quotation, as instructed below).",
        "Use polite, reverent sermon register (합쇼체, e.g. ~습니다/~십시오) as is "
        "customary in Korean church preaching.",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard Korean book names "
        "(e.g. John 3:16 → 요한복음 3장 16절).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
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
    ],
)

MANDARIN = LanguageConfig(
    code="zh",
    name="Mandarin Chinese",
    tts_voice="cmn-CN-Chirp3-HD-Charon",
    tts_speed=1.2,
    glossary={
        "grace": "恩典",
        "gospel": "福音",
        "salvation": "救恩",
        "repentance": "悔改",
        "worship": "敬拜",
        "sermon": "讲道",
        "congregation": "会众",
        "the Lord": "主",
        "God": "神",
        "Jesus Christ": "耶稣基督",
        "Holy Spirit": "圣灵",
        "kingdom of God": "神的国",
        "faith": "信心",
        "prayer": "祷告",
        "the Word": "神的话语",
        "scripture": "圣经",
        "blessing": "祝福",
        "covenant": "约",
        "cross": "十字架",
        "resurrection": "复活",
        "amen": "阿们",
        "hallelujah": "哈利路亚",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into Mandarin Chinese (Simplified script).",
        "Translate the given {source} sentence into natural, fluent Mandarin. "
        "Output ONLY the Chinese translation — no explanations, no pinyin, "
        "no quotation marks around the output (the only exception: “ ” around a "
        "Bible verse quotation, as instructed below).",
        "Use the solemn, reverent register customary in Chinese church preaching "
        "(庄重、恭敬的讲道语气).",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard Chinese book names "
        "(e.g. John 3:16 → 约翰福音 3 章 16 节).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "和合本 (Chinese Union Version, Simplified, 神版) word for word. If you "
        "are not certain of the exact 和合本 wording, translate it in 和合本 "
        "style.",
        "Wrap the 和合本 verse quotation — and ONLY the quotation — in “ ” "
        "quotation marks. When the sentence mixes the speaker's own words with a "
        "verse (e.g. 'Now verse 6.' followed by the verse), the speaker's words "
        "stay outside the quotation marks: "
        "现在看第六节。“他们聚集的时候，问耶稣说……”",
        "When you reproduced 和合本 wording and you are certain which verse it "
        "is, add one extra line after the translation: '@ref' followed by the "
        "standard Chinese book name, chapter, and verse (e.g. '@ref 约翰福音 3:16', "
        "'@ref 罗马书 8:1-2'). This marker line is the ONLY thing allowed besides "
        "the translation itself. If the sentence is not a verse quotation, or you "
        "are not certain of the exact reference, output no marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

CANTONESE = LanguageConfig(
    code="yue",
    name="Cantonese",
    tts_voice="yue-HK-Chirp3-HD-Charon",
    tts_speed=1.2,
    glossary={
        "grace": "恩典",
        "gospel": "福音",
        "salvation": "救恩",
        "repentance": "悔改",
        "worship": "敬拜",
        "sermon": "講道",
        "congregation": "會眾",
        "the Lord": "主",
        "God": "神",
        "Jesus Christ": "耶穌基督",
        "Holy Spirit": "聖靈",
        "kingdom of God": "神的國",
        "faith": "信心",
        "prayer": "禱告",
        "the Word": "神的話語",
        "scripture": "聖經",
        "blessing": "祝福",
        "covenant": "約",
        "cross": "十字架",
        "resurrection": "復活",
        "amen": "阿們",
        "hallelujah": "哈利路亞",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} for a Cantonese-speaking congregation (Hong Kong usage).",
        "Translate the given {source} sentence into standard written Chinese in "
        "Traditional characters (書面語), phrased so it reads naturally when "
        "spoken aloud in Cantonese. Output ONLY the Chinese translation — no "
        "explanations, no romanization, no quotation marks around the output "
        "(the only exception: “ ” around a Bible verse quotation, as instructed "
        "below).",
        "Use the solemn, reverent register customary in Hong Kong church "
        "preaching (莊重、恭敬的講道語氣).",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard Chinese book names "
        "(e.g. John 3:16 → 約翰福音 3 章 16 節).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "和合本 (Chinese Union Version, Traditional, 神版) word for word. If you "
        "are not certain of the exact 和合本 wording, translate it in 和合本 "
        "style.",
        "Wrap the 和合本 verse quotation — and ONLY the quotation — in “ ” "
        "quotation marks. When the sentence mixes the speaker's own words with a "
        "verse (e.g. 'Now verse 6.' followed by the verse), the speaker's words "
        "stay outside the quotation marks: "
        "現在看第六節。“他們聚集的時候，問耶穌說……”",
        "When you reproduced 和合本 wording and you are certain which verse it "
        "is, add one extra line after the translation: '@ref' followed by the "
        "standard Chinese book name, chapter, and verse (e.g. '@ref 約翰福音 3:16', "
        "'@ref 羅馬書 8:1-2'). This marker line is the ONLY thing allowed besides "
        "the translation itself. If the sentence is not a verse quotation, or you "
        "are not certain of the exact reference, output no marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

FARSI = LanguageConfig(
    code="fa",
    name="Farsi",
    tts_voice=None,  # Google Cloud TTS has no Persian voice — subtitles only
    tts_speed=1.1,
    glossary={
        "grace": "فیض",
        "gospel": "انجیل",
        "salvation": "نجات",
        "repentance": "توبه",
        "worship": "پرستش",
        "sermon": "موعظه",
        "congregation": "جماعت",
        "the Lord": "خداوند",
        "God": "خدا",
        "Jesus Christ": "عیسی مسیح",
        "Holy Spirit": "روح‌القدس",
        "kingdom of God": "پادشاهی خدا",
        "faith": "ایمان",
        "prayer": "دعا",
        "the Word": "کلام خدا",
        "scripture": "کتاب مقدس",
        "blessing": "برکت",
        "covenant": "عهد",
        "cross": "صلیب",
        "resurrection": "رستاخیز",
        "amen": "آمین",
        "hallelujah": "هللویاه",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into Persian (Farsi).",
        "Translate the given {source} sentence into natural, fluent Persian. "
        "Output ONLY the Persian translation — no explanations, no "
        "transliteration, no quotation marks around the output (the only "
        "exception: “ ” around a Bible verse quotation, as instructed below).",
        "Use the formal, reverent register customary in Persian-language "
        "Christian preaching.",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard Persian book names "
        "(e.g. John 3:16 → یوحنا ۳:۱۶).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "ترجمهٔ هزارهٔ نو (New Millennium Version) word for word. If you are not "
        "certain of the exact wording, translate it in that translation's style.",
        "Wrap the Bible verse quotation — and ONLY the quotation — in “ ” "
        "quotation marks (use these marks only; never add « » or other quote "
        "marks). When the sentence mixes the speaker's own words with a verse "
        "(e.g. 'Now verse 6.' followed by the verse), the speaker's words stay "
        "outside the quotation marks.",
        "When you reproduced the Bible translation's wording and you are certain "
        "which verse it is, add one extra line after the translation: '@ref' "
        "followed by the standard Persian book name, chapter, and verse "
        "(e.g. '@ref یوحنا ۳:۱۶', '@ref رومیان ۸:۱-۲'). This marker line is the "
        "ONLY thing allowed besides the translation itself. If the sentence is "
        "not a verse quotation, or you are not certain of the exact reference, "
        "output no marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

PUNJABI = LanguageConfig(
    code="pa",
    name="Punjabi",
    tts_voice="pa-IN-Chirp3-HD-Charon",
    tts_speed=1.1,
    glossary={
        "grace": "ਕਿਰਪਾ",
        "gospel": "ਖੁਸ਼ਖਬਰੀ",
        "salvation": "ਮੁਕਤੀ",
        "repentance": "ਤੋਬਾ",
        "worship": "ਅਰਾਧਨਾ",
        "sermon": "ਉਪਦੇਸ਼",
        "congregation": "ਸੰਗਤ",
        "the Lord": "ਪ੍ਰਭੂ",
        "God": "ਪਰਮੇਸ਼ੁਰ",
        "Jesus Christ": "ਯਿਸੂ ਮਸੀਹ",
        "Holy Spirit": "ਪਵਿੱਤਰ ਆਤਮਾ",
        "kingdom of God": "ਪਰਮੇਸ਼ੁਰ ਦਾ ਰਾਜ",
        "faith": "ਵਿਸ਼ਵਾਸ",
        "prayer": "ਪ੍ਰਾਰਥਨਾ",
        "the Word": "ਬਚਨ",
        "scripture": "ਪਵਿੱਤਰ ਸ਼ਾਸਤਰ",
        "blessing": "ਬਰਕਤ",
        "covenant": "ਨੇਮ",
        "cross": "ਸਲੀਬ",
        "resurrection": "ਜੀ ਉੱਠਣਾ",
        "amen": "ਆਮੀਨ",
        "hallelujah": "ਹਲਲੂਯਾਹ",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into Punjabi (Gurmukhi script).",
        "Translate the given {source} sentence into natural, fluent Punjabi. "
        "Output ONLY the Punjabi translation — no explanations, no "
        "transliteration, no quotation marks around the output (the only "
        "exception: “ ” around a Bible verse quotation, as instructed below).",
        "Use the formal, reverent register customary in Punjabi-language "
        "Christian preaching.",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard Punjabi book names "
        "(e.g. John 3:16 → ਯੂਹੰਨਾ 3:16).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "standard Punjabi Bible (ਪਵਿੱਤਰ ਬਾਈਬਲ, BSI) word for word. If you are "
        "not certain of the exact wording, translate it in that translation's "
        "style.",
        "Wrap the Bible verse quotation — and ONLY the quotation — in “ ” "
        "quotation marks. When the sentence mixes the speaker's own words with a "
        "verse (e.g. 'Now verse 6.' followed by the verse), the speaker's words "
        "stay outside the quotation marks.",
        "When you reproduced the Bible translation's wording and you are certain "
        "which verse it is, add one extra line after the translation: '@ref' "
        "followed by the standard Punjabi book name, chapter, and verse "
        "(e.g. '@ref ਯੂਹੰਨਾ 3:16', '@ref ਰੋਮੀਆਂ 8:1-2'). This marker line is the "
        "ONLY thing allowed besides the translation itself. If the sentence is "
        "not a verse quotation, or you are not certain of the exact reference, "
        "output no marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

SPANISH = LanguageConfig(
    code="es",
    name="Spanish",
    tts_voice="es-US-Chirp3-HD-Charon",
    tts_speed=1.1,
    glossary={
        "grace": "gracia",
        "gospel": "evangelio",
        "salvation": "salvación",
        "repentance": "arrepentimiento",
        "worship": "adoración",
        "sermon": "sermón",
        "congregation": "congregación",
        "the Lord": "el Señor",
        "God": "Dios",
        "Jesus Christ": "Jesucristo",
        "Holy Spirit": "Espíritu Santo",
        "kingdom of God": "reino de Dios",
        "faith": "fe",
        "prayer": "oración",
        "the Word": "la Palabra",
        "scripture": "las Escrituras",
        "blessing": "bendición",
        "covenant": "pacto",
        "cross": "cruz",
        "resurrection": "resurrección",
        "amen": "amén",
        "hallelujah": "aleluya",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into Spanish (Latin American usage).",
        "Translate the given {source} sentence into natural, fluent Spanish. "
        "Output ONLY the Spanish translation — no explanations, no quotation "
        "marks around the output (the only exception: “ ” around a Bible verse "
        "quotation, as instructed below).",
        "Use the solemn, reverent register customary in Spanish-language "
        "preaching; address the congregation as ustedes.",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard Spanish book names "
        "(e.g. John 3:16 → Juan 3:16).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "Reina-Valera 1960 word for word. If you are not certain of the exact "
        "Reina-Valera 1960 wording, translate it in that translation's style.",
        "Wrap the Reina-Valera verse quotation — and ONLY the quotation — in "
        "“ ” quotation marks. When the sentence mixes the speaker's own words "
        "with a verse (e.g. 'Now verse 6.' followed by the verse), the "
        "speaker's words stay outside the quotation marks: "
        "Ahora el versículo 6. “Entonces los que se habían reunido le "
        "preguntaron…”",
        "When you reproduced Reina-Valera 1960 wording and you are certain "
        "which verse it is, add one extra line after the translation: '@ref' "
        "followed by the standard Spanish book name, chapter, and verse "
        "(e.g. '@ref Juan 3:16', '@ref Romanos 8:1-2'). This marker line is the "
        "ONLY thing allowed besides the translation itself. If the sentence is "
        "not a verse quotation, or you are not certain of the exact reference, "
        "output no marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

FRENCH = LanguageConfig(
    code="fr",
    name="French",
    tts_voice="fr-FR-Chirp3-HD-Charon",
    tts_speed=1.1,
    glossary={
        "grace": "grâce",
        "gospel": "Évangile",
        "salvation": "salut",
        "repentance": "repentance",
        "worship": "adoration",
        "sermon": "prédication",
        "congregation": "assemblée",
        "the Lord": "le Seigneur",
        "God": "Dieu",
        "Jesus Christ": "Jésus-Christ",
        "Holy Spirit": "le Saint-Esprit",
        "kingdom of God": "le royaume de Dieu",
        "faith": "foi",
        "prayer": "prière",
        "the Word": "la Parole",
        "scripture": "les Écritures",
        "blessing": "bénédiction",
        "covenant": "alliance",
        "cross": "croix",
        "resurrection": "résurrection",
        "amen": "amen",
        "hallelujah": "alléluia",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into French.",
        "Translate the given {source} sentence into natural, fluent French. "
        "Output ONLY the French translation — no explanations, no quotation "
        "marks around the output (the only exception: “ ” around a Bible verse "
        "quotation, as instructed below).",
        "Use the solemn, reverent register customary in French-language "
        "Protestant preaching; address the congregation with vous.",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard French book names "
        "(e.g. John 3:16 → Jean 3:16).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "Louis Segond (1910) translation word for word. If you are not certain "
        "of the exact Louis Segond wording, translate it in that translation's "
        "style.",
        "Wrap the Louis Segond verse quotation — and ONLY the quotation — in "
        "“ ” quotation marks (use these marks, not « »). When the sentence "
        "mixes the speaker's own words with a verse (e.g. 'Now verse 6.' "
        "followed by the verse), the speaker's words stay outside the quotation "
        "marks: Maintenant le verset 6. “Alors les apôtres réunis lui "
        "demandèrent…”",
        "When you reproduced Louis Segond wording and you are certain which "
        "verse it is, add one extra line after the translation: '@ref' followed "
        "by the standard French book name, chapter, and verse (e.g. '@ref Jean "
        "3:16', '@ref Romains 8:1-2'). This marker line is the ONLY thing "
        "allowed besides the translation itself. If the sentence is not a verse "
        "quotation, or you are not certain of the exact reference, output no "
        "marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

ENGLISH = LanguageConfig(
    code="en",
    name="English",
    tts_voice="en-US-Chirp3-HD-Charon",
    tts_speed=1.1,
    # Identity glossary: the keys name each concept in English, and for an
    # English target the canonical rendering is the concept itself. It still
    # anchors terminology (e.g. 은혜 → "grace", never "favor").
    glossary={
        "grace": "grace",
        "gospel": "gospel",
        "salvation": "salvation",
        "repentance": "repentance",
        "worship": "worship",
        "sermon": "sermon",
        "congregation": "congregation",
        "the Lord": "the Lord",
        "God": "God",
        "Jesus Christ": "Jesus Christ",
        "Holy Spirit": "Holy Spirit",
        "kingdom of God": "kingdom of God",
        "faith": "faith",
        "prayer": "prayer",
        "the Word": "the Word",
        "scripture": "Scripture",
        "blessing": "blessing",
        "covenant": "covenant",
        "cross": "cross",
        "resurrection": "resurrection",
        "amen": "amen",
        "hallelujah": "hallelujah",
    },
    style_rules=[
        "You are a simultaneous interpreter translating a live Christian sermon "
        "from {source} into English.",
        "Translate the given {source} sentence into natural, fluent English. "
        "Output ONLY the English translation — no explanations, no quotation "
        "marks around the output (the only exception: “ ” around a Bible verse "
        "quotation, as instructed below).",
        "Use the natural, reverent register customary in English-language "
        "preaching.",
        "Preserve the speaker's meaning and tone; do not add or omit content.",
        "Bible verse references should use standard English book names "
        "(e.g. 요한복음 3:16 / Jean 3:16 → John 3:16).",
        "When the {source} sentence is a quotation of a Bible verse, do NOT "
        "translate it freshly — reproduce the corresponding verse from the "
        "New International Version (NIV) word for word. If you are not certain "
        "of the exact NIV wording, translate it in NIV style.",
        "Wrap the NIV verse quotation — and ONLY the quotation — in “ ” "
        "quotation marks. When the sentence mixes the speaker's own words with a "
        "verse (e.g. 'Now verse 6.' followed by the verse), the speaker's words "
        "stay outside the quotation marks: "
        "Now verse 6. “Then they gathered around him and asked him…”",
        "When you reproduced NIV wording and you are certain which verse it is, "
        "add one extra line after the translation: '@ref' followed by the "
        "standard English book name, chapter, and verse (e.g. '@ref John 3:16', "
        "'@ref Romans 8:1-2'). This marker line is the ONLY thing allowed "
        "besides the translation itself. If the sentence is not a verse "
        "quotation, or you are not certain of the exact reference, output no "
        "marker line.",
        "If the sentence is an incomplete fragment, still translate it as "
        "naturally as possible.",
    ],
)

LANGUAGES: dict[str, LanguageConfig] = {
    config.code: config
    for config in (
        ENGLISH,
        KOREAN,
        MANDARIN,
        CANTONESE,
        FARSI,
        PUNJABI,
        SPANISH,
        FRENCH,
    )
}

# Aliases for the original Korean-only module-level API.
GLOSSARY: dict[str, str] = KOREAN.glossary
STYLE_RULES: list[str] = KOREAN.style_rules


def build_translation_instruction(lang: str = "ko", source: str = "en") -> str:
    """Build the system instruction for the Gemini translation model.

    ``source`` is the speaker's language (a SOURCE_LANGUAGES code); it fills
    the ``{source}`` placeholders in the style rules. The glossary keys are
    always English concept names, so for non-English sources the model is
    told to match concepts rather than literal key strings.
    """
    config = LANGUAGES[lang]
    source_name = SOURCE_LANGUAGES[source]
    lines: list[str] = [rule.format(source=source_name) for rule in config.style_rules]
    lines.append("")
    if source == "en":
        lines.append("Always use this glossary for the following terms:")
    else:
        lines.append(
            "Always use this glossary. Each entry names a concept in English; "
            f"whenever the equivalent concept appears in the {source_name} "
            "sentence, render it with the given term:"
        )
    for english, target in config.glossary.items():
        lines.append(f"- {english} → {target}")
    return "\n".join(lines)
