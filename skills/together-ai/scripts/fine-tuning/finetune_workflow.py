#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- Full Workflow (v2 SDK)

End-to-end: prepare data -> upload -> create LoRA job -> monitor -> deploy.

Usage:
    python finetune_workflow.py
    python finetune_workflow.py --training-file train.jsonl --model meta-llama/Meta-Llama-3.1-8B-Instruct-Reference
    python finetune_workflow.py --skip-deploy

Requires:
    uv pip install --upgrade together   # a release with the beta DMI surface (client.beta.*)
    export TOGETHER_API_KEY=your_key

Billing note: the deployment bills per minute per running replica until you
tear it down. The script prints the teardown command at the end.
"""

import argparse
import json
import tempfile
import time
from pathlib import Path

from together import Together

client = Together()

INFERENCE_BASE_URL = "https://api-inference.together.ai/v1"


def wait_for_file_ready(file_id: str, poll_interval: int = 5) -> None:
    """Block until server-side fine-tuning validation finishes for ``file_id``.

    Raises ``ValueError`` if the dataset is rejected (``INVALID_FORMAT``) and
    ``RuntimeError`` for any other terminal failure.
    """
    while True:
        meta = client.files.retrieve(file_id)
        if meta.processing_status == "COMPLETED":
            return
        if meta.processing_status == "INVALID_FORMAT":
            raise ValueError(
                f"file {file_id} is not suitable for fine-tuning: {meta.validation_report}"
            )
        if meta.processing_status == "FAILED":
            raise RuntimeError(
                f"file {file_id} processing did not complete: {meta.validation_report}"
            )
        time.sleep(poll_interval)


def sample_training_data() -> list[dict]:
    """Return a small conversational dataset for demonstration."""
    return [
        {
            "messages": [
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": "How do I reset my password?"},
                {
                    "role": "assistant",
                    "content": (
                        "Go to Settings > Security > Reset Password. "
                        "You'll receive a confirmation email within 5 minutes."
                    ),
                },
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": "What are your business hours?"},
                {
                    "role": "assistant",
                    "content": (
                        "We're available Monday-Friday, 9 AM - 6 PM EST. "
                        "Weekend support is available via email."
                    ),
                },
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": "How do I cancel my subscription?"},
                {
                    "role": "assistant",
                    "content": (
                        "Go to Settings > Billing > Cancel Subscription. "
                        "Your access continues until the end of the billing period."
                    ),
                },
            ]
        },
    ]


def create_temp_dataset(rows: list[dict]) -> Path:
    """Write JSONL rows to a temporary file."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for example in rows:
            temp_file.write(json.dumps(example) + "\n")
        return Path(temp_file.name)


def deploy_fine_tuned_model(
    model_object_id: str,
    endpoint_name: str,
    config_id: str | None = None,
    poll_interval: int = 30,
):
    """Serve a completed fine-tune on dedicated model inference and wait for READY.

    The SDK version of ``tg beta endpoints deploy <model_object_id> --endpoint <name>``:
    pick a config for the base model, create the endpoint, attach a deployment,
    and route all traffic to it. Returns the endpoint and the deployment.
    """
    project_id = client.whoami().project_id
    model = client.beta.models.retrieve(model_object_id, project_id=project_id)

    # Configs are published for the base model.
    configs = list(
        client.beta.models.configs.list(
            project_id=project_id,
            reference_model=model.base_model or f"projects/{model.project_id}/models/{model.id}",
        )
    )
    if config_id:
        config = next((c for c in configs if c.id == config_id), None)
        if config is None:
            raise SystemExit(f"Config {config_id} is not valid for {model_object_id}")
    elif len(configs) == 1:
        config = configs[0]
    else:
        available = ", ".join(c.id for c in configs) or "none"
        raise SystemExit(f"Choose a config with --config (available: {available})")

    endpoint = client.beta.endpoints.create(project_id=project_id, name=endpoint_name)
    print(f"Created endpoint: {endpoint.id} ({endpoint.name})")
    deployment = client.beta.endpoints.deployments.create(
        endpoint.id,
        project_id=project_id,
        name=f"{endpoint_name}-deployment",
        model=f"projects/{model.project_id}/models/{model.id}",
        # Use the config's own project: public configs can belong to another project.
        config=f"projects/{config.project_id}/configs/{config.id}",
        autoscaling={"min_replicas": 1, "max_replicas": 1},
    )
    print(f"Created deployment: {deployment.id}")

    # A READY deployment serves nothing until it is in the endpoint's traffic split.
    client.beta.endpoints.update(
        endpoint.id,
        project_id=project_id,
        traffic_split=[{"deployment_id": deployment.id, "weight": 1}],
    )

    while True:
        current = client.beta.endpoints.deployments.retrieve(
            deployment.id, project_id=project_id, endpoint_id=endpoint.id
        )
        print(f"  Deployment state: {current.status.state}")
        if current.status.state == "DEPLOYMENT_STATE_READY":
            return endpoint, deployment
        if current.status.state == "DEPLOYMENT_STATE_FAILED":
            print(f"Deployment failed: {current.status.message}")
            raise SystemExit(1)
        time.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI fine-tuning workflow")
    parser.add_argument("--training-file", help="Path to a training JSONL file")
    parser.add_argument(
        "--model",
        default="meta-llama/Meta-Llama-3.1-8B-Instruct-Reference",
        help="Base model to fine-tune",
    )
    parser.add_argument("--suffix", default="support-bot-v1", help="Suffix for the fine-tuned model")
    parser.add_argument("--n-epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Training learning rate")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between fine-tuning status checks",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Stop after training instead of creating a dedicated endpoint",
    )
    parser.add_argument(
        "--test-prompt",
        default="How do I update my billing info?",
        help="Prompt to use when testing the deployed model",
    )
    parser.add_argument(
        "--endpoint-name",
        default="support-bot-v1",
        help="Name for the new dedicated endpoint (unique in your project)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Config ID (cr_...) when the base model has more than one; list with tg beta models configs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path: Path | None = None
    upload_path = args.training_file
    if upload_path is None:
        training_data = sample_training_data()
        data_path = create_temp_dataset(training_data)
        upload_path = str(data_path)
        print(f"Wrote {len(training_data)} examples to {data_path}")

    # --- 2. Upload training file with validation enabled ---
    try:
        file_response = client.files.upload(file=upload_path, purpose="fine-tune", check=True)
    finally:
        if data_path is not None:
            data_path.unlink(missing_ok=True)
    file_id = file_response.id
    print(f"Uploaded file: {file_id}")

    # Wait for server-side validation before spending tokens on training.
    print("Waiting for server-side validation...")
    wait_for_file_ready(file_id)
    print("File ready for fine-tuning.")

    # --- 3. Create LoRA fine-tuning job ---
    job = client.fine_tuning.create(
        training_file=file_id,
        model=args.model,
        n_epochs=args.n_epochs,
        learning_rate=args.learning_rate,
        lora=True,
        suffix=args.suffix,
    )
    print(f"Created fine-tuning job: {job.id}")

    # --- 4. Monitor training ---
    while True:
        status = client.fine_tuning.retrieve(id=job.id)
        print(f"  Status: {status.status}")

        if status.status == "completed":
            print("\nTraining complete!")
            print(f"  Output model: {status.x_model_output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"Job ended: {status.status}")
            raise SystemExit(1)

        time.sleep(args.poll_interval)

    # --- 5. List training events ---
    events = client.fine_tuning.list_events(id=job.id)
    for event in events.data:
        print(f"  [{event.created_at}] {event.message}")

    if args.skip_deploy:
        print("\nSkipping deployment as requested.")
        return

    # --- 6. Deploy as a Dedicated Endpoint ---
    # Deploy by the registry ID (ml_...). model_output_name is not deployable.
    if not status.api_model_object_id:
        print("No model_object_id on the job: its weights did not reach the model registry.")
        raise SystemExit(1)
    endpoint, deployment = deploy_fine_tuned_model(
        status.api_model_object_id, args.endpoint_name, args.config, args.poll_interval
    )

    # --- 7. Query the fine-tuned model via the endpoint name ---
    # Inference takes the endpoint string (endpoint.name) on the inference base URL.
    inference_client = Together(base_url=INFERENCE_BASE_URL)
    response = inference_client.chat.completions.create(
        model=endpoint.name,
        messages=[
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": args.test_prompt},
        ],
        max_tokens=256,
    )
    print(f"\nFine-tuned model response: {response.choices[0].message.content}")
    print(f"\nDeployment {deployment.id} is running and bills per minute. Tear it down when done:")
    print(f"  tg beta endpoints rm {endpoint.id} --force")


if __name__ == "__main__":
    main()
