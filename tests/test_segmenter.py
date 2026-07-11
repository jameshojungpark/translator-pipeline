from server.segmenter import SentenceSegmenter


def test_emits_sentence_on_period() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("God is good all the time.") == ["God is good all the time."]


def test_buffers_until_period_arrives() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("In the beginning") == []
    assert seg.feed("was the Word.") == ["In the beginning was the Word."]


def test_multiple_sentences_in_one_chunk() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("God so loved the world. He gave His only Son. And so") == [
        "God so loved the world.",
        "He gave His only Son.",
    ]
    assert seg.feed("we begin the sermon today.") == [
        "And so we begin the sermon today."
    ]


def test_question_and_exclamation_end_sentences() -> None:
    seg = SentenceSegmenter(min_length=1)
    assert seg.feed("Can I get an amen? Hallelujah!") == [
        "Can I get an amen?",
        "Hallelujah!",
    ]


def test_short_sentences_merge_into_one() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("hello. hello. hello.") == ["hello. hello. hello."]


def test_short_sentence_merges_with_next_chunk() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("Amen.") == []
    assert seg.feed("Let us pray together.") == ["Amen. Let us pray together."]


def test_custom_min_length() -> None:
    seg = SentenceSegmenter(min_length=10)
    assert seg.feed("hello. hello. hello.") == ["hello. hello."]
    assert seg.flush() == "hello."


def test_empty_chunk_emits_nothing() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("") == []


def test_flush_returns_leftover_once() -> None:
    seg = SentenceSegmenter()
    seg.feed("unfinished thought")
    assert seg.flush() == "unfinished thought"
    assert seg.flush() is None


def test_flush_returns_held_short_sentence() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("Amen.") == []
    assert seg.flush() == "Amen."
