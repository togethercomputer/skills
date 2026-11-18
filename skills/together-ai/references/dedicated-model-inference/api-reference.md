# Dedicated Model Inference — SDK / API Reference

## Contents

- [Basics](#basics)
- [Resource IDs and names](#resource-ids-and-names)
- [Create an Endpoint](#create-an-endpoint)
- [Create a Deployment](#create-a-deployment)
- [Poll Deployment Status](#poll-deployment-status)
- [Deployment States](#deployment-states)
- [Autoscaling](#autoscaling)
- [Scaling Metrics](#scaling-metrics)
- [Stop / Restart](#stop--restart)
- [Route Traffic](#route-traffic)
- [List, Paginate, Filter](#list-paginate-filter)
- [Delete Resources](#delete-resources)
- [Monitoring](#monitoring)
- [Events Feed](#events-feed)
- [Send Inference Requests](#send-inference-requests)
- [Troubleshooting](#troubleshooting)

## Basics

- **Management API**: `https://api.together.ai` under `/v2/` (for example
  `/v2/projects/{project_id}/endpoints/{endpoint_id}/deployments`). Auth is
  `Authorization: Bearer $TOGETHER_API_KEY`.
- **Inference API**: `https://api-inference.together.ai/v1` — same request shapes as serverless.
- **SDK namespaces**: `client.endpoints` (with `.deployments`,
  `.ab_experiments`, `.shadow_experiments`) and `client.models` (with `.configs`,
  `.remote_uploads`). TypeScript uses the camelCase equivalents (`client.endpoints`,
  `abExperiments`, `shadowExperiments`, `remoteUploads`).
- **Every SDK method needs a project ID**: pass `project_id` (TypeScript: `projectId`), or set
  `TOGETHER_PROJECT_ID` or `Together(project_id=...)` once. The CLI infers it from the API key.
  With a project API key, `whoami()` returns it (SDK 3.x nests it under `project`; 2.x had a flat
  `project_id`):

```python
from together import Together

client = Together()
identity = client.whoami()
if identity.type != "project_api_key":
    raise RuntimeError("Use a project API key, or set TOGETHER_PROJECT_ID")
project_id = identity.project.id
```

```typescript
import Together from "together-ai";

const client = new Together();
const identity = await client.whoami();
if (identity.type !== "project_api_key") {
  throw new Error("Use a project API key, or set TOGETHER_PROJECT_ID");
}
const projectId = identity.project.id;
```

- Wire format is camelCase JSON; the Python SDK uses snake_case arguments and attributes.

## Resource IDs and names

| Resource | ID format | Notes |
| --- | --- | --- |
| Project | `proj_...` | Scoped to your API key; get it from `whoami`. |
| Model | `ml_...` | Public base models and uploaded models both use this format. |
| Model revision | `rv_...` | Optional pin; omitting it pins the latest revision at create time. |
| Config | `cr_...` | A config revision. Configs are immutable; each revision has a new ID. |
| Endpoint | `ep_...` | Inference uses the endpoint string `<project_slug>/<endpoint_name>`. |
| Deployment | `dep_...` | Fully qualified as `<project_slug>/<endpoint_name>/<deployment_name>`. |
| A/B experiment | `abx_...` | See [traffic-routing.md](traffic-routing.md). |
| Shadow experiment / target | `exp_...` / `shet_...` | See [traffic-routing.md](traffic-routing.md). |
| Upload job | `job_...` | See [models-and-configs.md](models-and-configs.md). |
| Architecture (catalog) | `arch_...` | Supported-models catalog entries. |

The SDK references models and configs by **resource name**, not bare ID:

- Model: `projects/{project_id}/models/{model_id}[/revisions/{revision_id}]`
- Config: `projects/{project_id}/configs/{config_revision_id}`

`{project_id}` is the **owning** project — for public models and published configs that's
usually a platform project, not yours. List/retrieve responses return these resource names, so
copy them rather than reassembling from IDs.

## Create an Endpoint

An endpoint is a logical grouping of deployments and the stable name your application calls.
The platform prepends your project slug: an endpoint named `my-endpoint` in project slug
`acme` gets the endpoint string `acme/my-endpoint`. Names are immutable.

```python
endpoint = client.endpoints.create(
    project_id=project_id,
    name="my-endpoint",
)
print(endpoint.id, endpoint.name)  # ep_abc123  acme/my-endpoint
```

```typescript
const endpoint = await client.endpoints.create({
  projectId,
  name: 'my-endpoint',
});
```

There is no standalone create-endpoint CLI command — `tg endpoints deploy` creates
the endpoint and its first deployment together.

## Create a Deployment

A deployment binds a model and config to an endpoint with an autoscaling policy.

```python
model = f"projects/{project_id}/models/ml_abc123"          # owning project's ID
config = "projects/proj_platform/configs/cr_abc123"        # use the config's own projectId

deployment = client.endpoints.deployments.create(
    "ep_abc123",
    project_id=project_id,
    name="my-deployment",
    model=model,
    config=config,
    autoscaling={"min_replicas": 1, "max_replicas": 2},
)
```

```shell
curl -X POST "https://api.together.ai/v2/projects/$PROJECT_ID/endpoints/ep_abc123/deployments" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-deployment",
    "model": "projects/'"$PROJECT_ID"'/models/ml_abc123",
    "config": "projects/proj_platform/configs/cr_abc123",
    "autoscaling": {"minReplicas": 1, "maxReplicas": 2}
  }'
```

### Create request fields

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Deployment name within the endpoint. |
| `model` | Yes | Model resource name. Omit `/revisions/{rv}` to pin the latest revision at create time. |
| `config` | Yes | Config-revision resource name. Hardware and engine are fixed for the deployment's life. |
| `autoscaling` | Yes | Replica bounds + optional scaling metrics. See [Autoscaling](#autoscaling). |

The speculator (draft model for speculative decoding) comes from the config and is pinned at
creation — it cannot be set on the deployment.

**A new deployment receives no traffic until it's in the endpoint's traffic split** — see
[Route Traffic](#route-traffic).

## Poll Deployment Status

The CLI's `get` accepts an endpoint **or** deployment ID. `tg endpoints get ep_abc123`
prints the endpoint with each deployment's state and replica counts; `tg endpoints get
dep_abc123` resolves the parent endpoint and prints that deployment's detail —
`tg endpoints get dep_abc123 --json | jq -r '.status.state'` gives a machine-readable
state for polling loops. The same fields via the SDK:

```python
d = client.endpoints.deployments.retrieve(
    "dep_abc123", project_id=project_id, endpoint_id="ep_abc123"
)
print(d.status.state, d.status.message)
```

| Field | Description |
| --- | --- |
| `desiredReplicas` | Target replica count from autoscaling. |
| `status.scheduledReplicas` | Replicas placed on clusters (can trail desired while capacity is found). |
| `status.readyReplicas` | Replicas actively serving. |
| `status.message` | Human-readable explanation of the current stage or cause. |
| `status.state` | See below. |

## Deployment States

The API returns fully qualified enums (`DEPLOYMENT_STATE_READY`); filters must use the full name.

| State | Meaning |
| --- | --- |
| `PROVISIONING` | Scheduler is placing replicas (`Scheduling replicas`). |
| `SCALING` | Replicas starting or draining toward the desired count. |
| `READY` | All replicas healthy and serving. Still needs a traffic-split entry to receive requests. |
| `DEGRADED` | Below requested capacity or blocked by a transient issue; usually self-resolves. |
| `STOPPING` | Draining after a stop; settles to `STOPPED` (or `FAILED` on teardown failure). |
| `STOPPED` | Zero replicas. Not billing, not serving. Does not restart on its own. |
| `FAILED` | Terminal; `status.message` explains why. A deployment that never reaches `READY` within six hours is marked `FAILED`. |

## Autoscaling

Two bounds control replica count:

- `min_replicas` — floor; runs (and bills) continuously. At least `1` on a running deployment.
- `max_replicas` — ceiling; caps maximum cost.

Rules:

- `min == max` — fixed size, autoscaling off.
- `min < max` — autoscaling on. With no metric specified, the platform scales on concurrent
  in-flight requests per replica (default target 8).
- `0 / 0` — stops the deployment. `min 0` with a positive max is **rejected**.

```python
client.endpoints.deployments.update(
    "dep_abc123",
    project_id=project_id,
    endpoint_id="ep_abc123",
    autoscaling={"min_replicas": 1, "max_replicas": 4},
)
```

CLI equivalent: `tg endpoints update dep_abc123 --min-replicas 1 --max-replicas 4`.

Optional windows (settable at deploy or update time via CLI flags): `scale_up_window` (metric must stay
above target this long before adding replicas) and `scale_down_window` (cooldown between
scale-downs). Scale-up reacts fast; scale-down is deliberately slow so bursty traffic doesn't
pay a cold start on every trough. To stop an idle deployment, set `inactive_timeout` (see
[Stop / Restart](#stop--restart)). Autoscaling never takes a running deployment to zero.

New replicas **cold start**: placement → image pull → weight load → engine load → warmup.
Minutes even for small models (image pull on a cold node often dominates — up to several
minutes), longer for large ones. Two things to design around:

- **`desired` reacts far faster than `ready` climbs.** The autoscaler moves `desired` within
  roughly the metric window + `scale_up_window` (tens of seconds), but `readyReplicas` only
  catches up after the full cold start. When measuring "scale-up speed," separate the
  *decision* (`desired` / `status.scheduledReplicas` changing) from *fulfillment*
  (`status.readyReplicas` changing); the `pod.startup_phase_changed` events (see
  [Events Feed](#events-feed)) attribute the wall-clock to each boot phase.
- **Reactive scale-up cannot catch a spike shorter than the cold start.** Keep
  `min_replicas >= 1` to avoid a cold start on the first request, and raise `min_replicas`
  *ahead of* a known burst — a 90-second wave is over before a new replica is ready.

## Scaling Metrics

Each `scaling_metrics` entry sets `name`, `type`, and `target`:

| `name` | `type` | `target` meaning |
| --- | --- | --- |
| `inflight_requests` | `METRIC_TARGET_TYPE_AVERAGE_VALUE` | Concurrent in-flight requests per replica (default metric, target 8). |
| `gpu_utilization` | `METRIC_TARGET_TYPE_UTILIZATION` | GPU compute %, 0–100. |
| `token_utilization` | `METRIC_TARGET_TYPE_UTILIZATION` | KV-cache utilization %, 0–100. |
| `cache_hit_rate` | `METRIC_TARGET_TYPE_UTILIZATION` | Prompt-cache hit rate %, 0–100. |
| `throughput_per_replica` | `METRIC_TARGET_TYPE_AVERAGE_VALUE` | Tokens/sec per replica. |
| `ttft` | `METRIC_TARGET_TYPE_VALUE` | Time to first token, ms. |
| `decoding_speed` | `METRIC_TARGET_TYPE_VALUE` | Time per output token, ms. |
| `e2e_latency` | `METRIC_TARGET_TYPE_VALUE` | End-to-end request latency, ms. |

```python
client.endpoints.deployments.update(
    "dep_abc123",
    project_id=project_id,
    endpoint_id="ep_abc123",
    autoscaling={
        "min_replicas": 1,
        "max_replicas": 4,
        "scaling_metrics": [
            {"name": "gpu_utilization", "type": "METRIC_TARGET_TYPE_UTILIZATION", "target": 70}
        ],
    },
)
```

CLI equivalent — the CLI takes one metric as flat flags (`--scaling-metric` /
`--scaling-target`, plus optional `--scaling-percentile` for latency metrics), not the JSON
array the SDK/API uses:

```bash
tg endpoints update dep_abc123 --min-replicas 1 --max-replicas 4 \
  --scaling-metric gpu_utilization --scaling-target 70
```

Caveats:

- **The default `inflight_requests` target (8) scales on concurrency, not latency.** A
  capable replica can serve well above 8 concurrent requests with no latency degradation, so
  the default fires scale-ups before the replica is actually latency-saturated. If you want
  scaling tied to an SLO rather than raw concurrency, raise the target or switch to a latency
  metric (`e2e_latency` / `ttft`, streaming only for `ttft`).
- `throughput_per_replica`, `ttft`, and `decoding_speed` are recorded **only for streaming
  responses** — scaling on them without `"stream": true` traffic won't work.
- Latency metrics default to p95 over the measurement window; set `"percentile"` to `"p50"`,
  `"p90"`, `"p95"`, or `"p99"` to change it.
- These names are the **autoscaling catalog** — raw Prometheus series names are not valid
  here.

## Stop / Restart

Idle shutdown is off by default: a deployment runs and bills until you stop it, unless you set
`inactive_timeout` on the deployment (`inactiveTimeout` in the REST API, `--inactive-timeout` in
the CLI), which stops it after that many minutes without requests. A deployment with an
inactivity timeout cannot take part in a rollout.

```python
client.endpoints.deployments.update(
    "dep_abc123", project_id=project_id, endpoint_id="ep_abc123",
    update_mask="inactiveTimeout",   # the same mask the CLI sends
    inactive_timeout=30,             # minutes: 0 turns it off, otherwise 30 to 1440
)
```

- **Accepted values are `0` or `30` to `1440`.** Anything else returns HTTP 400
  `inactive_timeout (N minutes) must be within [30, 1440] minutes (0 disables)`. When a task asks
  for less than 30 minutes, set `30`, report that it is the minimum, and verify the shutdown at
  that value.
- **The clock** starts when the deployment first reaches `READY`, resets on every inference
  request, and resets when you change the timeout. The deployment bills for the whole idle
  period.
- **After an idle shutdown** the deployment is `DEPLOYMENT_STATE_STOPPED` and does not restart
  on its own. The timeout stays set.
- HTTP 400 `inactive_timeout is not available for this account` means idle shutdown is not
  enabled for the organization. Tell the user that Together support has to enable it, deploy
  without the timeout, and stop the deployment by hand (`0/0`) when it is no longer needed.

```python
# Stop (drains, then STOPPED; billing stops)
client.endpoints.deployments.update(
    "dep_abc123", project_id=project_id, endpoint_id="ep_abc123",
    autoscaling={"min_replicas": 0, "max_replicas": 0},
)

# Restart (first replica cold-starts)
client.endpoints.deployments.update(
    "dep_abc123", project_id=project_id, endpoint_id="ep_abc123",
    autoscaling={"min_replicas": 1, "max_replicas": 2},
)
```

CLI equivalents: `tg endpoints update dep_abc123 --min-replicas 0 --max-replicas 0`
(stop), `--min-replicas 1 --max-replicas 2` (restart).

A stopped deployment keeps its configuration and traffic-split weight (the weight reapplies
when it scales back up), but never restarts on its own.

## Route Traffic

Traffic is routed by the endpoint's `traffic_split`. The CLI's `deploy` sets it automatically
for the first deployment. To change one deployment's weight, use the CLI's upsert (it resolves
the parent endpoint and preserves the other deployments' weights):

```bash
tg endpoints update dep_abc123 --traffic-weight 30
tg endpoints update dep_abc123 --traffic-weight 0   # out of rotation, no scale-down
```

To replace the whole split at once, update the endpoint from the SDK/API:

```python
client.endpoints.update(
    "ep_abc123",
    project_id=project_id,
    traffic_split=[{"deployment_id": "dep_abc123", "weight": 1}],
)
```

Weights are relative capacity: share = weight × ready replicas. Full semantics, plus gradual
cutovers, A/B tests, and shadow experiments, are in [traffic-routing.md](traffic-routing.md).

## List, Paginate, Filter

```python
client.endpoints.list(project_id=project_id)
client.endpoints.retrieve("ep_abc123", project_id=project_id)
client.endpoints.deployments.list("ep_abc123", project_id=project_id)
```

| Parameter | Description |
| --- | --- |
| `limit` | Max results (max 500, default 50). |
| `after` | Opaque cursor from the previous response's `next_cursor`. |
| `order_by` | `created_at` or `updated_at`, optionally with ` asc` / ` desc`. |
| `filter` | Expression; see below. |

Filter expressions support `=`, `!=`, `<`, `<=`, `>`, `>=`, `AND`, `OR`, `NOT`, double-quoted
strings, and RFC-3339 timestamps. Endpoint lists filter on `created_at` / `updated_at`;
deployment lists also support `state` (fully qualified enum) and `model` (resource name,
matched regardless of revision):

```python
client.endpoints.deployments.list(
    "ep_abc123",
    project_id=project_id,
    filter='state = "DEPLOYMENT_STATE_READY" AND created_at > "2026-01-01T00:00:00Z"',
    order_by="created_at desc",
)
```

Invalid syntax or unknown fields return `400` with `invalid filter expression`.

## Delete Resources

Deletion is permanent, and a deployment must be stopped first. Order:

1. Scale the deployment to `0/0`; wait for `DEPLOYMENT_STATE_STOPPED`.
2. Remove it from the endpoint's traffic split.
3. Delete the deployment.
4. Delete the endpoint once it has no deployments.

```python
# Send the split with this deployment's entry removed (keeping any others), and pass
# update_mask. Without the mask the API does not treat an empty list as a change and
# returns "400 no fields to update".
client.endpoints.update("ep_abc123", project_id=project_id,
                        traffic_split=[{"deployment_id": "dep_other", "weight": 1}],
                        update_mask="trafficSplit")
client.endpoints.deployments.delete("dep_abc123", project_id=project_id, endpoint_id="ep_abc123")
client.endpoints.delete("ep_abc123", project_id=project_id)
```

When the deployment is the endpoint's **only** traffic entry, send `traffic_split=[]` with
`update_mask="trafficSplit"` to clear the split. The CLI's `rm ep_... --force` makes the same
call, and it is the shorter path: it detaches from the split and deletes the deployment and
endpoint together (it smart-deletes by ID prefix; see [cli-reference.md](cli-reference.md)). The CLI now handles
running deployments: `rm ep_... --force` scales the endpoint's deployments to `0/0` itself as
part of teardown, and a bare `rm dep_...` on a running deployment scales it to `0/0` and asks
you to retry once it reaches `STOPPED` (the delete itself still requires a stopped
deployment).

## Monitoring

DMI records latency, throughput, replica-count, and utilization metrics for every endpoint
and deployment — the same series that drive autoscaling. Three surfaces:

- **Analytics dashboard** — `https://api.together.ai/endpoints` shows per-endpoint charts.
  Use it to monitor at a glance and to compare deployments during a cutover or A/B test.
- **Events feed** — the audit trail of lifecycle changes (below).
- **Prometheus-compatible metrics endpoint** (beta) — org-scoped scrape target for your own
  Prometheus/Grafana/Datadog stack, and the source for per-endpoint and per-deployment request
  counts (below).

Note the autoscaling metric names (`gpu_utilization`, `inflight_requests`, ...) are their
own catalog — not interchangeable with the raw Prometheus series below.

### Prometheus-compatible metrics endpoint (beta)

Org-scoped, bearer-authenticated scrape target (beta — host/path may change, and access may
need enabling for your org):

```bash
curl -s -H "Authorization: Bearer $TOGETHER_API_KEY" \
  "https://o11y-de2-metrics.cloud.together.ai/organizations/$ORG_ID/metrics" \
  | grep '^router_inference_requests_rate5m{'
```

`$ORG_ID` is your organization ID (`org_...`): run `tg whoami`, or read `organization.id` from
`GET https://api.together.ai/v3/whoami` (the same response has `project.id`). The response holds
every series for the organization and can be hundreds of megabytes, so filter it with `grep`
as above and never print it whole.

Works with any Prometheus-compatible scraper (set `metrics_path:
/organizations/<ORG_ID>/metrics`, target `o11y-de2-metrics.cloud.together.ai`, bearer
credentials).

Most request, token, and latency metrics end in `_rate5m`. They are precomputed per-second rates
over the last 5 minutes, exposed as gauges, so read or chart them directly and do not wrap them
in `rate()`. Histograms are exposed as `_rate5m_bucket`, `_rate5m_sum`, and `_rate5m_count`.

| Stage | Metrics |
| --- | --- |
| Edge | `edge_inference_requests_rate5m`, `edge_inference_request_duration_ms_rate5m`, `edge_inference_ttft_ms_rate5m`, `edge_inference_inflight_requests` (gauge) |
| Router | `router_inference_requests_rate5m`, `router_inference_request_duration_seconds_rate5m`, `router_inference_ttft_seconds_rate5m`, `router_pre_worker_duration_seconds_rate5m`, `router_inference_inflight_requests` (gauge), `router_token_rate5m`, `router_tokens_per_request_rate5m` |
| Worker | `worker_inference_request_total` (counter), `worker_ttft_seconds_rate5m`, `worker_generation_duration_seconds_rate5m`, `worker_tpot_seconds_rate5m`, `worker_token_rate5m`, `worker_tokens_per_request_rate5m`, `worker_engine_kv_cache_utilization` (gauge, 0–1), `worker_engine_cache_hit_rate` (gauge, 0–1) |

The older names without `_rate5m` (`edge_inference_requests_total`,
`router_inference_requests_total`, `router_token_count`, `worker_token_total`, and the plain
histograms) are deprecated and due for removal. Their values reset when a replica restarts or
scales down, so do not build on them.

Labels include `endpoint_id`/`endpoint_name`, `deployment_id`/`deployment_name`, `replica_id`,
`status_code`, `path`, `is_streaming`, and `token_type`. Not every label is on every metric. The
router request series carry `endpoint_id`, `deployment_id`, `replica_id`, `status_code`, and
`path`.

### Count requests per endpoint or deployment

To turn a `_rate5m` value into a count, multiply it by the 300 seconds it covers. Add up the
`router_inference_requests_rate5m` lines that match a `deployment_id` (or an `endpoint_id`) and
your inference `path`, then multiply by 300 for the requests received in the last 5 minutes. In
Prometheus:

```text
sum by (deployment_id) (router_inference_requests_rate5m{endpoint_id="<ENDPOINT_ID>", path=~".*/chat/completions"}) * 300
```

For a longer period, add up the 5-minute windows:

```text
sum by (endpoint_id) (sum_over_time(router_inference_requests_rate5m{path=~".*/chat/completions"}[24h:5m])) * 300
```

The router series count every request a deployment receives, including the copies mirrored to a
shadow target, which is how you confirm a shadow experiment is mirroring (see
[traffic-routing.md](traffic-routing.md), Confirm mirrored volume). They are split by `path`, so
match your inference path to leave out other APIs and health probes such as `/liveness` and
`/readiness`. Chat requests appear as `/v1/chat/completions` or `/chat/completions`, which is why
the queries above match `path=~".*/chat/completions"`. Each line of the raw response is
`name{labels} value timestamp`, so the rate is the field after the closing brace.

The analytics API (`client.endpoints.analytics`,
`GET /v2/projects/{project_id}/endpoints/{id}/analytics`) returns organization-wide totals today,
the same numbers for every endpoint, with an empty per-deployment breakdown. It cannot give
per-endpoint or per-deployment counts, so use the metrics above for those.

## Events Feed

Each endpoint has an audit feed (newest first) merging endpoint- and deployment-scoped events:
scale-ups, traffic shifts, readiness changes.

```python
events = client.endpoints.list_events("ep_abc123", project_id=project_id, limit=50)
```

Optional filters: `types` (event-type strings), `since` / `until` (time range), `subject_id`
(scope to one subject's audit trail), `deployment_ids` (scope to specific
deployments), `limit` / `after` (max 500, default 50). Events come back newest-first — reverse
them for a chronological timeline.

The feed is the authoritative source for a **cold-start phase breakdown**. Alongside
`deployment.created` and `deployment.status_updated` (which carries each state transition plus
`first_ready_at` / `first_replica_ready_at`), `pod.startup_phase_changed` events trace the
replica boot — typically `PullingImage → Starting → LoadingWeights → StartupComplete` — each
with a `phase_budget`. Diffing consecutive event timestamps attributes wall-clock time to each
phase (image pull vs. engine start vs. weight load vs. warmup), which is finer-grained than
polling `status.state` alone.

## Send Inference Requests

Same shared inference API as serverless — function calling, structured outputs, and streaming
work if the underlying model supports them. Prompt caching is on by default.

```python
from together import Together

client = Together(base_url="https://api-inference.together.ai")   # SDK 3.x: no /v1

response = client.chat.completions.create(
    model="your-project-slug/my-endpoint",   # endpoint string, not ep_ ID
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=30,
)
```

To attribute a response to the deployment/replica that served it (e.g. verifying a split),
read the **response headers**, not the body: `x-cluster` is the per-deployment cluster ID and
`worker_url` (in `x-i-router-log-event`) is the replica pod. The body's `model` field only
echoes the endpoint name. Full method — including varying the sampling key so load spreads
across the split — is in [traffic-routing.md](traffic-routing.md) (Observing routing). To count
what each deployment received without reading headers, including a shadow target, see
[Count requests per endpoint or deployment](#count-requests-per-endpoint-or-deployment).

## Troubleshooting

- **HTTP 400 `endpoint_not_configured` on a `READY` deployment** — the deployment isn't in the
  traffic split with a non-zero weight, or it has zero ready replicas.
- **HTTP 409 `endpoint_not_ready` on an inference request** — no deployment on the endpoint is
  ready to serve yet. Retry with a short backoff. The error can continue briefly after a
  deployment reports `READY`.
- **HTTP 400 `endpoint_not_ready` on an inference request** — every deployment on the endpoint
  is stopped. Restart one (see [Stop / Restart](#stop--restart)).
- **`DEGRADED` with `Cannot place replicas: insufficient GPU capacity`** — hardware for the
  config is constrained. The scheduler keeps retrying; compare `status.scheduledReplicas` to
  `desiredReplicas`. Request fewer replicas or pick a smaller-footprint config.
- **`DEGRADED` with `Startup stalled` / `Not ready`** — a placed replica is booting or hit a
  startup failure; the detail follows the colon in `status.message`.
- **`FAILED` with `Timed out waiting for readiness`** — no replica provisioned within six
  hours. Read the stall cause in `status.message`; restart for a fresh budget.
- **Model not deployable** — not every model is supported; a fine-tune deploys only if its
  base model is supported. See [models-and-configs.md](models-and-configs.md).
- **`400 invalid filter expression`** — check filter field names and quoting.
- **`409` on update/delete** — stale `etag` (shadow experiments and other etag-guarded
  resources). Re-read to get the current etag and retry.
