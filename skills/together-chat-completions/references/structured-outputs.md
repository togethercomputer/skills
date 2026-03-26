# Structured Outputs Reference
## Contents

- [Three Modes](#three-modes)
- [Structured Outputs with Reasoning Models](#structured-outputs-with-reasoning-models)
- [Streaming Structured Output](#streaming-structured-output)
- [Supported Models](#supported-models)
- [Troubleshooting](#troubleshooting)
- [Prompting Best Practices](#prompting-best-practices)


## Three Modes

### 1. json_schema (Recommended)

Constrains output to match your JSON schema exactly. Use Pydantic in Python and Zod in TypeScript
to define schemas.

### Python

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

Output:
```json
{
  "title": "Morning Routine",
  "summary": "Starting the day with a quick breakfast and checking emails",
  "actionItems": [
    "Cook scrambled eggs and toast",
    "Brew a cup of coffee",
    "Check emails for urgent messages"
  ]
}
```

### TypeScript

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

### cURL

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

### OpenAI SDK Compatibility

```python
from pydantic import BaseModel
from openai import OpenAI
import os, json

client = OpenAI(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
)

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "Alice and Bob are going to a science fair on Friday. Answer in JSON"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "calendar_event",
            "schema": CalendarEvent.model_json_schema(),
        },
    },
)

output = json.loads(completion.choices[0].message.content)
print(json.dumps(output, indent=2))
```

### 2. json_object (Simple)

Model outputs valid JSON but structure is guided by prompt only.

### Python

```python
from together import Together

client = Together()

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": "Respond in JSON with keys: name, age, city"},
        {"role": "user", "content": "Tell me about yourself"},
    ],
    response_format={"type": "json_object"},
)
print(response.choices[0].message.content)
```

### TypeScript

```typescript
import Together from "together-ai";
const together = new Together();

const response = await together.chat.completions.create({
  model: "openai/gpt-oss-20b",
  messages: [
    { role: "system", content: "Respond in JSON with keys: name, age, city" },
    { role: "user", content: "Tell me about yourself" },
  ],
  response_format: { type: "json_object" },
});
console.log(response.choices[0].message.content);
```

### cURL

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

### 3. regex (Pattern Matching)

Constrains output to match a regex pattern. All models supported for JSON mode also support regex.

### Python

```python
from together import Together

client = Together()

# Sentiment classification
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
print(response.choices[0].message.content)  # "positive"

# Phone number pattern
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Generate a US phone number for a pizza shop"}],
    response_format={"type": "regex", "pattern": r"\(\d{3}\) \d{3}-\d{4}"},
)
```

### TypeScript

```typescript
import Together from "together-ai";
const together = new Together();

const completion = await together.chat.completions.create({
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
    // @ts-ignore
    pattern: "(positive|neutral|negative)",
  },
});

console.log(completion?.choices[0]?.message?.content); // "positive"
```

### cURL

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

## Structured Outputs with Reasoning Models

Some reasoning models support JSON mode. The model reasons internally then produces structured JSON.

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

## Streaming Structured Output

You can combine `response_format` with `stream=True`. Tokens arrive incrementally (individual chunks
are not valid JSON), so accumulate all chunks and parse the final concatenated string.

```python
import json
from together import Together
from pydantic import BaseModel, Field

client = Together()

class Summary(BaseModel):
    title: str = Field(description="A short title")
    bullets: list[str] = Field(description="Key points")

schema = Summary.model_json_schema()

stream = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": f"Respond in JSON matching: {json.dumps(schema)}"},
        {"role": "user", "content": "Summarize the benefits of exercise"},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "summary", "schema": schema},
    },
    stream=True,
)

chunks: list[str] = []
for chunk in stream:
    token = chunk.choices[0].delta.content or ""
    chunks.append(token)
    print(token, end="", flush=True)
print()

result = json.loads("".join(chunks))
print(f"Title: {result['title']}")
print(f"Bullets: {result['bullets']}")
```

```typescript
import Together from "together-ai";
import { z } from "zod";

const together = new Together();

const summarySchema = z.object({
  title: z.string().describe("A short title"),
  bullets: z.array(z.string()).describe("Key points"),
});
const jsonSchema = z.toJSONSchema(summarySchema);

const stream = await together.chat.completions.create({
  model: "openai/gpt-oss-20b",
  messages: [
    { role: "system", content: `Respond in JSON matching: ${JSON.stringify(jsonSchema)}` },
    { role: "user", content: "Summarize the benefits of exercise" },
  ],
  response_format: {
    type: "json_schema",
    json_schema: { name: "summary", schema: jsonSchema },
  },
  stream: true,
});

const chunks: string[] = [];
for await (const chunk of stream) {
  const token = chunk.choices[0]?.delta?.content || "";
  chunks.push(token);
  process.stdout.write(token);
}

const result = JSON.parse(chunks.join(""));
console.log(`Title: ${result.title}`);
```

## Supported Models

### Top Models (json_schema, json_object, regex)
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`
- `moonshotai/Kimi-K2.5`
- `zai-org/GLM-5`
- `zai-org/GLM-4.5-Air-FP8`
- `MiniMaxAI/MiniMax-M2.5`
- `Qwen/Qwen3.5-397B-A17B`
- `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8`
- `deepseek-ai/DeepSeek-R1`
- `deepseek-ai/DeepSeek-V3`
- `deepseek-ai/DeepSeek-V3.1`
- `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`

### Additional Supported Models
- `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- `Qwen/Qwen2.5-7B-Instruct-Turbo`
- `google/gemma-3n-E4B-it`
- `mistralai/Mistral-Small-24B-Instruct-2501`
- `mistralai/Mistral-7B-Instruct-v0.2`

## Troubleshooting

- **Token limits**: Check the max token limit of your model. Truncated output is a common issue.
- **Malformed JSON**: Validate your example JSON before using it in prompts. The model follows your
  example exactly, including syntax errors.
- **Common symptoms**: Unterminated strings, repeated newlines, incomplete structures, or truncated
  output with `stop` finish reason.

## Prompting Best Practices

1. Always tell the model to respond **only in JSON** in the system prompt
2. Include a plain-text copy of the schema in the prompt
3. Use `json_schema` mode when you need guaranteed structure
4. Use `json_object` for simpler cases where prompt guidance is sufficient
5. Use `regex` mode for simple constrained outputs (classification, IDs, phone numbers)
6. Works with vision models (e.g., `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`)
7. Works with reasoning models (e.g., `deepseek-ai/DeepSeek-R1`)
