# Dedicated Model Inference — Traffic Routing

How an endpoint decides which deployment serves each request, and the tools for moving
traffic: weighted splits, A/B tests, and shadow experiments.

## Contents

- [How routing works](#how-routing-works)
- [Stickiness](#stickiness)
- [Observing routing](#observing-routing)
- [Traffic splits (weights)](#traffic-splits-weights)
- [Replace a deployment (gradual cutover)](#replace-a-deployment-gradual-cutover)
- [A/B tests](#ab-tests)
- [Shadow experiments](#shadow-experiments)
- [Choosing a strategy](#choosing-a-strategy)

## How routing works

A deployment — even `READY` — receives no traffic until it's routed to. The endpoint resolves
each request through sampling stages:

1. **Traffic split** — sample a candidate in proportion to capacity (weight × ready replicas).
2. **A/B test** — if the candidate is an A/B control, re-sample among control + variants by
   the test percentages.
3. **Route** — send to the final deployment.

Shadow experiments sit outside this path entirely (copies, not routing).

## Stickiness

Routing is deterministic per request: the endpoint derives a **sampling key** and always
routes the same key to the same deployment (while the split is stable). This keeps prompt
caches warm across a conversation. Key precedence:

1. `prompt_cache_key` request field, if set.
2. Otherwise the `user` field, if set.
3. Otherwise a key derived from request content.

Set `prompt_cache_key` on requests sharing a prompt prefix (e.g. every turn of one
conversation) to control stickiness. Editing weights or adding/removing deployments
reassigns some keys.

## Observing routing

To verify empirically how traffic actually lands — for a split or an A/B test — you
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

Set one deployment's weight from the CLI — it resolves the parent endpoint and preserves the
other deployments' weights, so run it once per deployment:

```bash
tg beta endpoints update dep_abc123 --traffic-weight 70
tg beta endpoints update dep_def456 --traffic-weight 30

# Take a deployment out of rotation without scaling it down
tg beta endpoints update dep_abc123 --traffic-weight 0
```

Or replace the whole split at once from the SDK/API:

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

## Replace a deployment (gradual cutover)

To migrate an endpoint to a new model version, config, or hardware on live traffic, run both
deployments side by side and shift traffic with weights and replica counts:

1. Create the new deployment on the **same endpoint**, sized for its eventual share, and wait
   for `READY`. It receives no traffic yet (weight unset).
2. Give it a small share: `tg beta endpoints update dep_new --traffic-weight 10` (with the old
   deployment holding e.g. weight 90 — remember share is weight x ready replicas, so match
   replica counts or account for them).
3. Watch the dashboard (and the [Observing routing](#observing-routing) probe) between steps;
   raise the new deployment's weight stepwise (25 -> 50 -> 100-equivalent) as confidence grows.
4. Cut over: `tg beta endpoints update dep_old --traffic-weight 0` takes the old deployment
   out of rotation without scaling it down — instant rollback is just restoring its weight.
5. Once stable, scale the old deployment to `0/0`, wait for `STOPPED`, and `rm` it.

Weight changes propagate in tens of seconds (see the propagation note above) and reassign
some sticky keys. To evaluate the candidate *before* giving it live traffic, use a
[shadow experiment](#shadow-experiments); to compare on a fixed slice of live traffic, use an
[A/B test](#ab-tests).


## A/B tests

An A/B experiment holds a **fixed** split between a control deployment and 1–19 variants,
subdividing only the control's share of traffic. Use it to measure a candidate before
committing; migrate with a [gradual cutover](#replace-a-deployment-gradual-cutover).

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

To ship a winning variant, delete the test (`rm abx_abc123`) and move traffic with a
[gradual cutover](#replace-a-deployment-gradual-cutover): give the variant a traffic weight
and take the old control to `--traffic-weight 0`. Deleting the test returns all traffic to
the regular split immediately (verified: after `rm`, a varied probe lands 100% on the
control's cluster) — so set the variant's weight promptly after deleting.

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
| Replace a deployment on live traffic | Gradual cutover with `--traffic-weight` steps. |
| Measure a candidate on a fixed slice of user-visible traffic | A/B test. |
| Test a candidate with zero user impact / warm it up | Shadow experiment. |
| Ship the A/B or shadow winner | Delete the experiment, then shift weights to the winner. |
