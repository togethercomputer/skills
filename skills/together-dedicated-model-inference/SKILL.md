---
name: together-dedicated-model-inference
description: "Deploy and operate models on dedicated GPUs with Together AI's Dedicated Model Inference (DMI, the v2 dedicated endpoints API): beta endpoints, deployments, hardware configs, autoscaling with auto-shutdown, traffic splitting, canary/blue-green/rolling rollouts, A/B tests, shadow experiments, and custom model or LoRA adapter uploads. Reach for it whenever the user mentions together beta endpoints or tg beta commands, client.beta.endpoints, DMI resources like ep_/dep_/cr_/ml_ IDs, or wants production model serving with traffic management on Together AI. Use together-dedicated-endpoints only for the legacy v1 endpoints API."
---

# Together Dedicated Model Inference

## Overview

Dedicated model inference (DMI) serves a model on reserved single-tenant GPUs. It bills per
minute per running replica (by hardware, not by token), has no hard rate limits, and uses the
same inference API as serverless models.

The resource model has six parts: **Project → Model → Config → Endpoint → Deployment → Replica**.

- **Endpoint** — stable inference name; routes traffic across its deployments by weight.
- **Deployment** — binds one model + one config to an endpoint with an autoscaling policy;
  runs the replicas.
- **Config** — immutable published revision describing how the model runs (engine, GPU type
  and count, optimization profile). The model determines the available configs.
- **Replica** — one model instance on its own dedicated hardware.

Inference goes to `https://api-inference.together.ai/v1` with the endpoint's **qualified name**
(`<project_slug>/<endpoint_name>`) as the `model` parameter. Management goes through the
Together CLI (`tg beta ...` — install with `uv tool install "together[cli]"`; `tg` and
`together` are interchangeable), the `client.beta.*` SDK namespaces, or the `/v2` REST API at
`https://api.together.ai`.

## When This Skill Wins

- Deploying a model (public, fine-tuned, or uploaded) on dedicated GPUs via the v2 API
- Anything involving `tg beta endpoints` / `tg beta models` (a.k.a. `together beta ...`) CLI commands
- Anything involving `client.beta.endpoints` / `client.beta.models` SDK namespaces
- Traffic management: splits, rollouts (canary/blue-green/rolling), A/B tests, shadow experiments
- Autoscaling, scale-to-zero/auto-shutdown, deployment lifecycle, monitoring and events
- Uploading custom model weights or LoRA adapters for dedicated serving

## Hand Off To Another Skill

- Use `together-dedicated-endpoints` for the **legacy v1 API** (`client.endpoints.create` with
  `model=` + `hardware=`, hardware IDs like `1x_nvidia_h100_80gb_sxm`, `together endpoints`
  CLI without `beta`). v1 stays supported through end of 2026; new work should target v2.
- Use `together-chat-completions` for serverless inference and request-shaping questions
  (the request shape is identical once the endpoint is up).
- Use `together-fine-tuning` for training the model you'll deploy here.
- Use `together-dedicated-containers` for custom Docker runtimes (Sprocket/Jig).
- Use `together-gpu-clusters` for raw multi-node compute.

## Quick Routing

- **Deploy a model end to end**
  - Start with [scripts/deploy_model.py](scripts/deploy_model.py)
  - Read [references/cli-reference.md](references/cli-reference.md) for the one-command CLI path
- **Endpoint/deployment lifecycle from the SDK or API** (create, poll, scale, stop, delete, list filters)
  - Read [references/api-reference.md](references/api-reference.md)
- **Split traffic, rollouts, A/B tests, shadow experiments**
  - Read [references/traffic-routing.md](references/traffic-routing.md)
  - Start with [scripts/rollout_new_version.py](scripts/rollout_new_version.py) for rollouts
- **Choose a model or config, pricing, upload custom weights or LoRA adapters**
  - Read [references/models-and-configs.md](references/models-and-configs.md)
  - Start with [scripts/upload_custom_model.py](scripts/upload_custom_model.py)
- **Autoscaling and monitoring**
  - Read [references/api-reference.md](references/api-reference.md) (Autoscaling, Monitoring sections)

## Workflow

1. Pick a model: `tg beta models public` (or upload custom weights first).
2. Optionally pick a config: `tg beta models configs <model_id>` (the CLI's `deploy`
   auto-picks when there's exactly one).
3. Deploy: `tg beta endpoints deploy <model_id> --endpoint <name>` — creates the
   endpoint, attaches a deployment, and routes 100% of traffic in one step.
4. Poll until `status.state` is `DEPLOYMENT_STATE_READY` (re-run `tg beta endpoints get <ep>`).
5. Send requests to `https://api-inference.together.ai/v1` with the qualified name as `model`.
6. Scale or reconfigure with `tg beta endpoints update <dep_id>`; split traffic, roll out new
   versions, or experiment as needed.
7. Clean up: `tg beta endpoints update <dep_id> --min-replicas 0 --max-replicas 0` to stop
   billing, or `tg beta endpoints rm <id>` to delete.

## High-Signal Rules

- **Billing runs while replicas run.** Per minute, per replica, by hardware. Always scale to
  zero (`min_replicas: 0, max_replicas: 0`) or delete when the user is done, and suggest
  `--inactive-timeout` (minutes; auto-stop) for dev workloads.
- **A `READY` deployment serves nothing until it's in the endpoint's traffic split.** The CLI's
  `deploy` routes automatically; SDK flows must call `endpoints.update(traffic_split=[...])`.
  A `routing_error`/503 on a READY deployment almost always means a missing/zero weight.
- **Management IDs vs inference name.** Management calls take IDs (`ep_`, `dep_`, `cr_`, `ml_`,
  `rol_`, `abx_`, `exp_`); inference takes the qualified name `<project_slug>/<endpoint_name>`.
- **The SDK requires `project_id` on every method** — derive it with `client.whoami().project_id`.
  The SDK also takes models/configs as resource names (`projects/{p}/models/{ml}`,
  `projects/{p}/configs/{cr}`), while the CLI takes bare IDs. Use the config's own `projectId`
  (often a platform project) when building its resource name.
- **Traffic weights are relative capacity, not percentages.** Share = weight × ready replicas.
  Prefer shifting traffic by changing replica counts; keep weights stable.
- **Scale-to-zero is all-or-nothing:** `min_replicas: 0` with a positive `max_replicas` is
  rejected. `0/0` stops; on a running deployment the floor is otherwise `1`.
- **Metric names come in two disjoint catalogs.** Autoscaling uses `gpu_utilization`,
  `inflight_requests`, `ttft`, etc.; rollout gates use `serving_latency`, `router_error_rate`,
  etc. The sets are not interchangeable — a name from the wrong catalog is rejected. Charts
  live in the dashboard (`https://api.together.ai/endpoints`); there's no metrics query API.
- **Deletion order matters:** stop the deployment (wait for `STOPPED`), remove it from the
  traffic split, delete it, then delete the endpoint. The CLI's `rm` smart-deletes by ID
  prefix and auto-detaches from the split; `--force` deletes an endpoint's deployments too.
  But **neither `rm` nor `--force` stops a running deployment** — a `READY` deployment must
  already be scaled to `0/0` and `STOPPED`, or `rm` fails with `deployment must be stopped or
  failed before deletion (current state: ready)`. Scale down and wait for `STOPPED` first.
- **To see which deployment/replica served a request, read the inference response headers.**
  The response *body*'s `model` field only echoes the endpoint's qualified name — identical for
  every deployment. The routing headers distinguish them: `x-cluster` is the per-deployment
  cluster ID and `worker_url` (inside the `x-i-router-log-event` header) is the replica pod.
  This is the only way to verify a split, rollout, or A/B empirically. See
  [traffic-routing.md](references/traffic-routing.md) (Observing routing).
- **Rollouts are the safe way to replace a deployment on live traffic** — create the target
  stopped (`0/0`), then `tg beta endpoints rollout <target> --from <source> --canary`.
  Metric gates are canary-only and need live traffic to evaluate.
- The `client.beta.*` SDK surface and `together beta` CLI are **beta**: pin a current SDK
  release (`uv pip install --upgrade together`) and expect the surface to evolve.

## Resource Map

- **SDK/API lifecycle reference**: [references/api-reference.md](references/api-reference.md)
- **CLI reference**: [references/cli-reference.md](references/cli-reference.md)
- **Traffic routing guide**: [references/traffic-routing.md](references/traffic-routing.md)
- **Models, configs, pricing, uploads**: [references/models-and-configs.md](references/models-and-configs.md)
- **Deploy workflow script**: [scripts/deploy_model.py](scripts/deploy_model.py)
- **Rollout workflow script**: [scripts/rollout_new_version.py](scripts/rollout_new_version.py)
- **Custom model upload script**: [scripts/upload_custom_model.py](scripts/upload_custom_model.py)

## Official Docs

- [Dedicated Model Inference overview](https://docs.together.ai/docs/dedicated-endpoints/overview)
- [Quickstart](https://docs.together.ai/docs/dedicated-endpoints/quickstart)
- [Concepts](https://docs.together.ai/docs/dedicated-endpoints/concepts)
- [CLI reference: beta endpoints](https://docs.together.ai/reference/cli/endpoints-beta)
- [CLI reference: beta models](https://docs.together.ai/reference/cli/models-beta)
- [Migrate from v1](https://docs.together.ai/docs/dedicated-endpoints/migrate-from-v1)
