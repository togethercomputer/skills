#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- VLM (Vision-Language) Fine-Tuning (v2 SDK)

Prepare image+text training data with base64-encoded images, upload,
and fine-tune a vision-language model.

Usage:
    python vlm_finetune.py

Requires:
    pip install together requests
    export TOGETHER_API_KEY=your_key
"""

import base64
import json
import time
import tempfile
import requests
from together import Together

client = Together()


def url_to_base64(url: str, mime_type: str = "image/jpeg") -> str:
    """Download an image URL and return a base64 data URI."""
    response = requests.get(url)
    response.raise_for_status()
    encoded = base64.b64encode(response.content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


# --- 1. Prepare VLM training data ---
# In production, replace these with your actual image URLs and labels.
# Images must be base64 encoded with MIME prefix.
# Max 10 images per example, 10MB each. Formats: PNG, JPEG, WEBP.

# For this example, we create a small placeholder dataset.
# Replace with real base64 images for actual training.
PLACEHOLDER_BASE64 = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="  # Truncated placeholder

vlm_training_data = [
    {
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful vision assistant."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "How many items are in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": PLACEHOLDER_BASE64},
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "There are 3 items in the image."}],
            },
        ]
    },
    {
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful vision assistant."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe what you see in this image."},
                    {
                        "type": "image_url",
                        "image_url": {"url": PLACEHOLDER_BASE64},
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "The image shows a desk with a laptop, a coffee mug, and a notebook.",
                    }
                ],
            },
        ]
    },
    # Add more examples with real base64 images for production use...
]

data_path = tempfile.mktemp(suffix=".jsonl")
with open(data_path, "w") as f:
    for example in vlm_training_data:
        f.write(json.dumps(example) + "\n")

print(f"Wrote {len(vlm_training_data)} VLM examples to {data_path}")

# --- 2. Upload ---
file_resp = client.files.upload(file=data_path, purpose="fine-tune", check=True)
print(f"Uploaded file: {file_resp.id}")

# --- 3. Start VLM LoRA fine-tuning ---
job = client.fine_tuning.create(
    training_file=file_resp.id,
    model="Qwen/Qwen3-VL-8B-Instruct",
    lora=True,
    train_vision=False,  # Set True to also update vision encoder weights
    n_epochs=3,
    learning_rate=1e-5,
    suffix="vlm-v1",
)
print(f"Created VLM fine-tuning job: {job.id}")

# --- 4. Monitor ---
while True:
    status = client.fine_tuning.retrieve(id=job.id)
    print(f"  Status: {status.status}")
    if status.status == "completed":
        print(f"\nVLM training complete! Output: {status.output_name}")
        break
    elif status.status in ("failed", "cancelled"):
        print(f"Job ended: {status.status}")
        exit(1)
    time.sleep(30)

# --- 5. Test VLM inference ---
print("\n--- Testing VLM inference ---")
response = client.chat.completions.create(
    model=status.output_name,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What do you see in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": PLACEHOLDER_BASE64},
                },
            ],
        }
    ],
    max_tokens=512,
)
print(f"VLM response: {response.choices[0].message.content}")
