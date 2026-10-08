#!/usr/bin/env -S npx tsx
/**
 * Together AI Function Calling — Complete Tool Call Loop
 *
 * Runs a multi-round tool loop: the model calls tools, the tools run, results
 * go back, and the loop repeats until the model answers without a tool call.
 * It also enforces grounding: if the task requires an action and no tool result
 * exists for it, the loop tells the model what is missing and continues, so a
 * model that skips a step and claims it happened cannot end the run.
 *
 * Usage:
 *   npx tsx tool_call_loop.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import type {
  ChatCompletionMessageParam,
  ChatCompletionTool,
} from "together-ai/resources/chat/completions";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

const MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo";

// --- 1. Define tools ---
const tools: ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "getWeather",
      description: "Get the current weather in a city",
      parameters: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "City name, e.g. 'San Francisco, CA'",
          },
          unit: { type: "string", enum: ["celsius", "fahrenheit"] },
        },
        required: ["location"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "getStockPrice",
      description: "Get the current stock price for a ticker symbol",
      parameters: {
        type: "object",
        properties: {
          symbol: {
            type: "string",
            description: "Stock ticker, e.g. 'AAPL'",
          },
        },
        required: ["symbol"],
      },
    },
  },
];

// --- 2. Implement your functions ---
function getWeather(args: {
  location: string;
  unit?: string;
}): Record<string, unknown> {
  // Replace with real API call
  return {
    location: args.location,
    temperature: 72,
    unit: args.unit ?? "fahrenheit",
    condition: "sunny",
  };
}

function getStockPrice(args: { symbol: string }): Record<string, unknown> {
  // Replace with real API call
  return { symbol: args.symbol, price: 185.5, currency: "USD" };
}

const functions: Record<
  string,
  (args: any) => Record<string, unknown>
> = {
  getWeather,
  getStockPrice,
};

// --- 3. Execute one tool call; errors go back to the model, not up the stack ---
function executeToolCall(tc: {
  function: { name: string; arguments: string };
}): { result: string; ok: boolean } {
  const fn = functions[tc.function.name];
  if (!fn) {
    return { result: JSON.stringify({ error: `unknown tool ${tc.function.name}` }), ok: false };
  }
  let args: unknown;
  try {
    args = JSON.parse(tc.function.arguments || "{}");
  } catch (err) {
    return { result: JSON.stringify({ error: `arguments were not valid JSON: ${err}` }), ok: false };
  }
  try {
    return { result: JSON.stringify(fn(args)), ok: true };
  } catch (err) {
    return { result: JSON.stringify({ error: String(err) }), ok: false };
  }
}

// --- 4. Loop until no more tool calls AND every required tool has succeeded ---
async function runToolLoop(
  messages: ChatCompletionMessageParam[],
  requiredTools: Set<string> = new Set(),
  maxRounds = 8,
): Promise<{ answer: string; succeeded: Set<string>; missing: Set<string> }> {
  const succeeded = new Set<string>();
  const missingNow = () => new Set([...requiredTools].filter((t) => !succeeded.has(t)));

  for (let round = 0; round < maxRounds; round++) {
    const response = await client.chat.completions.create({ model: MODEL, messages, tools });
    const message = response.choices[0]?.message;
    if (!message) throw new Error("Model returned no assistant message.");

    const toolCalls = message.tool_calls ?? [];
    if (toolCalls.length > 0) {
      messages.push(message);
      for (const tc of toolCalls) {
        const { result, ok } = executeToolCall(tc);
        console.log(`  tool ${tc.function.name}(${tc.function.arguments}) -> ${result}`);
        if (ok) succeeded.add(tc.function.name);
        messages.push({ role: "tool", tool_call_id: tc.id, content: result });
      }
      continue;
    }

    const missing = missingNow();
    if (missing.size === 0) {
      return { answer: message.content ?? "", succeeded, missing };
    }

    // Grounding check: detecting the gap is not enough; push the loop to finish the work.
    messages.push({ role: "assistant", content: message.content ?? "" });
    messages.push({
      role: "user",
      content:
        `You have not called ${[...missing].sort().join(", ")} yet, so that action has not ` +
        "happened. Call it now, or say plainly that you could not. Only report IDs and values " +
        "that a tool result returned.",
    });
  }
  return { answer: "", succeeded, missing: missingNow() };
}

async function main(): Promise<void> {
  const messages: ChatCompletionMessageParam[] = [
    {
      role: "system",
      content: "You are a helpful assistant with access to weather and stock tools.",
    },
    {
      role: "user",
      content: "What's the weather in NYC and the current Apple stock price?",
    },
  ];

  const { answer, succeeded, missing } = await runToolLoop(
    messages,
    new Set(["getWeather", "getStockPrice"]),
  );
  if (missing.size > 0) {
    // A non-empty "missing" set means the task is NOT done: report it as a failure.
    console.log(`\nIncomplete: required tools never succeeded: ${[...missing].sort().join(", ")}`);
  } else {
    console.log(`\nTools used: ${[...succeeded].sort().join(", ")}`);
    console.log(`Assistant: ${answer}`);
  }
}

main();
