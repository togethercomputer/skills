# Structured Outputs Reference

## Three Modes

### 1. json_schema (Recommended)

Constrains output to match your JSON schema exactly.

```python
from pydantic import BaseModel, Field

class VoiceNote(BaseModel):
    title: str = Field(description="A title")
    summary: str = Field(description="Short summary")
    actionItems: list[str] = Field(description="Action items")

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": f"Respond in JSON: {json.dumps(VoiceNote.model_json_schema())}"},
        {"role": "user", "content": transcript},
    ],
    response_format={
        "type": "json_schema",
        "schema": VoiceNote.model_json_schema(),
    },
)
result = VoiceNote.model_validate_json(response.choices[0].message.content)
```

**TypeScript:**
```typescript
import Together from "together-ai";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

const together = new Together();

const voiceNoteSchema = z.object({
  title: z.string().describe("A title for the voice note"),
  summary: z.string().describe("A short one sentence summary of the voice note."),
  actionItems: z.array(z.string()).describe("A list of action items from the voice note"),
});
const jsonSchema = zodToJsonSchema(voiceNoteSchema, { target: "openAi" });

const extract = await together.chat.completions.create({
  messages: [
    {
      role: "system",
      content: `The following is a voice message transcript. Only answer in JSON and follow this schema ${JSON.stringify(jsonSchema)}.`,
    },
    { role: "user", content: transcript },
  ],
  model: "openai/gpt-oss-20b",
  response_format: { type: "json_schema", schema: jsonSchema },
});

const output = JSON.parse(extract?.choices?.[0]?.message?.content);
console.log(output);
```

**cURL:**
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
          "actionItems": { "items": { "type": "string" }, "type": "array", "description": "Action items" }
        },
        "required": ["title", "summary", "actionItems"],
        "type": "object"
      }
    }
  }'
```

### 2. json_object (Simple)

Model outputs valid JSON but structure is guided by prompt only.

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

Constrains output to match a regex pattern.

```python
# Sentiment classification
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[
        {"role": "system", "content": "Classify sentiment."},
        {"role": "user", "content": "I loved the movie!"},
    ],
    response_format={
        "type": "regex",
        "pattern": "(positive|neutral|negative)",
    },
)

# Phone number
response_format={"type": "regex", "pattern": r"\(\d{3}\) \d{3}-\d{4}"}

# Email
response_format={"type": "regex", "pattern": r"\w+@\w+\.com\n"}
```

```typescript
import Together from "together-ai";
const together = new Together();

const completion = await together.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  messages: [
    {
      role: "system",
      content:
        "You are an AI-powered expert specializing in classifying sentiment. Classify the text as positive, neutral, or negative.",
    },
    { role: "user", content: "Wow. I loved the movie!" },
  ],
  response_format: {
    type: "regex",
    // @ts-ignore
    pattern: "(positive|neutral|negative)",
  },
});

console.log(completion?.choices[0]?.message?.content);
```

```shell
curl -X POST "https://api.together.xyz/v1/chat/completions" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "messages": [
      {
        "role": "user",
        "content": "Return only an email address for Alan Turing at Enigma. End with .com and newline."
      }
    ],
    "stop": ["\n"],
    "response_format": {
      "type": "regex",
      "pattern": "\\w+@\\w+\\.com\\n"
    },
    "temperature": 0.0,
    "max_tokens": 50
  }'
```

## Supported Models

### Top Models (json_schema, json_object, regex)
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`
- `moonshotai/Kimi-K2-Instruct`
- `zai-org/GLM-5`
- `zai-org/GLM-4.5-Air-FP8`
- `MiniMaxAI/MiniMax-M2.5`
- `Qwen/Qwen3.5-397B-A17B`
- `Qwen/Qwen3-235B-A22B-Thinking-2507`
- `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8`
- `deepseek-ai/DeepSeek-R1`
- `deepseek-ai/DeepSeek-V3`
- `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`
- `Qwen/Qwen2.5-VL-72B-Instruct`

### Additional Supported Models
- `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- `deepcogito/cogito-v2-preview-llama-70B`
- `deepcogito/cogito-v2-preview-llama-405B`
- `deepseek-ai/DeepSeek-R1-Distill-Llama-70B`
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B`
- `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
- `Qwen/Qwen2.5-7B-Instruct-Turbo`
- `Qwen/Qwen2.5-Coder-32B-Instruct`
- `Qwen/QwQ-32B`
- `meta-llama/Llama-3.2-3B-Instruct-Turbo`
- `google/gemma-3n-E4B-it`
- `mistralai/Mistral-7B-Instruct-v0.1`
- `mistralai/Mistral-7B-Instruct-v0.2`
- `mistralai/Mistral-7B-Instruct-v0.3`

## Prompting Best Practices

1. Always tell the model to respond **only in JSON**
2. Include a plain-text copy of the schema in the prompt
3. Use `json_schema` mode when you need guaranteed structure
4. Use `regex` mode for simple constrained outputs (classification, IDs)
5. Works with vision models (e.g., `Qwen/Qwen2.5-VL-72B-Instruct`)
6. Works with reasoning models (e.g., `deepseek-ai/DeepSeek-R1`)
