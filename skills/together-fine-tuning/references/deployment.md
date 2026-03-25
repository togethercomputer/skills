# Fine-tuned Model Deployment Reference
## Contents

- [Deployment Options](#deployment-options)
- [Training Parameters](#training-parameters)
- [Job Monitoring](#job-monitoring)
- [Continued Fine-tuning](#continued-fine-tuning)
- [Pricing](#pricing)


## Deployment Options

### Option 1: Dedicated Endpoint

Deploy your fine-tuned model on a dedicated endpoint for production use.

```python
endpoint = client.endpoints.create(
    display_name="Fine-tuned Model",
    model="your-username/Model-Name-your-suffix",
    hardware="4x_nvidia_h100_80gb_sxm",
    autoscaling={"min_replicas": 1, "max_replicas": 1},
)
print(endpoint)

# Query the endpoint
response = client.chat.completions.create(
    model="your-username/Model-Name-your-suffix",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=128,
)
print(response.choices[0].message.content)
```

- Per-minute hosting charges while running
- Guaranteed capacity and latency
- No rate limits, high max load
- Supports both LoRA and Full fine-tuned models

### Option 2: Download Weights

Download and run locally or on your infrastructure.

```python
client.fine_tuning.download(
    id="ft-abc123",
    output="my-model/model.tar.zst",
)
```

```shell
# CLI: download model weights
together fine-tuning download ft-abc123

# Download to a specific directory
together fine-tuning download ft-abc123 --output_dir ./my-model

# Download a specific checkpoint step
together fine-tuning download ft-abc123 --checkpoint-step 48

# Download merged or adapter-only weights (LoRA jobs)
together fine-tuning download ft-abc123 --checkpoint-type merged
together fine-tuning download ft-abc123 --checkpoint-type adapter
```

```shell
# Extract the downloaded archive
tar -xf model-name.tar.zst
```

Options:
- `--output_dir`, `-o` -- Specify the output directory
- `--checkpoint-step`, `-s` -- Download a specific checkpoint's weights (default: latest)
- `--checkpoint-type` -- `default`, `merged`, or `adapter` (merged/adapter only for LoRA jobs)

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
| `lora_r` | int | 64 | LoRA rank |
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
```

### CLI

```shell
together fine-tuning retrieve <JOB_ID>
together fine-tuning list-events <JOB_ID>
together fine-tuning list-checkpoints <JOB_ID>
together fine-tuning list
together fine-tuning cancel <JOB_ID>
together fine-tuning delete <JOB_ID>
```

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
