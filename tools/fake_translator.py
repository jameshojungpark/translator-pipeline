"""Fake translator server for testing the client app without the real pipeline.

Imitates the wire protocol of server/main.py exactly — same /ws/client
endpoint, same JSON message shapes (transcript / translation / tts), same
per-language broadcast filtering via server.rooms.Room — but drives a scripted
sermon instead of Deepgram STT + Gemini + Cloud TTS. No API keys needed.

The "TTS" audio is a synthesized pulsing tone (24 kHz 16-bit PCM, duration
proportional to sentence length) so the client's audio decode/queue/highlight
path is exercised end to end.

Usage:
    python -m tools.fake_translator            # serves on :8000
    python -m tools.fake_translator --port 9000 --interval 4
Then open http://localhost:8000/?room=main in a browser.

The scripted feed starts when the first client joins a room, loops forever,
and stops when the room empties. Like the real server, only languages some
connected viewer selected get translation/tts messages.
"""

import argparse
import array
import asyncio
import base64
import logging
import math

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from server.rooms import Room, RoomManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("fake_translator")

INPUT_LANG = "en"  # the pretend preacher speaks English (passthrough, no TTS)
TEXT_ONLY = {"fa"}  # mirrors the real server: Farsi has no Cloud TTS voice
OUTPUT_SAMPLE_RATE = 24000

# Scripted sermon: English transcript + Korean translation, with one Bible
# verse entry so the reference pill and “ ” quotation display get tested.
SCRIPT: list[dict[str, str | None]] = [
    {
        "en": "Good morning, church family, it is so good to see you all today.",
        "ko": "교회 가족 여러분, 좋은 아침입니다. 오늘 여러분 모두를 뵙게 되어 정말 기쁩니다.",
        "reference": None,
    },
    {
        "en": "Please open your Bibles with me to the Gospel of John, chapter three.",
        "ko": "저와 함께 성경 요한복음 3장을 펴 주시기 바랍니다.",
        "reference": None,
    },
    {
        "en": "For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.",
        "ko": "“하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라”",
        "reference": "요한복음 3장 16절",
    },
    {
        "en": "This single verse contains the whole gospel in miniature.",
        "ko": "이 한 구절 안에 복음 전체가 축소되어 담겨 있습니다.",
        "reference": None,
    },
    {
        "en": "Notice that God's love is not merely a feeling, but an action.",
        "ko": "하나님의 사랑은 단순한 감정이 아니라 행동이라는 것을 주목하십시오.",
        "reference": None,
    },
    {
        "en": "He gave his only Son, and that giving cost him everything.",
        "ko": "하나님은 독생자를 주셨고, 그 내어 주심에는 모든 것이 담겨 있었습니다.",
        "reference": None,
    },
    {
        "en": "Grace is not something we earn; it is something we receive.",
        "ko": "은혜는 우리가 얻어내는 것이 아니라 받는 것입니다.",
        "reference": None,
    },
    {
        "en": "Let us come to the Lord in prayer with thankful hearts. Amen.",
        "ko": "감사한 마음으로 주님께 기도로 나아갑시다. 아멘.",
        "reference": None,
    },
]


def fake_translation(entry: dict[str, str | None], lang: str) -> tuple[str, str | None]:
    """Return (text, reference) for a target language.

    Korean is fully scripted; other languages get a tagged pseudo-translation
    so language switching in the client is still testable.
    """
    if lang == "ko":
        return str(entry["ko"]), entry["reference"]
    return f"[{lang}] {entry['ko']}", entry["reference"]


def synth_tts_pcm(text: str, sentence_id: int, rate: int = OUTPUT_SAMPLE_RATE) -> bytes:
    """Generate placeholder speech: a pulsing tone, ~0.35 s per word.

    Pitch varies with sentence id so overlapping or dropped clips are audible
    when listening to the client.
    """
    words = max(2, len(text.split()))
    duration = min(6.0, 0.35 * words)
    base_freq = 260.0 + (sentence_id % 6) * 60.0
    n = int(duration * rate)
    samples = array.array("h")
    for i in range(n):
        t = i / rate
        syllable = 0.5 * (1.0 + math.sin(2 * math.pi * 3.5 * t - math.pi / 2))
        edge = min(1.0, i / (rate * 0.02), (n - i) / (rate * 0.05))
        s = math.sin(2 * math.pi * base_freq * t) * syllable * edge * 0.3
        samples.append(int(s * 32767))
    return samples.tobytes()


app = FastAPI(title="Fake Sermon Translator (client test harness)")
rooms = RoomManager()
_feeds: dict[str, asyncio.Task[None]] = {}

# Set from CLI args in main(); module-level so `uvicorn tools.fake_translator:app`
# also works with the defaults.
settings = {"interval": 5.0, "translation_delay": 1.0, "tts_delay": 0.6}


async def relay_language(
    room: Room, sentence_id: int, entry: dict[str, str | None], lang: str
) -> None:
    """Mimic HostSession._relay_language: translation, then tts, per language."""
    source = str(entry["en"])
    if lang == INPUT_LANG:
        await room.broadcast(
            {
                "type": "translation",
                "id": sentence_id,
                "lang": lang,
                "source": source,
                "text": source,
                "reference": None,
            },
            lang=lang,
        )
        return
    text, reference = fake_translation(entry, lang)
    await room.broadcast(
        {
            "type": "translation",
            "id": sentence_id,
            "lang": lang,
            "source": source,
            "text": text,
            "reference": reference,
        },
        lang=lang,
    )
    if lang in TEXT_ONLY:
        return
    await asyncio.sleep(settings["tts_delay"])
    audio = synth_tts_pcm(text, sentence_id)
    await room.broadcast(
        {
            "type": "tts",
            "id": sentence_id,
            "lang": lang,
            "rate": OUTPUT_SAMPLE_RATE,
            "audio": base64.b64encode(audio).decode("ascii"),
        },
        lang=lang,
    )


async def run_feed(room: Room) -> None:
    """Loop the scripted sermon into a room until it empties."""
    sentence_id = 0
    logger.info("room=%s feed started", room.name)
    try:
        while True:
            for entry in SCRIPT:
                if room.client_count == 0:
                    return
                sentence = str(entry["en"])
                logger.info("room=%s [%d] %s", room.name, sentence_id, sentence)
                await room.broadcast(
                    {"type": "transcript", "id": sentence_id, "text": sentence}
                )
                await asyncio.sleep(settings["translation_delay"])
                langs = room.wanted_langs()
                await asyncio.gather(
                    *(
                        relay_language(room, sentence_id, entry, lang)
                        for lang in sorted(langs)
                    )
                )
                sentence_id += 1
                await asyncio.sleep(settings["interval"])
    finally:
        logger.info("room=%s feed stopped", room.name)


@app.websocket("/ws/client")
async def ws_client(websocket: WebSocket, room: str = "main", lang: str = "ko") -> None:
    the_room = rooms.get_or_create(room)
    await websocket.accept()
    the_room.add_client(websocket, lang)
    logger.info(
        "client joined room=%s lang=%s (%d total)", room, lang, the_room.client_count
    )
    feed = _feeds.get(room)
    if feed is None or feed.done():
        _feeds[room] = asyncio.create_task(run_feed(the_room))
    try:
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
    return {"status": "ok", "mode": "fake"}


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent.parent / "client", html=True),
    name="client",
)


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--interval", type=float, default=5.0, help="seconds between sentences"
    )
    parser.add_argument(
        "--translation-delay",
        type=float,
        default=1.0,
        help="seconds between transcript and translation (tests the pending state)",
    )
    parser.add_argument(
        "--tts-delay",
        type=float,
        default=0.6,
        help="seconds between translation and its tts audio",
    )
    args = parser.parse_args()
    settings["interval"] = args.interval
    settings["translation_delay"] = args.translation_delay
    settings["tts_delay"] = args.tts_delay
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
