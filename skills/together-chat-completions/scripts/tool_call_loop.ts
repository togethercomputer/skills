#!/usr/bin/env -S npx tsx
/**
 * Together AI Function Calling — Complete Tool Call Loop
 *
 * Defines tools, sends a request, executes function calls, and passes
 * results back to the model for a final response. Handles parallel calls.
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

// --- 3. Send request with tools ---
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

  const response = await client.chat.completions.create({
    model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages,
    tools,
  });

  // --- 4. Process tool calls (handles parallel calls) ---
  const assistantMessage = response.choices[0]?.message;
  if (!assistantMessage) {
    throw new Error("Model returned no assistant message.");
  }
  const toolCalls = assistantMessage.tool_calls ?? [];

  if (toolCalls.length > 0) {
    // Add assistant message with tool calls to history
    messages.push(assistantMessage);

    for (const tc of toolCalls) {
      const fnName = tc.function.name;
      const fnArgs = JSON.parse(tc.function.arguments);
      const fn = functions[fnName];
      if (!fn) {
        throw new Error(`No implementation found for tool: ${fnName}`);
      }

      console.log(`Calling ${fnName}(${JSON.stringify(fnArgs)})`);
      const result = fn(fnArgs);

      // Add each tool result to history
      messages.push({
        role: "tool",
        tool_call_id: tc.id,
        content: JSON.stringify(result),
      });
    }

    // --- 5. Get final response with tool results ---
    const final = await client.chat.completions.create({
      model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
      messages,
      tools,
    });
    console.log(`\nAssistant: ${final.choices[0].message.content}`);
  } else {
    // Model responded directly without calling tools
    console.log(`Assistant: ${response.choices[0].message.content}`);
  }
}

main();
