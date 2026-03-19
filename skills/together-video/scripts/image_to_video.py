#!/usr/bin/env python3
"""
Together AI Video -- Image-to-Video with Keyframe Control (v2 SDK)

Animate images using keyframe control. Supports first frame, last frame,
and first+last frame control depending on model.

Usage:
    python image_to_video.py

Requires:
    pip install together requests
    export TOGETHER_API_KEY=your_key
"""

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


def image_to_video_url(
    prompt: str,
    image_url: str,
    model: str = "minimax/hailuo-02",
    frame: str = "first",
    width: int = 1366,
    height: int = 768,
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
    return wait_for_video(job.id)


def image_to_video_base64(
    prompt: str,
    image_path: str,
    model: str = "minimax/hailuo-02",
    frame: str = "first",
    width: int = 1366,
    height: int = 768,
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
    return wait_for_video(job.id)


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
    SOURCE_IMAGE = "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg"

    # --- Example 1: Animate an image from URL ---
    print("=== Image-to-Video (URL) ===")
    image_to_video_url(
        prompt="The cat slowly turns its head and blinks",
        image_url=SOURCE_IMAGE,
    )

    # --- Example 2: First + Last keyframes (Seedance) ---
    # print("\n=== First + Last Keyframes ===")
    # first_and_last_keyframes(
    #     prompt="Smooth transition from day to night",
    #     first_image_url="https://example.com/day.jpg",
    #     last_image_url="https://example.com/night.jpg",
    # )

    # --- Example 3: Local file (base64) ---
    # print("\n=== Image-to-Video (Local File) ===")
    # image_to_video_base64(
    #     prompt="Camera slowly pans across the scene",
    #     image_path="./my_image.jpg",
    # )
