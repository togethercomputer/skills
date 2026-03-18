# STT Models & Transcription Reference

## Models

| Model | API String | Features |
|-------|-----------|----------|
| Whisper Large v3 | `openai/whisper-large-v3` | Transcription, Translation, Diarization, Real-time WebSocket |
| Voxtral Mini 3B | `mistralai/Voxtral-Mini-3B-2507` | Transcription |
| Parakeet TDT 0.6B v3 | `nvidia/parakeet-tdt-0.6b-v3` | Transcription, Diarization, Real-time WebSocket |

## Supported Audio Formats
`.wav`, `.mp3`, `.m4a`, `.webm`, `.flac`

## Transcription Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | string/file | Yes | Audio file (path, URL, or file object) |
| `model` | string | Yes | STT model identifier |
| `language` | string | No | ISO 639-1 code: `en`, `es`, `fr`, `de`, `ja`, `zh`, `auto` |
| `response_format` | string | No | `json` (default) or `verbose_json` |
| `prompt` | string | No | Custom prompt for domain-specific accuracy |
| `temperature` | float | No | 0.0 (deterministic) to 1.0 (creative) |
| `timestamp_granularities` | string | No | `segment` or `word` |
| `diarize` | bool | No | Enable speaker identification |
| `min_speakers` | int | No | Minimum expected speakers |
| `max_speakers` | int | No | Maximum expected speakers |

## Translation Parameters

Translation converts speech from any language to English text.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | string/file | Yes | Audio file (path, URL, or file object) |
| `model` | string | No | Default: `openai/whisper-large-v3` |
| `language` | string | No | ISO 639-1 target language code |
| `prompt` | string | No | Optional text biasing decoding |
| `response_format` | string | No | `json` (default) or `verbose_json` |
| `temperature` | float | No | 0.0 to 1.0 |
| `timestamp_granularities` | string | No | `segment` or `word` |

## Response Formats

### JSON (Default)
```json
{"text": "Hello, this is a test recording."}
```

### Verbose JSON
Includes `text`, `language`, `duration`, `segments[]`, `words[]`, `speaker_segments[]`

**Segment object:**
```json
{"start": 0.11, "end": 10.85, "text": "..."}
```

**Word object (with `timestamp_granularities="word"`):**
```json
{"word": "Hello", "start": 0.00, "end": 0.36}
```

**Diarization (with `diarize=true`):**
```json
{
  "id": 1,
  "speaker_id": "SPEAKER_01",
  "start": 6.268,
  "end": 30.776,
  "text": "...",
  "words": [{"word": "Hello", "start": 6.268, "end": 11.314, "speaker_id": "SPEAKER_01"}]
}
```

## Real-time WebSocket STT

**URL:** `wss://api.together.ai/v1/realtime?model={model}&input_audio_format=pcm_s16le_16000`

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
```

Audio format: 16-bit PCM, 16kHz sample rate (`pcm_s16le_16000`)

**Client to Server:**
```json
{"type": "input_audio_buffer.append", "audio": "<base64-pcm-chunk>"}
{"type": "input_audio_buffer.commit"}
```

**Server to Client:**

| Event | Description |
|-------|-------------|
| `session.created` | Connection established with session metadata |
| `conversation.item.input_audio_transcription.delta` | Partial transcription (interim result) |
| `conversation.item.input_audio_transcription.completed` | Final transcription |
| `conversation.item.input_audio_transcription.failed` | Transcription error |

## Transcription Examples

### Basic

```python
from together import Together
client = Together()

response = client.audio.transcriptions.create(
    file=open("audio.mp3", "rb"),
    model="openai/whisper-large-v3",
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

### With Timestamps

```python
response = client.audio.transcriptions.create(
    file="audio.mp3",
    model="openai/whisper-large-v3",
    response_format="verbose_json",
    timestamp_granularities="word",
)
for word in response.words:
    print(f"  [{word.start:.2f}s - {word.end:.2f}s] {word.word}")
```

### With Diarization

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

## Translation

Translates speech from any language to English:

```python
response = client.audio.translations.create(
    file=open("foreign_audio.mp3", "rb"),
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

```shell
curl -X POST "https://api.together.xyz/v1/audio/translations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F model="openai/whisper-large-v3" \
  -F file=@foreign_audio.mp3
```

## Input Methods

```python
# Local file path
file="audio.mp3"

# Path object
file=Path("recordings/interview.wav")

# URL
file="https://example.com/audio.mp3"

# File-like object
file=open("audio.mp3", "rb")
```

## Async Support

```python
from together import AsyncTogether

async def transcribe():
    client = AsyncTogether()
    response = await client.audio.transcriptions.create(
        file="audio.mp3",
        model="openai/whisper-large-v3",
    )
    return response.text
```
