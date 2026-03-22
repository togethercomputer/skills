# Video Generation API Reference
## Contents

- [Endpoints](#endpoints)
- [Create Video](#create-video)
- [Get Video Status](#get-video-status)
- [Job Statuses](#job-statuses)
- [Polling Pattern](#polling-pattern)
- [Guidance Scale](#guidance-scale)
- [Steps](#steps)


## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /v2/videos` | Create video | Submit a video generation job |
| `GET /v2/videos/{id}` | Get video status | Poll for job completion |

Base URL: `https://api.together.xyz`

## Create Video

### Request

```python
from together import Together
client = Together()

job = client.videos.create(
    prompt="A serene sunset over the ocean with gentle waves",
    model="minimax/video-01-director",
    width=1366,
    height=768,
)
print(job.id)
```

```typescript
import Together from "together-ai";
const client = new Together();

const job = await client.videos.create({
  prompt: "A serene sunset over the ocean with gentle waves",
  model: "minimax/video-01-director",
  width: 1366,
  height: 768,
});
console.log(job.id);
```

```shell
curl -X POST "https://api.together.xyz/v2/videos" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax/video-01-director",
    "prompt": "A serene sunset over the ocean with gentle waves",
    "width": 1366,
    "height": 768
  }'
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model identifier |
| `prompt` | string | Yes* | - | Text description (1-32,000 chars) |
| `width` | integer | No | 1366 | Video width in pixels |
| `height` | integer | No | 768 | Video height in pixels |
| `seconds` | string | No | varies | Clip duration override. Supported values depend on the model. |
| `fps` | integer | No | 24 | Frames per second (15-60) |
| `steps` | integer | No | varies | Diffusion steps (10-50) |
| `guidance_scale` | float | No | varies | Prompt adherence (6.0-10.0, avoid >12) |
| `seed` | integer | No | random | Random seed for reproducibility |
| `negative_prompt` | string | No | - | Elements to exclude |
| `frame_images` | array | No | - | Keyframe images: `[{input_image, frame}]` |
| `reference_images` | array | No | - | Style reference image URLs |
| `output_format` | string | No | `"MP4"` | `"MP4"` or `"WEBM"` |
| `output_quality` | integer | No | 20 | Compression quality (lower = higher quality) |

*Prompt not required for Kling 2.1 Standard/Pro and Kling 1.6 Pro.

### frame_images Schema

Each element in the `frame_images` array:

| Field | Type | Description |
|-------|------|-------------|
| `input_image` | string | Image URL or base64-encoded image data |
| `frame` | number or string | Frame index: `0`, `"first"`, or `"last"` |

Frame number calculation: `frame = seconds x fps` (for specific frame positions).

### Advanced Example

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
const job = await client.videos.create({
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

### Keyframe Example

```python
job = client.videos.create(
    prompt="Smooth camera zoom out revealing a vast landscape",
    model="minimax/hailuo-02",
    width=1366,
    height=768,
    frame_images=[{
        "input_image": "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
        "frame": "first",
    }],
)
```

```typescript
const job = await client.videos.create({
  prompt: "Smooth camera zoom out revealing a vast landscape",
  model: "minimax/hailuo-02",
  width: 1366,
  height: 768,
  frame_images: [{
    input_image: "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
    frame: "first",
  }],
});
```

### Reference Images Example

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

### Create Response

```json
{
  "id": "019a0068-794a-7213-90f6-cc4eb62e3da7",
  "object": "video",
  "model": "minimax/video-01-director",
  "status": "in_progress",
  "created_at": 1729407438
}
```

## Get Video Status

### Request

```python
status = client.videos.retrieve("019a0068-794a-7213-90f6-cc4eb62e3da7")
print(f"Status: {status.status}")
if status.status == "completed":
    print(f"Video URL: {status.outputs.video_url}")
    print(f"Cost: ${status.outputs.cost}")
```

```typescript
const status = await client.videos.retrieve("019a0068-794a-7213-90f6-cc4eb62e3da7");
console.log(`Status: ${status.status}`);
if (status.status === "completed") {
  console.log(`Video URL: ${status.outputs.video_url}`);
  console.log(`Cost: $${status.outputs.cost}`);
}
```

```shell
curl -X GET "https://api.together.xyz/v2/videos/$JOB_ID" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Job ID from create response |

### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique job identifier |
| `object` | string | Always `"video"` |
| `model` | string | Model used |
| `status` | string | `in_progress`, `completed`, or `failed` |
| `created_at` | number | Unix timestamp of creation |
| `completed_at` | number | Unix timestamp of completion |
| `size` | string | Video resolution |
| `seconds` | string | Clip duration |
| `outputs` | object | `{cost, video_url}` when completed |
| `error` | object | `{code, message}` when failed |

### Completed Response

```json
{
  "id": "019a0068-794a-7213-90f6-cc4eb62e3da7",
  "object": "video",
  "model": "minimax/video-01-director",
  "status": "completed",
  "created_at": 1729407438,
  "completed_at": 1729407612,
  "size": "1366x768",
  "seconds": "5",
  "outputs": {
    "cost": 0.28,
    "video_url": "https://api.together.ai/shrt/DwlaBdSakNRFlBxN"
  }
}
```

## Job Statuses

| Status | Description |
|--------|-------------|
| `queued` | Waiting in queue |
| `in_progress` | Generating |
| `completed` | Done -- `outputs.video_url` available |
| `failed` | Check `error` for details |
| `cancelled` | Job cancelled |

## Polling Pattern

```python
import time
from together import Together
client = Together()

job = client.videos.create(
    prompt="A mountain landscape at sunset",
    model="minimax/video-01-director",
)

while True:
    status = client.videos.retrieve(job.id)
    if status.status == "completed":
        print(f"Video: {status.outputs.video_url}")
        break
    elif status.status == "failed":
        print(f"Error: {status.error}")
        break
    time.sleep(5)
```

## Guidance Scale

| Range | Effect |
|-------|--------|
| 6.0-7.0 | More creative, less literal |
| 7.0-9.0 | Balanced (recommended) |
| 9.0-10.0 | Strict prompt adherence |
| >12.0 | Avoid -- causes artifacts |

## Steps

| Steps | Effect |
|-------|--------|
| 10 | Quick testing, lower quality |
| 20 | Standard quality |
| 30-40 | Production-grade |
| >50 | Diminishing returns |
