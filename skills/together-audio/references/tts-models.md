# TTS Models & Voices Reference

## Models

| Model | API String | Endpoints | Pricing |
|-------|-----------|-----------|---------|
| Orpheus 3B | `canopylabs/orpheus-3b-0.1-ft` | REST, Streaming, WebSocket | $15/1M chars |
| Kokoro 82M | `hexgrad/Kokoro-82M` | REST, Streaming, WebSocket | $4/1M chars |
| Cartesia Sonic 3 | `cartesia/sonic-3` | REST | - |
| Cartesia Sonic 2 | `cartesia/sonic-2` | REST | $65/1M chars |
| Deepgram Aura 2* | `deepgram/deepgram-aura-2` | REST, Streaming, WebSocket | DE only |
| Rime Arcana v3 Turbo* | `rime-labs/rime-arcana-v3-turbo` | REST, Streaming, WebSocket | DE only |
| Rime Arcana v3* | `rime-labs/rime-arcana-v3` | REST, Streaming, WebSocket | DE only |
| Rime Mist v2* | `rime-labs/rime-mist-v2` | REST, Streaming, WebSocket | DE only |
| MiniMax Speech 2.6 Turbo* | `minimax/speech-2.6-turbo` | REST, Streaming, WebSocket | DE only |

*Dedicated Endpoint only

## Voice Lists

### Orpheus (8 voices)
`tara`, `leah`, `jess`, `leo`, `dan`, `mia`, `zac`, `zoe`

### Kokoro (51 voices)

**American Female (af_):** `af_heart`, `af_alloy`, `af_aoede`, `af_bella`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky`

**American Male (am_):** `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa`

**British Female (bf_):** `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`

**British Male (bm_):** `bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis`

**Japanese Female (jf_):** `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`

**Japanese Male (jm_):** `jm_kumo`

**Chinese Female (zf_):** `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`

**Chinese Male (zm_):** `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang`

**Other Languages:** `ef_dora`, `em_alex`, `em_santa`, `ff_siwis`, `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`, `if_sara`, `im_nicola`, `pf_dora`, `pm_alex`, `pm_santa`

### Cartesia (94+ voices)
Key voices include: `reading lady`, `newsman`, `child`, `meditation lady`, `maria`, `calm lady`, `helpful woman`, `reading man`, `new york man`, `barbershop man`, `customer support man`, `sarah`, `laidback woman`, `reflective woman`, `professional woman`, `california girl`, `john`, `anna`

Regional voices: `german conversational woman`, `french conversational lady`, `indian lady`, `british reading lady`, `japanese children book`, `korean narrator woman`, `russian calm lady`, `chinese female conversational`, `spanish narrator man`, `dutch confident man`, `hindi reporter man`, `italian calm man`, `swedish narrator man`, `polish confident man`

### Rime Mist v2 (14 voices)
`cove`, `eucalyptus`, `lagoon`, `mari`, `marlu`, `mesa_extra`, `moon`, `moraine`, `peak`, `summit`, `talon`, `thunder`, `tundra`, `wildflower`

### Rime Arcana v2/v3/v3 Turbo (22+ voices)
`albion`, `arcade`, `astra`, `atrium`, `bond`, `cupola`, `eliphas`, `estelle`, `eucalyptus`, `fern`, `lintel`, `luna`, `lyra`, `marlu`, `masonry`, `moss`, `oculus`, `parapet`, `pilaster`, `sirius`, `stucco`, `transom`, `truss`, `vashti`, `vespera`, `walnut`

### MiniMax Speech 2.6 Turbo (sample voices)
`English_DeterminedMan`, `English_Diligent_Man`, `English_expressive_narrator`, `English_FriendlyNeighbor`, `English_Graceful_Lady`, `Japanese_GentleButler`

Query the full list via API:

```python
response = client.audio.voices.list()
```

```shell
curl -X GET "https://api.together.xyz/v1/voices?model=canopylabs/orpheus-3b-0.1-ft" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## REST Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | TTS model identifier |
| `input` | string | Yes | Text to synthesize |
| `voice` | string | Yes | Voice ID |
| `response_format` | string | No | `mp3`, `wav`, `raw`, `mulaw`. Default: `wav` |
| `stream` | bool | No | Enable streaming (`raw` format only) |
| `response_encoding` | string | No | `pcm_s16le`, `pcm_f32le`, `pcm_mulaw`, `pcm_alaw` for raw |
| `language` | string | No | Input text language (en, de, fr, es, hi, it, ja, ko, nl, pl, pt, ru, sv, tr, zh) |
| `sample_rate` | int | No | Audio sample rate (e.g., 44100, 24000) |

## WebSocket Parameters

Connection: `wss://api.together.xyz/v1/audio/speech/websocket`

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | TTS model (query param) |
| `voice` | string | Voice ID (query param) |
| `response_format` | string | `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm` |
| `speed` | float | Playback speed (default: 1.0) |
| `max_partial_length` | int | Character buffer before triggering TTS (default: 250) |

## WebSocket Events

**Client to Server:**
- `input_text_buffer.append` -- Append text to buffer
- `input_text_buffer.commit` -- Force processing remaining text
- `input_text_buffer.clear` -- Clear buffer
- `tts_session.updated` -- Update session settings (e.g., voice)

**Server to Client:**
- `session.created` -- Session established with metadata
- `conversation.item.input_text.received` -- Text acknowledged
- `conversation.item.audio_output.delta` -- Audio chunk (base64-encoded)
- `conversation.item.audio_output.done` -- Generation complete for item
- `conversation.item.tts.failed` -- Error with details

## Response Formats

| Format | Extension | Description | Streaming |
|--------|-----------|-------------|-----------|
| wav | .wav | Uncompressed audio | No |
| mp3 | .mp3 | Compressed audio | No |
| raw | .pcm | Raw PCM data | Yes |
| mulaw | .ulaw | Logarithmic compression (telephony) | Yes |
