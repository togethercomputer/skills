#!/usr/bin/env python3
"""
Together AI realtime speech-to-text over WebSocket.

Reads 16 kHz mono PCM audio from a WAV or raw PCM file, streams it to Together AI,
and prints interim and final transcription events.

Usage:
    python stt_realtime.py audio.wav
    python stt_realtime.py audio.pcm --model openai/whisper-large-v3

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
import wave
from pathlib import Path

import websockets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI realtime STT example")
    parser.add_argument("audio_file", help="Input WAV or raw PCM file")
    parser.add_argument(
        "--model",
        default="openai/whisper-large-v3",
        help="Realtime STT model",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4096,
        help="Bytes per websocket append event",
    )
    return parser.parse_args()


def load_pcm_s16le_16k(audio_path: Path) -> bytes:
    """Load a 16 kHz mono PCM file from WAV or raw PCM."""
    if audio_path.suffix.lower() != ".wav":
        return audio_path.read_bytes()

    with wave.open(str(audio_path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        if channels != 1 or sample_width != 2 or sample_rate != 16000:
            raise ValueError("Expected a mono 16-bit 16 kHz WAV file for realtime transcription.")
        return wav_file.readframes(wav_file.getnframes())


async def stream_audio(args: argparse.Namespace) -> None:
    api_key = os.environ["TOGETHER_API_KEY"]
    audio_path = Path(args.audio_file)
    pcm_audio = load_pcm_s16le_16k(audio_path)
    url = f"wss://api.together.ai/v1/realtime?model={args.model}&input_audio_format=pcm_s16le_16000"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    async with websockets.connect(url, additional_headers=headers) as ws:
        commit_sent = asyncio.Event()
        completed_transcripts: list[str] = []

        async def receive_events() -> None:
            while True:
                try:
                    if commit_sent.is_set():
                        message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    else:
                        message = await ws.recv()
                except asyncio.TimeoutError:
                    return

                event = json.loads(message)
                event_type = event.get("type")

                if event_type == "session.created":
                    print(f"Session created: {event['session']['id']}")
                elif event_type == "conversation.item.input_audio_transcription.delta":
                    print(f"\r{event['delta']}", end="", flush=True)
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = str(event["transcript"]).strip()
                    if transcript:
                        completed_transcripts.append(transcript)
                        print(f"\nFinal: {transcript}")
                elif event_type in {"conversation.item.input_audio_transcription.failed", "error"}:
                    raise RuntimeError(json.dumps(event))

        receiver = asyncio.create_task(receive_events())

        for start in range(0, len(pcm_audio), args.chunk_size):
            chunk = pcm_audio[start : start + args.chunk_size]
            payload = {
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(chunk).decode("utf-8"),
            }
            await ws.send(json.dumps(payload))

        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        commit_sent.set()
        await receiver

        if completed_transcripts:
            print("\nCombined transcript:")
            print(" ".join(completed_transcripts))


def main() -> None:
    args = parse_args()
    asyncio.run(stream_audio(args))


if __name__ == "__main__":
    main()
