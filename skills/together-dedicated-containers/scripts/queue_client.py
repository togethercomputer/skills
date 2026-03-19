#!/usr/bin/env python3
"""
Together AI Dedicated Containers — Queue Client (v2 SDK)

Submit jobs, poll for results, and manage queue operations.

Usage:
    python queue_client.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import time
from together import Together

client = Together()

# Change this to your deployment name
DEPLOYMENT = "hello-world"


def submit_and_poll(payload: dict, priority: int = 1) -> dict:
    """Submit a job and poll until completion."""
    job = client.beta.jig.queue.submit(
        model=DEPLOYMENT,
        payload=payload,
        priority=priority,
    )
    print(f"Submitted job: {job.request_id}")

    while True:
        status = client.beta.jig.queue.retrieve(
            request_id=job.request_id,
            model=DEPLOYMENT,
        )
        print(f"  Status: {status.status}", end="")

        # Show progress if available
        if hasattr(status, "info") and status.info:
            progress = status.info.get("progress")
            if progress is not None:
                print(f" | Progress: {progress:.0%}", end="")
        print()

        if status.status == "done":
            print(f"  Outputs: {status.outputs}")
            return {"status": "done", "outputs": status.outputs}
        elif status.status == "failed":
            print(f"  Error: {getattr(status, 'error', 'unknown')}")
            return {"status": "failed", "error": getattr(status, "error", None)}
        elif status.status == "canceled":
            print("  Job was canceled")
            return {"status": "canceled"}

        time.sleep(2)


def submit_multiple(payloads: list[dict]) -> list[str]:
    """Submit multiple jobs and return their request IDs."""
    request_ids = []
    for payload in payloads:
        job = client.beta.jig.queue.submit(
            model=DEPLOYMENT,
            payload=payload,
        )
        request_ids.append(job.request_id)
        print(f"Submitted: {job.request_id}")
    return request_ids


def check_status(request_id: str) -> dict:
    """Check the status of a single job."""
    status = client.beta.jig.queue.retrieve(
        request_id=request_id,
        model=DEPLOYMENT,
    )
    print(f"Job {request_id}: {status.status}")
    if status.status == "done":
        print(f"  Outputs: {status.outputs}")
    return {"status": status.status, "outputs": getattr(status, "outputs", None)}


if __name__ == "__main__":
    # --- Example 1: Submit and wait for result ---
    print("=== Submit and poll ===")
    result = submit_and_poll({"name": "Together"})
    print()

    # --- Example 2: Submit with priority ---
    print("=== Priority job ===")
    result = submit_and_poll({"name": "Priority User"}, priority=10)
    print()

    # --- Example 3: Submit batch ---
    print("=== Batch submit ===")
    ids = submit_multiple([
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"},
    ])
    print(f"Submitted {len(ids)} jobs")

    # Poll all
    for rid in ids:
        time.sleep(1)
        check_status(rid)
