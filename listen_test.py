"""Stand-in for the client app: prints transcripts/translations.

Usage:  python listen_test.py [--room main] [--lang all] [--url ws://127.0.0.1:8000]
Run alongside mic_test.py (or a real host). Ctrl+C to stop.
"""

import argparse
import asyncio
import json

import websockets


async def main(url: str, room: str, lang: str) -> None:
    async with websockets.connect(
        f"{url}/ws/client?room={room}&lang={lang}", max_size=None
    ) as ws:
        print("Connected — waiting for the host to speak…")
        if lang == "all":
            print(
                "(monitor mode: translations only flow for languages a real "
                "viewer has selected — pass --lang ko etc. to create demand)"
            )
        async for raw in ws:
            message = json.loads(raw)
            kind = message["type"]
            label = message.get("lang", "ko").upper()
            if kind == "transcript":
                print(f"[EN] {message['text']}")
            elif kind == "translation":
                ref = message.get("reference")
                suffix = f"  〔{ref}〕" if ref else ""
                print(f"[{label}] {message['text']}{suffix}")
            elif kind == "tts":
                pcm_bytes = len(message["audio"]) * 3 // 4  # base64 → raw size
                seconds = pcm_bytes / (2 * message["rate"])
                print(f"[TTS {label}] {seconds:.1f}s of audio (id={message['id']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", default="main")
    parser.add_argument("--lang", default="all", help="ko, zh, or all")
    parser.add_argument("--url", default="ws://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.url, args.room, args.lang))
    except KeyboardInterrupt:
        print("\nstopped")
