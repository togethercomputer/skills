# Reasoning Models Reference

## Full Model Table

| Model | API String | Type | Context | Tool Calling |
|-------|-----------|------|---------|--------------|
| DeepSeek R1 | `deepseek-ai/DeepSeek-R1` | Reasoning only | 164K | No |
| DeepSeek V3.1 | `deepseek-ai/DeepSeek-V3.1` | Hybrid (off by default) | 164K | Non-reasoning only |
| GLM-5 | `zai-org/GLM-5` | Hybrid (on by default) | 200K | Yes |
| GPT-OSS 120B | `openai/gpt-oss-120b` | Adjustable effort | 128K | No |
| GPT-OSS 20B | `openai/gpt-oss-20b` | Adjustable effort | 128K | No |
| Kimi K2.5 | `moonshotai/Kimi-K2.5` | Hybrid (on by default) | 256K | Yes |
| MiniMax M2.5 | `MiniMaxAI/MiniMax-M2.5` | Reasoning only | 229K | No |
| Qwen3.5 397B | `Qwen/Qwen3.5-397B-A17B` | Hybrid (on by default) | 128K | No |
| Qwen3.5 9B | `Qwen/Qwen3.5-9B` | Hybrid (on by default) | 128K | No |

**Type definitions:**
- **Reasoning only**: Always produces reasoning tokens. Cannot be toggled off.
- **Hybrid**: Supports both reasoning and non-reasoning modes via `reasoning={"enabled": True/False}`.
- **Adjustable effort**: Supports `reasoning_effort` parameter (`"low"`, `"medium"`, `"high"`).

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

**Models supporting this parameter:**
- `deepseek-ai/DeepSeek-V3.1` (off by default)
- `Qwen/Qwen3.5-397B-A17B` (on by default)
- `Qwen/Qwen3.5-9B` (on by default)
- `moonshotai/Kimi-K2.5` (on by default)
- `zai-org/GLM-5` (on by default)

Note: For DeepSeek V3.1, function calling only works in non-reasoning mode
(`reasoning={"enabled": False}`).

### Python -- Enable Reasoning

```python
from together import Together

client = Together()

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

### Python -- Disable Reasoning (Instant Mode)

```python
response = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    reasoning={"enabled": False},
    temperature=0.6,
)
print(response.choices[0].message.content)
```

### Alternative: chat_template_kwargs

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3.5-397B-A17B",
    messages=[{"role": "user", "content": "Prove that sqrt(2) is irrational."}],
    chat_template_kwargs={"thinking": True},
    stream=True,
)
```

## Controlling Reasoning Depth via Prompting

For models without `reasoning_effort` (e.g., DeepSeek R1), influence thinking depth through the
prompt:

```python
# Ask for concise reasoning
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
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
    model="deepseek-ai/DeepSeek-R1",
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

Models like Kimi K2.5, GLM-5, DeepSeek V3.1, GPT-OSS, and Qwen3.5 return reasoning in a dedicated
`reasoning` field on the response message or streaming delta.

**Non-streaming (Python):**

```python
response = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[{"role": "user", "content": "Say test 10 times"}],
)
print("Reasoning:", response.choices[0].message.reasoning)
print("Answer:", response.choices[0].message.content)
```

**Non-streaming (TypeScript):**

```typescript
const response = await together.chat.completions.create({
  model: "moonshotai/Kimi-K2.5",
  messages: [{ role: "user", content: "Say test 10 times" }],
} as any);

console.log("Reasoning:", (response.choices[0].message as any).reasoning);
console.log("Answer:", response.choices[0].message.content);
```

**Streaming (Python):**

```python
stream = client.chat.completions.create(
    model="moonshotai/Kimi-K2.5",
    messages=[{"role": "user", "content": "Which number is bigger, 9.11 or 9.9?"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta
        if hasattr(delta, "reasoning") and delta.reasoning:
            print(delta.reasoning, end="", flush=True)
        if hasattr(delta, "content") and delta.content:
            print(delta.content, end="", flush=True)
```

**Streaming (TypeScript):**

```typescript
import type { ChatCompletionChunk } from "together-ai/resources/chat/completions";

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
  if (delta?.reasoning) process.stdout.write(delta.reasoning);
  if (delta?.content) process.stdout.write(delta.content);
}
```

### DeepSeek R1 -- `<think>` tags in content

DeepSeek R1 outputs reasoning inside `<think>` tags within the `content` field.

**Streaming (Python):**

```python
stream = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "Which number is bigger 9.9 or 9.11?"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

**Streaming (TypeScript):**

```typescript
const stream = await together.chat.completions.create({
  model: "deepseek-ai/DeepSeek-R1",
  messages: [{ role: "user", content: "Which number is bigger 9.9 or 9.11?" }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

Output:
```
<think>
Let me compare 9.9 and 9.11...
9.9 = 9.90, and 9.90 > 9.11
</think>

**Answer:** 9.9 is bigger.
```

**Parsing `<think>` tags (Python):**

```python
import re

content = response.choices[0].message.content
think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
thinking = think_match.group(1).strip() if think_match else ""
answer = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
```

**Parsing `<think>` tags (TypeScript):**

```typescript
const content = response.choices[0].message.content ?? "";
const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/);
const thinking = thinkMatch ? thinkMatch[1].trim() : "";
const answer = content.replace(/<think>[\s\S]*?<\/think>/, "").trim();
```

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
    model="deepseek-ai/DeepSeek-R1",
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
  model: "deepseek-ai/DeepSeek-R1",
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

### DeepSeek R1
- **Temperature:** 0.5-0.7 (recommended 0.6)
- **Top-p:** 0.95 recommended
- **System prompts:** Omit -- put all instructions in user message
- **Prompting:** High-level objectives, let model determine methodology
- **Few-shot:** Avoid -- consistently degrades performance
- **Chain-of-thought:** Do not prompt "think step by step" (model already reasons)
- **Math tasks:** Include "put your final answer within \boxed{}" in prompt
- Avoid micromanaging reasoning steps

### Kimi K2.5
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
