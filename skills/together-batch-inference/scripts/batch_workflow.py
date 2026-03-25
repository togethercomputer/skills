#!/usr/bin/env python3
"""
Together AI Batch Inference — Full Workflow (v2 SDK)

End-to-end: prepare JSONL -> upload -> create batch -> poll -> download results.

Usage:
    python batch_workflow.py
    python batch_workflow.py --prompt "Classify this review: great product" --prompt "Summarize this note"
    python batch_workflow.py --input-jsonl requests.jsonl --output-path results.jsonl

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


def build_sample_requests(prompts: list[str], model: str, max_tokens: int) -> list[dict]:
    """Build a small batch request list from prompts."""
    return [
        {
            "custom_id": f"req-{index}",
            "body": {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
        }
        for index, prompt in enumerate(prompts, start=1)
    ]


def load_requests_from_jsonl(path: str) -> list[dict]:
    """Load batch requests from a JSONL file."""
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI Batch API workflow")
    parser.add_argument("--input-jsonl", help="Path to a JSONL file containing batch requests")
    parser.add_argument(
        "--prompt",
        action="append",
        default=[],
        help="Prompt to include in a generated sample batch payload. Repeat for multiple prompts.",
    )
    parser.add_argument(
        "--model",
        default="Qwen/Qwen2.5-7B-Instruct-Turbo",
        help="Model to use when generating a sample batch payload",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=128,
        help="max_tokens value for generated sample requests",
    )
    parser.add_argument(
        "--output-path",
        default="batch_results.jsonl",
        help="Where to save the batch output JSONL file",
    )
    parser.add_argument(
        "--error-path",
        default="batch_errors.jsonl",
        help="Where to save the batch error JSONL file",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Seconds between status checks",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompts = args.prompt or [
        "What is the capital of France?",
        "Explain quantum computing in one sentence.",
    ]
    requests = (
        load_requests_from_jsonl(args.input_jsonl)
        if args.input_jsonl
        else build_sample_requests(prompts=prompts, model=args.model, max_tokens=args.max_tokens)
    )

    # --- 1. Prepare batch input file ---
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for req in requests:
            temp_file.write(json.dumps(req) + "\n")
        input_path = Path(temp_file.name)

    print(f"Wrote {len(requests)} requests to {input_path}")

    # --- 2. Upload input file ---
    try:
        file_response = client.files.upload(file=str(input_path), purpose="batch-api", check=False)
    finally:
        input_path.unlink(missing_ok=True)
    file_id = file_response.id
    print(f"Uploaded file: {file_id}")

    # --- 3. Create batch job ---
    response = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
    )
    batch = response.job
    print(f"Created batch: {batch.id} (status: {batch.status})")

    # --- 4. Poll for completion ---
    while True:
        batch = client.batches.retrieve(batch.id)
        print(f"  Status: {batch.status} | Progress: {batch.progress:.0f}%")

        if batch.status == "COMPLETED":
            break
        if batch.status in ("FAILED", "EXPIRED", "CANCELLED"):
            print(f"Batch ended with status: {batch.status}")
            if batch.error:
                print(f"Error: {batch.error}")
            raise SystemExit(1)

        time.sleep(args.poll_interval)

    # --- 5. Download results ---
    if batch.output_file_id:
        with client.files.with_streaming_response.content(id=batch.output_file_id) as output_response:
            with open(args.output_path, "wb") as handle:
                for chunk in output_response.iter_bytes():
                    handle.write(chunk)
        print(f"\nResults saved to {args.output_path}")

        with open(args.output_path, encoding="utf-8") as handle:
            for line in handle:
                result = json.loads(line)
                custom_id = result.get("custom_id", "?")
                content = (
                    result.get("response", {})
                    .get("body", {})
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                print(f"  [{custom_id}] {content[:100]}")

    # --- 6. Check for errors ---
    if batch.error_file_id:
        with client.files.with_streaming_response.content(id=batch.error_file_id) as error_response:
            with open(args.error_path, "wb") as handle:
                for chunk in error_response.iter_bytes():
                    handle.write(chunk)
        print(f"Errors saved to {args.error_path}")


if __name__ == "__main__":
    main()
