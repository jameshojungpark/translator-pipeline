"""HTTP-level gating: the app's HTML pages are withheld for disallowed rooms."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from server import main
from server.rooms import RoomManager

BLOCKED_MARKER = "Room unavailable"


@pytest.fixture
def client() -> Iterator[TestClient]:
    original = main.rooms
    yield TestClient(main.app, raise_server_exceptions=True)
    main.rooms = original


def _set_allowlist(allowed: set[str] | None) -> None:
    main.rooms = RoomManager(allowed)


def test_disallowed_room_is_blocked_at_root(client: TestClient) -> None:
    _set_allowlist({"main"})
    resp = client.get("/?room=secret")
    assert resp.status_code == 404
    assert BLOCKED_MARKER in resp.text


def test_disallowed_room_is_blocked_on_host_page(client: TestClient) -> None:
    _set_allowlist({"main"})
    resp = client.get("/host?room=secret")
    assert resp.status_code == 404
    assert BLOCKED_MARKER in resp.text


def test_allowed_room_is_not_blocked(client: TestClient) -> None:
    _set_allowlist({"main"})
    resp = client.get("/?room=Main")  # canonicalized to "main"
    assert BLOCKED_MARKER not in resp.text


def test_default_room_blocked_when_main_not_allowed(client: TestClient) -> None:
    _set_allowlist({"youth"})
    resp = client.get("/")  # no ?room → "main"
    assert resp.status_code == 404
    assert BLOCKED_MARKER in resp.text


def test_no_allowlist_serves_any_room(client: TestClient) -> None:
    _set_allowlist(set())
    resp = client.get("/?room=anything-goes")
    assert BLOCKED_MARKER not in resp.text


def test_health_always_available(client: TestClient) -> None:
    _set_allowlist({"main"})
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
