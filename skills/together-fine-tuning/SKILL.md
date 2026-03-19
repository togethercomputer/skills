---
name: together-fine-tuning
description: Fine-tune open-source LLMs on Together AI with LoRA, Full fine-tuning, DPO preference tuning, VLM (vision-language) fine-tuning, reasoning fine-tuning, function calling fine-tuning, and Bring Your Own Model (BYOM). Supports 100+ models including Qwen3, Llama 3/4, DeepSeek, Gemma 3, GLM, Kimi K2.5, Mistral. Use when users want to train, fine-tune, customize, adapt, or specialize language models on custom data.
---

# Together Fine-Tuning

## Overview

Fine-tune models on Together AI with a complete workflow: prepare data, upload, train, monitor, deploy.

**Methods:**
- **LoRA** (recommended): Trains small subset of weights -- faster, cheaper
- **Full fine-tuning**: Updates all weights -- maximum customization, higher cost
- **DPO (Preference)**: Trains on preferred vs non-preferred output pairs
- **VLM fine-tuning**: Fine-tune vision-language models on image+text data
- **Reasoning fine-tuning**: Train models with chain-of-thought reasoning data
- **Function calling fine-tuning**: Train models to reliably invoke tools and structured functions

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together  # for quick installation without new project setup
```

```shell
# or with pip
pip install together
```

Set your API key:

```shell
export TOGETHER_API_KEY=<your-api-key>
```

## Quick Start

### 1. Prepare Data

Conversational format (most common):

```jsonl training_data.jsonl
{"messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "AI is artificial intelligence."}]}
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi! How can I help?"}]}
```

### 2. Upload with Validation

```python
from together import Together
client = Together()

# Upload with validation enabled
file_resp = client.files.upload(file="training_data.jsonl", purpose="fine-tune", check=True)
print(file_resp.id)
```

```shell
# CLI: check and upload
together files check "training_data.jsonl"
together files upload "training_data.jsonl"
```

```shell
# cURL upload
curl "https://api.together.xyz/v1/files/upload" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F "file=@training_data.jsonl" \
  -F "file_name=training_data.jsonl" \
  -F "purpose=fine-tune"
```

### 3. Start LoRA Fine-Tuning (Recommended)

```python
job = client.fine_tuning.create(
    training_file=file_resp.id,
    model="Qwen/Qwen3-8B",
    lora=True,
    n_epochs=3,
    learning_rate=1e-5,
    suffix="my-model-v1",
)
print(f"Job ID: {job.id}")
```

```shell
# CLI
together fine-tuning create \
  --training-file "file-abc123" \
  --model "Qwen/Qwen3-8B" \
  --lora \
  --n-epochs 3 \
  --learning-rate 1e-5 \
  --suffix "my-model-v1"
```

```shell
# cURL
curl -X POST "https://api.together.xyz/v1/fine-tunes" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "training_file": "file-abc123",
    "n_epochs": 3,
    "learning_rate": 1e-5,
    "suffix": "my-model-v1"
  }'
```

### 4. Monitor

```python
status = client.fine_tuning.retrieve(job.id)
print(status.status)  # Pending -> Queued -> Running -> Uploading -> Completed

for event in client.fine_tuning.list_events(id=job.id).data:
    print(event.message)
```

```shell
# CLI: status and events
together fine-tuning retrieve ft-abc123
together fine-tuning list-events ft-abc123
```

```shell
# cURL
curl "https://api.together.xyz/v1/fine-tunes/ft-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

curl "https://api.together.xyz/v1/fine-tunes/ft-abc123/events" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### 5. Use Fine-Tuned Model

**Deploy as a Dedicated Endpoint:**

```python
endpoint = client.endpoints.create(
    display_name="My Fine-tuned Model",
    model=job.output_name,
    hardware="4x_nvidia_h100_80gb_sxm",
    autoscaling={"min_replicas": 1, "max_replicas": 1},
)

# Query the endpoint
response = client.chat.completions.create(
    model=job.output_name,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

**Download weights** (run locally):

```python
client.fine_tuning.download(id=job.id, output="my-model/model.tar.zst")
```

```shell
# CLI
together fine-tuning download ft-abc123
together fine-tuning download ft-abc123 --output_dir ./my-model
together fine-tuning download ft-abc123 --checkpoint-step 48
together fine-tuning download ft-abc123 --checkpoint-type merged   # or: adapter
```

## Full Fine-Tuning

Updates all model weights. Omit the `lora` parameter or set `lora=False`:

```python
job = client.fine_tuning.create(
    training_file=file_resp.id,
    model="Qwen/Qwen3-8B",
    lora=False,
    n_epochs=3,
    learning_rate=1e-5,
    suffix="full-ft-v1",
)
```

```shell
# CLI: use --no-lora for full fine-tuning
together fine-tuning create \
  --training-file "file-abc123" \
  --model "Qwen/Qwen3-8B" \
  --no-lora \
  --n-epochs 3 \
  --learning-rate 1e-5
```

## DPO Preference Fine-Tuning

Provide paired preferred/non-preferred outputs:

```jsonl preference_data.jsonl
{"input": {"messages": [{"role": "user", "content": "Explain AI"}]}, "preferred_output": [{"role": "assistant", "content": "AI is a broad field..."}], "non_preferred_output": [{"role": "assistant", "content": "It means computers."}]}
```

```python
job = client.fine_tuning.create(
    training_file=preference_file_id,
    model="meta-llama/Llama-3.2-3B-Instruct",
    training_method="dpo",
    dpo_beta=0.2,
    lora=True,
)
```

Best practice -- run SFT first, then DPO from checkpoint:

```python
dpo_job = client.fine_tuning.create(
    training_file=preference_file_id,
    from_checkpoint=sft_job_id,
    model="meta-llama/Llama-3.2-3B-Instruct",
    training_method="dpo",
    dpo_beta=0.2,
)
```

## VLM Fine-Tuning (Vision-Language)

Fine-tune vision-language models on image+text data. Images must be base64-encoded.

```python
job = client.fine_tuning.create(
    training_file=vlm_file_id,
    model="Qwen/Qwen3-VL-8B-Instruct",
    lora=True,
    train_vision=False,  # Set True to also update vision encoder
)
```

```shell
together fine-tuning create \
  --training-file "file-abc123" \
  --model "Qwen/Qwen3-VL-8B-Instruct" \
  --train-vision false \
  --lora
```

Supported VLM models: `Qwen/Qwen3-VL-8B-Instruct`, `Qwen/Qwen3-VL-30B-A3B-Instruct`,
`Qwen/Qwen3-VL-235B-A22B-Instruct` (LoRA only), `meta-llama/Llama-4-Maverick-17B-128E-Instruct-VLM`
(LoRA only), `meta-llama/Llama-4-Scout-17B-16E-Instruct-VLM` (LoRA only),
`google/gemma-3-4b-it-VLM`, `google/gemma-3-12b-it-VLM`, `google/gemma-3-27b-it-VLM`.

## Function Calling Fine-Tuning

Train models to reliably invoke tools. Dataset includes a `tools` field and assistant messages
with `tool_calls`:

```jsonl function_calling_data.jsonl
{"tools": [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}}}], "messages": [{"role": "user", "content": "Weather in NYC?"}, {"role": "assistant", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "get_weather", "arguments": "{\"city\": \"New York\"}"}}]}, {"role": "tool", "tool_call_id": "call_1", "content": "{\"temp\": 72}"}, {"role": "assistant", "content": "It's 72F in NYC."}]}
```

```python
job = client.fine_tuning.create(
    training_file=fc_file_id,
    model="Qwen/Qwen3-8B",
    lora=True,
)
```

## Reasoning Fine-Tuning

Train models with chain-of-thought reasoning data. Uses conversational format with thinking
content in assistant messages.

Supported models: Qwen3 family (0.6B to 235B), Qwen3-Next-80B-A3B-Thinking, GLM-4.6, GLM-4.7.

```python
job = client.fine_tuning.create(
    training_file=reasoning_file_id,
    model="Qwen/Qwen3-8B",
    lora=True,
)
```

## BYOM (Bring Your Own Model)

Fine-tune any CausalLM model from HuggingFace (the `model` parameter acts as a template for
infrastructure config; `from_hf_model` is your actual model):

```python
job = client.fine_tuning.create(
    model="Qwen/Qwen3-4B",               # Base template (architecture config)
    from_hf_model="my-org/my-custom-model",  # Your HuggingFace model
    training_file=file_id,
    hf_api_token="hf_xxx",               # Optional, for private repos
    suffix="domain-specialist-v1",
)
```

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `model` | Base model to fine-tune | Required |
| `training_file` | Uploaded file ID | Required |
| `validation_file` | Optional validation file ID | None |
| `lora` | LoRA fine-tuning | True |
| `lora_r` | LoRA rank | 64 |
| `lora_alpha` | LoRA scaling factor | 16 |
| `n_epochs` | Training epochs | 1 |
| `learning_rate` | Weight update rate | 1e-5 |
| `batch_size` | Examples per iteration | "max" |
| `train_on_inputs` | Train on user messages/prompts | "auto" |
| `suffix` | Custom model name suffix | None |
| `n_checkpoints` | Checkpoints to save | 1 |
| `warmup_ratio` | Warmup steps ratio | 0 |
| `n_evals` | Validation evaluations (must be >0 to use validation set) | 0 |
| `wandb_api_key` | W&B monitoring | None |
| `training_method` | `"sft"` or `"dpo"` | "sft" |
| `dpo_beta` | DPO deviation control (0.05-0.9) | 0.1 |
| `from_checkpoint` | Continue from previous job ID | None |
| `from_hf_model` | HuggingFace model for BYOM | None |
| `hf_api_token` | HF token for private repos | None |
| `train_vision` | Update vision encoder (VLM only) | False |

## Evaluation

Use a validation set during training:

```python
job = client.fine_tuning.create(
    training_file=train_file_id,
    validation_file=val_file_id,
    n_evals=10,
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Reference",
)
```

## Continue Training

Resume from a previous job's checkpoint:

```python
job = client.fine_tuning.create(
    training_file=new_file_id,
    from_checkpoint=previous_job_id,
    model="Qwen/Qwen3-8B",
)
```

## Manage Jobs

```python
client.fine_tuning.list()                  # List all jobs
client.fine_tuning.retrieve(job_id)        # Get status
client.fine_tuning.list_events(id=job_id)  # Get logs
client.fine_tuning.cancel(id=job_id)       # Cancel
client.fine_tuning.delete(job_id)          # Delete (irreversible)
```

```shell
# CLI
together fine-tuning list
together fine-tuning retrieve ft-abc123
together fine-tuning list-events ft-abc123
together fine-tuning list-checkpoints ft-abc123
together fine-tuning cancel ft-abc123
together fine-tuning delete ft-abc123
```

```shell
# cURL
curl "https://api.together.xyz/v1/fine-tunes" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

curl "https://api.together.xyz/v1/fine-tunes/ft-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

curl "https://api.together.xyz/v1/fine-tunes/ft-abc123/events" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

curl "https://api.together.xyz/v1/fine-tunes/ft-abc123/checkpoints" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

curl -X POST "https://api.together.xyz/v1/fine-tunes/ft-abc123/cancel" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## Pricing

- Based on total tokens processed: `(n_epochs x training_tokens) + (n_evals x validation_tokens)`
- Cost varies by model size, method (LoRA vs Full), and type (SFT vs DPO)
- No minimum price -- you only pay for tokens processed
- Dedicated endpoint hosting charges are separate (per-minute while running)

## Resources

- **Data format details**: See [references/data-formats.md](references/data-formats.md)
- **Supported models**: See [references/supported-models.md](references/supported-models.md)
- **Deployment options**: See [references/deployment.md](references/deployment.md)
- **Runnable scripts (Python)**:
  - [scripts/finetune_workflow.py](scripts/finetune_workflow.py) -- upload, train, monitor, deploy
  - [scripts/dpo_workflow.py](scripts/dpo_workflow.py) -- SFT then DPO preference tuning
  - [scripts/function_calling_finetune.py](scripts/function_calling_finetune.py) -- function calling
    fine-tuning with tool_calls data
  - [scripts/reasoning_finetune.py](scripts/reasoning_finetune.py) -- reasoning fine-tuning with
    chain-of-thought data
  - [scripts/vlm_finetune.py](scripts/vlm_finetune.py) -- vision-language fine-tuning with base64 images
- **Official docs**: [Fine-tuning Quickstart](https://docs.together.ai/docs/fine-tuning-quickstart)
- **Official docs**: [Data Preparation](https://docs.together.ai/docs/fine-tuning-data-preparation)
- **Official docs**: [Fine-tuning Models](https://docs.together.ai/docs/fine-tuning-models)
- **Official docs**: [LoRA Training](https://docs.together.ai/docs/lora-training-and-inference)
- **Official docs**: [VLM Fine-tuning](https://docs.together.ai/docs/fine-tuning-vlm)
- **Official docs**: [Function Calling Fine-tuning](https://docs.together.ai/docs/fine-tuning-function-calling)
- **Official docs**: [Reasoning Fine-tuning](https://docs.together.ai/docs/fine-tuning-reasoning)
- **Official docs**: [Preference Fine-tuning](https://docs.together.ai/docs/preference-fine-tuning)
- **Official docs**: [BYOM](https://docs.together.ai/docs/fine-tuning-byom)
- **Official docs**: [Deploying](https://docs.together.ai/docs/deploying-a-fine-tuned-model)
- **Official docs**: [Pricing](https://docs.together.ai/docs/fine-tuning-pricing)
- **API reference**: [Fine-tuning API](https://docs.together.ai/reference/post-fine-tunes)
- **CLI reference**: [Fine-tuning CLI](https://docs.together.ai/reference/cli/finetune)
