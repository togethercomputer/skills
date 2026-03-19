---
name: together-images
description: Generate and edit images via Together AI's image generation API. Models include FLUX.2 (pro/dev/flex), FLUX.1 (schnell/dev/pro), Kontext (image editing with text+image prompts), Google Imagen and Gemini, Seedream, Stable Diffusion, and more. Supports LoRA adapters, reference images, prompt upsampling, and multiple output formats. Use when users want to generate images from text, edit existing images, apply LoRA styles, use reference images, or work with any image generation task.
---

# Together Image Generation

## Overview

Generate images from text prompts and edit existing images via the Together AI API.

- Endpoint: `/v1/images/generations`
- Response: URL or base64-encoded image
- Models: FLUX.2, FLUX.1, Kontext, Google Imagen/Gemini, Seedream, Stable Diffusion, and more

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

### Text-to-Image

```python
from together import Together
client = Together()

response = client.images.generate(
    prompt="A serene mountain landscape at sunset with a lake reflection",
    model="black-forest-labs/FLUX.1-schnell",
    steps=4,
)
print(f"Image URL: {response.data[0].url}")
```

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.images.generate({
  prompt: "A serene mountain landscape at sunset with a lake reflection",
  model: "black-forest-labs/FLUX.1-schnell",
  steps: 4,
});
console.log(response.data[0].url);
```

```shell
curl -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "black-forest-labs/FLUX.1-schnell",
    "prompt": "A serene mountain landscape at sunset with a lake reflection",
    "steps": 4
  }'
```

### FLUX.2 Generation

FLUX.2 models support `prompt_upsampling`, `output_format`, and `reference_images`:

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.2-pro",
    prompt="A mountain landscape at sunset with golden light reflecting on a calm lake",
    width=1024,
    height=768,
    prompt_upsampling=True,
    output_format="png",
)
print(response.data[0].url)
```

```typescript
const response = await together.images.generate({
  model: "black-forest-labs/FLUX.2-pro",
  prompt: "A mountain landscape at sunset with golden light reflecting on a calm lake",
  width: 1024,
  height: 768,
  prompt_upsampling: true,
  output_format: "png",
});
console.log(response.data[0].url);
```

```shell
curl -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "black-forest-labs/FLUX.2-pro",
    "prompt": "A mountain landscape at sunset with golden light reflecting on a calm lake",
    "width": 1024,
    "height": 768,
    "prompt_upsampling": true,
    "output_format": "png"
  }'
```

### FLUX.2 with Reference Images

Use `reference_images` for image-to-image guidance with FLUX.2 and Google models:

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

### Image Editing (Kontext)

Transform existing images using a text prompt and reference image:

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.1-kontext-pro",
    prompt="Make his shirt yellow",
    image_url="https://github.com/nutlope.png",
    width=1536,
    height=1024,
    steps=28,
)
print(response.data[0].url)
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
console.log(response.data[0].url);
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

Kontext use cases: style transfer, object modification, scene transformation, character
creation, text rendering.

### LoRA Adapters

Apply up to 2 LoRA adapters per image for custom styles. Sources: Hugging Face, CivitAI,
Replicate, or direct `.safetensors` URLs.

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
print(response.data[0].url)
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

### Multiple Variations

```python
response = client.images.generate(
    prompt="A cute robot assistant",
    model="black-forest-labs/FLUX.1-schnell",
    n=4,
    steps=4,
)
for i, img in enumerate(response.data):
    print(f"Variation {i+1}: {img.url}")
```

### Base64 Response

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.1-schnell",
    prompt="a cat in outer space",
    response_format="base64",
)
print(response.data[0].b64_json)
```

```typescript
const response = await together.images.generate({
  model: "black-forest-labs/FLUX.1-schnell",
  prompt: "a cat in outer space",
  response_format: "base64",
});
console.log(response.data[0].b64_json);
```

## Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prompt` | string | Text description (required) | - |
| `model` | string | Model ID (required) | - |
| `width` | int | Width in pixels (256-1920) | 1024 |
| `height` | int | Height in pixels (256-1920) | 1024 |
| `n` | int | Number of images (1-4) | 1 |
| `steps` | int | Diffusion steps (1-50) | varies |
| `seed` | int | Random seed for reproducibility | random |
| `negative_prompt` | string | What to exclude from generation | - |
| `response_format` | string | `"url"` or `"base64"` | `"url"` |
| `image_url` | string | Reference image URL (Kontext) | - |
| `reference_images` | array | Reference image URLs (FLUX.2, Google) | - |
| `image_loras` | array | LoRA adapters: `[{path, scale}]` | - |
| `guidance` | float | Guidance scale for FLUX.2 dev/flex | - |
| `prompt_upsampling` | bool | Auto-enhance prompts (FLUX.2) | true |
| `output_format` | string | `"jpeg"` or `"png"` (FLUX.2) | `"jpeg"` |
| `disable_safety_checker` | bool | Disable NSFW filter | false |

Notes:
- Schnell and Kontext models also support `aspect_ratio` (1:1, 16:9, 9:16, 4:3, 3:2)
- FLUX.1 Pro/Dev use `width`/`height`; Schnell and Kontext can use either
- Dimensions should be multiples of 8
- FLUX.2 supports HEX color specification in prompts (e.g., `"color #2E4057"`)

## Models

| Model | API String | Best For |
|-------|-----------|----------|
| FLUX.2 Pro | `black-forest-labs/FLUX.2-pro` | Production quality, up to 9MP |
| FLUX.2 Dev | `black-forest-labs/FLUX.2-dev` | Development, LoRA support |
| FLUX.2 Flex | `black-forest-labs/FLUX.2-flex` | Adjustable steps/guidance, typography |
| FLUX.1 Schnell | `black-forest-labs/FLUX.1-schnell` | Fast generation (1-4 steps) |
| FLUX.1.1 Pro | `black-forest-labs/FLUX.1.1-pro` | High quality FLUX.1 |
| FLUX.1 Kontext Pro | `black-forest-labs/FLUX.1-kontext-pro` | Image editing (recommended) |
| FLUX.1 Kontext Max | `black-forest-labs/FLUX.1-kontext-max` | Maximum editing quality |
| Google Imagen 4.0 | `google/imagen-4.0-preview` | Google image generation |
| Flash Image 2.5 | `google/flash-image-2.5` | Fast editing, best quality |
| Gemini 3 Pro Image | `google/gemini-3-pro-image` | Gemini editing, up to 4K |
| Seedream 4.0 | `ByteDance-Seed/Seedream-4.0` | ByteDance generation |
| Ideogram 3.0 | `ideogram/ideogram-3.0` | Text rendering in images |

See [references/models.md](references/models.md) for the full model list with dimensions.

## Common Dimensions

| Use Case | Width | Height |
|----------|-------|--------|
| Square (social media) | 1024 | 1024 |
| Landscape (banners) | 1344 | 768 |
| Portrait (mobile) | 768 | 1344 |
| Photography (3:2) | 1248 | 832 |
| Classic (4:3) | 1184 | 864 |

## Steps Guide

- **1-4 steps**: Fast preview (FLUX.1 Schnell)
- **10-20 steps**: Good balance of speed and quality
- **28 steps**: High quality (Kontext, FLUX.1 Dev default)
- **30-50 steps**: Maximum quality (diminishing returns)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Prompt mismatch | Add descriptive language, style references, increase steps |
| Poor quality | Use 30-40 steps, add quality modifiers ("highly detailed", "8k") |
| Inconsistent results | Set `seed` for reproducibility |
| Wrong dimensions | Ensure width/height are multiples of 8, use standard ratios |
| LoRA not applying | Check `.safetensors` URL is accessible, adjust `scale` (0.3-1.2) |

## Resources

- **Supported models**: See [references/models.md](references/models.md)
- **API parameter details**: See [references/api-reference.md](references/api-reference.md)
- **Runnable scripts**: See [scripts/](scripts/) for Python and TypeScript examples
- **Official docs**: [Images Overview](https://docs.together.ai/docs/images-overview)
- **FLUX quickstart**: [FLUX.2](https://docs.together.ai/docs/quickstart-flux)
- **Kontext guide**: [FLUX Kontext](https://docs.together.ai/docs/quickstart-flux-kontext)
- **LoRA guide**: [FLUX LoRA](https://docs.together.ai/docs/quickstart-flux-lora)
- **API reference**: [Image Generation API](https://docs.together.ai/reference/post-images-generations)
