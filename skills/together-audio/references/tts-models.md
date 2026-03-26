# TTS Models & Voice Reference
## Contents

- [Model Catalog](#model-catalog)
- [REST Parameters](#rest-parameters)
- [Streaming HTTP](#streaming-http)
- [Realtime WebSocket](#realtime-websocket)
- [Response Formats](#response-formats)
- [Voice Discovery](#voice-discovery)
- [Voice Lists](#voice-lists)


## Model Catalog

These models are current in the latest text-to-speech guide and are not listed in the current deprecation history.

| Model | API String | Access | Endpoints | Pricing / Notes |
|-------|-----------|--------|-----------|-----------------|
| Orpheus 3B | `canopylabs/orpheus-3b-0.1-ft` | Serverless | REST, Streaming, WebSocket | $15 per 1M characters |
| Kokoro | `hexgrad/Kokoro-82M` | Serverless | REST, Streaming, WebSocket | $4 per 1M characters |
| Cartesia Sonic 3 | `cartesia/sonic-3` | Serverless / Dedicated / Reserved | REST | Build Tier 2+ |
| Cartesia Sonic 2 | `cartesia/sonic-2` | Serverless / Dedicated / Reserved | REST | $65 per 1M characters, Build Tier 2+ |
| Cartesia Sonic | `cartesia/sonic` | Serverless | REST | Listed in `/audio/speech` reference enum |
| Deepgram Aura 2 | `deepgram/deepgram-aura-2` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Arcana v3 Turbo | `rime-labs/rime-arcana-v3-turbo` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Arcana v3 | `rime-labs/rime-arcana-v3` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Arcana v2 | `rime-labs/rime-arcana-v2` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Mist v3 (Beta) | `rime-labs/rime-mist-v3` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| Rime Mist v2 | `rime-labs/rime-mist-v2` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |
| MiniMax Speech 2.6 Turbo | `minimax/speech-2.6-turbo` | Dedicated / Reserved | REST, Streaming, WebSocket | Dedicated only |

Notes:
- Orpheus and Kokoro support realtime WebSocket streaming for the lowest-latency TTS flows.
- Cartesia Sonic 2 and Sonic 3 require Build Tier 2 or higher on serverless and are also available on Dedicated and
  Reserved Endpoints.
- The `/audio/speech` API reference currently enumerates `cartesia/sonic`, `hexgrad/Kokoro-82M`, and
  `canopylabs/orpheus-3b-0.1-ft` in the request schema.

## REST Parameters

Use `/v1/audio/speech` for standard HTTP generation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | TTS model identifier |
| `input` | string | Yes | Text to synthesize |
| `voice` | string | Yes | Voice ID |
| `response_format` | string | No | `mp3`, `wav`, `raw`, `mulaw`; MiniMax also supports `opus`, `aac`, `flac` in the guide |
| `sample_rate` | int | No | Output sample rate in Hz |
| `language` | string | No | Input language code such as `en`, `fr`, `es` |
| `alignment` | string | No | `none` or `word` |
| `segment` | string | No | `sentence`, `immediate`, or `never` |
| `response_encoding` | string | No | `pcm_f32le`, `pcm_s16le`, `pcm_mulaw`, `pcm_alaw` |
| `stream` | bool | No | Stream as SSE instead of waiting for the full file |

Current behavior from the docs and reference:
- `response_format` defaults to `wav`
- when `stream=true`, the only supported HTTP `response_format` is `raw`
- `alignment=word` is only supported on streaming requests
- `/audio/speech` documents default sample rates of `24000` for Orpheus/Kokoro and `44100` for `cartesia/sonic`

SDK response types (Python v2):
- Non-streaming: `client.audio.speech.create()` returns a `BinaryAPIResponse`. Save with `response.write_to_file(path)`.
- Streaming (`stream=True`): returns a `Stream[AudioSpeechStreamChunk]`. Iterate chunks, check `chunk.type`, and use `base64.b64decode(chunk.delta)` for `conversation.item.audio_output.delta` events.
- The SDK `create()` method accepts: `model`, `input`, `voice`, `language`, `response_encoding`, `response_format`, `sample_rate`, `stream`. Pass `alignment` and `segment` via `extra_body={"alignment": ..., "segment": ...}`.

## Streaming HTTP

When `stream=true`, the HTTP endpoint returns server-sent events.

Event examples:

```json
data: {"type":"conversation.item.audio_output.delta","item_id":"tts_1","delta":"<base64-encoded-audio>"}
```

```json
data: {"type":"conversation.item.word_timestamps","words":["Hello","world"],"start_seconds":[0.0,0.4],"end_seconds":[0.4,0.8]}
```

```text
data: [DONE]
```

Use streaming HTTP when:
- you want lower time-to-first-byte without moving to raw WebSockets
- you want `conversation.item.word_timestamps` via `alignment=word`
- you are comfortable consuming SSE and decoding audio client-side

## Realtime WebSocket

Connection:

```text
wss://api.together.ai/v1/audio/speech/websocket
```

Authentication:
- `Authorization: Bearer YOUR_API_KEY`
- or `?api_key=YOUR_API_KEY`

The guide and reference document these query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | TTS model identifier |
| `voice` | string | Voice ID |
| `response_format` | string | `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm` |
| `speed` | float | Playback speed, default `1.0` |
| `max_partial_length` | int | Character threshold before forced generation |
| `sample_rate` | int | Output sample rate in Hz |
| `language` | string | Language code such as `en`, `fr`, `es` |
| `alignment` | string | `none` or `word` |
| `segment` | string | `sentence`, `immediate`, or `never` |

You can pass these in the URL or update them later with `tts_session.updated`.

### Client Events

- `input_text_buffer.append` -- append text to the server buffer
- `input_text_buffer.commit` -- force synthesis of buffered text
- `input_text_buffer.clear` -- clear pending buffered text
- `tts_session.updated` -- update voice or other session options

### Server Events

- `session.created` -- initial session metadata
- `conversation.item.input_text.received` -- text acknowledged
- `conversation.item.audio_output.delta` -- base64-encoded audio chunks
- `conversation.item.audio_output.done` -- synthesis finished for an item
- `conversation.item.word_timestamps` -- emitted when `alignment=word`
- `conversation.item.tts.failed` -- error payload

### Audio Format

The reference documents realtime audio deltas as:
- base64-encoded chunks
- WAV / PCM s16le
- 24 kHz default sample rate in the documented examples

If you request `response_format=pcm`, the payload is convenient to save directly as a `.pcm` file.

## Response Formats

| Format | Extension | Description | Notes |
|--------|-----------|-------------|-------|
| `wav` | `.wav` | Uncompressed audio | Standard file output |
| `mp3` | `.mp3` | Compressed audio | Smaller files |
| `raw` | `.pcm` | Raw PCM bytes | Required for HTTP streaming |
| `mulaw` | `.ulaw` | Telephony-friendly μ-law | Useful for phone pipelines |
| `pcm` | `.pcm` | Realtime WebSocket PCM output | WebSocket query parameter |
| `opus` | `.opus` | Compressed audio | WebSocket / MiniMax guide coverage |
| `aac` | `.aac` | Compressed audio | WebSocket / MiniMax guide coverage |
| `flac` | `.flac` | Lossless compressed audio | WebSocket / MiniMax guide coverage |

## Voice Discovery

List voices programmatically:

```python
from together import Together

client = Together()
response = client.audio.voices.list()
for model_voices in response.data:
    print(f"Model: {model_voices.model}")
    for voice in model_voices.voices:
        print(f"  - {voice.name}")
```

Or via cURL:

```bash
curl -X GET "https://api.together.ai/v1/voices?model=canopylabs/orpheus-3b-0.1-ft" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## Voice Lists

### Orpheus

`tara`, `leah`, `jess`, `leo`, `dan`, `mia`, `zac`, `zoe`

### Kokoro

`af_heart`, `af_alloy`, `af_aoede`, `af_bella`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`,
`af_river`, `af_sarah`, `af_sky`, `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`,
`am_michael`, `am_onyx`, `am_puck`, `am_santa`, `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`,
`bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis`, `jf_alpha`, `jf_gongitsune`, `jf_nezumi`,
`jf_tebukuro`, `jm_kumo`, `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`, `zm_yunjian`,
`zm_yunxi`, `zm_yunxia`, `zm_yunyang`, `ef_dora`, `em_alex`, `em_santa`, `ff_siwis`, `hf_alpha`,
`hf_beta`, `hm_omega`, `hm_psi`, `if_sara`, `im_nicola`, `pf_dora`, `pm_alex`, `pm_santa`

### Cartesia

The guide lists a large shared Cartesia voice catalog, including:
`friendly sidekick`, `reading lady`, `newsman`, `child`, `meditation lady`, `maria`, `calm lady`,
`helpful woman`, `reading man`, `new york man`, `barbershop man`, `customer support man`, `sarah`,
`laidback woman`, `reflective woman`, `professional woman`, `california girl`, `john`, `anna`

Regional examples include:
`german conversational woman`, `french conversational lady`, `indian lady`, `british reading lady`,
`japanese children book`, `korean narrator woman`, `russian calm lady`, `chinese female conversational`,
`spanish narrator man`, `dutch confident man`, `hindi reporter man`, `italian calm man`,
`swedish narrator man`, `polish confident man`

### Rime Mist v2 / v3

`cove`, `lagoon`, `mari`, `moon`, `moraine`, `peak`, `summit`, `talon`, `thunder`, `tundra`,
`wildflower`

### Rime Arcana v2 / v3 / v3 Turbo

`albion`, `arcade`, `astra`, `atrium`, `bond`, `cupola`, `eliphas`, `estelle`, `eucalyptus`, `fern`,
`lintel`, `luna`, `lyra`, `marlu`, `masonry`, `moss`, `oculus`, `parapet`, `pilaster`, `sirius`,
`stucco`, `transom`, `truss`, `vashti`, `vespera`, `walnut`

### MiniMax Speech 2.6 Turbo

`English_DeterminedMan`, `English_Diligent_Man`, `English_expressive_narrator`,
`English_FriendlyNeighbor`, `English_Graceful_Lady`, `Japanese_GentleButler`
