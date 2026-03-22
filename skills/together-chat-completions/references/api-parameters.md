# Chat Completions API Parameters
## Contents

- [Required Parameters](#required-parameters)
- [Generation Parameters](#generation-parameters)
- [Output Control](#output-control)
- [Response Format](#response-format)
- [Function Calling](#function-calling)
- [Safety & Compliance](#safety-compliance)
- [Reasoning](#reasoning)
- [Context Handling](#context-handling)
- [Message Object](#message-object)
- [HTTP Status Codes](#http-status-codes)


## Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model identifier (e.g., `meta-llama/Llama-3.3-70B-Instruct-Turbo`) |
| `messages` | array | Array of message objects with `role` and `content` |

## Generation Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_tokens` | integer | varies | 1+ | Maximum tokens to generate |
| `temperature` | float | varies | 0-2 | Randomness. Lower = more deterministic |
| `top_p` | float | 1.0 | 0-1 | Nucleus sampling threshold |
| `top_k` | integer | - | 1+ | Limit choices per token step |
| `min_p` | float | - | 0-1 | Alternative to top_p/top_k |
| `repetition_penalty` | float | 1.0 | - | Higher = less repetition |
| `presence_penalty` | float | 0 | -2.0 to 2.0 | Penalize tokens already present |
| `frequency_penalty` | float | 0 | -2.0 to 2.0 | Penalize frequent tokens |
| `stop` | string[] | - | - | Sequences that stop generation |
| `n` | integer | 1 | 1-128 | Number of completions to generate |
| `seed` | integer | - | - | For reproducible outputs |

### Python Example

```python
from together import Together

client = Together()

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello!"},
    ],
    max_tokens=512,
    temperature=0.7,
    top_p=0.9,
    stop=["END"],
)
print(response.choices[0].message.content)
```

### TypeScript Example

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  messages: [
    { role: "system", content: "You are a helpful assistant" },
    { role: "user", content: "Hello!" },
  ],
  max_tokens: 512,
  temperature: 0.7,
  top_p: 0.9,
  stop: ["END"],
});
console.log(response.choices[0].message.content);
```

## Output Control

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stream` | bool | false | Stream tokens as Server-Sent Events |
| `logprobs` | integer | - | Return top-k token log probs (0-20) |
| `echo` | bool | false | Include prompt in response |
| `logit_bias` | object | - | Token ID to bias value mapping |

### Streaming Example (Python)

```python
stream = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Streaming Example (TypeScript)

```typescript
const stream = await together.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  messages: [{ role: "user", content: "Write a story" }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

## Response Format

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_format` | object | Control output structure |

Options:

```python
# Plain text (default)
response_format={"type": "text"}

# JSON object (model decides structure, guided by prompt)
response_format={"type": "json_object"}

# JSON schema (constrained to your schema) -- nested format with name
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "my_schema",
        "schema": {...},
    },
}

# Regex pattern matching
response_format={"type": "regex", "pattern": "(positive|neutral|negative)"}
```

```typescript
// JSON schema (TypeScript with Zod)
import { z } from "zod";

const schema = z.object({ name: z.string(), age: z.number() });
const jsonSchema = z.toJSONSchema(schema);

response_format: {
  type: "json_schema",
  json_schema: {
    name: "person",
    schema: jsonSchema,
  },
}
```

## Function Calling

| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | array | Tool definitions the model can call |
| `tool_choice` | string/object | `"auto"`, `"required"`, `"none"`, or specific function |

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    },
}]

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Weather in NYC?"}],
    tools=tools,
    tool_choice="auto",
)
```

```typescript
const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages: [{ role: "user", content: "Weather in NYC?" }],
  tools: [
    {
      type: "function",
      function: {
        name: "getWeather",
        description: "Get weather for a location",
        parameters: {
          type: "object",
          properties: {
            location: { type: "string", description: "City name" },
          },
          required: ["location"],
        },
      },
    },
  ],
  tool_choice: "auto",
});
```

## Safety & Compliance

| Parameter | Type | Description |
|-----------|------|-------------|
| `safety_model` | string | Moderation model (e.g., `meta-llama/Llama-Guard-4-12B`) |
| `compliance` | string | Set to `"hipaa"` for HIPAA mode |

## Reasoning

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `reasoning_effort` | string | `"low"`, `"medium"`, `"high"` | Control reasoning depth (GPT-OSS only) |
| `reasoning` | object | `{"enabled": true/false}` | Toggle reasoning for hybrid models |
| `chat_template_kwargs` | object | `{"thinking": true}` | Alternative reasoning toggle |

### Reasoning Effort (Python)

```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Prove the infinitude of primes"}],
    temperature=1.0,
    top_p=1.0,
    reasoning_effort="medium",
    stream=True,
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Reasoning Effort (TypeScript)

```typescript
const stream = await together.chat.completions.create({
  model: "openai/gpt-oss-120b",
  messages: [{ role: "user", content: "Prove the infinitude of primes" }],
  temperature: 1.0,
  top_p: 1.0,
  reasoning_effort: "medium",
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

### Enabling/Disabling Reasoning (Python)

```python
stream = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[{"role": "user", "content": "Which is bigger, 9.11 or 9.9?"}],
    reasoning={"enabled": True},
    temperature=1.0,
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta
    if hasattr(delta, "reasoning") and delta.reasoning:
        print(delta.reasoning, end="", flush=True)
    if hasattr(delta, "content") and delta.content:
        print(delta.content, end="", flush=True)
```

### Enabling/Disabling Reasoning (TypeScript)

```typescript
import type { ChatCompletionChunk } from "together-ai/resources/chat/completions";

type ReasoningDelta = ChatCompletionChunk.Choice.Delta & {
  reasoning?: string;
};

const stream = await together.chat.completions.create({
  model: "moonshotai/Kimi-K2.5",
  messages: [{ role: "user", content: "Which is bigger, 9.11 or 9.9?" }],
  reasoning: { enabled: true },
  temperature: 1.0,
  stream: true,
} as any);

for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta as ReasoningDelta;
  if (delta?.reasoning) process.stdout.write(delta.reasoning);
  if (delta?.content) process.stdout.write(delta.content);
}
```

## Context Handling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context_length_exceeded_behavior` | string | `"error"` | `"truncate"` or `"error"` when exceeding context |

## Message Object

```python
{"role": "system", "content": "You are a helpful assistant."}
{"role": "user", "content": "Hello!"}
{"role": "assistant", "content": "Hi there!"}
{"role": "tool", "tool_call_id": "...", "content": "..."}
```

Multimodal content (vision models):

```python
{"role": "user", "content": [
    {"type": "text", "text": "What's in this image?"},
    {"type": "image_url", "image_url": {"url": "https://..."}},
    {"type": "video_url", "video_url": {"url": "https://..."}},
    {"type": "audio_url", "audio_url": {"url": "https://..."}},
]}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid params) |
| 401 | Unauthorized (invalid API key) |
| 402 | Payment required (spending limit reached) |
| 403 | Input token count + max_tokens exceeds model context length |
| 404 | Model not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Service overloaded |
| 504 | Request timeout |
