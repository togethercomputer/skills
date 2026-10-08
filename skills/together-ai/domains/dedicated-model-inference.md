# Together AI: Dedicated Model Inference

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

> **The legacy v1 dedicated endpoints API is retired.** The old flow (`client.endpoints.create`
> with `model=` + `hardware=`, hardware IDs like `1x_nvidia_h100_80gb_sxm`, the `together
> endpoints` CLI *without* `beta`) no longer accepts new endpoints: `POST /v1/endpoints`,
> `client.endpoints.create(...)`, and `tg endpoints create` return
> `endpoints_v1_create_access_disabled` (HTTP 403), and a stopped/paused v1 endpoint can't be
> restarted. Already-running v1 endpoints keep serving until further notice; everything new —
> and any redeploy of a stopped v1 endpoint — uses the v2 flow this guide describes.

Hand-offs: the request shape for inference is the same as serverless, so
`domains/chat-completions.md` covers calling the model; training is `domains/fine-tuning.md`;
your own Docker runtime is `domains/dedicated-containers.md`; raw nodes are `domains/gpu-clusters.md`.

## Workflow

1. Pick a model: `tg beta models public` (or upload custom weights first).
2. Pick a config/precision: read the model's `deploymentProfiles` (they carry `quantization`
   like `BF16`/`FP8`, `gpuCount`, and the exact `model`+`config` resource names). `tg beta
   models configs <id>` is often empty for catalog architectures — see
   [models-and-configs.md](references/dedicated-model-inference/models-and-configs.md). `deploy` auto-picks only when the
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

## Rules

- **Billing runs while replicas run.** Per minute, per replica, by hardware. Idle shutdown is off
  unless you set an inactivity timeout: `--inactive-timeout N` on `deploy` or `update` (30 to
  1440 minutes, `0` disables; `inactive_timeout` in a current Python SDK). It stops the deployment
  after N minutes without requests. Otherwise scale to zero (`min_replicas: 0, max_replicas: 0`)
  or delete when the user is done; a forgotten deployment bills until someone stops it. A
  deployment with an inactivity timeout cannot take part in a rollout.
- **A `READY` deployment serves nothing until it's in the endpoint's traffic split.** The CLI's
  `deploy` routes automatically; otherwise set a weight with `tg beta endpoints update <dep_id>
  --traffic-weight N` (upserts one entry) or replace the split via SDK
  `endpoints.update(traffic_split=[...])`. HTTP 400 `endpoint_not_configured` on a READY
  deployment means it is missing from the split or has weight 0; 400 `endpoint_not_ready` means
  no deployment behind the endpoint is running.
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
  [traffic-routing.md](references/dedicated-model-inference/traffic-routing.md) (Observing routing).
- **To replace a deployment on live traffic**, create the new deployment on the same
  endpoint, wait for `READY`, then shift traffic gradually with `--traffic-weight` (and
  replica counts), watching the dashboard between steps. Take the old deployment out with
  `--traffic-weight 0`, then scale it down and delete it.
- The `client.beta.*` SDK surface and `together beta` CLI are **beta**: pin a current SDK
  release (`uv pip install --upgrade together`) and expect the surface to evolve.

## Finishing and teardown

These come from runs that did the hard part and then failed at the end.

- **Do not finish while anything is pending.** If a deployment is still provisioning, a load test
  or probe is still running, or teardown is unconfirmed, keep polling in the foreground (bounded,
  up to about 25 minutes for provisioning). Do not schedule a later check and end the turn. If you
  must stop, list exactly what is still running and the command that checks it.
- **Teardown is a loop, not one call** (deletion order is in Rules above). A 409 while deleting
  means a deployment is still stopping: poll until `STOPPED`, then retry the delete. You are done
  only when `tg beta endpoints ls` no longer shows the endpoint.
- **Measure, do not assume.** Record wall-clock timestamps when a test starts and ends, and report
  the measured duration, not the planned one. For autoscaling, align latency samples to the
  scale-up and scale-down times in the endpoint's events feed (`tg beta endpoints events EP_ID
  --json`, or api-reference.md, Events Feed),
  not to when you expected scaling to happen. Report an observed split from counted `x-cluster`
  headers, as described in Rules.

## Open next

The workflow and rules above cover a standard deploy, scale, split, and teardown. Open a reference
only for the detail named in its row, and read just that section; each starts with `## Contents`.

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/dedicated-model-inference/deploy_model.py](scripts/dedicated-model-inference/deploy_model.py) | 254 | SDK path: deploy, poll to READY, infer on the dedicated base URL, scale, clean up | scripting the lifecycle in Python |
| [scripts/dedicated-model-inference/upload_custom_model.py](scripts/dedicated-model-inference/upload_custom_model.py) | 145 | upload custom weights or a LoRA adapter, then deploy | serving your own weights |
| [references/dedicated-model-inference/cli-reference.md](references/dedicated-model-inference/cli-reference.md) | 297 | every `tg beta endpoints` and `models` command and flag: deploy, get, update, rm, `ab`, `shadow`; what the CLI cannot do | a CLI flag or subcommand |
| [references/dedicated-model-inference/api-reference.md](references/dedicated-model-inference/api-reference.md) | 478 | SDK and REST for endpoints and deployments: states, autoscaling and scaling metrics, stop/restart, routing, deletion, Prometheus monitoring, Events Feed | SDK calls, metrics, or the events feed |
| [references/dedicated-model-inference/traffic-routing.md](references/dedicated-model-inference/traffic-routing.md) | 290 | how weights route, stickiness, observing routing via headers, gradual cutover, A/B tests, shadow experiments | traffic splits, A/B, or shadow |
| [references/dedicated-model-inference/models-and-configs.md](references/dedicated-model-inference/models-and-configs.md) | 349 | choosing a model, deployment profiles, configs, hardware pricing, model and LoRA upload, upload troubleshooting | picking a profile or uploading weights |

## Docs

- [Dedicated Model Inference overview](https://docs.together.ai/docs/dedicated-endpoints/overview)
- [Quickstart](https://docs.together.ai/docs/dedicated-endpoints/quickstart)
- [Concepts](https://docs.together.ai/docs/dedicated-endpoints/concepts)
- [CLI reference: beta endpoints](https://docs.together.ai/reference/cli/endpoints-beta)
- [CLI reference: beta models](https://docs.together.ai/reference/cli/models-beta)
- [Migrate from v1](https://docs.together.ai/docs/dedicated-endpoints/migrate-from-v1)
