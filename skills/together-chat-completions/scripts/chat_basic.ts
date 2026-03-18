#!/usr/bin/env -S npx tsx
/**
 * Together AI Chat Completions — Basic Chat and Streaming
 *
 * Demonstrates single-query chat, streaming, and multi-turn conversation.
 *
 * Usage:
 *   npx tsx chat_basic.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function basicChat(): Promise<void> {
  console.log("=== Basic Chat ===");
  const response = await client.chat.completions.create({
    model: "openai/gpt-oss-20b",
    messages: [{ role: "user", content: "What are some fun things to do in NYC?" }],
  });
  console.log(response.choices[0].message.content);
  console.log();
}

async function streamingChat(): Promise<void> {
  console.log("=== Streaming ===");
  const stream = await client.chat.completions.create({
    model: "openai/gpt-oss-20b",
    messages: [{ role: "user", content: "Write a haiku about coding" }],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
  console.log("\n");
}

async function multiTurnChat(): Promise<void> {
  console.log("=== Multi-Turn ===");
  const messages: { role: string; content: string }[] = [
    { role: "system", content: "You are a helpful travel guide. Keep answers brief." },
    { role: "user", content: "What should I do in Paris?" },
  ];

  const response = await client.chat.completions.create({
    model: "openai/gpt-oss-20b",
    messages: messages as any,
  });
  const assistantReply = response.choices[0].message.content ?? "";
  console.log("User: What should I do in Paris?");
  console.log(`Assistant: ${assistantReply}\n`);

  messages.push({ role: "assistant", content: assistantReply });
  messages.push({ role: "user", content: "How about food recommendations?" });

  const response2 = await client.chat.completions.create({
    model: "openai/gpt-oss-20b",
    messages: messages as any,
  });
  console.log("User: How about food recommendations?");
  console.log(`Assistant: ${response2.choices[0].message.content}`);
}

async function main(): Promise<void> {
  await basicChat();
  await streamingChat();
  await multiTurnChat();
}

main();
