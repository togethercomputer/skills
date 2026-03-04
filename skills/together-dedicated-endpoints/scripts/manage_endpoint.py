#!/usr/bin/env python3
"""
Together AI Dedicated Endpoints — Create, Monitor, Use, Stop (v2 SDK)

Full lifecycle: list hardware, create endpoint, wait for ready,
run inference, then stop/delete.

Usage:
    python manage_endpoint.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import time
from together import Together

client = Together()


def list_hardware(model: str | None = None):
    """List available hardware options, optionally filtered by model."""
    response = client.endpoints.list_hardware(model=model)
    for hw in response.data:
        status = hw.availability.status if hw.availability else "unknown"
        price = hw.pricing.cents_per_minute if hw.pricing else "N/A"
        print(f"  {hw.id}  ({status}, {price}¢/min)")
    return response.data


def create_endpoint(
    model: str,
    hardware: str,
    min_replicas: int = 1,
    max_replicas: int = 1,
    display_name: str | None = None,
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
    )
    print(f"Created endpoint: {endpoint.id}  (state: {endpoint.state})")
    return endpoint


def wait_for_ready(endpoint_id: str, timeout: int = 600, poll_interval: int = 10):
    """Poll until endpoint reaches STARTED state."""
    elapsed = 0
    while elapsed < timeout:
        endpoint = client.endpoints.retrieve(endpoint_id)
        print(f"  State: {endpoint.state}  ({elapsed}s)")

        if endpoint.state == "STARTED":
            return endpoint

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Endpoint not ready after {timeout}s")


def run_inference(endpoint_name: str, prompt: str):
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
    """Stop (but don't delete) an endpoint."""
    endpoint = client.endpoints.update(endpoint_id, state="STOPPED")
    print(f"Stopped endpoint: {endpoint.id}  (state: {endpoint.state})")
    return endpoint


def delete_endpoint(endpoint_id: str):
    """Permanently delete an endpoint."""
    client.endpoints.delete(endpoint_id)
    print(f"Deleted endpoint: {endpoint_id}")


if __name__ == "__main__":
    MODEL = "openai/gpt-oss-20b"
    HARDWARE = "1x_nvidia_a100_80gb_sxm"

    # 1. List available hardware
    print("Available hardware:")
    list_hardware(model=MODEL)

    # 2. Create endpoint
    ep = create_endpoint(
        model=MODEL,
        hardware=HARDWARE,
        display_name="My Llama Endpoint",
    )

    # 3. Wait until ready
    ep = wait_for_ready(ep.id)

    # 4. Run inference
    run_inference(ep.name, "What is the capital of France?")

    # 5. Stop endpoint (comment out delete if you want to restart later)
    stop_endpoint(ep.id)

    # 6. Delete endpoint (uncomment to permanently remove)
    # delete_endpoint(ep.id)
