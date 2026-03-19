# Fine-tuning Data Formats Reference

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

Supported models: Qwen3 family (0.6B-235B), Qwen3-Next-80B-A3B-Thinking, GLM-4.6, GLM-4.7.

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

- **Conversational format**: Use `weight: 0` on specific messages to exclude from loss
- **`train_on_inputs` parameter**:
  - `"auto"` (default): Framework decides based on format
  - `true`: Train on everything including user messages/prompts
  - `false`: Only train on assistant/completion text
- **Parquet format**: Set label to -100 for tokens to exclude

## Data Validation

```python
from together import Together

client = Together()

# Upload with validation enabled
file = client.files.upload(file="my_data.jsonl", purpose="fine-tune", check=True)
print(file.id)  # file-abc123
```

```shell
# CLI: check format and upload
together files check my_data.jsonl
together files upload my_data.jsonl

# Upload without format checking
together files upload my_data.jsonl --no-check

# List and manage files
together files list
together files retrieve <FILE-ID>
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
