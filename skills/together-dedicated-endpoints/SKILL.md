---
name: together-dedicated-endpoints
description: Deploy models on dedicated single-tenant GPU endpoints via Together AI for predictable performance, no rate limits, autoscaling, and custom hardware. Supports 179+ models including fine-tuned and custom uploaded models across chat, image, audio, embedding, and moderation categories. Use when users need dedicated inference endpoints, always-on model hosting, production deployments with SLAs, custom or fine-tuned model deployment, or scaling beyond serverless limits.
---

# Together Dedicated Endpoints

## Overview

Deploy models as dedicated endpoints with custom hardware and scaling. Benefits over serverless:
- Predictable performance unaffected by shared traffic
- No rate limits -- scale with replica count
- 179+ models supported across chat, image, audio, transcription, moderation, and rerank
- Fine-tuned and custom uploaded models supported
- Autoscaling, speculative decoding, and prompt caching

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together # for quick install without setting project
```

```shell
# or with pip
pip install together
```

```shell
# TypeScript / JavaScript
npm install together-ai
```

Set your API key:

```shell
export TOGETHER_API_KEY=<your-api-key>
```

## Workflow

1. Select a model (browse dedicated models or upload your own)
2. Check hardware options for that model
3. Create the endpoint with hardware and scaling config
4. Wait for READY state
5. Send inference requests using the endpoint name
6. Stop/delete when done to avoid charges

## Quick Start

### Check Available Hardware

```python
from together import Together
client = Together()

response = client.endpoints.list_hardware(model="Qwen/Qwen3.5-9B-FP8")
for hw in response.data:
    status = hw.availability.status if hw.availability else "unknown"
    price = hw.pricing.cents_per_minute if hw.pricing else "N/A"
    print(f"  {hw.id}  ({status}, {price}c/min)")
```

```typescript
import Together from "together-ai";
const together = new Together();

const hardware = await together.endpoints.listHardware({
  model: "Qwen/Qwen3.5-9B-FP8",
});
console.log(hardware);
```

```shell
curl "https://api.together.xyz/v1/hardware?model=Qwen/Qwen3.5-9B-FP8" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

```shell
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8 --available
```

### Create an Endpoint

```python
from together import Together
client = Together()

endpoint = client.endpoints.create(
    display_name="My Qwen Endpoint",
    model="Qwen/Qwen3.5-9B-FP8",
    hardware="1x_nvidia_h100_80gb_sxm",
    autoscaling={"min_replicas": 1, "max_replicas": 3},
)
print(endpoint.id)    # endpoint-xxxxxxxx for management
print(endpoint.name)  # account/model-name-hash for inference
```

```typescript
import Together from "together-ai";
const together = new Together();

const endpoint = await together.endpoints.create({
  model: "Qwen/Qwen3.5-9B-FP8",
  hardware: "1x_nvidia_h100_80gb_sxm",
  autoscaling: {
    min_replicas: 1,
    max_replicas: 3,
  },
});
console.log(endpoint.id);
```

```shell
curl -X POST "https://api.together.xyz/v1/endpoints" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-9B-FP8",
    "hardware": "1x_nvidia_h100_80gb_sxm",
    "display_name": "My Qwen Endpoint",
    "autoscaling": {
      "min_replicas": 1,
      "max_replicas": 3
    }
  }'
```

```shell
together endpoints create \
  --model Qwen/Qwen3.5-9B-FP8 \
  --hardware 1x_nvidia_h100_80gb_sxm \
  --display-name "My Qwen Endpoint" \
  --min-replicas 1 --max-replicas 3 \
  --wait
```

### Send Inference Requests

Use the **endpoint name** (not ID) as the `model` parameter:

```python
response = client.chat.completions.create(
    model="your-account/Qwen/Qwen3.5-9B-FP8-bb04c904",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

```typescript
const response = await together.chat.completions.create({
  model: "your-account/Qwen/Qwen3.5-9B-FP8-bb04c904",
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(response.choices[0].message.content);
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-account/Qwen/Qwen3.5-9B-FP8-bb04c904",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Manage Endpoints

```python
# Get endpoint status
endpoint = client.endpoints.retrieve("endpoint-abc123")
print(endpoint.state)

# List your endpoints
response = client.endpoints.list()
for ep in response.data:
    print(f"{ep.id}: {ep.model} ({ep.state})")

# Start / Stop
client.endpoints.update("endpoint-abc123", state="STARTED")
client.endpoints.update("endpoint-abc123", state="STOPPED")

# Update replicas
client.endpoints.update(
    "endpoint-abc123",
    autoscaling={"min_replicas": 2, "max_replicas": 4},
)

# Delete
client.endpoints.delete("endpoint-abc123")
```

```typescript
import Together from "together-ai";
const together = new Together();

// Get endpoint status
const endpoint = await together.endpoints.retrieve("endpoint-abc123");
console.log(endpoint.state);

// List your endpoints
const endpoints = await together.endpoints.list();
for (const ep of endpoints.data) {
  console.log(ep);
}

// Start / Stop
await together.endpoints.update("endpoint-abc123", { state: "STARTED" });
await together.endpoints.update("endpoint-abc123", { state: "STOPPED" });

// Update replicas
await together.endpoints.update("endpoint-abc123", {
  autoscaling: { min_replicas: 2, max_replicas: 4 },
});

// Delete
await together.endpoints.delete("endpoint-abc123");
```

```shell
# Get endpoint status
curl "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# Stop endpoint
curl -X PATCH "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "STOPPED"}'

# Start endpoint
curl -X PATCH "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "STARTED"}'

# Delete endpoint
curl -X DELETE "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

```shell
# CLI management commands
together endpoints retrieve <ENDPOINT_ID>
together endpoints list --mine
together endpoints list --mine --type dedicated
together endpoints list --mine --type dedicated --usage-type on-demand
together endpoints start <ENDPOINT_ID>
together endpoints start <ENDPOINT_ID> --wait
together endpoints stop <ENDPOINT_ID>
together endpoints stop <ENDPOINT_ID> --wait
together endpoints delete <ENDPOINT_ID>

# Update replicas (both min and max required together)
together endpoints update --min-replicas 2 --max-replicas 4 <ENDPOINT_ID>
```

## Deploy Fine-tuned Models

Deploy LoRA or full fine-tuned models on dedicated endpoints. First, find the model output name
from your fine-tuning job:

```shell
together fine-tuning list
```

Then deploy:

```python
from together import Together
client = Together()

endpoint = client.endpoints.create(
    display_name="Fine-tuned Qwen3-8B",
    model="your-username/Qwen3-8B-your-suffix",
    hardware="4x_nvidia_h100_80gb_sxm",
    autoscaling={"min_replicas": 1, "max_replicas": 1},
)
print(endpoint.id)
```

```typescript
import Together from "together-ai";
const together = new Together();

const endpoint = await together.endpoints.create({
  model: "your-username/Qwen3-8B-your-suffix",
  hardware: "4x_nvidia_h100_80gb_sxm",
  autoscaling: { min_replicas: 1, max_replicas: 1 },
});
console.log(endpoint.id);
```

```shell
together endpoints create \
  --model <your-model-output-name> \
  --hardware 4x_nvidia_h100_80gb_sxm \
  --display-name "My Fine-tuned Endpoint" \
  --wait
```

Once deployed, send inference requests using the endpoint name just like any other endpoint.
The fine-tuned model must be based on a supported base model.

## Deploy Custom Models

Upload models from Hugging Face or S3 and deploy them on dedicated endpoints.
Requirements: Hugging Face-compatible format, text generation or embedding type, fits on a
single node.

### Upload from Hugging Face

```python
from together import Together
client = Together()

response = client.models.upload(
    model_name="my-custom-model",
    model_source="https://huggingface.co/your-org/your-model",
    hf_token="hf_...",
)
print(response.data.job_id)
```

```shell
together models upload \
  --model-name my-custom-model \
  --model-source https://huggingface.co/your-org/your-model \
  --hf-token $HF_TOKEN
```

### Upload from S3

Archive model files at the root of a `.zip`, `.tar`, or `.tar.gz`. The presigned URL must have
at least 100 minutes of validity.

```python
response = client.models.upload(
    model_name="my-s3-model",
    model_source="https://my-bucket.s3.amazonaws.com/model.tar.gz?...",
)
print(response.data.job_id)
```

```shell
together models upload \
  --model-name my-s3-model \
  --model-source "$PRESIGNED_URL"
```

### Deploy the Uploaded Model

After the upload job completes, deploy as a dedicated endpoint:

```shell
together models list              # Verify model appears
together endpoints hardware --model <model-name>  # Check hardware options
together endpoints create \
  --model <model-name> \
  --hardware 2x_nvidia_h100_80gb_sxm \
  --display-name "My Custom Endpoint" \
  --no-speculative-decoding \
  --wait
```

## Model Discovery

Find models available for dedicated endpoints:

```shell
# List all dedicated-eligible models
together models list --type dedicated

# Check hardware for a specific model
together endpoints hardware --model <model-id>
together endpoints hardware --model <model-id> --available
```

```python
from together import Together
client = Together()

# List all models (use API query param ?dedicated=true to filter)
models = client.models.list()
for model in models:
    print(model.id)
```

See [references/dedicated-models.md](references/dedicated-models.md) for the full list of
dedicated-eligible models.

## Key Concepts

### Hardware Format

Format: `{gpu-count}x_nvidia_{gpu-type}_{vram}_{link}`

Example: `1x_nvidia_h100_80gb_sxm`

Available GPU types include H100 (80GB SXM), A100 (80GB SXM), A100 (80GB PCIe), L40, and
RTX-6000. Use `together endpoints hardware` to get current options and pricing.

### Endpoint Name vs ID

- **Endpoint ID** (e.g., `endpoint-e6c6b82f-...`): For management (start/stop/update/delete)
- **Endpoint Name** (e.g., `account/model-hash`): For inference requests as `model` parameter

Both can be used for inference, but the endpoint name is the standard approach.

### Autoscaling

Set `min_replicas` and `max_replicas`. When max > min, auto-scales based on load.
More GPUs per replica = higher throughput, lower latency. More replicas = higher max QPS.

### Auto-Shutdown

Endpoints auto-stop after 1 hour of inactivity by default. Set `inactive_timeout` in the API
to customize (in minutes). Set to `0` or `null` to disable auto-shutdown.

### Speculative Decoding

Disabled by default. Improves average throughput but may increase tail latency.
Enable by omitting `--no-speculative-decoding` when creating via CLI or setting
`disable_speculative_decoding=false` in the API.

Best for general workloads. Avoid for latency-sensitive real-time applications.

### Prompt Caching

Always enabled for all dedicated endpoints and cannot be disabled. Caches previously processed
prompts to reduce latency on repeated inputs.

### Availability Zones

```shell
together endpoints availability-zones  # List available zones
together endpoints create --availability-zone us-central-4b ...
```

Only specify if you have geographic/latency requirements -- restricting zones limits hardware
availability.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Hardware unavailable | Try a different comparable model or retry later |
| Endpoint queued (not starting) | Reduce `min_replicas` to match available capacity |
| Low replica scaling | Not enough hardware for max replicas; reduce max or wait |
| Model not supported | Must be a dedicated-eligible model; `together models list --type dedicated` |
| Fine-tuned model won't deploy | Base model must be a supported dedicated endpoint model |

## Billing

Charged per minute while the endpoint is running, even when idle. Stop the endpoint to pause
charges. No charge during spin-up or for failed deployments. Price varies by hardware
configuration -- check `cents_per_minute` from the hardware API.

## Resources

- **Hardware configs**: See [references/hardware-options.md](references/hardware-options.md)
- **Full API reference**: See [references/api-reference.md](references/api-reference.md)
- **Dedicated models list**: See [references/dedicated-models.md](references/dedicated-models.md)
- **Runnable scripts**: See [scripts/](scripts/) for Python and TypeScript examples
- **Official docs**: [Dedicated Endpoints](https://docs.together.ai/docs/dedicated-inference)
- **API reference**: [Endpoints API](https://docs.together.ai/reference/createendpoint)
- **Custom models**: [Upload & Deploy](https://docs.together.ai/docs/custom-models)
