"""Room management: one host per room, N passive client listeners."""

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ClientSocket(Protocol):
    """Minimal interface a client connection must expose."""

    async def send_json(self, data: Any) -> None: ...


class Room:
    def __init__(self, name: str) -> None:
        self.name = name
        self.host_connected: bool = False
        self._clients: set[ClientSocket] = set()

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def add_client(self, client: ClientSocket) -> None:
        self._clients.add(client)

    def remove_client(self, client: ClientSocket) -> None:
        self._clients.discard(client)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client, dropping dead ones."""
        dead: list[ClientSocket] = []
        for client in self._clients:
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        for client in dead:
            self._clients.discard(client)
        if dead:
            logger.info(
                "room=%s dropped %d dead client(s), %d remain",
                self.name, len(dead), len(self._clients),
            )


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def get_or_create(self, name: str) -> Room:
        if name not in self._rooms:
            self._rooms[name] = Room(name)
            logger.info("room=%s created", name)
        return self._rooms[name]

    def cleanup(self, name: str) -> None:
        room = self._rooms.get(name)
        if room and not room.host_connected and room.client_count == 0:
            del self._rooms[name]
            logger.info("room=%s removed (empty)", name)
