#!/usr/bin/env python3
"""
Together AI LoRA Image Generation -- Apply LoRA Adapters to FLUX (v2 SDK)

Generate images with custom LoRA adapters for unique styles.
Supports up to 2 LoRAs per image from Hugging Face, CivitAI,
Replicate, or direct .safetensors URLs.

Usage:
    python lora_generation.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

from together import Together

client = Together()

LORA_MODEL = "black-forest-labs/FLUX.2-dev"


def generate_with_lora(
    prompt: str,
    loras: list[dict],
    width: int = 1024,
    height: int = 768,
    steps: int = 28,
    seed: int | None = None,
) -> str:
    """Generate an image with LoRA adapters applied."""
    kwargs: dict = dict(
        model=LORA_MODEL,
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        image_loras=loras,
    )
    if seed is not None:
        kwargs["seed"] = seed

    response = client.images.generate(**kwargs)
    url = response.data[0].url
    print(f"  Image: {url}")
    return url


if __name__ == "__main__":
    # --- Example 1: Single LoRA (realism) ---
    print("=== Realism LoRA ===")
    generate_with_lora(
        prompt="a professional photograph of a woman in a modern cafe",
        loras=[
            {
                "path": "https://huggingface.co/XLabs-AI/flux-RealismLora",
                "scale": 0.8,
            },
        ],
    )

    # --- Example 2: Two LoRAs combined ---
    print("\n=== Two LoRAs Combined ===")
    generate_with_lora(
        prompt="a BLKLGHT image of a man walking outside on a rainy day",
        loras=[
            {
                "path": "https://replicate.com/fofr/flux-black-light",
                "scale": 0.8,
            },
            {
                "path": "https://huggingface.co/XLabs-AI/flux-RealismLora",
                "scale": 0.5,
            },
        ],
    )

    # --- Example 3: Different scales ---
    print("\n=== Subtle LoRA (low scale) ===")
    generate_with_lora(
        prompt="a portrait photo of a young man in golden hour lighting",
        loras=[
            {
                "path": "https://huggingface.co/XLabs-AI/flux-RealismLora",
                "scale": 0.3,
            },
        ],
    )

    print("\n=== Strong LoRA (high scale) ===")
    generate_with_lora(
        prompt="a portrait photo of a young man in golden hour lighting",
        loras=[
            {
                "path": "https://huggingface.co/XLabs-AI/flux-RealismLora",
                "scale": 1.2,
            },
        ],
    )
