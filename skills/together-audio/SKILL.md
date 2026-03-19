---
name: together-audio
description: Text-to-speech (TTS) and speech-to-text (STT) via Together AI. TTS covers Orpheus, Kokoro, Cartesia, and dedicated-endpoint voice models across REST, streaming, and WebSocket APIs. STT covers Whisper, Voxtral, Parakeet, and dedicated-endpoint Deepgram models for transcription, translation, diarization, and realtime WebSocket transcription.
---

# Together Audio (TTS & STT)

## Overview

Together AI provides text-to-speech and speech-to-text capabilities.

**TTS**
- REST endpoint: `/v1/audio/speech`
- Realtime WebSocket: `wss://api.together.ai/v1/audio/speech/websocket`
- Delivery modes: full-file REST, streaming REST, raw WebSocket

**STT**
- Transcription: `/v1/audio/transcriptions`
- Translation: `/v1/audio/translations`
- Realtime WebSocket: `wss://api.together.ai/v1/realtime?model={model}&input_audio_format=pcm_s16le_16000`
- Delivery modes: file/URL transcription, translation, raw WebSocket

Use this skill when you need:
- TTS file generation, low-latency streaming, or realtime voice output
- STT transcription, translation, diarization, timestamps, or live transcription
- Voice discovery with `/v1/voices`

## Installation

```bash
# Python
uv add together
```

```bash
# or with pip
pip install together
```

```bash
# TypeScript / JavaScript
npm install together-ai
```

Set your API key:

```bash
export TOGETHER_API_KEY=your-api-key
```

## TTS Quick Start

### Generate Speech (REST)

```python
from together import Together

client = Together()

response = client.audio.speech.create(
    model="canopylabs/orpheus-3b-0.1-ft",
    input="Today is a wonderful day to build something people love!",
    voice="tara",
    response_format="mp3",
)
response.stream_to_file("speech.mp3")
```

```typescript
import Together from "together-ai";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new Together();

const response = await client.audio.speech.create({
  model: "canopylabs/orpheus-3b-0.1-ft",
  input: "Today is a wonderful day to build something people love!",
  voice: "tara",
  response_format: "mp3",
});

if (response.body) {
  const nodeStream = Readable.fromWeb(response.body as ReadableStream<Uint8Array>);
  await pipeline(nodeStream, createWriteStream("speech.mp3"));
}
```

```bash
curl -X POST "https://api.together.ai/v1/audio/speech" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"canopylabs/orpheus-3b-0.1-ft","input":"Hello world","voice":"tara","response_format":"mp3"}' \
  --output speech.mp3
```

### Streaming Audio

Streaming REST is best when time-to-first-byte matters. When `stream=true`, HTTP returns server-sent events and
`response_format="raw"` is required. `alignment="word"` is only supported on streaming requests.

```python
from together import Together

client = Together()

response = client.audio.speech.create(
    model="canopylabs/orpheus-3b-0.1-ft",
    input="The quick brown fox jumps over the lazy dog",
    voice="tara",
    stream=True,
    response_format="raw",
    response_encoding="pcm_s16le",
    alignment="word",
)
response.stream_to_file("speech_streaming.wav", response_format="wav")
```

```typescript
import Together from "together-ai";

const client = new Together();

const response = await client.audio.speech.create({
  model: "canopylabs/orpheus-3b-0.1-ft",
  input: "The quick brown fox jumps over the lazy dog",
  voice: "tara",
  stream: true,
  response_format: "raw",
  response_encoding: "pcm_s16le",
  alignment: "word",
});

for await (const event of response as AsyncIterable<any>) {
  console.log(event);
}
```

```bash
curl -N -X POST "https://api.together.ai/v1/audio/speech" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"canopylabs/orpheus-3b-0.1-ft","input":"The quick brown fox jumps over the lazy dog","voice":"tara","stream":true,"response_format":"raw","response_encoding":"pcm_s16le","alignment":"word"}'
```

### Realtime TTS (WebSocket)

Use the WebSocket API for the lowest latency and interactive voice applications. It is currently available through raw
WebSocket connections rather than the SDK.

```python
import asyncio
import base64
import json
import os

import websockets


async def generate_speech() -> None:
    api_key = os.environ["TOGETHER_API_KEY"]
    url = (
        "wss://api.together.ai/v1/audio/speech/websocket"
        "?model=hexgrad/Kokoro-82M"
        "&voice=af_alloy"
        "&response_format=pcm"
        "&sample_rate=24000"
        "&alignment=word"
    )
    headers = {"Authorization": f"Bearer {api_key}"}

    audio_data = bytearray()

    async with websockets.connect(url, additional_headers=headers) as ws:
        print(await ws.recv())  # session.created

        await ws.send(json.dumps({"type": "input_text_buffer.append", "text": "Hello from Together AI."}))
        await ws.send(json.dumps({"type": "input_text_buffer.commit"}))

        async for message in ws:
            event = json.loads(message)
            if event["type"] == "conversation.item.audio_output.delta":
                audio_data.extend(base64.b64decode(event["delta"]))
            elif event["type"] == "conversation.item.word_timestamps":
                print(event)
            elif event["type"] == "conversation.item.audio_output.done":
                break

    with open("speech_ws.pcm", "wb") as f:
        f.write(audio_data)


asyncio.run(generate_speech())
```

## TTS Models

The current guide-level TTS model catalog includes:

| Model | API String | Access | Endpoints | Notes |
|-------|-----------|--------|-----------|-------|
| Orpheus 3B | `canopylabs/orpheus-3b-0.1-ft` | Serverless | REST, Streaming, WebSocket | Realtime capable |
| Kokoro | `hexgrad/Kokoro-82M` | Serverless | REST, Streaming, WebSocket | Realtime capable |
| Cartesia Sonic 3 | `cartesia/sonic-3` | Serverless / Dedicated / Reserved | REST | Build Tier 2+ |
| Cartesia Sonic 2 | `cartesia/sonic-2` | Serverless / Dedicated / Reserved | REST | Build Tier 2+ |
| Cartesia Sonic | `cartesia/sonic` | Serverless | REST | Supported in `/audio/speech` reference |
| Deepgram Aura 2 | `deepgram/deepgram-aura-2` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Arcana v3 Turbo | `rime-labs/rime-arcana-v3-turbo` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Arcana v3 | `rime-labs/rime-arcana-v3` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Arcana v2 | `rime-labs/rime-arcana-v2` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Mist v3 (Beta) | `rime-labs/rime-mist-v3` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Mist v2 | `rime-labs/rime-mist-v2` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| MiniMax Speech 2.6 Turbo | `minimax/speech-2.6-turbo` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |

## TTS Parameters

Use the guide for high-level semantics and the `/audio/speech` reference for exact REST request fields.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | TTS model identifier |
| `input` | string | Text to synthesize |
| `voice` | string | Voice ID for the selected model |
| `response_format` | string | HTTP: `mp3`, `wav`, `raw`, `mulaw`; WebSocket also supports `pcm`, `opus`, `aac`, `flac` |
| `sample_rate` | int | Output sample rate in Hz |
| `language` | string | Language code such as `en`, `fr`, or `es` |
| `alignment` | string | `none` or `word`; `word` emits word timestamps |
| `segment` | string | `sentence`, `immediate`, or `never` |
| `response_encoding` | string | For raw audio: `pcm_f32le`, `pcm_s16le`, `pcm_mulaw`, `pcm_alaw` |
| `stream` | bool | Streaming HTTP mode; only `raw` is supported when true |

Key rules:
- `stream=true` requires `response_format="raw"`
- `alignment="word"` is only supported for streaming requests
- `/audio/speech` currently documents default sample rates of `24000` for Orpheus/Kokoro and `44100` for Cartesia
- The WebSocket API accepts query parameters or runtime updates via `tts_session.updated`

### List Available Voices

```python
from together import Together

client = Together()
response = client.audio.voices.list()

for model_voices in response.data:
    print(f"Model: {model_voices.model}")
    for voice in model_voices.voices:
        print(f"  - {voice.name}")
```

```bash
curl -X GET "https://api.together.ai/v1/voices?model=canopylabs/orpheus-3b-0.1-ft" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

See [references/tts-models.md](references/tts-models.md) for the current model table, parameter details, WebSocket
events, and voice lists.

## STT Quick Start

### Transcribe Audio

```python
from together import Together

client = Together()

response = client.audio.transcriptions.create(
    file="meeting_recording.mp3",
    model="openai/whisper-large-v3",
    language="en",
    response_format="json",
)
print(response.text)
```

```typescript
import Together from "together-ai";
import { readFileSync } from "fs";

const client = new Together();
const audioBuffer = readFileSync("meeting_recording.mp3");
const audioFile = new File([audioBuffer], "meeting_recording.mp3", {
  type: "audio/mpeg",
});

const response = await client.audio.transcriptions.create({
  file: audioFile,
  model: "openai/whisper-large-v3",
  language: "en",
  response_format: "json",
});

console.log(response.text);
```

```bash
curl -X POST "https://api.together.ai/v1/audio/transcriptions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F model="openai/whisper-large-v3" \
  -F language="en" \
  -F file=@meeting_recording.mp3
```

### Translate Audio

The guide examples frame translation as speech-to-English. The `/audio/translations` reference also documents an
optional `language` parameter whose default is `en`.

```python
response = client.audio.translations.create(
    file="french_audio.mp3",
    model="openai/whisper-large-v3",
)
print(response.text)
```

```typescript
const translation = await client.audio.translations.create({
  file: audioFile,
  model: "openai/whisper-large-v3",
});

console.log(translation.text);
```

```bash
curl -X POST "https://api.together.ai/v1/audio/translations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F model="openai/whisper-large-v3" \
  -F file=@foreign_audio.mp3
```

### Speaker Diarization

Use `response_format="verbose_json"` and `diarize=true` to identify speaker turns.

```python
response = client.audio.transcriptions.create(
    file="meeting.mp3",
    model="openai/whisper-large-v3",
    response_format="verbose_json",
    diarize=True,
    min_speakers=1,
    max_speakers=5,
)

for segment in response.speaker_segments:
    print(f"[{segment.speaker_id}] {segment.start:.1f}s-{segment.end:.1f}s: {segment.text}")
```

### Word-level Timestamps

```python
response = client.audio.transcriptions.create(
    file="audio.mp3",
    model="openai/whisper-large-v3",
    response_format="verbose_json",
    timestamp_granularities="word",
)

for word in response.words:
    print(f"{word.word}: {word.start:.2f}s-{word.end:.2f}s")
```

### Realtime STT (WebSocket)

Use the realtime WebSocket API for incremental transcription.

```json
{"type": "input_audio_buffer.append", "audio": "<base64-encoded-pcm-s16le-16k-chunk>"}
{"type": "input_audio_buffer.commit"}
```

Server events:

```json
{"type": "session.created", "session": {"model": "openai/whisper-large-v3"}}
{"type": "conversation.item.input_audio_transcription.delta", "delta": "partial text"}
{"type": "conversation.item.input_audio_transcription.completed", "transcript": "final text"}
{"type": "conversation.item.input_audio_transcription.failed", "error": {"message": "error"}}
```

Current docs show:
- connection URL `wss://api.together.ai/v1/realtime?model={model}&input_audio_format=pcm_s16le_16000`
- `Authorization: Bearer ...` authentication
- guide examples that also include `OpenAI-Beta: realtime=v1` or equivalent WebSocket subprotocols in some clients

## STT Models

The current guide-level STT model catalog includes:

| Model | API String | Access | Capabilities |
|-------|-----------|--------|--------------|
| Whisper Large v3 | `openai/whisper-large-v3` | Serverless | Realtime, translation, diarization |
| Voxtral Mini 3B | `mistralai/Voxtral-Mini-3B-2507` | Serverless | Transcription |
| Deepgram Flux | `deepgram/deepgram-flux` | Dedicated / Reserved | Realtime |
| Deepgram Nova 3 | `deepgram/deepgram-nova-3` | Dedicated / Reserved | Transcription |
| Deepgram Nova 3 Multilingual | `deepgram/deepgram-nova-3-multilingual` | Dedicated / Reserved | Transcription |
| Parakeet TDT 0.6B v3 | `nvidia/parakeet-tdt-0.6b-v3` | Serverless | Realtime, diarization |

## STT Parameters

Supported input formats: `.wav`, `.mp3`, `.m4a`, `.webm`, `.flac`

| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | string / file / URL / path | Audio input |
| `model` | string | STT model identifier |
| `language` | string | ISO 639-1 language code; transcription also supports `auto` |
| `prompt` | string | Optional text to bias decoding |
| `response_format` | string | `json` or `verbose_json` |
| `temperature` | float | `0.0` to `1.0` |
| `timestamp_granularities` | string or array | `segment` and/or `word` for `verbose_json` |
| `diarize` | bool | Enable speaker diarization |
| `min_speakers` / `max_speakers` | int | Speaker-count hints for diarization |

## Delivery Guide

- **REST TTS/STT**: complete files, simplest integration
- **Streaming HTTP TTS**: lower time-to-first-byte while keeping HTTP semantics
- **Realtime WebSocket**: interactive assistants, phone agents, live captioning, and conversational voice apps

## Resources

- **TTS reference**: See [references/tts-models.md](references/tts-models.md)
- **STT reference**: See [references/stt-models.md](references/stt-models.md)
- **Python TTS script**: See [scripts/tts_generate.py](scripts/tts_generate.py) -- REST, streaming, raw bytes, voices (v2 SDK)
- **Python realtime TTS script**: See [scripts/tts_websocket.py](scripts/tts_websocket.py) -- realtime WebSocket TTS
- **TypeScript TTS script**: See [scripts/tts_generate.ts](scripts/tts_generate.ts) -- REST and streaming TTS
- **Python STT script**: See [scripts/stt_transcribe.py](scripts/stt_transcribe.py) -- transcribe, translate, diarize, timestamps (v2 SDK)
- **Python realtime STT script**: See [scripts/stt_realtime.py](scripts/stt_realtime.py) -- realtime WebSocket transcription
- **TypeScript STT script**: See [scripts/stt_transcribe.ts](scripts/stt_transcribe.ts) -- transcribe, translate, diarize, timestamps
- **Official guide**: [Text-to-Speech](https://docs.together.ai/docs/text-to-speech)
- **Official guide**: [Speech-to-Text](https://docs.together.ai/docs/speech-to-text)
- **API reference**: [TTS REST](https://docs.together.ai/reference/audio-speech)
- **API reference**: [TTS WebSocket](https://docs.together.ai/reference/audio-speech-websocket)
- **API reference**: [Audio Transcriptions](https://docs.together.ai/reference/audio-transcriptions)
- **API reference**: [Audio Translations](https://docs.together.ai/reference/audio-translations)
- **API reference**: [Realtime Audio Transcriptions](https://docs.together.ai/reference/audio-transcriptions-realtime)
