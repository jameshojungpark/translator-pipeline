"""FastAPI server: host audio in → Deepgram STT → sentence → Gemini translation.

Endpoints:
  WS /ws/host?room=NAME&input_lang=CODE — binary 16 kHz mono 16-bit PCM audio from
                                       the host app; input_lang is the speaker's
                                       language (a SOURCE_LANGUAGES code: en/fr/ko)
  WS /ws/client?room=NAME&lang=CODE  — receive-only; gets JSON transcript/translation
                                       events for one language code from
                                       server/glossary.py ("all" = every language)
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
from server.glossary import LANGUAGES, SOURCE_LANGUAGES
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
_translators: dict[tuple[str, str], Translator] = {}  # (source, target) → Translator
_synthesizers: dict[str, Synthesizer] = {}


def _require_gemini_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def get_translator(lang: str, source: str = "en") -> Translator:
    key = (source, lang)
    if key not in _translators:
        _translators[key] = Translator(_require_gemini_key(), lang=lang, source=source)
    return _translators[key]


def _tts_voice(lang: str) -> str | None:
    """Resolve the Cloud TTS voice for a language (env override, then default).

    None means the language is text-only: Cloud TTS has no voice for it.
    """
    override = os.environ.get(f"TTS_VOICE_{lang.upper()}")
    if override:
        return override
    if lang == "ko" and os.environ.get("TTS_VOICE"):  # pre-Mandarin variable name
        return os.environ["TTS_VOICE"]
    return LANGUAGES[lang].tts_voice


def _tts_speed(lang: str) -> float:
    """Resolve speakingRate: per-language env, shared env, then config default."""
    override = os.environ.get(f"TTS_SPEED_{lang.upper()}") or os.environ.get(
        "TTS_SPEED"
    )
    if override:
        return float(override)
    return LANGUAGES[lang].tts_speed


def get_synthesizer(lang: str) -> Synthesizer | None:
    """Build the synthesizer for a language; None for text-only languages."""
    if lang not in _synthesizers:
        voice = _tts_voice(lang)
        if voice is None:
            return None
        api_key = os.environ.get("GOOGLE_CLOUD_TTS_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_CLOUD_TTS_KEY is not set")
        _synthesizers[lang] = Synthesizer(
            api_key,
            voice=voice,
            speed=_tts_speed(lang),
        )
    return _synthesizers[lang]


class HostSession:
    """Pipeline for one host connection: STT → segmenter → translation queue.

    Every segmented sentence gets an incrementing id; the transcript,
    translation, and tts messages for that sentence all carry it, so clients
    can align (and pair audio with) the three streams explicitly.
    """

    def __init__(
        self,
        room: Room,
        translators: dict[str, Translator],
        synthesizers: dict[str, Synthesizer],
        input_lang: str = "en",
    ) -> None:
        self.room = room
        self.translators = translators
        self.synthesizers = synthesizers
        self.input_lang = input_lang
        self.segmenter = SentenceSegmenter()
        self.sentence_queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue()
        self.transcriber = DeepgramTranscriber(
            os.environ["DEEPGRAM_API_KEY"], self.on_transcript, input_lang=input_lang
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
        print(f"[{self.input_lang.upper()}] {sentence}", flush=True)
        await self.room.broadcast(
            {"type": "transcript", "id": sentence_id, "text": sentence}
        )
        await self.sentence_queue.put((sentence_id, sentence))

    async def translation_worker(self) -> None:
        """Translate then synthesize sentences one at a time, preserving order.

        Sentences stay serial (order guarantee); within a sentence the target
        languages run concurrently, and a failure in one language never costs
        the others their text or audio. Only languages some viewer actually
        selected are processed — no Gemini/TTS spend on languages nobody is
        listening to ("all" monitors don't create demand).
        """
        while True:
            item = await self.sentence_queue.get()
            if item is None:
                return
            sentence_id, sentence = item
            # The speaker's own language needs no translator — it passes
            # through — so it counts as servable alongside the translators.
            servable = self.translators.keys() | {self.input_lang}
            langs = self.room.wanted_langs() & servable
            if not langs:
                continue
            await asyncio.gather(
                *(
                    self._relay_language(sentence_id, sentence, lang)
                    for lang in sorted(langs)
                )
            )

    async def _relay_language(
        self, sentence_id: int, sentence: str, lang: str
    ) -> None:
        """Translate + synthesize one sentence into one language and broadcast."""
        if lang == self.input_lang:
            # Same language as the speaker: pass the transcript through as the
            # translation. No TTS — the preacher's own voice is the audio.
            await self.room.broadcast(
                {
                    "type": "translation",
                    "id": sentence_id,
                    "lang": lang,
                    "source": sentence,
                    "text": sentence,
                    "reference": None,
                },
                lang=lang,
            )
            return
        try:
            translated = await self.translators[lang].translate(sentence)
        except Exception:
            logger.exception("translation failed lang=%s for: %s", lang, sentence)
            return
        ref_note = f"  〔{translated.reference}〕" if translated.reference else ""
        print(f"[{lang.upper()}] {translated.text}{ref_note}", flush=True)
        await self.room.broadcast(
            {
                "type": "translation",
                "id": sentence_id,
                "lang": lang,
                "source": sentence,
                "text": translated.text,
                "reference": translated.reference,
            },
            lang=lang,
        )
        synthesizer = self.synthesizers.get(lang)
        if synthesizer is None:
            return  # text-only language (no TTS voice available)
        # Text is already out; a TTS failure only costs this sentence's audio.
        # Verse quotation marks are display-only — keep them out of TTS.
        tts_text = translated.text.replace("“", "").replace("”", "")
        try:
            audio = await synthesizer.synthesize(tts_text)
        except Exception:
            logger.exception("tts failed lang=%s for: %s", lang, tts_text)
            return
        await self.room.broadcast(
            {
                "type": "tts",
                "id": sentence_id,
                "lang": lang,
                "rate": tts.OUTPUT_SAMPLE_RATE,
                "audio": base64.b64encode(audio).decode("ascii"),
            },
            lang=lang,
        )

    async def close(self) -> None:
        leftover = self.segmenter.flush()
        if leftover:
            await self.emit_sentence(leftover)
        await self.sentence_queue.put(None)
        await self.transcriber.stop()


@app.websocket("/ws/host")
async def ws_host(
    websocket: WebSocket, room: str = "main", input_lang: str = "en"
) -> None:
    if input_lang not in SOURCE_LANGUAGES:
        logger.warning("host requested unsupported input_lang=%s; using en", input_lang)
        input_lang = "en"
    the_room = rooms.get_or_create(room)
    if the_room.host_connected:
        await websocket.close(code=4409, reason="room already has a host")
        return

    await websocket.accept()
    the_room.host_connected = True
    logger.info("host connected room=%s input_lang=%s", room, input_lang)

    session = HostSession(
        the_room,
        {
            lang: get_translator(lang, input_lang)
            for lang in LANGUAGES
            if lang != input_lang  # the speaker's language passes through
        },
        {
            lang: synth
            for lang in LANGUAGES
            if lang != input_lang
            if (synth := get_synthesizer(lang)) is not None
        },
        input_lang=input_lang,
    )
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
async def ws_client(websocket: WebSocket, room: str = "main", lang: str = "ko") -> None:
    if lang != "all" and lang not in LANGUAGES:
        logger.warning("client requested unsupported lang=%s; serving ko", lang)
        lang = "ko"
    the_room = rooms.get_or_create(room)
    await websocket.accept()
    the_room.add_client(websocket, lang)
    logger.info(
        "client joined room=%s lang=%s (%d total)", room, lang, the_room.client_count
    )
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


# Serve the built client app at / (mounted last so API routes take
# precedence). Produced by `npm run build` in client/; check_dir=False so the
# server still boots for API-only use (e.g. tests) without a frontend build.
app.mount(
    "/",
    StaticFiles(
        directory=Path(__file__).parent.parent / "client" / "dist",
        html=True,
        check_dir=False,
    ),
    name="client",
)
