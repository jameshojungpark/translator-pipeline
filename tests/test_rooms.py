from typing import Any

import pytest

from server.rooms import Room, RoomManager, canonical_room, parse_allowed_rooms


class FakeClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.received: list[Any] = []

    async def send_json(self, data: Any) -> None:
        if self.fail:
            raise ConnectionError("gone")
        self.received.append(data)


@pytest.mark.asyncio
async def test_broadcast_reaches_all_clients() -> None:
    room = Room("main")
    a, b = FakeClient(), FakeClient()
    room.add_client(a)
    room.add_client(b)
    await room.broadcast({"type": "transcript", "text": "hi"})
    assert a.received == [{"type": "transcript", "text": "hi"}]
    assert b.received == [{"type": "transcript", "text": "hi"}]


@pytest.mark.asyncio
async def test_broadcast_drops_dead_clients() -> None:
    room = Room("main")
    ok, dead = FakeClient(), FakeClient(fail=True)
    room.add_client(ok)
    room.add_client(dead)
    await room.broadcast({"type": "transcript", "text": "hi"})
    assert room.client_count == 1
    await room.broadcast({"type": "transcript", "text": "again"})
    assert len(ok.received) == 2


@pytest.mark.asyncio
async def test_broadcast_with_lang_targets_matching_and_all_clients() -> None:
    room = Room("main")
    ko, zh, monitor = FakeClient(), FakeClient(), FakeClient()
    room.add_client(ko, "ko")
    room.add_client(zh, "zh")
    room.add_client(monitor, "all")
    message = {"type": "translation", "lang": "zh", "text": "恩典"}
    await room.broadcast(message, lang="zh")
    assert ko.received == []
    assert zh.received == [message]
    assert monitor.received == [message]


@pytest.mark.asyncio
async def test_broadcast_without_lang_reaches_every_client() -> None:
    room = Room("main")
    ko, zh = FakeClient(), FakeClient()
    room.add_client(ko, "ko")
    room.add_client(zh, "zh")
    await room.broadcast({"type": "transcript", "text": "hi"})
    assert ko.received == [{"type": "transcript", "text": "hi"}]
    assert zh.received == [{"type": "transcript", "text": "hi"}]


@pytest.mark.asyncio
async def test_broadcast_stats_counts_languages_excluding_monitors() -> None:
    room = Room("main")
    ko1, ko2, es, monitor = FakeClient(), FakeClient(), FakeClient(), FakeClient()
    room.add_client(ko1, "ko")
    room.add_client(ko2, "ko")
    room.add_client(es, "es")
    room.add_client(monitor, "all")
    await room.broadcast_stats()
    expected = {"type": "stats", "total": 3, "langs": {"ko": 2, "es": 1}, "host": False}
    assert monitor.received == [expected]
    assert ko1.received == [expected]
    room.host_connected = True
    await room.broadcast_stats()
    assert monitor.received[-1]["host"] is True


def test_wanted_langs_ignores_all_monitors() -> None:
    room = Room("main")
    room.add_client(FakeClient(), "ko")
    room.add_client(FakeClient(), "fa")
    room.add_client(FakeClient(), "all")
    assert room.wanted_langs() == {"ko", "fa"}


def test_canonical_room_normalizes_case_and_whitespace() -> None:
    assert canonical_room("  Main ") == "main"
    assert canonical_room("YOUTH") == "youth"


def test_parse_allowed_rooms_splits_and_canonicalizes() -> None:
    assert parse_allowed_rooms("main, Youth , SPANISH") == {"main", "youth", "spanish"}


def test_parse_allowed_rooms_empty_when_unset_or_blank() -> None:
    assert parse_allowed_rooms(None) == set()
    assert parse_allowed_rooms("") == set()
    assert parse_allowed_rooms("  , ,") == set()


def test_is_allowed_unrestricted_when_no_allowlist() -> None:
    manager = RoomManager()
    assert manager.is_allowed("anything")
    assert manager.is_allowed("literally-any-room")


def test_is_allowed_restricts_to_allowlist_case_insensitively() -> None:
    manager = RoomManager({"main", "youth"})
    assert manager.is_allowed("main")
    assert manager.is_allowed("  Youth ")
    assert not manager.is_allowed("random")


def test_manager_cleanup_only_removes_empty_rooms() -> None:
    manager = RoomManager()
    room = manager.get_or_create("main")
    room.host_connected = True
    manager.cleanup("main")
    assert manager.get_or_create("main") is room
    room.host_connected = False
    manager.cleanup("main")
    assert manager.get_or_create("main") is not room
