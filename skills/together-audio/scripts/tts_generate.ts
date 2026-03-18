#!/usr/bin/env -S npx tsx
/**
 * Together AI Text-to-Speech — REST and Streaming (TypeScript SDK)
 *
 * Two TTS modes: REST (file output) and streaming (low latency).
 *
 * Usage:
 *     npx tsx tts_generate.ts
 *
 * Requires:
 *     npm install together-ai
 *     export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import { createWriteStream } from "fs";
import { pipeline } from "stream/promises";

const client = new Together();

async function ttsRest(text: string, outputFile: string = "speech.mp3") {
  console.log(`\n=== REST TTS ===`);

  const response = await client.audio.speech.create({
    model: "canopylabs/orpheus-3b-0.1-ft",
    input: text,
    voice: "tara",
    response_format: "mp3",
  });

  const writeStream = createWriteStream(outputFile);
  if (response.body) {
    await pipeline(response.body, writeStream);
  }
  console.log(`Saved to ${outputFile}`);
}

async function ttsStreaming(
  text: string,
  outputFile: string = "speech_stream.raw"
) {
  console.log(`\n=== Streaming TTS ===`);

  const response = await client.audio.speech.create({
    model: "canopylabs/orpheus-3b-0.1-ft",
    input: text,
    voice: "tara",
    stream: true,
    response_format: "raw",
    response_encoding: "pcm_s16le",
  });

  const chunks: any[] = [];
  for await (const chunk of response) {
    chunks.push(chunk);
  }
  console.log(`Streaming complete! Received ${chunks.length} chunks`);
}

async function listVoices() {
  console.log(`\n=== Available Voices ===`);

  const response = await client.audio.voices.list();
  for (const modelVoices of response.data ?? []) {
    console.log(`Model: ${modelVoices.model}`);
    for (const voice of modelVoices.voices ?? []) {
      console.log(`  - ${voice.name}`);
    }
  }
}

async function main() {
  const text = "Today is a wonderful day to build something people love!";

  // REST — simple file output
  await ttsRest(text);

  // Streaming — low-latency first byte
  await ttsStreaming(text);

  // List voices
  // await listVoices();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
