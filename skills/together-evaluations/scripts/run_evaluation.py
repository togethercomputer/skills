#!/usr/bin/env python3
"""
Together AI Evaluations — Run Classify, Score, and Compare (v2 SDK)

Upload a dataset, create an evaluation, and poll for results.
Demonstrates all three evaluation types.

Usage:
    python run_evaluation.py --type classify
    python run_evaluation.py --type score --dataset score_prompts.jsonl
    python run_evaluation.py --type compare --model-a model-a --model-b model-b

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import argparse
import json
import tempfile
import time
from pathlib import Path

from together import Together

client = Together()

JUDGE_MODEL = "deepseek-ai/DeepSeek-V3.1"
EVAL_MODEL = "Qwen/Qwen3.5-9B"


def upload_dataset(dataset: list[dict]) -> str:
    """Write dataset rows to JSONL and upload with purpose=eval."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for row in dataset:
            temp_file.write(json.dumps(row) + "\n")
        data_path = Path(temp_file.name)

    try:
        file_response = client.files.upload(file=str(data_path), purpose="eval", check=False)
    finally:
        data_path.unlink(missing_ok=True)
    print(f"Uploaded dataset: {file_response.id}")
    return file_response.id


def poll_evaluation(workflow_id: str, poll_interval: int) -> object:
    """Poll until the evaluation completes or fails."""
    while True:
        result = client.evals.status(workflow_id)
        print(f"  Status: {result.status}")

        if result.status == "completed":
            return result
        if result.status in ("error", "user_error"):
            print("Evaluation failed")
            return result

        time.sleep(poll_interval)


def load_dataset(path: str | None, fallback_rows: list[dict]) -> list[dict]:
    """Load dataset rows from JSONL, or return bundled sample rows."""
    if not path:
        return fallback_rows
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def run_classify(dataset: list[dict], judge_model: str, eval_model: str, poll_interval: int) -> None:
    """Classify evaluation — categorize responses into labels."""
    print("\n=== Classify Evaluation ===")
    file_id = upload_dataset(dataset)

    evaluation = client.evals.create(
        type="classify",
        parameters={
            "input_data_file_path": file_id,
            "judge": {
                "model": judge_model,
                "model_source": "serverless",
                "system_template": "Classify the following text as positive, negative, or neutral sentiment.",
            },
            "labels": ["positive", "negative", "neutral"],
            "pass_labels": ["positive"],
            "model_to_evaluate": {
                "model": eval_model,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id, poll_interval=poll_interval)
    if result.results:
        print(f"  Label counts: {result.results.label_counts}")
        print(f"  Pass percentage: {result.results.pass_percentage}")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Result file: {result.results.result_file_id}")


def run_score(dataset: list[dict], judge_model: str, eval_model: str, poll_interval: int) -> None:
    """Score evaluation — rate responses on a numerical scale."""
    print("\n=== Score Evaluation ===")
    file_id = upload_dataset(dataset)

    evaluation = client.evals.create(
        type="score",
        parameters={
            "input_data_file_path": file_id,
            "judge": {
                "model": judge_model,
                "model_source": "serverless",
                "system_template": (
                    "Rate the quality of the response from 1 to 10, where 1 is very poor and 10 is "
                    "excellent. Consider accuracy, clarity, and completeness."
                ),
            },
            "min_score": 1.0,
            "max_score": 10.0,
            "pass_threshold": 7.0,
            "model_to_evaluate": {
                "model": eval_model,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id, poll_interval=poll_interval)
    if result.results:
        scores = result.results.aggregated_scores
        if scores:
            print(f"  Mean score: {scores.mean_score}")
            print(f"  Std score: {scores.std_score}")
            print(f"  Pass percentage: {scores.pass_percentage}")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Result file: {result.results.result_file_id}")


def run_compare(
    dataset: list[dict],
    judge_model: str,
    model_a: str,
    model_b: str,
    poll_interval: int,
) -> None:
    """Compare evaluation — A/B comparison between two models."""
    print("\n=== Compare Evaluation ===")
    file_id = upload_dataset(dataset)

    evaluation = client.evals.create(
        type="compare",
        parameters={
            "input_data_file_path": file_id,
            "judge": {
                "model": judge_model,
                "model_source": "serverless",
                "system_template": (
                    "Please assess which model has smarter and more helpful responses. Consider "
                    "clarity, accuracy, and usefulness."
                ),
            },
            "model_a": {
                "model": model_a,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
            "model_b": {
                "model": model_b,
                "model_source": "serverless",
                "system_template": "You are a helpful assistant.",
                "input_template": "{{prompt}}",
                "max_tokens": 512,
                "temperature": 0.7,
            },
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id, poll_interval=poll_interval)
    if result.results:
        print(f"  A wins: {result.results.A_wins}")
        print(f"  B wins: {result.results.B_wins}")
        print(f"  Ties: {result.results.Ties}")
        if hasattr(result.results, "result_file_id") and result.results.result_file_id:
            print(f"  Result file: {result.results.result_file_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI evaluations workflow")
    parser.add_argument(
        "--type",
        choices=["classify", "score", "compare"],
        default="classify",
        help="Evaluation workflow to run",
    )
    parser.add_argument("--dataset", help="Path to a JSONL dataset; uses bundled samples when omitted")
    parser.add_argument("--judge-model", default=JUDGE_MODEL, help="Judge model")
    parser.add_argument("--eval-model", default=EVAL_MODEL, help="Model under test for classify or score")
    parser.add_argument(
        "--model-a",
        default="Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
        help="Model A for compare evaluations",
    )
    parser.add_argument(
        "--model-b",
        default=EVAL_MODEL,
        help="Model B for compare evaluations",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between evaluation status checks",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sample_datasets = {
        "classify": [
            {"prompt": "The product arrived on time and works perfectly!"},
            {"prompt": "Terrible experience. The item was broken."},
            {"prompt": "It's okay, nothing special."},
        ],
        "score": [
            {"prompt": "Explain quantum computing in simple terms."},
            {"prompt": "What causes rainbows?"},
            {"prompt": "How do vaccines work?"},
        ],
        "compare": [
            {"prompt": "Explain the theory of relativity."},
            {"prompt": "What is the meaning of life?"},
            {"prompt": "How does photosynthesis work?"},
        ],
    }
    dataset = load_dataset(args.dataset, fallback_rows=sample_datasets[args.type])

    if args.type == "classify":
        run_classify(dataset, judge_model=args.judge_model, eval_model=args.eval_model, poll_interval=args.poll_interval)
    elif args.type == "score":
        run_score(dataset, judge_model=args.judge_model, eval_model=args.eval_model, poll_interval=args.poll_interval)
    else:
        run_compare(
            dataset,
            judge_model=args.judge_model,
            model_a=args.model_a,
            model_b=args.model_b,
            poll_interval=args.poll_interval,
        )


if __name__ == "__main__":
    main()
