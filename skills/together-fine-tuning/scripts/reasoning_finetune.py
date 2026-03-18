#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- Reasoning Fine-Tuning (v2 SDK)

Prepare chain-of-thought training data with reasoning fields, upload,
fine-tune a reasoning model, and test inference with reasoning output.

Reasoning datasets use conversational format where assistant messages
include a `reasoning` (or `reasoning_content`) field containing the
model's chain of thought, and a `content` field for the final answer.

Supported models: Qwen3 family (0.6B-235B), GLM-4.6, GLM-4.7,
Qwen3-Next-80B-A3B-Thinking.

Usage:
    python reasoning_finetune.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import json
import time
import tempfile
from together import Together

client = Together()

# --- 1. Prepare reasoning training data ---
# Each assistant message has:
#   - "reasoning" or "reasoning_content": the chain-of-thought process
#   - "content": the final answer shown to the user

training_data = [
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
            {
                "role": "user",
                "content": "Solve for x: 3x + 7 = 22",
            },
            {
                "role": "assistant",
                "reasoning": (
                    "3x + 7 = 22\n"
                    "Subtract 7 from both sides: 3x = 15\n"
                    "Divide both sides by 3: x = 5\n"
                    "Check: 3(5) + 7 = 15 + 7 = 22 ✓"
                ),
                "content": "**x = 5**",
            },
        ]
    },
    # Add more examples for production use...
]

data_path = tempfile.mktemp(suffix=".jsonl")
with open(data_path, "w") as f:
    for example in training_data:
        f.write(json.dumps(example) + "\n")

print(f"Wrote {len(training_data)} reasoning examples to {data_path}")

# --- 2. Upload ---
file_resp = client.files.upload(file=data_path, purpose="fine-tune", check=True)
print(f"Uploaded file: {file_resp.id}")

# --- 3. Start LoRA fine-tuning on a reasoning-capable model ---
job = client.fine_tuning.create(
    training_file=file_resp.id,
    model="Qwen/Qwen3-8B",
    lora=True,
    n_epochs=3,
    learning_rate=1e-5,
    suffix="reasoning-math-v1",
)
print(f"Created reasoning fine-tuning job: {job.id}")

# --- 4. Monitor ---
while True:
    status = client.fine_tuning.retrieve(id=job.id)
    print(f"  Status: {status.status}")
    if status.status == "completed":
        print(f"\nTraining complete! Output: {status.output_name}")
        break
    elif status.status in ("failed", "cancelled"):
        print(f"Job ended: {status.status}")
        exit(1)
    time.sleep(30)

# --- 5. Test reasoning inference ---
# The fine-tuned model should now produce chain-of-thought reasoning
# in the `reasoning` field and the final answer in `content`.
print("\n--- Testing reasoning inference ---")
stream = client.chat.completions.create(
    model=status.output_name,
    messages=[
        {"role": "user", "content": "What is 25% of 360?"},
    ],
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


# --- 6. (Optional) Preference fine-tuning for reasoning ---
# You can also do DPO with reasoning data. Both preferred and
# non-preferred outputs include reasoning fields:
dpo_example = {
    "input": {
        "messages": [
            {"role": "user", "content": "What is 15% of 240?"}
        ]
    },
    "preferred_output": [
        {
            "role": "assistant",
            "reasoning": (
                "15% means 15/100 = 0.15\n"
                "0.15 * 240 = 36"
            ),
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
