---
name: together-video
description: "Text-to-video and image-to-video generation via Together AI, including keyframe control, model and dimension selection, asynchronous job polling, and video downloads. Reach for it whenever the user wants motion generation on Together AI rather than still-image generation or text-only inference."
---

# Together Video

## Overview

Use Together AI video APIs for:

- text-to-video generation
- image-to-video generation
- first-frame and last-frame keyframe control
- asynchronous job polling
- local download of completed outputs

## When This Skill Wins

- Generate short videos from prompts
- Animate an existing image
- Choose among Veo, Sora, Kling, Seedance, PixVerse, Vidu, or other supported models
- Add polling and download logic to a product or script

## Hand Off To Another Skill

- Use `together-images` for still-image generation or editing
- Use `together-dedicated-containers` only when a custom video-serving runtime is required

## Quick Routing

- **Text-to-video generation**
  - Start with [scripts/generate_video.py](scripts/generate_video.py) or [scripts/generate_video.ts](scripts/generate_video.ts)
  - Read [references/api-reference.md](references/api-reference.md)
- **Image-to-video with keyframes**
  - Start with [scripts/image_to_video.py](scripts/image_to_video.py)
  - Read [references/api-reference.md](references/api-reference.md)
- **Parameter tuning, polling, or troubleshooting**
  - Read [references/api-reference.md](references/api-reference.md)
- **Model, dimension, and prompt-limit selection**
  - Read [references/models.md](references/models.md)

## Workflow

1. Confirm whether the user needs text-to-video or image-to-video.
2. Choose the model based on duration, dimension, keyframe support, and audio support.
3. Submit the async job and poll until a terminal state.
4. Download the result promptly before signed URLs expire.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Together video generation is asynchronous; do not treat it like a synchronous image call.
- Keyframe support is model-specific. Validate support before promising first-plus-last-frame control.
- Keep polling and download logic as part of the workflow, not as an afterthought.
- Use explicit dimensions and generation parameters rather than relying on unstable defaults.

## Resource Map

- **API reference**: [references/api-reference.md](references/api-reference.md)
- **Polling, parameter tuning, and troubleshooting**: [references/api-reference.md](references/api-reference.md)
- **Model guide**: [references/models.md](references/models.md)
- **Python text-to-video workflow**: [scripts/generate_video.py](scripts/generate_video.py)
- **TypeScript text-to-video workflow**: [scripts/generate_video.ts](scripts/generate_video.ts)
- **Python image-to-video workflow**: [scripts/image_to_video.py](scripts/image_to_video.py)

## Official Docs

- [Videos Overview](https://docs.together.ai/docs/videos-overview)
- [Create Video API](https://docs.together.ai/reference/create-videos)
