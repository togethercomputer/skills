# Together AI: Audio

Use Together AI audio APIs for speech synthesis and speech recognition -- REST, streaming, and realtime WebSocket TTS, plus transcription, translation, diarization, and timestamps.

- text-to-speech generation
- streaming or realtime voice output
- speech-to-text transcription
- translation, diarization, and timestamps
- live captioning and realtime transcription

## Use this guide for

- Generate spoken audio from text
- Transcribe uploaded audio files or URLs
- Add realtime voice or captioning to an app
- Extract speaker segments or word timings

## Do not use this guide for

- text-only generation -> `domains/chat-completions.md`
- or `domains/images.md` for visual generation workflows -> `domains/video.md`
- only when the audio model itself must be hosted on dedicated infrastructure -> `domains/dedicated-model-inference.md`

## Workflow

1. Confirm whether the task is TTS or STT.
2. Choose REST, streaming, or realtime transport based on latency and interaction needs.
3. Pick the model and response format from the relevant reference file.
4. Start from the matching script instead of rebuilding the request contract from memory.
5. For Python STT uploads, open audio files in binary mode and pass the file handle rather than a bare path string.

## Open next

- **REST TTS or streaming TTS**
  - Read [references/audio/tts-models.md](references/audio/tts-models.md)
  - Start with [scripts/audio/tts_generate.py](scripts/audio/tts_generate.py) or [scripts/audio/tts_generate.ts](scripts/audio/tts_generate.ts)
- **Realtime TTS over WebSocket**
  - Read [references/audio/tts-models.md](references/audio/tts-models.md)
  - Start with [scripts/audio/tts_websocket.py](scripts/audio/tts_websocket.py)
- **File transcription, translation, diarization, or timestamps**
  - Read [references/audio/stt-models.md](references/audio/stt-models.md)
  - Start with [scripts/audio/stt_transcribe.py](scripts/audio/stt_transcribe.py) or [scripts/audio/stt_transcribe.ts](scripts/audio/stt_transcribe.ts)
- **Realtime STT**
  - Read [references/audio/stt-models.md](references/audio/stt-models.md)
  - Start with [scripts/audio/stt_realtime.py](scripts/audio/stt_realtime.py)

## Rules

- Use `client.audio.speech.create()` for TTS.
- REST TTS returns a `BinaryAPIResponse`; call `response.write_to_file(path)` to save it. Do NOT use `stream_to_file` (it does not exist on this object).
- Streaming TTS (`stream=True`) returns a `Stream` of `AudioSpeechStreamChunk` objects. Iterate chunks, check `chunk.type`, and decode `base64.b64decode(chunk.delta)` for audio data. There is no file-writing helper on the stream object.
- Use `client.audio.transcriptions.create()` for transcription and `client.audio.translations.create()` for translation.
- Batch transcription and translation share hard limits: 80 MB direct upload, 1 GB URL-fetch, 4 hours of audio per request. For larger payloads, pass a public HTTPS URL on `file=`; for longer audio, split into ≤ 4 h chunks. See the Limits section of [references/audio/stt-models.md](references/audio/stt-models.md).
- Realtime APIs require audio-format discipline; confirm PCM expectations before streaming bytes.
- Diarization and word timestamps change response shape; code for the richer verbose output explicitly.

## Docs

- [Text-to-Speech](https://docs.together.ai/docs/text-to-speech)
- [Speech-to-Text](https://docs.together.ai/docs/speech-to-text)
- [TTS REST API](https://docs.together.ai/reference/audio-speech)
- [TTS WebSocket API](https://docs.together.ai/reference/audio-speech-websocket)
- [Audio Transcriptions API](https://docs.together.ai/reference/audio-transcriptions)
- [Audio Translations API](https://docs.together.ai/reference/audio-translations)
- [Realtime Audio Transcriptions API](https://docs.together.ai/reference/audio-transcriptions-realtime)
