"""Multi-language fan-out in HostSession.translation_worker, with fakes."""

import asyncio
from typing import Any

import pytest

from server.main import HostSession
from server.rooms import Room
from server.translator import Translation


class FakeClient:
    def __init__(self) -> None:
        self.received: list[Any] = []

    async def send_json(self, data: Any) -> None:
        self.received.append(data)


class FakeTranslator:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.calls = 0

    async def translate(self, sentence: str) -> Translation:
        self.calls += 1
        return Translation(f"{self.prefix}:{sentence}")


class FailingTranslator:
    async def translate(self, sentence: str) -> Translation:
        raise RuntimeError("boom")


class FakeSynthesizer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        return b"\x00\x01"


def make_session(room: Room, translators: dict, synthesizers: dict) -> HostSession:
    session = HostSession.__new__(HostSession)
    session.room = room
    session.translators = translators
    session.synthesizers = synthesizers
    session.sentence_queue = asyncio.Queue()
    session._next_id = 0
    return session


@pytest.mark.asyncio
async def test_worker_sends_each_language_to_its_own_clients() -> None:
    room = Room("main")
    ko, zh = FakeClient(), FakeClient()
    room.add_client(ko, "ko")
    room.add_client(zh, "zh")
    session = make_session(
        room,
        {"ko": FakeTranslator("ko"), "zh": FakeTranslator("zh")},
        {"ko": FakeSynthesizer(), "zh": FakeSynthesizer()},
    )
    await session.sentence_queue.put((0, "Grace."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    assert [(m["type"], m["lang"]) for m in ko.received] == [
        ("translation", "ko"),
        ("tts", "ko"),
    ]
    assert [(m["type"], m["lang"]) for m in zh.received] == [
        ("translation", "zh"),
        ("tts", "zh"),
    ]
    assert ko.received[0]["text"] == "ko:Grace."
    assert zh.received[0]["text"] == "zh:Grace."
    assert all(m["id"] == 0 for m in ko.received + zh.received)


@pytest.mark.asyncio
async def test_monitor_client_receives_every_demanded_language() -> None:
    room = Room("main")
    monitor, ko, zh = FakeClient(), FakeClient(), FakeClient()
    room.add_client(monitor, "all")
    room.add_client(ko, "ko")
    room.add_client(zh, "zh")
    session = make_session(
        room,
        {"ko": FakeTranslator("ko"), "zh": FakeTranslator("zh")},
        {"ko": FakeSynthesizer(), "zh": FakeSynthesizer()},
    )
    await session.sentence_queue.put((0, "Amen."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    langs = {m["lang"] for m in monitor.received if m["type"] == "translation"}
    assert langs == {"ko", "zh"}


@pytest.mark.asyncio
async def test_undemanded_language_is_not_translated() -> None:
    room = Room("main")
    ko = FakeClient()
    room.add_client(ko, "ko")
    ko_tr, zh_tr = FakeTranslator("ko"), FakeTranslator("zh")
    session = make_session(
        room, {"ko": ko_tr, "zh": zh_tr}, {"ko": FakeSynthesizer(), "zh": FakeSynthesizer()}
    )
    await session.sentence_queue.put((0, "Grace."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    assert ko_tr.calls == 1
    assert zh_tr.calls == 0


@pytest.mark.asyncio
async def test_no_viewers_means_no_translation_calls() -> None:
    room = Room("main")
    monitor = FakeClient()
    room.add_client(monitor, "all")  # monitors don't create demand
    ko_tr = FakeTranslator("ko")
    session = make_session(room, {"ko": ko_tr}, {"ko": FakeSynthesizer()})
    await session.sentence_queue.put((0, "Grace."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    assert ko_tr.calls == 0
    assert monitor.received == []


@pytest.mark.asyncio
async def test_text_only_language_gets_translation_but_no_tts() -> None:
    room = Room("main")
    fa = FakeClient()
    room.add_client(fa, "fa")
    # no synthesizer entry for fa — text-only language
    session = make_session(room, {"fa": FakeTranslator("fa")}, {})
    await session.sentence_queue.put((0, "Grace."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    assert [(m["type"], m["lang"]) for m in fa.received] == [("translation", "fa")]


@pytest.mark.asyncio
async def test_one_language_failing_does_not_block_the_other() -> None:
    room = Room("main")
    ko, zh = FakeClient(), FakeClient()
    room.add_client(ko, "ko")
    room.add_client(zh, "zh")
    session = make_session(
        room,
        {"ko": FailingTranslator(), "zh": FakeTranslator("zh")},
        {"ko": FakeSynthesizer(), "zh": FakeSynthesizer()},
    )
    await session.sentence_queue.put((0, "Grace."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    assert ko.received == []
    assert [(m["type"], m["lang"]) for m in zh.received] == [
        ("translation", "zh"),
        ("tts", "zh"),
    ]


@pytest.mark.asyncio
async def test_verse_quotes_are_stripped_from_tts_input() -> None:
    class QuotingTranslator:
        async def translate(self, sentence: str) -> Translation:
            return Translation("이제 6절입니다. “그들이 모였을 때에”", "사도행전 1:6")

    room = Room("main")
    room.add_client(FakeClient(), "ko")
    synth = FakeSynthesizer()
    session = make_session(room, {"ko": QuotingTranslator()}, {"ko": synth})
    await session.sentence_queue.put((0, "Now verse 6."))
    await session.sentence_queue.put(None)
    await session.translation_worker()

    assert synth.calls == ["이제 6절입니다. 그들이 모였을 때에"]
