# Together AI: Video

Text-to-video and image-to-video, billed per video. Every request is an **async job**: create,
poll to a terminal state, then download. Still images go to `domains/images.md`.

## Workflow

1. Decide text-to-video or image-to-video (first and/or last keyframe).
2. Pick the model by duration, resolution, keyframe and audio support; for example
   `google/veo-3.1`, `ByteDance/Seedance-2.0`, `minimax/hailuo-02`, `Wan-AI/wan2.7-i2v`.
3. `client.videos.create(...)`, then poll `client.videos.retrieve(job.id)` every 10 to 60 seconds
   until `completed`, `failed`, or `cancelled` (it passes through `queued` and `in_progress`).
4. Download `outputs.video_url` immediately; the signed URL expires.

## Rules

- Do not treat video like a synchronous image call, and do not end the task while a job you
  submitted is still `queued` or `in_progress`.
- Keyframe and reference-image support are model-specific; check before promising them.
- Set dimensions and duration explicitly rather than relying on defaults.
- HTTP 402 `insufficient balance` is an account problem; switching models will not help.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/video/generate_video.py](scripts/video/generate_video.py) (.ts) | 130 | text-to-video, polling loop, reference images, download | generating from a prompt |
| [scripts/video/image_to_video.py](scripts/video/image_to_video.py) | 160 | first/last keyframe control | animating an image |
| [references/video/models.md](references/video/models.md) | 59 | model table, per-model dimensions, feature support, prompt limits | choosing a model or size |
| [references/video/api-reference.md](references/video/api-reference.md) | 312 | create and status fields, job statuses, polling pattern, guidance and steps, troubleshooting | a parameter or failure not covered above |

## Docs

- [Videos Overview](https://docs.together.ai/docs/inference/videos/overview)
- [Create Video API](https://docs.together.ai/reference/create-videos)
