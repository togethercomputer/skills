#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: audio-transcriptions, audio-translations
 * Minimal edits: wrapped in main() for script execution.
 */

import Together from "together-ai";
import { readFileSync } from "fs";
import { join } from "path";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const audioFilePath = join(process.cwd(), "audio.wav");
  const audioBuffer = readFileSync(audioFilePath);
  const audioFile = new File([audioBuffer], "audio.wav", { type: "audio/wav" });

  const transcriptionResponse = await client.audio.transcriptions.create({
    model: "openai/whisper-large-v3",
    file: audioFile,
  });

  console.log(transcriptionResponse.text);

  const translationResponse = await client.audio.translations.create({
    model: "openai/whisper-large-v3",
    file: audioFile,
    language: "es",
  });

  console.log(translationResponse.text);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
