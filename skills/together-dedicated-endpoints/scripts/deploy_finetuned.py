#!/usr/bin/env python3
"""
Together AI -- Deploy a Fine-tuned Model on a Dedicated Endpoint (v2 SDK)

Deploy a fine-tuned model (from a completed fine-tuning job) as a dedicated
endpoint, wait for it to become ready, and run inference.

Usage:
    python deploy_finetuned.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import time
from together import Together

client = Together()


def list_finetuning_jobs():
    """List recent fine-tuning jobs to find the model output name."""
    jobs = client.fine_tuning.list()
    for job in jobs.data:
        status = job.status
        model = getattr(job, "fine_tuned_model", None) or "pending"
        print(f"  {job.id}: {status}  model={model}")
    return jobs.data


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
        autoscaling={
            "min_replicas": min_replicas,
            "max_replicas": max_replicas,
        },
        display_name=display_name,
    )
    print(f"Created endpoint: {endpoint.id}  (state: {endpoint.state})")
    print(f"  Endpoint name (for inference): {endpoint.name}")
    return endpoint


def wait_for_ready(endpoint_id: str, timeout: int = 600, poll_interval: int = 10):
    """Poll until endpoint reaches STARTED state."""
    elapsed = 0
    while elapsed < timeout:
        endpoint = client.endpoints.retrieve(endpoint_id)
        print(f"  State: {endpoint.state}  ({elapsed}s)")

        if endpoint.state == "STARTED":
            return endpoint
        if endpoint.state == "ERROR":
            raise RuntimeError(f"Endpoint entered ERROR state: {endpoint_id}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Endpoint not ready after {timeout}s")


def run_inference(endpoint_name: str, prompt: str):
    """Send a chat completion to the fine-tuned model endpoint."""
    response = client.chat.completions.create(
        model=endpoint_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    reply = response.choices[0].message.content
    print(f"Response: {reply}")
    return reply


if __name__ == "__main__":
    # 1. List fine-tuning jobs to find your model
    print("Recent fine-tuning jobs:")
    list_finetuning_jobs()

    # 2. Set your fine-tuned model name (from the fine-tuning job output)
    FINETUNED_MODEL = "your-username/Qwen3-8B-your-suffix"
    HARDWARE = "4x_nvidia_h100_80gb_sxm"

    # 3. Check hardware options
    print(f"\nAvailable hardware for {FINETUNED_MODEL}:")
    hw_response = client.endpoints.list_hardware(model=FINETUNED_MODEL)
    for hw in hw_response.data:
        status = hw.availability.status if hw.availability else "unknown"
        print(f"  {hw.id}  ({status})")

    # 4. Deploy the fine-tuned model
    ep = deploy_finetuned(
        model_name=FINETUNED_MODEL,
        hardware=HARDWARE,
        display_name="Fine-tuned Qwen3-8B",
    )

    # 5. Wait until ready
    ep = wait_for_ready(ep.id)

    # 6. Run inference
    run_inference(ep.name, "What are some fun things to do in New York?")

    # 7. Stop when done to avoid charges
    client.endpoints.update(ep.id, state="STOPPED")
    print(f"Stopped endpoint: {ep.id}")
