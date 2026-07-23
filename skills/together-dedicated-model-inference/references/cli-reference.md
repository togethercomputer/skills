# Dedicated Model Inference — CLI Reference

The Together CLI is the fastest path for DMI. It's intent-based: each command expresses a goal
and wires up the underlying resources.

## Contents

- [Installation and invocation](#installation-and-invocation)
- [Command tree](#command-tree)
- [endpoints deploy](#endpoints-deploy)
- [endpoints ls / get](#endpoints-ls--get)
- [endpoints update](#endpoints-update)
- [endpoints rm (smart delete)](#endpoints-rm-smart-delete)
- [endpoints ab (A/B tests)](#endpoints-ab-ab-tests)
- [endpoints shadow (shadow experiments)](#endpoints-shadow-shadow-experiments)
- [models commands](#models-commands)
- [What the CLI can't do](#what-the-cli-cant-do)

## Installation and invocation

```bash
uv tool install "together[cli]"
tg --version                      # check; upgrade with: uv tool upgrade together
```

`tg` and `together` are interchangeable entry points (docs use `tg`). Project scoping: the CLI
uses the project associated with your API key, overridable with the `TOGETHER_PROJECT_ID` env
var or `--project` on any command. Every command accepts `--json` for machine-readable output.

**Scripting / non-interactive use (agents, CI, piped stdin).** Mutating commands such as
`deploy` print a confirmation preview and prompt before acting; with no TTY they can't read the
prompt and fail. Pass `--non-interactive` to skip the prompt. In that mode project inference
from the API key is *not* applied — `deploy` errors with `Project argument is required` unless
you also pass `--project <proj_...>` (or set `TOGETHER_PROJECT_ID`). A reliable scripted deploy
is therefore `tg beta endpoints deploy ... --project <proj_id> --non-interactive --json`.

## Command tree

```text
tg beta endpoints
  deploy     Deploy a model: create endpoint + deployment + route traffic in one step
  ls         List endpoints in the project
  get        Get endpoint details (also the default command: tg beta endpoints ep_abc123)
  update     Update a deployment: replica bounds, scaling metrics, traffic weight
  rm         Smart-delete any endpoint/deployment/experiment by ID prefix
  ab         Start an A/B test (creates the variant deployment)
  shadow     Start a shadow experiment (creates the shadow deployment)

tg beta models
  public          List platform-supported public models (the deployable catalog)
  list | ls       List models in your project (uploaded/fine-tuned)
  get <id>        Get a model
  configs <id>    List published configs for a model
  create          Register a custom model/adapter record
  upload          Upload local weights to a model record
  ls-files        List files in a model or adapter
  ls-revisions    List revisions for a model
  download        Download model/adapter files to a local directory
  update / rm     Update or delete a model record (rm was previously `delete`)
  remote-uploads  create | retrieve | list  (import from Hugging Face or presigned URL)
```

## endpoints deploy

Creates (or reuses) an endpoint, attaches a new deployment, and routes 100% of traffic to it.
Returns as soon as resources are created; the deployment provisions in the background.

```bash
tg beta endpoints deploy <model> --endpoint <name-or-id> [flags]
```

`<model>` (positional) accepts a model ID (`ml_...`) or a model name (public catalog name or a
model in your project). `--endpoint` takes a new name (creates the endpoint) or an existing
name/ID (adds a deployment to it).

| Flag | Default | Description |
| --- | --- | --- |
| `--config` | auto | Config ID (`cr_...`). Auto-selected when the model has exactly one; use `tg beta models configs <model_id>` to list. |
| `--deployment-name` | derived | Deployment name; defaults to model name + short suffix. |
| `--min-replicas` / `--max-replicas` | 1 / 1 | Replica bounds. Pass a range (e.g. 1/10) to autoscale. |
| `--scale-up-window` | — | Seconds the metric must stay above target before adding replicas. |
| `--scale-down-window` | — | Cooldown seconds between scale-downs. |
| `--scale-to-zero-window` | — | Idle time before scaling to zero replicas. |
| `--model-revision` | latest | Model revision ID (`rv_...`) to pin. |
| `--scaling-metric` / `--scaling-target` / `--scaling-percentile` | — | Autoscale on one metric (pair with a `--min`/`--max` range): metric name + target, optional percentile (`p50`/`p90`/`p95`/`p99`, latency metrics only). The CLI takes a single metric as flat flags — the JSON `scaling_metrics` array is SDK/API-only. |
| `--placement` | — | Placement profile ID to use. |
| `--regions` | — | Comma-separated inline placement regions (mutually exclusive with `--placement`). |
| `--constraint` | — | `required` or `preferred` — how strictly to enforce inline placement regions. |
| `--enable-lora` | off | Run the multi-LoRA kernel so adapters hot-load. Toggling later needs a redeploy. |

There is no `--inactive-timeout` / auto-shutdown — deployments run and bill until you stop
them.

```bash
# Deploy a public model, single replica
tg beta endpoints deploy ml_CbJNwQC2ZqCU2iFT3mrCh --endpoint my-endpoint

# Explicit config, autoscaling 1-10
tg beta endpoints deploy ml_CbJNwQC2ZqCU2iFT3mrCh \
  --endpoint my-endpoint \
  --config cr_CbzGdmn14t3HYrXXitmKa \
  --min-replicas 1 --max-replicas 10
```

Output includes the endpoint ID (`ep_...`), deployment ID (`dep_...`), and the **endpoint
string** (`your-project-slug/my-endpoint`, labeled "Endpoint string" in `get` output) — the
value for the inference `model` parameter. First-time provisioning commonly takes up to ~20 minutes while
weights download and hardware is allocated.

## endpoints ls / get

```bash
tg beta endpoints ls [--limit N] [--after CURSOR] [--org] [--public]
tg beta endpoints get ep_abc123    # endpoint detail: split + each deployment's state/replicas
tg beta endpoints get dep_abc123   # deployment detail (parent endpoint resolved automatically)

# Machine-readable deployment state for polling loops
tg beta endpoints get dep_abc123 --json | jq -r '.status.state'
```

`get` accepts an endpoint **or** deployment ID. Re-running it is a quick way to poll a
deployment as it comes up. Passing an ID with no subcommand (`tg beta endpoints ep_abc123`)
runs `get`. For deployment lists with `filter`/`order_by`, use the SDK/API — see
[api-reference.md](api-reference.md).

## endpoints update

Updates a **deployment's** parameters. Pass the deployment ID (`dep_...`); the CLI resolves
its parent endpoint automatically. At least one option is required.

```bash
# Scale replica bounds
tg beta endpoints update dep_abc123 --min-replicas 2 --max-replicas 4

# Stop (scale to zero; billing stops) / restart
tg beta endpoints update dep_abc123 --min-replicas 0 --max-replicas 0
tg beta endpoints update dep_abc123 --min-replicas 1 --max-replicas 2

# Scale on a specific metric (one metric, flat flags — not the SDK/API JSON array)
tg beta endpoints update dep_abc123 --min-replicas 1 --max-replicas 4 \
  --scaling-metric gpu_utilization --scaling-target 70

# Set this deployment's traffic weight (preserves the other deployments' weights)
tg beta endpoints update dep_abc123 --traffic-weight 30

# Take it out of rotation without scaling it down
tg beta endpoints update dep_abc123 --traffic-weight 0
```

| Flag | Description |
| --- | --- |
| `--name` | Rename the deployment. |
| `--min-replicas` / `--max-replicas` | Updated replica bounds. |
| `--scale-up-window` / `--scale-down-window` / `--scale-to-zero-window` | Autoscaling stabilization windows. |
| `--scaling-metric` / `--scaling-target` / `--scaling-percentile` | Autoscale on one metric: metric name + target, plus an optional percentile (`p50`/`p90`/`p95`/`p99`, latency metrics only). The CLI takes a single metric this way; the JSON `scaling_metrics` array is SDK/API-only (see api-reference.md, Scaling Metrics). |
| `--traffic-weight` | Capacity weight in the endpoint's traffic split. Upserts just this deployment's entry; `0` stops routing to it. |
| `--etag` | ETag for optimistic concurrency. |

Notes:

- `--traffic-weight` edits one deployment's split entry. Replacing the whole split at once is
  still an SDK/API operation (`endpoints.update(traffic_split=[...])`).
- LoRA loading can't be changed after a deployment is created — redeploy with
  `deploy --enable-lora` to turn it on or off.
- There is no `--inactive-timeout` — auto-shutdown was removed; stop idle deployments with
  `--min-replicas 0 --max-replicas 0`.

## endpoints rm (smart delete)

Resolves the resource by ID prefix and deletes it: endpoint (`ep_`), deployment (`dep_`), A/B
experiment (`abx_`), shadow experiment (`exp_`).

```bash
tg beta endpoints rm dep_abc123          # delete a deployment (must be STOPPED)
tg beta endpoints rm ep_abc123           # delete an endpoint with no deployments
tg beta endpoints rm ep_abc123 --force   # scale deployments to 0/0 and tear everything down
tg beta endpoints rm abx_abc123          # end an A/B test (traffic returns to control)
tg beta endpoints rm exp_abc123          # stop a shadow experiment
```

Deleting a deployment auto-detaches it from the traffic split and any experiments. Running
deployments: `rm dep_...` on a running deployment scales it to `0/0` for you and asks you to
retry once it reaches `STOPPED` (the delete itself still requires a stopped deployment);
`rm ep_... --force` scales the endpoint's deployments down itself as part of teardown. `rm`
smart-deletes endpoints, deployments, and experiments only.

## endpoints ab (A/B tests)

Creates a variant deployment for a model and starts an A/B experiment against a control
deployment that's already serving traffic. The CLI assigns the remainder to the control.

```bash
tg beta endpoints ab Qwen/Qwen2.5-7B-Instruct \
  --control dep_control123 \
  --percent 5 \
  --name sampling-tweak-v1
```

The variant model is the positional argument (same forms as `deploy`). For a **public catalog
model, pass the name** (as above), not the `ml_` ID echoed by `deploy`/`models public` — that
ID is owned by a platform project and the positional resolves it in *your* project, failing
with `Model ml_… not found`. Use the `ml_` ID only for a model that lives in your own project.

| Flag | Description |
| --- | --- |
| `--control` | Control deployment ID currently serving live traffic. Required. |
| `--percent` | Traffic percent for the variant, integer 1–100 (default 1). |
| `--config` | Config for the variant (auto-selected like `deploy`). |
| `--name` | Variant deployment name (defaults to model name + suffix). |
| `--enable-lora` | Enable the multi-LoRA kernel on the variant. |

Ramping or editing an existing experiment is SDK/API only (`ab_experiments.update` replaces
the whole member set, and requires `update_mask="members"` + the current `etag` or it 400s —
see [traffic-routing.md](traffic-routing.md)). End the test with `rm abx_...`.

## endpoints shadow (shadow experiments)

Creates a shadow deployment from a model and mirrors a sampled fraction of live endpoint
traffic to it. Responses from the shadow are measured and discarded — callers never see them.

```bash
# Uniform 10% mirror
tg beta endpoints shadow --endpoint ep_abc123 \
  --model ml_CbJNwQC2ZqCU2iFT3mrCh --rate 0.1 --name candidate-v2

# Sticky per-user sampling
tg beta endpoints shadow --endpoint ep_abc123 \
  --model ml_CbJNwQC2ZqCU2iFT3mrCh --rate 0.05 --key body.user --name candidate-v2

# Adaptive: throttle toward ~5 QPS
tg beta endpoints shadow --endpoint ep_abc123 \
  --model ml_CbJNwQC2ZqCU2iFT3mrCh --target-qps 5.0 --name candidate-v2
```

| Flag | Description |
| --- | --- |
| `--endpoint` | Endpoint serving the live traffic to mirror — accepts an ID or a name. |
| `--model` / `--config` | Model (and optional config) for the shadow deployment. |
| `--rate` | Fraction of traffic to mirror, 0.0–1.0 (uniform / key_based). |
| `--key` | Request-body field for sticky sampling (e.g. `body.user`). |
| `--target-qps` | Target mirrored QPS (adaptive strategies; approximate throttle). |
| `--window` | Sliding window for adaptive QPS observation (default 60s). |
| `--name` | Shadow deployment name. |

Pass `--rate` or `--target-qps` (one is required). Stop with `rm exp_...`.

## models commands

```bash
# Browse the deployable public catalog
tg beta models public --product DEDICATED
tg beta models public --modality TEXT --search qwen

# List configs published for a model (hardware, GPU count, optimization)
tg beta models configs ml_CbJNwQC2ZqCU2iFT3mrCh

# Register a custom model or adapter record (name it bare, no org prefix)
tg beta models create gemma-4-31b-it --base-model ml_CbJNwQC2ZqCU2iFT3mrCh

# Upload local weights (use --type adapter for a LoRA adapter)
tg beta models upload ml_abc123 ./path/to/model-dir
tg beta models upload ml_abc123 ./path/to/adapter-dir --type adapter

# Import from Hugging Face or a presigned S3 URL (server-side streaming)
tg beta models remote-uploads create ml_abc123 \
  --from https://huggingface.co/your-org/your-repo --token hf_your_token
tg beta models remote-uploads retrieve job_abc123
tg beta models remote-uploads list

# Inspect your project's models
tg beta models list
tg beta models ls-files ml_abc123
tg beta models ls-revisions ml_abc123

# Download files back to your machine (--format hf = HuggingFace snapshot layout)
tg beta models download ml_abc123 ./local-dir [--revision rv_...] [--format hf]

# Delete a model record (metadata only; renamed from `delete`)
tg beta models rm ml_abc123
```

`--type` values are asymmetric: **write** commands (`upload`, `remote-uploads create`) take
singular `model` / `adapter` (default `model`); **read** commands (`ls-files`,
`remote-uploads retrieve` / `list`) take plural `models` / `adapters` (default `models`).

Full upload flows (requirements, S3 archive format, polling, deploying the result) are in
[models-and-configs.md](models-and-configs.md).

## What the CLI can't do

These are SDK/API-only operations; don't hunt for CLI flags:

- Replace an endpoint's traffic split in one call (`update --traffic-weight` upserts one
  deployment at a time; the full-split write is `endpoints.update(traffic_split=[...])`).
- List deployments or use `filter` / `order_by` (though `get` reads a single deployment and
  shows every deployment's state on the endpoint view).
- Ramp/edit an existing A/B experiment, or update a shadow experiment's sampling.
- Read the events feed.
- Inference itself — point the SDK or curl at `https://api-inference.together.ai/v1`.
