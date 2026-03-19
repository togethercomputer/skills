#!/usr/bin/env python3
"""
Together AI Image Generation -- Text-to-Image and FLUX.2 (v2 SDK)

Generate images from text prompts, save locally, create variations,
and use FLUX.2 reference images.

Usage:
    python generate_image.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import base64
from together import Together

client = Together()


def generate_image_url(
    prompt: str,
    model: str = "black-forest-labs/FLUX.1-schnell",
    width: int = 1024,
    height: int = 1024,
    steps: int = 4,
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
    model: str = "black-forest-labs/FLUX.1-schnell",
    width: int = 1024,
    height: int = 1024,
    steps: int = 4,
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

    with open(output_path, "wb") as f:
        f.write(image_data)

    print(f"  Saved to {output_path} ({len(image_data)} bytes)")
    return output_path


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
        prompt_upsampling=prompt_upsampling,
        output_format=output_format,
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
        steps=4,
    )

    # --- Example 2: Save locally ---
    print("\n=== Save to File ===")
    generate_and_save(
        prompt="A futuristic city skyline with flying cars",
        output_path="city.png",
        steps=4,
    )

    # --- Example 3: Multiple variations ---
    print("\n=== 3 Variations ===")
    generate_image_url(
        prompt="A cute robot reading a book",
        n=3,
        steps=4,
    )

    # --- Example 4: Reproducible with seed ---
    print("\n=== Reproducible (seed=42) ===")
    generate_image_url(
        prompt="Abstract geometric pattern in blue and gold",
        seed=42,
        steps=4,
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
