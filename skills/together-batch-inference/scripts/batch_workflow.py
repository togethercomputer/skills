#!/usr/bin/env python3
"""
Together AI Batch Inference — Full Workflow (v2 SDK)

End-to-end: prepare JSONL → upload → create batch → poll → download results.

Usage:
    python batch_workflow.py

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
    # --- 1. Prepare batch input file ---
    requests = [
        {
            "custom_id": "req-1",
            "body": {
                "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
                "messages": [{"role": "user", "content": "What is the capital of France?"}],
                "max_tokens": 128,
            },
        },
        {
            "custom_id": "req-2",
            "body": {
                "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
                "messages": [{"role": "user", "content": "Explain quantum computing in one sentence."}],
                "max_tokens": 128,
            },
        },
    ]

    input_path = tempfile.mktemp(suffix=".jsonl")
    with open(input_path, "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")

    print(f"Wrote {len(requests)} requests to {input_path}")

    # --- 2. Upload input file ---
    file_response = client.files.upload(file=input_path, purpose="batch-api", check=False)
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

        time.sleep(10)

    # --- 5. Download results ---
    if batch.output_file_id:
        output_path = "batch_results.jsonl"
        with client.files.with_streaming_response.content(id=batch.output_file_id) as output_response:
            with open(output_path, "wb") as f:
                for chunk in output_response.iter_bytes():
                    f.write(chunk)
        print(f"\nResults saved to {output_path}")

        with open(output_path) as f:
            for line in f:
                result = json.loads(line)
                custom_id = result.get("custom_id", "?")
                content = result.get("response", {}).get("body", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  [{custom_id}] {content[:100]}")

    # --- 6. Check for errors ---
    if batch.error_file_id:
        error_path = "batch_errors.jsonl"
        with client.files.with_streaming_response.content(id=batch.error_file_id) as error_response:
            with open(error_path, "wb") as f:
                for chunk in error_response.iter_bytes():
                    f.write(chunk)
        print(f"Errors saved to {error_path}")


if __name__ == "__main__":
    main()
