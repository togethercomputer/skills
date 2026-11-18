# Reasoning Models Reference
## Contents

- [Full Model Table](#full-model-table)
- [Reasoning Controls by Model](#reasoning-controls-by-model)
- [Reasoning Effort Levels](#reasoning-effort-levels)
- [Enabling and Disabling Reasoning (Hybrid Models)](#enabling-and-disabling-reasoning)
- [Controlling Reasoning Depth via Prompting](#controlling-reasoning-depth-via-prompting)
- [Reasoning Output Format](#reasoning-output-format)
- [Tracking Reasoning and Cached Token Usage](#tracking-reasoning-and-cached-token-usage)
- [Structured Outputs with Reasoning](#structured-outputs-with-reasoning)
- [Best Practices by Model](#best-practices-by-model)


## Full Model Table

Serverless reasoning models as of 2026-10-07 (source:
[Reasoning](https://docs.together.ai/docs/inference/chat/reasoning)). Kimi K2.x, GLM-5, DeepSeek-R1
and its distillations, QwQ-32B, and DeepSeek V3.1 are no longer serverless; only some of them can
run on dedicated endpoints (see the deprecations page). The trace arrives on
`reasoning` or `reasoning_content` depending on the model (Kimi K3 uses `reasoning_content`), so
read both.

| Model | API String | Type | Context | Tool Calling |
|-------|-----------|------|---------|--------------|
| Kimi K3 | `moonshotai/Kimi-K3` | Hybrid (on by default) | 1M | Yes |
| DeepSeek V4 Pro 0813 | `deepseek-ai/DeepSeek-V4-Pro-0813` | Hybrid (on by default) | 1M | Yes |
| GLM-5.2 | `zai-org/GLM-5.2` | Hybrid (on by default) | 512K | Yes |
| MiniMax M3 | `MiniMaxAI/MiniMax-M3` | Hybrid (on by default) | 512K | Yes |
| Qwen3.6 Plus | `Qwen/Qwen3.6-Plus` | Hybrid (on by default) | 1M | No |
| Qwen3.5 9B | `Qwen/Qwen3.5-9B` | Hybrid (on by default) | 262K | Yes |
| GPT-OSS 120B | `openai/gpt-oss-120b` | Adjustable effort | 128K | Yes |

**Type definitions:**
- **Reasoning only**: Always produces reasoning tokens. Cannot be toggled off.
- **Hybrid**: Supports both reasoning and non-reasoning modes via `reasoning={"enabled": True/False}`.
- **Adjustable effort**: Supports `reasoning_effort` parameter (`"low"`, `"medium"`, `"high"`).

The types are the documented ones. What each model did with each control when measured is in the
next section, and it does not always match the type. Checked 2026-11-18: `MiniMaxAI/MiniMax-M3`
is no longer in the serverless model list, and `MiniMaxAI/MiniMax-M3.1-Flash` is.

## Reasoning Controls by Model

Which control a model honors differs by model, and the API answers HTTP 200 to a control the
model ignores. So a setting can look accepted and change nothing.

Measured 2026-11-18 on serverless with one date-arithmetic prompt that has a two-word answer,
`max_tokens: 1200`, and one or two requests per cell (non-streaming, except Qwen3.6 Plus, which
only streams). Each number is one request's `usage.completion_tokens_details.reasoning_tokens`.
`cap` means the request hit `max_tokens` while still reasoning and returned empty `content`.
`off` means no reasoning tokens and no trace. The samples are small and these behaviors change,
so treat the table as a starting point and measure on your own prompt.

| Model | Default | `reasoning: {"enabled": false}` | `chat_template_kwargs` `enable_thinking: false` / `thinking: false` | `reasoning_effort: "low"` | `"high"` | `"none"` | Trace field |
|---|---|---|---|---|---|---|---|
| `openai/gpt-oss-120b` | 235, 858 | ignored (911) | ignored (966 / 1135) | 299, 474 | cap, cap | accepted (768) | `reasoning_content` |
| `Qwen/Qwen3.5-9B` | cap, cap | off | off / off | cap, cap | cap, cap | off | `reasoning_content` |
| `Qwen/Qwen3.6-Plus` | 2136, 2211 | off | off / off | 1487, 1755 | 1695, 2045 | off | `reasoning` |
| `moonshotai/Kimi-K3` | 484, 890 | off | off / off | 209, 225 | 361, 437 | off | `reasoning_content` |
| `deepseek-ai/DeepSeek-V4-Pro-0813` | 709, 770 | ignored (438) | off / off | 563, 736 | 581, 723 | accepted (483) | `reasoning_content` |
| `deepseek-ai/DeepSeek-V4.1-Flash` | 385, 532 | off | off / off | 315, 401 | 454, 485 | off | `reasoning_content` |
| `zai-org/GLM-5.2` | cap, cap | off | off / off | 771, 952 | 633, 918 | off | `reasoning_content` |
| `zai-org/GLM-5.3` | 853, 946 | ignored (880) | ignored (cap / 999) | 55, 57 | 111, 204 | HTTP 400 | `reasoning_content` |
| `zai-org/GLM-5.3-Flash` | 502, 591 | ignored (530) | ignored (507 / 1018) | 122, 130 | 137, 165 | accepted (403) | `reasoning_content` |
| `MiniMaxAI/MiniMax-M3.1-Flash` | 697, 724 | off | ignored (765 / 1126) | 203, 362 | 576, 936 | accepted (550) | `reasoning_content` |
| `meta-models/Muse-Glimmer-30B` | cap, cap | ignored (1068) | ignored (1036 / 984) | 355, 460 | 1172, cap | accepted (428) | `reasoning` |

Muse Glimmer 30B returned no `reasoning_tokens` in `usage`, so its numbers are
`completion_tokens`. "Trace field" is the key on the response message (for Qwen3.6 Plus, on the
streaming delta). Streaming deltas used the same key as the message on the five models checked:
GPT-OSS 120B, Qwen3.5 9B, Kimi K3, DeepSeek V4 Pro 0813, and Muse Glimmer 30B.

What the measurements say:

- **Turning reasoning off.** `reasoning: {"enabled": false}` worked on Qwen3.5 9B, Qwen3.6 Plus,
  Kimi K3, DeepSeek V4.1 Flash, GLM-5.2, and MiniMax M3.1 Flash. DeepSeek V4 Pro 0813 ignored it
  and went off only with `chat_template_kwargs` (`{"enable_thinking": false}` or
  `{"thinking": false}`). MiniMax M3.1 Flash is the reverse: it ignored both `chat_template_kwargs`
  keys. GPT-OSS 120B, GLM-5.3, GLM-5.3 Flash, and Muse Glimmer 30B kept reasoning under every off
  switch tried.
- **`reasoning_effort`.** `low` cut reasoning well below the default in both samples on GLM-5.3
  (55 and 57 against 853 and 946), GLM-5.3 Flash, Kimi K3, and MiniMax M3.1 Flash. On GPT-OSS 120B
  and Muse Glimmer 30B, `low` finished in a few hundred tokens where `high` hit the cap or came
  within 30 tokens of it. On DeepSeek V4 Pro 0813, GLM-5.2, and Qwen3.6 Plus, `low` and `high`
  overlapped, and on DeepSeek V4.1 Flash the gap was small, so the level made no clear difference
  there. On Qwen3.5 9B every request with reasoning on hit the cap, so its effort levels could
  not be compared.
- **`reasoning_effort: "none"`** turned reasoning off on Qwen3.5 9B, Qwen3.6 Plus, Kimi K3,
  DeepSeek V4.1 Flash, and GLM-5.2. GLM-5.3 rejected it with HTTP 400
  `reasoning_effort_not_allowed` ("only low, high or max is allowed for this model"). The other
  five accepted it and kept reasoning.
- **Reasoning off cost accuracy on this prompt.** With reasoning on, all 72 answers that completed
  were correct. With it off, 15 of 23 were. Check accuracy before you ship an off switch.
- **Budget for the trace.** With no control set, Qwen3.5 9B, GLM-5.2, and Muse Glimmer 30B spent
  all 1,200 tokens on reasoning and returned empty `content`. Qwen3.6 Plus returned 2,143 and
  2,218 completion tokens with `max_tokens: 1200`, so the limit did not hold there.
- **Confirm a control worked.** Compare `reasoning_tokens` (or `completion_tokens` where there
  are none) with and without the control on the same prompt, a few times. The status code does
  not tell you.

## Reasoning Effort Levels

GPT-OSS models support `reasoning_effort` to control reasoning depth:

| Level | Behavior | Best For |
|-------|----------|----------|
| `"low"` | Minimal thinking, fast | Simple factual questions |
| `"medium"` | Balanced (recommended default) | Most tasks |
| `"high"` | Extensive thinking, thorough | Complex math, code, logic proofs |

### Python

```python
from together import Together

client = Together()

stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Prove the infinitude of primes"}],
    temperature=1.0,
    top_p=1.0,
    reasoning_effort="high",
    stream=True,
)

for chunk in stream:
    if not chunk.choices:  # final usage-only chunk
        continue
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### TypeScript

```typescript
import Together from "together-ai";
const together = new Together();

const stream = await together.chat.completions.create({
  model: "openai/gpt-oss-120b",
  messages: [{ role: "user", content: "Prove the infinitude of primes" }],
  temperature: 1.0,
  top_p: 1.0,
  reasoning_effort: "high",
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

### cURL

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
    "reasoning_effort": "high"
  }'
```

## Enabling and Disabling Reasoning (Hybrid Models)

Hybrid models support `reasoning={"enabled": True/False}` to toggle reasoning on or off.

**Models that honored `reasoning={"enabled": False}` when measured on 2026-11-18** (all reason by
default):
- `Qwen/Qwen3.5-9B`
- `Qwen/Qwen3.6-Plus`
- `moonshotai/Kimi-K3`
- `zai-org/GLM-5.2`
- `deepseek-ai/DeepSeek-V4.1-Flash`
- `MiniMaxAI/MiniMax-M3.1-Flash`

`deepseek-ai/DeepSeek-V4-Pro-0813` ignored it and needs
`chat_template_kwargs={"enable_thinking": False}`. See
[Reasoning Controls by Model](#reasoning-controls-by-model) for the models that cannot be turned
off.

### Python -- Enable Reasoning

```python
from together import Together

client = Together()

stream = client.chat.completions.create(
    model="moonshotai/Kimi-K3",
    messages=[
        {"role": "user", "content": "Which number is bigger, 9.11 or 9.9? Think carefully."},
    ],
    reasoning={"enabled": True},
    temperature=1.0,
    top_p=0.95,
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

### TypeScript -- Enable Reasoning

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
  reasoning_content?: string;
};

const params: ReasoningParams = {
  model: "moonshotai/Kimi-K3",
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
  const trace = delta?.reasoning ?? delta?.reasoning_content;
  if (trace) process.stdout.write(trace);
  if (delta?.content) process.stdout.write(delta.content);
}
```

### Python -- Disable Reasoning (Instant Mode)

```python
response = client.chat.completions.create(
    model="moonshotai/Kimi-K3",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    reasoning={"enabled": False},
    temperature=0.6,
)
print(response.choices[0].message.content)
```

### Alternative: chat_template_kwargs

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3.5-9B",
    messages=[{"role": "user", "content": "Prove that sqrt(2) is irrational."}],
    chat_template_kwargs={"thinking": True},
    stream=True,
)
```

## Controlling Reasoning Depth via Prompting

For hybrid models without `reasoning_effort`, influence thinking depth through the
prompt:

```python
# Ask for concise reasoning
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Pro-0813",
    messages=[
        {
            "role": "user",
            "content": "Please think briefly.\n\nWhat is 15% of 240?",
        }
    ],
    stream=True,
)

# Or suggest a reasoning budget
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Pro-0813",
    messages=[
        {
            "role": "user",
            "content": (
                "Please use around 1000 words to think, "
                "but do not literally count each one.\n\n"
                "Explain why quicksort has O(n log n) average-case complexity."
            ),
        }
    ],
    stream=True,
)
```

## Reasoning Output Format

### Separate reasoning field (most models)

Most reasoning models return the chain of thought in a dedicated field on the response message or
streaming delta, but the field name depends on the model and has changed over time. Observed
2026-11-18: Qwen3.6 Plus and Muse Glimmer 30B use `reasoning`; GPT-OSS 120B, Qwen3.5 9B, Kimi K3,
DeepSeek V4 Pro 0813, DeepSeek V4.1 Flash, GLM-5.2, GLM-5.3, GLM-5.3 Flash, and MiniMax M3.1 Flash
use `reasoning_content`. On 2026-10-07, GPT-OSS and Qwen3.5 9B used `reasoning`. Read both.

Use the same key for input and output: when you send a prior assistant turn back for preserved
thinking or multi-turn tool calling, return the trace unmodified under the key it arrived on
([Reasoning docs](https://docs.together.ai/docs/inference/chat/reasoning)).

**Non-streaming (Python):**

```python
response = client.chat.completions.create(
    model="moonshotai/Kimi-K3",
    messages=[{"role": "user", "content": "Say test 10 times"}],
)
message = response.choices[0].message
print("Reasoning:", getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None))
print("Answer:", response.choices[0].message.content)
```

**Non-streaming (TypeScript):**

```typescript
const response = await together.chat.completions.create({
  model: "moonshotai/Kimi-K3",
  messages: [{ role: "user", content: "Say test 10 times" }],
} as any);

const message = response.choices[0].message as any;
console.log("Reasoning:", message.reasoning ?? message.reasoning_content);
console.log("Answer:", response.choices[0].message.content);
```

**Streaming (Python):**

```python
stream = client.chat.completions.create(
    model="moonshotai/Kimi-K3",
    messages=[{"role": "user", "content": "Which number is bigger, 9.11 or 9.9?"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta
        trace = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
        if trace:
            print(trace, end="", flush=True)
        if hasattr(delta, "content") and delta.content:
            print(delta.content, end="", flush=True)
```

**Streaming (TypeScript):**

```typescript
import type { ChatCompletionChunk } from "together-ai/resources/chat/completions";

const stream = await together.chat.completions.stream({
  model: "moonshotai/Kimi-K3",
  messages: [
    { role: "user", content: "Which number is bigger, 9.11 or 9.9?" },
  ],
} as any);

for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta as ChatCompletionChunk.Choice.Delta & {
    reasoning?: string;
    reasoning_content?: string;
  };
  const trace = delta?.reasoning ?? delta?.reasoning_content;
  if (trace) process.stdout.write(trace);
  if (delta?.content) process.stdout.write(delta.content);
}
```

## Tracking Reasoning and Cached Token Usage

Reasoning output is billed as completion tokens. The extra token counts (reasoning tokens, cached
prompt tokens) always live somewhere on `response.usage`, but their **location varies by model**, so
read both shapes defensively.

- **Reasoning models** (for example `deepseek-ai/DeepSeek-V4-Pro-0813`, `Qwen/Qwen3.6-Plus`,
  `zai-org/GLM-5.2`) nest them OpenAI-style:
  - `usage.completion_tokens_details.reasoning_tokens`
  - `usage.prompt_tokens_details.cached_tokens`
- **Some non-reasoning models** (for example `meta-llama/Llama-3.3-70B-Instruct-Turbo`) return
  `cached_tokens` flat at the top level of `usage`, with no `*_details` objects.

A client configured for only one shape will silently return `0` for all others. Fall back across
both locations:

```python
usage = response.usage
reasoning_tokens = (
    getattr(usage, "completion_tokens_details", None)
    and getattr(usage.completion_tokens_details, "reasoning_tokens", 0)
) or 0

cached_tokens = (
    getattr(usage, "prompt_tokens_details", None)
    and getattr(usage.prompt_tokens_details, "cached_tokens", 0)
) or getattr(usage, "cached_tokens", 0)
```

```typescript
const usage = response.usage as any;
const reasoningTokens =
  usage?.completion_tokens_details?.reasoning_tokens ?? 0;
const cachedTokens =
  usage?.prompt_tokens_details?.cached_tokens ?? usage?.cached_tokens ?? 0;
```

`prompt_tokens`, `completion_tokens`, and `total_tokens` are always present at the top level of
`usage` regardless of model type.

## Structured Outputs with Reasoning

Reasoning models support JSON mode for structured output extraction:

### Python

```python
import json
from together import Together
from pydantic import BaseModel, Field

client = Together()

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Pro-0813",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "math_reasoning",
            "schema": MathReasoning.model_json_schema(),
        },
    },
)

math_reasoning = json.loads(completion.choices[0].message.content)
print(json.dumps(math_reasoning, indent=2))
```

### TypeScript

```typescript
import Together from "together-ai";
import { z } from "zod";

const together = new Together();

const stepSchema = z.object({
  explanation: z.string(),
  output: z.string(),
});

const mathReasoningSchema = z.object({
  steps: z.array(stepSchema),
  final_answer: z.string(),
});

const jsonSchema = z.toJSONSchema(mathReasoningSchema);

const completion = await together.chat.completions.create({
  model: "deepseek-ai/DeepSeek-V4-Pro-0813",
  messages: [
    {
      role: "system",
      content:
        "You are a helpful math tutor. Guide the user through the solution step by step.",
    },
    { role: "user", content: "how can I solve 8x + 7 = -23" },
  ],
  response_format: {
    type: "json_schema",
    json_schema: {
      name: "math_reasoning",
      schema: jsonSchema,
    },
  },
});

if (completion?.choices?.[0]?.message?.content) {
  const result = JSON.parse(completion.choices[0].message.content);
  console.log(JSON.stringify(result, null, 2));
}
```

## Best Practices by Model

### DeepSeek-V4-Pro
- Hybrid reasoning model with very long context (1M)
- Turn reasoning off with `chat_template_kwargs={"enable_thinking": False}`. It ignored
  `reasoning={"enabled": False}` when measured on 2026-11-18.
- Strong performance on math, code, and agentic tool use
- Avoid micromanaging reasoning steps -- let the model determine methodology

### Kimi K3
- Temperature 1.0 for thinking mode, 0.6 for instant mode
- Supports both reasoning and non-reasoning modes
- Excels at multi-turn tool calling with reasoning interleaved

### GLM-5
- Thinking is enabled by default
- Supports Preserved Thinking: set `"clear_thinking": false` in `chat_template_kwargs`
- Preserved Thinking retains reasoning across turns for better agentic workflows

### GPT-OSS
- Use `reasoning_effort` to control depth
- Set `max_tokens` to ~30,000 with `reasoning_effort="high"`
- Build Tier 1+ required
