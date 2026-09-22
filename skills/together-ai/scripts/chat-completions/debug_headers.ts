#!/usr/bin/env -S npx tsx
/**
 * Together AI Chat Completions — Debug Headers and Raw Responses
 *
 * Inspect parsed chat output together with raw response headers for latency,
 * routing, and rate-limit debugging.
 *
 * Usage:
 *   npx tsx debug_headers.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main(): Promise<void> {
  const response = await client.chat.completions.create(
    {
      model: "openai/gpt-oss-20b",
      messages: [{ role: "user", content: "Say hello in one sentence." }],
    },
    { headers: { "x-together-debug": "1" } }
  ).asResponse();

  const parsed = await response.json();
  console.log("=== Parsed Response ===");
  console.log(parsed.choices[0].message.content);
  console.log();

  console.log("=== Selected Headers ===");
  const interestingHeaders = [
    "x-request-id",
    "x-together-traceid",
    "x-cluster",
    "x-engine-pod",
    "x-api-received",
    "x-api-call-start",
    "x-api-call-end",
    "x-inference-version",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-tokenlimit-limit",
    "x-tokenlimit-remaining",
  ];

  for (const key of interestingHeaders) {
    const value = response.headers.get(key);
    if (value) {
      console.log(`${key}: ${value}`);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
