# Dedicated Model Inference — Models, Configs, Pricing, and Uploads

## Contents

- [Choose a model](#choose-a-model)
- [Deployment profiles](#deployment-profiles)
- [Configs](#configs)
- [Pricing and hardware](#pricing-and-hardware)
- [Upload a custom model](#upload-a-custom-model)
- [Upload a LoRA adapter](#upload-a-lora-adapter)
- [Upload troubleshooting](#upload-troubleshooting)

## Choose a model

List the platform-supported catalog (public base models deployable for DMI):

```bash
tg beta models public --product DEDICATED
tg beta models public --modality TEXT --search qwen
```

```python
models = client.beta.models.list_supported(product="PRODUCT_DEDICATED")
for m in models.data:
    print(m.id, m.name)

model = client.beta.models.retrieve_supported("arch_abc123")
```

Catalog entries are architectures (`arch_...`) with a catalog-controlled Hugging Face `name`
(e.g. `Qwen/...`), a `displayName`, a `displayType` badge (`chat`, `language`, `code`,
`image`, `embedding`, `rerank`, `moderation`, `audio`, `video`, `transcribe`), and
`deploymentProfiles`.

Models in **your project** (uploads, fine-tunes) are listed separately:

```bash
tg beta models list
```

```python
models = client.beta.models.list(project_id=project_id)
```

Not every model is deployable, and a fine-tuned model deploys only if its base architecture is
supported. Don't hardcode model names — list the catalog and use real IDs.

## Deployment profiles

Each supported-model entry carries `deploymentProfiles`: certified model-and-config pairs
Together publishes. Each profile gives you `model` and `config` **resource names you can pass
straight into a deployment create**, plus `gpuType`, `gpuCount`, and `parallelism` (free-form:
`TP8`, `TP4`, `EP`, `PD` — not always a tensor-parallel degree).

```json
{
  "profileId": "cfg_a",
  "config": "projects/proj_cfg/configs/cr_certified",
  "model": "projects/proj_weights/models/ml_weight/revisions/rv_snap",
  "parallelism": "TP8",
  "gpuType": "H100",
  "gpuCount": 8
}
```

Note the owning projects in these resource names are platform projects — copy the strings
verbatim rather than substituting your own project ID.

## Configs

A config describes how a model runs: inference engine, hardware selectors, optimization
profile. Together publishes configs per model; you pick one when creating a deployment. The
CLI's `deploy` auto-picks when the model has exactly one config.

```bash
tg beta models configs ml_CbJNwQC2ZqCU2iFT3mrCh
```

```python
configs = client.beta.models.configs.list(
    project_id=project_id,
    reference_model=f"projects/{project_id}/models/{model_id}",
)
```

Responses include the config `id` (`cr_...`), `referenceModel`, the owning `projectId` (use it
when building the config resource name), and `selectors`:

| Selector | Description | Example |
| --- | --- | --- |
| `accelerator_type` | GPU SKU the config targets. | `nvidia-h100-80gb` |
| `accelerator_count` | GPUs per replica. | `1`, `2`, `4`, `8` |
| `optimization` | Serving profile. | `balanced`, `throughput`, `latency` |
| `topology` | Model layout across GPUs. | `aggregated` |

Picking a config:

- **Single-GPU, balanced** — good default; lowest per-replica cost.
- **Multi-GPU** — higher throughput / lower latency for large models or heavy traffic, at a
  proportionally higher per-replica price.
- **Latency-optimized** — when time to first token matters most.

Key properties:

- **Configs are immutable.** New revisions get new `cr_...` IDs; a deployment pins the
  revision you selected, so hardware and engine never change underneath it.
- **Hardware is fixed for a deployment's life.** To change hardware, create a new deployment
  with a different config and shift traffic over (ideally with a rollout).
- **Speculative decoding** is declared by the config (`draftModel` in the response when
  enabled); the deployment's speculator is derived and pinned at create — you can't set it
  yourself. Speculative decoding raises average throughput but can add occasional tail-latency
  spikes; latency-strict workloads should pick a latency-profile config.

## Pricing and hardware

DMI bills **per minute, per running replica, by hardware** — model and token volume don't
affect cost. A replica stops billing as soon as it scales down; a stopped deployment costs
nothing.

Single-GPU per-hour rates (multi-GPU configs cost proportionally more; check
[the pricing page](https://docs.together.ai/docs/dedicated-endpoints/pricing) for current rates):

| GPU | Hardware ID | Cost/hour |
| --- | --- | --- |
| H100 80GB | `1xnvidia-h100-80gb` | $5.49 |
| B200 180GB | `1xnvidia-b200-180gb` | $8.99 |

As a scale reference: one H100 replica running continuously is about $132/day, or roughly
$3,950 over a 30-day month.

Cost levers:

- `min_replicas` sets the cost floor (always running); `max_replicas` sets the ceiling.
- `inactive_timeout` (auto-shutdown) stops idle deployments; the next request pays a cold start.
- **On-demand** (per-minute, no commitment) vs **reserved** (committed term, lower effective
  rate, guaranteed hardware — contact Together sales).

DMI vs serverless rule of thumb: DMI wins when a replica stays busy most of the day (fixed
cost spread over high throughput, plus reserved capacity and predictable latency); serverless
wins for low or bursty traffic where a dedicated replica would idle.

## Upload a custom model

Serve your own fine-tuned weights. Requirements:

- **Source**: Hugging Face Hub or an S3 presigned URL (or local files via CLI upload).
- **Architecture**: a fine-tuned variant of a base model Together supports for dedicated
  inference — uploads cannot introduce new architectures.
- **Type**: text generation or embedding; **must fit on a single GPU** (multi-GPU uploads not
  supported).
- **Format**: standard Hugging Face repo layout compatible with `from_pretrained`
  (`config.json`, `*.safetensors`, `tokenizer.json`, ...).
- **S3 archives**: a single `.zip` / `.tar.gz` with the files at the **archive root** (no
  nested top-level directory); presigned URL valid for at least 100 minutes.
  From inside the model dir: `tar -czvf ../model.tar.gz .`

### Step 1 — Register the model record

Every custom model references a supported base model via `base_model_id`. **Name it bare**
(`gemma-4-31b-it`), not org-prefixed (`google/gemma-4-31b-it`) — the platform prepends your
project slug, an org prefix produces a doubled slug, and a doubled name can't be renamed
(delete and re-upload is the only fix).

```bash
tg beta models create gemma-4-31b-it --base-model ml_CbJNwQC2ZqCU2iFT3mrCh
```

```python
model = client.beta.models.create(
    project_id=project_id,
    model={"name": "gemma-4-31b-it", "base_model_id": "ml_CbJNwQC2ZqCU2iFT3mrCh"},
)
```

Save the returned `id` (`ml_...`).

### Step 2 — Upload the weights

Local directory (CLI handles the multipart upload):

```bash
tg beta models upload ml_abc123 ./path/to/model-dir
```

Remote (server-side streaming from Hugging Face or presigned S3 URL; `--token` for gated or
private HF repos):

```bash
tg beta models remote-uploads create ml_abc123 \
  --from https://huggingface.co/your-org/your-repo --token hf_your_token
```

```python
job = client.beta.models.remote_uploads.create(
    project_id=project_id,
    type="model",
    model_id="ml_abc123",
    remote_url="https://huggingface.co/your-org/your-repo",
    token="hf_your_token",
)
```

### Step 3 — Poll until succeeded

```bash
tg beta models remote-uploads retrieve job_abc123
tg beta models ls-files ml_abc123     # confirm files landed
```

Poll `status` until `REMOTE_UPLOAD_STATUS_SUCCEEDED`.

### Step 4 — Deploy

Same as any model — list your project's configs for it and deploy:

```bash
tg beta endpoints deploy ml_abc123 --endpoint my-custom-model --config cr_abc123
```

## Upload a LoRA adapter

Same flow as a custom model with `--type adapter` (`type="adapter"` in the SDK). Adapter-specific
requirements:

- The adapter directory must contain `adapter_config.json` and `adapter_model.safetensors`.
- The adapter must target a supported base model (set via `base_model_id` on the record).
- Adapter versioning isn't supported — re-upload under a new name.

```bash
tg beta models create my-stsb-lora --base-model ml_CbJNwQC2ZqCU2iFT3mrCh

# Local
tg beta models upload ml_abc123 ./path/to/adapter-dir --type adapter

# Remote
tg beta models remote-uploads create ml_abc123 \
  --from https://huggingface.co/your-org/your-adapter --type adapter --token hf_your_token

# Poll / verify — read commands take the PLURAL --type adapters
tg beta models remote-uploads retrieve job_abc123 --type adapters
tg beta models ls-files ml_abc123 --type adapters
```

Note the `--type` asymmetry: write commands (`upload`, `remote-uploads create`) take singular
`model`/`adapter`; read commands (`ls-files`, `remote-uploads retrieve`/`list`) take plural
`models`/`adapters`.

Deploy the adapter's `ml_...` ID like a base model, using a config for its base model. To
hot-load adapters onto a running deployment, the deployment must have been created with
`--enable-lora` (toggling later requires a redeploy).

## Upload troubleshooting

- **"Model not found" during upload** — create the record first (`models create`) and pass
  the returned `ml_...` ID to the upload.
- **`base_model_id is required`** — every custom model/adapter must reference a supported
  base model; get the ID from `tg beta models public`.
- **"Model name already exists"** — names are unique; pick a new one (no versioning).
- **Missing required files** — adapters need both `adapter_config.json` and
  `adapter_model.safetensors` at the source root.
- **Job stuck in `Processing`** — the source usually can't be reached: expired presigned URL,
  or HF token lacking repo access.
- **`401`/`403`** — check `TOGETHER_API_KEY`, HF token permissions, and presigned URL expiry.
- **Doubled slug in the catalog** (`your-project/google/gemma...`) — the record was created
  with an org-prefixed name; delete and re-create with the bare name.
