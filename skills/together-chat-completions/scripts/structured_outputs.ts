#!/usr/bin/env -S npx tsx
/**
 * Together AI Chat Completions — Structured Outputs
 *
 * Demonstrates json_schema (with Zod), json_object, and regex response formats.
 *
 * Usage:
 *   npx tsx structured_outputs.ts
 *
 * Requires:
 *   npm install together-ai zod
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import { z } from "zod";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

// --- 1. json_schema with Zod ---
async function jsonSchemaExample(): Promise<void> {
  console.log("=== json_schema (Zod) ===");

  const voiceNoteSchema = z.object({
    title: z.string().describe("A title for the voice note"),
    summary: z.string().describe("A short one sentence summary of the voice note."),
    actionItems: z.array(z.string()).describe("A list of action items from the voice note"),
  });
  const jsonSchema = z.toJSONSchema(voiceNoteSchema);

  const transcript =
    "Good morning! Today is going to be a busy day. First, I need to make a quick " +
    "breakfast. While cooking, I'll also check my emails to see if there's anything " +
    "urgent. Then I have a meeting at 10am to discuss the Q4 roadmap.";

  const extract = await client.chat.completions.create({
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
    console.log(JSON.stringify(output, null, 2));
  }
  console.log();
}

// --- 2. json_object (simple) ---
async function jsonObjectExample(): Promise<void> {
  console.log("=== json_object (simple) ===");

  const response = await client.chat.completions.create({
    model: "openai/gpt-oss-20b",
    messages: [
      { role: "system", content: "Respond in JSON with keys: name, age, city, hobby" },
      { role: "user", content: "Make up a character for a story" },
    ],
    response_format: { type: "json_object" },
  });

  if (response?.choices?.[0]?.message?.content) {
    const output = JSON.parse(response.choices[0].message.content);
    console.log(JSON.stringify(output, null, 2));
  }
  console.log();
}

// --- 3. regex (classification) ---
async function regexExample(): Promise<void> {
  console.log("=== regex (classification) ===");

  const response = await client.chat.completions.create({
    model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    temperature: 0.2,
    max_tokens: 10,
    messages: [
      {
        role: "system",
        content: "Classify the sentiment of the text as positive, neutral, or negative.",
      },
      {
        role: "user",
        content: "The food was absolutely amazing, best meal I've ever had!",
      },
    ],
    response_format: {
      type: "regex",
      // @ts-ignore
      pattern: "(positive|neutral|negative)",
    },
  });

  console.log(`Sentiment: ${response?.choices[0]?.message?.content}`);
  console.log();
}

// --- 4. json_schema with reasoning model ---
async function reasoningJsonExample(): Promise<void> {
  console.log("=== json_schema + reasoning model ===");

  const stepSchema = z.object({
    explanation: z.string(),
    output: z.string(),
  });
  const mathReasoningSchema = z.object({
    steps: z.array(stepSchema),
    final_answer: z.string(),
  });
  const jsonSchema = z.toJSONSchema(mathReasoningSchema);

  const completion = await client.chat.completions.create({
    model: "deepseek-ai/DeepSeek-R1",
    messages: [
      {
        role: "system",
        content: "You are a helpful math tutor. Guide the user through the solution step by step.",
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
}

async function main(): Promise<void> {
  await jsonSchemaExample();
  await jsonObjectExample();
  await regexExample();
  await reasoningJsonExample();
}

main();
