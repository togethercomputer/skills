#!/usr/bin/env -S npx tsx
/**
 * Together AI text-to-speech examples with the TypeScript SDK.
 *
 * Demonstrates:
 * - REST file generation
 * - Streaming HTTP generation
 * - Voice discovery
 *
 * Usage:
 *   npx tsx tts_generate.ts --mode rest --text "Hello world" --output speech.mp3
 *   npx tsx tts_generate.ts --mode stream --text "Hello world" --output speech_stream.pcm
 *   npx tsx tts_generate.ts --mode voices
 *
 * Requirements:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import { createWriteStream, promises as fs } from "fs";
import { Readable } from "stream";
import { pipeline } from "stream/promises";

const client = new Together();

type Mode = "rest" | "stream" | "voices";

interface ParsedArgs {
  mode: Mode;
  text: string;
  output: string;
  model: string;
  voice: string;
  responseFormat: "mp3" | "wav";
  responseEncoding: "pcm_f32le" | "pcm_s16le" | "pcm_mulaw" | "pcm_alaw";
  language?: string;
  sampleRate?: number;
  alignment: "none" | "word";
  segment: "sentence" | "immediate" | "never";
}

function parseArgs(): ParsedArgs {
  const raw = process.argv.slice(2);
  const get = (flag: string): string | undefined => {
    const index = raw.indexOf(flag);
    if (index === -1) return undefined;
    return raw[index + 1];
  };

  const mode = (get("--mode") ?? "rest") as Mode;
  const responseFormat = (get("--response-format") ?? "mp3") as ParsedArgs["responseFormat"];
  const responseEncoding = (get("--response-encoding") ?? "pcm_s16le") as ParsedArgs["responseEncoding"];
  const alignment = (get("--alignment") ?? "none") as ParsedArgs["alignment"];
  const segment = (get("--segment") ?? "sentence") as ParsedArgs["segment"];
  const sampleRate = get("--sample-rate");

  if (!["rest", "stream", "voices"].includes(mode)) {
    console.error("Expected --mode to be one of: rest, stream, voices");
    process.exit(1);
  }

  return {
    mode,
    text: get("--text") ?? "Today is a wonderful day to build something people love!",
    output: get("--output") ?? "speech.mp3",
    model: get("--model") ?? "canopylabs/orpheus-3b-0.1-ft",
    voice: get("--voice") ?? "tara",
    responseFormat,
    responseEncoding,
    language: get("--language"),
    sampleRate: sampleRate ? Number(sampleRate) : undefined,
    alignment,
    segment,
  };
}

async function writeBodyToFile(body: unknown, outputFile: string): Promise<void> {
  if (!body) {
    throw new Error("Expected a response body");
  }

  if (typeof (body as NodeJS.ReadableStream).pipe === "function") {
    await pipeline(body as NodeJS.ReadableStream, createWriteStream(outputFile));
    return;
  }

  if (typeof (body as ReadableStream<Uint8Array>).getReader === "function") {
    const nodeStream = Readable.fromWeb(body as ReadableStream<Uint8Array>);
    await pipeline(nodeStream, createWriteStream(outputFile));
    return;
  }

  throw new Error("Unsupported response body type");
}

function parseStreamingPayloads(chunk: unknown): Array<Record<string, unknown>> {
  if (chunk && typeof chunk === "object" && "type" in (chunk as Record<string, unknown>)) {
    return [chunk as Record<string, unknown>];
  }

  const text =
    typeof chunk === "string"
      ? chunk
      : chunk instanceof Uint8Array
        ? Buffer.from(chunk).toString("utf8")
        : Buffer.isBuffer(chunk)
          ? chunk.toString("utf8")
          : "";

  if (!text) return [];

  const payloads: Array<Record<string, unknown>> = [];
  for (const line of text.split("\n")) {
    if (!line.startsWith("data:")) continue;
    const data = line.slice(5).trim();
    if (!data || data === "[DONE]") continue;
    try {
      payloads.push(JSON.parse(data) as Record<string, unknown>);
    } catch {
      // Ignore malformed SSE lines.
    }
  }
  return payloads;
}

async function generateRest(args: ParsedArgs): Promise<void> {
  const payload: Record<string, unknown> = {
    model: args.model,
    input: args.text,
    voice: args.voice,
    response_format: args.responseFormat,
  };
  if (args.language) payload.language = args.language;
  if (typeof args.sampleRate === "number") payload.sample_rate = args.sampleRate;

  const response = await client.audio.speech.create(payload);
  await writeBodyToFile(response.body, args.output);
  console.log(`Saved ${args.responseFormat} audio to ${args.output}`);
}

async function generateStream(args: ParsedArgs): Promise<void> {
  const payload: Record<string, unknown> = {
    model: args.model,
    input: args.text,
    voice: args.voice,
    stream: true,
    response_format: "raw",
    response_encoding: args.responseEncoding,
    alignment: args.alignment,
    segment: args.segment,
  };
  if (args.language) payload.language = args.language;
  if (typeof args.sampleRate === "number") payload.sample_rate = args.sampleRate;

  const response = await client.audio.speech.create(payload);
  const rawChunks: Buffer[] = [];

  for await (const chunk of response as AsyncIterable<unknown>) {
    for (const event of parseStreamingPayloads(chunk)) {
      if (event.type === "conversation.item.audio_output.delta" && typeof event.delta === "string") {
        rawChunks.push(Buffer.from(event.delta, "base64"));
      }
      if (event.type === "conversation.item.word_timestamps") {
        console.log(JSON.stringify(event));
      }
    }
  }

  await fs.writeFile(args.output, Buffer.concat(rawChunks));
  console.log(`Saved raw streaming audio to ${args.output}`);
}

async function listVoices(): Promise<void> {
  const response = await client.audio.voices.list();
  for (const modelVoices of response.data ?? []) {
    console.log(`Model: ${modelVoices.model}`);
    for (const voice of modelVoices.voices ?? []) {
      console.log(`  - ${voice.name}`);
    }
  }
}

async function main(): Promise<void> {
  const args = parseArgs();

  if (args.mode === "voices") {
    await listVoices();
    return;
  }

  if (args.mode === "rest") {
    await generateRest(args);
    return;
  }

  await generateStream(args);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
