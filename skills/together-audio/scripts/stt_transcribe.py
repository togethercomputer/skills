#!/usr/bin/env python3
"""
Together AI speech-to-text examples with the Python v2 SDK.

Demonstrates:
- transcription
- translation
- diarization
- timestamps

Usage:
    python stt_transcribe.py transcribe audio.mp3
    python stt_transcribe.py translate foreign_audio.mp3 --target-language en
    python stt_transcribe.py diarize meeting.mp3 --min-speakers 2 --max-speakers 5
    python stt_transcribe.py timestamps audio.mp3 --granularity word

Requirements:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

from __future__ import annotations

import argparse
from pathlib import Path

from together import Together

client = Together()


def transcribe(
    audio_path: Path,
    model: str,
    language: str | None,
    prompt: str | None,
    temperature: float | None,
) -> str:
    """Run a basic transcription request."""
    with open(audio_path, "rb") as audio_file:
        payload: dict[str, object] = {
            "file": audio_file,
            "model": model,
            "response_format": "json",
        }
        if language:
            payload["language"] = language
        if prompt:
            payload["prompt"] = prompt
        if temperature is not None:
            payload["temperature"] = temperature

        response = client.audio.transcriptions.create(**payload)
    print(f"Transcription: {response.text}")
    return response.text


def translate(
    audio_path: Path,
    model: str,
    target_language: str | None,
    prompt: str | None,
    temperature: float | None,
) -> str:
    """Translate audio, defaulting to English if no target language is provided."""
    with open(audio_path, "rb") as audio_file:
        payload: dict[str, object] = {
            "file": audio_file,
            "model": model,
        }
        if target_language:
            payload["language"] = target_language
        if prompt:
            payload["prompt"] = prompt
        if temperature is not None:
            payload["temperature"] = temperature

        response = client.audio.translations.create(**payload)
    print(f"Translation: {response.text}")
    return response.text


def diarize(audio_path: Path, model: str, min_speakers: int, max_speakers: int) -> None:
    """Run diarization and print speaker segments."""
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            response_format="verbose_json",
            diarize=True,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
    if not response.speaker_segments:
        print("No speaker segments returned.")
        return

    for segment in response.speaker_segments:
        print(f"[{segment.speaker_id}] {segment.start:.1f}s-{segment.end:.1f}s: {segment.text}")


def timestamps(audio_path: Path, model: str, granularity: str) -> None:
    """Print timestamped transcription results."""
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            response_format="verbose_json",
            timestamp_granularities=granularity,
        )
    print(f"Text: {response.text}")
    print(f"Language: {response.language}")
    print(f"Duration: {response.duration}s")

    if granularity == "word" and response.words:
        for word in response.words:
            print(f"'{word.word}' [{word.start:.2f}s - {word.end:.2f}s]")
        return

    if response.segments:
        for segment in response.segments:
            print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI STT examples")
    parser.add_argument(
        "mode",
        choices=("transcribe", "translate", "diarize", "timestamps"),
        help="Workflow to run",
    )
    parser.add_argument("audio_file", help="Path to the input audio file")
    parser.add_argument(
        "--model",
        default="openai/whisper-large-v3",
        help="Speech-to-text model",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Source language for transcription or target language for translation when appropriate",
    )
    parser.add_argument(
        "--target-language",
        default=None,
        help="Optional target language for translations",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Optional prompt to bias decoding",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Optional sampling temperature between 0.0 and 1.0",
    )
    parser.add_argument(
        "--granularity",
        choices=("segment", "word"),
        default="word",
        help="Timestamp granularity",
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=1,
        help="Minimum expected speakers for diarization",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=5,
        help="Maximum expected speakers for diarization",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audio_path = Path(args.audio_file)

    if args.mode == "transcribe":
        transcribe(
            audio_path=audio_path,
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            temperature=args.temperature,
        )
        return

    if args.mode == "translate":
        translate(
            audio_path=audio_path,
            model=args.model,
            target_language=args.target_language or args.language,
            prompt=args.prompt,
            temperature=args.temperature,
        )
        return

    if args.mode == "diarize":
        diarize(
            audio_path=audio_path,
            model=args.model,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
        )
        return

    timestamps(
        audio_path=audio_path,
        model=args.model,
        granularity=args.granularity,
    )


if __name__ == "__main__":
    main()
