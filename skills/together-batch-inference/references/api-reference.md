# Batch Inference API Reference
## Contents

- [Endpoints](#endpoints)
- [Input File Format (JSONL)](#input-file-format)
- [Output File Format (JSONL)](#output-file-format)
- [Create Batch Request](#create-batch-request)
- [Batch Job Object (Response)](#batch-job-object)
- [Batch Job Status](#batch-job-status)
- [Workflow](#workflow)
- [Models with 50% Discount](#models-with-50-discount)
- [Rate Limits](#rate-limits)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Error Codes](#error-codes)
- [CLI Commands](#cli-commands)


## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /batches` | Create batch | Submit a new batch job |
| `GET /batches` | List batches | List all batch jobs |
| `GET /batches/{id}` | Get batch | Get batch details |
| `POST /batches/{id}/cancel` | Cancel batch | Cancel a batch job |

Base URL: `https://api.together.xyz/v1`
Authentication: `Authorization: Bearer $TOGETHER_API_KEY`

## Input File Format (JSONL)

Each line is a JSON object with two required fields:

```json
{"custom_id": "request-1", "body": {"model": "Qwen/Qwen2.5-7B-Instruct-Turbo", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 200}}
```

- `custom_id` (string, required): Unique identifier for tracking (max 64 chars)
- `body` (object, required): Request matching the `/v1/chat/completions` schema

## Output File Format (JSONL)

Each line in the output file is a JSON object keyed by `custom_id`:

```json
{"custom_id": "request-1", "response": {"status_code": 200, "body": {"id": "...", "object": "chat.completion", "model": "Qwen/Qwen2.5-7B-Instruct-Turbo", "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}}}}
```

To extract the assistant's reply from a result line:

```python
content = (
    result["response"]["body"]["choices"][0]["message"]["content"]
)
```

## Create Batch Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint` | string | Yes | API endpoint (`/v1/chat/completions`) |
| `input_file_id` | string | Yes | ID of the uploaded input file |
| `completion_window` | string | No | Time window for completion (default: `24h`) |
| `priority` | integer | No | Priority for batch processing |
| `model_id` | string | No | Model to use for processing |

## Batch Job Object (Response)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique batch job identifier |
| `user_id` | string | Associated user ID |
| `input_file_id` | string | Input file reference |
| `file_size_bytes` | integer | Size of input file in bytes |
| `status` | enum | Job state (see Status table below) |
| `endpoint` | string | API endpoint used |
| `progress` | float | Completion percentage (0.0 to 100.0) |
| `model_id` | string | Model used for processing |
| `output_file_id` | string | Results file reference (available on COMPLETED) |
| `error_file_id` | string | Error file reference (available on failure) |
| `error` | string | Error message (if applicable) |
| `job_deadline` | datetime | Deadline for completion |
| `created_at` | datetime | Creation timestamp |
| `completed_at` | datetime | Completion timestamp |

## Batch Job Status

| Status | Description |
|--------|-------------|
| `VALIDATING` | Input file being validated |
| `IN_PROGRESS` | Processing requests |
| `COMPLETED` | All requests processed |
| `FAILED` | Processing failed |
| `EXPIRED` | Job exceeded time limit |
| `CANCELLED` | User cancelled |

## Workflow

### 1. Upload Input File

Pass `check=False` to skip client-side file validation and let the server validate during the `VALIDATING` phase.

```python
from together import Together

client = Together()
file_resp = client.files.upload(file="batch_input.jsonl", purpose="batch-api", check=False)
print(file_resp.id)  # file-abc123
```

```typescript
import Together from "together-ai";

const client = new Together();
const fileResp = await client.files.upload("batch_input.jsonl", "batch-api", false);
console.log(fileResp.id);
```

```shell
curl -X POST "https://api.together.xyz/v1/files" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F "purpose=batch-api" \
  -F "file=@batch_input.jsonl"
```

### 2. Create Batch

Note: `create()` returns a wrapper object. Access the batch via `.job`:

```python
response = client.batches.create(
    input_file_id=file_resp.id,
    endpoint="/v1/chat/completions",
)
batch = response.job
print(batch.id)  # batch-abc123
```

```typescript
const response = await client.batches.create({
  endpoint: "/v1/chat/completions",
  input_file_id: fileResp.id,
});
console.log(response.job?.id);
```

```shell
curl -X POST "https://api.together.xyz/v1/batches" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input_file_id": "file-abc123", "endpoint": "/v1/chat/completions"}'
```

### 3. Check Status

Unlike `create()`, `retrieve()` returns the batch object directly (no `.job` wrapper):

```python
batch = client.batches.retrieve(batch.id)
print(batch.status)    # VALIDATING, IN_PROGRESS, COMPLETED, FAILED
print(batch.progress)  # 0.0 to 100.0
```

```typescript
const batchId = batch.job?.id;
const batchInfo = await client.batches.retrieve(batchId);
console.log(batchInfo.status);
```

```shell
curl -X GET "https://api.together.xyz/v1/batches/batch-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### 4. Download Results

```python
if status.status == "COMPLETED":
    with client.files.with_streaming_response.content(id=status.output_file_id) as response:
        with open("batch_output.jsonl", "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
```

```typescript
const batchResult = await client.batches.retrieve(batchId);

if (batchResult.status === "COMPLETED" && batchResult.output_file_id) {
  const resp = await client.files.content(batchResult.output_file_id);
  const result = await resp.text();
  console.log(result);
}
```

```shell
# First retrieve the batch to get output_file_id, then download:
curl -X GET "https://api.together.xyz/v1/files/file-output456/content" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -o batch_output.jsonl
```

### 5. Cancel Batch

```python
client.batches.cancel("batch-abc123")
```

```typescript
const cancelled = await client.batches.cancel("batch-abc123");
console.log(cancelled);
```

```shell
curl -X POST "https://api.together.xyz/v1/batches/batch-abc123/cancel" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### 6. List Batches

```python
batches = client.batches.list()
for batch in batches:
    print(batch)
```

```typescript
const allBatches = await client.batches.list();
for (const batch of allBatches ?? []) {
  console.log(batch);
}
```

```shell
curl -X GET "https://api.together.xyz/v1/batches" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## Models with 50% Discount

- `Qwen/Qwen2.5-7B-Instruct-Turbo`
- `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- `meta-llama/Llama-3-70b-chat-hf`
- `mistralai/Mixtral-8x7B-Instruct-v0.1`
- `zai-org/GLM-4.5-Air-FP8`
- `openai/whisper-large-v3`

Most serverless models support batch processing through the chat completions endpoint; models not listed above have no discount. A small number of serverless models are not available for batch and will fail if submitted, currently `deepseek-ai/DeepSeek-R1-0528-tput` and `deepseek-ai/DeepSeek-V3.1`.

## Rate Limits

| Limit | Value |
|-------|-------|
| Max requests per batch | 50,000 |
| Max file size | 100MB |
| Max tokens enqueued per model | 30B |
| Recommended batch size | 1,000-10,000 |

Batch API rate limits are separate from standard per-model rate limits.

## Error Handling

Per-request errors are recorded in a separate file accessible via `error_file_id`:

```jsonl
{"custom_id": "req-1", "error": {"message": "Invalid model specified", "code": "invalid_model"}}
{"custom_id": "req-5", "error": {"message": "Request timeout", "code": "timeout"}}
```

## Best Practices

- Aim for 1,000-10,000 requests per batch unless you have a strong reason to go smaller or larger
- Validate JSONL before submission to avoid wasting a full batch run on malformed input
- Use unique `custom_id` values so output and error rows can be reconciled deterministically
- Poll status every 30-60 seconds rather than tight-looping the API
- Small batches (under 1K requests) typically complete in minutes; most batches finish within 24 hours; allow up to 72 hours for very large or complex runs
- Reuse uploaded batch files across multiple jobs when the request set is unchanged

## Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Invalid request format | Check JSONL syntax and required fields |
| 401 | Authentication failed | Verify API key |
| 404 | Batch not found | Check batch ID |
| 429 | Rate limit exceeded | Reduce request frequency |
| 500 | Server error | Retry with exponential backoff |

## CLI Commands

```shell
# Upload file
together files upload batch_input.jsonl --purpose batch-api

# Create batch
together batches create --input-file file-abc123 --endpoint /v1/chat/completions

# Check status
together batches retrieve batch-abc123

# List batches
together batches list

# Cancel
together batches cancel batch-abc123
```
