# Together AI: Images

Text-to-image generation and image editing. Billing depends on the model: most bill per image;
FLUX1.1 [pro], FLUX.1 Kontext, and FLUX.2 [max] bill per megapixel. Motion goes to
`domains/video.md`.

LoRA image generation is no longer available: the FLUX LoRA models were deprecated and current
FLUX.2 models reject `image_loras`. A LoRA-adapted image model needs a dedicated endpoint.

## Workflow

1. Decide whether the task is generation or editing.
2. Pick the model and size. Together's recommended model for text-to-image and image-to-image is
   `openai/gpt-image-2` (alternative `google/flash-image-2.5`). FLUX options:
   `black-forest-labs/FLUX.2-pro`, `FLUX.2-dev`, `FLUX.2-flex`, `FLUX.2-max`; editing with
   `FLUX.1-kontext-pro` or `-max`.
3. Add reference images or model-specific parameters only when the task needs them.
4. Generate, then download the URL or decode `b64_json` promptly.

## Rules

- **Saved files must match their bytes.** `output_format` defaults to `"jpeg"`; pass
  `output_format="png"` when PNG is required (supported on FLUX models, Kontext included), or save
  with the extension of the actual bytes. The scripts' `save_image_bytes` does this.
- **Some parameters are not SDK arguments.** The Python SDK rejects `aspect_ratio` and
  `prompt_upsampling` as keywords (`TypeError`); pass them in `extra_body={...}`. Kontext sizes
  output with `aspect_ratio` (for example `"16:9"`); `prompt_upsampling` is FLUX.2 [pro] only.
  The prompt-alignment knob is `guidance_scale` (FLUX.2 dev and flex).
- Kontext and FLUX.2 [pro]/[flex] take one source image via `image_url`; `reference_images`
  (several images) works on FLUX.2 pro/dev/flex, Gemini 3 Pro Image, and Flash Image 2.5.
- Generate-then-edit: generate an image, pass its URL as `image_url` to Kontext, save both.
- A 403 `third_party_data_sharing_blocked` (seen on FLUX.2) means the organization must enable
  third-party data sharing; try a model hosted without that requirement or ask the user.
- Set `seed` when the user needs reproducible output.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/images/generate_image.py](scripts/images/generate_image.py) (.ts) | 164 | text-to-image, variations, base64 save, FLUX.2 options, format-safe saving | generating images |
| [scripts/images/kontext_editing.py](scripts/images/kontext_editing.py) | 198 | Kontext edits by aspect ratio, style transfer, generate-then-edit chain (Example 7) | editing an image |
| [references/images/models.md](references/images/models.md) | 127 | full serverless image catalog, editing and reference-image support, recommended picks, dimensions, FLUX pricing formula | choosing a model or size |
| [references/images/api-reference.md](references/images/api-reference.md) | 302 | all parameters, Kontext, reference images, steps and dimension guides, feature matrix, troubleshooting | a parameter or error not covered above |

## Docs

- [Images overview](https://docs.together.ai/docs/inference/images/overview)
- [Image parameters](https://docs.together.ai/docs/inference/images/parameters)
- [Reference images](https://docs.together.ai/docs/inference/images/reference-images)
- [FLUX quickstart](https://docs.together.ai/docs/quickstart-flux)
- [Images API](https://docs.together.ai/reference/post-images-generations)
