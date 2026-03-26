#!/usr/bin/env python3
"""
Together AI text-to-speech examples with the Python v2 SDK.

Demonstrates:
- REST file generation
- Streaming HTTP generation
- Raw PCM byte output
- Voice discovery

Usage:
    python tts_generate.py --mode rest --text "Hello world" --output speech.mp3
    python tts_generate.py --mode stream --text "Hello world" --output speech_stream.wav
    python tts_generate.py --mode raw --text "Hello world" --output speech_raw.pcm
    python tts_generate.py --mode voices

Requirements:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

from __future__ import annotations

import argparse
import base64
import struct
from pathlib import Path

from together import Together
from together import Omit

client = Together()


def _write_wav(pcm_data: bytes, output_file: Path, sample_rate: int = 24000) -> None:
    """Wrap raw PCM s16le bytes in a WAV header and write to file."""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)

    with open(output_file, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(pcm_data)


def generate_rest(
    text: str,
    output_file: Path,
    model: str,
    voice: str,
    response_format: str,
    language: str | None,
    sample_rate: int | None,
) -> None:
    """Generate a complete audio file over HTTP."""
    payload: dict[str, object] = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": response_format,
    }
    if language:
        payload["language"] = language
    if sample_rate is not None:
        payload["sample_rate"] = sample_rate

    response = client.audio.speech.create(**payload)
    response.write_to_file(str(output_file))
    print(f"Saved {response_format} audio to {output_file}")


def generate_stream(
    text: str,
    output_file: Path,
    model: str,
    voice: str,
    response_encoding: str,
    language: str | None,
    sample_rate: int | None,
    alignment: str,
    segment: str,
) -> None:
    """Generate streaming audio and save it as a WAV file."""
    extra: dict[str, object] = {
        "alignment": alignment,
        "segment": segment,
    }
    response = client.audio.speech.create(
        model=model,
        input=text,
        voice=voice,
        stream=True,
        response_format="raw",
        response_encoding=response_encoding,
        language=language if language else Omit(),
        sample_rate=sample_rate if sample_rate is not None else Omit(),
        extra_body=extra,
    )
    raw_chunks: list[bytes] = []
    for chunk in response:
        if chunk.type == "conversation.item.audio_output.delta":
            raw_chunks.append(base64.b64decode(chunk.delta))
        elif chunk.type == "conversation.item.word_timestamps":
            print(f"Timestamps: {chunk.model_extra}")

    pcm_data = b"".join(raw_chunks)
    _write_wav(pcm_data, output_file, sample_rate=sample_rate or 24000)
    print(f"Saved streaming audio to {output_file}")


def generate_raw_bytes(
    text: str,
    output_file: Path,
    model: str,
    voice: str,
    response_encoding: str,
    language: str | None,
    sample_rate: int | None,
) -> None:
    """Request raw PCM bytes and save them directly."""
    payload: dict[str, object] = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "raw",
        "response_encoding": response_encoding,
    }
    if language:
        payload["language"] = language
    if sample_rate is not None:
        payload["sample_rate"] = sample_rate

    response = client.audio.speech.create(**payload)
    response.write_to_file(str(output_file))
    print(f"Saved raw audio bytes to {output_file}")


def list_voices() -> None:
    """List every voice returned by the voices API."""
    response = client.audio.voices.list()
    for model_voices in response.data:
        print(f"Model: {model_voices.model}")
        for voice in model_voices.voices:
            print(f"  - {voice.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI TTS examples")
    parser.add_argument(
        "--mode",
        choices=("rest", "stream", "raw", "voices"),
        default="rest",
        help="Workflow to run",
    )
    parser.add_argument(
        "--text",
        default="Today is a wonderful day to build something people love!",
        help="Input text",
    )
    parser.add_argument(
        "--output",
        default="speech.mp3",
        help="Output file path",
    )
    parser.add_argument(
        "--model",
        default="canopylabs/orpheus-3b-0.1-ft",
        help="TTS model",
    )
    parser.add_argument(
        "--voice",
        default="tara",
        help="Voice identifier",
    )
    parser.add_argument(
        "--response-format",
        choices=("mp3", "wav"),
        default="mp3",
        help="Output format for REST mode",
    )
    parser.add_argument(
        "--response-encoding",
        choices=("pcm_f32le", "pcm_s16le", "pcm_mulaw", "pcm_alaw"),
        default="pcm_s16le",
        help="Raw audio encoding for streaming or raw-byte modes",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language code such as en, fr, or es",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=None,
        help="Optional output sample rate in Hz",
    )
    parser.add_argument(
        "--alignment",
        choices=("none", "word"),
        default="none",
        help="Streaming alignment mode",
    )
    parser.add_argument(
        "--segment",
        choices=("sentence", "immediate", "never"),
        default="sentence",
        help="Streaming segmentation mode",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_file = Path(args.output)

    if args.mode == "voices":
        list_voices()
        return

    if args.mode == "rest":
        generate_rest(
            text=args.text,
            output_file=output_file,
            model=args.model,
            voice=args.voice,
            response_format=args.response_format,
            language=args.language,
            sample_rate=args.sample_rate,
        )
        return

    if args.mode == "stream":
        generate_stream(
            text=args.text,
            output_file=output_file,
            model=args.model,
            voice=args.voice,
            response_encoding=args.response_encoding,
            language=args.language,
            sample_rate=args.sample_rate,
            alignment=args.alignment,
            segment=args.segment,
        )
        return

    generate_raw_bytes(
        text=args.text,
        output_file=output_file,
        model=args.model,
        voice=args.voice,
        response_encoding=args.response_encoding,
        language=args.language,
        sample_rate=args.sample_rate,
    )


if __name__ == "__main__":
    main()
