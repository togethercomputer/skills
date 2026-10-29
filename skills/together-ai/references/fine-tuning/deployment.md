# Fine-tuned Model Deployment Reference
## Contents

- [Deployment Options](#deployment-options)
- [Training Parameters](#training-parameters)
- [Job Monitoring](#job-monitoring)
- [Continued Fine-tuning](#continued-fine-tuning)
- [Pricing](#pricing)


## Deployment Options

### Option 1: Dedicated Model Inference

A completed job is already a private model in your project, so it deploys on dedicated model
inference (DMI) with no upload step. Deploy it by its model object ID (`ml_...`): `model_object_id`
in `tg fine-tuning retrieve`, or `job.api_model_object_id` in the Python SDK. `model_output_name`
(`x_model_output_name` in the SDK) is not a deployable identifier. This needs `together` 3.x and CLI
3.x. In 2.x, `client.endpoints.create(model=..., hardware=...)` and `tg endpoints create` call the
retired v1 API, which returns HTTP 403 `endpoints_v1_create_access_disabled`. Scaling, traffic
splits, and teardown details are in `domains/dedicated-model-inference.md`.

The CLI creates the endpoint, attaches a deployment, and routes all traffic to it in one step:

```shell
tg fine-tuning retrieve ft-abc123                # copy model_object_id (ml_...)
tg endpoints deploy ml_abc123 --endpoint my-finetuned-endpoint
tg endpoints get dep_abc123 --json | jq -r '.status.state'   # until DEPLOYMENT_STATE_READY
tg endpoints rm ep_abc123 --force                # tear down: scales to zero, then deletes
```

`deploy` also accepts the full `model_object_name` (`<project_slug>/<model_name>`). If it reports
more than one config, rerun it with `--config cr_...` (list them with `tg models configs
ml_abc123`).

The SDK has no single deploy call, so it runs the same steps. Every `client.endpoints` and
`client.models` call takes `project_id` (or reads `TOGETHER_PROJECT_ID`), and models and configs are
passed as resource names:

```python
import time

from together import Together

client = Together()
identity = client.whoami()
if identity.type != "project_api_key":
    raise SystemExit("TOGETHER_API_KEY must be a project API key")
project_id = identity.project.id

job = client.fine_tuning.retrieve(id="ft-abc123")
if not job.api_model_object_id:
    raise SystemExit("No model_object_id: the job is not completed or its upload failed")
model = client.models.retrieve(job.api_model_object_id, project_id=project_id)

# Configs are published for the base model. If there is more than one, choose by
# config.selectors (accelerator_type, accelerator_count, optimization).
configs = list(
    client.models.configs.list(
        project_id=project_id,
        reference_model=model.base_model or f"projects/{model.project_id}/models/{model.id}",
    )
)
config = configs[0]

endpoint = client.endpoints.create(project_id=project_id, name="my-finetuned-endpoint")
deployment = client.endpoints.deployments.create(
    endpoint.id,
    project_id=project_id,
    name="my-finetuned-deployment",
    model=f"projects/{model.project_id}/models/{model.id}",
    # Use the config's own project: public configs can belong to another project.
    config=f"projects/{config.project_id}/configs/{config.id}",
    autoscaling={"min_replicas": 1, "max_replicas": 1},
)
# A READY deployment serves nothing until it is in the endpoint's traffic split.
client.endpoints.update(
    endpoint.id,
    project_id=project_id,
    traffic_split=[{"deployment_id": deployment.id, "weight": 1}],
)

while True:
    current = client.endpoints.deployments.retrieve(
        deployment.id, project_id=project_id, endpoint_id=endpoint.id
    )
    print(f"  State: {current.status.state}")
    if current.status.state == "DEPLOYMENT_STATE_READY":
        break
    if current.status.state == "DEPLOYMENT_STATE_FAILED":
        raise SystemExit(current.status.message)
    time.sleep(15)

# Inference takes the endpoint string (endpoint.name, "<project_slug>/<endpoint_name>")
# on the inference base URL, not the model ID. SDK 3.x base URLs omit /v1.
inference_client = Together(base_url="https://api-inference.together.ai")
response = inference_client.chat.completions.create(
    model=endpoint.name,
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=128,
)
print(response.choices[0].message.content)
```

To stop billing, scale the deployment to zero. To delete it, wait for `DEPLOYMENT_STATE_STOPPED`,
drop its traffic weight, then delete the deployment and the endpoint:

```python
client.endpoints.deployments.update(
    deployment.id,
    project_id=project_id,
    endpoint_id=endpoint.id,
    autoscaling={"min_replicas": 0, "max_replicas": 0},
)
# Once the deployment is DEPLOYMENT_STATE_STOPPED:
client.endpoints.update(
    endpoint.id,
    project_id=project_id,
    traffic_split=[{"deployment_id": deployment.id, "weight": 0}],
)
client.endpoints.deployments.delete(
    deployment.id, project_id=project_id, endpoint_id=endpoint.id
)
client.endpoints.delete(endpoint.id, project_id=project_id)
```

- Bills per minute per running replica, even when idle. Scale to zero or delete when done.
- Reserved single-tenant GPUs with no hard rate limits.
- Deploys only if the base model is supported for dedicated inference. Check the
  [supported models](https://docs.together.ai/docs/dedicated-endpoints/models) before training.
  `-Reference` base models often can't be deployed.
- A 404 on inference means the wrong host or `model`: OpenAI-compatible clients and curl use
  `https://api-inference.together.ai/v1`, and `model` is the endpoint string, not the `ml_...` ID.

### Option 2: Download Weights

Download the weights to run them locally or on your own infrastructure.

```shell
tg fine-tuning download ft-abc123                              # final weights
tg fine-tuning download ft-abc123 --output-dir ./my-model
tg fine-tuning download ft-abc123 --checkpoint-step 48         # an intermediate checkpoint
tg fine-tuning download ft-abc123 --checkpoint-type adapter    # LoRA jobs: adapter weights only
```

| Option | Description |
|---|---|
| `--output-dir`, `-o` | Directory to save the archive in. |
| `--checkpoint-step`, `-s` | Checkpoint step to download, from `tg fine-tuning list-checkpoints`. Defaults to the final weights. `ft-abc123:48` is shorthand. |
| `--checkpoint-type`, `-c` | `default`, `merged`, or `adapter`. `default` resolves to `merged` for LoRA jobs and to the full weights for full fine-tunes. `merged` and `adapter` apply to LoRA jobs only. |

The Python SDK call is `fine_tuning.content`, which returns the archive as a binary response. Pass
`checkpoint` explicitly unless you set `checkpoint_step`, which overrides it:

```python
response = client.fine_tuning.content(ft_id="ft-abc123", checkpoint="merged")
response.write_to_file("my-model/model.tar.zst")
```

| Job type | `checkpoint` values | What you get |
|---|---|---|
| LoRA | `merged`, `adapter`, `model_output_path` | `merged`: base model plus adapter as self-contained weights. `adapter`: the LoRA adapter only, to load on the base model yourself (for example, with PEFT or vLLM). |
| Full | `model_output_path` only | The full trained weights. `adapter` returns an error. |

`model_output_path` is the raw training output before any merging. The archive is a `.tar.zst`
([Zstandard](https://github.com/facebook/zstd)), so decompress it before extracting:

```shell
zstd -d model.tar.zst      # macOS: brew install zstd
tar -xvf model.tar
```

## Training Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | Required | Base model |
| `training_file` | string | Required | File ID from upload |
| `validation_file` | string | - | Optional validation file |
| `suffix` | string | - | Custom model name suffix |
| `n_epochs` | int | 1-3 | Training epochs |
| `n_checkpoints` | int | 1 | Checkpoints to save |
| `batch_size` | int/str | `"max"` | Batch size (or "max" for auto) |
| `learning_rate` | float | ~1e-5 | Learning rate |
| `warmup_ratio` | float | 0 | Warmup step ratio |
| `lora` | bool | true | Use LoRA method |
| `lora_r` | int | 64 | LoRA rank. Per-model max -- 64 for most models; 16 for Moonshot Kimi-K2 family, Z.ai GLM-5/5.1, and DeepSeek R1/V3 (non-distill) families. See [supported-models.md](supported-models.md). |
| `lora_alpha` | int | 16 | LoRA scaling factor |
| `train_on_inputs` | bool/str | "auto" | Train on prompts/user msgs |
| `n_evals` | int | 0 | Validation evaluations (>0 to use validation set) |
| `wandb_api_key` | string | - | W&B integration |
| `from_checkpoint` | string | - | Continue from previous job ID |

### DPO-specific Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `training_method` | string | "sft" | Set to `"dpo"` for preference tuning |
| `dpo_beta` | float | 0.1 | Deviation control (0.05-0.9) |

### VLM-specific Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `train_vision` | bool | false | Update vision encoder weights |

### BYOM-specific Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_hf_model` | string | - | HuggingFace model ID |
| `hf_api_token` | string | - | HuggingFace token (for private repos) |

## Job Monitoring

### Status Flow
`Pending` -> `Queued` -> `Running` -> `Uploading` -> `Completed`

### Python SDK

```python
from together import Together

client = Together()

# Get status
status = client.fine_tuning.retrieve(job_id)
print(status.status)

# List events
events = client.fine_tuning.list_events(id=job_id)
for event in events.data:
    print(event.message)

# List checkpoints
checkpoints = client.fine_tuning.list_checkpoints(id=job_id)
for cp in checkpoints:
    print(f"Step {cp.step}: {cp.metrics}")

# List per-step training metrics (loss, learning rate, grad norm, eval/loss, ...)
metrics = client.fine_tuning.list_metrics(job_id)
for step in metrics.metrics:
    print(step)
```

`list_metrics` accepts optional filters for trimming long runs:

| Parameter | Type | Description |
|-----------|------|-------------|
| `global_step_from` | int | Return only metrics with `global_step` >= this value |
| `global_step_to` | int | Return only metrics with `global_step` <= this value |
| `logged_at_from` | str or datetime | Return only metrics logged at or after this ISO 8601 timestamp |
| `logged_at_to` | str or datetime | Return only metrics logged at or before this ISO 8601 timestamp |
| `resolution` | int | Cap the response at this many uniformly sampled training points (eval metrics are always returned in full) |

Each entry is either a training step (`train/global_step`, `train/loss`, `train/learning_rate`, `train/grad_norm`, ...) or an eval step (`eval/loss`, ...). When both occur at the same step, two separate objects are returned.

### CLI

```shell
together fine-tuning retrieve <JOB_ID>
together fine-tuning list-events <JOB_ID>
together fine-tuning list-checkpoints <JOB_ID>
together fine-tuning list-metrics <JOB_ID>            # ASCII charts (default)
together fine-tuning list-metrics <JOB_ID> --json     # raw JSON output
together fine-tuning list
together fine-tuning cancel <JOB_ID>
together fine-tuning delete <JOB_ID>
```

`list-metrics` also accepts `--global-step-from`, `--global-step-to`, `--logged-at-from`, `--logged-at-to`, and `--resolution` for the same filtering behavior as the Python SDK.

### cURL

```shell
# Retrieve job details
curl "https://api.together.xyz/v1/fine-tunes/ft-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# List events
curl "https://api.together.xyz/v1/fine-tunes/ft-abc123/events" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# List checkpoints
curl "https://api.together.xyz/v1/fine-tunes/ft-abc123/checkpoints" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# Cancel job
curl -X POST "https://api.together.xyz/v1/fine-tunes/ft-abc123/cancel" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# Delete job
curl -X DELETE "https://api.together.xyz/v1/fine-tunes/ft-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## Continued Fine-tuning

Resume from a previous job's checkpoint:

```python
response = client.fine_tuning.create(
    training_file=new_file_id,
    model="Qwen/Qwen3-8B",
    from_checkpoint=previous_job_id,
)
```

## Pricing

- Based on total tokens processed: `total_tokens x per_token_rate`
- `total_tokens = (n_epochs x training_tokens) + (n_evals x validation_tokens)`
- Cost varies by model size, method (LoRA vs Full), and type (SFT vs DPO)
- No minimum price -- pay only for tokens processed
- Exact token count and price available after tokenization via dashboard or
  `together fine-tuning retrieve $JOB_ID`
- Dedicated endpoint hosting charges are separate (per-minute while running)
