#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: audio-speech, fetchVoices
 * Minimal edits: wrapped in main() for script execution.
 */

import Together from "together-ai";
import { createWriteStream } from "fs";
import { join } from "path";
import { pipeline } from "stream/promises";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const speechResponse = await client.audio.speech.create({
    model: "cartesia/sonic-2",
    input: "The quick brown fox jumps over the lazy dog.",
    voice: "laidback woman",
  });

  const filepath = join(process.cwd(), "audio.wav");
  const writeStream = createWriteStream(filepath);

  if (speechResponse.body) {
    await pipeline(speechResponse.body, writeStream);
  }

  const voicesResponse = await client.audio.voices.list();
  console.log(voicesResponse.data);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
