# Video Generation Models Reference

## Complete Model Table

| Organization | Model | API String | Duration | Dimensions | FPS | Keyframes |
|-------------|-------|-----------|----------|-----------|-----|-----------|
| Google | Veo 3.0 | `google/veo-3.0` | 8s | 1280x720, 720x1280, 1920x1080, 1080x1920 | 24 | First |
| Google | Veo 3.0 + Audio | `google/veo-3.0-audio` | 8s | 1280x720, 720x1280, 1920x1080, 1080x1920 | 24 | First |
| Google | Veo 3.0 Fast | `google/veo-3.0-fast` | 8s | 1280x720, 720x1280, 1920x1080, 1080x1920 | 24 | First |
| Google | Veo 3.0 Fast + Audio | `google/veo-3.0-fast-audio` | 8s | 1280x720, 720x1280, 1920x1080, 1080x1920 | 24 | First |
| Google | Veo 2.0 | `google/veo-2.0` | 5s | 1280x720, 720x1280 | 24 | First, Last |
| OpenAI | Sora 2 | `openai/sora-2` | 8s | 1280x720, 720x1280 | - | First |
| OpenAI | Sora 2 Pro | `openai/sora-2-pro` | 8s | 1280x720, 720x1280 | - | First |
| MiniMax | Hailuo 02 | `minimax/hailuo-02` | 10s | 1366x768, 1920x1080 | 25 | First |
| MiniMax | Video 01 Director | `minimax/video-01-director` | 5s | 1366x768 | 25 | First |
| Kuaishou | Kling 2.1 Master | `kwaivgI/kling-2.1-master` | 5s | 1920x1080, 1080x1080, 1080x1920 | 24 | First |
| Kuaishou | Kling 2.1 Standard | `kwaivgI/kling-2.1-standard` | 5s | 1920x1080, 1080x1080, 1080x1920 | 24 | First |
| Kuaishou | Kling 2.1 Pro | `kwaivgI/kling-2.1-pro` | 5s | 1920x1080, 1080x1080, 1080x1920 | 24 | First, Last |
| Kuaishou | Kling 2.0 Master | `kwaivgI/kling-2.0-master` | 5s | 1280x720, 720x720, 720x1280 | 24 | First |
| Kuaishou | Kling 1.6 Standard | `kwaivgI/kling-1.6-standard` | 5s | 1920x1080, 1080x1080, 1080x1920 | 30, 24 | First |
| Kuaishou | Kling 1.6 Pro | `kwaivgI/kling-1.6-pro` | 5s | 1920x1080, 1080x1080, 1080x1920 | 24 | First |
| ByteDance | Seedance 1.0 Pro | `ByteDance/Seedance-1.0-pro` | 5s | Multiple (see below) | 24 | First, Last |
| ByteDance | Seedance 1.0 Lite | `ByteDance/Seedance-1.0-lite` | 5s | Multiple (see below) | 24 | First, Last |
| PixVerse | PixVerse v5 | `pixverse/pixverse-v5` | 5s | Multiple (see below) | 16, 24 | First, Last |
| Vidu | Vidu 2.0 | `vidu/vidu-2.0` | 8s | Multiple (see below) | 24 | First, Last |
| Vidu | Vidu Q1 | `vidu/vidu-q1` | 5s | 1920x1080, 1080x1080, 1080x1920 | 24 | First, Last |
| Wan-AI | Wan 2.2 T2V | `Wan-AI/Wan2.2-T2V-A14B` | - | - | - | Text-to-Video |
| Wan-AI | Wan 2.2 I2V | `Wan-AI/Wan2.2-I2V-A14B` | - | - | - | Image-to-Video |

## Seedance Dimensions

864x480, 736x544, 640x640, 960x416, 416x960, 1248x704, 1120x832, 960x960, 1504x640, 640x1504

## PixVerse v5 Dimensions

640x360, 480x360, 360x360, 270x360, 360x640, 960x540, 720x540, 540x540, 405x540, 540x960,
1280x720, 960x720, 720x720, 540x720, 720x1280, 1920x1080, 1440x1080, 1080x1080, 810x1080,
1080x1920

## Vidu 2.0 Dimensions

1920x1080, 1080x1080, 1080x1920, 1280x720, 720x720, 720x1280, 640x360, 360x360, 360x640

## Feature Support

| Feature | Models |
|---------|--------|
| Audio generation | Veo 3.0 + Audio, Veo 3.0 Fast + Audio |
| Reference images | Vidu 2.0 |
| First + Last keyframe | Veo 2.0, Kling 2.1 Pro, Seedance, PixVerse, Vidu |
| 10 second duration | Hailuo 02 |
| 1080p output | Veo 3.0, Seedance Pro, PixVerse, Kling 2.1, Vidu Q1, Sora 2 Pro |
| No prompt required | Kling 2.1 Standard/Pro, Kling 1.6 Pro |

## Prompt Limits

| Model | Prompt Length |
|-------|-------------|
| Most models | 2-3,000 characters |
| PixVerse v5 | 2-2,048 characters |
| Kling 2.1 Master | 2-2,500 characters |
| Sora 2 / 2 Pro | 1-4,000 characters |
