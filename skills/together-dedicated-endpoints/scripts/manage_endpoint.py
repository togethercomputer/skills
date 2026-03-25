#!/usr/bin/env python3
"""
Together AI Dedicated Endpoints -- Create, Monitor, Use, Stop (v2 SDK)

Full lifecycle: list hardware, create endpoint, wait for ready,
run inference, then stop or delete.

Usage:
    python manage_endpoint.py list-hardware --model Qwen/Qwen3.5-9B-FP8
    python manage_endpoint.py create --model Qwen/Qwen3.5-9B-FP8 --hardware 1x_nvidia_h100_80gb_sxm
    python manage_endpoint.py demo

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import time

from together import Together

client = Together()


def list_hardware(model: str | None = None) -> list:
    """List available hardware options, optionally filtered by model."""
    response = client.endpoints.list_hardware(model=model)
    for hw in response.data:
        status = hw.availability.status if hw.availability else "unknown"
        price = hw.pricing.cents_per_minute if hw.pricing else "N/A"
        print(f"  {hw.id} ({status}, {price}c/min)")
    return response.data


def list_endpoints() -> list:
    """List all endpoints owned by the caller."""
    response = client.endpoints.list()
    for endpoint in response.data:
        print(f"  {endpoint.id}: {endpoint.model} ({endpoint.state})")
    return response.data


def create_endpoint(
    model: str,
    hardware: str,
    min_replicas: int = 1,
    max_replicas: int = 1,
    display_name: str | None = None,
    inactive_timeout: int | None = 60,
):
    """Create a dedicated endpoint."""
    endpoint = client.endpoints.create(
        model=model,
        hardware=hardware,
        autoscaling={
            "min_replicas": min_replicas,
            "max_replicas": max_replicas,
        },
        display_name=display_name,
        inactive_timeout=inactive_timeout,
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
    """Send a chat completion to the dedicated endpoint."""
    response = client.chat.completions.create(
        model=endpoint_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    reply = response.choices[0].message.content
    print(f"Response: {reply}")
    return reply


def stop_endpoint(endpoint_id: str):
    """Stop but do not delete an endpoint."""
    endpoint = client.endpoints.update(endpoint_id, state="STOPPED")
    print(f"Stopped endpoint: {endpoint.id} (state: {endpoint.state})")
    return endpoint


def delete_endpoint(endpoint_id: str) -> None:
    """Permanently delete an endpoint."""
    client.endpoints.delete(endpoint_id)
    print(f"Deleted endpoint: {endpoint_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI dedicated endpoint management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_hardware_parser = subparsers.add_parser("list-hardware", help="List available hardware")
    list_hardware_parser.add_argument("--model", help="Optional model filter")

    subparsers.add_parser("list-endpoints", help="List existing endpoints")

    create_parser = subparsers.add_parser("create", help="Create a dedicated endpoint")
    create_parser.add_argument("--model", required=True, help="Model name to deploy")
    create_parser.add_argument("--hardware", required=True, help="Hardware id to use")
    create_parser.add_argument("--min-replicas", type=int, default=1, help="Minimum replicas")
    create_parser.add_argument("--max-replicas", type=int, default=1, help="Maximum replicas")
    create_parser.add_argument("--display-name", help="Optional display name")
    create_parser.add_argument("--inactive-timeout", type=int, default=60, help="Inactive timeout in minutes")

    wait_parser = subparsers.add_parser("wait", help="Wait for an endpoint to become ready")
    wait_parser.add_argument("--endpoint-id", required=True, help="Endpoint id")
    wait_parser.add_argument("--timeout", type=int, default=600, help="Maximum wait time in seconds")
    wait_parser.add_argument("--poll-interval", type=int, default=10, help="Seconds between polls")

    infer_parser = subparsers.add_parser("infer", help="Run inference against an endpoint")
    infer_parser.add_argument("--model-name", required=True, help="Endpoint model name to query")
    infer_parser.add_argument("--prompt", required=True, help="Prompt to send")

    stop_parser = subparsers.add_parser("stop", help="Stop an endpoint")
    stop_parser.add_argument("--endpoint-id", required=True, help="Endpoint id")

    delete_parser = subparsers.add_parser("delete", help="Delete an endpoint")
    delete_parser.add_argument("--endpoint-id", required=True, help="Endpoint id")

    demo_parser = subparsers.add_parser("demo", help="Run the full example flow")
    demo_parser.add_argument("--model", default="Qwen/Qwen3.5-9B-FP8", help="Model name")
    demo_parser.add_argument("--hardware", default="1x_nvidia_h100_80gb_sxm", help="Hardware id")
    demo_parser.add_argument("--display-name", default="My Qwen Endpoint", help="Endpoint display name")
    demo_parser.add_argument(
        "--prompt",
        default="What is the capital of France?",
        help="Prompt for the inference step",
    )
    demo_parser.add_argument("--timeout", type=int, default=600, help="Maximum wait time in seconds")
    demo_parser.add_argument("--poll-interval", type=int, default=10, help="Seconds between polls")
    demo_parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete the endpoint at the end instead of leaving it stopped",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "list-hardware":
        list_hardware(model=args.model)
        return
    if args.command == "list-endpoints":
        list_endpoints()
        return
    if args.command == "create":
        create_endpoint(
            model=args.model,
            hardware=args.hardware,
            min_replicas=args.min_replicas,
            max_replicas=args.max_replicas,
            display_name=args.display_name,
            inactive_timeout=args.inactive_timeout,
        )
        return
    if args.command == "wait":
        wait_for_ready(args.endpoint_id, timeout=args.timeout, poll_interval=args.poll_interval)
        return
    if args.command == "infer":
        run_inference(args.model_name, args.prompt)
        return
    if args.command == "stop":
        stop_endpoint(args.endpoint_id)
        return
    if args.command == "delete":
        delete_endpoint(args.endpoint_id)
        return

    print("Available hardware:")
    list_hardware(model=args.model)
    print("\nYour endpoints:")
    list_endpoints()
    endpoint = create_endpoint(
        model=args.model,
        hardware=args.hardware,
        display_name=args.display_name,
    )
    endpoint = wait_for_ready(endpoint.id, timeout=args.timeout, poll_interval=args.poll_interval)
    run_inference(endpoint.name, args.prompt)
    if args.delete:
        delete_endpoint(endpoint.id)
    else:
        stop_endpoint(endpoint.id)


if __name__ == "__main__":
    main()
