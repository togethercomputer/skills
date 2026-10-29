#!/usr/bin/env python3
"""
Together AI Fine-Tuning -- DPO Preference Workflow (SDK 3.x)

End-to-end: SFT first, then DPO preference tuning from checkpoint, then deploy
the result on dedicated model inference (DMI) and send a test request.
Best practice is to run SFT before DPO for better model quality.

Usage:
    python dpo_workflow.py
    python dpo_workflow.py --sft-training-file sft.jsonl --dpo-training-file dpo.jsonl
    python dpo_workflow.py --model meta-llama/Llama-3.2-3B-Instruct
    python dpo_workflow.py --endpoint-name my-dpo-endpoint --config cr_abc123

Requires:
    uv pip install --upgrade "together>=3"
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

# SDK 3.x base URLs omit /v1; each method adds its own version.
INFERENCE_BASE_URL = "https://api-inference.together.ai"


def wait_for_file_ready(file_id: str, poll_interval: int = 5) -> None:
    """Block until server-side fine-tuning validation finishes for ``file_id``."""
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


def sample_sft_data() -> list[dict]:
    """Return a small SFT dataset for the DPO warm-up stage."""
    return [
        {
            "messages": [
                {"role": "user", "content": "Explain quantum computing simply."},
                {
                    "role": "assistant",
                    "content": (
                        "Quantum computing uses quantum bits (qubits) that can represent "
                        "0 and 1 simultaneously through superposition. This allows quantum "
                        "computers to explore many solutions at once for certain problems."
                    ),
                },
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "What is machine learning?"},
                {
                    "role": "assistant",
                    "content": (
                        "Machine learning is a branch of AI where systems learn patterns "
                        "from data instead of being explicitly programmed. Models improve "
                        "their predictions as they see more examples."
                    ),
                },
            ]
        },
    ]


def sample_dpo_data() -> list[dict]:
    """Return a small preference dataset for DPO training."""
    return [
        {
            "input": {"messages": [{"role": "user", "content": "Explain quantum computing simply."}]},
            "preferred_output": [
                {
                    "role": "assistant",
                    "content": (
                        "Quantum computing uses quantum bits (qubits) that can be in "
                        "superposition -- representing both 0 and 1 at once. This enables "
                        "solving certain problems exponentially faster than classical computers."
                    ),
                }
            ],
            "non_preferred_output": [
                {
                    "role": "assistant",
                    "content": "It's just faster computers that use quantum stuff.",
                }
            ],
        },
        {
            "input": {"messages": [{"role": "user", "content": "What is machine learning?"}]},
            "preferred_output": [
                {
                    "role": "assistant",
                    "content": (
                        "Machine learning is a branch of AI where systems learn patterns from "
                        "data rather than following explicit rules. Models are trained on examples "
                        "and progressively improve their accuracy on new, unseen data."
                    ),
                }
            ],
            "non_preferred_output": [
                {
                    "role": "assistant",
                    "content": "ML means computers learn things.",
                }
            ],
        },
    ]


def resolve_project_id() -> str:
    """TOGETHER_PROJECT_ID if set, else the project of a project-scoped API key."""
    if client.project_id:
        return client.project_id
    identity = client.whoami()
    project = getattr(identity, "project", None)
    if project is None:
        raise SystemExit(f"whoami returned {identity.type}, which has no project: set TOGETHER_PROJECT_ID.")
    return project.id


def deploy_fine_tuned_model(
    model_object_id: str,
    endpoint_name: str,
    config_id: str | None = None,
    poll_interval: int = 30,
):
    """Serve a completed fine-tune on dedicated model inference and wait for READY.

    The SDK version of ``tg endpoints deploy <model_object_id> --endpoint <name>``:
    pick a config for the base model, create the endpoint, attach a deployment,
    and route all traffic to it. Returns the endpoint and the deployment.
    """
    project_id = resolve_project_id()
    model = client.models.retrieve(model_object_id, project_id=project_id)

    # Configs are published for the base model.
    configs = list(
        client.models.configs.list(
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

    endpoint = client.endpoints.create(project_id=project_id, name=endpoint_name)
    print(f"Created endpoint: {endpoint.id} ({endpoint.name})")
    deployment = client.endpoints.deployments.create(
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
    client.endpoints.update(
        endpoint.id,
        project_id=project_id,
        traffic_split=[{"deployment_id": deployment.id, "weight": 1}],
    )

    while True:
        current = client.endpoints.deployments.retrieve(
            deployment.id, project_id=project_id, endpoint_id=endpoint.id
        )
        print(f"  Deployment state: {current.status.state}")
        if current.status.state == "DEPLOYMENT_STATE_READY":
            return endpoint, deployment
        if current.status.state == "DEPLOYMENT_STATE_FAILED":
            print(f"Deployment failed: {current.status.message}")
            raise SystemExit(1)
        time.sleep(poll_interval)


def create_temp_dataset(rows: list[dict]) -> Path:
    """Write JSONL rows to a temporary file."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as temp_file:
        for row in rows:
            temp_file.write(json.dumps(row) + "\n")
        return Path(temp_file.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI DPO fine-tuning workflow")
    parser.add_argument("--sft-training-file", help="Path to an SFT training JSONL file")
    parser.add_argument("--dpo-training-file", help="Path to a DPO preference JSONL file")
    parser.add_argument(
        "--model",
        default="meta-llama/Llama-3.2-3B-Instruct",
        help="Base model for both SFT and DPO",
    )
    parser.add_argument("--sft-suffix", default="sft-step", help="Suffix for the SFT warm-up job")
    parser.add_argument("--dpo-suffix", default="dpo-step", help="Suffix for the DPO job")
    parser.add_argument("--sft-epochs", type=int, default=3, help="Epochs for the SFT warm-up job")
    parser.add_argument("--dpo-epochs", type=int, default=2, help="Epochs for the DPO job")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Learning rate for the SFT warm-up job")
    parser.add_argument("--dpo-beta", type=float, default=0.2, help="DPO beta value")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between status checks")
    parser.add_argument(
        "--test-prompt",
        default="Explain quantum computing simply.",
        help="Prompt to send to the final fine-tuned model",
    )
    parser.add_argument(
        "--endpoint-name",
        default="dpo-finetuned",
        help="Name for the new dedicated endpoint (unique in your project)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Config ID (cr_...) when the base model has more than one; list with tg models configs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sft_path: Path | None = None
    dpo_path: Path | None = None
    sft_upload_path = args.sft_training_file
    dpo_upload_path = args.dpo_training_file

    if sft_upload_path is None:
        sft_path = create_temp_dataset(sample_sft_data())
        sft_upload_path = str(sft_path)
    if dpo_upload_path is None:
        dpo_path = create_temp_dataset(sample_dpo_data())
        dpo_upload_path = str(dpo_path)

    # --- 3. Upload both files ---
    try:
        sft_file = client.files.upload(file=sft_upload_path, purpose="fine-tune", check=True)
        dpo_file = client.files.upload(file=dpo_upload_path, purpose="fine-tune", check=True)
    finally:
        if sft_path is not None:
            sft_path.unlink(missing_ok=True)
        if dpo_path is not None:
            dpo_path.unlink(missing_ok=True)
    print(f"SFT file: {sft_file.id}")
    print(f"DPO file: {dpo_file.id}")

    # Wait for server-side validation on both files before starting training.
    print("Waiting for server-side validation...")
    wait_for_file_ready(sft_file.id)
    wait_for_file_ready(dpo_file.id)
    print("Files ready for fine-tuning.")

    # --- 4. Step 1: Run SFT job first ---
    print("\n--- Step 1: SFT Training ---")
    sft_job = client.fine_tuning.create(
        training_file=sft_file.id,
        model=args.model,
        lora=True,
        n_epochs=args.sft_epochs,
        learning_rate=args.learning_rate,
        suffix=args.sft_suffix,
    )
    print(f"SFT job: {sft_job.id}")

    while True:
        status = client.fine_tuning.retrieve(id=sft_job.id)
        print(f"  SFT status: {status.status}")
        if status.status == "completed":
            print(f"  SFT output: {status.x_model_output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"SFT failed: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 5. Step 2: Run DPO from SFT checkpoint ---
    print("\n--- Step 2: DPO Training (from SFT checkpoint) ---")
    dpo_job = client.fine_tuning.create(
        training_file=dpo_file.id,
        from_checkpoint=sft_job.id,
        model=args.model,
        training_method="dpo",
        dpo_beta=args.dpo_beta,
        lora=True,
        n_epochs=args.dpo_epochs,
        suffix=args.dpo_suffix,
    )
    print(f"DPO job: {dpo_job.id}")

    while True:
        status = client.fine_tuning.retrieve(id=dpo_job.id)
        print(f"  DPO status: {status.status}")
        if status.status == "completed":
            print(f"  DPO output: {status.x_model_output_name}")
            break
        if status.status in ("failed", "cancelled"):
            print(f"DPO failed: {status.status}")
            raise SystemExit(1)
        time.sleep(args.poll_interval)

    # --- 6. Deploy and test the DPO-tuned model ---
    print("\n--- Deploying DPO-tuned model ---")
    # Deploy by the registry ID (ml_...). model_output_name is not deployable.
    if not status.api_model_object_id:
        print("No model_object_id on the job: its weights did not reach the model registry.")
        raise SystemExit(1)
    endpoint, deployment = deploy_fine_tuned_model(
        status.api_model_object_id, args.endpoint_name, args.config, args.poll_interval
    )

    print("\n--- Testing DPO-tuned model ---")
    # Inference takes the endpoint string (endpoint.name) on the inference base URL.
    inference_client = Together(base_url=INFERENCE_BASE_URL)
    response = inference_client.chat.completions.create(
        model=endpoint.name,
        messages=[{"role": "user", "content": args.test_prompt}],
        max_tokens=256,
    )
    print(f"Response: {response.choices[0].message.content}")
    print(f"\nDeployment {deployment.id} is running and bills per minute. Tear it down when done:")
    print(f"  tg endpoints rm {endpoint.id} --force")


if __name__ == "__main__":
    main()
