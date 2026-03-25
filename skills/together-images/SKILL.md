---
name: together-images
description: "Use this skill for Together AI image workflows: text-to-image generation, image editing with Kontext, FLUX model selection, LoRA-based styling, reference-image guidance, and local image downloads. Reach for it whenever the user wants to generate or edit images on Together AI rather than create videos or build text-only chat applications."
---

# Together Images

## Overview

Use Together AI image APIs for:

- text-to-image generation
- image editing with Kontext
- FLUX.2-specific options
- LoRA adapters
- reference-image guidance

## When This Skill Wins

- Generate still images from prompts
- Edit an existing image with text guidance
- Apply LoRA styles to FLUX models
- Choose image models or dimensions for a product workflow

## Hand Off To Another Skill

- Use `together-video` for motion or video generation
- Use `together-chat-completions` for text-only generation
- Use `together-dedicated-containers` only when the user needs a custom image runtime rather than the managed API

## Quick Routing

- **Basic text-to-image**
  - Start with [scripts/generate_image.py](scripts/generate_image.py) or [scripts/generate_image.ts](scripts/generate_image.ts)
  - Read [references/api-reference.md](references/api-reference.md)
- **Multiple variations, base64 output, or seeded runs**
  - Start with [scripts/generate_image.py](scripts/generate_image.py) or [scripts/generate_image.ts](scripts/generate_image.ts)
  - Read [references/api-reference.md](references/api-reference.md)
- **Image editing with Kontext**
  - Start with [scripts/kontext_editing.py](scripts/kontext_editing.py)
  - Read [references/api-reference.md](references/api-reference.md)
- **LoRA styling**
  - Start with [scripts/lora_generation.py](scripts/lora_generation.py)
  - Read [references/api-reference.md](references/api-reference.md)
- **Model and dimension selection**
  - Read [references/models.md](references/models.md)

## Workflow

1. Confirm whether the task is generation, editing, or style transfer.
2. Choose the model family and output dimensions first.
3. Add reference images, LoRAs, or FLUX.2-only parameters only when the use case needs them.
4. Generate the asset, then download or decode it into the expected local format.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Match the script to the workflow type instead of packing every image feature into one request path.
- Keep model selection explicit because FLUX, Kontext, and partner models differ in capabilities.
- Preserve reproducibility with seeds when the user needs stable outputs.
- For editing or reference-image flows, validate that the chosen model actually supports the feature.

## Resource Map

- **API reference**: [references/api-reference.md](references/api-reference.md)
- **Troubleshooting and generation tuning**: [references/api-reference.md](references/api-reference.md)
- **Model guide**: [references/models.md](references/models.md)
- **Python image generation**: [scripts/generate_image.py](scripts/generate_image.py)
- **TypeScript image generation**: [scripts/generate_image.ts](scripts/generate_image.ts)
- **Python Kontext editing**: [scripts/kontext_editing.py](scripts/kontext_editing.py)
- **Python LoRA generation**: [scripts/lora_generation.py](scripts/lora_generation.py)

## Official Docs

- [Images Overview](https://docs.together.ai/docs/images-overview)
- [FLUX.2 Quickstart](https://docs.together.ai/docs/quickstart-flux)
- [FLUX Kontext](https://docs.together.ai/docs/quickstart-flux-kontext)
- [FLUX LoRA](https://docs.together.ai/docs/quickstart-flux-lora)
- [Image Generation API](https://docs.together.ai/reference/post-images-generations)
