#!/usr/bin/env python3
"""
Together AI -- Upload and Deploy a Custom Model (v2 SDK)

Upload a custom model from Hugging Face or S3, wait for the upload job
to complete, then deploy it on a dedicated endpoint.

Usage:
    python upload_custom_model.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import time
from together import Together

client = Together()


def upload_from_huggingface(
    model_name: str,
    hf_repo: str,
    hf_token: str | None = None,
) -> str:
    """Upload a model from Hugging Face Hub. Returns the job ID."""
    kwargs: dict = {"model_name": model_name, "model_source": hf_repo}
    if hf_token:
        kwargs["hf_token"] = hf_token
    response = client.models.upload(**kwargs)
    job_id = response.data.job_id
    print(f"Upload started: job_id={job_id}")
    return job_id


def upload_from_s3(model_name: str, presigned_url: str) -> str:
    """Upload a model from an S3 presigned URL. Returns the job ID.

    Archive (.zip, .tar, .tar.gz) must have model files at root level.
    Presigned URL must have at least 100 minutes of validity.
    """
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
        print(f"  Upload status: {status}  ({elapsed}s)")

        if status == "Complete":
            print("Upload complete.")
            return
        if status in ("Failed", "Cancelled"):
            raise RuntimeError(f"Upload job {status}: {job_id}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Upload not complete after {timeout}s")


def deploy_model(model_name: str, hardware: str, display_name: str | None = None):
    """Deploy the uploaded model on a dedicated endpoint."""
    endpoint = client.endpoints.create(
        model=model_name,
        hardware=hardware,
        autoscaling={"min_replicas": 1, "max_replicas": 1},
        display_name=display_name,
    )
    print(f"Endpoint created: {endpoint.id}  (state: {endpoint.state})")
    print(f"  Endpoint name (for inference): {endpoint.name}")
    return endpoint


if __name__ == "__main__":
    MODEL_NAME = "my-custom-model"
    HF_REPO = "your-org/your-model"
    HARDWARE = "2x_nvidia_h100_80gb_sxm"

    # 1. Upload from Hugging Face (or use upload_from_s3 for S3)
    job_id = upload_from_huggingface(
        model_name=MODEL_NAME,
        hf_repo=HF_REPO,
        # hf_token="hf_...",  # uncomment for private repos
    )

    # 2. Wait for upload to complete
    wait_for_upload(job_id)

    # 3. Check hardware options
    print("\nAvailable hardware:")
    hw_response = client.endpoints.list_hardware(model=MODEL_NAME)
    for hw in hw_response.data:
        status = hw.availability.status if hw.availability else "unknown"
        print(f"  {hw.id}  ({status})")

    # 4. Deploy on dedicated endpoint
    ep = deploy_model(MODEL_NAME, HARDWARE, display_name="My Custom Model")
    print(f"\nEndpoint ID: {ep.id}")
    print(f"Use for inference: model='{ep.name}'")
