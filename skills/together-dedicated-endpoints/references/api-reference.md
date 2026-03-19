# Dedicated Endpoints API Reference

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /endpoints` | Create endpoint | Deploy a new dedicated endpoint |
| `GET /endpoints` | List endpoints | List all endpoints |
| `GET /endpoints/{id}` | Get endpoint | Get endpoint details |
| `PATCH /endpoints/{id}` | Update endpoint | Update config/scaling |
| `DELETE /endpoints/{id}` | Delete endpoint | Remove endpoint |
| `GET /hardware` | List hardware | Available hardware configs |
| `POST /models` | Upload model | Upload custom model |
| `GET /models` | List models | List available models |

Base URL: `https://api.together.xyz/v1`

## Create Endpoint

```python
endpoint = client.endpoints.create(
    model="Qwen/Qwen3.5-9B-FP8",
    hardware="1x_nvidia_h100_80gb_sxm",
    display_name="My Endpoint",
    autoscaling={"min_replicas": 1, "max_replicas": 3},
    inactive_timeout=60,  # minutes, 0 or None to disable
)
print(endpoint.id)  # endpoint-abc123
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
    "display_name": "My Endpoint",
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
  --display-name "My Endpoint" \
  --min-replicas 1 --max-replicas 3 \
  --wait
```

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model to deploy |
| `hardware` | string | Yes | - | Hardware config ID |
| `autoscaling` | object | Yes | - | `{min_replicas, max_replicas}` |
| `display_name` | string | No | - | Human-readable name |
| `disable_speculative_decoding` | bool | No | false | Disable spec decoding |
| `state` | string | No | `"STARTED"` | `"STARTED"` or `"STOPPED"` |
| `inactive_timeout` | int/null | No | 60 | Minutes before auto-stop (0/null disables) |
| `availability_zone` | string | No | - | Preferred zone |

## Get Endpoint

```python
endpoint = client.endpoints.retrieve("endpoint-abc123")
print(endpoint.state)
```

```typescript
const endpoint = await together.endpoints.retrieve("endpoint-abc123");
console.log(endpoint);
```

```shell
curl "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

```shell
together endpoints retrieve <ENDPOINT_ID>
together endpoints retrieve <ENDPOINT_ID> --json
```

## List Endpoints

```python
response = client.endpoints.list()
for ep in response.data:
    print(ep.id)
```

```typescript
const endpoints = await together.endpoints.list();
for (const endpoint of endpoints.data) {
  console.log(endpoint);
}
```

```shell
curl "https://api.together.xyz/v1/endpoints" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"

# Filter by type and ownership
curl "https://api.together.xyz/v1/endpoints?type=dedicated&mine=true" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

```shell
together endpoints list --mine
together endpoints list --type dedicated
together endpoints list --mine --type dedicated --usage-type on-demand
together endpoints list --json
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by `dedicated` or `serverless` |
| `usage_type` | string | Filter by `on-demand` or `reserved` |
| `mine` | boolean | Only endpoints owned by the caller |

## Endpoint States

| State | Description |
|-------|-------------|
| `PENDING` | Waiting for resources |
| `STARTING` | Initializing |
| `STARTED` | Running, accepting requests |
| `STOPPING` | Shutting down |
| `STOPPED` | Not running |
| `ERROR` | Failed |

## Update Endpoint

```python
client.endpoints.update(
    "endpoint-abc123",
    autoscaling={"min_replicas": 2, "max_replicas": 5},
    display_name="Updated Name",
)
```

```typescript
await together.endpoints.update("endpoint-abc123", {
  autoscaling: { min_replicas: 2, max_replicas: 5 },
  display_name: "Updated Name",
});
```

```shell
curl -X PATCH "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "autoscaling": {
      "min_replicas": 2,
      "max_replicas": 5
    },
    "display_name": "Updated Name"
  }'
```

```shell
together endpoints update --min-replicas 2 --max-replicas 5 <ENDPOINT_ID>
together endpoints update --display-name "Updated Name" <ENDPOINT_ID>
```

### Updatable Fields

- `display_name`
- `state` (`"STARTED"` or `"STOPPED"`)
- `autoscaling`
- `inactive_timeout`

## Start / Stop

```python
# Start
client.endpoints.update("endpoint-abc123", state="STARTED")

# Stop
client.endpoints.update("endpoint-abc123", state="STOPPED")
```

```typescript
// Start
await together.endpoints.update("endpoint-abc123", { state: "STARTED" });

// Stop
await together.endpoints.update("endpoint-abc123", { state: "STOPPED" });
```

```shell
# Start
curl -X PATCH "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "STARTED"}'

# Stop
curl -X PATCH "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "STOPPED"}'
```

```shell
together endpoints start <ENDPOINT_ID>
together endpoints start <ENDPOINT_ID> --wait
together endpoints stop <ENDPOINT_ID>
together endpoints stop <ENDPOINT_ID> --wait
```

## Delete

Returns HTTP 204 on success.

```python
client.endpoints.delete("endpoint-abc123")
```

```typescript
await together.endpoints.delete("endpoint-abc123");
```

```shell
curl -X DELETE "https://api.together.xyz/v1/endpoints/endpoint-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

```shell
together endpoints delete <ENDPOINT_ID>
```

## List Hardware

```python
response = client.endpoints.list_hardware()
for hw in response.data:
    print(hw.id)

# Filter by model
response = client.endpoints.list_hardware(model="Qwen/Qwen3.5-9B-FP8")
for hw in response.data:
    price = hw.pricing.cents_per_minute if hw.pricing else "N/A"
    print(f"{hw.id}: {hw.specs.gpu_count}x {hw.specs.gpu_type} @ {price}c/min")
```

```typescript
const hardware = await together.endpoints.listHardware();
console.log(hardware);
```

```shell
curl "https://api.together.xyz/v1/hardware" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"

# Filter by model
curl "https://api.together.xyz/v1/hardware?model=Qwen/Qwen3.5-9B-FP8" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

```shell
together endpoints hardware
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8 --available
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8 --json
```

### Hardware Response Object

```json
{
  "object": "hardware",
  "id": "1x_nvidia_h100_80gb_sxm",
  "pricing": { "cents_per_minute": 6.0 },
  "specs": {
    "gpu_type": "h100",
    "gpu_link": "sxm",
    "gpu_memory": 80,
    "gpu_count": 1
  },
  "availability": { "status": "available" },
  "updated_at": "2025-01-15T14:30:00Z"
}
```

## Upload Model

```python
response = client.models.upload(
    model_name="my-custom-model",
    model_source="https://huggingface.co/your-org/your-model",
    hf_token="hf_...",
)
print(response.data.job_id)
```

```typescript
const response = await client.models.upload({
  model_name: "my-custom-model",
  model_source: "https://huggingface.co/your-org/your-model",
});
console.log(response);
```

```shell
curl -X POST "https://api.together.xyz/v1/models" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "my-custom-model",
    "model_source": "https://huggingface.co/your-org/your-model",
    "hf_token": "hf_..."
  }'
```

```shell
together models upload \
  --model-name my-custom-model \
  --model-source https://huggingface.co/your-org/your-model \
  --hf-token $HF_TOKEN
```

### Upload Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_name` | string | Yes | Name for the uploaded model |
| `model_source` | string | Yes | Hugging Face repo URL or S3 presigned URL |
| `model_type` | string | No | `"model"` (default) or `"adapter"` |
| `hf_token` | string | No | Hugging Face token for private repos |
| `description` | string | No | Model description |
| `base_model` | string | No | Base model for adapters (serverless) |
| `lora_model` | string | No | LoRA pool for adapters (dedicated) |

### Upload Response

```json
{
  "data": {
    "job_id": "job-b641db51-38e8-40f2-90a0-5353aeda6f21",
    "model_name": "devuser/my-custom-model",
    "model_source": "remote_archive"
  },
  "message": "job created"
}
```

### Check Upload Status

```shell
curl "https://api.together.xyz/v1/jobs/<job_id>" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## List Models

```python
models = client.models.list()
for model in models:
    print(model.id)
```

```shell
# All models
curl "https://api.together.xyz/v1/models" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"

# Dedicated-eligible models only
curl "https://api.together.xyz/v1/models?dedicated=true" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json"
```

```shell
together models list
together models list --type dedicated
together models list --json
```

## Using the Endpoint

Once STARTED, use the Chat Completions API with either the endpoint **name** or **ID**:

```python
response = client.chat.completions.create(
    model="endpoint-abc123",  # or endpoint name
    messages=[{"role": "user", "content": "Hello!"}],
)
```

```typescript
const response = await together.chat.completions.create({
  model: "endpoint-abc123",  // or endpoint name
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(response.choices[0].message.content);
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "endpoint-abc123",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## CLI Reference

### Endpoint Commands

| Command | Description |
|---------|-------------|
| `together endpoints create` | Create a new endpoint |
| `together endpoints retrieve <ID>` | Get endpoint details |
| `together endpoints list` | List endpoints |
| `together endpoints update <ID>` | Update endpoint config |
| `together endpoints start <ID>` | Start a stopped endpoint |
| `together endpoints stop <ID>` | Stop a running endpoint |
| `together endpoints delete <ID>` | Delete an endpoint |
| `together endpoints hardware` | List available hardware |
| `together endpoints availability-zones` | List availability zones |

### Model Commands

| Command | Description |
|---------|-------------|
| `together models upload` | Upload a custom model |
| `together models list` | List available models |

### Create Options

| Flag | Description |
|------|-------------|
| `--model` | (required) Model to deploy |
| `--hardware` | (required) Hardware config ID |
| `--min-replicas` | Minimum replica count |
| `--max-replicas` | Maximum replica count |
| `--display-name` | Human-readable name |
| `--no-auto-start` | Create in STOPPED state |
| `--no-speculative-decoding` | Disable speculative decoding |
| `--availability-zone` | Preferred availability zone |
| `--wait` | Wait for endpoint to be ready |
| `--json` | Output in JSON format |

### List Options

| Flag | Description |
|------|-------------|
| `--mine` | Show only your endpoints |
| `--type` | Filter by `dedicated` or `serverless` |
| `--usage-type` | Filter by `on-demand` or `reserved` |
| `--json` | Output in JSON format |

### Hardware Options

| Flag | Description |
|------|-------------|
| `--model` | Filter by model compatibility |
| `--available` | Show only available hardware (requires `--model`) |
| `--json` | Output in JSON format |

### Upload Options

| Flag | Description |
|------|-------------|
| `--model-name` | (required) Name for the uploaded model |
| `--model-source` | (required) HF repo URL or S3 presigned URL |
| `--model-type` | `model` or `adapter` |
| `--hf-token` | Hugging Face API token |
| `--description` | Model description |
| `--base-model` | Base model for adapters (serverless) |
| `--lora-model` | LoRA pool for adapters (dedicated) |
| `--json` | Output in JSON format |

## Endpoint Response Object

```json
{
  "object": "endpoint",
  "id": "endpoint-d23901de-ef8f-44bf-b3e7-de9c1ca8f2d7",
  "name": "devuser/Qwen/Qwen3.5-9B-FP8-a32b82a1",
  "display_name": "My Endpoint",
  "model": "Qwen/Qwen3.5-9B-FP8",
  "hardware": "1x_nvidia_h100_80gb_sxm",
  "type": "dedicated",
  "owner": "devuser",
  "state": "STARTED",
  "autoscaling": { "min_replicas": 1, "max_replicas": 3 },
  "created_at": "2025-02-04T10:43:55.405Z"
}
```
