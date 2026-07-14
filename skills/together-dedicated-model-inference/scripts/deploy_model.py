#!/usr/bin/env python3
"""
Together AI Dedicated Model Inference -- Deploy, Poll, Infer, Scale, Clean Up

Full DMI lifecycle from the SDK: list supported models and configs, create an
endpoint + deployment, route traffic, wait for READY, send a test request,
scale, stop, and delete.

Usage:
    python deploy_model.py models [--search qwen]
    python deploy_model.py configs --model ml_abc123
    python deploy_model.py deploy --model ml_abc123 --config cr_abc123 --endpoint my-endpoint
    python deploy_model.py status --endpoint ep_abc123 --deployment dep_abc123
    python deploy_model.py infer --name your-project-slug/my-endpoint
    python deploy_model.py scale --endpoint ep_abc123 --deployment dep_abc123 --min 1 --max 4
    python deploy_model.py stop --endpoint ep_abc123 --deployment dep_abc123
    python deploy_model.py rm --endpoint ep_abc123 --deployment dep_abc123

Requires:
    uv pip install --upgrade together   # a release with the beta DMI surface (client.beta.*)
    export TOGETHER_API_KEY=your_key

Billing note: replicas bill per minute while running and there is NO automatic
idle shutdown. `stop` (scale to 0/0) halts billing without deleting anything.
"""

import argparse
import sys
import time

from together import Together

client = Together()
PROJECT_ID = client.whoami().project_id

INFERENCE_BASE_URL = "https://api-inference.together.ai/v1"


def list_supported_models(search: str | None = None) -> list:
    """List public base models deployable for dedicated inference."""
    models = client.beta.models.list_supported(product="PRODUCT_DEDICATED")
    rows = [m for m in models.data if not search or search.lower() in m.name.lower()]
    for m in rows:
        print(f"  {m.id}  {m.name}")
    return rows


def list_configs(model_id: str) -> list:
    """List published configs (hardware/engine/optimization) for a model."""
    configs = client.beta.models.configs.list(
        project_id=PROJECT_ID,
        reference_model=f"projects/{PROJECT_ID}/models/{model_id}",
    )
    for c in configs.data:
        selectors = {s.key: s.value for s in (c.selectors or [])}
        print(
            f"  {c.id}  {selectors.get('accelerator_count', '?')}x "
            f"{selectors.get('accelerator_type', '?')}  "
            f"optimization={selectors.get('optimization', '?')}"
        )
    return configs.data


def deploy(
    model_id: str,
    config_id: str,
    config_project_id: str,
    endpoint_name: str,
    min_replicas: int = 1,
    max_replicas: int = 1,
):
    """Create an endpoint, attach a deployment, and route 100% of traffic to it.

    This is what the CLI's `tg beta endpoints deploy` does in one command.
    """
    endpoint = client.beta.endpoints.create(project_id=PROJECT_ID, name=endpoint_name)
    print(f"Created endpoint: {endpoint.id} ({endpoint.name})")

    deployment = client.beta.endpoints.deployments.create(
        endpoint.id,
        project_id=PROJECT_ID,
        name=f"{endpoint_name}-deployment",
        model=f"projects/{PROJECT_ID}/models/{model_id}",
        config=f"projects/{config_project_id}/configs/{config_id}",
        autoscaling={"min_replicas": min_replicas, "max_replicas": max_replicas},
    )
    print(f"Created deployment: {deployment.id}")

    # A READY deployment still serves nothing until it's in the traffic split.
    client.beta.endpoints.update(
        endpoint.id,
        project_id=PROJECT_ID,
        traffic_split=[{"deployment_id": deployment.id, "weight": 1}],
    )
    print("Routed 100% of traffic to the deployment.")

    wait_for_ready(endpoint.id, deployment.id)
    print(f"\nEndpoint ready. Inference model name: {endpoint.name}")
    return endpoint, deployment


def wait_for_ready(endpoint_id: str, deployment_id: str, timeout: int = 3600, poll: int = 15):
    """Poll deployment status until READY (cold start can take minutes for large models)."""
    elapsed = 0
    while elapsed < timeout:
        d = client.beta.endpoints.deployments.retrieve(
            deployment_id, project_id=PROJECT_ID, endpoint_id=endpoint_id
        )
        state = d.status.state
        print(
            f"  {state}  ready={d.status.ready_replicas}/{d.desired_replicas}"
            f"  ({d.status.message or ''})"
        )
        if state == "DEPLOYMENT_STATE_READY":
            return d
        if state == "DEPLOYMENT_STATE_FAILED":
            raise RuntimeError(f"Deployment failed: {d.status.message}")
        time.sleep(poll)
        elapsed += poll
    raise TimeoutError(f"Deployment not READY after {timeout}s")


def show_status(endpoint_id: str, deployment_id: str):
    """Print the deployment's current state and replica counts."""
    d = client.beta.endpoints.deployments.retrieve(
        deployment_id, project_id=PROJECT_ID, endpoint_id=endpoint_id
    )
    print(f"  state:     {d.status.state}")
    print(f"  desired:   {d.desired_replicas}")
    print(f"  scheduled: {d.status.scheduled_replicas}")
    print(f"  ready:     {d.status.ready_replicas}")
    print(f"  message:   {d.status.message}")
    return d


def infer(qualified_name: str, prompt: str = "What is 2+2?"):
    """Send a chat completion to the endpoint via the shared inference API.

    `qualified_name` is `<project_slug>/<endpoint_name>` (from endpoint.name),
    not the ep_ ID.
    """
    inference_client = Together(base_url=INFERENCE_BASE_URL)
    response = inference_client.chat.completions.create(
        model=qualified_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=64,
    )
    print(response.choices[0].message.content)
    return response


def scale(endpoint_id: str, deployment_id: str, min_replicas: int, max_replicas: int):
    """Update replica bounds. 0/0 stops the deployment; min 0 with max > 0 is rejected."""
    d = client.beta.endpoints.deployments.update(
        deployment_id,
        project_id=PROJECT_ID,
        endpoint_id=endpoint_id,
        autoscaling={"min_replicas": min_replicas, "max_replicas": max_replicas},
    )
    print(f"Scaled {deployment_id} to bounds {min_replicas}/{max_replicas} (state: {d.status.state})")
    return d


def stop(endpoint_id: str, deployment_id: str):
    """Scale to zero: drains, then STOPPED, and billing stops. Config is preserved."""
    return scale(endpoint_id, deployment_id, 0, 0)


def delete(endpoint_id: str, deployment_id: str | None = None):
    """Tear down: stop deployment, wait for STOPPED, clear split, delete deployment + endpoint."""
    if deployment_id:
        stop(endpoint_id, deployment_id)
        while True:
            d = client.beta.endpoints.deployments.retrieve(
                deployment_id, project_id=PROJECT_ID, endpoint_id=endpoint_id
            )
            if d.status.state in ("DEPLOYMENT_STATE_STOPPED", "DEPLOYMENT_STATE_FAILED"):
                break
            print(f"  waiting for STOPPED (now {d.status.state})")
            time.sleep(10)
        client.beta.endpoints.update(endpoint_id, project_id=PROJECT_ID, traffic_split=[])
        client.beta.endpoints.deployments.delete(
            deployment_id, project_id=PROJECT_ID, endpoint_id=endpoint_id
        )
        print(f"Deleted deployment {deployment_id}")
    client.beta.endpoints.delete(endpoint_id, project_id=PROJECT_ID)
    print(f"Deleted endpoint {endpoint_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("models", help="List deployable public models")
    p.add_argument("--search", default=None)

    p = sub.add_parser("configs", help="List configs for a model")
    p.add_argument("--model", required=True, help="Model ID (ml_...)")

    p = sub.add_parser("deploy", help="Create endpoint + deployment, route traffic, wait for READY")
    p.add_argument("--model", required=True, help="Model ID (ml_...)")
    p.add_argument("--config", required=True, help="Config revision ID (cr_...)")
    p.add_argument("--config-project", default=PROJECT_ID, help="Config's owning project (from configs list)")
    p.add_argument("--endpoint", required=True, help="New endpoint name")
    p.add_argument("--min", type=int, default=1, dest="min_replicas")
    p.add_argument("--max", type=int, default=1, dest="max_replicas")

    p = sub.add_parser("status", help="Show deployment status")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--deployment", required=True)

    p = sub.add_parser("infer", help="Send a test chat completion")
    p.add_argument("--name", required=True, help="Qualified endpoint name (slug/endpoint)")
    p.add_argument("--prompt", default="What is 2+2?")

    p = sub.add_parser("scale", help="Update replica bounds")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--min", type=int, required=True, dest="min_replicas")
    p.add_argument("--max", type=int, required=True, dest="max_replicas")

    p = sub.add_parser("stop", help="Scale to 0/0 (stops billing)")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--deployment", required=True)

    p = sub.add_parser("rm", help="Delete deployment (if given) and endpoint")
    p.add_argument("--endpoint", required=True)
    p.add_argument("--deployment", default=None)

    args = parser.parse_args()
    if args.command == "models":
        list_supported_models(args.search)
    elif args.command == "configs":
        list_configs(args.model)
    elif args.command == "deploy":
        deploy(
            args.model, args.config, args.config_project, args.endpoint,
            args.min_replicas, args.max_replicas,
        )
    elif args.command == "status":
        show_status(args.endpoint, args.deployment)
    elif args.command == "infer":
        infer(args.name, args.prompt)
    elif args.command == "scale":
        scale(args.endpoint, args.deployment, args.min_replicas, args.max_replicas)
    elif args.command == "stop":
        stop(args.endpoint, args.deployment)
    elif args.command == "rm":
        delete(args.endpoint, args.deployment)
    return 0


if __name__ == "__main__":
    sys.exit(main())
