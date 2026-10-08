# Fine-tuning Data Formats Reference
## Contents

- [Format Overview](#format-overview)
- [Conversational Format](#conversational-format)
- [Instruction Format](#instruction-format)
- [Generic Text Format](#generic-text-format)
- [Preference/DPO Format](#preferencedpo-format)
- [Reasoning Format](#reasoning-format)
- [Function Calling Format](#function-calling-format)
- [VLM Conversational Format](#vlm-conversational-format)
- [VLM Instruction Format](#vlm-instruction-format)
- [File Formats](#file-formats)
- [Loss Masking](#loss-masking)
- [Sample Weights](#sample-weights)
- [Data Validation](#data-validation)
- [Converting Image URLs to Base64](#converting-image-urls-to-base64)


## Format Overview

| Format | Use Case | Key Field |
|--------|----------|-----------|
| Conversational | Multi-turn chat | `messages` |
| Instruction | Prompt-completion pairs | `prompt` + `completion` |
| Generic Text | Text completion / pretraining | `text` |
| Preference/DPO | Preference learning | `input` + `preferred_output` + `non_preferred_output` |
| Reasoning | Chain-of-thought training | `messages` with `reasoning` field on assistant |
| Function Calling | Tool use training | `messages` + `tools` |
| VLM | Vision + language | `messages` with image content |

## Conversational Format

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "Explain ML", "weight": 0},
    {"role": "assistant", "content": "Machine learning is...", "weight": 1}
  ]
}
```

- `weight: 0` -- Exclude from loss (masking)
- `weight: 1` -- Include in loss (default for assistant)
- By default, only assistant messages are trained on

### Preparing a Dataset (Python example)

```python
from datasets import load_dataset

coqa_dataset = load_dataset("stanfordnlp/coqa")

system_prompt = "Read the story and extract answers for the questions.\nStory: {}"

def map_fields(row):
    messages = [{"role": "system", "content": system_prompt.format(row["story"])}]
    for q, a in zip(row["questions"], row["answers"]["input_text"]):
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    return {"messages": messages}

train_messages = coqa_dataset["train"].map(
    map_fields, remove_columns=coqa_dataset["train"].column_names
)
train_messages.to_json("coqa_prepared_train.jsonl")
```

## Instruction Format

```json
{"prompt": "What is photosynthesis?", "completion": "Photosynthesis is..."}
```

- By default, model not trained on prompt text
- Use `train_on_inputs=true` to train on prompts too

## Generic Text Format

```json
{"text": "The quick brown fox jumps over the lazy dog."}
```

## Preference/DPO Format

```json
{
  "input": {
    "messages": [
      {"role": "user", "content": "What's open-source AI?"}
    ]
  },
  "preferred_output": [
    {"role": "assistant", "content": "Open-source AI means models are free to use, modify, and share..."}
  ],
  "non_preferred_output": [
    {"role": "assistant", "content": "It means the code is public."}
  ]
}
```

Both outputs must contain exactly one message from the assistant role.

## Reasoning Format

For fine-tuning reasoning models, assistant messages include a `reasoning` (or `reasoning_content`)
field containing the chain of thought, alongside the `content` field for the final answer:

```json
{
  "messages": [
    {"role": "user", "content": "What is 15% of 240?"},
    {
      "role": "assistant",
      "reasoning": "15% means 15/100 = 0.15\n0.15 * 240 = 36",
      "content": "15% of 240 is 36."
    }
  ]
}
```

For preference fine-tuning with reasoning, include `reasoning` in both outputs:

```json
{
  "input": {
    "messages": [{"role": "user", "content": "What is 15% of 240?"}]
  },
  "preferred_output": [
    {
      "role": "assistant",
      "reasoning": "15% means 15/100 = 0.15\n0.15 * 240 = 36",
      "content": "15% of 240 is 36."
    }
  ],
  "non_preferred_output": [
    {
      "role": "assistant",
      "reasoning": "15% of 240... about 30 maybe?",
      "content": "About 30."
    }
  ]
}
```

Supported models: Qwen3.5 family (0.8B-397B), Qwen3 family (0.6B-235B), Qwen3-Next-80B-A3B-Thinking, GLM-5.1, GLM-5, GLM-4.7, GLM-4.6.

## Function Calling Format

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string", "description": "City name"}
          },
          "required": ["city"]
        }
      }
    }
  ],
  "messages": [
    {"role": "user", "content": "What's the weather in NYC?"},
    {
      "role": "assistant",
      "tool_calls": [
        {
          "id": "call_1",
          "type": "function",
          "function": {"name": "get_weather", "arguments": "{\"city\": \"New York\"}"}
        }
      ]
    },
    {"role": "tool", "tool_call_id": "call_1", "content": "{\"temp\": 72, \"condition\": \"sunny\"}"},
    {"role": "assistant", "content": "It's currently 72F and sunny in New York City."}
  ]
}
```

For preference fine-tuning with function calling, the `tools` field goes inside `input`:

```json
{
  "input": {
    "tools": [...],
    "messages": [{"role": "user", "content": "..."}]
  },
  "preferred_output": [{"role": "assistant", "tool_calls": [...]}],
  "non_preferred_output": [{"role": "assistant", "content": "wrong answer"}]
}
```

## VLM Conversational Format

```json
{
  "messages": [
    {"role": "system", "content": [{"type": "text", "text": "Vision assistant."}]},
    {"role": "user", "content": [
      {"type": "text", "text": "How many oranges?"},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,iVBORw0KG..."}}
    ]},
    {"role": "assistant", "content": [{"type": "text", "text": "There are 7 oranges."}]}
  ]
}
```

- Images must be base64 encoded with MIME prefix
- Max 10 images per example, 10MB each
- Formats: PNG, JPEG, WEBP
- Only user messages can contain images

## VLM Instruction Format

```json
{
  "prompt": [
    {"type": "text", "text": "Describe this image."},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
  ],
  "completion": [{"type": "text", "text": "The image shows..."}]
}
```

## File Formats

### JSONL (Default)
- One JSON object per line
- Automatic sample packing for efficient training
- Max file size: 50GB

### Parquet (Advanced)
- Pre-tokenized data
- Required columns: `input_ids`, `attention_mask`
- Optional: `labels` (use -100 to mask tokens from loss)
- Useful for custom tokenization or loss masking

## Loss Masking

- **Conversational format**: Use `weight: 0` on specific messages to exclude from loss (only `0` and `1` are accepted on messages; `1` is the default)
- **`train_on_inputs` parameter**:
  - `"auto"` (default): Framework decides based on format
  - `true`: Train on everything including user messages/prompts
  - `false`: Only train on assistant/completion text
- **Parquet format**: Set label to -100 for tokens to exclude
- **Per-sample loss scaling**: Add a top-level `"weight"` to a JSONL sample to multiply the loss for all of its tokens (see [Sample Weights](#sample-weights))

## Sample Weights

All JSONL fine-tuning formats (conversational, instruction, generic text, preference, reasoning, function calling) and all training methods support an optional top-level `"weight"` key on each JSON object. The value is a non-negative float that acts as a loss multiplier on every token in that sample, letting you up- or down-weight individual examples without changing the dataset itself.

- Top-level `weight` is a non-negative float (e.g. `0.1`, `1.0`, `2.5`); `1.0` is the implicit default if omitted
- Distinct from the per-message `weight` field in conversational data, which only accepts `0` or `1` and gates whether a message's tokens enter the loss at all
- Sample weights and message weights can be combined in the same file
- Setting a sample's top-level `weight` to `0` effectively drops it from the loss while still keeping it in the dataset (e.g. for packing statistics)

```json
{
  "messages": [
    {"role": "system", "content": "This is a system prompt."},
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thank you! How can I help you?"},
    {"role": "user", "content": "Can you explain machine learning?", "weight": 0},
    {"role": "assistant", "content": "Machine learning is...", "weight": 1}
  ],
  "weight": 0.9
}
{
  "messages": [
    {"role": "user", "content": "Can you explain why?"},
    {"role": "assistant", "content": "I can't."}
  ],
  "weight": 0.1
}
```

## Data Validation

Validation runs in two stages:

1. **Client-side structural check** (local). Runs by default inside `client.files.upload(..., check=True)` or with `together files check`. Verifies only basic formatting: UTF-8 encoding, one JSON object per line, minimum sample count, and maximum file size. Pass `check=False` to skip (useful for very large files).
2. **Server-side schema validation** (during ingestion). Runs after upload and performs the full fine-tuning schema check (conversation roles, tool calls, required fields, etc.). The file is only usable for fine-tuning once `processing_status` becomes `COMPLETED`. If validation rejects the dataset, `processing_status` becomes `INVALID_FORMAT` and `validation_report.error` carries a user-facing reason.

```python
import time
from together import Together

client = Together()

# 1. Upload with the local structural check enabled (default).
file = client.files.upload(file="my_data.jsonl", purpose="fine-tune", check=True)
print(file.id)  # file-abc123

# 2. Poll until server-side validation finishes before creating a fine-tuning job.
while True:
    meta = client.files.retrieve(file.id)
    if meta.processing_status == "COMPLETED":
        break
    if meta.processing_status == "INVALID_FORMAT":
        # meta.validation_report["error"] carries a user-facing reason.
        raise ValueError(
            f"file is not suitable for fine-tuning: {meta.validation_report}"
        )
    if meta.processing_status == "FAILED":
        raise RuntimeError(
            f"file processing did not complete: {meta.validation_report}"
        )
    time.sleep(5)
```

Treat `processing_status` as the authoritative readiness signal; the `validation_report` schema may evolve. A successful response looks like:

```json
{
  "processing_status": "COMPLETED",
  "validation_report": {"valid": true, "dataset_format": "conversation", "nlines": 7199}
}
```

A user-correctable failure looks like:

```json
{
  "processing_status": "INVALID_FORMAT",
  "validation_report": {
    "valid": false,
    "error_type": "INVALID_FORMAT",
    "error": "Line 7: `messages[1]` must contain a `role` field"
  }
}
```

```shell
# CLI: check format and upload
together files check my_data.jsonl
together files upload my_data.jsonl

# Upload without the local structural check
together files upload my_data.jsonl --no-check

# Inspect server-side validation status (processing_status / validation_report)
together files retrieve <FILE-ID>

# List and download files
together files list
together files retrieve-content <FILE-ID>
```

## Converting Image URLs to Base64

```python
import base64
import requests

def url_to_base64(url: str, mime_type: str = "image/jpeg") -> str:
    response = requests.get(url)
    encoded = base64.b64encode(response.content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"
```
