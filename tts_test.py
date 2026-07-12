"""TTS-only test: synthesizes one Korean sentence and plays it, no server.

Verifies the Cloud TTS key/voice work before wiring a live service through
them. Also writes the raw PCM to a .wav for inspection.

Usage:  python tts_test.py [text] [--voice ...] [--speed 1.2] [--out tts_test.wav]
"""

import argparse
import asyncio
import os
import wave

import sounddevice as sd
from dotenv import load_dotenv

from server.tts import OUTPUT_SAMPLE_RATE, SPEED, VOICE, Synthesizer

DEFAULT_TEXT = "하나님의 은혜와 평강이 여러분과 함께 하시기를 바랍니다."


async def main(text: str, voice: str, speed: float, out: str) -> None:
    load_dotenv()
    api_key = os.environ.get("GOOGLE_CLOUD_TTS_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_CLOUD_TTS_KEY is not set (check .env)")

    synthesizer = Synthesizer(api_key, voice=voice, speed=speed)
    print(f"Synthesizing with voice={voice} speed={speed}:\n  {text}")
    pcm = await synthesizer.synthesize(text)
    seconds = len(pcm) / (2 * OUTPUT_SAMPLE_RATE)
    print(f"Got {len(pcm)} bytes ({seconds:.1f}s at {OUTPUT_SAMPLE_RATE} Hz)")

    with wave.open(out, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(OUTPUT_SAMPLE_RATE)
        f.writeframes(pcm)
    print(f"Wrote {out}")

    print("Playing…")
    sd.play(
        memoryview(pcm).cast("h"), samplerate=OUTPUT_SAMPLE_RATE, blocking=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="?", default=DEFAULT_TEXT)
    parser.add_argument("--voice", default=VOICE)
    parser.add_argument("--speed", type=float, default=SPEED)
    parser.add_argument("--out", default="tts_test.wav")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.text, args.voice, args.speed, args.out))
    except KeyboardInterrupt:
        print("\nstopped")
