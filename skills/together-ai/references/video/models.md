# Video Generation Models Reference

## Complete Model Table

Serverless video models as of 2026-10-07 (source: [Serverless models](https://docs.together.ai/docs/serverless/models)). If a listed model returns an unavailable error, treat the runtime response and the [deprecations page](https://docs.together.ai/docs/deprecations) as the source of truth. `-` means not stated in the catalog: check the model's docs page before relying on a duration, size, or keyframe mode. Names ending in I2V take an input image; R2V takes reference media.

| Organization | Model | API String | Duration | Dimensions | FPS | Keyframes |
|-------------|-------|-----------|----------|-----------|-----|-----------|
| MiniMax | Hailuo 02 | `minimax/hailuo-02` | 10s | 1366x768, 1920x1080 | 25 | First |
| MiniMax | Video 01 Director | `minimax/video-01-director` | 5s | 1366x768 | 25 | First |
| ByteDance | Seedance 1.0 Pro | `ByteDance/Seedance-1.0-pro` | 5s | Multiple (see below) | 24 | First, Last |
| ByteDance | Seedance 1.0 Lite | `ByteDance/Seedance-1.0-lite` | 5s | Multiple (see below) | 24 | First, Last |
| PixVerse | PixVerse v5 | `pixverse/pixverse-v5` | 5s | Multiple (see below) | 16, 24 | First, Last |
| Vidu | Vidu Q1 | `vidu/vidu-q1` | 5s | 1920x1080, 1080x1080, 1080x1920 | 24 | First, Last |
| Google | Veo 3.1 | `google/veo-3.1` | - | - | - | - |
| Google | Veo 3.1 Lite | `google/veo-3.1-lite` | - | - | - | - |
| ByteDance | Seedance 2.5 | `ByteDance/Seedance-2.5` | - | - | - | - |
| ByteDance | Seedance 2.0 | `ByteDance/Seedance-2.0` | - | - | - | - |
| Black Forest Labs | FLUX 3 | `black-forest-labs/FLUX-3` | - | - | - | - |
| Wan-AI | Wan 2.7 T2V | `Wan-AI/wan2.7-t2v` | - | - | - | - |
| Wan-AI | Wan 2.7 I2V | `Wan-AI/wan2.7-i2v` | - | - | - | - |
| Wan-AI | Wan 2.7 R2V | `Wan-AI/wan2.7-r2v` | - | - | - | - |
| Alibaba | HappyHorse 1.1 T2V | `alibaba/happyhorse-1.1-t2v` | - | - | - | - |
| Alibaba | HappyHorse 1.1 I2V | `alibaba/happyhorse-1.1-i2v` | - | - | - | - |
| Alibaba | HappyHorse 1.1 R2V | `alibaba/happyhorse-1.1-r2v` | - | - | - | - |
| PixVerse | PixVerse v6 | `pixverse/pixverse-v6` | - | - | - | - |
| PixVerse | PixVerse v5.6 | `pixverse/pixverse-v5.6` | - | - | - | - |
| Vidu | Vidu Q3 | `vidu/vidu-q3` | - | - | - | - |
| Vidu | Vidu Q3 Turbo | `vidu/vidu-q3-turbo` | - | - | - | - |
| MiniMax | MiniMax H3 | `MiniMaxAI/MiniMax-H3` | 1s | 2k | - | - |

## Seedance Dimensions

864x480, 736x544, 640x640, 960x416, 416x960, 1248x704, 1120x832, 960x960, 1504x640, 640x1504

## PixVerse v5 Dimensions

640x360, 480x360, 360x360, 270x360, 360x640, 960x540, 720x540, 540x540, 405x540, 540x960,
1280x720, 960x720, 720x720, 540x720, 720x1280, 1920x1080, 1440x1080, 1080x1080, 810x1080,
1080x1920

## Feature Support

Current models only; for anything not listed, check the model's docs page.

| Feature | Models |
|---------|--------|
| Reference images | Hailuo 02, and the R2V models (Wan 2.7 R2V, HappyHorse R2V) |
| Image input (I2V) | Wan 2.7 I2V, HappyHorse I2V |
| First + Last keyframe | Seedance 1.0 Pro and Lite, PixVerse v5, Vidu Q1 |
| 10 second duration | Hailuo 02 |
| 1080p output | Seedance 1.0 Pro, PixVerse v5, Vidu Q1 |

## Prompt Limits

| Model | Prompt Length |
|-------|-------------|
| Most models | 2-3,000 characters |
| PixVerse v5 | 2-2,048 characters |
