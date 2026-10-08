# Together AI: Images

Text-to-image generation and image editing, billed per image (FLUX models also scale with
megapixels and steps). Covers FLUX.2, FLUX.1 Kontext editing, LoRA styling, and reference images.
Motion goes to `domains/video.md`.

## Workflow

1. Decide whether the task is generation, editing (Kontext), or LoRA style transfer.
2. Pick the model and dimensions first. Current serverless picks: `black-forest-labs/FLUX.2-dev`
   (general), `FLUX.2-pro` / `FLUX.2-max` (quality), `FLUX.1-kontext-pro` / `-max` (editing).
3. Add reference images, LoRAs, or FLUX.2-only parameters only when the task needs them.
4. Generate, then download the URL or decode `b64_json` promptly.

## Rules

- **Saved files must match their bytes.** Models return JPEG unless you request another format, and
  `output_format` exists only on FLUX.2. Pass `output_format="png"` on FLUX.2 when PNG is required;
  otherwise save with the extension of the actual bytes. The scripts' `save_image_bytes` does this.
- Generate-then-edit: generate with FLUX.2, pass the returned URL as `image_url` to Kontext, and
  save both results.
- Kontext takes one source image via `image_url`; `reference_images` is FLUX.2 and Google only.
- Check that the chosen model supports editing or reference images before promising them.
- Set `seed` when the user needs reproducible output.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/images/generate_image.py](scripts/images/generate_image.py) (.ts) | 162 | text-to-image, variations, base64 save, FLUX.2 options, format-safe saving | generating images |
| [scripts/images/kontext_editing.py](scripts/images/kontext_editing.py) | 200 | Kontext edits, style transfer, generate-then-edit chain (Example 7) | editing an image |
| [scripts/images/lora_generation.py](scripts/images/lora_generation.py) | 100 | applying one or more LoRA adapters to FLUX | LoRA styling |
| [references/images/models.md](references/images/models.md) | 111 | model table, feature matrix by family, supported dimensions, FLUX pricing formula | choosing a model or size |
| [references/images/api-reference.md](references/images/api-reference.md) | 368 | all parameters, Kontext, reference images, LoRA, steps and dimension guides, troubleshooting | a parameter or error not covered above |

## Docs

- [Images Overview](https://docs.together.ai/docs/images-overview)
- [FLUX.2 Quickstart](https://docs.together.ai/docs/quickstart-flux)
- [FLUX Kontext](https://docs.together.ai/docs/quickstart-flux-kontext)
- [FLUX LoRA](https://docs.together.ai/docs/quickstart-flux-lora)
- [Image Generation API](https://docs.together.ai/reference/post-images-generations)
