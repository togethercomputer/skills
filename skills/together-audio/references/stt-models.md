# STT Models & Transcription Reference
## Contents

- [Model Catalog](#model-catalog)
- [Supported Input Formats](#supported-input-formats)
- [Limits](#limits)
- [Audio Transcriptions](#audio-transcriptions)
- [Audio Translations](#audio-translations)
- [Realtime Transcription (WebSocket)](#realtime-transcription)
- [Response Formats](#response-formats)
- [Errors and Troubleshooting](#errors-and-troubleshooting)
- [Common Workflows](#common-workflows)
- [Async Support](#async-support)


## Model Catalog

These models are current in the latest speech-to-text guide and are not listed in the current deprecation history.

| Model | API String | Access | Capabilities |
|-------|-----------|--------|--------------|
| Whisper Large v3 | `openai/whisper-large-v3` | Serverless | Realtime, translation, diarization |
| Deepgram Flux | `deepgram/deepgram-flux` | Dedicated / Reserved | Realtime |
| Deepgram Nova 3 | `deepgram/deepgram-nova-3` | Dedicated / Reserved | Transcription |
| Deepgram Nova 3 Multilingual | `deepgram/deepgram-nova-3-multilingual` | Dedicated / Reserved | Transcription |
| Parakeet TDT 0.6B v3 | `nvidia/parakeet-tdt-0.6b-v3` | Serverless | Realtime, diarization |
| Nemotron 3 ASR Streaming 0.6B | `nvidia/nemotron-3-asr-streaming-0.6b` | Serverless | Streaming transcription |
| Nemotron 3.5 ASR Streaming 0.6B | `nvidia/nemotron-3.5-asr-streaming-0.6b` | Serverless | Streaming transcription |

Notes:
- The `/audio/transcriptions` and `/audio/translations` reference schemas currently enumerate
  `openai/whisper-large-v3` in the request body.
- The broader guide model catalog also includes Parakeet and dedicated-endpoint Deepgram models.

## Supported Input Formats

The guide and reference both list:
- `.wav` (`audio/wav`)
- `.mp3` (`audio/mpeg`)
- `.m4a` (`audio/mp4`)
- `.webm` (`audio/webm`)
- `.flac` (`audio/flac`)

## Limits

Both `/v1/audio/transcriptions` and `/v1/audio/translations` enforce the same caps.

| Limit | Value | Notes |
|-------|-------|-------|
| Max file size (direct upload) | 500 MB | Requests above this are rejected at the edge with `HTTP 413 Payload Too Large`. |
| Max file size (URL fetch) | 1 GB | When you submit an HTTPS URL on the `file` field instead of binary, the server downloads up to 1 GB. Larger downloads fail with `400 file_too_large`. |
| Max audio duration | 4 hours per request | Longer audio is rejected with `400 audio_too_long`. Split into ≤ 4 h segments and submit separately. |

Tips:
- For payloads larger than 500 MB, host the file at a public HTTPS URL and pass that URL as the `file` field — the 500 MB edge cap only applies to direct uploads.
- For audio longer than 4 hours, split into ≤ 4 h chunks before submitting.
- Real-time/streaming transports are unaffected by these batch upload limits.

## Audio Transcriptions

Use `/v1/audio/transcriptions` to transcribe speech into text in the same language as the source audio.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | string / file / path / URL | Yes | Audio file upload or public HTTP/HTTPS URL |
| `model` | string | No | Defaults to `openai/whisper-large-v3` in the reference |
| `language` | string | No | ISO 639-1 code; `auto` enables auto-detection |
| `prompt` | string | No | Optional text to bias decoding |
| `response_format` | string | No | `json` or `verbose_json` |
| `temperature` | float | No | `0.0` to `1.0` |
| `timestamp_granularities` | string or array | No | `segment` and/or `word`; only used with `verbose_json` |
| `diarize` | bool | No | Enable speaker diarization |
| `min_speakers` | int | No | Minimum expected speakers |
| `max_speakers` | int | No | Maximum expected speakers |

Language examples called out in the guide:
- `en` -- English
- `es` -- Spanish
- `fr` -- French
- `de` -- German
- `ja` -- Japanese
- `zh` -- Chinese
- `auto` -- auto-detect

### Input Methods

The guide shows all of these as valid Python inputs:

```python
from pathlib import Path

file="/path/to/audio.mp3"
file=Path("recordings/interview.wav")
file="https://example.com/audio.mp3"
file=open("audio.mp3", "rb")
```

## Audio Translations

Use `/v1/audio/translations` to translate spoken audio. The guide frames this as translation to English. The current
reference also documents an optional `language` parameter whose default is `en`.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | string / file / path / URL | Yes | Audio file upload or public HTTP/HTTPS URL |
| `model` | string | No | Defaults to `openai/whisper-large-v3` |
| `language` | string | No | Target output language; default `en` |
| `prompt` | string | No | Optional text to bias decoding |
| `response_format` | string | No | `json` or `verbose_json` |
| `temperature` | float | No | `0.0` to `1.0` |
| `timestamp_granularities` | string or array | No | `segment` and/or `word` for `verbose_json` |

## Realtime Transcription (WebSocket)

Use the realtime API when you need incremental transcription.

Connection URL:

```text
wss://api.together.ai/v1/realtime?model={model}&input_audio_format=pcm_s16le_16000
```

Audio requirements:
- PCM signed 16-bit little-endian
- 16 kHz sample rate
- base64-encoded in `input_audio_buffer.append`

### Authentication

The reference documents Bearer auth. The speech-to-text guide also shows raw websocket examples using:
- `Authorization: Bearer YOUR_API_KEY`
- `OpenAI-Beta: realtime=v1`

Some websocket client examples in the guide also use the `realtime`, `openai-insecure-api-key.*`, and
`openai-beta.realtime-v1` subprotocol pattern.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Realtime STT model such as `openai/whisper-large-v3` |
| `input_audio_format` | string | Yes | Use `pcm_s16le_16000` |

### Client Events

```json
{"type": "input_audio_buffer.append", "audio": "<base64-encoded-pcm-chunk>"}
{"type": "input_audio_buffer.commit"}
```

### Server Events

```json
{"type": "session.created", "session": {"model": "openai/whisper-large-v3"}}
{"type": "conversation.item.input_audio_transcription.delta", "delta": "The quick brown"}
{"type": "conversation.item.input_audio_transcription.completed", "transcript": "The quick brown fox jumps over the lazy dog"}
{"type": "conversation.item.input_audio_transcription.failed", "error": {"message": "Error description"}}
```

Delta semantics:
- `conversation.item.input_audio_transcription.delta` is an interim result
- each delta can replace the previous delta
- `conversation.item.input_audio_transcription.completed` is the finalized text chunk

## Response Formats

### JSON

```json
{"text": "Hello, this is a test recording."}
```

### Verbose JSON

`verbose_json` can include:
- `text`
- `language`
- `duration`
- `segments`
- `words`
- `speaker_segments`

Segment example:

```json
{"start": 0.11, "end": 10.85, "text": "..."}
```

Word example:

```json
{"word": "Hello", "start": 0.00, "end": 0.36}
```

Speaker segment example:

```json
{
  "speaker_id": "SPEAKER_01",
  "start": 6.268,
  "end": 30.776,
  "text": "...",
  "words": [{"word": "Hello", "start": 6.268, "end": 11.314, "speaker_id": "SPEAKER_01"}]
}
```

## Errors and Troubleshooting

`/v1/audio/transcriptions` and `/v1/audio/translations` share the same code path and return the same error codes.

| Response | Meaning | Recommended action |
|----------|---------|--------------------|
| `400 audio_too_long` | Audio duration exceeds the 4 hour cap. | Split the file into ≤ 4 h segments and submit separately. |
| `400 file_too_large` | A URL-fetched audio download exceeded the 1 GB server-side cap. | Compress the source, or split into smaller files. |
| `400 unsupported_format` | The audio container or codec could not be decoded. | Re-encode to a supported format. Run `ffprobe` on the file to confirm it is valid audio. |
| `400 invalid_params` | Request parameters failed validation. | Check the API reference for the endpoint. |
| `413 Payload Too Large` | A direct upload exceeded the 500 MB edge limit. | Submit the file via an HTTPS URL on the `file` field instead, or split the file. The 413 response is plain HTML, not JSON. |
| `429` | Rate limit exceeded. | See serverless rate limits. |
| `500 processing_failed` | Internal decode failure after the file was accepted. | Verify the file is valid audio with `ffprobe`. If it is, contact Together support with the response `id`. |

## Common Workflows

### Basic Transcription

```python
from together import Together

client = Together()
with open("meeting_recording.mp3", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        file=audio_file,
        model="openai/whisper-large-v3",
        language="en",
        response_format="json",
    )
print(response.text)
```

### Translation

```python
with open("french_audio.mp3", "rb") as audio_file:
    response = client.audio.translations.create(
        file=audio_file,
        model="openai/whisper-large-v3",
    )
print(response.text)
```

### Diarization

```python
with open("meeting.mp3", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        file=audio_file,
        model="openai/whisper-large-v3",
        response_format="verbose_json",
        diarize=True,
        min_speakers=1,
        max_speakers=5,
    )
print(response.speaker_segments)
```

### Word-level Timestamps

```python
with open("audio.mp3", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        file=audio_file,
        model="openai/whisper-large-v3",
        response_format="verbose_json",
        timestamp_granularities="word",
    )
for word in response.words:
    print(f"{word.word}: {word.start:.2f}s-{word.end:.2f}s")
```

## Async Support

```python
import asyncio
from together import AsyncTogether


async def transcribe_audio() -> str:
    client = AsyncTogether()
    with open("audio.mp3", "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            file=audio_file,
            model="openai/whisper-large-v3",
            language="en",
        )
    return response.text


print(asyncio.run(transcribe_audio()))
```
