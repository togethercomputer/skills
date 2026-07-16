---
name: together-dedicated-endpoints
description: "Single-tenant GPU endpoints on Together AI with autoscaling and no rate limits. Deploy fine-tuned or uploaded models, upload LoRA adapters, size hardware, and manage endpoint lifecycle with the v2 dedicated model inference (DMI) resource model — endpoints, deployments, and configs — plus traffic splits, A/B tests, shadow experiments, and metric-gated rollouts. Reach for it whenever the user needs predictable always-on hosting rather than serverless inference, custom containers, or raw clusters."
---

# Together Dedicated Endpoints

## Overview

Dedicated endpoints serve a model on hardware reserved for one project, priced per GPU-minute and shared with nothing else. Two generations are live:

- **v2 (default): dedicated model inference (DMI)**. Splits an endpoint from the deployment that runs the model, letting one endpoint host several deployments and shift traffic between them. Adds traffic splits, A/B tests, shadow experiments, metric-gated rollouts, and CLI-first management under `tg beta`.
- **v1 (legacy, supported through end of 2026)**. One model per endpoint. Managed by the top-level `together endpoints` CLI and `client.endpoints.*` SDK. Kept alive for existing endpoints; new deployments should target v2.

Typical fits:

- Production inference with stable latency and no shared-fleet rate limits
- Fine-tuned or uploaded custom model hosting (including LoRA adapters via v2 uploads)
- Autoscaled model APIs where per-GPU-minute economics beat per-token serverless
- Shipping a candidate deployment behind an A/B test, shadow experiment, or gated rollout

## When This Skill Wins

- The user needs always-on or single-tenant hosting.
- The model is supported for dedicated deployment (or is a fine-tune of a supported base).
- Hardware, autoscaling metric, or replica bounds need explicit control.
- The workflow includes safe rollouts, live A/B comparison, or shadow-traffic evaluation.

## Hand Off To Another Skill

- Use `together-chat-completions` for serverless chat inference.
- Use `together-dedicated-containers` for custom runtimes or nonstandard inference pipelines.
- Use `together-gpu-clusters` for raw infrastructure or cluster orchestration.
- For production **stock-model** workloads that need a defined SLA (committed throughput and reliability) without managing hardware, point users to Together's [provisioned throughput](https://docs.together.ai/docs/inference/provisioned-throughput) tier (reserved PTU capacity, one-month minimum, contact sales). Use dedicated endpoints instead when the user needs to serve a fine-tuned or uploaded model, or wants direct control over hardware, latency, and throughput.

## Quick Routing

- **Deploy a supported model on v2 (one-shot)**
  - Use `tg beta endpoints deploy <model> --endpoint <name>` (creates endpoint + deployment + traffic split).
  - Read [references/api-reference.md](references/api-reference.md).
- **Manage v2 endpoints, deployments, and configs individually**
  - Start with [scripts/deploy_v2.sh](scripts/deploy_v2.sh).
  - Read [references/api-reference.md](references/api-reference.md).
- **Upload a fine-tuned model or LoRA adapter (v2)**
  - Use `tg beta models create` then `tg beta models upload` or `tg beta models remote-uploads create`.
  - Read [references/models-and-configs.md](references/models-and-configs.md).
- **Split traffic, run an A/B test, shadow experiment, or gated rollout (v2 only)**
  - Read [references/traffic-routing.md](references/traffic-routing.md).
- **Manage a v1 endpoint (legacy)**
  - Start with [scripts/manage_endpoint.py](scripts/manage_endpoint.py) or [scripts/manage_endpoint.ts](scripts/manage_endpoint.ts).
  - Read the v1 API section at the end of [references/api-reference.md](references/api-reference.md).
- **Hardware and sizing choices**
  - Read [references/hardware-options.md](references/hardware-options.md).

## Workflow (v2)

1. Confirm the task needs dedicated hosting rather than serverless or containers.
2. Pick a supported model (or upload one), and select a deployment profile (config).
3. Run `tg beta endpoints deploy <model>` to create the endpoint, attach a deployment, and route all traffic in one step. Set `--min-replicas` and `--max-replicas` for the autoscaling policy.
4. Poll deployment status until it reaches `DEPLOYMENT_STATE_READY`, then send inference to `https://api-inference.together.ai/v1` with `model = "<project_slug>/<endpoint_name>"`.
5. Delete or scale to zero when the workload is done. `tg beta endpoints rm <id> --force` smart-deletes endpoint, deployment, A/B, or shadow resources by ID prefix.

## High-Signal Rules

- **v2 CLI requires Together CLI 2.24.0+**. Install with `uv tool install "together[cli]"` (or `pip install together`). Every v2 management command lives under `tg beta`.
- **v2 SDK surface (`client.beta.endpoints.*`, `client.beta.models.*`) is still being published**. Prefer the CLI or raw HTTP for v2 automation until the SDK stabilizes; the v1 SDK (`client.endpoints.*`) continues to work only against v1 endpoints.
- **Project scope matters**. `tg beta` and the v2 management API read the project from `TOGETHER_PROJECT_ID` or the `--project` flag; without either, the CLI falls back to the project associated with your API key and prompts for confirmation in interactive shells.
- **Model eligibility and instance-type headroom gate every deployment**. Check them early with `tg beta models public --product DEDICATED` and by reading the `regions[].headroom` field on `/v2/public/inference-instance-types`.
- **A ready deployment doesn't serve traffic on its own**. In v2 a deployment only receives requests once it's in the endpoint's traffic split with a non-zero weight. `tg beta endpoints deploy` handles this for the first deployment; add subsequent ones with `tg beta endpoints update <dep_id> --traffic-weight <n>`.
- **Endpoint (`ep_...`) is the URL; deployment (`dep_...`) runs the model**. The management API takes IDs; the inference `model` parameter is the endpoint string `"<project_slug>/<endpoint_name>"`.
- **Stopping a deployment means both replica bounds to `0`**. `min:0` requires `max:0`. Scaled-to-zero deployments don't restart on requests; raise both bounds to `1` or more to bring them back (paying a cold start).
- **Autoscaling metric target units differ**. Latency metrics (`ttft`, `decoding_speed`, `e2e_latency`) are milliseconds. Percentages (`gpu_utilization`, `token_utilization`, `cache_hit_rate`) are 0–100. Averages (`inflight_requests`, `throughput_per_replica`) are per-replica. Streaming-only metrics require `"stream": true` on requests.
- **Uploads must be fine-tuned variants of a supported base architecture**. `baseModelId` (a `ml_...` model ID) is required on `tg beta models create`; the architecture `arch_...` ID is not accepted.
- **Rollout metric gates are canary-only** and require live traffic on the target. Blue-green and rolling strategies reject a `metrics` block.
- **Prompt caching is on by default** on dedicated model inference — no headers, no toggles.

## Resource Map

- **v2 API reference and CLI commands**: [references/api-reference.md](references/api-reference.md)
- **Traffic routing (splits, A/B, shadow, rollouts)**: [references/traffic-routing.md](references/traffic-routing.md)
- **Models, configs, and deployment profiles**: [references/models-and-configs.md](references/models-and-configs.md)
- **Dedicated model list**: [references/dedicated-models.md](references/dedicated-models.md)
- **Hardware, instance types, and pricing**: [references/hardware-options.md](references/hardware-options.md)
- **v2 CLI walkthrough (deploy, scale, split, tear down)**: [scripts/deploy_v2.sh](scripts/deploy_v2.sh)
- **v1 Python endpoint lifecycle (legacy)**: [scripts/manage_endpoint.py](scripts/manage_endpoint.py)
- **v1 TypeScript endpoint lifecycle (legacy)**: [scripts/manage_endpoint.ts](scripts/manage_endpoint.ts)
- **v1 fine-tuned deployment (legacy)**: [scripts/deploy_finetuned.py](scripts/deploy_finetuned.py)
- **v1 custom model upload and deployment (legacy)**: [scripts/upload_custom_model.py](scripts/upload_custom_model.py)

## Official Docs

- [Dedicated model inference (v2 overview)](https://docs.together.ai/docs/dedicated-endpoints/overview)
- [Concepts (endpoints, deployments, configs, profiles)](https://docs.together.ai/docs/dedicated-endpoints/concepts)
- [Migrate from v1](https://docs.together.ai/docs/dedicated-endpoints/migrate-from-v1)
- [Quickstart](https://docs.together.ai/docs/dedicated-endpoints/quickstart)
- [Manage deployments](https://docs.together.ai/docs/dedicated-endpoints/manage)
- [Configure autoscaling](https://docs.together.ai/docs/dedicated-endpoints/scaling)
- [Route traffic](https://docs.together.ai/docs/dedicated-endpoints/route-traffic)
- [A/B tests](https://docs.together.ai/docs/dedicated-endpoints/ab-tests)
- [Shadow experiments](https://docs.together.ai/docs/dedicated-endpoints/shadow-experiments)
- [Rollouts](https://docs.together.ai/docs/dedicated-endpoints/rollouts)
- [Upload a fine-tuned model](https://docs.together.ai/docs/dedicated-endpoints/custom-models)
- [Upload a LoRA adapter](https://docs.together.ai/docs/dedicated-endpoints/adapter)
- [Pricing](https://docs.together.ai/docs/dedicated-endpoints/pricing)
- [v1 (legacy) overview](https://docs.together.ai/docs/dedicated-endpoints/v1/overview)
