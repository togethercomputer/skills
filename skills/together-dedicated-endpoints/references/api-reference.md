# Dedicated Model Inference API Reference

Together's dedicated endpoints ship in two generations:

- **v2 (default): dedicated model inference (DMI)**. Endpoint / deployment / config resource model,
  managed under `tg beta` and the `/v2` management API. All new capabilities land here.
- **v1 (legacy)**. Single-model endpoints managed under `tg endpoints` and `client.endpoints.*`.
  Supported through the end of 2026; migrate with [migrate-from-v1](https://docs.together.ai/docs/dedicated-endpoints/migrate-from-v1).

## Contents

- [Resource Model (v2)](#resource-model-v2)
- [Resource IDs](#resource-ids)
- [CLI installation](#cli-installation)
- [Project scope](#project-scope)
- [Endpoints (v2)](#endpoints-v2)
- [Deployments (v2)](#deployments-v2)
- [Deployment states](#deployment-states)
- [Autoscaling (v2)](#autoscaling-v2)
- [Configs and profiles (v2)](#configs-and-profiles-v2)
- [Instance types and capacity](#instance-types-and-capacity)
- [Model uploads (v2)](#model-uploads-v2)
- [LoRA adapter uploads (v2)](#lora-adapter-uploads-v2)
- [Sending inference (v1 and v2)](#sending-inference-v1-and-v2)
- [Prompt caching](#prompt-caching)
- [Observability](#observability)
- [Troubleshooting (v2)](#troubleshooting-v2)
- [Smart delete (v2)](#smart-delete-v2)
- [v1 legacy API](#v1-legacy-api)

## Resource Model (v2)

DMI is built from six components:

- **Project (`proj_...`)**: Organizational boundary. Every API key is scoped to a project, and every
  resource lives inside it.
- **Model (`ml_...`)**: A concrete set of weights. One base architecture can have several weights,
  one per quantization. Together-supported models are visible from every project; uploads and
  fine-tunes belong to your project.
- **Config (`cr_...`)**: A published, immutable serving spec that fixes engine, parallelism,
  hardware, and optimization for one model weight. Often lives in a Together platform project rather
  than yours.
- **Endpoint (`ep_...`)**: A logical grouping of deployments and a stable inference URL. Always
  lives in your project. The endpoint string used for inference is `<project_slug>/<endpoint_name>`.
- **Deployment (`dep_...`)**: Binds a model + config to an endpoint with an autoscaling policy. This
  is what actually runs replicas and serves traffic. One endpoint can host several deployments.
- **Replica**: An instance of the model running on its own hardware. Replicas serve requests in
  parallel and can be autoscaled.

A **deployment profile** is a certified pairing of one model weight with one config, exposed in the
public catalog. When a model has one profile the CLI picks it automatically; when it has several,
pass `--config <cr_...>`.

Request routing: request → endpoint → traffic split → (optional A/B re-sample) → deployment →
replica. See [traffic-routing.md](traffic-routing.md).

## Resource IDs

| Resource | ID format | Notes |
| --- | --- | --- |
| Project | `proj_...` | Retrieve with `tg whoami` or from the [settings page](https://api.together.ai/settings/organization/~current/projects). |
| Model | `ml_...` | Same format for supported models and your uploads. |
| Model revision | `rv_...` | An immutable snapshot of a model. |
| Architecture | `arch_...` | Top-level catalog entry for a model family. |
| Config | `cr_...` | Config revision. Immutable; new revisions get new IDs. |
| Endpoint | `ep_...` | Inference name is `<project_slug>/<endpoint_name>`. |
| Deployment | `dep_...` | Management name is `<project_slug>/<endpoint_name>/<deployment_name>`. |
| A/B experiment | `abx_...` | See [traffic-routing.md](traffic-routing.md#ab-tests-abx_). |
| Shadow experiment | `exp_...` | See [traffic-routing.md](traffic-routing.md#shadow-experiments-exp_). |
| Rollout | `rol_...` | See [traffic-routing.md](traffic-routing.md#rollouts-rol_). |
| Model upload job | `job_...` | Remote-upload job for `tg beta models remote-uploads`. |
| Instance type | `1xnvidia-h100-80gb` (etc.) | Deployable unit of hardware; per-hour price attaches to it. |

## CLI installation

The v2 CLI requires Together CLI `2.24.0` or later:

```bash
uv tool install "together[cli]"           # or: pip install together
tg --version                              # verify 2.24.0+
```

All v2 management commands live under `tg beta`. The Python SDK is imported as `together` (v2 SDK
uses `client.beta.endpoints.*` and `client.beta.models.*` namespaces; some surfaces are still being
published — prefer the CLI or raw HTTP for automation until the SDK stabilizes).

## Project scope

Every v2 call resolves against a single project:

```bash
export TOGETHER_PROJECT_ID=proj_abc123    # explicit
tg beta endpoints ls --project proj_abc123 # per-command override
tg whoami                                  # inspect the resolved project
```

Without either, `tg beta` uses the project associated with your API key and prompts for
confirmation. In CI, agents, or headless environments always set `TOGETHER_PROJECT_ID` or
`--project`.

## Endpoints (v2)

### Deploy in one step

`tg beta endpoints deploy` bundles endpoint creation, deployment attachment, and traffic-split
setup:

```bash
tg beta endpoints deploy google/gemma-4-E4B-it \
  --endpoint my-endpoint \
  --min-replicas 1 --max-replicas 2
```

Positional argument is the model (public name, private name, `ml_...`, or resolved model path).
`--endpoint` accepts either an existing endpoint's name/ID or a new name. When the model has more
than one deployment profile, the command errors and prints available profiles; re-run with
`--config <cr_...>`.

### Deploy flags

| Flag | Required | Description |
| --- | --- | --- |
| `MODEL` | Yes | Positional. Model to deploy. |
| `--endpoint` | Yes | Existing endpoint name/ID or new name. |
| `--config` | No | Config ID (`cr_...`). Required when the model has multiple profiles. |
| `--deployment-name` | No | Defaults to a combo of the endpoint + model names. |
| `--min-replicas` / `--max-replicas` | No | Default `1` each. |
| `--scaling-metric` / `--scaling-target` | No | Set together. See [Autoscaling](#autoscaling-v2). |
| `--scaling-percentile` | No | `p50`, `p90`, `p95` (default), or `p99`. Latency metrics only. |
| `--scale-up-window` / `--scale-down-window` | No | Stabilization windows. Defaults: `0s` up, `5m` down. |
| `--enable-lora` | No | Boot the deployment's multi-LoRA kernel so adapters hot-load after deploy. Cannot be changed on a running deployment. |
| `--project` | No | Override `TOGETHER_PROJECT_ID`. |

### Create an empty endpoint

The CLI has no standalone create-endpoint command. Use the SDK or API:

```python
from together import Together

client = Together()
project_id = client.whoami().project_id

endpoint = client.beta.endpoints.create(
    project_id=project_id,
    name="my-endpoint",
)
print(endpoint)
```

### List and inspect

```bash
tg beta endpoints ls                       # all endpoints in the project
tg beta endpoints ls --limit 100 --after <cursor>
tg beta endpoints ls --org                 # org-scoped
tg beta endpoints ls --public              # public
tg beta endpoints get ep_abc123            # one endpoint, with each deployment's state and replica counts
```

List responses paginate with `next_cursor`; pass it as `--after` on the next request.

### Update

```bash
tg beta endpoints update dep_abc123 --min-replicas 2 --max-replicas 4
tg beta endpoints update dep_abc123 --traffic-weight 70
```

Pass a **deployment ID** (`dep_...`); the CLI resolves the parent endpoint automatically.

## Deployments (v2)

A deployment binds one model + one config to an endpoint and controls autoscaling. Create with
`tg beta endpoints deploy`, or via the SDK/API to add a second deployment to an existing endpoint.

### Create (via API)

```python
deployment = client.beta.endpoints.deployments.create(
    endpoint_id,
    project_id=project_id,
    name="prod",
    model="projects/proj_abc123/models/ml_abc123",
    config="projects/proj_abc123/configs/cr_abc123",
    autoscaling={"min_replicas": 1, "max_replicas": 2},
)
```

List and retrieve responses return a flat deployment object whose `model` and `config` resource
names can be copied straight into a new create request:

```json
{
  "id": "dep_abc123",
  "projectId": "proj_abc123",
  "endpointId": "ep_abc123",
  "name": "your-project-slug/my-endpoint/my-deployment",
  "model": "projects/proj_abc123/models/ml_abc123/revisions/rv_abc",
  "config": "projects/proj_abc123/configs/cr_abc123",
  "autoscaling": {"minReplicas": 1, "maxReplicas": 2},
  "hardware": "1xnvidia-h100-80gb",
  "trafficMode": "TRAFFIC_MODE_LIVE",
  "desiredReplicas": 1,
  "status": {"state": "DEPLOYMENT_STATE_PROVISIONING", "scheduledReplicas": 0, "readyReplicas": 0, "message": "Scheduling replicas"}
}
```

After creating a deployment, [route traffic](traffic-routing.md) to it before it can serve
requests.

### Poll status

```bash
tg beta endpoints get ep_abc123            # each deployment's state + replica counts
```

Retrieve a single deployment from the SDK to read the full `status`:

```python
deployment = client.beta.endpoints.deployments.retrieve(
    "dep_abc123",
    project_id=project_id,
    endpoint_id="ep_abc123",
)
print(deployment.status.state, deployment.status.message)
```

Progress fields:

| Field | Description |
| --- | --- |
| `desiredReplicas` | Target replica count from autoscaling. |
| `status.scheduledReplicas` | Replicas the scheduler has placed on clusters. |
| `status.readyReplicas` | Replicas actively serving traffic. |
| `status.message` | Human-readable stage or cause. |
| `status.state` | See below. |

### Scale, stop, restart

```bash
tg beta endpoints update dep_abc123 --min-replicas 2 --max-replicas 4    # rescale
tg beta endpoints update dep_abc123 --min-replicas 0 --max-replicas 0    # stop (drains, then DEPLOYMENT_STATE_STOPPED)
tg beta endpoints update dep_abc123 --min-replicas 1 --max-replicas 2    # restart
```

Rules:

- `min:0` requires `max:0`. `min:0` with a positive `max` is rejected.
- Setting `min == max` fixes the deployment size and disables autoscaling.
- A stopped deployment doesn't restart on requests. Raise both bounds to `1` or more.

## Deployment states

`status.state` is returned as the fully-qualified enum (for example
`DEPLOYMENT_STATE_READY`). Short names below.

| State | Description |
| --- | --- |
| `PROVISIONING` | Scheduler is placing replicas. |
| `SCALING` | Replicas starting or draining. |
| `READY` | All replicas healthy and serving. Still needs a non-zero traffic weight to receive requests. |
| `DEGRADED` | Below requested capacity or blocked by a transient issue. Usually self-heals. |
| `STOPPING` | Draining after a stop request. Settles to `STOPPED` (or `FAILED` on teardown failure). |
| `STOPPED` | Zero replicas. Not billing, not serving. |
| `FAILED` | Terminal. Read `status.message` for cause. A deployment that never reaches `READY` within six hours after starting is marked `FAILED`. |

## Autoscaling (v2)

Set replica bounds and (optionally) a scaling metric on `deploy` or `update`:

```bash
tg beta endpoints deploy zai-org/GLM-5.2 \
  --endpoint my-glm-endpoint \
  --min-replicas 1 --max-replicas 4 \
  --scaling-metric gpu_utilization \
  --scaling-target 70
```

With bounds but no metric, DMI applies the default: `inflight_requests` with target `8`.

### Scaling metrics

| `--scaling-metric` | Target unit | Notes |
| --- | --- | --- |
| `inflight_requests` | Concurrent requests per replica (average) | Default. Leading indicator. |
| `gpu_utilization` | Percentage (0–100), averaged across replicas | Cost-first. |
| `token_utilization` | Percentage (0–100) | KV-cache utilization. |
| `cache_hit_rate` | Percentage (0–100) | Prompt-cache hit rate. Specialist. |
| `throughput_per_replica` | Tokens/s per replica | Streaming-only. |
| `ttft` | Milliseconds, percentile across deployment | Streaming-only. |
| `decoding_speed` | Milliseconds per output token | Streaming-only. |
| `e2e_latency` | Milliseconds, percentile across deployment | Streaming + non-streaming. |

Rules:

- Streaming-only metrics require `"stream": true` on requests.
- Latency-metric targets are read at the percentile in `--scaling-percentile` (default `p95`).
- Percentages are per-replica averages; averages are per-replica; latencies are fleet-wide percentiles.

### Timing

Each scaling evaluation runs roughly every 60 seconds:

1. Stabilization windows: `--scale-up-window` (default `0s`) and `--scale-down-window` (default `5m`).
2. Rate limits (fleet defaults, not overridable):

   | Direction | Limit | Period |
   | --- | --- | --- |
   | Scale up | Smaller of +100% or +4 replicas | 15s |
   | Scale down | Smaller of −25% or −1 replica | 60s |

3. Clamp to `[minReplicas, maxReplicas]`.

## Configs and profiles (v2)

List configs published for a model with:

```bash
tg beta models configs ml_CbJNwQC2ZqCU2iFT3mrCh
```

Response shape (abbreviated):

```json
{
  "data": [
    {
      "id": "cr_CbeuemXsU8yGStQvBBEgY",
      "referenceModel": "projects/proj_weights/models/ml_CbJ9yCnij7A47b1xkpioB",
      "referenceModelId": "ml_CbJ9yCnij7A47b1xkpioB",
      "projectId": "proj_abc123",
      "selectors": [
        {"key": "accelerator_count", "value": "1"},
        {"key": "accelerator_type",  "value": "nvidia-h100-80gb"},
        {"key": "optimization",      "value": "balanced"},
        {"key": "topology",          "value": "aggregated"}
      ]
    }
  ]
}
```

Selectors:

| Selector | Description | Example |
| --- | --- | --- |
| `accelerator_type` | GPU SKU. | `nvidia-h100-80gb` |
| `accelerator_count` | Replica GPU count. | `1`, `2`, `4`, `8` |
| `optimization` | Serving profile. | `balanced`, `throughput`, `latency` |
| `topology` | Layout across GPUs. | `aggregated` |

Pass the config `id` as a resource name (`projects/{project_id}/configs/{config_revision_id}`) in
the `config` field of a create-deployment request, using the config's `projectId` (often a Together
platform project, not yours). Configs are immutable; new revisions get new `cr_...` IDs. Speculative
decoding and other decoding optimizations are declared inside the config — you cannot toggle them
on the deployment.

## Instance types and capacity

A config's `accelerator_type` + `accelerator_count` maps to a deployable instance type (for example
`1xnvidia-h100-80gb`). Query the public catalog:

```bash
curl -s -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.ai/v2/public/inference-instance-types
```

Each instance type lists `regions`, and each region reports `headroom` — a best-effort hint of how
many more replicas of that type currently fit. `headroom = N` with `RELATION_GTE` means at least N
units are free; the actual number may be higher. Use it to pick a region with capacity before you
deploy. Per-hour pricing lives in [hardware-options.md](hardware-options.md).

## Model uploads (v2)

Uploads must be fine-tuned variants of a supported base architecture. See
[models-and-configs.md](models-and-configs.md) for a fuller walkthrough. Summary:

```bash
# 1. Create the record. Save the returned model id (ml_...).
tg beta models create gemma-4-31b-it \
  --base-model ml_CbJNwQC2ZqCU2iFT3mrCh

# 2a. Upload from your machine.
tg beta models upload ml_abc123 ./path/to/model-dir

# 2b. Or upload from Hugging Face / S3.
tg beta models remote-uploads create ml_abc123 \
  --from https://huggingface.co/your-org/your-repo \
  --token hf_your_token

# 3. Poll the remote-upload job until REMOTE_UPLOAD_STATUS_SUCCEEDED.
tg beta models remote-uploads retrieve job_abc123
tg beta models ls-files ml_abc123           # confirm files landed

# 4. Deploy it like any base model.
tg beta endpoints deploy ml_abc123 \
  --endpoint my-custom-model \
  --config cr_CbzGdmn14t3HYrXXitmKa
```

Create request fields:

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Inference-addressable name (readable, not a Hugging Face repo ID). |
| `base_model_id` | Yes | `baseModelId` (`ml_...`) of the supported base. Not the architecture `arch_...`. |
| `description` | No | Description in the project catalog. |
| `type` | No | `model` (default) or `adapter`. Fixed at create; can't be changed. |

## LoRA adapter uploads (v2)

Same create/upload/deploy flow as full models, with `--type adapter` on create. The adapter must
target a supported base model that Together AI serves for dedicated inference:

```bash
tg beta models create my-stsb-lora \
  --type adapter \
  --base-model ml_CbJNwQC2ZqCU2iFT3mrCh

tg beta models remote-uploads create ml_abc123 \
  --from https://huggingface.co/your-org/your-adapter \
  --token hf_your_token

tg beta endpoints deploy ml_abc123 \
  --endpoint my-adapter \
  --config cr_CbzGdmn14t3HYrXXitmKa
```

Adapter naming tip: strip any org prefix from the repo name (for example use `glue_stsb`, not
`predibase/glue_stsb`) — the server prepends your project slug and doubled slugs can't be renamed.

Adapter files: the source must contain `adapter_config.json` and `adapter_model.safetensors`, at the
root of the S3 archive or the Hugging Face repo. Presigned S3 URLs must have at least 100 minutes of
validity.

## Sending inference (v1 and v2)

Dedicated model inference is served at `https://api-inference.together.ai`. There is no CLI for
inference; use the SDK or curl and point the base URL at that host. Pass the endpoint string
(`<project_slug>/<endpoint_name>`) as `model`:

```python
from together import Together

client = Together(base_url="https://api-inference.together.ai/v1")

response = client.chat.completions.create(
    model="your-project-slug/my-endpoint",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=512,
)
print(response.choices[0].message.content)
```

```bash
curl -s -X POST https://api-inference.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-project-slug/my-endpoint",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 512
  }'
```

Everything the underlying model supports — function calling, structured outputs, streaming, vision —
works the same on DMI as on serverless.

## Prompt caching

Prompt caching is enabled by default on dedicated model inference. There is no header, parameter,
or account toggle. Requests that share a prompt prefix and route to the same replica reuse the
cached prefix.

To keep cache hits from scattering across replicas, set `prompt_cache_key` on requests that share a
prefix. The endpoint uses `prompt_cache_key` first, then `user`, then a content-derived key to pin
requests to the same deployment.

## Observability

Every endpoint exposes:

- **Analytics dashboard** at [api.together.ai/endpoints](https://api.together.ai/endpoints) with
  per-endpoint latency, throughput, replica count, and utilization.
- **Events feed** merging endpoint- and deployment-scoped events. List via
  `client.beta.endpoints.list_events(endpoint_id, project_id=..., limit=50)`. Filters:
  `types`, `min_level`, `source_kinds`, `since`, `until`, `subject_id`, `deployment_ids`, `after`.
  `limit` defaults to 50, max 500.
- **Prometheus-compatible metrics endpoint (beta)** at
  `GET https://o11y-de2-metrics.cloud.together.ai/organizations/{org_id}/metrics`. Authenticate with
  your API key as a bearer token. Grouped by edge / router / worker; histograms exposed as
  `_bucket`, `_sum`, `_count`. See the [monitoring docs](https://docs.together.ai/docs/dedicated-endpoints/monitoring)
  for the full metric list.

## Troubleshooting (v2)

- **`endpoint_not_configured` (HTTP 400) though the deployment is `READY`** — Deployment isn't in
  the endpoint's traffic split (or has weight `0`). Set a non-zero weight with
  `tg beta endpoints update <dep_id> --traffic-weight <n>`.
- **`DEGRADED` with `Cannot place replicas: insufficient GPU capacity`** — Fleet is constrained.
  Compare `status.scheduledReplicas` to `desiredReplicas`. Ask for fewer replicas or a smaller
  config.
- **`DEGRADED` with `Startup stalled` or `Not ready`** — A placed replica is still booting or hit a
  startup failure. Read the detail in `status.message`.
- **`FAILED` with `Timed out waiting for readiness`** — No replica provisioned within six hours.
  Restart to begin a fresh budget.
- **Deploy fails with `the model has no revisions to deploy`** — Model record exists but has no
  uploaded weights yet.
- **Deployment delete fails with `the deployment is referenced by an endpoint's traffic split and
  cannot be deleted`** — Drop the traffic weight to `0` first, or use `tg beta endpoints rm dep_...`
  which auto-detaches.
- **Model delete fails with `the model is referenced by a live deployment`** — Stop the deployment,
  wait for `STOPPED`, delete the deployment, then delete the model.

## Smart delete (v2)

`tg beta endpoints rm` resolves the resource by ID prefix and does the right thing:

| ID prefix | Effect |
| --- | --- |
| `ep_` | Deletes the endpoint (must have no deployments unless `--force`). |
| `dep_` | Auto-detaches from the traffic split and any experiments, then deletes the deployment (must be stopped). |
| `abx_` | Deletes an A/B experiment. Returns traffic to the control. |
| `exp_` | Deletes a shadow experiment. Cascade-deletes its targets. |

Rollout IDs (`rol_...`) are not accepted by `rm`; use the SDK's `rollouts.delete`.

Teardown order for a full endpoint:

1. Scale each deployment to `0/0`. Wait for `DEPLOYMENT_STATE_STOPPED`.
2. `tg beta endpoints rm dep_...` for each deployment (or drop traffic weight to `0` if using the API).
3. `tg beta endpoints rm ep_...`.

Pass `--force` to `rm ep_...` to delete an endpoint that still has deployments.

## v1 legacy API

v1 remains available for existing endpoints and is supported through the end of 2026. New endpoints
should target v2. The tables below cover the v1 surface.

### v1 endpoint operations

| Method | Path | Description |
| --- | --- | --- |
| `POST /endpoints` | Create endpoint (v1) |
| `GET /endpoints` | List endpoints |
| `GET /endpoints/{id}` | Get endpoint |
| `PATCH /endpoints/{id}` | Update config / scaling / state |
| `DELETE /endpoints/{id}` | Delete endpoint |
| `GET /hardware` | List v1 hardware |
| `POST /models` | Upload custom model (v1) |
| `GET /models` | List v1 models |

Base URL: `https://api.together.xyz/v1`.

### v1 create example

```python
endpoint = client.endpoints.create(
    model="Qwen/Qwen3.5-9B-FP8",
    hardware="1x_nvidia_h100_80gb_sxm",
    display_name="My Endpoint",
    autoscaling={"min_replicas": 1, "max_replicas": 3},
    inactive_timeout=60,  # minutes, 0 or None to disable
)
```

```bash
together endpoints create \
  --model Qwen/Qwen3.5-9B-FP8 \
  --hardware 1x_nvidia_h100_80gb_sxm \
  --display-name "My Endpoint" \
  --min-replicas 1 --max-replicas 3 \
  --wait
```

### v1 request fields

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `model` | string | Yes | — | Model to deploy. |
| `hardware` | string | Yes | — | Hardware config ID (v1 underscore format). |
| `autoscaling` | object | Yes | — | `{min_replicas, max_replicas}`. |
| `display_name` | string | No | — | Human-readable name. |
| `disable_speculative_decoding` | bool | No | `false` | Disable speculative decoding. |
| `state` | string | No | `"STARTED"` | `"STARTED"` or `"STOPPED"`. |
| `inactive_timeout` | int/null | No | 60 | Minutes before auto-stop (0/null disables). |
| `availability_zone` | string | No | — | Preferred zone. |

### v1 endpoint states

| State | Description |
| --- | --- |
| `PENDING` | Waiting for resources. |
| `STARTING` | Initializing. |
| `STARTED` | Running, accepting requests. |
| `STOPPING` | Shutting down. |
| `STOPPED` | Not running. |
| `ERROR` | Failed. |

### v1 start / stop / delete

```python
client.endpoints.update("endpoint-abc123", state="STARTED")
client.endpoints.update("endpoint-abc123", state="STOPPED")
client.endpoints.delete("endpoint-abc123")
```

```bash
together endpoints start   <ID>
together endpoints stop    <ID>
together endpoints delete  <ID>
```

### v1 upload

```python
response = client.models.upload(
    model_name="my-custom-model",
    model_source="https://huggingface.co/your-org/your-model",
    hf_token="hf_...",
)
print(response.data.job_id)
```

```bash
together models upload \
  --model-name my-custom-model \
  --model-source https://huggingface.co/your-org/your-model \
  --hf-token $HF_TOKEN
```

Job status:

```bash
curl "https://api.together.xyz/v1/jobs/<job_id>" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### v1 auto-shutdown

v1 endpoints auto-stop after `inactive_timeout` minutes of inactivity (default 60). `0` or `null`
disables. v2 has no automatic idle shutdown; scale to zero (`0/0`) to stop billing.

### v1 → v2 command mapping

| v1 | v2 |
| --- | --- |
| `tg endpoints hardware --model <m>` | `tg beta models configs <model_id>` |
| `tg endpoints create --model <m> --hardware <h>` | `tg beta endpoints deploy <model_id> --endpoint <name> [--config <cr_...>]` |
| `tg endpoints update --min-replicas / --max-replicas <id>` | `tg beta endpoints update <dep_id> --min-replicas <n> --max-replicas <n>` |
| `tg endpoints stop <id>` | `tg beta endpoints update <dep_id> --min-replicas 0 --max-replicas 0` |
| `tg endpoints start <id>` | `tg beta endpoints update <dep_id> --min-replicas 1 --max-replicas <n>` |
| `tg endpoints list` / `retrieve <id>` | `tg beta endpoints ls` / `tg beta endpoints get <ep_...>` |
| `tg endpoints delete <id>` | Scale to `0/0`, then `tg beta endpoints rm <dep_...>` and `tg beta endpoints rm <ep_...>` |

See [migrate-from-v1](https://docs.together.ai/docs/dedicated-endpoints/migrate-from-v1) for a
full walkthrough.
