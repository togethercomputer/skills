#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- VLM (Vision-Language) Fine-Tuning (v2 SDK)

Prepare image+text training data with base64-encoded images, upload,
and fine-tune a vision-language model.

Usage:
    python vlm_finetune.py
    python vlm_finetune.py --training-file vlm.jsonl --model Qwen/Qwen3-VL-8B-Instruct
    python vlm_finetune.py --sample-image-url https://example.com/image.jpg

Requires:
    uv pip install "together>=2.0.0" requests
    export TOGETHER_API_KEY=your_key
"""

import argparse
import base64
import json
import tempfile
import time
from pathlib import Path

import requests
from together import Together

client = Together()


def url_to_base64(url: str, mime_type: str = "image/jpeg") -> str:
    """Download an image URL and return a base64 data URI."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    encoded = base64.b64encode(response.content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def sample_training_data(image_data_uri: str) -> list[dict]:
    """Return a small VLM fine-tuning dataset."""
    return [
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
                        {"type": "image_url", "image_url": {"url": image_data_uri}},
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
                        {"type": "image_url", "image_url": {"url": image_data_uri}},
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
    ]


def create_temp_dataset(rows: list[dict]) -> Path:
    """Write JSONL rows to a temporary file."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for example in rows:
            temp_file.write(json.dumps(example) + "\n")
        return Path(temp_file.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI VLM fine-tuning workflow")
    parser.add_argument("--training-file", help="Path to a VLM training JSONL file")
    parser.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct", help="Base VLM to fine-tune")
    parser.add_argument("--suffix", default="vlm-v1", help="Suffix for the fine-tuned model")
    parser.add_argument("--n-epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Training learning rate")
    parser.add_argument(
        "--train-vision",
        action="store_true",
        help="Also train the vision encoder instead of text-only LoRA updates",
    )
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between status checks")
    parser.add_argument("--sample-image-url", help="Optional image URL to embed into the bundled sample dataset")
    parser.add_argument(
        "--test-prompt",
        default="What do you see in this image?",
        help="Prompt to use when testing the fine-tuned model",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path: Path | None = None
    upload_path = args.training_file
    sample_image = (
        url_to_base64(args.sample_image_url)
        if args.sample_image_url
        else "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    )
    if upload_path is None:
        vlm_training_data = sample_training_data(sample_image)
        data_path = create_temp_dataset(vlm_training_data)
        upload_path = str(data_path)
        print(f"Wrote {len(vlm_training_data)} VLM examples to {data_path}")

    # --- 2. Upload ---
    try:
        file_resp = client.files.upload(file=upload_path, purpose="fine-tune", check=True)
    finally:
        if data_path is not None:
            data_path.unlink(missing_ok=True)
    print(f"Uploaded file: {file_resp.id}")

    # --- 3. Start VLM LoRA fine-tuning ---
    job = client.fine_tuning.create(
        training_file=file_resp.id,
        model=args.model,
        lora=True,
        train_vision=args.train_vision,
        n_epochs=args.n_epochs,
        learning_rate=args.learning_rate,
        suffix=args.suffix,
    )
    print(f"Created VLM fine-tuning job: {job.id}")

    # --- 4. Monitor ---
    while True:
        status = client.fine_tuning.retrieve(id=job.id)
        print(f"  Status: {status.status}")
        if status.status == "completed":
            print(f"\nVLM training complete! Output: {status.x_model_output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"Job ended: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 5. Deploy and test VLM inference ---
    print("\n--- Deploying fine-tuned VLM ---")
    output_model = status.x_model_output_name
    endpoint = client.endpoints.create(
        display_name="VLM Fine-tuned",
        model=output_model,
        hardware="4x_nvidia_h100_80gb_sxm",
        autoscaling={"min_replicas": 1, "max_replicas": 1},
    )
    print(f"Created endpoint: {endpoint.id}")

    while True:
        ep = client.endpoints.retrieve(endpoint.id)
        print(f"  Endpoint state: {ep.state}")
        if ep.state == "STARTED":
            break
        if ep.state in ("FAILED", "STOPPED"):
            print(f"Endpoint {ep.state}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    print("\n--- Testing VLM inference ---")
    response = client.chat.completions.create(
        model=endpoint.name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": args.test_prompt},
                    {"type": "image_url", "image_url": {"url": sample_image}},
                ],
            }
        ],
        max_tokens=512,
    )
    print(f"VLM response: {response.choices[0].message.content}")
    print(f"\nEndpoint is running. Delete it when done to avoid charges:")
    print(f"  client.endpoints.delete(\"{endpoint.id}\")")


if __name__ == "__main__":
    main()
