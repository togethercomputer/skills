# Together AI: Audio

Text-to-speech (REST, streaming, realtime WebSocket) and speech-to-text (transcription,
translation, diarization, timestamps, realtime). Serverless TTS includes `hexgrad/Kokoro-82M`,
`cartesia/sonic-3`, and `canopylabs/orpheus-3b-0.1-ft`; STT includes
`openai/whisper-large-v3` and `nvidia/parakeet-tdt-0.6b-v3`.

## Workflow

1. Decide TTS or STT, then the transport: REST for files, streaming for low latency, WebSocket
   for live interaction.
2. Pick the model and response format.
3. Start from the matching script.
4. For Python STT uploads, open the file in binary mode and pass the handle, not a path string.

## Rules

- TTS: `client.audio.speech.create()`. REST returns a `BinaryAPIResponse`; save it with
  `response.write_to_file(path)`. There is no `stream_to_file`.
- Streaming TTS (`stream=True`) yields `AudioSpeechStreamChunk` objects: check `chunk.type` and
  decode `base64.b64decode(chunk.delta)`. The stream has no file-writing helper.
- STT: `client.audio.transcriptions.create()` and `client.audio.translations.create()`. Limits:
  80 MB direct upload, 1 GB by URL, 4 hours of audio per request. Pass a public HTTPS URL as
  `file=` for big files; split audio longer than 4 hours.
- Realtime endpoints expect a specific PCM format; confirm sample rate and encoding before
  streaming bytes.
- Diarization and word timestamps change the response shape; parse the verbose output explicitly.
- For a voice agent, test the configuration you ship end to end (STT, model, TTS) with its real
  defaults, not with a test-only override.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/audio/tts_generate.py](scripts/audio/tts_generate.py) (.ts) | 267 | REST and streaming TTS, voices, formats | generating speech |
| [scripts/audio/tts_websocket.py](scripts/audio/tts_websocket.py) | 137 | realtime TTS over WebSocket | live or conversational speech |
| [scripts/audio/stt_transcribe.py](scripts/audio/stt_transcribe.py) (.ts) | 221 | transcription, translation, diarization, timestamps | transcribing files |
| [scripts/audio/stt_realtime.py](scripts/audio/stt_realtime.py) | 125 | realtime STT over WebSocket | live captions or voice input |
| [references/audio/tts-models.md](references/audio/tts-models.md) | 227 | TTS models, REST and streaming parameters, WebSocket protocol, voice lists | choosing a voice or TTS parameter |
| [references/audio/stt-models.md](references/audio/stt-models.md) | 303 | STT models, input formats, limits, response formats, realtime protocol, errors | an STT parameter, limit, or error |

## Docs

- [Text-to-Speech](https://docs.together.ai/docs/text-to-speech)
- [Speech-to-Text](https://docs.together.ai/docs/speech-to-text)
- [TTS REST API](https://docs.together.ai/reference/audio-speech)
- [TTS WebSocket API](https://docs.together.ai/reference/audio-speech-websocket)
- [Audio Transcriptions API](https://docs.together.ai/reference/audio-transcriptions)
- [Audio Translations API](https://docs.together.ai/reference/audio-translations)
- [Realtime Audio Transcriptions API](https://docs.together.ai/reference/audio-transcriptions-realtime)
