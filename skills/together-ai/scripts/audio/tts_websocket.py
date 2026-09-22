#!/usr/bin/env python3
"""
Together AI realtime text-to-speech over WebSocket.

Sends text to the realtime TTS WebSocket API, saves raw PCM audio, and optionally
prints word timestamps when `alignment=word` is enabled.

Usage:
    python tts_websocket.py --text "Hello from Together AI" --output speech_ws.pcm
    python tts_websocket.py --text "Hello from Together AI" --model hexgrad/Kokoro-82M --voice af_alloy

Requirements:
    pip install websockets
    export TOGETHER_API_KEY=your_key
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
from urllib.parse import urlencode

import websockets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI realtime TTS example")
    parser.add_argument(
        "--text",
        default="Hello from Together AI.",
        help="Text to synthesize",
    )
    parser.add_argument(
        "--output",
        default="speech_ws.pcm",
        help="PCM output file",
    )
    parser.add_argument(
        "--model",
        default="hexgrad/Kokoro-82M",
        help="TTS model",
    )
    parser.add_argument(
        "--voice",
        default="af_alloy",
        help="Voice ID",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=24000,
        help="Output sample rate in Hz",
    )
    parser.add_argument(
        "--response-format",
        default="pcm",
        choices=("pcm", "wav", "mp3", "opus", "aac", "flac"),
        help="Realtime audio format",
    )
    parser.add_argument(
        "--alignment",
        choices=("none", "word"),
        default="none",
        help="Whether to request word timestamps",
    )
    parser.add_argument(
        "--segment",
        choices=("sentence", "immediate", "never"),
        default="sentence",
        help="Text segmentation behavior",
    )
    parser.add_argument(
        "--max-partial-length",
        type=int,
        default=250,
        help="Buffer size before forced synthesis",
    )
    return parser.parse_args()


async def synthesize(args: argparse.Namespace) -> None:
    api_key = os.environ["TOGETHER_API_KEY"]
    query = urlencode(
        {
            "model": args.model,
            "voice": args.voice,
            "response_format": args.response_format,
            "sample_rate": args.sample_rate,
            "alignment": args.alignment,
            "segment": args.segment,
            "max_partial_length": args.max_partial_length,
        }
    )
    url = f"wss://api.together.ai/v1/audio/speech/websocket?{query}"
    headers = {"Authorization": f"Bearer {api_key}"}

    output = bytearray()

    async with websockets.connect(url, additional_headers=headers) as ws:
        session_message = json.loads(await ws.recv())
        print(f"Session created: {session_message['session']['id']}")

        await ws.send(json.dumps({"type": "input_text_buffer.append", "text": args.text}))
        await ws.send(json.dumps({"type": "input_text_buffer.commit"}))

        async for message in ws:
            event = json.loads(message)
            event_type = event.get("type")

            if event_type == "conversation.item.audio_output.delta":
                output.extend(base64.b64decode(event["delta"]))
            elif event_type == "conversation.item.word_timestamps":
                print(json.dumps(event, indent=2))
            elif event_type == "conversation.item.audio_output.done":
                break
            elif event_type in {"conversation.item.tts.failed", "error"}:
                raise RuntimeError(json.dumps(event))

    output_path = Path(args.output)
    output_path.write_bytes(output)
    print(f"Saved realtime audio to {output_path}")

    if args.response_format == "pcm":
        print(f"Play with: ffplay -f s16le -ar {args.sample_rate} {output_path}")


def main() -> None:
    args = parse_args()
    asyncio.run(synthesize(args))


if __name__ == "__main__":
    main()
