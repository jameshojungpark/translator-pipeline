"""Stand-in for the client app: prints transcripts/translations.

Usage:  python listen_test.py [--room main] [--url ws://127.0.0.1:8000]
Run alongside mic_test.py (or a real host). Ctrl+C to stop.
"""

import argparse
import asyncio
import json

import websockets


async def main(url: str, room: str) -> None:
    async with websockets.connect(
        f"{url}/ws/client?room={room}", max_size=None
    ) as ws:
        print("Connected — waiting for the host to speak…")
        async for raw in ws:
            message = json.loads(raw)
            kind = message["type"]
            if kind == "transcript":
                print(f"[EN] {message['text']}")
            elif kind == "translation":
                ref = message.get("reference")
                suffix = f"  〔{ref}〕" if ref else ""
                print(f"[KO] {message['text']}{suffix}")
            elif kind == "tts":
                pcm_bytes = len(message["audio"]) * 3 // 4  # base64 → raw size
                seconds = pcm_bytes / (2 * message["rate"])
                print(f"[TTS] {seconds:.1f}s of audio (id={message['id']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", default="main")
    parser.add_argument("--url", default="ws://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.url, args.room))
    except KeyboardInterrupt:
        print("\nstopped")
