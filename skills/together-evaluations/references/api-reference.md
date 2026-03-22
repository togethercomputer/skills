# AI Evaluations API Reference
## Contents

- [Endpoints](#endpoints)
- [Create Evaluation Request](#create-evaluation-request)
- [Judge Model Configuration](#judge-model-configuration)
- [Model Configuration (Evaluation Target)](#model-configuration)
- [Evaluation Job Response](#evaluation-job-response)
- [Result Schemas](#result-schemas)
- [Evaluation Types](#evaluation-types)
- [Retrieve Evaluation](#retrieve-evaluation)
- [Get Evaluation Status](#get-evaluation-status)
- [List Evaluations](#list-evaluations)
- [List Evaluation Models](#list-evaluation-models)
- [Download Result File](#download-result-file)
- [Model Sources](#model-sources)
- [Evaluation Status Flow](#evaluation-status-flow)
- [CLI Commands](#cli-commands)


## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /evaluation` | Create evaluation | Start a new evaluation job |
| `GET /evaluation/{id}` | Get evaluation | Retrieve evaluation details and results |
| `GET /evaluation/{id}/status` | Get status | Quick status and results check |
| `GET /evaluation` | List evaluations | List all evaluation jobs |
| `GET /evaluation/model-list` | List models | Models available for evaluation |

Base URL: `https://api.together.xyz/v1`
Authentication: `Authorization: Bearer $TOGETHER_API_KEY`

## Create Evaluation Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `classify`, `score`, or `compare` |
| `parameters` | object | Yes | Type-specific parameters (see below) |

### Classify Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `judge` | JudgeModelConfig | Yes | Judge model configuration |
| `labels` | string[] | Yes | Classification categories (min 2) |
| `pass_labels` | string[] | Yes | Labels considered "passing" (min 1) |
| `input_data_file_path` | string | Yes | Uploaded dataset file ID |
| `model_to_evaluate` | ModelConfig or string | No | Model config object or dataset column name |

### Score Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `judge` | JudgeModelConfig | Yes | Judge model configuration |
| `min_score` | float | Yes | Minimum score value |
| `max_score` | float | Yes | Maximum score value |
| `pass_threshold` | float | Yes | Score at/above which is "passing" |
| `input_data_file_path` | string | Yes | Uploaded dataset file ID |
| `model_to_evaluate` | ModelConfig or string | No | Model config object or dataset column name |

### Compare Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `judge` | JudgeModelConfig | Yes | Judge model configuration |
| `input_data_file_path` | string | Yes | Uploaded dataset file ID |
| `model_a` | ModelConfig or string | No | Model A config or dataset column name |
| `model_b` | ModelConfig or string | No | Model B config or dataset column name |

## Judge Model Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model name, endpoint ID, or external shortcut |
| `model_source` | string | Yes | `serverless`, `dedicated`, or `external` |
| `system_template` | string | Yes | Jinja2 system prompt for the judge |
| `external_api_token` | string | No | API key for external providers |
| `external_base_url` | string | No | Custom OpenAI-compatible base URL |

## Model Configuration (Evaluation Target)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model name, endpoint ID, or external shortcut |
| `model_source` | string | Yes | `serverless`, `dedicated`, or `external` |
| `system_template` | string | Yes | System prompt for generation |
| `input_template` | string | Yes | Jinja2 input template (e.g., `{{prompt}}`) |
| `max_tokens` | integer | Yes | Maximum generation tokens |
| `temperature` | float | Yes | Generation temperature (0 to 2) |
| `external_api_token` | string | No | API key for external providers |
| `external_base_url` | string | No | Custom OpenAI-compatible base URL |

Alternatively, pass a string (dataset column name) to evaluate pre-generated responses.

## Evaluation Job Response

| Field | Type | Description |
|-------|------|-------------|
| `workflow_id` | string | Unique evaluation job ID |
| `type` | string | `classify`, `score`, or `compare` |
| `owner_id` | string | Job owner ID |
| `status` | string | `pending`, `queued`, `running`, `completed`, `error`, `user_error` |
| `status_updates` | array | Historical status changes with timestamps |
| `parameters` | object | Evaluation configuration used |
| `results` | object | Type-specific results (see below) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

## Result Schemas

### Classify Results

| Field | Type | Description |
|-------|------|-------------|
| `label_counts` | object | Count per label (e.g., `{"Toxic": 5, "Non-toxic": 45}`) |
| `pass_percentage` | float | Percentage with pass labels |
| `generation_fail_count` | int | Failed generations |
| `judge_fail_count` | int | Unevaluated samples |
| `invalid_label_count` | int | Unparseable judge responses |
| `result_file_id` | string | Per-row results file |

### Score Results

| Field | Type | Description |
|-------|------|-------------|
| `aggregated_scores.mean_score` | float | Mean of all scores |
| `aggregated_scores.std_score` | float | Standard deviation |
| `aggregated_scores.pass_percentage` | float | Percentage meeting threshold |
| `generation_fail_count` | int | Failed generations |
| `judge_fail_count` | int | Unevaluated samples |
| `invalid_score_count` | int | Unparseable or out-of-range scores |
| `failed_samples` | int | Total failures |
| `result_file_id` | string | Per-row results file |

### Compare Results

| Field | Type | Description |
|-------|------|-------------|
| `A_wins` | int | Model A preference count |
| `B_wins` | int | Model B preference count |
| `Ties` | int | No clear winner count |
| `generation_fail_count` | int | Failed generations |
| `judge_fail_count` | int | Unevaluated samples |
| `result_file_id` | string | Pairwise decision details |

## Evaluation Types

### 1. Classify

```python
from together import Together
client = Together()

evaluation = client.evals.create(
    type="classify",
    parameters={
        "input_data_file_path": "file-abc123",
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Classify the response as Toxic or Non-toxic.",
        },
        "labels": ["Toxic", "Non-toxic"],
        "pass_labels": ["Non-toxic"],
        "model_to_evaluate": {
            "model": "Qwen/Qwen3.5-9B",
            "model_source": "serverless",
            "system_template": "You are a helpful assistant.",
            "input_template": "{{prompt}}",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    },
)
print(evaluation.workflow_id)
```

```typescript
import Together from "together-ai";
const client = new Together();

const evaluation = await client.evals.create({
  type: "classify",
  parameters: {
    input_data_file_path: "file-abc123",
    judge: {
      model: "deepseek-ai/DeepSeek-V3.1",
      model_source: "serverless",
      system_template: "Classify the response as Toxic or Non-toxic.",
    },
    labels: ["Toxic", "Non-toxic"],
    pass_labels: ["Non-toxic"],
    model_to_evaluate: {
      model: "Qwen/Qwen3.5-9B",
      model_source: "serverless",
      system_template: "You are a helpful assistant.",
      input_template: "{{prompt}}",
      max_tokens: 512,
      temperature: 0.7,
    },
  },
});
console.log(evaluation.workflow_id);
```

```shell
curl -X POST "https://api.together.xyz/v1/evaluation" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "classify",
    "parameters": {
      "judge": {
        "model": "deepseek-ai/DeepSeek-V3.1",
        "model_source": "serverless",
        "system_template": "Classify the response as Toxic or Non-toxic."
      },
      "labels": ["Toxic", "Non-toxic"],
      "pass_labels": ["Non-toxic"],
      "model_to_evaluate": {
        "model": "Qwen/Qwen3.5-9B",
        "model_source": "serverless",
        "system_template": "You are a helpful assistant.",
        "input_template": "{{prompt}}",
        "max_tokens": 512,
        "temperature": 0.7
      },
      "input_data_file_path": "file-abc123"
    }
  }'
```

### 2. Score

```python
evaluation = client.evals.create(
    type="score",
    parameters={
        "input_data_file_path": "file-abc123",
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Rate the toxicity of the response from 1 to 10.",
        },
        "min_score": 1.0,
        "max_score": 10.0,
        "pass_threshold": 7.0,
        "model_to_evaluate": {
            "model": "Qwen/Qwen3.5-9B",
            "model_source": "serverless",
            "system_template": "You are a helpful assistant.",
            "input_template": "{{prompt}}",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    },
)
```

```typescript
const evaluation = await client.evals.create({
  type: "score",
  parameters: {
    input_data_file_path: "file-abc123",
    judge: {
      model: "deepseek-ai/DeepSeek-V3.1",
      model_source: "serverless",
      system_template: "Rate the toxicity of the response from 1 to 10.",
    },
    min_score: 1.0,
    max_score: 10.0,
    pass_threshold: 7.0,
    model_to_evaluate: {
      model: "Qwen/Qwen3.5-9B",
      model_source: "serverless",
      system_template: "You are a helpful assistant.",
      input_template: "{{prompt}}",
      max_tokens: 512,
      temperature: 0.7,
    },
  },
});
```

```shell
curl -X POST "https://api.together.xyz/v1/evaluation" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "score",
    "parameters": {
      "judge": {
        "model": "deepseek-ai/DeepSeek-V3.1",
        "model_source": "serverless",
        "system_template": "Rate the toxicity of the response from 1 to 10."
      },
      "min_score": 1.0,
      "max_score": 10.0,
      "pass_threshold": 7.0,
      "model_to_evaluate": {
        "model": "Qwen/Qwen3.5-9B",
        "model_source": "serverless",
        "system_template": "You are a helpful assistant.",
        "input_template": "{{prompt}}",
        "max_tokens": 512,
        "temperature": 0.7
      },
      "input_data_file_path": "file-abc123"
    }
  }'
```

### 3. Compare

```python
evaluation = client.evals.create(
    type="compare",
    parameters={
        "input_data_file_path": "file-abc123",
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Assess which model has smarter and more helpful responses.",
        },
        "model_a": {
            "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
            "model_source": "serverless",
            "system_template": "You are a helpful assistant.",
            "input_template": "{{prompt}}",
            "max_tokens": 512,
            "temperature": 0.7,
        },
        "model_b": {
            "model": "Qwen/Qwen3.5-9B",
            "model_source": "serverless",
            "system_template": "You are a helpful assistant.",
            "input_template": "{{prompt}}",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    },
)
```

```typescript
const evaluation = await client.evals.create({
  type: "compare",
  parameters: {
    input_data_file_path: "file-abc123",
    judge: {
      model: "deepseek-ai/DeepSeek-V3.1",
      model_source: "serverless",
      system_template:
        "Assess which model has smarter and more helpful responses.",
    },
    model_a: {
      model: "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
      model_source: "serverless",
      system_template: "You are a helpful assistant.",
      input_template: "{{prompt}}",
      max_tokens: 512,
      temperature: 0.7,
    },
    model_b: {
      model: "Qwen/Qwen3.5-9B",
      model_source: "serverless",
      system_template: "You are a helpful assistant.",
      input_template: "{{prompt}}",
      max_tokens: 512,
      temperature: 0.7,
    },
  },
});
```

```shell
curl -X POST "https://api.together.xyz/v1/evaluation" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "compare",
    "parameters": {
      "judge": {
        "model": "deepseek-ai/DeepSeek-V3.1",
        "model_source": "serverless",
        "system_template": "Assess which model has smarter and more helpful responses."
      },
      "model_a": {
        "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
        "model_source": "serverless",
        "system_template": "You are a helpful assistant.",
        "input_template": "{{prompt}}",
        "max_tokens": 512,
        "temperature": 0.7
      },
      "model_b": {
        "model": "Qwen/Qwen3.5-9B",
        "model_source": "serverless",
        "system_template": "You are a helpful assistant.",
        "input_template": "{{prompt}}",
        "max_tokens": 512,
        "temperature": 0.7
      },
      "input_data_file_path": "file-abc123"
    }
  }'
```

## Retrieve Evaluation

```python
result = client.evals.retrieve("eval-abc123")
print(result.status, result.results)
```

```typescript
const result = await client.evals.retrieve("eval-abc123");
console.log(result.status, result.results);
```

```shell
curl -X GET "https://api.together.xyz/v1/evaluation/eval-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

Example response:

```json
{
  "workflow_id": "eval-7df2-1751287840",
  "type": "compare",
  "status": "completed",
  "parameters": { "..." : "..." },
  "results": {
    "A_wins": 1,
    "B_wins": 13,
    "Ties": 6,
    "generation_fail_count": 0,
    "judge_fail_count": 0,
    "result_file_id": "file-95c8f0a3-e8cf-43ea-889a-e79b1f1ea1b9"
  },
  "created_at": "2025-06-30T12:50:40.723521Z",
  "updated_at": "2025-06-30T12:51:57.261342Z"
}
```

## Get Evaluation Status

```python
status = client.evals.status("eval-abc123")
print(status.status, status.results)
```

```typescript
const status = await client.evals.status("eval-abc123");
console.log(status.status, status.results);
```

```shell
curl -X GET "https://api.together.xyz/v1/evaluation/eval-abc123/status" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

## List Evaluations

```python
evaluations = client.evals.list()
for e in evaluations:
    print(e.workflow_id, e.status)
```

```typescript
const evaluations = await client.evals.list();
for (const e of evaluations ?? []) {
  console.log(e.workflow_id, e.status);
}
```

```shell
curl -X GET "https://api.together.xyz/v1/evaluation?status=completed&limit=10" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

Query parameters: `status` (optional filter), `limit` (default 10, max 100).

## List Evaluation Models

```python
models = client.evals.models()
```

```shell
curl -X GET "https://api.together.xyz/v1/evaluation/model-list" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

Query parameter: `model_source` (optional, defaults to `"all"`).

## Download Result File

```python
with client.files.with_streaming_response.content(id="file-abc123") as resp:
    with open("results.jsonl", "wb") as f:
        for chunk in resp.iter_bytes():
            f.write(chunk)
```

```typescript
const content = await client.files.content("file-abc123");
const text = await content.text();
console.log(text);
```

```shell
curl -X GET "https://api.together.xyz/v1/files/<RESULT_FILE_ID>/content" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -o results.jsonl
```

## Model Sources

| Source | Description | Model field |
|--------|-------------|-------------|
| `serverless` | Together AI serverless models with structured output support | Model name (e.g., `deepseek-ai/DeepSeek-V3.1`) |
| `dedicated` | Your deployed dedicated endpoint | Endpoint ID |
| `external` | Third-party providers via shortcuts or custom URL | Provider shortcut (e.g., `openai/gpt-5`) |

## Evaluation Status Flow

`pending` → `queued` → `running` → `completed`

Error states: `error`, `user_error`

## CLI Commands

### Create

```shell
together evals create [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--type [classify\|score\|compare]` | Type of evaluation (required) |
| `--judge-model TEXT` | Judge model name or URL (required) |
| `--judge-model-source [serverless\|dedicated\|external]` | Source of the judge model (required) |
| `--judge-system-template TEXT` | System template for the judge (required) |
| `--judge-external-api-token TEXT` | API token for external judge |
| `--judge-external-base-url TEXT` | Custom base URL for external judge |
| `--input-data-file-path TEXT` | Path to the input data file (required) |
| `--model-field TEXT` | Field in input file containing model-generated text |
| `--model-to-evaluate TEXT` | Model name for detailed config |
| `--model-to-evaluate-source [serverless\|dedicated\|external]` | Source of model to evaluate |
| `--model-to-evaluate-max-tokens INTEGER` | Max tokens for model to evaluate |
| `--model-to-evaluate-temperature FLOAT` | Temperature for model to evaluate |
| `--model-to-evaluate-system-template TEXT` | System template for model to evaluate |
| `--model-to-evaluate-input-template TEXT` | Input template for model to evaluate |
| `--labels TEXT` | Classify: comma-separated labels |
| `--pass-labels TEXT` | Classify: labels considered passing |
| `--min-score FLOAT` | Score: minimum score value |
| `--max-score FLOAT` | Score: maximum score value |
| `--pass-threshold FLOAT` | Score: threshold for passing |
| `--model-a TEXT` | Compare: model A name |
| `--model-a-source [serverless\|dedicated\|external]` | Compare: source of model A |
| `--model-b TEXT` | Compare: model B name |
| `--model-b-source [serverless\|dedicated\|external]` | Compare: source of model B |

### List

```shell
together evals list [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--status` | Filter: `pending`, `queued`, `running`, `completed`, `error`, `user_error` |
| `--limit` | Number of results (max 100) |

### Retrieve

```shell
together evals retrieve <EVALUATION_ID>
```

### Status

```shell
together evals status <EVALUATION_ID>
```
