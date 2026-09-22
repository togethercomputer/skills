#!/usr/bin/env python3
"""
Together AI Video Generation -- Text-to-Video with Polling (v2 SDK)

Submit a video job, poll for completion, and download the result.
Demonstrates text-to-video, advanced parameters, and reference images.

Usage:
    python generate_video.py

Requires:
    uv pip install "together>=2.0.0" requests
    export TOGETHER_API_KEY=your_key
"""

import time

import requests
from together import Together

client = Together()


def wait_for_video(job_id: str, poll_interval: int = 5, timeout: int = 600) -> str:
    """Poll a video job until completion. Returns the video URL."""
    elapsed = 0
    while elapsed < timeout:
        status = client.videos.retrieve(job_id)
        print(f"  Status: {status.status}  ({elapsed}s)")

        if status.status == "completed":
            video_url = status.outputs.video_url
            cost = status.outputs.cost
            print(f"  Video ready! Cost: ${cost}")
            print(f"  URL: {video_url}")
            return video_url
        elif status.status == "failed":
            error = getattr(status, "error", None)
            raise RuntimeError(f"Video generation failed: {error}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Video job {job_id} did not complete within {timeout}s")


def text_to_video(
    prompt: str,
    model: str = "minimax/video-01-director",
    width: int = 1366,
    height: int = 768,
    **kwargs,
) -> str:
    """Generate a video from a text prompt."""
    job = client.videos.create(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        **kwargs,
    )
    print(f"Submitted job: {job.id}")
    return wait_for_video(job.id)


def text_to_video_advanced(
    prompt: str,
    model: str = "minimax/hailuo-02",
) -> str:
    """Generate a video with advanced parameters."""
    job = client.videos.create(
        prompt=prompt,
        model=model,
        width=1366,
        height=768,
        seconds="6",
        fps=30,
        steps=30,
        guidance_scale=8.0,
        output_format="MP4",
        output_quality=20,
        seed=42,
        negative_prompt="blurry, low quality, distorted",
    )
    print(f"Submitted job: {job.id}")
    return wait_for_video(job.id)


def video_with_reference(
    prompt: str,
    reference_images: list[str],
    model: str = "vidu/vidu-2.0",
) -> str:
    """Generate a video guided by reference images (Vidu 2.0)."""
    job = client.videos.create(
        prompt=prompt,
        model=model,
        width=1280,
        height=720,
        reference_images=reference_images,
    )
    print(f"Submitted job: {job.id}")
    return wait_for_video(job.id)


if __name__ == "__main__":
    # --- Example 1: Basic text-to-video ---
    print("=== Basic Text-to-Video ===")
    url = text_to_video(
        prompt="A serene sunset over the ocean with gentle waves lapping at the shore",
    )

    # Download the video
    response = requests.get(url)
    with open("output.mp4", "wb") as f:
        f.write(response.content)
    print(f"  Saved to output.mp4 ({len(response.content)} bytes)")

    # --- Example 2: Advanced parameters ---
    # print("\n=== Advanced Parameters ===")
    # text_to_video_advanced(
    #     prompt="A futuristic city at night with neon lights reflecting on wet streets",
    # )

    # --- Example 3: Reference images (Vidu 2.0) ---
    # print("\n=== Reference Images ===")
    # video_with_reference(
    #     prompt="A cat dancing energetically",
    #     reference_images=["https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg"],
    # )
