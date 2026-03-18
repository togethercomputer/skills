---
name: together-audio
description: Text-to-speech (TTS) and speech-to-text (STT) via Together AI. TTS models include Orpheus, Kokoro, Cartesia Sonic with REST, streaming, and WebSocket support. STT models include Whisper, Voxtral, and Parakeet with transcription, translation, diarization, and real-time WebSocket streaming. Use when users need voice synthesis, audio generation, speech recognition, transcription, translation, TTS, STT, or real-time voice applications.
---

# Together Audio (TTS & STT)

## Overview

Together AI provides text-to-speech and speech-to-text capabilities.

**TTS** -- Generate speech from text via REST, streaming, or WebSocket:
- Endpoint: `/v1/audio/speech`
- WebSocket: `wss://api.together.xyz/v1/audio/speech/websocket`

**STT** -- Transcribe and translate audio to text:
- Transcription: `/v1/audio/transcriptions`
- Translation: `/v1/audio/translations`
- Real-time WebSocket: `wss://api.together.ai/v1/realtime`

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together
```

```shell
# or with pip
pip install together
```

```shell
# TypeScript / JavaScript
npm install together-ai
```

Set your API key:

```shell
export TOGETHER_API_KEY=<your-api-key>
```

## TTS Quick Start

### Basic Speech Generation (REST)

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
import { pipeline } from "stream/promises";

const client = new Together();

const response = await client.audio.speech.create({
  model: "canopylabs/orpheus-3b-0.1-ft",
  input: "Today is a wonderful day to build something people love!",
  voice: "tara",
  response_format: "mp3",
});

const writeStream = createWriteStream("speech.mp3");
if (response.body) {
  await pipeline(response.body, writeStream);
}
```

```shell
curl -X POST "https://api.together.xyz/v1/audio/speech" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"canopylabs/orpheus-3b-0.1-ft","input":"Hello world","voice":"tara","response_format":"mp3"}' \
  --output speech.mp3
```

### Streaming Audio (Low Latency)

Streaming requires `response_format="raw"` with a PCM encoding.

```python
response = client.audio.speech.create(
    model="canopylabs/orpheus-3b-0.1-ft",
    input="The quick brown fox jumps over the lazy dog",
    voice="tara",
    stream=True,
    response_format="raw",
    response_encoding="pcm_s16le",
)
response.stream_to_file("speech.wav", response_format="wav")
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
});

const chunks: any[] = [];
for await (const chunk of response) {
  chunks.push(chunk);
}
console.log("Streaming complete!");
```

```shell
curl -X POST "https://api.together.xyz/v1/audio/speech" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"canopylabs/orpheus-3b-0.1-ft","input":"The quick brown fox","voice":"tara","stream":true}' \
  --output speech_stream.raw
```

### WebSocket (Lowest Latency)

Orpheus and Kokoro support real-time WebSocket streaming for interactive applications.

```python
import asyncio, websockets, json, base64, os

async def generate_speech():
    api_key = os.environ["TOGETHER_API_KEY"]
    url = "wss://api.together.ai/v1/audio/speech/websocket?model=hexgrad/Kokoro-82M&voice=af_alloy"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with websockets.connect(url, additional_headers=headers) as ws:
        session = json.loads(await ws.recv())
        print(f"Session: {session['session']['id']}")

        await ws.send(json.dumps({"type": "input_text_buffer.append", "text": "Hello, world!"}))
        await ws.send(json.dumps({"type": "input_text_buffer.commit"}))

        audio_data = bytearray()
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "conversation.item.audio_output.delta":
                audio_data.extend(base64.b64decode(data["delta"]))
            elif data["type"] == "conversation.item.audio_output.done":
                break

        with open("speech_ws.wav", "wb") as f:
            f.write(audio_data)

asyncio.run(generate_speech())
```

## TTS Models

| Model | API String | Endpoints | Price |
|-------|-----------|-----------|-------|
| Orpheus 3B | `canopylabs/orpheus-3b-0.1-ft` | REST, Streaming, WebSocket | $15/1M chars |
| Kokoro | `hexgrad/Kokoro-82M` | REST, Streaming, WebSocket | $4/1M chars |
| Cartesia Sonic 3 | `cartesia/sonic-3` | REST | - |
| Cartesia Sonic 2 | `cartesia/sonic-2` | REST | $65/1M chars |
| Deepgram Aura 2* | `deepgram/deepgram-aura-2` | REST, Streaming, WebSocket | DE only |
| Rime Arcana v3 Turbo* | `rime-labs/rime-arcana-v3-turbo` | REST, Streaming, WebSocket | DE only |
| MiniMax Speech 2.6* | `minimax/speech-2.6-turbo` | REST, Streaming, WebSocket | DE only |

*Dedicated Endpoint only

## TTS Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | string | TTS model (required) | - |
| `input` | string | Text to synthesize (required) | - |
| `voice` | string | Voice ID (required) | - |
| `response_format` | string | `mp3`, `wav`, `raw`, `mulaw` | `wav` |
| `stream` | bool | Enable streaming (`raw` format only) | false |
| `response_encoding` | string | `pcm_f32le`, `pcm_s16le`, `pcm_mulaw`, `pcm_alaw` for raw | `pcm_f32le` |
| `language` | string | Input text language: en, de, fr, es, hi, it, ja, ko, nl, pl, pt, ru, sv, tr, zh | `en` |
| `sample_rate` | int | Audio sample rate in Hz | Model default |

### List Available Voices

```python
response = client.audio.voices.list()
for model_voices in response.data:
    print(f"Model: {model_voices.model}")
    for voice in model_voices.voices:
        print(f"  - {voice.name}")
```

```shell
curl -X GET "https://api.together.xyz/v1/voices?model=canopylabs/orpheus-3b-0.1-ft" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

**Key voices:** Orpheus: `tara`, `leah`, `jess`, `leo`, `dan`, `mia`, `zac`, `zoe`. Kokoro: `af_alloy`, `af_bella`, `am_adam`, `am_echo`. See [references/tts-models.md](references/tts-models.md) for complete voice lists.

## STT Quick Start

### Transcribe Audio

```python
from together import Together
client = Together()

response = client.audio.transcriptions.create(
    model="openai/whisper-large-v3",
    file=open("audio.mp3", "rb"),
)
print(response.text)
```

```typescript
import Together from "together-ai";
import { readFileSync } from "fs";

const client = new Together();

const audioBuffer = readFileSync("audio.mp3");
const audioFile = new File([audioBuffer], "audio.mp3", { type: "audio/mpeg" });

const response = await client.audio.transcriptions.create({
  model: "openai/whisper-large-v3",
  file: audioFile,
});
console.log(response.text);
```

```shell
curl -X POST "https://api.together.xyz/v1/audio/transcriptions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F model="openai/whisper-large-v3" \
  -F file=@audio.mp3
```

### Transcribe with Timestamps

```python
response = client.audio.transcriptions.create(
    file="audio.mp3",
    model="openai/whisper-large-v3",
    response_format="verbose_json",
    timestamp_granularities="word",
)
print(f"Duration: {response.duration}s")
for word in response.words:
    print(f"  [{word.start:.2f}s - {word.end:.2f}s] {word.word}")
```

### Speaker Diarization

Identify who spoke when (Whisper and Parakeet):

```python
response = client.audio.transcriptions.create(
    file=open("meeting.mp3", "rb"),
    model="openai/whisper-large-v3",
    response_format="verbose_json",
    diarize="true",
    min_speakers=2,
    max_speakers=5,
)
for segment in response.speaker_segments:
    print(f"  [{segment.speaker_id}] ({segment.start:.1f}s-{segment.end:.1f}s): {segment.text}")
```

```typescript
const response = await client.audio.transcriptions.create({
  file: audioFile,
  model: "openai/whisper-large-v3",
  diarize: true,
});
console.log(response.speaker_segments);
```

### Translate to English

Convert speech from any language to English text:

```python
response = client.audio.translations.create(
    file=open("foreign_audio.mp3", "rb"),
    model="openai/whisper-large-v3",
)
print(response.text)  # English translation
```

```typescript
const translation = await client.audio.translations.create({
  file: audioFile,
  model: "openai/whisper-large-v3",
});
console.log(translation.text);
```

```shell
curl -X POST "https://api.together.xyz/v1/audio/translations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F model="openai/whisper-large-v3" \
  -F file=@foreign_audio.mp3
```

### Real-time STT (WebSocket)

Stream audio for live transcription via WebSocket. Sends PCM audio chunks and receives partial/final transcription events.

URL: `wss://api.together.ai/v1/realtime?model=openai/whisper-large-v3&input_audio_format=pcm_s16le_16000`

**Client to Server:**
```json
{"type": "input_audio_buffer.append", "audio": "<base64-pcm-chunk>"}
{"type": "input_audio_buffer.commit"}
```

**Server to Client:**
```json
{"type": "conversation.item.input_audio_transcription.delta", "delta": "partial text"}
{"type": "conversation.item.input_audio_transcription.completed", "transcript": "final text"}
```

## STT Models

| Model | API String | Features |
|-------|-----------|----------|
| Whisper Large v3 | `openai/whisper-large-v3` | Transcription, Translation, Diarization, Real-time |
| Voxtral Mini 3B | `mistralai/Voxtral-Mini-3B-2507` | Transcription |
| Parakeet TDT 0.6B v3 | `nvidia/parakeet-tdt-0.6b-v3` | Transcription, Diarization, Real-time |

Supported audio formats: `.wav`, `.mp3`, `.m4a`, `.webm`, `.flac`

## STT Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | string/file | Yes | Audio file path, URL, or file object |
| `model` | string | Yes | STT model identifier |
| `language` | string | No | ISO 639-1 code (`en`, `es`, `fr`, `auto`) |
| `response_format` | string | No | `json` (default) or `verbose_json` |
| `prompt` | string | No | Custom context for domain-specific accuracy |
| `temperature` | float | No | 0.0 (deterministic) to 1.0 |
| `timestamp_granularities` | string | No | `segment` or `word` |
| `diarize` | bool | No | Enable speaker identification |
| `min_speakers` / `max_speakers` | int | No | Speaker count hints |

## Delivery Method Guide

- **REST**: Batch processing, complete audio files
- **Streaming**: Real-time apps where time-to-first-byte matters
- **WebSocket**: Interactive/conversational apps, lowest latency

## Resources

- **Complete voice lists**: See [references/tts-models.md](references/tts-models.md)
- **STT details**: See [references/stt-models.md](references/stt-models.md)
- **TTS script**: See [scripts/tts_generate.py](scripts/tts_generate.py) -- REST, streaming, and WebSocket TTS (v2 SDK)
- **TTS script (TypeScript)**: See [scripts/tts_generate.ts](scripts/tts_generate.ts) -- REST and streaming TTS (TypeScript SDK)
- **STT script**: See [scripts/stt_transcribe.py](scripts/stt_transcribe.py) -- transcribe, translate, diarize with CLI flags (v2 SDK)
- **STT script (TypeScript)**: See [scripts/stt_transcribe.ts](scripts/stt_transcribe.ts) -- transcribe, translate, timestamps, diarize (TypeScript SDK)
- **Official docs**: [Text-to-Speech](https://docs.together.ai/docs/text-to-speech)
- **Official docs**: [Speech-to-Text](https://docs.together.ai/docs/speech-to-text)
- **API reference**: [TTS API](https://docs.together.ai/reference/audio-speech)
- **API reference**: [STT API](https://docs.together.ai/reference/audio-transcriptions)
