---
name: together-chat-completions
description: Serverless chat completion inference via Together AI's OpenAI-compatible API. Access 100+ open-source models with pay-per-token pricing. Includes function calling (tool use) with 6 calling patterns, structured outputs (JSON mode, json_schema, regex), and reasoning/thinking models (DeepSeek R1, DeepSeek V3.1, Kimi K2.5, GLM-5, GPT-OSS, Qwen3.5). Use when building chat applications, text generation, multi-turn conversations, function calling, structured JSON outputs, reasoning/chain-of-thought, thinking mode toggle, or any LLM inference task using Together AI.
---

# Together Chat Completions

## Overview

Send inference requests to 100+ open-source models via Together AI's serverless API. OpenAI-compatible -- swap
the base URL and API key to migrate existing code.

- Base URL: `https://api.together.xyz/v1`
- Auth: `Authorization: Bearer $TOGETHER_API_KEY`
- Endpoints: `/v1/chat/completions` (chat)
- SDKs: `uv pip install together` (Python), `npm install together-ai` (TypeScript)

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together # for quick installation without new project setup
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

### Basic Chat Completion

```python
from together import Together

client = Together()

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": "What are some fun things to do in NYC?"}],
)
print(response.choices[0].message.content)
```

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.chat.completions.create({
  model: "openai/gpt-oss-20b",
  messages: [{ role: "user", content: "What are some fun things to do in NYC?" }],
});
console.log(response.choices[0].message.content);
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [
      {"role": "user", "content": "What are some fun things to do in NYC?"}
    ]
  }'
```

### Streaming

Set `stream=True` to receive tokens incrementally:

```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": "Write a haiku about coding"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

```typescript
import Together from "together-ai";
const together = new Together();

const stream = await together.chat.completions.create({
  model: "openai/gpt-oss-20b",
  messages: [
    { role: "user", content: "What are some fun things to do in New York?" },
  ],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [
      {"role": "user", "content": "What are some fun things to do in New York?"}
    ],
    "stream": true
  }'
```

### Multi-Turn Conversation

Pass conversation history in the `messages` array with alternating `user`/`assistant` roles:

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": "You are a helpful travel guide."},
        {"role": "user", "content": "What should I do in Paris?"},
        {"role": "assistant", "content": "Visit the Eiffel Tower and the Louvre!"},
        {"role": "user", "content": "How about food recommendations?"},
    ],
)
```

### Async (Python)

Use `AsyncTogether` for parallel requests:

```python
import asyncio
from together import AsyncTogether

async def main():
    client = AsyncTogether()
    tasks = [
        client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": msg}],
        )
        for msg in ["Hello", "How are you?", "Tell me a joke"]
    ]
    responses = await asyncio.gather(*tasks)
    for r in responses:
        print(r.choices[0].message.content)

asyncio.run(main())
```

## Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model ID (required) |
| `messages` | array | Conversation messages with `role` and `content` (required for chat) |
| `max_tokens` | int | Max tokens to generate |
| `temperature` | float | Sampling temperature (0-2, default ~0.7) |
| `top_p` | float | Nucleus sampling threshold (0-1) |
| `top_k` | int | Top-k sampling |
| `repetition_penalty` | float | Penalize repeated tokens (>1.0 = more penalty) |
| `stop` | string[] | Stop sequences |
| `stream` | bool | Enable streaming |
| `response_format` | object | Force JSON output or schema (see Structured Outputs section) |
| `logprobs` | int | Return log probabilities for top N tokens |
| `n` | int | Number of completions to generate |
| `reasoning_effort` | string | Reasoning depth: `"low"`, `"medium"`, `"high"` (GPT-OSS models) |
| `reasoning` | object | Enable/disable reasoning: `{"enabled": true}` (hybrid models) |

## Message Roles

- **system**: Set model behavior and context (first message)
- **user**: End-user input
- **assistant**: Model responses (for conversation history)
- **tool**: Tool/function call results

## OpenAI Compatibility

Migrate from OpenAI by changing base URL and API key:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.together.xyz/v1",
    api_key="YOUR_TOGETHER_API_KEY",
)
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

## Rate Limits & Build Tiers

Rate limits depend on your Build Tier (based on lifetime spend):

| Tier | Lifetime Spend | RPM (most models) |
|------|---------------|-------------------|
| Tier 1 | $5+ | 60 |
| Tier 2 | $50+ | 600 |
| Tier 3 | $200+ | 600 |
| Tier 4 | $500+ | 600 |
| Tier 5 | $1000+ | 600 |

Larger models (>100B) have separate, lower limits. See references/models.md for the full model catalog.

## Function Calling (Tool Use)

Define tools the model can call, then execute them and pass results back:

```python
import json
from together import Together
client = Together()

tools = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
        },
    },
}]

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that can access external functions."},
        {"role": "user", "content": "What is the current temperature of New York?"},
    ],
    tools=tools,
)

# Process tool calls
tool_calls = response.choices[0].message.tool_calls
messages = [
    {"role": "system", "content": "You are a helpful assistant that can access external functions."},
    {"role": "user", "content": "What is the current temperature of New York?"},
]
messages.append(response.choices[0].message)

for tc in tool_calls:
    args = json.loads(tc.function.arguments)
    result = get_current_weather(**args)  # your function
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

final = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)
```

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages: [
    {
      role: "system",
      content: "You are a helpful assistant that can access external functions.",
    },
    { role: "user", content: "What is the current temperature of New York?" },
  ],
  tools: [
    {
      type: "function",
      function: {
        name: "getCurrentWeather",
        description: "Get the current weather in a given location",
        parameters: {
          type: "object",
          properties: {
            location: {
              type: "string",
              description: "The city and state, e.g. San Francisco, CA",
            },
            unit: {
              type: "string",
              description: "The unit of temperature",
              enum: ["celsius", "fahrenheit"],
            },
          },
        },
      },
    },
  ],
});

console.log(JSON.stringify(response.choices[0].message?.tool_calls, null, 2));
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct-Turbo",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant that can access external functions."
      },
      {
        "role": "user",
        "content": "What is the current temperature of New York?"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
              },
              "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
              }
            }
          }
        }
      }
    ]
  }'
```

### tool_choice Parameter

- `"auto"` (default): Model decides whether to call functions
- `"required"`: Model must call at least one function
- `"none"`: Never call functions
- `{"type": "function", "function": {"name": "fn_name"}}`: Force specific function

### 6 Calling Patterns

1. **Simple**: Single function, single call
2. **Multiple functions**: Multiple tools available, model picks one
3. **Parallel**: Same function called multiple times in one turn
4. **Parallel multiple**: Different functions called in one turn
5. **Multi-step**: Chained calls (call -> result -> call -> result) within one turn
6. **Multi-turn**: Function calls across conversation turns with maintained context

### Supported Models for Function Calling

openai/gpt-oss-120b, openai/gpt-oss-20b, moonshotai/Kimi-K2.5, zai-org/GLM-5, zai-org/GLM-4.5-Air-FP8,
MiniMaxAI/MiniMax-M2.5, Qwen/Qwen3-Next-80B-A3B-Instruct, Qwen/Qwen3.5-397B-A17B,
Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8, deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-V3,
meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8, meta-llama/Llama-3.3-70B-Instruct-Turbo,
Qwen/Qwen2.5-7B-Instruct-Turbo, mistralai/Mistral-Small-24B-Instruct-2501

## Structured Outputs (JSON Mode)

### json_schema (Recommended)

Constrain output to match your JSON schema exactly. Use Pydantic in Python and Zod in TypeScript to
define schemas:

```python
import json
from together import Together
from pydantic import BaseModel, Field

client = Together()

class VoiceNote(BaseModel):
    title: str = Field(description="A title for the voice note")
    summary: str = Field(description="A short one sentence summary of the voice note.")
    actionItems: list[str] = Field(description="A list of action items from the voice note")

transcript = (
    "Good morning! Today is going to be a busy day. First, I need to make a quick breakfast. "
    "While cooking, I'll also check my emails to see if there's anything urgent."
)

extract = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": (
                "The following is a voice message transcript. Only answer in JSON "
                f"and follow this schema {json.dumps(VoiceNote.model_json_schema())}."
            ),
        },
        {"role": "user", "content": transcript},
    ],
    model="openai/gpt-oss-20b",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "voice_note",
            "schema": VoiceNote.model_json_schema(),
        },
    },
)

output = json.loads(extract.choices[0].message.content)
print(json.dumps(output, indent=2))
```

```typescript
import Together from "together-ai";
import { z } from "zod";

const together = new Together();

const voiceNoteSchema = z.object({
  title: z.string().describe("A title for the voice note"),
  summary: z
    .string()
    .describe("A short one sentence summary of the voice note."),
  actionItems: z
    .array(z.string())
    .describe("A list of action items from the voice note"),
});
const jsonSchema = z.toJSONSchema(voiceNoteSchema);

async function main() {
  const transcript =
    "Good morning! Today is going to be a busy day. First, I need to make a quick " +
    "breakfast. While cooking, I'll also check my emails to see if there's anything urgent.";
  const extract = await together.chat.completions.create({
    messages: [
      {
        role: "system",
        content: `The following is a voice message transcript. Only answer in JSON and follow this schema ${JSON.stringify(jsonSchema)}.`,
      },
      { role: "user", content: transcript },
    ],
    model: "openai/gpt-oss-20b",
    response_format: {
      type: "json_schema",
      json_schema: {
        name: "voice_note",
        schema: jsonSchema,
      },
    },
  });

  if (extract?.choices?.[0]?.message?.content) {
    const output = JSON.parse(extract.choices[0].message.content);
    console.log(output);
  }
}

main();
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "The following is a voice message transcript. Only answer in JSON."
      },
      {
        "role": "user",
        "content": "Good morning! Today is going to be a busy day. First, I need to make a quick breakfast. While cooking, I will also check my emails."
      }
    ],
    "model": "openai/gpt-oss-20b",
    "response_format": {
      "type": "json_schema",
      "schema": {
        "properties": {
          "title": { "type": "string", "description": "A title for the voice note" },
          "summary": { "type": "string", "description": "A short one sentence summary" },
          "actionItems": {
            "items": { "type": "string" },
            "type": "array",
            "description": "Action items"
          }
        },
        "required": ["title", "summary", "actionItems"],
        "type": "object"
      }
    }
  }'
```

### json_object (Simple)

Model outputs valid JSON, structure guided by prompt only:

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": "Respond in JSON with keys: name, age, city"},
        {"role": "user", "content": "Tell me about yourself"},
    ],
    response_format={"type": "json_object"},
)
```

```typescript
const response = await together.chat.completions.create({
  model: "openai/gpt-oss-20b",
  messages: [
    { role: "system", content: "Respond in JSON with keys: name, age, city" },
    { role: "user", content: "Tell me about yourself" },
  ],
  response_format: { type: "json_object" },
});
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [
      {"role": "system", "content": "Respond in JSON with keys: name, age, city"},
      {"role": "user", "content": "Tell me about yourself"}
    ],
    "response_format": {"type": "json_object"}
  }'
```

### regex (Pattern Matching)

Constrain output to match a regex:

```python
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    temperature=0.2,
    max_tokens=10,
    messages=[
        {
            "role": "system",
            "content": "Classify the sentiment of the text as positive, neutral, or negative.",
        },
        {"role": "user", "content": "Wow. I loved the movie!"},
    ],
    response_format={"type": "regex", "pattern": "(positive|neutral|negative)"},
)
print(response.choices[0].message.content)
```

```typescript
const response = await together.chat.completions.create(
  {
    model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    temperature: 0.2,
    max_tokens: 10,
    messages: [
      {
        role: "system",
        content:
          "Classify the sentiment of the text as positive, neutral, or negative.",
      },
      { role: "user", content: "Wow. I loved the movie!" },
    ],
    response_format: {
      type: "regex",
      pattern: "(positive|neutral|negative)",
    },
  } as any
);

console.log(response?.choices[0]?.message?.content);
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "temperature": 0.2,
    "max_tokens": 10,
    "messages": [
      {
        "role": "system",
        "content": "Classify the sentiment of the text as positive, neutral, or negative."
      },
      {"role": "user", "content": "Wow. I loved the movie!"}
    ],
    "response_format": {"type": "regex", "pattern": "(positive|neutral|negative)"}
  }'
```

**JSON mode supported models**: DeepSeek R1/V3, GLM-5, Kimi K2.5, Llama 3.x/4, Qwen 2.5/3/3.5, GPT-OSS,
and many more. All models supported for JSON mode also support regex mode.

## Reasoning Models

Reasoning models think step-by-step before answering. Best for complex math, code, planning, and logic
tasks.

**How reasoning output is returned:**
- **Most reasoning models** (Kimi K2.5, GLM-5, DeepSeek V3.1, GPT-OSS, Qwen3.5, etc.) return reasoning
  in a separate `reasoning` field: `response.choices[0].message.reasoning`
- **DeepSeek R1** is a special case that outputs reasoning inside `<think>` tags within `content`

### Quick Start

Most reasoning models return a separate `reasoning` field alongside `content`. Since reasoning models
produce longer outputs, streaming is recommended:

```python
from together import Together

client = Together()

stream = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[
        {"role": "user", "content": "Which number is bigger, 9.11 or 9.9?"},
    ],
    stream=True,
)

for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta

        # Show reasoning tokens if present
        if hasattr(delta, "reasoning") and delta.reasoning:
            print(delta.reasoning, end="", flush=True)

        # Show content tokens if present
        if hasattr(delta, "content") and delta.content:
            print(delta.content, end="", flush=True)
```

```typescript
import Together from "together-ai";
import type { ChatCompletionChunk } from "together-ai/resources/chat/completions";

const together = new Together();

const stream = await together.chat.completions.stream({
  model: "moonshotai/Kimi-K2.5",
  messages: [
    { role: "user", content: "Which number is bigger, 9.11 or 9.9?" },
  ],
} as any);

for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta as ChatCompletionChunk.Choice.Delta & {
    reasoning?: string;
  };

  // Show reasoning tokens if present
  if (delta?.reasoning) process.stdout.write(delta.reasoning);

  // Show content tokens if present
  if (delta?.content) process.stdout.write(delta.content);
}
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-K2.5",
    "messages": [
      {"role": "user", "content": "Which number is bigger, 9.11 or 9.9?"}
    ],
    "stream": true
  }'
```

DeepSeek R1 uses a different format -- reasoning is inside `<think>` tags within the `content` field:

```python
stream = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "Which is bigger: 9.9 or 9.11?"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

Output:
```
<think>
Let me compare 9.9 and 9.11...
9.9 = 9.90, and 9.90 > 9.11
</think>

**Answer:** 9.9 is bigger.
```

### Supported Reasoning Models

| Model | API String | Type | Context | Tool Calling |
|-------|-----------|------|---------|--------------|
| DeepSeek R1 | `deepseek-ai/DeepSeek-R1` | Reasoning only | 164K | No |
| DeepSeek V3.1 | `deepseek-ai/DeepSeek-V3.1` | Hybrid (off by default) | 164K | Non-reasoning only |
| GPT-OSS 120B | `openai/gpt-oss-120b` | Adjustable effort | 128K | No |
| GPT-OSS 20B | `openai/gpt-oss-20b` | Adjustable effort | 128K | No |
| Kimi K2.5 | `moonshotai/Kimi-K2.5` | Hybrid (on by default) | 256K | Yes |
| GLM-5 | `zai-org/GLM-5` | Hybrid (on by default) | 200K | Yes |
| MiniMax M2.5 | `MiniMaxAI/MiniMax-M2.5` | Reasoning only | 228.7K | No |
| Qwen3.5 397B | `Qwen/Qwen3.5-397B-A17B` | Hybrid (on by default) | 128K | No |
| Qwen3.5 9B | `Qwen/Qwen3.5-9B` | Hybrid (on by default) | 128K | No |

**Type definitions:**
- **Reasoning only**: Always produces reasoning tokens. Cannot be toggled off.
- **Hybrid**: Supports both reasoning and non-reasoning modes via `reasoning={"enabled": True/False}`.
- **Adjustable effort**: Supports `reasoning_effort` parameter (`"low"`, `"medium"`, `"high"`).

### Enabling and Disabling Reasoning

Hybrid models let you toggle reasoning on or off using the `reasoning` parameter. This is useful when
you want reasoning for complex queries but faster, cheaper responses for simple ones:

```python
# Enable reasoning (thinking mode)
stream = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[
        {"role": "user", "content": "Which number is bigger, 9.11 or 9.9? Think carefully."},
    ],
    reasoning={"enabled": True},
    temperature=1.0,
    top_p=0.95,
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta
    if hasattr(delta, "reasoning") and delta.reasoning:
        print(delta.reasoning, end="", flush=True)
    if hasattr(delta, "content") and delta.content:
        print(delta.content, end="", flush=True)
```

```typescript
import Together from "together-ai";
import type {
  ChatCompletionChunk,
  CompletionCreateParamsStreaming,
} from "together-ai/resources/chat/completions";

const together = new Together();

type ReasoningParams = CompletionCreateParamsStreaming & {
  reasoning?: { enabled: boolean };
};

type ReasoningDelta = ChatCompletionChunk.Choice.Delta & {
  reasoning?: string;
};

const params: ReasoningParams = {
  model: "moonshotai/Kimi-K2.5",
  messages: [
    {
      role: "user",
      content: "Which number is bigger, 9.11 or 9.9? Think carefully.",
    },
  ],
  reasoning: { enabled: true },
  temperature: 1.0,
  top_p: 0.95,
  stream: true,
};

const stream = await together.chat.completions.create(params);

for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta as ReasoningDelta;
  if (delta?.reasoning) process.stdout.write(delta.reasoning);
  if (delta?.content) process.stdout.write(delta.content);
}
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/Kimi-K2.5",
    "messages": [
      {"role": "user", "content": "Which number is bigger, 9.11 or 9.9? Think carefully."}
    ],
    "reasoning": {"enabled": true},
    "temperature": 1.0,
    "stream": true
  }'
```

**Models supporting `reasoning={"enabled": True/False}`:**
- `deepseek-ai/DeepSeek-V3.1` (off by default)
- `Qwen/Qwen3.5-397B-A17B` (on by default)
- `Qwen/Qwen3.5-9B` (on by default)
- `moonshotai/Kimi-K2.5` (on by default)
- `zai-org/GLM-5` (on by default)

Note: For DeepSeek V3.1, function calling only works in non-reasoning mode
(`reasoning={"enabled": False}`).

You can also toggle reasoning via `chat_template_kwargs`:

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3.5-397B-A17B",
    messages=[{"role": "user", "content": "Prove that sqrt(2) is irrational."}],
    chat_template_kwargs={"thinking": True},
    stream=True,
)
```

### Reasoning Effort

GPT-OSS models support a `reasoning_effort` parameter that controls how much computation the model
spends on reasoning (`"low"`, `"medium"`, `"high"`):

```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Prove the infinitude of primes"}],
    temperature=1.0,
    top_p=1.0,
    reasoning_effort="high",
    stream=True,
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

```typescript
import Together from "together-ai";
const together = new Together();

const stream = await together.chat.completions.create({
  model: "openai/gpt-oss-120b",
  messages: [
    {
      role: "user",
      content:
        "Solve: If all roses are flowers and some flowers are red, can we conclude some roses are red?",
    },
  ],
  temperature: 1.0,
  top_p: 1.0,
  reasoning_effort: "medium",
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {"role": "user", "content": "Prove the infinitude of primes"}
    ],
    "temperature": 1.0,
    "reasoning_effort": "high",
    "stream": true
  }'
```

- `"low"`: Faster responses for simpler tasks with reduced reasoning depth.
- `"medium"`: Balanced performance for most use cases (recommended default).
- `"high"`: Maximum reasoning for complex problems. Set `max_tokens` to ~30,000 with this setting.

### Controlling Reasoning Depth via Prompting

For models that do not support `reasoning_effort` (e.g., DeepSeek R1), you can influence how much the
model thinks by including instructions in your prompt:

```python
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[
        {
            "role": "user",
            "content": (
                "Please use around 1000 words to think, but do not literally count each one.\n\n"
                "Explain why quicksort has O(n log n) average-case complexity."
            ),
        }
    ],
    stream=True,
)
```

### Accessing Reasoning Output

**Most models (Kimi K2.5, GLM-5, DeepSeek V3.1, GPT-OSS, Qwen3.5) -- use the `reasoning` field:**

Non-streaming:

```python
response = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[{"role": "user", "content": "Say test 10 times"}],
)
print("Reasoning:", response.choices[0].message.reasoning)
print("Answer:", response.choices[0].message.content)
```

Streaming (check for `reasoning` on the delta):

```python
for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta
        if hasattr(delta, "reasoning") and delta.reasoning:
            print(delta.reasoning, end="", flush=True)
        if hasattr(delta, "content") and delta.content:
            print(delta.content, end="", flush=True)
```

**DeepSeek R1 -- parse `<think>` tags from `content`:**

```python
import re
content = response.choices[0].message.content
think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
thinking = think_match.group(1).strip() if think_match else ""
answer = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
```

### Best Practices

- **DeepSeek R1**: Use temperature 0.5-0.7, omit system prompts, put instructions in user message,
  avoid few-shot examples, no chain-of-thought prompting (it already reasons)
- Use streaming -- reasoning outputs are long
- Use `reasoning_effort="low"` for simple questions, `"high"` for complex math/code/logic
- Reasoning models cost more (more tokens) -- use standard models for simple tasks
- For hybrid models, disable reasoning on simple tasks to save cost and latency

## Debug Mode

Send the `x-together-debug: 1` header to get detailed response headers for debugging latency,
routing, and request tracing. Use `with_raw_response` to access both the parsed response and headers.

```python
from together import Together
import json

client = Together()

response = client.chat.completions.with_raw_response.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": "Say hello"}],
    extra_headers={"x-together-debug": "1"},
)

# Parsed API object (same as .create() would return)
parsed = response.parse()
print(parsed.choices[0].message.content)

# Inspect response headers for debugging
headers = dict(response.headers)
print(json.dumps(headers, indent=2))
```

```typescript
import Together from "together-ai";

const client = new Together();

const response = await client.chat.completions.create(
  {
    model: "openai/gpt-oss-20b",
    messages: [{ role: "user", content: "Say hello" }],
  },
  { headers: { "x-together-debug": "1" } }
).asResponse();

const parsed = await response.json();
console.log(parsed.choices[0].message.content);

// Inspect response headers
for (const [key, value] of response.headers.entries()) {
  if (key.startsWith("x-")) console.log(`${key}: ${value}`);
}
```

```shell
curl -s -D - -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "x-together-debug: 1" \
  -d '{"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":"Say hello"}]}'
```

**Key debug headers returned:**

| Header | Description |
|--------|-------------|
| `x-request-id` | Unique request ID for support tickets |
| `x-together-traceid` | Distributed trace ID for internal routing |
| `x-cluster` | Inference cluster that served the request |
| `x-engine-pod` | Specific engine pod that processed the request |
| `x-api-received` | Timestamp when the API received the request |
| `x-api-call-start` | Timestamp when inference started |
| `x-api-call-end` | Timestamp when inference completed |
| `x-inference-version` | Inference engine version |

## Resources

- **Model catalog and specs**: See [references/models.md](references/models.md)
- **Full parameter reference**: See [references/api-parameters.md](references/api-parameters.md)
- **Function calling patterns (detailed)**: See
  [references/function-calling-patterns.md](references/function-calling-patterns.md)
- **Structured output details**: See [references/structured-outputs.md](references/structured-outputs.md)
- **Reasoning model details**: See [references/reasoning-models.md](references/reasoning-models.md)
- **Runnable scripts (Python + TypeScript)**:
  - [scripts/chat_basic.py](scripts/chat_basic.py) /
    [chat_basic.ts](scripts/chat_basic.ts) -- basic chat, streaming, multi-turn
  - [scripts/structured_outputs.py](scripts/structured_outputs.py) /
    [structured_outputs.ts](scripts/structured_outputs.ts) -- json_schema, json_object, regex
  - [scripts/reasoning_models.py](scripts/reasoning_models.py) /
    [reasoning_models.ts](scripts/reasoning_models.ts) -- reasoning field, effort, hybrid toggle
  - [scripts/tool_call_loop.py](scripts/tool_call_loop.py) /
    [tool_call_loop.ts](scripts/tool_call_loop.ts) -- function calling with parallel calls
  - [scripts/async_parallel.py](scripts/async_parallel.py) -- async parallel requests (Python)
- **Official docs**: [Chat Overview](https://docs.together.ai/docs/chat-overview)
- **Official docs**: [Inference Parameters](https://docs.together.ai/docs/inference-parameters)
- **Official docs**: [Serverless Models](https://docs.together.ai/docs/serverless-models)
- **Official docs**: [Function Calling](https://docs.together.ai/docs/function-calling)
- **Official docs**: [JSON Mode](https://docs.together.ai/docs/json-mode)
- **Official docs**: [Reasoning Overview](https://docs.together.ai/docs/reasoning-overview)
- **Official docs**: [DeepSeek R1](https://docs.together.ai/docs/deepseek-r1)
- **API reference**: [Chat Completions API](https://docs.together.ai/reference/chat-completions)
