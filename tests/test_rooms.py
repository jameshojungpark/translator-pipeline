from typing import Any

import pytest

from server.rooms import Room, RoomManager


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


def test_wanted_langs_ignores_all_monitors() -> None:
    room = Room("main")
    room.add_client(FakeClient(), "ko")
    room.add_client(FakeClient(), "fa")
    room.add_client(FakeClient(), "all")
    assert room.wanted_langs() == {"ko", "fa"}


def test_manager_cleanup_only_removes_empty_rooms() -> None:
    manager = RoomManager()
    room = manager.get_or_create("main")
    room.host_connected = True
    manager.cleanup("main")
    assert manager.get_or_create("main") is room
    room.host_connected = False
    manager.cleanup("main")
    assert manager.get_or_create("main") is not room
