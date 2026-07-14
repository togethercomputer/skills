# Dedicated Model Inference — Traffic Routing

How an endpoint decides which deployment serves each request, and the four tools for moving
traffic: weighted splits, rollouts, A/B tests, and shadow experiments.

## Contents

- [How routing works](#how-routing-works)
- [Stickiness](#stickiness)
- [Observing routing](#observing-routing)
- [Traffic splits (weights)](#traffic-splits-weights)
- [Rollouts](#rollouts)
  - [Strategies](#strategies)
  - [Create and start](#create-and-start)
  - [Metric gates (canary only)](#metric-gates-canary-only)
  - [Lifecycle controls](#lifecycle-controls)
  - [Rollout states](#rollout-states)
  - [Failure categories](#failure-categories)
- [A/B tests](#ab-tests)
- [Shadow experiments](#shadow-experiments)
- [Choosing a strategy](#choosing-a-strategy)

## How routing works

A deployment — even `READY` — receives no traffic until it's routed to. The endpoint resolves
each request through sampling stages:

1. **Traffic split** — sample a candidate in proportion to capacity (weight × ready replicas).
2. **A/B test** — if the candidate is an A/B control, re-sample among control + variants by
   the test percentages.
3. **Rollout** — if the candidate is an active rollout's source, re-sample between source and
   target by the current rollout percentage.
4. **Route** — send to the final deployment.

The A/B stage runs before the rollout stage, so a deployment can be both an A/B control and a
rollout source. Shadow experiments sit outside this path entirely (copies, not routing).

## Stickiness

Routing is deterministic per request: the endpoint derives a **sampling key** and always
routes the same key to the same deployment (while the split is stable). This keeps prompt
caches warm across a conversation. Key precedence:

1. `prompt_cache_key` request field, if set.
2. Otherwise the `user` field, if set.
3. Otherwise a key derived from request content.

Set `prompt_cache_key` on requests sharing a prompt prefix (e.g. every turn of one
conversation) to control stickiness. Editing weights, adding/removing deployments, or a
rollout shifting its percentage reassigns some keys.

## Observing routing

To verify empirically how traffic actually lands — for a split, rollout, or A/B test — you
need two things the obvious approach misses:

- **Attribution comes from the response headers, not the body.** The response body's `model`
  field only echoes the endpoint's qualified name, so two deployments serving the same model
  produce byte-identical bodies. The routing headers on the inference response distinguish
  them:
  - `x-cluster` — the per-deployment cluster ID (one stable value per deployment).
  - `x-i-router-log-event` — a JSON array whose `worker_url` field is the replica's pod
    (`http://<pod-ip>:<port>`); distinct pod IPs count distinct replicas within a deployment.

  These header names are operational, not part of the stable inference API contract — confirm
  them against a live probe before relying on them. `x-cluster` values don't equal the `dep_`
  management IDs; map them by briefly routing 100% to one deployment (see propagation note
  below) and recording the `x-cluster` it returns.

- **Vary the sampling key or all your load lands on one deployment.** Because routing is
  sticky (above), sending N identical requests routes all N to the same deployment — you'll
  measure 100/0 no matter what the weights say. Set a unique `prompt_cache_key` (or `user`)
  per request so the sample spreads across the split. A few hundred varied requests gives a
  stable share estimate.

- **Split changes take tens of seconds to propagate.** After `endpoints.update(traffic_split=...)`
  (or a scale change), the router keeps serving the old split briefly — a probe within ~10s
  can still hit the previous target. Allow ~30s before measuring or mapping clusters.

Reading the header from the Python SDK needs `with_raw_response` (the normal `.create` returns
a parsed body with no headers), and `prompt_cache_key` is not a top-level argument — pass it in
`extra_body`. A minimal probe that tallies the split:

```python
from collections import Counter
from together import Together

client = Together(base_url="https://api-inference.together.ai/v1")
counts = Counter()
for i in range(200):  # a few hundred varied requests → stable share estimate
    raw = client.chat.completions.with_raw_response.create(
        model="your-project-slug/my-endpoint",   # qualified name, not ep_ ID
        messages=[{"role": "user", "content": f"ping {i}"}],
        max_tokens=1,
        extra_body={"prompt_cache_key": f"probe-{i}"},   # unique key defeats sticky routing
    )
    counts[raw.headers.get("x-cluster")] += 1
print(counts)   # {control_cluster: ~N*control%, variant_cluster: ~N*variant%}
```

Size N so the smallest arm gets a countable sample — a 5% arm needs a few hundred requests to
clear single digits. Expect binomial noise: a configured 95/5 typically measures ~92–97% on the
control at N=200, not exactly 95%.

## Traffic splits (weights)

Set by updating the endpoint (SDK/API only):

```python
client.beta.endpoints.update(
    "ep_abc123",
    project_id=project_id,
    traffic_split=[
        {"deployment_id": "dep_abc123", "weight": 70},
        {"deployment_id": "dep_def456", "weight": 30},
    ],
)
```

Semantics that trip people up:

- **Weights are relative ratios, not percentages** — `.7`/`.3` equals `700`/`300`.
- **Share = weight × ready replicas.** Weight 1 with two replicas draws the same traffic as
  weight 2 with one replica. Equal weights with unequal replica counts are not a 50/50 split.
- **Prefer shifting traffic by scaling replicas**, keeping weights as a stable capacity
  definition — a deployment's share tracks its ready replicas automatically.
- A deployment gets no traffic if its weight is 0, it's absent from the split, or it has zero
  ready replicas. Scaling to zero takes it out of rotation but its weight is remembered and
  reapplies on scale-up.
- An endpoint with no routable deployment returns `routing_error`.

## Rollouts

A rollout migrates traffic from a **source** deployment to a **target** deployment under the
same endpoint, scaling the target up and draining the source. Use it instead of hand-editing
the split when replacing a deployment on live traffic (new model version, new config/hardware).

Requirements:

- Source and target under the same endpoint.
- The source must be referenced in the traffic split (a rollout only shifts traffic already
  routed to the source; otherwise it runs but moves nothing).
- Create the target **stopped** (`0/0` bounds) so the rollout scales it up from zero.
- One active rollout per endpoint (`409` on create otherwise).

### Strategies

| Strategy | Traffic movement | Use when |
| --- | --- | --- |
| **Canary** | Staged ladder (e.g. 25→50→75→100%), source drains stepwise. | Gradual, metric-gated exposure. Safest for production. |
| **Blue-green** | Single 0→100 cutover once the target is ready. Default. | Atomic flip/rollback; you have capacity to run both at full size briefly. |
| **Rolling** | Replica-by-replica swap (target +1 / source −1 per batch). | Preserve total GPU capacity; no ramp or gate needed. |

Metric gates are **canary-only** — blue-green and rolling have no soak window, and a
`metrics` block is rejected at create time.

### Create and start

CLI (`rollout` creates and starts in one step):

```bash
tg beta endpoints rollout dep_target456 --from dep_source123 --canary --steps 25,50,75,100 --interval 10m
```

SDK (two steps — `create` returns `PENDING`, `start` begins shifting):

```python
rollout = client.beta.endpoints.rollouts.create(
    "ep_abc123",
    project_id=project_id,
    source_deployment_id="dep_source123",
    target_deployment_id="dep_target456",
    blue_green={},                                  # or canary={...} / rolling={...}
    source_cleanup="SOURCE_CLEANUP_POLICY_DRAIN",   # or keep the source scaled up
    final_source_replicas=0,
    final_target_replicas=4,                        # must be >= 1
)
client.beta.endpoints.rollouts.start(rollout.id, project_id=project_id, endpoint_id="ep_abc123")
```

### Metric gates (canary only)

SDK/API only. After each step's soak (`step_interval`), the gate evaluates the rules and
either advances or pauses (`SYSTEM_PAUSED`) for review. Rules are ANDed.

```python
rollout = client.beta.endpoints.rollouts.create(
    "ep_abc123",
    project_id=project_id,
    source_deployment_id="dep_source123",
    target_deployment_id="dep_target456",
    canary={
        "steps": [
            {"traffic": 25, "replicas": 1},
            {"traffic": 50, "replicas": 2},
            {"traffic": 100, "replicas": 4},
        ],
        "step_interval": "390s",
    },
    metrics=[
        {
            "name": "serving_latency",
            "stat": "METRIC_STAT_TYPE_PERCENTILE",
            "percentile": 95,
            "regression_check": {
                "max_regression_percent": 50,
                "direction": "REGRESSION_DIRECTION_HIGHER_IS_WORSE",
            },
            "window": "300s",
        }
    ],
    source_cleanup="SOURCE_CLEANUP_POLICY_DRAIN",
    final_source_replicas=0,
    final_target_replicas=4,
)
```

Gate catalog (`name` must be one of these — anything else, including autoscaling metric
names like `gpu_utilization`, is rejected with `400`):

| `name` | Type | Measures | `stat` |
| --- | --- | --- | --- |
| `serving_latency` | Histogram | Engine request duration — the preferred latency gate. | `AVG` or `PERCENTILE` |
| `router_latency` | Histogram | Router per-attempt latency. Bimodal — gate on `PERCENTILE` ≥ 95, not the mean. | `AVG` or `PERCENTILE` |
| `router_error_rate` | Ratio | Router 5xx / all responses. | `AVG` |
| `inflight_requests` | Gauge | In-flight requests across the target's pods. | `AVG` |

Each rule uses exactly one criterion:

- **`regression_check`** — target vs source; fails when the target is worse by more than
  `max_regression_percent` in the given direction. Relative safety ("no more than 50% slower").
- **`threshold_check`** — target vs an absolute `value` with `THRESHOLD_OPERATOR_GT|GTE|LT|LTE`.
  Latency values are **milliseconds** (`30000` = 30 s). Fixed SLOs ("p95 under 30 s").

Practical rules:

- **Gates need live traffic.** With no requests on the target, the gate reports
  `METRICS_UNAVAILABLE` and the rollout pauses instead of completing. Keep the endpoint under
  load for the whole rollout.
- Use `window: "300s"` for histogram percentiles — shorter windows sit inside ingestion lag
  and hold too few samples, causing spurious pauses.
- Keep `step_interval >= window + ~90s` so metrics settle and new replicas warm past their
  cold start before the gate samples.

### Lifecycle controls

| CLI | SDK | Effect |
| --- | --- | --- |
| `rollout <rol> --pause` | `rollouts.pause` | Hold at the current step (honored at the next step boundary). |
| `rollout <rol> --continue` | `rollouts.resume` | Resume from the current step (re-evaluates a paused step). |
| `rollout <rol> --complete` | `rollouts.promote` | Fast-forward: all traffic to the target. |
| `rollout <rol> --abort` | `rollouts.abort` | Roll traffic back to the source. Terminal; only while active. |

Pass `--reason` / `reason=` on pause and abort to record why. Monitor with
`rollouts.retrieve` (`state`, `current_step`, `current_traffic_percent`, per-step metric
verdicts) or the dashboard's Rollouts tab.

**After `COMPLETED` there is no rollback** — the source is drained. Revert by running a new
rollout in the reverse direction. Delete pending/terminal rollouts via `rollouts.delete`
(SDK/API; `rm` doesn't take `rol_` IDs).

### Rollout states

| State | Meaning |
| --- | --- |
| `PENDING` | Created, not started. |
| `RUNNING` | Actively shifting traffic. |
| `STABILIZING` | Soaking at a step's traffic level. |
| `PAUSED` | Operator-paused; split holds. |
| `SYSTEM_PAUSED` | Platform-paused for review — read `status.condition.category` before acting. |
| `ABORTING` / `ABORTED` | Reverting / reverted to the source (terminal). |
| `COMPLETED` | All traffic on the target (terminal). |

### Failure categories

On `SYSTEM_PAUSED` or terminal failure, `status.condition.category` is typed — trust it over
the free-text message:

| Category | Meaning | Action |
| --- | --- | --- |
| `METRIC_REGRESSION` | Gate found the target worse than the source. | Abort. |
| `HEALTH_REGRESSION` | Health check failed during soak. | Abort. |
| `METRICS_UNAVAILABLE` | Too few samples (usually no live traffic). | Restore load, resume. |
| `TARGET_NOT_READY` | Target didn't become ready in time. | Investigate target, resume or abort. |
| `SOURCE_NOT_DRAINED` | Source replicas didn't drain. | Wait/investigate, resume. |
| `CAPACITY_EXHAUSTED` | Not enough fleet capacity (checked in-rollout, not at create). | Wait; often auto-resumes. |
| `ROUTING_ERROR` | Invalid routing configuration mid-shift. | Fix routing, resume or abort. |
| `DEPENDENCY_OUTAGE` | Platform dependency unreachable. | Wait for recovery, resume. |
| `POLICY_INFEASIBLE` | An autoscaling ceiling dropped below the step's replica floor. | Raise the ceiling or lower the step target, resume. |
| `UNDER_SERVED` | Ready capacity fell below what the split requires. | Restore capacity or reduce the split, resume. |
| `ENTITLEMENT_LAPSED` | Billing/org entitlement lapsed mid-run. | Restore it, resume or abort. |
| `ABORTED_BY_OPERATOR` | Someone aborted. | Terminal; run a new rollout. |
| `INTERNAL` | Unexpected platform error. | Contact support with the rollout ID. |

## A/B tests

An A/B experiment holds a **fixed** split between a control deployment and 1–19 variants,
subdividing only the control's share of traffic. Use it to measure a candidate before
promoting; use a rollout to actually migrate.

Rules:

- 2–20 members, exactly one control; integer percents in [1, 100] summing to 100.
- **Only the control belongs in the endpoint's traffic split.** A variant with a non-zero
  split weight fails the test at start. A control with weight 0 (or absent) means the test
  receives no traffic.
- Updating `members` replaces the whole set — resend every member each time.
- **The CLI `ab` creates the variant deployment, which then cold-starts.** Until it reaches
  `READY` the experiment routes ~100% to the control (the variant can't serve yet), so a probe
  fired immediately after create measures 0% variant. Poll the variant to `READY` before
  measuring.

CLI (creates the variant deployment too — pass the model **name** for a public model, not the
`ml_` ID; the catalog `ml_` ID is owned by a platform project and resolves as
`Model ml_… not found` here):

```bash
tg beta endpoints ab Qwen/Qwen2.5-7B-Instruct --control dep_control123 --percent 5 --name candidate-v1
```

SDK (create the variant deployment first):

```python
experiment = client.beta.endpoints.ab_experiments.create(
    "ep_abc123",
    project_id=project_id,
    name="sampling-tweak-v1",
    members=[
        {"deployment_id": "dep_control123", "role": "AB_EXPERIMENT_MEMBER_ROLE_CONTROL", "percent": 95},
        {"deployment_id": "dep_variant456", "role": "AB_EXPERIMENT_MEMBER_ROLE_VARIANT", "percent": 5},
    ],
)
```

Ramp / add variants / remove variants: `ab_experiments.update` with the full new member set
(SDK/API only). **Pass `update_mask="members"` and the current `etag` (from a fresh
`retrieve`)** — calling `update(members=[...])` alone (the shape the SDK docstring implies is
enough) fails with a bare `400 Invalid Argument` that names no field; adding the mask + etag
fixes it (not isolated which of the two the server requires, so send both):

```python
cur = client.beta.endpoints.ab_experiments.retrieve(
    "abx_abc123", project_id=project_id, endpoint_id="ep_abc123")
client.beta.endpoints.ab_experiments.update(
    "abx_abc123", project_id=project_id, endpoint_id="ep_abc123",
    update_mask="members", etag=cur.etag,
    members=[
        {"deployment_id": "dep_control123", "role": "AB_EXPERIMENT_MEMBER_ROLE_CONTROL", "percent": 80},
        {"deployment_id": "dep_variant456", "role": "AB_EXPERIMENT_MEMBER_ROLE_VARIANT", "percent": 20},
    ],
)
```

Promote a winner with a rollout
(`rollout dep_variant456 --from dep_control123 --blue-green`), then delete the test
(`rm abx_abc123`) — deletion returns all traffic to the regular split immediately (verified:
after `rm`, a varied probe lands 100% on the control's cluster).

## Shadow experiments

A shadow experiment mirrors a sampled fraction of live endpoint traffic to one or more target
deployments. Copies are fire-and-forget: measured, discarded, never returned to callers. Use
it to warm a candidate under real load, stress-test a config, or gather latency data risk-free.

Structure:

- **Source** — the endpoint plus a sampling strategy.
- **Targets** — deployments under the same endpoint, **excluded from the traffic split**
  (weight 0 or unset). Each sampled request is copied to *every* target, so adding targets
  multiplies mirrored volume. Up to 100 inline targets at create.

Sampling strategies (exactly one):

| Strategy | Behavior | Parameters |
| --- | --- | --- |
| `uniform` | Fixed random fraction of all requests. Predictable volume. | `rate` (0.0–1.0) |
| `key_based` | Fixed fraction of distinct key values; same key always same decision. | `rate`, `key` |
| `adaptive_uniform` | Auto-adjusts rate toward a target mirrored QPS. | `target_qps`, optional `window` |
| `adaptive_key_based` | Sticky per-key sampling throttled toward target QPS. | `target_qps`, `key`, optional `window` |

`key` names a top-level request-body field (`body.user`, `body.prompt_cache_key`) — not a
nested path. `target_qps` is an approximate throttle that can run higher and grows as the
endpoint scales; use `uniform` when you need a predictable fraction.

```python
experiment = client.beta.endpoints.shadow_experiments.create(
    "ep_abc123",
    project_id=project_id,
    name="candidate-shadow",          # immutable, unique in project, <= 256 chars
    source={"endpoint": {"sampling": {"uniform": {"rate": 0.1}}}},
    targets=[{"name": "candidate-v2", "target_deployment_id": "dep_target456"}],
)
```

Operating notes:

- Changes (create/update/delete) take effect within ~30–60 seconds.
- **The create response can transiently show `targets: []` and `state: INACTIVE`** — target
  attachment lands a moment after the experiment row. Confirm the mirror is wired up with a
  follow-up `retrieve` (target present, `state: SHADOW_EXPERIMENT_STATE_ACTIVE`), not the create
  response. (When reading targets, retrieve the experiment and read its `.targets` rather than
  calling `targets.list(...)`.)
- **Pause without deleting**: update `source` with `rate: 0`.
- Updates to `source` are etag-guarded: retrieve first, pass `etag` back, handle `409 ABORTED`
  by re-reading. Use `update_mask` (`"source"`, `"description"`).
- Targets are sub-resources (`shadow_experiments.targets.create/list/retrieve/update/delete`).
  Removing the last target makes the experiment `INACTIVE` (mirroring stops, config kept).
- If a target is provisioning/stopped/unhealthy, copies are silently dropped (visible only in
  the target's shadow metrics) — callers are never affected, and mirroring self-recovers.
- Mirrored requests are never re-sampled; shadow loops are prevented automatically.
- Delete the experiment (`rm exp_abc123`) to stop all mirroring (cascade-deletes targets).
  Remove a deployment from experiments before deleting the deployment.

Multiple experiments can run on one endpoint, each sampling independently (volumes add up).
Prefer more targets in one experiment for apples-to-apples comparisons on identical sampled
requests; prefer separate experiments when candidates need different rates, strategies, or
lifetimes.

## Choosing a strategy

| Goal | Tool |
| --- | --- |
| Serve two deployments for redundancy | Traffic split with weights. |
| Replace a deployment on live traffic | Rollout (canary if you want metric gates). |
| Measure a candidate on a fixed slice of user-visible traffic | A/B test. |
| Test a candidate with zero user impact / warm it up | Shadow experiment. |
| Ship the A/B or shadow winner | Rollout from the current deployment to the winner. |
