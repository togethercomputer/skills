#!/usr/bin/env python3
"""
Together AI Evaluations — Run Classify, Score, and Compare (v2 SDK)

Upload a dataset, create an evaluation, and poll for results.
Demonstrates all three evaluation types.

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

client = Together()

JUDGE_MODEL = "deepseek-ai/DeepSeek-V3.1"
EVAL_MODEL = "Qwen/Qwen3.5-9B"


def upload_dataset(dataset: list[dict]) -> str:
    """Write dataset to JSONL and upload with purpose=eval."""
    data_path = tempfile.mktemp(suffix=".jsonl")
    with open(data_path, "w") as f:
        for row in dataset:
            f.write(json.dumps(row) + "\n")

    file_response = client.files.upload(file=data_path, purpose="eval", check=False)
    print(f"Uploaded dataset: {file_response.id}")
    return file_response.id


def poll_evaluation(workflow_id: str) -> object:
    """Poll until the evaluation completes or fails."""
    while True:
        result = client.evals.status(workflow_id)
        print(f"  Status: {result.status}")

        if result.status == "completed":
            return result
        elif result.status in ("error", "user_error"):
            print("Evaluation failed")
            return result

        time.sleep(5)


def run_classify():
    """Classify evaluation — categorize responses into labels."""
    print("\n=== Classify Evaluation ===")

    dataset = [
        {"prompt": "The product arrived on time and works perfectly!"},
        {"prompt": "Terrible experience. The item was broken."},
        {"prompt": "It's okay, nothing special."},
    ]
    file_id = upload_dataset(dataset)

    evaluation = client.evals.create(
        type="classify",
        parameters={
            "input_data_file_path": file_id,
            "judge": {
                "model": JUDGE_MODEL,
                "model_source": "serverless",
                "system_template": "Classify the following text as positive, negative, or neutral sentiment.",
            },
            "labels": ["positive", "negative", "neutral"],
            "pass_labels": ["positive"],
            "model_to_evaluate": {
                "model": EVAL_MODEL,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id)
    if result.results:
        print(f"  Label counts: {result.results.label_counts}")
        print(f"  Pass percentage: {result.results.pass_percentage}")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Result file: {result.results.result_file_id}")


def run_score():
    """Score evaluation — rate responses on a numerical scale."""
    print("\n=== Score Evaluation ===")

    dataset = [
        {"prompt": "Explain quantum computing in simple terms."},
        {"prompt": "What causes rainbows?"},
        {"prompt": "How do vaccines work?"},
    ]
    file_id = upload_dataset(dataset)

    evaluation = client.evals.create(
        type="score",
        parameters={
            "input_data_file_path": file_id,
            "judge": {
                "model": JUDGE_MODEL,
                "model_source": "serverless",
                "system_template": "Rate the quality of the response from 1 to 10, where 1 is very poor and 10 is excellent. Consider accuracy, clarity, and completeness.",
            },
            "min_score": 1.0,
            "max_score": 10.0,
            "pass_threshold": 7.0,
            "model_to_evaluate": {
                "model": EVAL_MODEL,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id)
    if result.results:
        scores = result.results.aggregated_scores
        if scores:
            print(f"  Mean score: {scores.mean_score}")
            print(f"  Std score: {scores.std_score}")
            print(f"  Pass percentage: {scores.pass_percentage}")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Result file: {result.results.result_file_id}")


def run_compare():
    """Compare evaluation — A/B comparison between two models."""
    print("\n=== Compare Evaluation ===")

    dataset = [
        {"prompt": "Explain the theory of relativity."},
        {"prompt": "What is the meaning of life?"},
        {"prompt": "How does photosynthesis work?"},
    ]
    file_id = upload_dataset(dataset)

    evaluation = client.evals.create(
        type="compare",
        parameters={
            "input_data_file_path": file_id,
            "judge": {
                "model": JUDGE_MODEL,
                "model_source": "serverless",
                "system_template": "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness.",
            },
            "model_a": {
                "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
            "model_b": {
                "model": EVAL_MODEL,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id)
    if result.results:
        print(f"  A wins: {result.results.A_wins}")
        print(f"  B wins: {result.results.B_wins}")
        print(f"  Ties: {result.results.Ties}")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Result file: {result.results.result_file_id}")


if __name__ == "__main__":
    run_classify()
    # run_score()
    # run_compare()
