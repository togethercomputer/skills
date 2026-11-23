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
- [OpenAI Compatibility](#openai-compatibility)
- [Rate Limits](#rate-limits)
- [Debug Mode](#debug-mode)
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
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Weather in NYC?"}],
    tools=tools,
    tool_choice="auto",
)
```

```typescript
const response = await together.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
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
| `safety_model` | string | Moderation model used to validate tokens; no moderation model is currently served serverless |
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
    if not chunk.choices:  # final usage-only chunk
        continue
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
    model="moonshotai/Kimi-K3",
    messages=[{"role": "user", "content": "Which is bigger, 9.11 or 9.9?"}],
    reasoning={"enabled": True},
    temperature=1.0,
    stream=True,
)

for chunk in stream:
    if not chunk.choices:  # final usage-only chunk
        continue
    delta = chunk.choices[0].delta
    trace = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
    if trace:
        print(trace, end="", flush=True)
    if hasattr(delta, "content") and delta.content:
        print(delta.content, end="", flush=True)
```

### Enabling/Disabling Reasoning (TypeScript)

```typescript
import type { ChatCompletionChunk } from "together-ai/resources/chat/completions";

type ReasoningDelta = ChatCompletionChunk.Choice.Delta & {
  reasoning?: string;
  reasoning_content?: string;
};

const stream = await together.chat.completions.create({
  model: "moonshotai/Kimi-K3",
  messages: [{ role: "user", content: "Which is bigger, 9.11 or 9.9?" }],
  reasoning: { enabled: true },
  temperature: 1.0,
  stream: true,
} as any);

for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta as ReasoningDelta;
  const trace = delta?.reasoning ?? delta?.reasoning_content;
  if (trace) process.stdout.write(trace);
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

## OpenAI Compatibility

Migrate from the OpenAI SDK by changing the base URL and API key while keeping the chat/completions
shape the same:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.together.xyz/v1",
    api_key="YOUR_TOGETHER_API_KEY",
)
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

Use the native Together SDK when you need Together-only helpers such as `.with_raw_response`,
typed reasoning fields, or other platform-specific workflows already covered by this skill.

## Rate Limits

Serverless has no published per-account request limits. Build Tiers 1 to 5 and their RPM table
were retired in April 2026, and the dynamic limits that replaced them were retired in October
2026. Most requests are not rate limited. During high demand Together may limit requests to
protect performance, and a model in especially high demand can get its own limit.

- **429 Too Many Requests:** reduce the request rate, spread requests out, and retry with
  exponential backoff.
- **503 Service Unavailable:** wait briefly, then retry with backoff.

Do not plan against rate-limit response headers. On 2026-11-18, successful serverless chat
responses from three models (`Qwen/Qwen3.5-9B`, `openai/gpt-oss-120b`, `moonshotai/Kimi-K3`)
carried no `x-ratelimit-*` or `x-tokenlimit-*` headers.

Best practices:

- keep traffic steady instead of bursty
- use batch inference for high-volume offline jobs
- for strict capacity or SLA requirements, use provisioned throughput (reserved capacity on supported stock models with a defined throughput and reliability SLA, contact sales) or dedicated endpoints (single-tenant GPUs, self-serve)

## Debug Mode

Send the `x-together-debug: 1` header to get detailed routing and latency headers. Use
`.with_raw_response` in Python or `.asResponse()` in TypeScript when you need both the parsed body
and the raw headers.

```python
from together import Together
import json

client = Together()

response = client.chat.completions.with_raw_response.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Say hello"}],
    extra_headers={"x-together-debug": "1"},
)

parsed = response.parse()
print(parsed.choices[0].message.content)

headers = dict(response.headers)
print(json.dumps(headers, indent=2))
```

```typescript
import Together from "together-ai";

const client = new Together();

const response = await client.chat.completions.create(
  {
    model: "openai/gpt-oss-120b",
    messages: [{ role: "user", content: "Say hello" }],
  },
  { headers: { "x-together-debug": "1" } }
).asResponse();

const parsed = await response.json();
console.log(parsed.choices[0].message.content);

for (const [key, value] of response.headers.entries()) {
  if (key.startsWith("x-")) console.log(`${key}: ${value}`);
}
```

```shell
curl -s -D - -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "x-together-debug: 1" \
  -d '{"model":"openai/gpt-oss-120b","messages":[{"role":"user","content":"Say hello"}]}'
```

Common debug headers:

| Header | Description |
|--------|-------------|
| `x-request-id` | Unique request ID for support tickets |
| `x-together-traceid` | Distributed trace ID for internal routing |
| `x-cluster` | Inference cluster that served the request |
| `x-engine-pod` | Engine pod that processed the request |
| `x-api-received` | Timestamp when the API received the request |
| `x-api-call-start` | Timestamp when inference started |
| `x-api-call-end` | Timestamp when inference completed |
| `x-inference-version` | Inference engine version |

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request: invalid params, or input tokens plus `max_tokens` exceed the model's context length |
| 401 | Unauthorized (invalid API key) |
| 402 | Payment required (spending limit reached) |
| 403 | Forbidden: the account cannot use the model or feature (plan, credit card on file, or an organization setting such as third-party data sharing) |
| 404 | Model not found |
| 413 | Request body too large. Pass large images or audio as a URL instead of inline base64 |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Service overloaded |
| 504 | Request timeout |
| 524 | Timeout at the network edge. Wait briefly, then retry |
| 529 | Model at its maximum replica count. Retry with exponential backoff |
