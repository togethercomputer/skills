#!/usr/bin/env python3
"""
Together AI Text-to-Speech — REST, Streaming, and WebSocket (v2 SDK)

Three TTS modes: REST (file output), streaming (low latency), WebSocket (real-time).

Usage:
    python tts_generate.py

Requires:
    pip install together websockets
    export TOGETHER_API_KEY=your_key
"""

import asyncio
import base64
import json
import os

from together import Together

client = Together()


def tts_rest(text: str, output_file: str = "speech.mp3"):
    """Generate speech and save to file (REST API)."""
    response = client.audio.speech.with_raw_response.create(
        model="canopylabs/orpheus-3b-0.1-ft",
        input=text,
        voice="tara",
        response_format="mp3",
    )
    response.write_to_file(output_file)
    print(f"Saved to {output_file}")


def tts_streaming(text: str, output_file: str = "speech_stream.pcm"):
    """Generate speech with streaming for low time-to-first-byte."""
    response = client.audio.speech.with_raw_response.create(
        model="canopylabs/orpheus-3b-0.1-ft",
        input=text,
        voice="tara",
        stream=True,
        response_format="raw",
        response_encoding="pcm_s16le",
    )
    response.write_to_file(output_file)
    print(f"Saved to {output_file}")


async def tts_websocket(text_chunks: list[str], output_file: str = "speech_ws.wav"):
    """Generate speech via WebSocket for real-time interactive use."""
    import websockets

    api_key = os.environ["TOGETHER_API_KEY"]
    url = "wss://api.together.ai/v1/audio/speech/websocket?model=hexgrad/Kokoro-82M&voice=af_alloy"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with websockets.connect(url, additional_headers=headers) as ws:
        # Wait for session creation
        session_msg = await ws.recv()
        session = json.loads(session_msg)
        print(f"Session: {session['session']['id']}")

        audio_data = bytearray()

        async def send():
            for chunk in text_chunks:
                await ws.send(json.dumps({"type": "input_text_buffer.append", "text": chunk}))
                await asyncio.sleep(0.3)
            await ws.send(json.dumps({"type": "input_text_buffer.commit"}))

        async def receive():
            async for message in ws:
                data = json.loads(message)
                if data["type"] == "conversation.item.audio_output.delta":
                    audio_data.extend(base64.b64decode(data["delta"]))
                elif data["type"] == "conversation.item.audio_output.done":
                    break

        await asyncio.gather(send(), receive())

        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"Saved to {output_file}")


if __name__ == "__main__":
    text = "Today is a wonderful day to build something people love!"

    # REST — simple file output
    tts_rest(text)

    # Streaming — low-latency first byte
    tts_streaming(text)

    # WebSocket — real-time interactive
    # asyncio.run(tts_websocket(["Hello. ", "This is real-time speech. ", "Pretty cool!"]))
