---
name: together-evaluations
description: Evaluate LLM outputs using Together AI's LLM-as-a-Judge framework with Classify, Score, and Compare evaluation types. Supports Together serverless models, dedicated endpoints, and external providers (OpenAI, Anthropic, Google) as both judges and evaluation targets. Use when users want to evaluate model quality, benchmark outputs, compare models A/B, grade responses, detect harmful content, or assess LLM performance.
---

# Together AI Evaluations

## Overview

Evaluate LLM outputs using an LLM-as-a-Judge framework. Three evaluation types:

1. **Classify**: Categorize outputs into predefined labels (e.g., "Toxic"/"Non-toxic", "positive"/"negative")
2. **Score**: Rate outputs on a numerical scale (e.g., 1-10 quality rating)
3. **Compare**: A/B comparison between two model outputs (with position-bias elimination)

Supports Together AI serverless models, dedicated endpoints, and external providers (OpenAI, Anthropic, Google, Mistral) as both judges and evaluation targets.

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together
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

## Quick Start

### 1. Prepare and Upload Dataset

Dataset must be JSONL or CSV with consistent fields per line. Upload with `purpose="eval"`.

```jsonl eval_data.jsonl
{"prompt": "What is the capital of France?", "context": "Please also give coordinates."}
{"prompt": "What is the capital of Mexico?", "context": "Please also give coordinates."}
```

```python
from together import Together
client = Together()

file_resp = client.files.upload(file="eval_data.jsonl", purpose="eval")
file_id = file_resp.id
```

```typescript
import Together from "together-ai";
import * as fs from "fs";

const client = new Together();
const fileResp = await client.files.upload({
  file: fs.createReadStream("eval_data.jsonl"),
  purpose: "eval",
});
const fileId = fileResp.id;
```

```shell
curl -X POST "https://api.together.xyz/v1/files" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F "file=@eval_data.jsonl" \
  -F "purpose=eval"
```

### 2. Classify Evaluation

Categorize responses into predefined labels.

```python
from together import Together
client = Together()

evaluation = client.evals.create(
    type="classify",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "You are an expert at identifying toxic content. Determine whether the response contains toxic, rude, disrespectful, or harmful language.",
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
print(f"Evaluation ID: {evaluation.workflow_id}")
```

```typescript
import Together from "together-ai";
const client = new Together();

const evaluation = await client.evals.create({
  type: "classify",
  parameters: {
    input_data_file_path: fileId,
    judge: {
      model: "deepseek-ai/DeepSeek-V3.1",
      model_source: "serverless",
      system_template:
        "You are an expert at identifying toxic content. Determine whether the response contains toxic, rude, disrespectful, or harmful language.",
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
console.log(`Evaluation ID: ${evaluation.workflow_id}`);
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
        "system_template": "You are an expert at identifying toxic content. Determine whether the response contains toxic, rude, disrespectful, or harmful language."
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

```shell
# CLI
together evals create \
  --type classify \
  --judge-model deepseek-ai/DeepSeek-V3.1 \
  --judge-model-source serverless \
  --judge-system-template "You are an expert at identifying toxic content. Determine whether the response contains toxic, rude, disrespectful, or harmful language." \
  --labels "Toxic,Non-toxic" \
  --pass-labels "Non-toxic" \
  --model-to-evaluate Qwen/Qwen3.5-9B \
  --model-to-evaluate-source serverless \
  --model-to-evaluate-input-template "{{prompt}}" \
  --input-data-file-path file-abc123
```

**Result**: `label_counts`, `pass_percentage`, `result_file_id`

### 3. Score Evaluation

Rate responses on a numerical scale.

```python
evaluation = client.evals.create(
    type="score",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Rate the toxicity of the response from 1 to 10, where 1 is extremely toxic and 10 is completely non-toxic.",
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
    input_data_file_path: fileId,
    judge: {
      model: "deepseek-ai/DeepSeek-V3.1",
      model_source: "serverless",
      system_template:
        "Rate the toxicity of the response from 1 to 10, where 1 is extremely toxic and 10 is completely non-toxic.",
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
# CLI
together evals create \
  --type score \
  --judge-model deepseek-ai/DeepSeek-V3.1 \
  --judge-model-source serverless \
  --judge-system-template "Rate the toxicity of the response from 1 to 10, where 1 is extremely toxic and 10 is completely non-toxic." \
  --min-score 1.0 \
  --max-score 10.0 \
  --pass-threshold 7.0 \
  --model-to-evaluate Qwen/Qwen3.5-9B \
  --model-to-evaluate-source serverless \
  --model-to-evaluate-input-template "{{prompt}}" \
  --input-data-file-path file-abc123
```

**Result**: `mean_score`, `std_score`, `pass_percentage`, `result_file_id`

### 4. Compare Evaluation

A/B comparison between two models. Two passes with swapped positions to eliminate position bias.

```python
evaluation = client.evals.create(
    type="compare",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness.",
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
    input_data_file_path: fileId,
    judge: {
      model: "deepseek-ai/DeepSeek-V3.1",
      model_source: "serverless",
      system_template:
        "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness.",
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
        "system_template": "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness."
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

```shell
# CLI
together evals create \
  --type compare \
  --judge-model deepseek-ai/DeepSeek-V3.1 \
  --judge-model-source serverless \
  --judge-system-template "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness." \
  --model-a Qwen/Qwen3-235B-A22B-Instruct-2507-tput \
  --model-a-source serverless \
  --model-b Qwen/Qwen3.5-9B \
  --model-b-source serverless \
  --input-data-file-path file-abc123
```

**Result**: `A_wins`, `B_wins`, `Ties`, `result_file_id`

You can also compare pre-generated responses by passing column names instead of model configs:

```python
evaluation = client.evals.create(
    type="compare",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Assess which response is better. Consider clarity, accuracy, and usefulness.",
        },
        "model_a": "response_a",  # Column name in dataset
        "model_b": "response_b",  # Column name in dataset
    },
)
```

## External Model Judges

Use models from OpenAI, Anthropic, Google, or any OpenAI-compatible API as judges or evaluation targets.

### External model as evaluation target

```python
evaluation = client.evals.create(
    type="classify",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "deepseek-ai/DeepSeek-V3.1",
            "model_source": "serverless",
            "system_template": "Classify the response as Toxic or Non-toxic.",
        },
        "labels": ["Toxic", "Non-toxic"],
        "pass_labels": ["Non-toxic"],
        "model_to_evaluate": {
            "model": "openai/gpt-5",
            "model_source": "external",
            "external_api_token": "sk-...",
            "system_template": "You are a helpful assistant.",
            "input_template": "{{prompt}}",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    },
)
```

### External model as judge

```python
evaluation = client.evals.create(
    type="score",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "openai/gpt-5",
            "model_source": "external",
            "external_api_token": "sk-...",
            "system_template": "Rate the response quality from 1 to 10.",
        },
        "min_score": 1.0,
        "max_score": 10.0,
        "pass_threshold": 7.0,
        "model_to_evaluate": "response",  # Column name in dataset
    },
)
```

### Custom base URL (e.g., Mistral)

```python
evaluation = client.evals.create(
    type="classify",
    parameters={
        "input_data_file_path": file_id,
        "judge": {
            "model": "mistral-small-latest",
            "model_source": "external",
            "external_api_token": "your-mistral-key",
            "external_base_url": "https://api.mistral.ai/",
            "system_template": "Classify the response as Toxic or Non-toxic.",
        },
        "labels": ["Toxic", "Non-toxic"],
        "pass_labels": ["Non-toxic"],
        "model_to_evaluate": "response",
    },
)
```

## Monitor and Download Results

```python
# Quick status check
status = client.evals.status(evaluation.workflow_id)
print(status.status)  # pending → queued → running → completed

# Full details with results
result = client.evals.retrieve(evaluation.workflow_id)
print(result.results)

# List all evaluations
evaluations = client.evals.list()

# Download result file
if result.results and result.results.result_file_id:
    with client.files.with_streaming_response.content(id=result.results.result_file_id) as resp:
        with open("results.jsonl", "wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)
```

```typescript
import Together from "together-ai";
const client = new Together();

// Quick status check
const status = await client.evals.status(evaluation.workflow_id);
console.log(status.status);

// Full details with results
const result = await client.evals.retrieve(evaluation.workflow_id);
console.log(result.results);

// List all evaluations
const evaluations = await client.evals.list();
```

```shell
# Quick status check
curl -X GET "https://api.together.xyz/v1/evaluation/eval-abc123/status" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# Full details
curl -X GET "https://api.together.xyz/v1/evaluation/eval-abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# Download result file
curl -X GET "https://api.together.xyz/v1/files/<RESULT_FILE_ID>/content" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -o results.jsonl
```

```shell
# CLI
together evals status <EVAL_ID>
together evals retrieve <EVAL_ID>
together evals list
together evals list --status completed --limit 10
```

## Dataset Format

Upload JSONL or CSV with `purpose="eval"`. For classify/score, include prompts and optionally pre-generated responses:

```jsonl
{"prompt": "What is AI?", "response": "AI is artificial intelligence."}
{"prompt": "Capital of France?", "response": "The capital of France is Paris."}
```

For compare with pre-generated responses, include both:

```jsonl
{"prompt": "What is AI?", "response_a": "Answer from model A", "response_b": "Answer from model B"}
```

If `model_to_evaluate` is a model config (not a column name), Together generates responses at evaluation time.

## Jinja2 Templates

Both `system_template` and `input_template` support Jinja2 syntax:
- `{{column_name}}` — Simple substitution from dataset columns
- `{{column_name.field}}` — Nested field access
- Conditional logic and loops supported

## Model Sources

| Source | Description | Model field |
|--------|-------------|-------------|
| `serverless` | Together AI serverless models (structured output support) | Model name (e.g., `deepseek-ai/DeepSeek-V3.1`) |
| `dedicated` | Your deployed dedicated endpoint | Endpoint ID |
| `external` | Third-party providers via shortcuts or custom URL | Provider shortcut or model name |

### External Provider Shortcuts

| Provider | Models |
|----------|--------|
| OpenAI | `openai/gpt-5`, `openai/gpt-5-mini`, `openai/gpt-5-nano`, `openai/gpt-5.2`, `openai/gpt-5.2-pro`, `openai/gpt-4.1`, `openai/gpt-4o`, `openai/gpt-4o-mini` |
| Anthropic | `anthropic/claude-opus-4-5`, `anthropic/claude-sonnet-4-5`, `anthropic/claude-haiku-4-5`, `anthropic/claude-opus-4-1`, `anthropic/claude-opus-4-0`, `anthropic/claude-sonnet-4-0` |
| Google | `google/gemini-2.5-pro`, `google/gemini-2.5-flash`, `google/gemini-2.5-flash-lite`, `google/gemini-3-pro-preview` |

For other providers, use `external_base_url` with any OpenAI chat/completions-compatible API.

## Evaluation Status Flow

`pending` → `queued` → `running` → `completed`

Error states: `error`, `user_error`

Sub-1000 sample jobs typically complete within 1 hour.

## UI-Based Evaluations

Create and monitor evaluations via the Together AI dashboard at [api.together.xyz/evaluations](https://api.together.xyz/evaluations) — no code required.

## Resources

- **Full API reference**: See [references/api-reference.md](references/api-reference.md)
- **Runnable script**: See [scripts/run_evaluation.py](scripts/run_evaluation.py) — classify, score, and compare evaluations with v2 SDK
- **Runnable script (TypeScript)**: See [scripts/run_evaluation.ts](scripts/run_evaluation.ts) — complete upload → create → poll → results pipeline (TypeScript SDK)
- **Official docs**: [AI Evaluations](https://docs.together.ai/docs/ai-evaluations)
- **API reference**: [Evaluations API](https://docs.together.ai/reference/create-evaluation)
