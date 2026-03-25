#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- Full Workflow (v2 SDK)

End-to-end: prepare data -> upload -> create LoRA job -> monitor -> deploy.

Usage:
    python finetune_workflow.py
    python finetune_workflow.py --training-file train.jsonl --model meta-llama/Meta-Llama-3.1-8B-Instruct-Reference
    python finetune_workflow.py --skip-deploy

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
    """Return a small conversational dataset for demonstration."""
    return [
        {
            "messages": [
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": "How do I reset my password?"},
                {
                    "role": "assistant",
                    "content": (
                        "Go to Settings > Security > Reset Password. "
                        "You'll receive a confirmation email within 5 minutes."
                    ),
                },
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": "What are your business hours?"},
                {
                    "role": "assistant",
                    "content": (
                        "We're available Monday-Friday, 9 AM - 6 PM EST. "
                        "Weekend support is available via email."
                    ),
                },
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": "How do I cancel my subscription?"},
                {
                    "role": "assistant",
                    "content": (
                        "Go to Settings > Billing > Cancel Subscription. "
                        "Your access continues until the end of the billing period."
                    ),
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
    parser = argparse.ArgumentParser(description="Together AI fine-tuning workflow")
    parser.add_argument("--training-file", help="Path to a training JSONL file")
    parser.add_argument(
        "--model",
        default="meta-llama/Meta-Llama-3.1-8B-Instruct-Reference",
        help="Base model to fine-tune",
    )
    parser.add_argument("--suffix", default="support-bot-v1", help="Suffix for the fine-tuned model")
    parser.add_argument("--n-epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Training learning rate")
    parser.add_argument("--hardware", default="4x_nvidia_h100_80gb_sxm", help="Hardware for optional deployment")
    parser.add_argument("--display-name", default="Support Bot v1", help="Display name for the endpoint")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between fine-tuning status checks",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Stop after training instead of creating a dedicated endpoint",
    )
    parser.add_argument(
        "--test-prompt",
        default="How do I update my billing info?",
        help="Prompt to use when testing the deployed model",
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
        print(f"Wrote {len(training_data)} examples to {data_path}")

    # --- 2. Upload training file with validation enabled ---
    try:
        file_response = client.files.upload(file=upload_path, purpose="fine-tune", check=True)
    finally:
        if data_path is not None:
            data_path.unlink(missing_ok=True)
    file_id = file_response.id
    print(f"Uploaded file: {file_id}")

    # --- 3. Create LoRA fine-tuning job ---
    job = client.fine_tuning.create(
        training_file=file_id,
        model=args.model,
        n_epochs=args.n_epochs,
        learning_rate=args.learning_rate,
        lora=True,
        suffix=args.suffix,
    )
    print(f"Created fine-tuning job: {job.id}")

    # --- 4. Monitor training ---
    while True:
        status = client.fine_tuning.retrieve(id=job.id)
        print(f"  Status: {status.status}")

        if status.status == "completed":
            print("\nTraining complete!")
            print(f"  Output model: {status.output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"Job ended: {status.status}")
            raise SystemExit(1)

        time.sleep(args.poll_interval)

    # --- 5. List training events ---
    events = client.fine_tuning.list_events(id=job.id)
    for event in events.data:
        print(f"  [{event.created_at}] {event.message}")

    if args.skip_deploy:
        print("\nSkipping deployment as requested.")
        return

    # --- 6. Deploy as a Dedicated Endpoint ---
    output_model = status.output_name
    endpoint = client.endpoints.create(
        display_name=args.display_name,
        model=output_model,
        hardware=args.hardware,
        autoscaling={"min_replicas": 1, "max_replicas": 1},
    )
    print(f"\nDeployed endpoint: {endpoint}")

    # --- 7. Query the fine-tuned model ---
    response = client.chat.completions.create(
        model=output_model,
        messages=[
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": args.test_prompt},
        ],
        max_tokens=256,
    )
    print(f"\nFine-tuned model response: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
