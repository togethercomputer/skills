---
name: together-video
description: Generate videos from text and image prompts via Together AI. 20+ models including Veo 2/3 (with audio), Sora 2, Kling 2.1, Hailuo 02, Seedance, PixVerse, Vidu, and Wan 2.2. Supports text-to-video, image-to-video with keyframe control (first/last frame), reference images, guidance scale, negative prompts, and configurable quality. Use when users want to generate videos, create video content, animate images, or work with any video generation task.
---

# Together Video Generation

## Overview

Generate videos asynchronously -- submit a job, poll for completion, download the result.

- Endpoint: `/v2/videos`
- Async workflow: create job -> poll status -> download video
- 20+ models from Google, OpenAI, MiniMax, Kuaishou, ByteDance, PixVerse, Vidu, Wan-AI

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together # for quick install without setting project
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

## Quick Start

### Text-to-Video

```python
import time
from together import Together
client = Together()

job = client.videos.create(
    prompt="A serene sunset over the ocean with gentle waves",
    model="minimax/video-01-director",
    width=1366,
    height=768,
)
print(f"Job ID: {job.id}")

# Poll until completion
while True:
    status = client.videos.retrieve(job.id)
    if status.status == "completed":
        print(f"Video URL: {status.outputs.video_url}")
        break
    elif status.status == "failed":
        print("Failed")
        break
    time.sleep(5)
```

```typescript
import Together from "together-ai";
const together = new Together();

const job = await together.videos.create({
  prompt: "A serene sunset over the ocean with gentle waves",
  model: "minimax/video-01-director",
  width: 1366,
  height: 768,
});
console.log(`Job ID: ${job.id}`);

// Poll until completion
while (true) {
  const status = await together.videos.retrieve(job.id);
  if (status.status === "completed") {
    console.log(`Video URL: ${status.outputs.video_url}`);
    break;
  } else if (status.status === "failed") break;
  await new Promise((r) => setTimeout(r, 5000));
}
```

```shell
# Create a video generation job
curl -X POST "https://api.together.xyz/v2/videos" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax/video-01-director",
    "prompt": "A serene sunset over the ocean with gentle waves",
    "width": 1366,
    "height": 768
  }'

# Poll for completion (replace $JOB_ID with the id from the create response)
curl -X GET "https://api.together.xyz/v2/videos/$JOB_ID" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### Advanced Parameters

Duration is model-specific. `minimax/hailuo-02` currently accepts `"6"` and `"10"`,
while fixed 5-second clips are better served by models such as `minimax/video-01-director`.

```python
job = client.videos.create(
    prompt="A futuristic city at night with neon lights reflecting on wet streets",
    model="minimax/hailuo-02",
    width=1366,
    height=768,
    seconds="6",
    fps=30,
    steps=30,
    guidance_scale=8.0,
    output_format="MP4",
    output_quality=20,
    seed=42,
    negative_prompt="blurry, low quality, distorted",
)
```

```typescript
const job = await together.videos.create({
  prompt: "A futuristic city at night with neon lights reflecting on wet streets",
  model: "minimax/hailuo-02",
  width: 1366,
  height: 768,
  seconds: "6",
  fps: 30,
  steps: 30,
  guidance_scale: 8.0,
  output_format: "MP4",
  output_quality: 20,
  seed: 42,
  negative_prompt: "blurry, low quality, distorted",
});
```

### Image-to-Video (Keyframes)

Animate a starting image. The `frame_images` parameter accepts a URL or base64-encoded image
with a `frame` index (0, "first", or "last"):

```python
job = client.videos.create(
    prompt="Smooth camera zoom out revealing a vast landscape",
    model="minimax/video-01-director",
    width=1366,
    height=768,
    frame_images=[{
        "input_image": "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
        "frame": "first",
    }],
)
```

```typescript
const job = await together.videos.create({
  prompt: "Smooth camera zoom out revealing a vast landscape",
  model: "minimax/video-01-director",
  width: 1366,
  height: 768,
  frame_images: [{
    input_image: "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
    frame: "first",
  }],
});
```

```shell
curl -X POST "https://api.together.xyz/v2/videos" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax/video-01-director",
    "prompt": "Smooth camera zoom out revealing a vast landscape",
    "width": 1366,
    "height": 768,
    "frame_images": [{
      "input_image": "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
      "frame": "first"
    }]
  }'
```

Models supporting first + last keyframes (Veo 2.0, Kling 2.1 Pro, Seedance, PixVerse, Vidu):

```python
job = client.videos.create(
    prompt="Smooth transition from sunrise to sunset",
    model="ByteDance/Seedance-1.0-pro",
    frame_images=[
        {"input_image": "https://example.com/sunrise.jpg", "frame": "first"},
        {"input_image": "https://example.com/sunset.jpg", "frame": "last"},
    ],
)
```

### Reference Images

Guide visual style with reference images (Vidu 2.0):

```python
job = client.videos.create(
    prompt="A cat dancing energetically",
    model="vidu/vidu-2.0",
    width=1280,
    height=720,
    reference_images=[
        "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
    ],
)
```

## Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | string | Text description (1-32,000 chars) | required* |
| `model` | string | Model ID | required |
| `width` | int | Video width in pixels | 1366 |
| `height` | int | Video height in pixels | 768 |
| `seconds` | string | Optional duration override; accepted values depend on the model | varies |
| `fps` | int | Frames per second (15-60) | 24-25 |
| `steps` | int | Diffusion steps (10-50) | varies |
| `guidance_scale` | float | Prompt adherence (6.0-10.0) | varies |
| `seed` | int | Random seed for reproducibility | random |
| `negative_prompt` | string | What to exclude | - |
| `frame_images` | array | Keyframe images: `[{input_image, frame}]` | - |
| `reference_images` | array | Style reference image URLs | - |
| `output_format` | string | `"MP4"` or `"WEBM"` | `"MP4"` |
| `output_quality` | int | Bitrate/quality (lower = higher quality) | 20 |

*Prompt not required for Kling 2.1 Standard/Pro and Kling 1.6 Pro.

## Job Status Flow

| Status | Description |
|--------|-------------|
| `queued` | Waiting in queue |
| `in_progress` | Generating |
| `completed` | Done -- `outputs.video_url` available |
| `failed` | Check `error` or `info.errors` for details |
| `cancelled` | Job cancelled |

## Guidance Scale

- **6.0-7.0**: More creative, less literal
- **7.0-9.0**: Balanced (recommended)
- **9.0-10.0**: Strict prompt adherence
- **>12.0**: Avoid -- causes artifacts

## Steps

- **10**: Quick testing, lower quality
- **20**: Standard quality, balanced
- **30-40**: Production-grade quality
- **>50**: Diminishing returns

## Key Models

| Model | API String | Duration | Dimensions |
|-------|-----------|----------|------------|
| Veo 3.0 | `google/veo-3.0` | 8s | 1280x720, 1920x1080 |
| Veo 3.0 + Audio | `google/veo-3.0-audio` | 8s | 1280x720, 1920x1080 |
| Veo 3.0 Fast | `google/veo-3.0-fast` | 8s | 1280x720, 1920x1080 |
| Sora 2 | `openai/sora-2` | 8s | 1280x720 |
| Sora 2 Pro | `openai/sora-2-pro` | 8s | 1280x720 |
| Hailuo 02 | `minimax/hailuo-02` | 10s | 1366x768, 1920x1080 |
| Video 01 Director | `minimax/video-01-director` | 5s | 1366x768 |
| Kling 2.1 Master | `kwaivgI/kling-2.1-master` | 5s | 1920x1080 |
| Seedance 1.0 Pro | `ByteDance/Seedance-1.0-pro` | 5s | Multiple |
| PixVerse v5 | `pixverse/pixverse-v5` | 5s | Multiple |
| Vidu 2.0 | `vidu/vidu-2.0` | 8s | Multiple |

See [references/models.md](references/models.md) for the complete model table.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Prompt mismatch | Increase `guidance_scale` to 8-10, use specific language |
| Visual artifacts | Reduce `guidance_scale` below 12, increase `steps` to 30-40 |
| Slow generation | Reduce `steps` (10-20 for dev), shorten `seconds`, lower `fps` |
| URL expired | Download videos immediately after completion |
| Unnatural motion | Adjust `fps`, use `negative_prompt` to exclude artifacts |

## Resources

- **Full model details**: See [references/models.md](references/models.md)
- **API reference**: See [references/api-reference.md](references/api-reference.md)
- **Runnable scripts**: See [scripts/](scripts/) for Python and TypeScript examples
- **Official docs**: [Videos Overview](https://docs.together.ai/docs/videos-overview)
- **API reference**: [Create Video API](https://docs.together.ai/reference/create-videos)
