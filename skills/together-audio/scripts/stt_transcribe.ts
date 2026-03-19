#!/usr/bin/env -S npx tsx
/**
 * Together AI speech-to-text examples with the TypeScript SDK.
 *
 * Demonstrates:
 * - transcription
 * - translation
 * - diarization
 * - timestamps
 *
 * Usage:
 *   npx tsx stt_transcribe.ts transcribe audio.mp3
 *   npx tsx stt_transcribe.ts translate foreign_audio.mp3 --target-language en
 *   npx tsx stt_transcribe.ts diarize meeting.mp3 --min-speakers 2 --max-speakers 5
 *   npx tsx stt_transcribe.ts timestamps audio.mp3 --granularity word
 *
 * Requirements:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import { readFileSync } from "fs";

const client = new Together();

type Mode = "transcribe" | "translate" | "diarize" | "timestamps";

interface ParsedArgs {
  mode: Mode;
  audioFile: string;
  model: string;
  language?: string;
  targetLanguage?: string;
  prompt?: string;
  temperature?: number;
  granularity: "segment" | "word";
  minSpeakers: number;
  maxSpeakers: number;
}

function parseArgs(): ParsedArgs {
  const raw = process.argv.slice(2);
  const get = (flag: string): string | undefined => {
    const index = raw.indexOf(flag);
    if (index === -1) return undefined;
    return raw[index + 1];
  };

  const mode = raw[0] as Mode | undefined;
  const audioFile = raw[1];

  if (!mode || !audioFile) {
    console.error(
      "Usage: npx tsx stt_transcribe.ts <transcribe|translate|diarize|timestamps> <audio_file> [options]",
    );
    process.exit(1);
  }

  if (!["transcribe", "translate", "diarize", "timestamps"].includes(mode)) {
    console.error("Mode must be one of: transcribe, translate, diarize, timestamps");
    process.exit(1);
  }

  const temperature = get("--temperature");
  return {
    mode,
    audioFile,
    model: get("--model") ?? "openai/whisper-large-v3",
    language: get("--language"),
    targetLanguage: get("--target-language"),
    prompt: get("--prompt"),
    temperature: temperature ? Number(temperature) : undefined,
    granularity: (get("--granularity") ?? "word") as "segment" | "word",
    minSpeakers: Number(get("--min-speakers") ?? "1"),
    maxSpeakers: Number(get("--max-speakers") ?? "5"),
  };
}

function loadAudioFile(filePath: string): File {
  const buffer = readFileSync(filePath);
  const ext = filePath.split(".").pop()?.toLowerCase() ?? "wav";
  const mimeMap: Record<string, string> = {
    wav: "audio/wav",
    mp3: "audio/mpeg",
    m4a: "audio/mp4",
    webm: "audio/webm",
    flac: "audio/flac",
  };
  return new File([buffer], filePath, { type: mimeMap[ext] ?? "audio/wav" });
}

async function transcribe(args: ParsedArgs): Promise<void> {
  const payload: Record<string, unknown> = {
    file: loadAudioFile(args.audioFile),
    model: args.model,
    response_format: "json",
  };
  if (args.language) payload.language = args.language;
  if (args.prompt) payload.prompt = args.prompt;
  if (typeof args.temperature === "number") payload.temperature = args.temperature;

  const response = await client.audio.transcriptions.create(payload);
  console.log(`Transcription: ${response.text}`);
}

async function translate(args: ParsedArgs): Promise<void> {
  const payload: Record<string, unknown> = {
    file: loadAudioFile(args.audioFile),
    model: args.model,
  };
  if (args.targetLanguage ?? args.language) {
    payload.language = args.targetLanguage ?? args.language;
  }
  if (args.prompt) payload.prompt = args.prompt;
  if (typeof args.temperature === "number") payload.temperature = args.temperature;

  const response = await client.audio.translations.create(payload);
  console.log(`Translation: ${response.text}`);
}

async function diarize(args: ParsedArgs): Promise<void> {
  const response: any = await client.audio.transcriptions.create({
    file: loadAudioFile(args.audioFile),
    model: args.model,
    response_format: "verbose_json",
    diarize: true,
    min_speakers: args.minSpeakers,
    max_speakers: args.maxSpeakers,
  });

  if (!response.speaker_segments?.length) {
    console.log("No speaker segments returned.");
    return;
  }

  for (const segment of response.speaker_segments) {
    console.log(
      `[${segment.speaker_id}] ${segment.start.toFixed(1)}s-${segment.end.toFixed(1)}s: ${segment.text}`,
    );
  }
}

async function timestamps(args: ParsedArgs): Promise<void> {
  const response: any = await client.audio.transcriptions.create({
    file: loadAudioFile(args.audioFile),
    model: args.model,
    response_format: "verbose_json",
    timestamp_granularities: args.granularity,
  });

  console.log(`Text: ${response.text}`);
  console.log(`Language: ${response.language}`);
  console.log(`Duration: ${response.duration}s`);

  if (args.granularity === "word" && response.words) {
    for (const word of response.words) {
      console.log(`'${word.word}' [${word.start.toFixed(2)}s - ${word.end.toFixed(2)}s]`);
    }
    return;
  }

  if (response.segments) {
    for (const segment of response.segments) {
      console.log(`[${segment.start.toFixed(2)}s - ${segment.end.toFixed(2)}s] ${segment.text}`);
    }
  }
}

async function main(): Promise<void> {
  const args = parseArgs();

  if (args.mode === "transcribe") {
    await transcribe(args);
    return;
  }

  if (args.mode === "translate") {
    await translate(args);
    return;
  }

  if (args.mode === "diarize") {
    await diarize(args);
    return;
  }

  await timestamps(args);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
