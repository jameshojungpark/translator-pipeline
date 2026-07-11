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


def test_manager_cleanup_only_removes_empty_rooms() -> None:
    manager = RoomManager()
    room = manager.get_or_create("main")
    room.host_connected = True
    manager.cleanup("main")
    assert manager.get_or_create("main") is room
    room.host_connected = False
    manager.cleanup("main")
    assert manager.get_or_create("main") is not room
