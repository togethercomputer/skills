#!/usr/bin/env python3
"""
Together AI -- Upload and Deploy a Custom Model (v2 SDK)

Upload a custom model from Hugging Face or S3, wait for the upload job
to complete, and optionally deploy it on a dedicated endpoint.

Usage:
    python upload_custom_model.py --model-name my-custom-model --hf-repo your-org/your-model --hardware 2x_nvidia_h100_80gb_sxm
    python upload_custom_model.py --model-name my-custom-model --s3-url https://signed-url --skip-deploy

Requires:
    uv pip install "together>=2.0.0"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import time

from together import Together

client = Together()


def upload_from_huggingface(model_name: str, hf_repo: str, hf_token: str | None = None) -> str:
    """Upload a model from Hugging Face Hub and return the upload job id."""
    kwargs: dict = {"model_name": model_name, "model_source": hf_repo}
    if hf_token:
        kwargs["hf_token"] = hf_token
    response = client.models.upload(**kwargs)
    job_id = response.data.job_id
    print(f"Upload started: job_id={job_id}")
    return job_id


def upload_from_s3(model_name: str, presigned_url: str) -> str:
    """Upload a model from an S3 presigned URL and return the upload job id."""
    response = client.models.upload(model_name=model_name, model_source=presigned_url)
    job_id = response.data.job_id
    print(f"Upload started: job_id={job_id}")
    return job_id


def check_upload_status(job_id: str) -> str:
    """Check upload job status via the v2 SDK."""
    response = client.models.uploads.status(job_id)
    return response.status


def wait_for_upload(job_id: str, timeout: int = 3600, poll_interval: int = 30) -> None:
    """Poll until the upload job completes."""
    elapsed = 0
    while elapsed < timeout:
        status = check_upload_status(job_id)
        print(f"  Upload status: {status} ({elapsed}s)")

        if status == "Complete":
            print("Upload complete.")
            return
        if status in ("Failed", "Cancelled"):
            raise RuntimeError(f"Upload job {status}: {job_id}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Upload not complete after {timeout}s")


def list_hardware(model_name: str) -> list:
    """List hardware available for a custom model."""
    response = client.endpoints.list_hardware(model=model_name)
    for hw in response.data:
        status = hw.availability.status if hw.availability else "unknown"
        print(f"  {hw.id} ({status})")
    return response.data


def deploy_model(model_name: str, hardware: str, display_name: str | None = None):
    """Deploy the uploaded model on a dedicated endpoint."""
    endpoint = client.endpoints.create(
        model=model_name,
        hardware=hardware,
        autoscaling={"min_replicas": 1, "max_replicas": 1},
        display_name=display_name,
    )
    print(f"Endpoint created: {endpoint.id} (state: {endpoint.state})")
    print(f"  Endpoint name (for inference): {endpoint.name}")
    return endpoint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload and optionally deploy a custom Together AI model")
    parser.add_argument("--model-name", required=True, help="Target Together AI model name")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--hf-repo", help="Hugging Face repo id")
    source_group.add_argument("--s3-url", help="Presigned S3 URL for a model archive")
    parser.add_argument("--hf-token", help="Hugging Face token for private repos")
    parser.add_argument("--hardware", help="Hardware id for optional deployment")
    parser.add_argument("--display-name", help="Optional endpoint display name")
    parser.add_argument("--show-hardware", action="store_true", help="List hardware after upload")
    parser.add_argument("--skip-deploy", action="store_true", help="Upload the model without deploying it")
    parser.add_argument("--timeout", type=int, default=3600, help="Maximum wait time in seconds")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between status checks")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.hf_repo:
        job_id = upload_from_huggingface(args.model_name, args.hf_repo, hf_token=args.hf_token)
    else:
        job_id = upload_from_s3(args.model_name, args.s3_url)

    wait_for_upload(job_id, timeout=args.timeout, poll_interval=args.poll_interval)

    if args.show_hardware or not args.skip_deploy:
        print("\nAvailable hardware:")
        list_hardware(args.model_name)

    if args.skip_deploy:
        return

    if not args.hardware:
        raise SystemExit("--hardware is required unless --skip-deploy is set")

    endpoint = deploy_model(args.model_name, args.hardware, display_name=args.display_name)
    print(f"\nEndpoint ID: {endpoint.id}")
    print(f"Use for inference: model='{endpoint.name}'")


if __name__ == "__main__":
    main()
