"""STT-only test: streams your microphone straight into Deepgram, no server.

Prints each final transcript chunk as Deepgram emits it, and the complete
sentences the SentenceSegmenter would hand to the translator. No translation
happens (GEMINI_API_KEY is not needed).

Usage:  python stt_test.py [--interim] [--min-length 15]
Speak English; Ctrl+C to stop (flushes any buffered partial sentence).
"""

import argparse
import asyncio
import os
from typing import Any

import sounddevice as sd
from dotenv import load_dotenv

from server.segmenter import SentenceSegmenter
from server.stt import DeepgramTranscriber

SAMPLE_RATE = 16000
CHUNK_FRAMES = 1600  # 100 ms at 16 kHz


async def main(show_interim: bool, min_length: int) -> None:
    load_dotenv()
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise SystemExit("DEEPGRAM_API_KEY is not set (check .env)")

    segmenter = SentenceSegmenter(min_length=min_length)

    async def on_transcript(text: str, is_final: bool) -> None:
        if not is_final:
            if show_interim:
                print(f"[interim]  {text}")
            return
        print(f"[final]    {text}")
        for sentence in segmenter.feed(text):
            print(f"[SENTENCE] {sentence}")

    transcriber = DeepgramTranscriber(api_key, on_transcript)
    await transcriber.start()

    loop = asyncio.get_running_loop()
    audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

    def on_audio(indata: Any, _frames: int, _time: Any, status: Any) -> None:
        if status:
            print(f"mic status: {status}")
        loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

    try:
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_FRAMES,
            callback=on_audio,
        ):
            print("Mic open — speak English. Ctrl+C to stop.")
            while True:
                await transcriber.send(await audio_queue.get())
    finally:
        leftover = segmenter.flush()
        if leftover:
            print(f"[LEFTOVER] {leftover}")
        await transcriber.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--interim", action="store_true", help="also print interim (non-final) results"
    )
    parser.add_argument(
        "--min-length", type=int, default=15, help="segmenter minimum sentence length"
    )
    args = parser.parse_args()
    try:
        asyncio.run(main(args.interim, args.min_length))
    except KeyboardInterrupt:
        print("\nstopped")
