"""Stand-in for the host app: streams your microphone to the server.

Usage:  python mic_test.py [--room main] [--url ws://127.0.0.1:8000]
Speak English; watch the server terminal for [EN]/[KO] lines. Ctrl+C to stop.
"""

import argparse
import asyncio
from typing import Any

import sounddevice as sd
import websockets

SAMPLE_RATE = 16000
CHUNK_FRAMES = 1600  # 100 ms at 16 kHz


async def main(url: str, room: str) -> None:
    loop = asyncio.get_running_loop()
    audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

    def on_audio(indata: Any, _frames: int, _time: Any, status: Any) -> None:
        if status:
            print(f"mic status: {status}")
        loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

    async with websockets.connect(f"{url}/ws/host?room={room}") as ws:
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_FRAMES,
            callback=on_audio,
        ):
            print("Mic open — speak English. Ctrl+C to stop.")
            while True:
                await ws.send(await audio_queue.get())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", default="main")
    parser.add_argument("--url", default="ws://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.url, args.room))
    except KeyboardInterrupt:
        print("\nstopped")
