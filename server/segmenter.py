"""Simple sentence segmentation over streaming transcript text."""

SENTENCE_ENDINGS: tuple[str, ...] = (".", "?", "!")


class SentenceSegmenter:
    """Accumulates final transcript chunks and emits complete sentences.

    A sentence is considered complete when it ends with one of
    SENTENCE_ENDINGS. Any trailing text that has not yet reached an
    ending stays buffered until the next chunk arrives.
    """

    def __init__(self) -> None:
        self._buffer: str = ""

    def feed(self, text: str) -> list[str]:
        """Add a transcript chunk; return any sentences completed by it."""
        if not text:
            return []
        if self._buffer and not self._buffer.endswith(" "):
            self._buffer += " "
        self._buffer += text.strip()

        sentences: list[str] = []
        start = 0
        for i, ch in enumerate(self._buffer):
            if ch in SENTENCE_ENDINGS:
                sentence = self._buffer[start : i + 1].strip()
                if sentence:
                    sentences.append(sentence)
                start = i + 1
        self._buffer = self._buffer[start:].lstrip()
        return sentences

    def flush(self) -> str | None:
        """Return and clear any incomplete buffered text (end of session)."""
        leftover = self._buffer.strip()
        self._buffer = ""
        return leftover or None
