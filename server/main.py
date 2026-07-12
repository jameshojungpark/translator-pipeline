"""FastAPI server: host audio in → Deepgram STT → sentence → Gemini translation.

Endpoints:
  WS /ws/host?room=NAME    — binary 16 kHz mono 16-bit PCM audio from the host app
  WS /ws/client?room=NAME  — receive-only; gets JSON transcript/translation events
"""

import asyncio
import base64
import logging
import os

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from server import tts
from server.rooms import Room, RoomManager
from server.segmenter import SentenceSegmenter
from server.stt import DeepgramTranscriber
from server.translator import Translator
from server.tts import Synthesizer

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Live Sermon Translator")
rooms = RoomManager()
_translator: Translator | None = None
_synthesizer: Synthesizer | None = None


def _require_gemini_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator(_require_gemini_key())
    return _translator


def get_synthesizer() -> Synthesizer:
    global _synthesizer
    if _synthesizer is None:
        api_key = os.environ.get("GOOGLE_CLOUD_TTS_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_CLOUD_TTS_KEY is not set")
        _synthesizer = Synthesizer(
            api_key,
            voice=os.environ.get("TTS_VOICE", tts.VOICE),
            speed=float(os.environ.get("TTS_SPEED", tts.SPEED)),
        )
    return _synthesizer


class HostSession:
    """Pipeline for one host connection: STT → segmenter → translation queue.

    Every segmented sentence gets an incrementing id; the transcript,
    translation, and tts messages for that sentence all carry it, so clients
    can align (and pair audio with) the three streams explicitly.
    """

    def __init__(
        self, room: Room, translator: Translator, synthesizer: Synthesizer
    ) -> None:
        self.room = room
        self.translator = translator
        self.synthesizer = synthesizer
        self.segmenter = SentenceSegmenter()
        self.sentence_queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue()
        self.transcriber = DeepgramTranscriber(
            os.environ["DEEPGRAM_API_KEY"], self.on_transcript
        )
        self._next_id = 0

    async def on_transcript(self, text: str, is_final: bool) -> None:
        if not is_final:
            return
        for sentence in self.segmenter.feed(text):
            await self.emit_sentence(sentence)

    async def emit_sentence(self, sentence: str) -> None:
        """Broadcast a segmented sentence and queue it for translation."""
        sentence_id = self._next_id
        self._next_id += 1
        print(f"[EN] {sentence}", flush=True)
        await self.room.broadcast(
            {"type": "transcript", "id": sentence_id, "text": sentence}
        )
        await self.sentence_queue.put((sentence_id, sentence))

    async def translation_worker(self) -> None:
        """Translate then synthesize sentences one at a time, preserving order."""
        while True:
            item = await self.sentence_queue.get()
            if item is None:
                return
            sentence_id, sentence = item
            try:
                korean = await self.translator.translate(sentence)
            except Exception:
                logger.exception("translation failed for: %s", sentence)
                continue
            ref_note = f"  〔{korean.reference}〕" if korean.reference else ""
            print(f"[KO] {korean.text}{ref_note}", flush=True)
            await self.room.broadcast(
                {
                    "type": "translation",
                    "id": sentence_id,
                    "source": sentence,
                    "text": korean.text,
                    "reference": korean.reference,
                }
            )
            # Text is already out; a TTS failure only costs this sentence's audio.
            # Verse quotation marks are display-only — keep them out of TTS.
            tts_text = korean.text.replace("“", "").replace("”", "")
            try:
                audio = await self.synthesizer.synthesize(tts_text)
            except Exception:
                logger.exception("tts failed for: %s", tts_text)
                continue
            await self.room.broadcast(
                {
                    "type": "tts",
                    "id": sentence_id,
                    "rate": tts.OUTPUT_SAMPLE_RATE,
                    "audio": base64.b64encode(audio).decode("ascii"),
                }
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

    session = HostSession(the_room, get_translator(), get_synthesizer())
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
