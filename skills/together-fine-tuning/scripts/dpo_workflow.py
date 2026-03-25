#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- DPO Preference Workflow (v2 SDK)

End-to-end: SFT first, then DPO preference tuning from checkpoint.
Best practice is to run SFT before DPO for better model quality.

Usage:
    python dpo_workflow.py
    python dpo_workflow.py --sft-training-file sft.jsonl --dpo-training-file dpo.jsonl
    python dpo_workflow.py --model meta-llama/Llama-3.2-3B-Instruct

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


def sample_sft_data() -> list[dict]:
    """Return a small SFT dataset for the DPO warm-up stage."""
    return [
        {
            "messages": [
                {"role": "user", "content": "Explain quantum computing simply."},
                {
                    "role": "assistant",
                    "content": (
                        "Quantum computing uses quantum bits (qubits) that can represent "
                        "0 and 1 simultaneously through superposition. This allows quantum "
                        "computers to explore many solutions at once for certain problems."
                    ),
                },
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "What is machine learning?"},
                {
                    "role": "assistant",
                    "content": (
                        "Machine learning is a branch of AI where systems learn patterns "
                        "from data instead of being explicitly programmed. Models improve "
                        "their predictions as they see more examples."
                    ),
                },
            ]
        },
    ]


def sample_dpo_data() -> list[dict]:
    """Return a small preference dataset for DPO training."""
    return [
        {
            "input": {"messages": [{"role": "user", "content": "Explain quantum computing simply."}]},
            "preferred_output": [
                {
                    "role": "assistant",
                    "content": (
                        "Quantum computing uses quantum bits (qubits) that can be in "
                        "superposition -- representing both 0 and 1 at once. This enables "
                        "solving certain problems exponentially faster than classical computers."
                    ),
                }
            ],
            "non_preferred_output": [
                {
                    "role": "assistant",
                    "content": "It's just faster computers that use quantum stuff.",
                }
            ],
        },
        {
            "input": {"messages": [{"role": "user", "content": "What is machine learning?"}]},
            "preferred_output": [
                {
                    "role": "assistant",
                    "content": (
                        "Machine learning is a branch of AI where systems learn patterns from "
                        "data rather than following explicit rules. Models are trained on examples "
                        "and progressively improve their accuracy on new, unseen data."
                    ),
                }
            ],
            "non_preferred_output": [
                {
                    "role": "assistant",
                    "content": "ML means computers learn things.",
                }
            ],
        },
    ]


def create_temp_dataset(rows: list[dict]) -> Path:
    """Write JSONL rows to a temporary file."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for row in rows:
            temp_file.write(json.dumps(row) + "\n")
        return Path(temp_file.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI DPO fine-tuning workflow")
    parser.add_argument("--sft-training-file", help="Path to an SFT training JSONL file")
    parser.add_argument("--dpo-training-file", help="Path to a DPO preference JSONL file")
    parser.add_argument(
        "--model",
        default="meta-llama/Llama-3.2-3B-Instruct",
        help="Base model for both SFT and DPO",
    )
    parser.add_argument("--sft-suffix", default="sft-step", help="Suffix for the SFT warm-up job")
    parser.add_argument("--dpo-suffix", default="dpo-step", help="Suffix for the DPO job")
    parser.add_argument("--sft-epochs", type=int, default=3, help="Epochs for the SFT warm-up job")
    parser.add_argument("--dpo-epochs", type=int, default=2, help="Epochs for the DPO job")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Learning rate for the SFT warm-up job")
    parser.add_argument("--dpo-beta", type=float, default=0.2, help="DPO beta value")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between status checks")
    parser.add_argument(
        "--test-prompt",
        default="Explain quantum computing simply.",
        help="Prompt to send to the final fine-tuned model",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sft_path: Path | None = None
    dpo_path: Path | None = None
    sft_upload_path = args.sft_training_file
    dpo_upload_path = args.dpo_training_file

    if sft_upload_path is None:
        sft_path = create_temp_dataset(sample_sft_data())
        sft_upload_path = str(sft_path)
    if dpo_upload_path is None:
        dpo_path = create_temp_dataset(sample_dpo_data())
        dpo_upload_path = str(dpo_path)

    # --- 3. Upload both files ---
    try:
        sft_file = client.files.upload(file=sft_upload_path, purpose="fine-tune", check=True)
        dpo_file = client.files.upload(file=dpo_upload_path, purpose="fine-tune", check=True)
    finally:
        if sft_path is not None:
            sft_path.unlink(missing_ok=True)
        if dpo_path is not None:
            dpo_path.unlink(missing_ok=True)
    print(f"SFT file: {sft_file.id}")
    print(f"DPO file: {dpo_file.id}")

    # --- 4. Step 1: Run SFT job first ---
    print("\n--- Step 1: SFT Training ---")
    sft_job = client.fine_tuning.create(
        training_file=sft_file.id,
        model=args.model,
        lora=True,
        n_epochs=args.sft_epochs,
        learning_rate=args.learning_rate,
        suffix=args.sft_suffix,
    )
    print(f"SFT job: {sft_job.id}")

    while True:
        status = client.fine_tuning.retrieve(id=sft_job.id)
        print(f"  SFT status: {status.status}")
        if status.status == "completed":
            print(f"  SFT output: {status.output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"SFT failed: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 5. Step 2: Run DPO from SFT checkpoint ---
    print("\n--- Step 2: DPO Training (from SFT checkpoint) ---")
    dpo_job = client.fine_tuning.create(
        training_file=dpo_file.id,
        from_checkpoint=sft_job.id,
        model=args.model,
        training_method="dpo",
        dpo_beta=args.dpo_beta,
        lora=True,
        n_epochs=args.dpo_epochs,
        suffix=args.dpo_suffix,
    )
    print(f"DPO job: {dpo_job.id}")

    while True:
        status = client.fine_tuning.retrieve(id=dpo_job.id)
        print(f"  DPO status: {status.status}")
        if status.status == "completed":
            print(f"  DPO output: {status.output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"DPO failed: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 6. Test the DPO-tuned model ---
    print("\n--- Testing DPO-tuned model ---")
    response = client.chat.completions.create(
        model=status.output_name,
        messages=[{"role": "user", "content": args.test_prompt}],
        max_tokens=256,
    )
    print(f"Response: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
