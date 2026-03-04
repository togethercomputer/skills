#!/usr/bin/env python3
"""
Together AI Evaluations — Run Classify/Score/Compare (v2 SDK)

Upload a dataset, create an evaluation, and poll for results.

Usage:
    python run_evaluation.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import json
import time
import tempfile
from together import Together
from together.types.eval_create_params import (
    ParametersEvaluationClassifyParameters,
    ParametersEvaluationClassifyParametersJudge,
)

client = Together()


def run_classify_evaluation():
    """Run a classify evaluation (e.g., sentiment, quality)."""

    # --- 1. Prepare evaluation dataset ---
    dataset = [
        {"prompt": "The product arrived on time and works perfectly!", "expected": "positive"},
        {"prompt": "Terrible experience. The item was broken.", "expected": "negative"},
        {"prompt": "It's okay, nothing special.", "expected": "neutral"},
    ]

    data_path = tempfile.mktemp(suffix=".jsonl")
    with open(data_path, "w") as f:
        for row in dataset:
            f.write(json.dumps(row) + "\n")

    # --- 2. Upload dataset ---
    file_response = client.files.upload(file=data_path, purpose="eval")
    file_id = file_response.id
    print(f"Uploaded dataset: {file_id}")

    # --- 3. Create evaluation ---
    evaluation = client.evals.create(
        type="classify",
        parameters=ParametersEvaluationClassifyParameters(
            judge=ParametersEvaluationClassifyParametersJudge(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                model_source="serverless",
                system_template="Classify the following text as positive, negative, or neutral sentiment.",
            ),
            input_data_file_path=file_id,
            labels=["positive", "negative", "neutral"],
            pass_labels=["positive"],
            model_to_evaluate={
                "model": "openai/gpt-oss-20b",
                "model_source": "serverless",
                "input_template": "{{prompt}}",
            },
        ),
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    # --- 4. Poll for completion ---
    while True:
        status = client.evals.retrieve(evaluation.workflow_id)
        current = status.status
        print(f"  Status: {current}")

        if current == "completed":
            break
        elif current in ("failed", "error", "user_error"):
            print("Evaluation failed")
            return

        time.sleep(5)

    # --- 5. Get results ---
    result = client.evals.retrieve(evaluation.workflow_id)
    print(f"\nResults:")
    if result.results:
        print(f"  Label counts: {result.results.label_counts}")
        print(f"  Pass percentage: {result.results.pass_percentage:.1f}%")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Full results file: {result.results.result_file_id}")


if __name__ == "__main__":
    run_classify_evaluation()
