#!/usr/bin/env python3
"""
Together AI Image Generation -- Text-to-Image and FLUX.2 (v2 SDK)

Generate images from text prompts, save locally, create variations,
and use FLUX.2 reference images.

Usage:
    python generate_image.py

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import base64
import pathlib
from together import Together

client = Together()


def save_image_bytes(data: bytes, output_path: str) -> str:
    """Write image bytes under an extension that matches their real format.

    Image models return JPEG by default (`output_format` defaults to "jpeg"), so
    "out.png" would otherwise hold JPEG bytes. Returns the path
    actually written.
    """
    signatures = {b"\x89PNG\r\n\x1a\n": ".png", b"\xff\xd8\xff": ".jpg", b"RIFF": ".webp"}
    actual = next((ext for sig, ext in signatures.items() if data.startswith(sig)), None)
    path = pathlib.Path(output_path)
    if actual and path.suffix.lower() not in ({actual} | ({".jpeg"} if actual == ".jpg" else set())):
        print(f"  Note: model returned {actual[1:].upper()} bytes; saving as {path.with_suffix(actual).name}")
        path = path.with_suffix(actual)
    path.write_bytes(data)
    return str(path)


def generate_image_url(
    prompt: str,
    model: str = "black-forest-labs/FLUX.2-dev",
    width: int = 1024,
    height: int = 1024,
    steps: int = 20,
    n: int = 1,
    seed: int | None = None,
) -> list[str]:
    """Generate image(s) and return URL(s)."""
    kwargs: dict = dict(
        model=model,
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        n=n,
    )
    if seed is not None:
        kwargs["seed"] = seed

    response = client.images.generate(**kwargs)
    urls = [img.url for img in response.data]
    for i, url in enumerate(urls):
        print(f"  Image {i}: {url}")
    return urls


def generate_and_save(
    prompt: str,
    output_path: str = "output.png",
    model: str = "black-forest-labs/FLUX.2-dev",
    width: int = 1024,
    height: int = 1024,
    steps: int = 20,
) -> str:
    """Generate an image and save it locally via base64."""
    response = client.images.generate(
        model=model,
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        n=1,
        response_format="base64",
    )
    image_data = base64.b64decode(response.data[0].b64_json)
    saved = save_image_bytes(image_data, output_path)
    print(f"  Saved to {saved} ({len(image_data)} bytes)")
    return saved


def generate_flux2(
    prompt: str,
    model: str = "black-forest-labs/FLUX.2-pro",
    width: int = 1024,
    height: int = 768,
    reference_images: list[str] | None = None,
    prompt_upsampling: bool = True,
    output_format: str = "png",
) -> str:
    """Generate with FLUX.2 features (prompt upsampling, reference images)."""
    kwargs: dict = dict(
        model=model,
        prompt=prompt,
        width=width,
        height=height,
        output_format=output_format,
        # FLUX.2 [pro] only. The SDK has no prompt_upsampling argument, so it goes
        # through extra_body.
        extra_body={"prompt_upsampling": prompt_upsampling},
    )
    if reference_images:
        kwargs["reference_images"] = reference_images

    response = client.images.generate(**kwargs)
    url = response.data[0].url
    print(f"  FLUX.2 image: {url}")
    return url


if __name__ == "__main__":
    # --- Example 1: Basic text-to-image ---
    print("=== Basic Generation ===")
    generate_image_url(
        prompt="A serene mountain landscape at sunset, digital art",
        steps=20,
    )

    # --- Example 2: Save locally ---
    print("\n=== Save to File ===")
    generate_and_save(
        prompt="A futuristic city skyline with flying cars",
        output_path="city.png",
        steps=20,
    )

    # --- Example 3: Multiple variations ---
    print("\n=== 3 Variations ===")
    generate_image_url(
        prompt="A cute robot reading a book",
        n=3,
        steps=20,
    )

    # --- Example 4: Reproducible with seed ---
    print("\n=== Reproducible (seed=42) ===")
    generate_image_url(
        prompt="Abstract geometric pattern in blue and gold",
        seed=42,
        steps=20,
    )

    # --- Example 5: FLUX.2 with prompt upsampling ---
    print("\n=== FLUX.2 Pro ===")
    generate_flux2(
        prompt="A mountain landscape at sunset with golden light reflecting on a calm lake",
    )

    # --- Example 6: FLUX.2 with reference image ---
    # print("\n=== FLUX.2 Reference Image ===")
    # generate_flux2(
    #     prompt="Replace the color of the car to blue",
    #     reference_images=["https://images.pexels.com/photos/3729464/pexels-photo-3729464.jpeg"],
    # )
