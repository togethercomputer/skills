#!/usr/bin/env python3
"""
Together AI Dedicated Model Inference -- Upload and Deploy a Custom Model or LoRA Adapter

Register a model record, import weights from Hugging Face or a presigned S3
URL, poll the upload job, and deploy the result on a dedicated endpoint.

Usage:
    python upload_custom_model.py create --name gemma-4-31b-it --base-model ml_base123
    python upload_custom_model.py upload --model ml_abc123 --from-url https://huggingface.co/org/repo [--hf-token hf_...] [--adapter]
    python upload_custom_model.py poll --job job_abc123 [--adapter]
    python upload_custom_model.py deploy --model ml_abc123 --config cr_abc123 --endpoint my-custom-model

Requires:
    uv pip install --upgrade together   # a release with the beta DMI surface (client.beta.*)
    export TOGETHER_API_KEY=your_key

Upload requirements:
    - Weights must be a fine-tuned variant of a base model Together supports for
      dedicated inference (uploads can't introduce new architectures). Meeting
      the requirements is necessary but not sufficient: unsupported base models,
      layer types, or adapter ranks are rejected at create/upload time.
    - Hugging Face repo layout compatible with from_pretrained; adapters need
      adapter_config.json + adapter_model.safetensors.
    - S3 sources: one .zip/.tar.gz archive with files at the archive ROOT, and a
      presigned URL valid for at least 100 minutes.
    - Name records bare (gemma-4-31b-it), never org-prefixed (google/gemma-4-31b-it):
      the platform prepends your project slug, and a doubled name can't be renamed.
"""

import argparse
import sys
import time

from together import Together

client = Together()
PROJECT_ID = client.whoami().project_id


def create_record(name: str, base_model_id: str, description: str | None = None):
    """Register the model/adapter record. Weights are attached by a later upload."""
    if "/" in name:
        print(f"WARNING: '{name}' looks org-prefixed; this produces an unrenamable doubled slug.")
    model = client.beta.models.create(
        project_id=PROJECT_ID,
        model={"name": name, "base_model_id": base_model_id, "description": description},
    )
    print(f"Created model record: {model.id} ({model.name})")
    return model


def start_remote_upload(model_id: str, remote_url: str, hf_token: str | None, adapter: bool):
    """Stream weights server-side from Hugging Face or a presigned S3 URL."""
    job = client.beta.models.remote_uploads.create(
        project_id=PROJECT_ID,
        type="adapter" if adapter else "model",
        model_id=model_id,
        remote_url=remote_url,
        token=hf_token,
    )
    print(f"Upload job: {job.id} (status: {job.status})")
    return job


def poll_job(job_id: str, adapter: bool, timeout: int = 7200, poll: int = 20):
    """Poll the upload job until REMOTE_UPLOAD_STATUS_SUCCEEDED."""
    upload_type = "adapters" if adapter else "models"
    elapsed = 0
    while elapsed < timeout:
        job = client.beta.models.remote_uploads.retrieve(
            job_id, project_id=PROJECT_ID, type=upload_type
        )
        print(f"  {job.status}  {job.status_message or ''}")
        if job.status == "REMOTE_UPLOAD_STATUS_SUCCEEDED":
            print("Upload complete. Verify files with: tg beta models ls-files <model_id>")
            return job
        if "FAILED" in (job.status or ""):
            raise RuntimeError(f"Upload failed: {job.status_message}")
        time.sleep(poll)
        elapsed += poll
    raise TimeoutError(f"Upload not finished after {timeout}s")


def deploy(model_id: str, config_id: str, config_project_id: str, endpoint_name: str):
    """Deploy the uploaded model like any other: endpoint + deployment + traffic."""
    endpoint = client.beta.endpoints.create(project_id=PROJECT_ID, name=endpoint_name)
    deployment = client.beta.endpoints.deployments.create(
        endpoint.id,
        project_id=PROJECT_ID,
        name="prod",
        model=f"projects/{PROJECT_ID}/models/{model_id}",
        config=f"projects/{config_project_id}/configs/{config_id}",
        autoscaling={"min_replicas": 1, "max_replicas": 1},
    )
    client.beta.endpoints.update(
        endpoint.id,
        project_id=PROJECT_ID,
        traffic_split=[{"deployment_id": deployment.id, "weight": 1}],
    )
    print(f"Deployed. Endpoint: {endpoint.id}  Deployment: {deployment.id}")
    print(f"Poll status, then send requests with model='{endpoint.name}'")
    return endpoint, deployment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="Register a model/adapter record")
    p.add_argument("--name", required=True, help="Bare name, no org prefix")
    p.add_argument("--base-model", required=True, help="Supported base model ID (ml_...)")
    p.add_argument("--description", default=None)

    p = sub.add_parser("upload", help="Start a remote upload from HF or presigned S3 URL")
    p.add_argument("--model", required=True, help="Model record ID (ml_...)")
    p.add_argument("--from-url", required=True, help="HF repo URL or presigned S3 archive URL")
    p.add_argument("--hf-token", default=None, help="Token for gated/private HF repos")
    p.add_argument("--adapter", action="store_true", help="Upload is a LoRA adapter")

    p = sub.add_parser("poll", help="Poll an upload job until it succeeds")
    p.add_argument("--job", required=True, help="Upload job ID (job_...)")
    p.add_argument("--adapter", action="store_true")

    p = sub.add_parser("deploy", help="Deploy the uploaded model")
    p.add_argument("--model", required=True, help="Model ID (ml_...)")
    p.add_argument("--config", required=True, help="Config revision ID (cr_...)")
    p.add_argument("--config-project", default=PROJECT_ID, help="Config's owning project")
    p.add_argument("--endpoint", required=True, help="New endpoint name")

    args = parser.parse_args()
    if args.command == "create":
        create_record(args.name, args.base_model, args.description)
    elif args.command == "upload":
        start_remote_upload(args.model, args.from_url, args.hf_token, args.adapter)
    elif args.command == "poll":
        poll_job(args.job, args.adapter)
    elif args.command == "deploy":
        deploy(args.model, args.config, args.config_project, args.endpoint)
    return 0


if __name__ == "__main__":
    sys.exit(main())
