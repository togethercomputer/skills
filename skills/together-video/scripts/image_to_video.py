#!/usr/bin/env python3
"""
Together AI Video -- Image-to-Video with Keyframe Control (v2 SDK)

Animate images using keyframe control, poll until completion, and download the MP4.
Supports first frame, last frame, and first+last frame control depending on model.

Usage:
    python image_to_video.py <image_url_or_path> [--prompt "..."] [--output promo.mp4]

Requires:
    pip install together requests
    export TOGETHER_API_KEY=your_key
"""

import argparse
import base64
import time
import requests as http_requests
from together import Together

client = Together()


def wait_for_video(job_id: str, poll_interval: int = 5, timeout: int = 600) -> str:
    """Poll a video job until completion. Returns the video URL."""
    elapsed = 0
    while elapsed < timeout:
        status = client.videos.retrieve(job_id)
        print(f"  Status: {status.status}  ({elapsed}s)")

        if status.status == "completed":
            print(f"  Video URL: {status.outputs.video_url}")
            return status.outputs.video_url
        elif status.status == "failed":
            error = getattr(status, "error", None)
            raise RuntimeError(f"Video generation failed: {error}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Video job {job_id} did not complete within {timeout}s")


def download_video(video_url: str, output_file: str) -> None:
    """Download the completed video to a local file."""
    response = http_requests.get(video_url, timeout=120)
    response.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(response.content)
    print(f"Saved to {output_file} ({len(response.content)} bytes)")


def image_to_video_url(
    prompt: str,
    image_url: str,
    model: str = "minimax/video-01-director",
    frame: str = "first",
    width: int = 1366,
    height: int = 768,
    output_file: str = "promo.mp4",
) -> str:
    """Animate an image using a URL (no base64 encoding needed)."""
    job = client.videos.create(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        frame_images=[{"input_image": image_url, "frame": frame}],
    )
    print(f"Submitted job: {job.id}")
    video_url = wait_for_video(job.id)
    download_video(video_url, output_file)
    return video_url


def image_to_video_base64(
    prompt: str,
    image_path: str,
    model: str = "minimax/video-01-director",
    frame: str = "first",
    width: int = 1366,
    height: int = 768,
    output_file: str = "promo.mp4",
) -> str:
    """Animate an image from a local file (base64-encoded)."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    job = client.videos.create(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        frame_images=[{"input_image": img_b64, "frame": frame}],
    )
    print(f"Submitted job: {job.id}")
    video_url = wait_for_video(job.id)
    download_video(video_url, output_file)
    return video_url


def first_and_last_keyframes(
    prompt: str,
    first_image_url: str,
    last_image_url: str,
    model: str = "ByteDance/Seedance-1.0-pro",
    width: int = 1248,
    height: int = 704,
) -> str:
    """Animate between two keyframes (first and last frame)."""
    job = client.videos.create(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        frame_images=[
            {"input_image": first_image_url, "frame": "first"},
            {"input_image": last_image_url, "frame": "last"},
        ],
    )
    print(f"Submitted job: {job.id}")
    return wait_for_video(job.id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a promo clip from a single image.")
    parser.add_argument("image", help="Image URL or local file path")
    parser.add_argument(
        "--prompt",
        default="Turn this single image into a 5-second promo clip with a slow cinematic camera move",
        help="Video prompt",
    )
    parser.add_argument("--output", default="promo.mp4", help="Where to save the downloaded MP4")
    parser.add_argument("--model", default="minimax/video-01-director", help="Video model")
    parser.add_argument("--frame", default="first", help="Keyframe position: first or last")
    parser.add_argument("--width", type=int, default=1366, help="Output width")
    parser.add_argument("--height", type=int, default=768, help="Output height")
    args = parser.parse_args()

    if args.image.startswith(("http://", "https://")):
        image_to_video_url(
            prompt=args.prompt,
            image_url=args.image,
            model=args.model,
            frame=args.frame,
            width=args.width,
            height=args.height,
            output_file=args.output,
        )
    else:
        image_to_video_base64(
            prompt=args.prompt,
            image_path=args.image,
            model=args.model,
            frame=args.frame,
            width=args.width,
            height=args.height,
            output_file=args.output,
        )
