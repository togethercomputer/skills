# Image Generation Models Reference
## Contents

- [Complete Model Table](#complete-model-table)
- [Model Categories](#model-categories)
- [Recommended Models](#recommended-models)
- [FLUX.2 Model Comparison](#flux2-model-comparison)
- [Supported Dimensions](#supported-dimensions)
- [FLUX Pricing Formula](#flux-pricing-formula)


## Complete Model Table

Serverless image models as of 2026-10-07 (source: [Serverless models](https://docs.together.ai/docs/serverless/models)). If a listed model returns an unavailable error, treat the runtime response and the [deprecations page](https://docs.together.ai/docs/deprecations) as the source of truth. Partner-hosted models (for example FLUX.2) return 403 `third_party_data_sharing_blocked` unless the organization enables third-party data sharing. FLUX.1 [schnell], FLUX.1 [dev], Imagen 4.0, HiDream, DreamShaper, and SD 3 Medium are no longer listed.

| Organization | Model | API String | Default Steps |
|-------------|-------|-----------|--------------|
| OpenAI | GPT Image 2 | `openai/gpt-image-2` | - |
| OpenAI | GPT Image 1.5 | `openai/gpt-image-1.5` | - |
| Google | Flash Image 2.5 (Nano Banana) | `google/flash-image-2.5` | - |
| Google | Gemini 3 Pro Image (Nano Banana Pro) | `google/gemini-3-pro-image` | - |
| Google | Gemini 3.1 Flash Image (Nano Banana 2) | `google/flash-image-3.1` | - |
| Google | Gemini 3.1 Flash-Lite Image (Nano Banana 2 Lite) | `google/flash-image-3.1-lite` | - |
| Black Forest Labs | FLUX.2 [pro] | `black-forest-labs/FLUX.2-pro` | - |
| Black Forest Labs | FLUX.2 [dev] | `black-forest-labs/FLUX.2-dev` | - |
| Black Forest Labs | FLUX.2 [flex] | `black-forest-labs/FLUX.2-flex` | - |
| Black Forest Labs | FLUX.2 [max] | `black-forest-labs/FLUX.2-max` | - |
| Black Forest Labs | FLUX1.1 [pro] | `black-forest-labs/FLUX.1.1-pro` | - |
| Black Forest Labs | FLUX.1 Kontext [pro] | `black-forest-labs/FLUX.1-kontext-pro` | 28 |
| Black Forest Labs | FLUX.1 Kontext [max] | `black-forest-labs/FLUX.1-kontext-max` | 28 |
| ByteDance | Seedream 5.0 Lite | `ByteDance/Seedream-5.0-lite` | - |
| ByteDance | Seedream 4.0 | `ByteDance-Seed/Seedream-4.0` | - |
| ByteDance | Seedream 3.0 | `ByteDance-Seed/Seedream-3.0` | - |
| Qwen | Qwen Image 2.0 Pro | `Qwen/Qwen-Image-2.0-Pro` | - |
| Qwen | Qwen Image 2.0 | `Qwen/Qwen-Image-2.0` | - |
| Qwen | Qwen Image | `Qwen/Qwen-Image` | - |
| Wan-AI | Wan 2.6 Image | `Wan-AI/Wan2.6-image` | - |
| Ideogram | Ideogram 4.0 | `ideogram/ideogram-4.0` | - |
| Ideogram | Ideogram 3.0 | `ideogram/ideogram-3.0` | - |
| Pruna AI | P-Image-Ideogram | `prunaai/p-image-ideogram` | - |
| RunDiffusion | Juggernaut Pro Flux | `RunDiffusion/Juggernaut-pro-flux` | - |
| RunDiffusion | Juggernaut Lightning Flux | `Rundiffusion/Juggernaut-Lightning-Flux` | - |
| Stability AI | SD XL | `stabilityai/stable-diffusion-xl-base-1.0` | - |

## Model Categories

### Text-to-Image (All models)

All models above support text-to-image generation via the `prompt` parameter.

### Image Editing (single reference via `image_url`)

- `black-forest-labs/FLUX.1-kontext-pro` -- Balanced speed/quality (recommended)
- `black-forest-labs/FLUX.1-kontext-max` -- Maximum editing quality
- `black-forest-labs/FLUX.2-pro` -- FLUX.2 editing
- `black-forest-labs/FLUX.2-flex` -- Adjustable guidance

### Multi-Image Guidance (via `reference_images`)

- `black-forest-labs/FLUX.2-pro`
- `black-forest-labs/FLUX.2-dev`
- `black-forest-labs/FLUX.2-flex`
- `google/gemini-3-pro-image`
- `google/flash-image-2.5`

## Recommended Models

| Use Case | Model | API String |
|----------|-------|-----------|
| Text-to-image (Together's pick) | GPT Image 2 | `openai/gpt-image-2` |
| Image-to-image (Together's pick) | GPT Image 2 | `openai/gpt-image-2` |
| Alternative to GPT Image 2 | Flash Image 2.5 | `google/flash-image-2.5` |
| Highest quality FLUX | FLUX.2 Pro | `black-forest-labs/FLUX.2-pro` |
| Image editing | FLUX.1 Kontext Max | `black-forest-labs/FLUX.1-kontext-max` |
| Typography | FLUX.2 Flex | `black-forest-labs/FLUX.2-flex` |
| Text in images | Ideogram 3.0 | `ideogram/ideogram-3.0` |
| Up to 4K output | Gemini 3 Pro Image | `google/gemini-3-pro-image` |

## FLUX.2 Model Comparison

| Variant | Best For | Unique Features |
|---------|----------|-----------------|
| Pro | Production, highest fidelity | Up to 9MP output, fastest |
| Dev | Development | `guidance_scale`, `steps` |
| Flex | Maximum control, typography | `guidance_scale`, `steps`, adjustable |

## Supported Dimensions

### Standard (most models)

- 1024x1024 (1:1), 1344x768 (16:9), 768x1344 (9:16)
- 1248x832 (3:2), 832x1248 (2:3)
- 1184x864 (4:3), 864x1184 (3:4)

### Gemini 3 Pro Image -- 1K

1024x1024, 1248x832, 832x1248, 1184x864, 864x1184, 896x1152, 1152x896, 768x1344, 1344x768,
1536x672

### Gemini 3 Pro Image -- 2K

2048x2048, 2496x1664, 1664x2496, 2368x1728, 1728x2368, 1792x2304, 2304x1792, 1536x2688,
2688x1536, 3072x1344

### Gemini 3 Pro Image -- 4K

4096x4096, 4992x3328, 3328x4992, 4736x3456, 3456x4736, 3584x4608, 4608x3584, 3072x5376,
5376x3072, 6144x2688

## FLUX Pricing Formula

Image models bill one of two ways; the **Unit** column of the
[serverless catalog](https://docs.together.ai/docs/serverless/models#image-models) says which
([How image models bill](https://docs.together.ai/docs/serverless/overview#how-image-models-bill)).

- **By megapixel** (models Together serves directly, such as FLUX1.1 [pro], FLUX.1 Kontext, and
  FLUX.2 [max]): cost scales with output megapixels, and is scaled up when you exceed the
  model's default step count.

  ```
  MP = Width x Height / 1,000,000
  Cost ~= MP x Price_per_MP   (higher when steps exceed the default)
  ```

- **By image, estimated** (provider-hosted models, which is most of them): the provider's own
  per-request charge is passed through, and varies with resolution and quality. Generate one
  image at the target settings to see the real cost before a large run.
