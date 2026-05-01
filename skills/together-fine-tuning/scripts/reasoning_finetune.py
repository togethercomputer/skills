#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- Reasoning Fine-Tuning (v2 SDK)

Prepare chain-of-thought training data with reasoning fields, upload,
fine-tune a reasoning model, and test inference with reasoning output.

Reasoning datasets use conversational format where assistant messages
include a `reasoning` (or `reasoning_content`) field containing the
model's chain of thought, and a `content` field for the final answer.

Supported models: Qwen3.5 family (0.8B-397B), Qwen3 family (0.6B-235B),
GLM-5.1, GLM-5, GLM-4.7, GLM-4.6, Qwen3-Next-80B-A3B-Thinking.

Usage:
    python reasoning_finetune.py
    python reasoning_finetune.py --training-file reasoning.jsonl --model Qwen/Qwen3-8B
    python reasoning_finetune.py --test-prompt "What is 30% of 250?"

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import json
import tempfile
import time
from pathlib import Path

from together import Together

client = Together()


def sample_training_data() -> list[dict]:
    """Return a small reasoning dataset."""
    return [
        {
            "messages": [
                {"role": "user", "content": "What is 15% of 240?"},
                {
                    "role": "assistant",
                    "reasoning": (
                        "I need to calculate 15% of 240.\n"
                        "15% means 15/100 = 0.15\n"
                        "0.15 * 240 = 36\n"
                        "So 15% of 240 is 36."
                    ),
                    "content": "15% of 240 is **36**.",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "If a train travels at 60 mph for 2.5 hours, how far does it go?",
                },
                {
                    "role": "assistant",
                    "reasoning": (
                        "Distance = speed * time\n"
                        "Speed = 60 mph\n"
                        "Time = 2.5 hours\n"
                        "Distance = 60 * 2.5 = 150 miles"
                    ),
                    "content": "The train travels **150 miles**.",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "A store has a 20% off sale. An item costs $80. What is the sale price?",
                },
                {
                    "role": "assistant",
                    "reasoning": (
                        "Original price: $80\n"
                        "Discount: 20% of $80 = 0.20 * 80 = $16\n"
                        "Sale price: $80 - $16 = $64"
                    ),
                    "content": "The sale price is **$64**.",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "There are 5 red balls and 3 blue balls in a bag. "
                        "What is the probability of drawing a blue ball?"
                    ),
                },
                {
                    "role": "assistant",
                    "reasoning": (
                        "Total balls = 5 red + 3 blue = 8\n"
                        "Blue balls = 3\n"
                        "P(blue) = 3/8 = 0.375 = 37.5%"
                    ),
                    "content": "The probability of drawing a blue ball is **3/8** (37.5%).",
                },
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "Solve for x: 3x + 7 = 22"},
                {
                    "role": "assistant",
                    "reasoning": (
                        "3x + 7 = 22\n"
                        "Subtract 7 from both sides: 3x = 15\n"
                        "Divide both sides by 3: x = 5\n"
                        "Check: 3(5) + 7 = 15 + 7 = 22"
                    ),
                    "content": "**x = 5**",
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
    parser = argparse.ArgumentParser(description="Together AI reasoning fine-tuning workflow")
    parser.add_argument("--training-file", help="Path to a reasoning training JSONL file")
    parser.add_argument("--model", default="Qwen/Qwen3-8B", help="Reasoning-capable base model")
    parser.add_argument("--suffix", default="reasoning-math-v1", help="Suffix for the fine-tuned model")
    parser.add_argument("--n-epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Training learning rate")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between status checks")
    parser.add_argument(
        "--test-prompt",
        default="What is 25% of 360?",
        help="Prompt to use when testing the fine-tuned model",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path: Path | None = None
    upload_path = args.training_file
    if upload_path is None:
        training_data = sample_training_data()
        data_path = create_temp_dataset(training_data)
        upload_path = str(data_path)
        print(f"Wrote {len(training_data)} reasoning examples to {data_path}")

    # --- 2. Upload ---
    try:
        file_resp = client.files.upload(file=upload_path, purpose="fine-tune", check=True)
    finally:
        if data_path is not None:
            data_path.unlink(missing_ok=True)
    print(f"Uploaded file: {file_resp.id}")

    # --- 3. Start LoRA fine-tuning on a reasoning-capable model ---
    job = client.fine_tuning.create(
        training_file=file_resp.id,
        model=args.model,
        lora=True,
        n_epochs=args.n_epochs,
        learning_rate=args.learning_rate,
        suffix=args.suffix,
    )
    print(f"Created reasoning fine-tuning job: {job.id}")

    # --- 4. Monitor ---
    while True:
        status = client.fine_tuning.retrieve(id=job.id)
        print(f"  Status: {status.status}")
        if status.status == "completed":
            print(f"\nTraining complete! Output: {status.x_model_output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"Job ended: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 5. Deploy and test reasoning inference ---
    print("\n--- Deploying fine-tuned model ---")
    output_model = status.x_model_output_name
    endpoint = client.endpoints.create(
        display_name="Reasoning Fine-tuned",
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

    print("\n--- Testing reasoning inference ---")
    stream = client.chat.completions.create(
        model=endpoint.name,
        messages=[{"role": "user", "content": args.test_prompt}],
        stream=True,
    )

    reasoning_text = ""
    content_text = ""
    for chunk in stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning") and delta.reasoning:
                reasoning_text += delta.reasoning
            if hasattr(delta, "content") and delta.content:
                content_text += delta.content

    print(f"Reasoning: {reasoning_text}")
    print(f"Answer: {content_text}")
    print(f"\nEndpoint is running. Delete it when done to avoid charges:")
    print(f"  client.endpoints.delete(\"{endpoint.id}\")")

    # --- 6. (Optional) Preference fine-tuning for reasoning ---
    dpo_example = {
        "input": {"messages": [{"role": "user", "content": "What is 15% of 240?"}]},
        "preferred_output": [
            {
                "role": "assistant",
                "reasoning": "15% means 15/100 = 0.15\n0.15 * 240 = 36",
                "content": "15% of 240 is **36**.",
            }
        ],
        "non_preferred_output": [
            {
                "role": "assistant",
                "reasoning": "15% of 240... let me guess...",
                "content": "About 30.",
            }
        ],
    }
    print(f"\nDPO reasoning example format:\n{json.dumps(dpo_example, indent=2)}")


if __name__ == "__main__":
    main()
