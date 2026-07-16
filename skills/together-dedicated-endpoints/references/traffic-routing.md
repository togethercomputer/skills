# Traffic routing (v2)

DMI v2 introduces multiple ways to route inference across the deployments behind a single endpoint:
basic traffic splits, A/B experiments, shadow experiments, and metric-gated rollouts. None of these
exist on v1 endpoints.

## Contents

- [How routing works](#how-routing-works)
- [Stickiness](#stickiness)
- [Basic weights](#basic-weights)
- [Split traffic](#split-traffic)
- [A/B tests (`abx_...`)](#ab-tests-abx_)
- [Shadow experiments (`exp_...`)](#shadow-experiments-exp_)
- [Rollouts (`rol_...`)](#rollouts-rol_)
- [Cross-feature rules](#cross-feature-rules)

## How routing works

The endpoint resolves each request through a sequence of sampling decisions:

1. **Traffic split** — Among the deployments in the split, sample a candidate in proportion to
   capacity (weight × ready replicas).
2. **A/B test** — If the candidate is the control of an active A/B experiment, re-sample among
   control + variants by the configured percentages.
3. **Route** — Send the request to a cluster within the resolved deployment.

Shadow experiments sit outside this path: they copy a sampled fraction of live traffic to target
deployments for observation without changing which deployment serves the caller.

## Stickiness

Routing is deterministic per request, not randomly drawn each time. The endpoint derives a
**sampling key** and always routes requests with the same key to the same deployment (as long as
the traffic split is stable). This is how DMI keeps prompt caches warm.

Key precedence:

1. `prompt_cache_key` (recommended: set it explicitly to pin a conversation's turns together).
2. Otherwise `user`.
3. Otherwise a key derived from request content.

Stickiness holds until the traffic split changes (weight edit, deployment added or removed); some
keys reassign when routing changes.

## Basic weights

Every deployment on an endpoint has a weight in the endpoint's traffic split. A weight is a
non-negative, finite ratio — not a percentage — and each deployment's share is proportional to its
weight × ready replicas.

Set with `tg beta endpoints update` passing the **deployment ID**; the CLI resolves the parent
endpoint and preserves the other deployments' weights:

```bash
tg beta endpoints update dep_abc123 --traffic-weight 1     # add / update
tg beta endpoints update dep_def456 --traffic-weight 0     # remove from split entirely
```

`weight = 0` unsets the deployment from the split (the deployment keeps running). A deployment
draws no traffic if its weight is `0`, it's absent from the split, or it has zero ready replicas.
An endpoint with no routable deployment returns HTTP `400 endpoint_not_configured`.

## Split traffic

Split traffic across multiple deployments on one endpoint for high availability, staged migration,
or independent scaling per model version.

```bash
tg beta endpoints update dep_abc123 --traffic-weight 70
tg beta endpoints update dep_def456 --traffic-weight 30
```

Rules:

- Weights are **relative capacity**, not percentages. `70 / 30` is the same as `7 / 3`.
- Two deployments with the same weight but different ready-replica counts do NOT receive equal
  traffic.
- Weights are remembered when a deployment scales to zero and reapply when it scales back up.
- **Shift traffic between deployments by rescaling** (change replica counts) rather than editing
  weights, so the endpoint's declared capacity split stays stable.

## A/B tests (`abx_...`)

An A/B test holds a fixed **control / variant** split under one endpoint for measured comparison on
live traffic. The test subdivides only the control's share of traffic; every other deployment in
the split is unaffected.

### Requirements

- A `READY` control deployment that is receiving traffic (i.e. in the endpoint's traffic split).
- Variants must be **excluded** from the endpoint's traffic split (weight `0` or unset). A variant
  with a non-zero weight causes the test to fail to start.
- Exactly one control and 1–19 variants (up to 20 members total).
- Percentages across all members (including the control) sum to `100`.

### Start (CLI)

The CLI's `ab` command creates the variant deployment for the model you pass and starts the
experiment, assigning `--percent` to the variant and the remainder to the control:

```bash
tg beta endpoints ab ml_CbJNwQC2ZqCU2iFT3mrCh \
  --control dep_control123 \
  --percent 5 \
  --name sampling-tweak-v1
```

Save the returned experiment ID (`abx_...`) and the variant deployment ID (`dep_...`).

### Ramp

Only the SDK/API can change existing members' percentages. `members` is replaced whole; re-list
every member:

```python
client.beta.endpoints.ab_experiments.update(
    "abx_abc123",
    endpoint_id="ep_abc123",
    project_id=project_id,
    members=[
        {"deployment_id": "dep_control123",
         "role": "AB_EXPERIMENT_MEMBER_ROLE_CONTROL", "percent": 90},
        {"deployment_id": "dep_variant456",
         "role": "AB_EXPERIMENT_MEMBER_ROLE_VARIANT", "percent": 10},
    ],
)
```

### Add more variants

Run `ab` again with the same control. Each `ab` call carves the new variant's percentage out of
the control's share and leaves existing variants untouched:

```bash
tg beta endpoints ab ml_Zk7pR2mQ9sT4vU6yB1nD3 \
  --control dep_control123 \
  --percent 10
```

The control's share cannot drop below `1%`.

### Promote and delete

Promote a winning variant by editing the endpoint's traffic split so the winner takes all traffic:

```bash
tg beta endpoints update dep_control123 --traffic-weight 0
tg beta endpoints update dep_variant456 --traffic-weight 1
tg beta endpoints rm abx_abc123          # ends the managed control/variant split
```

Deleting an A/B test immediately returns all traffic to the control (or the promoted variant).
Clean up member deployments in the usual [teardown order](api-reference.md#smart-delete-v2).

## Shadow experiments (`exp_...`)

Shadow experiments mirror a fraction of live endpoint traffic to one or more target deployments for
observation. Targets never return responses to the caller.

Use shadow to warm a new deployment under real load, stress-test a config change, or gather
comparative metrics before you shift real traffic.

### Requirements

- A running endpoint under live traffic.
- One or more candidate deployments to shadow to. Each target must be **excluded** from the
  endpoint's traffic split (weight `0` or unset).

### Sampling strategies

| Strategy | Flags | Behavior |
| --- | --- | --- |
| `uniform` | `--rate 0.0…1.0` | Fixed fraction of all requests, sampled at random. |
| `key_based` | `--rate 0.0…1.0 --key <field>` | Fixed fraction of distinct key values (sticky). |
| `adaptive_uniform` | `--target-qps <N> [--window <s>]` | Auto-tunes uniform rate to approach a target QPS. |
| `adaptive_key_based` | `--target-qps <N> --key <field> [--window <s>]` | Auto-tunes key-based rate to approach a target QPS. |

`--key` names a top-level field in the request body (for example `body.user` or
`body.prompt_cache_key`), not a nested path. Requests missing that field are sampled at random.

`--target-qps` is an approximate throttle, not a hard cap. Actual mirrored volume can exceed the
target as the endpoint scales up. Use `uniform` when you need a predictable fraction.

Setting `--rate 0` mirrors nothing — a way to pause without deleting.

### Create (CLI)

```bash
tg beta endpoints shadow \
  --endpoint ep_abc123 \
  --model ml_CbJNwQC2ZqCU2iFT3mrCh \
  --rate 0.1 \
  --name candidate-v2
```

The CLI creates a fresh shadow deployment from the model and wires it up as a target. Note the
experiment ID (`exp_...`) from the response. `name` is immutable and unique per endpoint.

### Adaptive and key-based examples

```bash
tg beta endpoints shadow --endpoint ep_abc123 --model ml_abc123 \
  --rate 0.05 --key body.user --name cohort-safety

tg beta endpoints shadow --endpoint ep_abc123 --model ml_abc123 \
  --target-qps 5.0 --name throttled-canary
```

### Update, target management, and stop

- **Retune sampling** — Fetch the experiment, pass its current `etag` back in an update. A stale
  `etag` returns `409 ABORTED`.
- **Add a target** — Adds fan-out. One sampling decision fans out to every target, multiplying
  mirrored volume across targets.
- **Pause without deleting** — Update `source` and set `rate` to `0`.
- **Stop** — Delete the experiment (cascade-deletes targets), or remove all targets so the
  experiment goes `INACTIVE`.

```bash
tg beta endpoints rm exp_abc123
```

Propagation: new or updated shadow experiments take effect within about 30–60 seconds. Deletes
stop mirroring within the same window. Mirrored requests are never sampled and mirrored again;
shadow loops are impossible.

### Response fields

| Field | Description |
| --- | --- |
| `id` | `exp_...` experiment identifier. |
| `endpoint_id` | Endpoint whose traffic is sampled. |
| `name` | Unique within the endpoint. Immutable after create. |
| `source` | Sampling configuration. |
| `targets` | Inline on `Get`. |
| `state` | Derived: `ACTIVE` when at least one target exists, `INACTIVE` otherwise. Not settable. |
| `etag` | Version tag for optimistic concurrency on update/delete. |
| `created_by` / `created_at` / `updated_at` | Provenance. |

### Limits

- Up to 100 inline targets on create; add more via target methods.
- `name` up to 256 characters, on experiments and targets.
- List `limit` defaults 50, max 500.

## Rollouts (`rol_...`)

A rollout shifts traffic from a source deployment to a target deployment under the same endpoint,
optionally gated on live metrics.

### Strategies

Pick one strategy per rollout:

| Strategy | Traffic pattern | Use when |
| --- | --- | --- |
| **Canary** | Staged percentage ladder (e.g. 25%, 50%, 75%, 100%). Source drains stepwise. | Gradual, metric-gated exposure. Safest for production. |
| **Blue-green** | Single 0 → 100 cutover after target is ready. | Atomic cutover with capacity for both sides at full size. |
| **Rolling** | Replica-by-replica batch swap (target +1 / source −1). | Preserve GPU capacity; no traffic ramp needed. |

Metric gates are **canary-only**. Blue-green and rolling reject a `metrics` block.

### Requirements

- A source deployment referenced in the endpoint's traffic split.
- A target deployment with at least one replica, `READY`. Don't start a rollout with target bounds
  at `0/0` — traffic can shift before a replica is ready and cause `deployment_stopped` errors.
- Target project in good billing standing (rechecked at each target scale-up; `ENTITLEMENT_LAPSED`
  otherwise).

### Create (CLI)

```bash
# Canary (defaults: steps 10,50,100 over 10m intervals)
tg beta endpoints rollout dep_target456 --from dep_source123 --canary

# Blue-green (default when no strategy flag is set)
tg beta endpoints rollout dep_target456 --from dep_source123 --blue-green

# Rolling
tg beta endpoints rollout dep_target456 --from dep_source123 --rolling
```

Customize a canary ladder with `--steps` (e.g. `--steps 25,50,75,100`) and `--interval` (e.g.
`--interval 10m`). Pass `--source-cleanup keep` to keep the source at its replica count after
completion instead of draining.

Save the returned rollout ID (`rol_...`).

### Metric gates (canary-only)

Only the SDK/API creates a metric-gated rollout. Metric gates evaluate after each step's soak
window and either advance or pause the rollout.

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
            {"traffic": 75, "replicas": 3},
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
client.beta.endpoints.rollouts.start(
    rollout.id, project_id=project_id, endpoint_id="ep_abc123"
)
```

`final_target_replicas` must be at least `1`. Steps declare the traffic ladder and the target
replica count at each step; metrics declare the gate checked after each soak.

Each metric rule has:

- `name` — a **gate catalog key** (not a raw Prometheus series). See table below.
- `stat` and `percentile` — `METRIC_STAT_TYPE_PERCENTILE` (with `percentile`) for histograms,
  `METRIC_STAT_TYPE_AVG` for ratios / gauges.
- Exactly one of `regression_check` (relative-to-source, with `max_regression_percent` and
  `direction`) or `threshold_check` (absolute, with `value` and `operator` from
  `THRESHOLD_OPERATOR_{GT,GTE,LT,LTE}`). Latency `value` is in **milliseconds**.
- `window` — Lookback duration in seconds. Use `300s` for histogram percentiles.
- Rules are ANDed; any regression or unavailability pauses the step.

Supported metric catalog:

| `name` | Type | Meaning | `stat` |
| --- | --- | --- | --- |
| `serving_latency` | Histogram | Engine request duration. Preferred latency gate. | `AVG`, `PERCENTILE` |
| `router_latency` | Histogram | Router per-attempt latency. Bimodal — gate on `PERCENTILE` ≥ 95. | `AVG`, `PERCENTILE` |
| `router_error_rate` | Ratio | Router 5xx / total responses. | `AVG` |
| `inflight_requests` | Gauge | In-flight on the target pods. | `AVG` |

Higher is worse for all four. For reliability gates, prefer `serving_latency` and
`router_error_rate`, which are keyed by deployment ID and present whenever the target takes
traffic.

Metric gates require live traffic on the target. Without it, samples never accumulate, the gate
reports `METRICS_UNAVAILABLE`, and the rollout pauses.

### `inflight_requests` normalization

For `regression_check` on `inflight_requests` only:

- Compares **per ready replica**. `sourceValue`, `targetValue`, and `reason` are per-replica, not
  totals, and won't match a dashboard's summed count. `reason` appends `(values per ready replica)`.
- `threshold_check` on `inflight_requests` stays on raw totals.
- **Low-signal baselines are floored** at one request per replica. Trickle traffic can't pause or
  abort a rollout on its own; if a regression still fires, the gate re-evaluates before acting and
  the `reason` also notes `(source baseline floored at 1 per replica)`.

### Choose a `window`

`window` is the lookback for the metric query, in seconds. Use `300s` for histogram percentiles.
Short windows (like `60s`) sit inside ingestion lag and produce untrustworthy percentiles. Keep
`step_interval` ≥ `window + ~90s` so the metric can settle.

### Manage a running rollout

| CLI | SDK | Effect |
| --- | --- | --- |
| `rollout <rol_id> --pause [--reason "..."]` | `rollouts.pause` | Hold at current step; honored at next step boundary. |
| `rollout <rol_id> --continue` | `rollouts.resume` | Resume from current step. |
| `rollout <rol_id> --complete` | `rollouts.promote` | Fast-forward to final step; all traffic to target. |
| `rollout <rol_id> --abort [--reason "..."]` | `rollouts.abort` | Cancel; traffic reverts to source. Terminal, active-only. |

### Pause categories

`SYSTEM_PAUSED` rollouts carry a `status.condition.category` — use it, not the free-text message,
to decide next steps:

| Category | Meaning | Typical action |
| --- | --- | --- |
| `METRIC_REGRESSION` | Metric gate detected regression vs. source. | Abort. |
| `METRICS_UNAVAILABLE` | Load gap; not enough samples. | Restore load, then resume. |
| `TARGET_NOT_READY` | Target didn't become ready in time. | Investigate, then resume or abort. |
| `SOURCE_NOT_DRAINED` | Source still has replicas that should have drained. | Wait or investigate. |
| `HEALTH_REGRESSION` | Health check failed during soak. | Abort. |
| `CAPACITY_EXHAUSTED` | Not enough fleet capacity for requested replicas. | Wait, then resume. |
| `ROUTING_ERROR` | Invalid routing configuration hit during shift. | Fix routing, then resume or abort. |
| `DEPENDENCY_OUTAGE` | Platform dependency unreachable too long. | Wait, then resume. |
| `POLICY_INFEASIBLE` | Autoscaling ceiling below the replica floor the step requires. | Fix bounds, then resume. |
| `UNDER_SERVED` | Ready capacity dropped below split requirements. | Restore capacity or reduce split, then resume. |
| `ENTITLEMENT_LAPSED` | Billing/entitlement check failed before a target scale-up. | Resolve billing, then resume or abort. |
| `ABORTED_BY_OPERATOR` | Operator aborted. | Terminal. |
| `INTERNAL` | Unexpected platform error. | Contact support with rollout ID and message. |

### Rollout state machine

`PENDING → RUNNING ↔ STABILIZING → COMPLETED` on success, with side branches into `PAUSED`,
`SYSTEM_PAUSED`, `ABORTING`, `ABORTED`.

| State | Meaning |
| --- | --- |
| `PENDING` | Created, not yet started. |
| `RUNNING` | Actively shifting traffic. |
| `STABILIZING` | Holding at a step's traffic level before moving to the next. |
| `PAUSED` | Operator-paused. Traffic holds. |
| `SYSTEM_PAUSED` | Platform-paused for review. Read `status.condition.category`. |
| `ABORTING` | Cancellation in progress; reverting to source. |
| `ABORTED` | Terminal. Traffic on source. |
| `COMPLETED` | Terminal. Traffic on target; source drained. |

### Roll back after completion

Once a rollout is `COMPLETED`, the source is drained — you cannot abort. To revert, run a new
rollout in reverse: the now-serving target becomes the source, and the old deployment becomes the
target.

### Delete

Delete pending or terminal rollouts via the SDK (`rm` doesn't accept `rol_...`):

```python
client.beta.endpoints.rollouts.delete(
    "rol_abc123", project_id=project_id, endpoint_id="ep_abc123",
)
```

An endpoint can have only one active rollout at a time. Finish or abort the existing rollout
before creating another.

## Cross-feature rules

- A deployment used as a **shadow target** cannot also serve live traffic. Attempting to give it a
  non-zero weight in the traffic split returns:
  `the deployment is a shadow experiment target and cannot serve live traffic; remove the shadow target first`.
- A deployment used as an **A/B variant** must be excluded from the traffic split.
- A **rollout** requires the source to be in the traffic split; against a source that isn't
  referenced in the split, the rollout starts but shifts nothing.
- **Deletion order matters**: stop deployments before deleting them, and drop their traffic-split
  weight to `0` first (or use `tg beta endpoints rm dep_...`, which auto-detaches).
