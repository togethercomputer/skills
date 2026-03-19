#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- DPO Preference Workflow (v2 SDK)

End-to-end: SFT first, then DPO preference tuning from checkpoint.
Best practice is to run SFT before DPO for better model quality.

Usage:
    python dpo_workflow.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import json
import time
import tempfile
from together import Together

client = Together()

def main() -> None:
    # --- 1. Prepare SFT training data ---
    sft_data = [
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

    sft_path = tempfile.mktemp(suffix=".jsonl")
    with open(sft_path, "w") as f:
        for ex in sft_data:
            f.write(json.dumps(ex) + "\n")

    # --- 2. Prepare DPO preference data ---
    dpo_data = [
        {
            "input": {
                "messages": [
                    {"role": "user", "content": "Explain quantum computing simply."}
                ]
            },
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
            "input": {
                "messages": [
                    {"role": "user", "content": "What is machine learning?"}
                ]
            },
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

    dpo_path = tempfile.mktemp(suffix=".jsonl")
    with open(dpo_path, "w") as f:
        for ex in dpo_data:
            f.write(json.dumps(ex) + "\n")

    # --- 3. Upload both files ---
    sft_file = client.files.upload(file=sft_path, purpose="fine-tune", check=True)
    dpo_file = client.files.upload(file=dpo_path, purpose="fine-tune", check=True)
    print(f"SFT file: {sft_file.id}")
    print(f"DPO file: {dpo_file.id}")

    # --- 4. Step 1: Run SFT job first ---
    print("\n--- Step 1: SFT Training ---")
    sft_job = client.fine_tuning.create(
        training_file=sft_file.id,
        model="meta-llama/Llama-3.2-3B-Instruct",
        lora=True,
        n_epochs=3,
        learning_rate=1e-5,
        suffix="sft-step",
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
        time.sleep(30)

    # --- 5. Step 2: Run DPO from SFT checkpoint ---
    print("\n--- Step 2: DPO Training (from SFT checkpoint) ---")
    dpo_job = client.fine_tuning.create(
        training_file=dpo_file.id,
        from_checkpoint=sft_job.id,
        model="meta-llama/Llama-3.2-3B-Instruct",
        training_method="dpo",
        dpo_beta=0.2,
        lora=True,
        n_epochs=2,
        suffix="dpo-step",
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
        time.sleep(30)

    # --- 6. Test the DPO-tuned model ---
    print("\n--- Testing DPO-tuned model ---")
    response = client.chat.completions.create(
        model=status.output_name,
        messages=[
            {"role": "user", "content": "Explain quantum computing simply."},
        ],
        max_tokens=256,
    )
    print(f"Response: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
