from server.segmenter import SentenceSegmenter


def test_emits_sentence_on_period() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("God is good.") == ["God is good."]


def test_buffers_until_period_arrives() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("In the beginning") == []
    assert seg.feed("was the Word.") == ["In the beginning was the Word."]


def test_multiple_sentences_in_one_chunk() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("Amen. Let us pray. And so") == ["Amen.", "Let us pray."]
    assert seg.feed("we begin.") == ["And so we begin."]


def test_question_and_exclamation_end_sentences() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("Can I get an amen? Hallelujah!") == [
        "Can I get an amen?",
        "Hallelujah!",
    ]


def test_empty_chunk_emits_nothing() -> None:
    seg = SentenceSegmenter()
    assert seg.feed("") == []


def test_flush_returns_leftover_once() -> None:
    seg = SentenceSegmenter()
    seg.feed("unfinished thought")
    assert seg.flush() == "unfinished thought"
    assert seg.flush() is None
