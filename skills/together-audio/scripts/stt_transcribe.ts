#!/usr/bin/env -S npx tsx
/**
 * Together AI Speech-to-Text — Transcribe, Translate, Timestamps, Diarize (TypeScript SDK)
 *
 * Demonstrates transcription, translation, word timestamps, and speaker diarization.
 *
 * Usage:
 *     npx tsx stt_transcribe.ts <audio_file> [--translate] [--diarize] [--timestamps]
 *
 * Requires:
 *     npm install together-ai
 *     export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import { readFileSync } from "fs";

const client = new Together();

function loadAudioFile(filePath: string): File {
  const buffer = readFileSync(filePath);
  const ext = filePath.split(".").pop() ?? "wav";
  const mimeMap: Record<string, string> = {
    wav: "audio/wav",
    mp3: "audio/mpeg",
    m4a: "audio/mp4",
    webm: "audio/webm",
    flac: "audio/flac",
  };
  return new File([buffer], filePath, { type: mimeMap[ext] ?? "audio/wav" });
}

async function transcribe(filePath: string) {
  console.log("\n=== Basic Transcription ===");

  const audioFile = loadAudioFile(filePath);
  const response = await client.audio.transcriptions.create({
    model: "openai/whisper-large-v3",
    file: audioFile,
    language: "en",
  });
  console.log(`Transcription: ${response.text}`);
}

async function transcribeWithTimestamps(filePath: string) {
  console.log("\n=== Transcription with Word Timestamps ===");

  const audioFile = loadAudioFile(filePath);
  const response: any = await client.audio.transcriptions.create({
    model: "openai/whisper-large-v3",
    file: audioFile,
    response_format: "verbose_json",
    timestamp_granularities: "word",
  });

  console.log(`Text: ${response.text}`);
  console.log(`Duration: ${response.duration}s`);

  if (response.words) {
    for (const word of response.words) {
      console.log(`  [${word.start.toFixed(2)}s - ${word.end.toFixed(2)}s] ${word.word}`);
    }
  }
}

async function transcribeWithDiarization(filePath: string) {
  console.log("\n=== Transcription with Speaker Diarization ===");

  const audioFile = loadAudioFile(filePath);
  const response: any = await client.audio.transcriptions.create({
    model: "openai/whisper-large-v3",
    file: audioFile,
    diarize: true,
  });

  console.log(`Text: ${response.text}`);

  if (response.speaker_segments) {
    for (const segment of response.speaker_segments) {
      console.log(
        `  [${segment.speaker_id}] (${segment.start.toFixed(1)}s-${segment.end.toFixed(1)}s): ${segment.text}`
      );
    }
  }
}

async function translateToEnglish(filePath: string) {
  console.log("\n=== Translation to English ===");

  const audioFile = loadAudioFile(filePath);
  const response = await client.audio.translations.create({
    model: "openai/whisper-large-v3",
    file: audioFile,
  });
  console.log(`English translation: ${response.text}`);
}

async function main() {
  const args = process.argv.slice(2);
  const filePath = args.find((a) => !a.startsWith("--"));

  if (!filePath) {
    console.log(
      "Usage: npx tsx stt_transcribe.ts <audio_file> [--translate] [--diarize] [--timestamps]"
    );
    process.exit(1);
  }

  const flags = args.filter((a) => a.startsWith("--"));

  if (flags.includes("--translate")) {
    await translateToEnglish(filePath);
  } else if (flags.includes("--diarize")) {
    await transcribeWithDiarization(filePath);
  } else if (flags.includes("--timestamps")) {
    await transcribeWithTimestamps(filePath);
  } else {
    await transcribe(filePath);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
