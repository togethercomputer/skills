#!/usr/bin/env python3
"""
Together AI -- Deploy a Fine-tuned Model on a Dedicated Endpoint (v2 SDK)

Deploy a fine-tuned model as a dedicated endpoint, wait for it to become
ready, and optionally run inference or stop the endpoint.

Usage:
    python deploy_finetuned.py list-jobs
    python deploy_finetuned.py deploy --model-name your-username/Qwen3-8B-your-suffix --hardware 4x_nvidia_h100_80gb_sxm

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import time

from together import Together

client = Together()


def list_finetuning_jobs() -> list:
    """List recent fine-tuning jobs to help locate model output names."""
    jobs = client.fine_tuning.list()
    for job in jobs.data:
        status = job.status
        model = getattr(job, "fine_tuned_model", None) or getattr(job, "output_name", None) or "pending"
        print(f"  {job.id}: {status} model={model}")
    return jobs.data


def list_hardware(model_name: str) -> list:
    """List available hardware for a fine-tuned model."""
    response = client.endpoints.list_hardware(model=model_name)
    for hw in response.data:
        status = hw.availability.status if hw.availability else "unknown"
        print(f"  {hw.id} ({status})")
    return response.data


def deploy_finetuned(
    model_name: str,
    hardware: str,
    display_name: str | None = None,
    min_replicas: int = 1,
    max_replicas: int = 1,
):
    """Deploy a fine-tuned model on a dedicated endpoint."""
    endpoint = client.endpoints.create(
        model=model_name,
        hardware=hardware,
        autoscaling={"min_replicas": min_replicas, "max_replicas": max_replicas},
        display_name=display_name,
    )
    print(f"Created endpoint: {endpoint.id} (state: {endpoint.state})")
    print(f"  Endpoint name (for inference): {endpoint.name}")
    return endpoint


def wait_for_ready(endpoint_id: str, timeout: int = 600, poll_interval: int = 10):
    """Poll until endpoint reaches STARTED state."""
    elapsed = 0
    while elapsed < timeout:
        endpoint = client.endpoints.retrieve(endpoint_id)
        print(f"  State: {endpoint.state} ({elapsed}s)")

        if endpoint.state == "STARTED":
            return endpoint
        if endpoint.state == "ERROR":
            raise RuntimeError(f"Endpoint entered ERROR state: {endpoint_id}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Endpoint not ready after {timeout}s")


def run_inference(endpoint_name: str, prompt: str) -> str:
    """Send a chat completion to the fine-tuned model endpoint."""
    response = client.chat.completions.create(
        model=endpoint_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    reply = response.choices[0].message.content
    print(f"Response: {reply}")
    return reply


def stop_endpoint(endpoint_id: str) -> None:
    """Stop an endpoint to avoid charges."""
    client.endpoints.update(endpoint_id, state="STOPPED")
    print(f"Stopped endpoint: {endpoint_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy a fine-tuned model on Together AI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-jobs", help="List recent fine-tuning jobs")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy a fine-tuned model")
    deploy_parser.add_argument("--model-name", required=True, help="Fine-tuned model name to deploy")
    deploy_parser.add_argument("--hardware", required=True, help="Hardware id for the endpoint")
    deploy_parser.add_argument("--display-name", help="Optional endpoint display name")
    deploy_parser.add_argument("--min-replicas", type=int, default=1, help="Minimum replicas")
    deploy_parser.add_argument("--max-replicas", type=int, default=1, help="Maximum replicas")
    deploy_parser.add_argument("--show-hardware", action="store_true", help="List hardware before deploying")
    deploy_parser.add_argument("--timeout", type=int, default=600, help="Maximum wait time in seconds")
    deploy_parser.add_argument("--poll-interval", type=int, default=10, help="Seconds between polls")
    deploy_parser.add_argument(
        "--prompt",
        default="What are some fun things to do in New York?",
        help="Prompt to use after the endpoint becomes ready",
    )
    deploy_parser.add_argument(
        "--leave-running",
        action="store_true",
        help="Leave the endpoint running instead of stopping it after the test prompt",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "list-jobs":
        list_finetuning_jobs()
        return

    if args.show_hardware:
        print(f"Available hardware for {args.model_name}:")
        list_hardware(args.model_name)

    endpoint = deploy_finetuned(
        model_name=args.model_name,
        hardware=args.hardware,
        display_name=args.display_name,
        min_replicas=args.min_replicas,
        max_replicas=args.max_replicas,
    )
    endpoint = wait_for_ready(endpoint.id, timeout=args.timeout, poll_interval=args.poll_interval)
    run_inference(endpoint.name, args.prompt)
    if not args.leave_running:
        stop_endpoint(endpoint.id)


if __name__ == "__main__":
    main()
