---
name: together-audio
description: "Use this skill for Together AI audio workflows: text-to-speech over REST, streaming, or realtime WebSocket APIs, plus speech-to-text transcription, translation, diarization, timestamps, and live transcription. Reach for it whenever the user needs audio in or audio out on Together AI rather than generic chat generation, image or video creation, or model training."
---

# Together Audio

## Overview

Use Together AI audio APIs for:

- text-to-speech generation
- streaming or realtime voice output
- speech-to-text transcription
- translation, diarization, and timestamps
- live captioning and realtime transcription

## When This Skill Wins

- Generate spoken audio from text
- Transcribe uploaded audio files or URLs
- Add realtime voice or captioning to an app
- Extract speaker segments or word timings

## Hand Off To Another Skill

- Use `together-chat-completions` for text-only generation
- Use `together-video` or `together-images` for visual generation workflows
- Use `together-dedicated-endpoints` only when the audio model itself must be hosted on dedicated infrastructure

## Quick Routing

- **REST TTS or streaming TTS**
  - Read [references/tts-models.md](references/tts-models.md)
  - Start with [scripts/tts_generate.py](scripts/tts_generate.py) or [scripts/tts_generate.ts](scripts/tts_generate.ts)
- **Realtime TTS over WebSocket**
  - Read [references/tts-models.md](references/tts-models.md)
  - Start with [scripts/tts_websocket.py](scripts/tts_websocket.py)
- **File transcription, translation, diarization, or timestamps**
  - Read [references/stt-models.md](references/stt-models.md)
  - Start with [scripts/stt_transcribe.py](scripts/stt_transcribe.py) or [scripts/stt_transcribe.ts](scripts/stt_transcribe.ts)
- **Realtime STT**
  - Read [references/stt-models.md](references/stt-models.md)
  - Start with [scripts/stt_realtime.py](scripts/stt_realtime.py)

## Workflow

1. Confirm whether the task is TTS or STT.
2. Choose REST, streaming, or realtime transport based on latency and interaction needs.
3. Pick the model and response format from the relevant reference file.
4. Start from the matching script instead of rebuilding the request contract from memory.
5. For Python STT uploads, open audio files in binary mode and pass the file handle rather than a bare path string.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Use `client.audio.speech.create()` for TTS.
- REST TTS returns a `BinaryAPIResponse`; call `response.write_to_file(path)` to save it. Do NOT use `stream_to_file` (it does not exist on this object).
- Streaming TTS (`stream=True`) returns a `Stream` of `AudioSpeechStreamChunk` objects. Iterate chunks, check `chunk.type`, and decode `base64.b64decode(chunk.delta)` for audio data. There is no file-writing helper on the stream object.
- Use `client.audio.transcriptions.create()` for transcription and `client.audio.translations.create()` for translation.
- Realtime APIs require audio-format discipline; confirm PCM expectations before streaming bytes.
- Diarization and word timestamps change response shape; code for the richer verbose output explicitly.

## Resource Map

- **TTS reference**: [references/tts-models.md](references/tts-models.md)
- **STT reference**: [references/stt-models.md](references/stt-models.md)
- **Python TTS workflow**: [scripts/tts_generate.py](scripts/tts_generate.py)
- **TypeScript TTS workflow**: [scripts/tts_generate.ts](scripts/tts_generate.ts)
- **Python realtime TTS workflow**: [scripts/tts_websocket.py](scripts/tts_websocket.py)
- **Python STT workflow**: [scripts/stt_transcribe.py](scripts/stt_transcribe.py)
- **TypeScript STT workflow**: [scripts/stt_transcribe.ts](scripts/stt_transcribe.ts)
- **Python realtime STT workflow**: [scripts/stt_realtime.py](scripts/stt_realtime.py)

## Official Docs

- [Text-to-Speech](https://docs.together.ai/docs/text-to-speech)
- [Speech-to-Text](https://docs.together.ai/docs/speech-to-text)
- [TTS REST API](https://docs.together.ai/reference/audio-speech)
- [TTS WebSocket API](https://docs.together.ai/reference/audio-speech-websocket)
- [Audio Transcriptions API](https://docs.together.ai/reference/audio-transcriptions)
- [Audio Translations API](https://docs.together.ai/reference/audio-translations)
- [Realtime Audio Transcriptions API](https://docs.together.ai/reference/audio-transcriptions-realtime)
