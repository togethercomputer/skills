# Together AI: Images

Use Together AI image APIs for text-to-image generation and image editing, including FLUX and Kontext models, LoRA styling, and reference-image guidance.

- text-to-image generation
- image editing with Kontext
- FLUX.2-specific options
- LoRA adapters
- reference-image guidance

## Use this guide for

- Generate still images from prompts
- Edit an existing image with text guidance
- Apply LoRA styles to FLUX models
- Choose image models or dimensions for a product workflow

## Do not use this guide for

- motion or video generation -> `domains/video.md`
- text-only generation -> `domains/chat-completions.md`
- only when the user needs a custom image runtime rather than the managed API -> `domains/dedicated-containers.md`

## Workflow

1. Confirm whether the task is generation, editing, or style transfer.
2. Choose the model family and output dimensions first.
3. Add reference images, LoRAs, or FLUX.2-only parameters only when the use case needs them.
4. Generate the asset, then download or decode it into the expected local format.

## Open next

- **Basic text-to-image**
  - Start with [scripts/images/generate_image.py](scripts/images/generate_image.py) or [scripts/images/generate_image.ts](scripts/images/generate_image.ts)
  - Read [references/images/api-reference.md](references/images/api-reference.md)
- **Multiple variations, base64 output, or seeded runs**
  - Start with [scripts/images/generate_image.py](scripts/images/generate_image.py) or [scripts/images/generate_image.ts](scripts/images/generate_image.ts)
  - Read [references/images/api-reference.md](references/images/api-reference.md)
- **Image editing with Kontext**
  - Start with [scripts/images/kontext_editing.py](scripts/images/kontext_editing.py)
  - Read [references/images/api-reference.md](references/images/api-reference.md)
- **Generate then edit (e.g. product photos)**
  - Start with [scripts/images/kontext_editing.py](scripts/images/kontext_editing.py) (Example 7)
  - Generate with FLUX, feed the URL to Kontext, save both locally
- **LoRA styling**
  - Start with [scripts/images/lora_generation.py](scripts/images/lora_generation.py)
  - Read [references/images/api-reference.md](references/images/api-reference.md)
- **Model and dimension selection**
  - Read [references/images/models.md](references/images/models.md)

## Rules

- Match the script to the workflow type instead of packing every image feature into one request path.
- Keep model selection explicit because FLUX, Kontext, and partner models differ in capabilities.
- Preserve reproducibility with seeds when the user needs stable outputs.
- For editing or reference-image flows, validate that the chosen model actually supports the feature.

## Docs

- [Images Overview](https://docs.together.ai/docs/images-overview)
- [FLUX.2 Quickstart](https://docs.together.ai/docs/quickstart-flux)
- [FLUX Kontext](https://docs.together.ai/docs/quickstart-flux-kontext)
- [FLUX LoRA](https://docs.together.ai/docs/quickstart-flux-lora)
- [Image Generation API](https://docs.together.ai/reference/post-images-generations)
