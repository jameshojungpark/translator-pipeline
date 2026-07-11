"""FastAPI server: host audio in → Deepgram STT → sentence → Gemini translation.

Endpoints:
  WS /ws/host?room=NAME    — binary 16 kHz mono 16-bit PCM audio from the host app
  WS /ws/client?room=NAME  — receive-only; gets JSON transcript/translation events
"""

import asyncio
import logging
import os

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from server.rooms import Room, RoomManager
from server.segmenter import SentenceSegmenter
from server.stt import DeepgramTranscriber
from server.translator import Translator

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Live Sermon Translator")
rooms = RoomManager()
_translator: Translator | None = None


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _translator = Translator(api_key)
    return _translator


class HostSession:
    """Pipeline for one host connection: STT → segmenter → translation queue."""

    def __init__(self, room: Room, translator: Translator) -> None:
        self.room = room
        self.translator = translator
        self.segmenter = SentenceSegmenter()
        self.sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.transcriber = DeepgramTranscriber(
            os.environ["DEEPGRAM_API_KEY"], self.on_transcript
        )

    async def on_transcript(self, text: str, is_final: bool) -> None:
        if not is_final:
            return
        for sentence in self.segmenter.feed(text):
            await self.emit_sentence(sentence)

    async def emit_sentence(self, sentence: str) -> None:
        """Broadcast a segmented sentence and queue it for translation."""
        print(f"[EN] {sentence}", flush=True)
        await self.room.broadcast({"type": "transcript", "text": sentence})
        await self.sentence_queue.put(sentence)

    async def translation_worker(self) -> None:
        """Translate sentences one at a time, preserving order."""
        while True:
            sentence = await self.sentence_queue.get()
            if sentence is None:
                return
            try:
                korean = await self.translator.translate(sentence)
            except Exception:
                logger.exception("translation failed for: %s", sentence)
                continue
            print(f"[KO] {korean}", flush=True)
            await self.room.broadcast(
                {"type": "translation", "source": sentence, "text": korean}
            )

    async def close(self) -> None:
        leftover = self.segmenter.flush()
        if leftover:
            await self.emit_sentence(leftover)
        await self.sentence_queue.put(None)
        await self.transcriber.stop()


@app.websocket("/ws/host")
async def ws_host(websocket: WebSocket, room: str = "main") -> None:
    the_room = rooms.get_or_create(room)
    if the_room.host_connected:
        await websocket.close(code=4409, reason="room already has a host")
        return

    await websocket.accept()
    the_room.host_connected = True
    logger.info("host connected room=%s", room)

    session = HostSession(the_room, get_translator())
    worker: asyncio.Task[None] | None = None
    try:
        await session.transcriber.start()
        worker = asyncio.create_task(session.translation_worker())
        while True:
            chunk = await websocket.receive_bytes()
            await session.transcriber.send(chunk)
    except WebSocketDisconnect:
        logger.info("host disconnected room=%s", room)
    finally:
        the_room.host_connected = False
        await session.close()
        if worker is not None:
            await worker
        rooms.cleanup(room)


@app.websocket("/ws/client")
async def ws_client(websocket: WebSocket, room: str = "main") -> None:
    the_room = rooms.get_or_create(room)
    await websocket.accept()
    the_room.add_client(websocket)
    logger.info("client joined room=%s (%d total)", room, the_room.client_count)
    try:
        # Clients are receive-only; we read just to detect disconnect.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        the_room.remove_client(websocket)
        logger.info("client left room=%s (%d remain)", room, the_room.client_count)
        rooms.cleanup(room)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Serve the client app at / (mounted last so API routes take precedence).
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent.parent / "client", html=True),
    name="client",
)
