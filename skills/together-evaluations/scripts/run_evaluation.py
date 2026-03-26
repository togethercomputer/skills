#!/usr/bin/env python3
"""
Together AI Evaluations — Run Classify, Score, and Compare (v2 SDK)

Upload an eval dataset, create an evaluation, poll for results, and optionally
download the per-row results file. Supports serverless, dedicated, and external
judge or target models, plus dataset-column evaluation for pre-generated
responses.

Usage:
    python run_evaluation.py --type classify
    python run_evaluation.py --type score --dataset score_prompts.jsonl --eval-column response
    python run_evaluation.py --type compare --model-a-column response_a --model-b-column response_b
    python run_evaluation.py --type classify --eval-model openai/gpt-5 \
        --eval-model-source external --eval-external-api-token "$OPENAI_API_KEY"

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from together import Together

client = Together()

MODEL_SOURCES = ("serverless", "dedicated", "external")
JUDGE_MODEL = "deepseek-ai/DeepSeek-V3.1"
EVAL_MODEL = "Qwen/Qwen3.5-9B"
DEFAULT_EVAL_SYSTEM_TEMPLATE = "You are a helpful assistant."
DEFAULT_INPUT_TEMPLATE = "{{prompt}}"
DEFAULT_CLASSIFY_TEMPLATE = "Classify the following text as positive, negative, or neutral sentiment."
DEFAULT_SCORE_TEMPLATE = (
    "Rate the quality of the response from 1 to 10, where 1 is very poor and 10 is excellent. "
    "Consider accuracy, clarity, and completeness."
)
DEFAULT_COMPARE_TEMPLATE = (
    "Please assess which model has smarter and more helpful responses. Consider clarity, "
    "accuracy, and usefulness."
)


def upload_dataset(dataset: list[dict[str, Any]]) -> str:
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


def load_dataset(path: str | None, fallback_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load dataset rows from JSONL, or return bundled sample rows."""
    if not path:
        return fallback_rows

    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def poll_evaluation(workflow_id: str, poll_interval: int) -> Any:
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


def result_file_id(result: Any) -> str | None:
    """Return the per-row result file ID when present."""
    results = getattr(result, "results", None)
    if not results:
        return None
    return getattr(results, "result_file_id", None)


def download_result_file(file_id: str, output_path: str) -> None:
    """Download the result JSONL file to a local path."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with client.files.with_streaming_response.content(id=file_id) as response:
        with open(destination, "wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)

    print(f"Saved result rows to {destination}")


def build_judge_config(args: argparse.Namespace, default_template: str) -> dict[str, Any]:
    """Build judge model config for serverless, dedicated, or external judges."""
    config: dict[str, Any] = {
        "model": args.judge_model,
        "model_source": args.judge_model_source,
        "system_template": args.judge_system_template or default_template,
    }
    if args.judge_external_api_token:
        config["external_api_token"] = args.judge_external_api_token
    if args.judge_external_base_url:
        config["external_base_url"] = args.judge_external_base_url
    return config


def build_model_config(
    *,
    model: str,
    model_source: str,
    system_template: str,
    input_template: str,
    max_tokens: int,
    temperature: float,
    external_api_token: str | None = None,
    external_base_url: str | None = None,
) -> dict[str, Any]:
    """Build an evaluation target config."""
    config: dict[str, Any] = {
        "model": model,
        "model_source": model_source,
        "system_template": system_template,
        "input_template": input_template,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if external_api_token:
        config["external_api_token"] = external_api_token
    if external_base_url:
        config["external_base_url"] = external_base_url
    return config


def sample_dataset_for_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Return a bundled sample dataset that matches the selected workflow."""
    if args.type == "compare" and args.model_a_column and args.model_b_column:
        return [
            {
                "prompt": "Explain the theory of relativity.",
                args.model_a_column: "Relativity explains gravity as the curvature of spacetime.",
                args.model_b_column: "Einstein's theory says mass bends spacetime and changes motion.",
            },
            {
                "prompt": "How does photosynthesis work?",
                args.model_a_column: "Plants convert sunlight, water, and carbon dioxide into sugar.",
                args.model_b_column: "Photosynthesis uses light energy to create glucose and oxygen.",
            },
        ]

    if args.type in {"classify", "score"} and args.eval_column:
        return [
            {
                "prompt": "Summarize what artificial intelligence is.",
                args.eval_column: "Artificial intelligence is software that performs tasks requiring reasoning or prediction.",
            },
            {
                "prompt": "What causes rainbows?",
                args.eval_column: "Rainbows form when water droplets refract, reflect, and disperse sunlight.",
            },
        ]

    samples: dict[str, list[dict[str, Any]]] = {
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
    return samples[args.type]


def maybe_download_results(args: argparse.Namespace, result: Any) -> None:
    """Download result rows when requested and available."""
    file_id = result_file_id(result)
    if file_id:
        print(f"  Result file: {file_id}")
    if args.download_results and file_id:
        download_result_file(file_id, args.download_results)


def run_classify(args: argparse.Namespace, dataset: list[dict[str, Any]]) -> None:
    """Classify evaluation — categorize responses into labels."""
    print("\n=== Classify Evaluation ===")
    file_id = upload_dataset(dataset)

    model_to_evaluate: str | dict[str, Any]
    if args.eval_column:
        model_to_evaluate = args.eval_column
        print(f"Using dataset column for candidate responses: {args.eval_column}")
    else:
        model_to_evaluate = build_model_config(
            model=args.eval_model,
            model_source=args.eval_model_source,
            system_template=args.eval_system_template,
            input_template=args.input_template,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            external_api_token=args.eval_external_api_token,
            external_base_url=args.eval_external_base_url,
        )

    evaluation = client.evals.create(
        type="classify",
        parameters={
            "input_data_file_path": file_id,
            "judge": build_judge_config(args, DEFAULT_CLASSIFY_TEMPLATE),
            "labels": ["positive", "negative", "neutral"],
            "pass_labels": ["positive"],
            "model_to_evaluate": model_to_evaluate,
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id, poll_interval=args.poll_interval)
    if getattr(result, "results", None):
        print(f"  Label counts: {result.results.label_counts}")
        print(f"  Pass percentage: {result.results.pass_percentage}")
        maybe_download_results(args, result)


def run_score(args: argparse.Namespace, dataset: list[dict[str, Any]]) -> None:
    """Score evaluation — rate responses on a numerical scale."""
    print("\n=== Score Evaluation ===")
    file_id = upload_dataset(dataset)

    model_to_evaluate: str | dict[str, Any]
    if args.eval_column:
        model_to_evaluate = args.eval_column
        print(f"Using dataset column for candidate responses: {args.eval_column}")
    else:
        model_to_evaluate = build_model_config(
            model=args.eval_model,
            model_source=args.eval_model_source,
            system_template=args.eval_system_template,
            input_template=args.input_template,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            external_api_token=args.eval_external_api_token,
            external_base_url=args.eval_external_base_url,
        )

    evaluation = client.evals.create(
        type="score",
        parameters={
            "input_data_file_path": file_id,
            "judge": build_judge_config(args, DEFAULT_SCORE_TEMPLATE),
            "min_score": 1.0,
            "max_score": 10.0,
            "pass_threshold": 7.0,
            "model_to_evaluate": model_to_evaluate,
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id, poll_interval=args.poll_interval)
    if getattr(result, "results", None):
        scores = result.results.aggregated_scores
        if scores:
            print(f"  Mean score: {scores.mean_score}")
            print(f"  Std score: {scores.std_score}")
            print(f"  Pass percentage: {scores.pass_percentage}")
        maybe_download_results(args, result)


def run_compare(args: argparse.Namespace, dataset: list[dict[str, Any]]) -> None:
    """Compare evaluation — A/B comparison between generated or dataset-column outputs."""
    print("\n=== Compare Evaluation ===")
    file_id = upload_dataset(dataset)

    if args.model_a_column and args.model_b_column:
        model_a: str | dict[str, Any] = args.model_a_column
        model_b: str | dict[str, Any] = args.model_b_column
        print(f"Using dataset columns for comparisons: {args.model_a_column} vs {args.model_b_column}")
    else:
        model_a = build_model_config(
            model=args.model_a,
            model_source=args.model_a_source,
            system_template=args.eval_system_template,
            input_template=args.input_template,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            external_api_token=args.model_a_external_api_token,
            external_base_url=args.model_a_external_base_url,
        )
        model_b = build_model_config(
            model=args.model_b,
            model_source=args.model_b_source,
            system_template=args.eval_system_template,
            input_template=args.input_template,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            external_api_token=args.model_b_external_api_token,
            external_base_url=args.model_b_external_base_url,
        )

    evaluation = client.evals.create(
        type="compare",
        parameters={
            "input_data_file_path": file_id,
            "judge": build_judge_config(args, DEFAULT_COMPARE_TEMPLATE),
            "model_a": model_a,
            "model_b": model_b,
        },
    )
    print(f"Created evaluation: {evaluation.workflow_id}")

    result = poll_evaluation(evaluation.workflow_id, poll_interval=args.poll_interval)
    if getattr(result, "results", None):
        print(f"  A wins: {result.results.a_wins}")
        print(f"  B wins: {result.results.b_wins}")
        print(f"  Ties: {result.results.ties}")
        maybe_download_results(args, result)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Together AI evaluations workflow")
    parser.add_argument(
        "--type",
        choices=["classify", "score", "compare"],
        default="classify",
        help="Evaluation workflow to run",
    )
    parser.add_argument("--dataset", help="Path to a JSONL dataset; uses bundled samples when omitted")
    parser.add_argument("--judge-model", default=JUDGE_MODEL, help="Judge model, endpoint ID, or provider shortcut")
    parser.add_argument(
        "--judge-model-source",
        choices=MODEL_SOURCES,
        default="serverless",
        help="Source for the judge model",
    )
    parser.add_argument(
        "--judge-system-template",
        help="Override the default judge Jinja2 template for the selected evaluation type",
    )
    parser.add_argument("--judge-external-api-token", help="API key for an external judge model")
    parser.add_argument("--judge-external-base-url", help="Custom OpenAI-compatible base URL for the judge")
    parser.add_argument("--eval-model", default=EVAL_MODEL, help="Target model for classify or score")
    parser.add_argument(
        "--eval-model-source",
        choices=MODEL_SOURCES,
        default="serverless",
        help="Source for the target model used in classify or score",
    )
    parser.add_argument("--eval-column", help="Dataset column containing pre-generated responses")
    parser.add_argument(
        "--eval-system-template",
        default=DEFAULT_EVAL_SYSTEM_TEMPLATE,
        help="System template for model-based evaluation targets",
    )
    parser.add_argument(
        "--input-template",
        default=DEFAULT_INPUT_TEMPLATE,
        help="Jinja2 input template for model-based evaluation targets",
    )
    parser.add_argument("--max-tokens", type=int, default=512, help="Maximum generation tokens")
    parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    parser.add_argument("--eval-external-api-token", help="API key for an external evaluation target")
    parser.add_argument("--eval-external-base-url", help="Custom OpenAI-compatible base URL for the target")
    parser.add_argument(
        "--model-a",
        default="Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
        help="Model A for compare evaluations",
    )
    parser.add_argument(
        "--model-a-source",
        choices=MODEL_SOURCES,
        default="serverless",
        help="Source for model A",
    )
    parser.add_argument("--model-a-column", help="Dataset column containing pre-generated model A responses")
    parser.add_argument("--model-a-external-api-token", help="API key for external model A")
    parser.add_argument("--model-a-external-base-url", help="Custom OpenAI-compatible base URL for model A")
    parser.add_argument("--model-b", default=EVAL_MODEL, help="Model B for compare evaluations")
    parser.add_argument(
        "--model-b-source",
        choices=MODEL_SOURCES,
        default="serverless",
        help="Source for model B",
    )
    parser.add_argument("--model-b-column", help="Dataset column containing pre-generated model B responses")
    parser.add_argument("--model-b-external-api-token", help="API key for external model B")
    parser.add_argument("--model-b-external-base-url", help="Custom OpenAI-compatible base URL for model B")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between evaluation status checks",
    )
    parser.add_argument(
        "--download-results",
        help="Optional local path for the per-row results JSONL file",
    )
    args = parser.parse_args()

    if (args.model_a_column and not args.model_b_column) or (args.model_b_column and not args.model_a_column):
        parser.error("--model-a-column and --model-b-column must be provided together")
    if args.type != "compare" and (args.model_a_column or args.model_b_column):
        parser.error("--model-a-column and --model-b-column only apply to --type compare")
    return args


def main() -> None:
    args = parse_args()
    dataset = load_dataset(args.dataset, fallback_rows=sample_dataset_for_args(args))

    if args.type == "classify":
        run_classify(args, dataset)
    elif args.type == "score":
        run_score(args, dataset)
    else:
        run_compare(args, dataset)


if __name__ == "__main__":
    main()
