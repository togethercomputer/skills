# Function Calling Patterns Reference
## Contents

- [6 Calling Patterns](#6-calling-patterns)
- [Combining Tool Calls with Structured Output](#combining-tool-calls-with-structured-output)
- [Processing Tool Calls](#processing-tool-calls)
- [tool_choice Parameter](#toolchoice-parameter)
- [Supported Models](#supported-models)


## 6 Calling Patterns

### 1. Simple -- Single function, single call

Model picks one function and calls it once.

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

tool_call = response.choices[0].message.tool_calls[0]
print(f"Function: {tool_call.function.name}")
print(f"Arguments: {tool_call.function.arguments}")
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

### 2. Multiple Functions -- Model picks which to call

Multiple tools available, model chooses the right one based on user intent.

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City and state"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_stock_price",
            "description": "Get the current stock price for a given stock symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "The stock symbol, e.g. AAPL"},
                    "exchange": {
                        "type": "string",
                        "description": "The stock exchange (optional)",
                        "enum": ["NYSE", "NASDAQ", "LSE", "TSX"],
                    },
                },
                "required": ["symbol"],
            },
        },
    },
]

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=[{"role": "user", "content": "What's the current price of Apple's stock?"}],
    tools=tools,
)
# Model correctly picks get_current_stock_price(symbol="AAPL")
```

```typescript
const tools = [
  {
    type: "function" as const,
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
  {
    type: "function" as const,
    function: {
      name: "getCurrentStockPrice",
      description: "Get the current stock price for a given stock symbol",
      parameters: {
        type: "object",
        properties: {
          symbol: {
            type: "string",
            description: "The stock symbol, e.g. AAPL, GOOGL, TSLA",
          },
          exchange: {
            type: "string",
            description: "The stock exchange (optional)",
            enum: ["NYSE", "NASDAQ", "LSE", "TSX"],
          },
        },
        required: ["symbol"],
      },
    },
  },
];

const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages: [
    { role: "user", content: "What's the current price of Apple's stock?" },
  ],
  tools,
});

// Model correctly picks getCurrentStockPrice(symbol="AAPL")
console.log(JSON.stringify(response.choices[0].message?.tool_calls, null, 2));
```

### 3. Parallel -- Same function, multiple calls

Model calls the same function multiple times in one turn.

```python
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that can access external functions."},
        {
            "role": "user",
            "content": "What is the current temperature of New York, San Francisco and Chicago?",
        },
    ],
    tools=[{
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
    }],
)

# Model returns 3 tool_calls:
#   get_current_weather(location="New York, NY", unit="fahrenheit")
#   get_current_weather(location="San Francisco, CA", unit="fahrenheit")
#   get_current_weather(location="Chicago, IL", unit="fahrenheit")
for tc in response.choices[0].message.tool_calls:
    print(f"  {tc.function.name}({tc.function.arguments})")
```

```typescript
const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages: [
    {
      role: "system",
      content: "You are a helpful assistant that can access external functions.",
    },
    {
      role: "user",
      content:
        "What is the current temperature of New York, San Francisco and Chicago?",
    },
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

// Model returns 3 tool_calls for NYC, SF, and Chicago
console.log(JSON.stringify(response.choices[0].message?.tool_calls, null, 2));
```

### 4. Parallel Multiple -- Different functions in one turn

Model calls multiple different functions simultaneously. Combines parallel and multiple function
calling: one user prompt triggers multiple different function calls.

```python
# User: "What's Apple and Google's stock price, and what's the weather in NYC, SF, and Chicago?"
# Model returns 5 tool_calls:
#   get_current_stock_price(symbol="AAPL")
#   get_current_stock_price(symbol="GOOGL")
#   get_current_weather(location="New York, NY")
#   get_current_weather(location="San Francisco, CA")
#   get_current_weather(location="Chicago, IL")

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=[
        {
            "role": "user",
            "content": (
                "What's Apple and Google's stock price, and what's the weather "
                "in New York, San Francisco, and Chicago?"
            ),
        },
    ],
    tools=tools,  # both weather and stock tools defined
)

for tc in response.choices[0].message.tool_calls:
    print(f"  {tc.function.name}({tc.function.arguments})")
```

```typescript
const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages: [
    {
      role: "user",
      content:
        "What's Apple and Google's stock price, and what's the weather in NYC, SF, and Chicago?",
    },
  ],
  tools, // both weather and stock tools defined
});

// Returns 5 tool_calls: 2 stock + 3 weather
for (const tc of response.choices[0].message?.tool_calls ?? []) {
  console.log(`  ${tc.function.name}(${tc.function.arguments})`);
}
```

### 5. Multi-step -- Chained function calls

Sequential function calls within one conversation turn. Functions are called, results are processed,
then used to inform the final response.

```python
import json
from together import Together

client = Together()

messages = [
    {"role": "system", "content": "You are a helpful assistant that can access external functions."},
    {
        "role": "user",
        "content": "What is the current temperature of New York, San Francisco and Chicago?",
    },
]

# Step 1: Model generates tool calls
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)

# Step 2: Execute functions and add results
messages.append(response.choices[0].message)
for tc in response.choices[0].message.tool_calls:
    args = json.loads(tc.function.arguments)
    result = get_current_weather(**args)  # your function
    messages.append({
        "role": "tool",
        "tool_call_id": tc.id,
        "content": json.dumps(result),
    })

# Step 3: Model produces final answer using all results
final = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)
print(final.choices[0].message.content)
# "The current temperature in New York is 11F, in San Francisco it is 55F, ..."
```

```typescript
import Together from "together-ai";
const together = new Together();

const messages: any[] = [
  {
    role: "system",
    content: "You are a helpful assistant that can access external functions.",
  },
  {
    role: "user",
    content:
      "What is the current temperature of New York, San Francisco and Chicago?",
  },
];

// Step 1: Model generates tool calls
const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages,
  tools,
});

// Step 2: Execute functions and add results
messages.push(response.choices[0].message);
for (const tc of response.choices[0].message?.tool_calls ?? []) {
  const args = JSON.parse(tc.function.arguments);
  const result = getCurrentWeather(args); // your function
  messages.push({
    role: "tool",
    tool_call_id: tc.id,
    content: JSON.stringify(result),
  });
}

// Step 3: Model produces final answer
const final = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages,
  tools,
});
console.log(final.choices[0].message.content);
```

### 6. Multi-turn -- Function calls across conversation turns

Context is maintained across multiple conversation turns and functions can be called at any point.
Previous function results inform future decisions, enabling truly agentic behavior.

```python
messages = [
    {"role": "system", "content": "You are a travel planning assistant."},
]

# Turn 1: User asks about weather in 3 cities
messages.append({
    "role": "user",
    "content": "What's the weather in NYC, SF, and Chicago?",
})

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)

# Execute weather calls, add results to messages...
messages.append(response.choices[0].message)
for tc in response.choices[0].message.tool_calls:
    args = json.loads(tc.function.arguments)
    result = get_current_weather(**args)
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

final = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)
messages.append(final.choices[0].message)

# Turn 2: User follows up -- model uses previous context
messages.append({
    "role": "user",
    "content": "Which city has the best weather for outdoor dining? Find me a restaurant there.",
})

response2 = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)
# Model remembers SF had 65F, picks it, and calls get_restaurant(location="San Francisco")
```

```typescript
const messages: any[] = [
  { role: "system", content: "You are a travel planning assistant." },
];

// Turn 1: User asks about weather
messages.push({
  role: "user",
  content: "What's the weather in NYC, SF, and Chicago?",
});

const response = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages,
  tools,
});

// Execute weather calls, add results...
messages.push(response.choices[0].message);
for (const tc of response.choices[0].message?.tool_calls ?? []) {
  const args = JSON.parse(tc.function.arguments);
  const result = getCurrentWeather(args);
  messages.push({
    role: "tool",
    tool_call_id: tc.id,
    content: JSON.stringify(result),
  });
}

const final = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages,
  tools,
});
messages.push(final.choices[0].message);

// Turn 2: Model uses previous weather data to recommend
messages.push({
  role: "user",
  content:
    "Which city has the best weather for outdoor dining? Find me a restaurant there.",
});

const response2 = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages,
  tools,
});
// Model picks the best-weather city and calls get_restaurant
```

## Combining Tool Calls with Structured Output

You cannot pass `tools` and `response_format` in the same request. Use a two-phase approach:

1. **Phase 1 (tool detection)**: Send with `tools`, no `response_format`. Model decides whether to call
   functions.
2. **Phase 2 (structured response)**: After executing tools and appending results, send a follow-up
   request with `response_format` (and optionally `stream=True`) but without `tools`.

```python
import json
from together import Together
from pydantic import BaseModel, Field

client = Together()

class ChatResponse(BaseModel):
    response: str = Field(description="The assistant's answer")
    confidence: float = Field(description="Confidence from 0.0 to 1.0")
    sources: list[str] = Field(description="Data sources used")

messages = [
    {"role": "system", "content": "You are a helpful assistant with weather tools."},
    {"role": "user", "content": "What's the weather in NYC?"},
]

# Phase 1: tool detection (no response_format)
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)

# Execute tool calls and append results
tool_calls = response.choices[0].message.tool_calls
if tool_calls:
    messages.append(response.choices[0].message)
    for tc in tool_calls:
        result = execute_function(tc.function.name, json.loads(tc.function.arguments))
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result),
        })

# Phase 2: structured response (no tools)
schema = ChatResponse.model_json_schema()
final = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=messages,
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "chat_response", "schema": schema},
    },
    stream=True,  # can stream structured JSON
)

chunks = []
for chunk in final:
    token = chunk.choices[0].delta.content or ""
    chunks.append(token)
    print(token, end="", flush=True)
output = json.loads("".join(chunks))
```

```typescript
import Together from "together-ai";
import { z } from "zod";

const together = new Together();

const chatResponseSchema = z.object({
  response: z.string().describe("The assistant's answer"),
  confidence: z.number().describe("Confidence from 0.0 to 1.0"),
  sources: z.array(z.string()).describe("Data sources used"),
});
const jsonSchema = z.toJSONSchema(chatResponseSchema);

// Phase 1: tool detection
const response = await together.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  messages,
  tools,
});

// Execute tool calls, append results to messages...

// Phase 2: structured response (no tools), with streaming
const stream = await together.chat.completions.create({
  model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  messages,
  response_format: {
    type: "json_schema",
    json_schema: { name: "chat_response", schema: jsonSchema },
  },
  stream: true,
});

const chunks: string[] = [];
for await (const chunk of stream) {
  const token = chunk.choices[0]?.delta?.content || "";
  chunks.push(token);
  process.stdout.write(token);
}
const output = JSON.parse(chunks.join(""));
```

## Processing Tool Calls

### Python

```python
import json

# 1. Get tool calls from response
tool_calls = response.choices[0].message.tool_calls

# 2. Add assistant message to history
messages.append(response.choices[0].message)

# 3. Execute each function and add results
for tc in tool_calls:
    args = json.loads(tc.function.arguments)
    result = execute_function(tc.function.name, args)
    messages.append({
        "role": "tool",
        "tool_call_id": tc.id,
        "content": json.dumps(result),
    })

# 4. Get final response
final = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    messages=messages,
    tools=tools,
)
```

### TypeScript

```typescript
// 1. Get tool calls from response
const toolCalls = response.choices[0].message?.tool_calls ?? [];

// 2. Add assistant message to history
messages.push(response.choices[0].message);

// 3. Execute each function and add results
for (const tc of toolCalls) {
  const args = JSON.parse(tc.function.arguments);
  const result = executeFunction(tc.function.name, args);
  messages.push({
    role: "tool",
    tool_call_id: tc.id,
    content: JSON.stringify(result),
  });
}

// 4. Get final response
const final = await together.chat.completions.create({
  model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
  messages,
  tools,
});
```

## tool_choice Parameter

| Value | Behavior |
|-------|----------|
| `"auto"` (default) | Model decides whether to call functions |
| `"required"` | Model must call at least one function |
| `"none"` | Never call functions |
| `{"type": "function", "function": {"name": "fn"}}` | Force specific function |

## Supported Models

openai/gpt-oss-120b, openai/gpt-oss-20b, moonshotai/Kimi-K2.6, moonshotai/Kimi-K2.5,
zai-org/GLM-5.1, zai-org/GLM-5, MiniMaxAI/MiniMax-M2.7, Qwen/Qwen3.5-397B-A17B,
Qwen/Qwen3.5-9B, Qwen/Qwen3.6-Plus, Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8,
Qwen/Qwen3-235B-A22B-Instruct-2507-tput, deepseek-ai/DeepSeek-V4-Pro,
meta-llama/Llama-3.3-70B-Instruct-Turbo, Qwen/Qwen2.5-7B-Instruct-Turbo, google/gemma-4-31B-it
