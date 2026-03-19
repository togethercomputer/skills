# Image Generation API Reference

## Endpoint

`POST https://api.together.xyz/v1/images/generations`

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | Text description of image to generate |
| `model` | string | Yes | - | Model identifier |
| `width` | integer | No | 1024 | Image width in pixels (256-1920) |
| `height` | integer | No | 1024 | Image height in pixels (256-1920) |
| `n` | integer | No | 1 | Number of images (1-4) |
| `steps` | integer | No | varies | Diffusion steps (1-50) |
| `seed` | integer | No | random | Random seed for reproducibility |
| `negative_prompt` | string | No | - | What to avoid in generation |
| `response_format` | string | No | `"url"` | `"base64"` for inline data, `"url"` for hosted |
| `image_url` | string | No | - | Reference image URL (Kontext models) |
| `reference_images` | array | No | - | Reference image URLs (FLUX.2, Google models) |
| `image_loras` | array | No | - | LoRA adapters: `[{path, scale}]` (max 2) |
| `guidance` | float | No | - | Guidance scale for FLUX.2 dev/flex |
| `guidance_scale` | number | No | 3.5 | Prompt alignment (1-5 creative, 8-10 faithful) |
| `prompt_upsampling` | bool | No | true | Auto-enhance prompts (FLUX.2) |
| `output_format` | string | No | `"jpeg"` | `"jpeg"` or `"png"` (FLUX.2) |
| `aspect_ratio` | string | No | - | For Schnell/Kontext: 1:1, 16:9, 9:16, 4:3, 3:2 |
| `disable_safety_checker` | bool | No | false | Disable NSFW check |

## Text-to-Image

```python
from together import Together
client = Together()

response = client.images.generate(
    prompt="A sunset over mountains",
    model="black-forest-labs/FLUX.1-schnell",
    width=1024,
    height=1024,
    steps=4,
    n=1,
)
print(response.data[0].url)
```

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.images.generate({
  prompt: "A sunset over mountains",
  model: "black-forest-labs/FLUX.1-schnell",
  width: 1024,
  height: 1024,
  steps: 4,
  n: 1,
});
console.log(response.data[0].url);
```

```shell
curl -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A sunset over mountains",
    "model": "black-forest-labs/FLUX.1-schnell",
    "width": 1024,
    "height": 1024,
    "steps": 4,
    "n": 1
  }'
```

## FLUX.2 Generation

FLUX.2 models support `prompt_upsampling`, `output_format`, `guidance`, and
`reference_images`.

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.2-pro",
    prompt="A mountain landscape at sunset with golden light",
    width=1024,
    height=768,
    prompt_upsampling=True,
    output_format="png",
)
```

```typescript
const response = await together.images.generate({
  model: "black-forest-labs/FLUX.2-pro",
  prompt: "A mountain landscape at sunset with golden light",
  width: 1024,
  height: 768,
  prompt_upsampling: true,
  output_format: "png",
});
```

### FLUX.2 Dev/Flex with Guidance

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.2-dev",
    prompt="A detailed portrait in oil painting style",
    width=1024,
    height=1024,
    steps=28,
    guidance=7.5,
)
```

## Image Editing (Kontext)

For Kontext models, provide a reference image and editing instructions:

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.1-kontext-pro",
    prompt="Make his shirt yellow",
    image_url="https://github.com/nutlope.png",
    width=1536,
    height=1024,
    steps=28,
)
```

```typescript
const response = await together.images.generate({
  model: "black-forest-labs/FLUX.1-kontext-pro",
  prompt: "Make his shirt yellow",
  image_url: "https://github.com/nutlope.png",
  width: 1536,
  height: 1024,
  steps: 28,
});
```

```shell
curl -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "black-forest-labs/FLUX.1-kontext-pro",
    "prompt": "Make his shirt yellow",
    "image_url": "https://github.com/nutlope.png",
    "width": 1536,
    "height": 1024,
    "steps": 28
  }'
```

## Reference Images (FLUX.2, Google)

Use `reference_images` for multi-image guidance:

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.2-pro",
    prompt="Replace the color of the car to blue",
    width=1024,
    height=768,
    reference_images=[
        "https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg",
    ],
)
```

```typescript
const response = await together.images.generate({
  model: "black-forest-labs/FLUX.2-pro",
  prompt: "Replace the color of the car to blue",
  width: 1024,
  height: 768,
  reference_images: [
    "https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg",
  ],
});
```

## LoRA Adapters

Apply up to 2 LoRA adapters per image. Compatible with FLUX.2 Dev and FLUX.1 Dev.

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.2-dev",
    prompt="a man walking outside on a rainy day",
    width=1024,
    height=768,
    steps=28,
    image_loras=[
        {"path": "https://huggingface.co/XLabs-AI/flux-RealismLora", "scale": 0.8},
    ],
)
```

```typescript
const response = await together.images.generate({
  model: "black-forest-labs/FLUX.2-dev",
  prompt: "a man walking outside on a rainy day",
  width: 1024,
  height: 768,
  steps: 28,
  image_loras: [
    { path: "https://huggingface.co/XLabs-AI/flux-RealismLora", scale: 0.8 },
  ],
});
```

```shell
curl -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "black-forest-labs/FLUX.2-dev",
    "prompt": "a man walking outside on a rainy day",
    "width": 1024,
    "height": 768,
    "steps": 28,
    "image_loras": [
      {"path": "https://huggingface.co/XLabs-AI/flux-RealismLora", "scale": 0.8}
    ]
  }'
```

### LoRA Path Formats

- Hugging Face repo: `https://huggingface.co/XLabs-AI/flux-RealismLora`
- Hugging Face file: `https://huggingface.co/.../resolve/main/model.safetensors`
- CivitAI: `https://civitai.com/api/download/models/...`
- Replicate: `https://replicate.com/fofr/flux-black-light`
- Direct `.safetensors` URL

### LoRA Scale Guide

- `0.3-0.5`: Subtle effect
- `0.6-0.8`: Balanced (recommended)
- `0.9-1.2`: Strong effect

## Response

```json
{
  "id": "img-abc123",
  "model": "black-forest-labs/FLUX.1-schnell",
  "object": "list",
  "data": [
    {
      "index": 0,
      "url": "https://api.together.ai/v1/images/...",
      "type": "url"
    }
  ]
}
```

With `response_format="base64"`:

```json
{
  "id": "img-abc123",
  "model": "black-forest-labs/FLUX.1-schnell",
  "object": "list",
  "data": [
    {
      "index": 0,
      "b64_json": "iVBORw0KGgo...",
      "type": "b64_json",
      "timings": { "inference": 0.799 }
    }
  ]
}
```

## Steps Guide

| Steps | Effect |
|-------|--------|
| 1-4 | Fast, lower quality (FLUX.1 Schnell default: 4) |
| 10-20 | Good balance of speed and quality |
| 28 | High quality (Kontext, FLUX.1 Dev default) |
| 30-50 | Maximum quality, slower |

## Dimensions Guide

| Aspect Ratio | Dimensions | Use Case |
|-------------|-----------|----------|
| 1:1 | 1024x1024 | Square, social media |
| 16:9 | 1344x768 | Landscape, widescreen |
| 9:16 | 768x1344 | Portrait, mobile |
| 3:2 | 1248x832 | Photography standard |
| 4:3 | 1184x864 | Classic ratio |

## Model Feature Matrix

| Feature | FLUX.2 | FLUX.1 Schnell | FLUX.1 Kontext | Google |
|---------|--------|---------------|---------------|--------|
| Text-to-image | Yes | Yes | Yes | Yes |
| `image_url` | Pro/Flex | No | Yes | No |
| `reference_images` | Yes | No | No | Yes |
| `image_loras` | Dev | No | No | No |
| `prompt_upsampling` | Yes | No | No | No |
| `guidance` | Dev/Flex | No | No | No |
| `output_format` | Yes | No | No | No |
| `negative_prompt` | No | Yes | No | No |
