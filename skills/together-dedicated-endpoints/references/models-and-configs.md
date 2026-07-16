# Models, configs, and deployment profiles (v2)

DMI v2 splits what v1 called "a model" into three layered concepts:

- **Architecture** — the top-level catalog entry (e.g. `zai-org/GLM-5.2`), identified by an
  `arch_...` slug. This is the family you pick from the [supported-models
  catalog](https://docs.together.ai/docs/dedicated-endpoints/models).
- **Weight (model)** — a concrete build of an architecture at one quantization (e.g. BF16 or FP8),
  identified by `ml_...`. Weights are what you actually deploy. An architecture can have several.
- **Config (`cr_...`)** — a certified serving spec for one weight, fixing engine, parallelism,
  hardware, and optimization. Immutable. New revisions get new IDs.

A **deployment profile** is a certified pair of one weight + one config, published in the catalog.
When an architecture has one profile the CLI selects it automatically; when it has several, pass
`--config <cr_...>`.

## Contents

- [List supported models](#list-supported-models)
- [List a model's profiles](#list-a-models-profiles)
- [Upload a fine-tuned model](#upload-a-fine-tuned-model)
- [Upload a LoRA adapter](#upload-a-lora-adapter)
- [Choose a profile](#choose-a-profile)
- [Decoding optimizations](#decoding-optimizations)

## List supported models

Use the [supported-models catalog](https://docs.together.ai/docs/dedicated-endpoints/models) as the
primary source of truth — it lists deployable architectures with their smallest published profile's
`Deployable hardware` (instance type). For the same data in JSON:

```bash
# All models available for dedicated inference
tg beta models public --product DEDICATED

# Narrow by modality or search
tg beta models public --modality TEXT --search qwen

# Full JSON records, including deploymentProfiles[]
tg beta models public --product DEDICATED --json
```

Response shape:

```json
{
  "data": [
    {
      "id": "arch_abc123",
      "name": "zai-org/GLM-5.2",
      "displayName": "GLM 5.2",
      "displayType": "chat",
      "deploymentProfiles": [
        {
          "profileId": "cfg_a",
          "certifiedConfigRevisionId": "cr_certified",
          "certifiedModelRevisionId": "rv_snap",
          "config": "projects/proj_cfg/configs/cr_certified",
          "model": "projects/proj_weights/models/ml_weight/revisions/rv_snap",
          "parallelism": "TP8",
          "gpuType": "H100",
          "gpuCount": 8
        }
      ]
    }
  ]
}
```

Identity fields per architecture:

| Field | Description |
| --- | --- |
| `id` | Architecture UID (`arch_...`). |
| `name` | Catalog-controlled Hugging Face model ID (e.g. `zai-org/GLM-5.2`). |
| `displayName` | Human-readable name (e.g. `GLM 5.2`). |
| `displayType` | One of `chat`, `language`, `code`, `image`, `embedding`, `rerank`, `moderation`, `audio`, `video`, `transcribe`. |

Deployment-profile fields:

| Field | Description |
| --- | --- |
| `config` | Resource name `projects/{project_id}/configs/{config_revision_id}`. Empty when unpinned. |
| `model` | Resource name `projects/{project_id}/models/{model_id}[/revisions/{revision_id}]`. Empty when unpinned. |
| `parallelism` | Free-form parallelism spec (e.g. `TP8`, `TP4`, `EP`, `PD`). |
| `gpuType`, `gpuCount` | Hardware summary. |

Copy `model` and `config` straight into the corresponding fields of a create-deployment request.

## List a model's profiles

For a specific weight (public or your own uploaded model):

```bash
tg beta models configs ml_CbJNwQC2ZqCU2iFT3mrCh
```

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

The config `id` is a config revision. Pass it as a resource name in the `config` field of a
create-deployment request, using the config's `projectId` for `{project_id}` (often a Together
platform project rather than yours):

```
projects/{project_id}/configs/{config_revision_id}
```

Config selectors:

| Selector | Description | Example |
| --- | --- | --- |
| `accelerator_type` | GPU SKU. | `nvidia-h100-80gb` |
| `accelerator_count` | GPUs per replica. | `1`, `2`, `4`, `8` |
| `optimization` | Serving profile. | `balanced`, `throughput`, `latency` |
| `topology` | Layout across GPUs. | `aggregated` |

## Upload a fine-tuned model

Uploads must be **fine-tuned variants of a supported base architecture**. Not every model is
accepted; unsupported architectures, layer types, or adapter ranks are rejected at create or upload.

File format is standard Hugging Face `from_pretrained`-compatible layout (`config.json`,
`tokenizer_config.json`, `tokenizer.json`, sharded `model-*.safetensors`, `model.safetensors.index.json`,
etc.).

### S3 archive requirements

- Package files in a `.zip` or `.tar.gz`.
- Files must be at the **root** of the archive — no extra top-level directory.
- Presigned URL expiration ≥ 100 minutes.

To create the archive from within a model directory:

```bash
cd /path/to/your/model
tar -czvf ../model.tar.gz .
```

### Step 1: Create the model record

```bash
tg beta models create gemma-4-31b-it \
  --base-model ml_CbJNwQC2ZqCU2iFT3mrCh
```

Save the returned `id` (for example `ml_abc123`). `--base-model` takes the base weight's
`baseModelId` (`ml_...`), NOT the architecture `arch_...`.

Uploaded models are **Private** by default (visible only to project members). Internal makes them
visible to the whole organization; Public makes them visible to anyone.

Create fields:

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Inference-addressable name. Prefer a readable name over a Hugging Face repo ID. |
| `base_model_id` | Yes | `baseModelId` (`ml_...`) of the supported base. |
| `description` | No | Description shown in the project catalog. |
| `type` | No | `model` (default) or `adapter`. Fixed at create. |

### Step 2: Upload the weights

```bash
# From your machine (multipart handled by the CLI)
tg beta models upload ml_abc123 ./path/to/model-dir

# From Hugging Face Hub or S3 (server-side stream)
tg beta models remote-uploads create ml_abc123 \
  --from https://huggingface.co/your-org/your-repo \
  --token hf_your_token
```

Remote-upload job response (relevant fields at top level):

```json
{
  "id": "job_abc123",
  "projectId": "proj_abc123",
  "modelId": "ml_abc123",
  "remoteUrl": "https://huggingface.co/your-org/your-repo",
  "status": "REMOTE_UPLOAD_STATUS_PENDING",
  "statusMessage": "",
  "restartCount": 0,
  "maxRestarts": 0,
  "createdAt": "2026-07-02T20:00:00Z",
  "updatedAt": "2026-07-02T20:00:00Z"
}
```

Poll until `REMOTE_UPLOAD_STATUS_SUCCEEDED`:

```bash
tg beta models remote-uploads retrieve job_abc123
tg beta models remote-uploads list
tg beta models ls-files ml_abc123           # confirm files landed
```

### Step 3: Deploy

```bash
tg beta endpoints deploy ml_abc123 \
  --endpoint my-custom-model \
  --config cr_CbzGdmn14t3HYrXXitmKa
```

### Common troubleshooting

- **"Model not found" during upload** — Create the record first with `tg beta models create`, then
  pass the returned `id` to the upload.
- **`base_model_id is required` on create** — Use the `baseModelId` (`ml_...`), not the
  architecture `arch_...`.
- **`tokenizer.chat_template is not set` during chat inference** — Uploaded tokenizer has no chat
  template. Add a compatible `chat_template` to `tokenizer_config.json` before upload, or use the
  text-completions API.
- **Model delete fails with `the model is referenced by a live deployment`** — Stop the deployment,
  wait for `DEPLOYMENT_STATE_STOPPED`, delete the deployment, then delete the model.

## Upload a LoRA adapter

Same workflow as full models, with `--type adapter` on create. Adapters must target a base model
that Together AI supports for dedicated inference.

Requirements:

- **Source** — Hugging Face Hub or S3 presigned URL.
- **Files** — `adapter_config.json` and `adapter_model.safetensors` at the root of the archive
  (S3) or the Hugging Face repo.
- **Base model** — Supported for dedicated inference.

Naming tip: strip any org prefix from the repo name (use `glue_stsb`, not `predibase/glue_stsb`).
The server prepends your project slug on top; adapters that already have a doubled slug can't be
renamed — the only fix is to delete and re-upload under the correct name.

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

Deploying an adapter creates its own endpoint. To hot-load multiple LoRA adapters at runtime on
one shared endpoint, deploy the base model with `--enable-lora` and follow the multi-LoRA v1
adapter flow (`docs/dedicated-endpoints/v1/lora-adapter`); at the v2 initial launch, multi-LoRA
serving is a v1-only feature.

### Common troubleshooting

- **"Model name already exists"** — Adapter names must be unique. Versioning isn't supported;
  re-upload under a new name.
- **Missing required files** — Confirm both `adapter_config.json` and `adapter_model.safetensors`
  exist at the root.
- **Base model incompatibility** — Verify the base is in the [supported-models
  catalog](https://docs.together.ai/docs/dedicated-endpoints/models).
- **Upload job stuck in `Processing`** — Source unreachable. Check S3 presigned URL expiration or
  Hugging Face token permissions.
- **`401` / `403` during upload** — Check `TOGETHER_API_KEY`, Hugging Face token scope for private
  repos, and S3 URL validity.
- **Adapter delete fails with `the model is referenced by a live deployment`** — Stop the
  deployment, wait for `STOPPED`, delete the deployment, then delete the adapter.

## Choose a profile

Match the profile to the workload:

- **Single-GPU, `balanced`** — Default for most models; lowest per-replica cost.
- **Multi-GPU** — Higher throughput and lower latency for large models; scales cost per replica.
- **`latency`** — Time-to-first-token matters more than aggregate throughput.
- **`throughput`** — Sustained batch generation.

Quantization, hardware, and GPU count are fixed for the life of a deployment. To move a running
model onto a different profile, create a new deployment with the new config and
[shift traffic](traffic-routing.md) over.

## Decoding optimizations

Speculative decoding and other decoding optimizations are properties of the config, not the
deployment. When a config declares a speculative-decoding draft, list/get responses include
`draftModel` (the draft model's resource name); configs without it omit the field. You cannot set a
speculator on the deployment.

Speculative decoding raises average throughput but can add tail-latency spikes. Latency-sensitive
workloads should pick a `latency`-optimization config instead.

The config's `optimization` selector — `balanced`, `throughput`, or `latency` — sets the serving
profile. Together publishes new config revisions over time (with new `cr_...` IDs); a deployment
pins its revision, so hardware and engine don't change underneath it.
