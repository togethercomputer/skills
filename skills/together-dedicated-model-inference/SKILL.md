---
name: together-dedicated-model-inference
description: "Deploy and operate models on dedicated GPUs with Together AI's Dedicated Model Inference (DMI, the v2 dedicated endpoints API): beta endpoints, deployments, deployment profiles and hardware configs, autoscaling, traffic splitting, A/B tests, shadow experiments, Prometheus metrics, and custom model or LoRA adapter uploads. Reach for it whenever the user mentions together beta endpoints or tg beta commands, client.beta.endpoints, DMI resources like ep_/dep_/cr_/ml_ IDs, or wants production model serving with traffic management on Together AI. Use together-dedicated-endpoints only for the legacy v1 endpoints API."
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

Inference goes to `https://api-inference.together.ai/v1` with the **endpoint string**
(`<project_slug>/<endpoint_name>`) as the `model` parameter. Management goes through the
Together CLI (`tg beta ...` — install with `uv tool install "together[cli]"`; `tg` and
`together` are interchangeable), the `client.beta.*` SDK namespaces, or the `/v2` REST API at
`https://api.together.ai`.

## When This Skill Wins

- Deploying a model (public, fine-tuned, or uploaded) on dedicated GPUs via the v2 API
- Anything involving `tg beta endpoints` / `tg beta models` (a.k.a. `together beta ...`) CLI commands
- Anything involving `client.beta.endpoints` / `client.beta.models` SDK namespaces
- Traffic management: splits, A/B tests, shadow experiments
- Autoscaling, scale-to-zero, deployment lifecycle, monitoring (dashboards, events, Prometheus scrape)
- Uploading custom model weights or LoRA adapters for dedicated serving

## Hand Off To Another Skill

- Use `together-dedicated-endpoints` for the **legacy v1 API** (`client.endpoints.create` with
  `model=` + `hardware=`, hardware IDs like `1x_nvidia_h100_80gb_sxm`, `together endpoints`
  CLI without `beta`). **v1 create and restart are now disabled**: `POST /v1/endpoints`,
  `client.endpoints.create(...)`, and `tg endpoints create` return
  `endpoints_v1_create_access_disabled` (HTTP 403), and a stopped/paused v1 endpoint can't be
  restarted. Already-running v1 endpoints keep serving until further notice; anything new —
  and any redeploy of a stopped v1 endpoint — goes through v2 (this skill).
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
- **Split traffic, A/B tests, shadow experiments**
  - Read [references/traffic-routing.md](references/traffic-routing.md)
- **Choose a model or config, pricing, upload custom weights or LoRA adapters**
  - Read [references/models-and-configs.md](references/models-and-configs.md)
  - Start with [scripts/upload_custom_model.py](scripts/upload_custom_model.py)
- **Autoscaling and monitoring**
  - Read [references/api-reference.md](references/api-reference.md) (Autoscaling, Monitoring sections)

## Workflow

1. Pick a model: `tg beta models public` (or upload custom weights first).
2. Pick a config/precision: read the model's `deploymentProfiles` (they carry `quantization`
   like `BF16`/`FP8`, `gpuCount`, and the exact `model`+`config` resource names). `tg beta
   models configs <id>` is often empty for catalog architectures — see
   [models-and-configs.md](references/models-and-configs.md). `deploy` auto-picks only when the
   model has a single profile.
3. Deploy: `tg beta endpoints deploy <model> --endpoint <name>` — creates the
   endpoint, attaches a deployment, and routes 100% of traffic in one step. For a public
   catalog model with one profile, pass its **name** (`Qwen/Qwen2.5-7B-Instruct`); the catalog
   `ml_`/`arch_` ID is owned by a platform project and won't resolve as a `deploy`/`ab`
   positional in your project. If the model has **multiple profiles** (e.g. BF16 + FP8), a
   bare-name deploy errors — pass the chosen profile's full resolved `model` resource path as
   the positional plus its `--config` (see models-and-configs.md).
4. Poll until `status.state` is `DEPLOYMENT_STATE_READY`. The CLI `get` now accepts an
   endpoint **or** deployment ID: `tg beta endpoints get dep_... --json | jq -r '.status.state'`
   is the scripted polling loop; the SDK equivalent is
   `client.beta.endpoints.deployments.retrieve(dep_id, project_id=..., endpoint_id=...)`.
   First-time provisioning commonly takes up to ~20 minutes.
5. Send requests to `https://api-inference.together.ai/v1` with the endpoint string as `model`.
6. Scale, reconfigure, or set traffic weights with `tg beta endpoints update <dep_id>`
   (`--min/--max-replicas`, `--scaling-metric`/`--scaling-target`, `--traffic-weight`); split traffic or
   experiment as needed.
7. Clean up: `tg beta endpoints update <dep_id> --min-replicas 0 --max-replicas 0` to stop
   billing, or `tg beta endpoints rm <ep_id> --force` to tear everything down (it scales
   deployments to zero itself).

## High-Signal Rules

- **Billing runs while replicas run, and there is no automatic idle shutdown.** Per minute,
  per replica, by hardware. The old `inactive_timeout` auto-stop was removed — always scale to
  zero (`min_replicas: 0, max_replicas: 0`) or delete when the user is done; a forgotten
  deployment bills until someone stops it.
- **A `READY` deployment serves nothing until it's in the endpoint's traffic split.** The CLI's
  `deploy` routes automatically; otherwise set a weight with `tg beta endpoints update <dep_id>
  --traffic-weight N` (upserts one entry) or replace the split via SDK
  `endpoints.update(traffic_split=[...])`. A `routing_error`/503 on a READY deployment almost
  always means a missing/zero weight.
- **Management IDs vs endpoint string.** Management calls take IDs (`ep_`, `dep_`, `cr_`, `ml_`,
  `abx_`, `exp_`); inference takes the endpoint string `<project_slug>/<endpoint_name>`.
- **The SDK requires `project_id` on every method** — derive it with `client.whoami().project_id`.
  The SDK also takes models/configs as resource names (`projects/{p}/models/{ml}`,
  `projects/{p}/configs/{cr}`), while the CLI takes bare IDs. Use the config's own `projectId`
  (often a platform project) when building its resource name.
- **Traffic weights are relative capacity, not percentages.** Share = weight × ready replicas.
  Prefer shifting traffic by changing replica counts; keep weights stable.
- **Scale-to-zero is all-or-nothing:** `min_replicas: 0` with a positive `max_replicas` is
  rejected. `0/0` stops; on a running deployment the floor is otherwise `1`.
- **Autoscaling metric names are their own catalog** (`gpu_utilization`, `inflight_requests`,
  `ttft`, ...) — raw Prometheus series names are rejected in scaling policies. Charts live in
  the dashboard (`https://api.together.ai/endpoints`); raw series can be scraped from the
  org-scoped Prometheus-compatible metrics endpoint (beta — see api-reference.md).
- **Deletion order matters:** stop the deployment (wait for `STOPPED`), delete it, then
  delete the endpoint. The CLI's `rm` smart-deletes by ID prefix and auto-detaches from the
  split. Deleting still requires a stopped deployment, but `rm` now scales down for you:
  `rm dep_...` on a running deployment sets `0/0` and asks you to retry once `STOPPED`, and
  `rm ep_... --force` scales the endpoint's deployments to zero itself as part of teardown.
- **To see which deployment/replica served a request, read the inference response headers.**
  The response *body*'s `model` field only echoes the endpoint string — identical for
  every deployment. The routing headers distinguish them: `x-cluster` is the per-deployment
  cluster ID and `worker_url` (inside the `x-i-router-log-event` header) is the replica pod.
  This is the only way to verify a split or A/B empirically. See
  [traffic-routing.md](references/traffic-routing.md) (Observing routing).
- **To replace a deployment on live traffic**, create the new deployment on the same
  endpoint, wait for `READY`, then shift traffic gradually with `--traffic-weight` (and
  replica counts), watching the dashboard between steps. Take the old deployment out with
  `--traffic-weight 0`, then scale it down and delete it.
- The `client.beta.*` SDK surface and `together beta` CLI are **beta**: pin a current SDK
  release (`uv pip install --upgrade together`) and expect the surface to evolve.

## Resource Map

- **SDK/API lifecycle reference**: [references/api-reference.md](references/api-reference.md)
- **CLI reference**: [references/cli-reference.md](references/cli-reference.md)
- **Traffic routing guide**: [references/traffic-routing.md](references/traffic-routing.md)
- **Models, configs, pricing, uploads**: [references/models-and-configs.md](references/models-and-configs.md)
- **Deploy workflow script**: [scripts/deploy_model.py](scripts/deploy_model.py)
- **Custom model upload script**: [scripts/upload_custom_model.py](scripts/upload_custom_model.py)

## Official Docs

- [Dedicated Model Inference overview](https://docs.together.ai/docs/dedicated-endpoints/overview)
- [Quickstart](https://docs.together.ai/docs/dedicated-endpoints/quickstart)
- [Concepts](https://docs.together.ai/docs/dedicated-endpoints/concepts)
- [CLI reference: beta endpoints](https://docs.together.ai/reference/cli/endpoints-beta)
- [CLI reference: beta models](https://docs.together.ai/reference/cli/models-beta)
- [Migrate from v1](https://docs.together.ai/docs/dedicated-endpoints/migrate-from-v1)
