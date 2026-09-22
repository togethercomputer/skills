# Together AI: Video

Use Together AI video APIs for text-to-video and image-to-video generation, including keyframe control, model and dimension selection, and asynchronous job polling.

- text-to-video generation
- image-to-video generation
- first-frame and last-frame keyframe control
- asynchronous job polling
- local download of completed outputs

## Use this guide for

- Generate short videos from prompts
- Animate an existing image
- Choose among Veo, Sora, Kling, Seedance, PixVerse, Vidu, or other supported models
- Add polling and download logic to a product or script

## Do not use this guide for

- still-image generation or editing -> `domains/images.md`
- only when a custom video-serving runtime is required -> `domains/dedicated-containers.md`

## Workflow

1. Confirm whether the user needs text-to-video or image-to-video.
2. Choose the model based on duration, dimension, keyframe support, and audio support.
3. Submit the async job and poll until a terminal state.
4. Download the result promptly before signed URLs expire.

## Open next

- **Text-to-video generation**
  - Start with [scripts/video/generate_video.py](scripts/video/generate_video.py) or [scripts/video/generate_video.ts](scripts/video/generate_video.ts)
  - Read [references/video/api-reference.md](references/video/api-reference.md)
- **Image-to-video with keyframes**
  - Start with [scripts/video/image_to_video.py](scripts/video/image_to_video.py)
  - Read [references/video/api-reference.md](references/video/api-reference.md)
- **Parameter tuning, polling, or troubleshooting**
  - Read [references/video/api-reference.md](references/video/api-reference.md)
- **Model, dimension, and prompt-limit selection**
  - Read [references/video/models.md](references/video/models.md)

## Rules

- Together video generation is asynchronous; do not treat it like a synchronous image call.
- Keyframe support is model-specific. Validate support before promising first-plus-last-frame control.
- Keep polling and download logic as part of the workflow, not as an afterthought.
- Use explicit dimensions and generation parameters rather than relying on unstable defaults.

## Docs

- [Videos Overview](https://docs.together.ai/docs/videos-overview)
- [Create Video API](https://docs.together.ai/reference/create-videos)
