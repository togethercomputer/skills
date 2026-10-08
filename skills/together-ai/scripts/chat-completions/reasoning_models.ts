#!/usr/bin/env -S npx tsx
/**
 * Together AI Chat Completions — Reasoning Models
 *
 * Demonstrates reasoning with separate reasoning fields, parsing DeepSeek-R1 <think> tags,
 * reasoning effort control, and enabling/disabling reasoning on hybrid models.
 *
 * Usage:
 *   npx tsx reasoning_models.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import type {
  ChatCompletionChunk,
  ChatCompletionMessageParam,
  CompletionCreateParamsStreaming,
} from "together-ai/resources/chat/completions";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

// Kimi K3 sends the trace as `reasoning_content`; most other models use `reasoning`.
type ReasoningDelta = ChatCompletionChunk.Choice.Delta & {
  reasoning?: string;
  reasoning_content?: string;
};

type ReasoningParams = CompletionCreateParamsStreaming & {
  reasoning?: { enabled: boolean };
};

// --- 1. Reasoning field (streaming) ---
async function reasoningFieldStreaming(): Promise<void> {
  console.log("=== Reasoning Field (Kimi K3 streaming) ===");

  const stream = await client.chat.completions.stream({
    model: "moonshotai/Kimi-K3",
    messages: [
      { role: "user", content: "Which number is bigger, 9.11 or 9.9?" },
    ],
  });

  let reasoningText = "";
  let contentText = "";

  for await (const chunk of stream) {
    const delta = chunk.choices[0]?.delta as ReasoningDelta;
    const trace = delta?.reasoning ?? delta?.reasoning_content;
    if (trace) reasoningText += trace;
    if (delta?.content) contentText += delta.content;
  }

  console.log(`Reasoning: ${reasoningText.slice(0, 200)}...`);
  console.log(`Answer: ${contentText}`);
  console.log();
}

// --- 2. <think> tags (DeepSeek-R1 on a dedicated endpoint) ---
// DeepSeek-R1 puts its reasoning inside <think> tags in `content`. It is no longer
// served serverless on Together, and current serverless reasoning models use a
// separate `reasoning` or `reasoning_content` field, so this parser runs offline.
function splitThinkTags(text: string): { thinking: string; answer: string } {
  const match = text.match(/<think>([\s\S]*?)<\/think>/);
  return {
    thinking: match ? match[1].trim() : "",
    answer: text.replace(/<think>[\s\S]*?<\/think>/, "").trim(),
  };
}

function thinkTagsExample(): void {
  console.log("=== <think> tags (DeepSeek-R1 on a dedicated endpoint) ===");
  const { thinking, answer } = splitThinkTags("<think>9.9 is 9.90, and 9.90 > 9.11.</think>9.9 is bigger.");
  console.log(`Thinking: ${thinking}`);
  console.log(`Answer: ${answer}`);
  console.log();
}

// --- 3. Reasoning effort (GPT-OSS) ---
async function reasoningEffortExample(): Promise<void> {
  console.log("=== Reasoning Effort (GPT-OSS) ===");

  for (const effort of ["low", "medium", "high"] as const) {
    const stream = await client.chat.completions.create({
      model: "openai/gpt-oss-120b",
      messages: [{ role: "user", content: "Is 17 a prime number?" }],
      temperature: 1.0,
      top_p: 1.0,
      reasoning_effort: effort,
      stream: true,
    });

    let content = "";
    for await (const chunk of stream) {
      content += chunk.choices[0]?.delta?.content || "";
    }

    console.log(`  effort=${effort}: ${content.slice(0, 100)}...`);
  }
  console.log();
}

// --- 4. Toggle reasoning on hybrid models ---
async function toggleReasoning(): Promise<void> {
  console.log("=== Toggle Reasoning (Kimi K3) ===");

  // Reasoning enabled (thinking mode)
  console.log("  [reasoning=true]");
  const enabledParams: ReasoningParams = {
    model: "moonshotai/Kimi-K3",
    messages: [
      { role: "user", content: "What is the capital of France?" },
    ],
    reasoning: { enabled: true },
    temperature: 1.0,
    stream: true,
  };

  const stream = await client.chat.completions.create(enabledParams);

  let reasoningText = "";
  let contentText = "";
  for await (const chunk of stream) {
    const delta = chunk.choices[0]?.delta as ReasoningDelta;
    const trace = delta?.reasoning ?? delta?.reasoning_content;
    if (trace) reasoningText += trace;
    if (delta?.content) contentText += delta.content;
  }

  console.log(`  Reasoning tokens: ${reasoningText.length} chars`);
  console.log(`  Answer: ${contentText.slice(0, 100)}`);

  // Reasoning disabled (instant mode)
  console.log("  [reasoning=false]");
  const disabledParams = {
    model: "moonshotai/Kimi-K3",
    messages: [
      { role: "user", content: "What is the capital of France?" },
    ] as ChatCompletionMessageParam[],
    reasoning: { enabled: false },
    temperature: 0.6,
  };

  const response = await client.chat.completions.create(disabledParams);
  console.log(`  Answer: ${response.choices[0].message.content?.slice(0, 100)}`);
}

async function main(): Promise<void> {
  await reasoningFieldStreaming();
  thinkTagsExample();
  await reasoningEffortExample();
  await toggleReasoning();
}

main();
