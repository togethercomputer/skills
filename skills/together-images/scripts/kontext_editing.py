#!/usr/bin/env python3
"""
Together AI Kontext -- Image Editing with Text+Image Prompts (v2 SDK)

Edit existing images using FLUX.1 Kontext models: style transfer,
object modification, scene transformation, and character creation.

Usage:
    python kontext_editing.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

from together import Together

client = Together()

KONTEXT_PRO = "black-forest-labs/FLUX.1-kontext-pro"
KONTEXT_MAX = "black-forest-labs/FLUX.1-kontext-max"


def edit_image(
    prompt: str,
    image_url: str,
    model: str = KONTEXT_PRO,
    width: int = 1024,
    height: int = 1024,
    steps: int = 28,
    seed: int | None = None,
) -> str:
    """Edit an existing image using a text prompt."""
    kwargs: dict = dict(
        model=model,
        prompt=prompt,
        image_url=image_url,
        width=width,
        height=height,
        steps=steps,
    )
    if seed is not None:
        kwargs["seed"] = seed

    response = client.images.generate(**kwargs)
    url = response.data[0].url
    print(f"  Edited image: {url}")
    return url


def style_transfer(image_url: str, style: str, **kwargs) -> str:
    """Apply a style to an image (watercolor, oil painting, etc.)."""
    print(f"  Style: {style}")
    return edit_image(
        prompt=f"Transform this into a {style}",
        image_url=image_url,
        **kwargs,
    )


def modify_object(image_url: str, modification: str, **kwargs) -> str:
    """Modify a specific object or attribute in an image."""
    print(f"  Modification: {modification}")
    return edit_image(
        prompt=modification,
        image_url=image_url,
        **kwargs,
    )


if __name__ == "__main__":
    # Source image for editing examples
    SOURCE_IMAGE = "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg"

    # --- Example 1: Style transfer ---
    print("=== Style Transfer ===")
    style_transfer(SOURCE_IMAGE, "watercolor painting")

    # --- Example 2: Object modification ---
    print("\n=== Object Modification ===")
    modify_object(SOURCE_IMAGE, "Make the cat wear a tiny top hat")

    # --- Example 3: Scene transformation ---
    print("\n=== Scene Transformation ===")
    edit_image(
        prompt="Place this cat in a snowy winter landscape",
        image_url=SOURCE_IMAGE,
        width=1344,
        height=768,
    )

    # --- Example 4: Landscape aspect ratio ---
    print("\n=== Landscape Edit ===")
    edit_image(
        prompt="Transform this into a pencil sketch",
        image_url=SOURCE_IMAGE,
        width=1536,
        height=1024,
    )

    # --- Example 5: Reproducible edit ---
    print("\n=== Reproducible Edit (seed=42) ===")
    edit_image(
        prompt="Make this a pop art poster",
        image_url=SOURCE_IMAGE,
        seed=42,
    )
