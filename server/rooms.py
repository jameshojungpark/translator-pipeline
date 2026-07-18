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
        self._clients: dict[ClientSocket, str] = {}  # socket -> language ("all" = every language)

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def add_client(self, client: ClientSocket, lang: str = "all") -> None:
        self._clients[client] = lang

    def remove_client(self, client: ClientSocket) -> None:
        self._clients.pop(client, None)

    def wanted_langs(self) -> set[str]:
        """Languages at least one viewer selected ("all" monitors don't count).

        The pipeline only translates languages someone is actually listening
        to; a viewer who joins mid-service is picked up at the next sentence.
        """
        return {lang for lang in self._clients.values() if lang != "all"}

    def lang_counts(self) -> dict[str, int]:
        """Listener count per selected language ("all" monitors don't count)."""
        counts: dict[str, int] = {}
        for lang in self._clients.values():
            if lang != "all":
                counts[lang] = counts.get(lang, 0) + 1
        return counts

    async def broadcast_stats(self) -> None:
        """Push room telemetry to everyone: listener counts and whether a
        host is broadcasting (viewers gate their LIVE badge on it)."""
        counts = self.lang_counts()
        await self.broadcast(
            {
                "type": "stats",
                "total": sum(counts.values()),
                "langs": counts,
                "host": self.host_connected,
            }
        )

    async def broadcast(self, message: dict[str, Any], lang: str | None = None) -> None:
        """Send a JSON message to connected clients, dropping dead ones.

        With ``lang`` set, only clients subscribed to that language (or to
        "all") receive the message; with ``lang=None`` everyone does.
        """
        dead: list[ClientSocket] = []
        for client, client_lang in self._clients.items():
            if lang is not None and client_lang not in (lang, "all"):
                continue
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        for client in dead:
            self._clients.pop(client, None)
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
