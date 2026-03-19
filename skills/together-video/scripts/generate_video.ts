#!/usr/bin/env -S npx tsx
/**
 * Together AI Video Generation -- Text-to-Video with Polling
 *
 * Submit a video job, poll for completion, and log the result.
 * Demonstrates text-to-video, advanced parameters, and keyframes.
 *
 * Usage:
 *   npx tsx generate_video.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function waitForVideo(
  jobId: string,
  pollMs: number = 5000,
  timeoutMs: number = 600_000,
): Promise<string> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const status = await client.videos.retrieve(jobId);
    const elapsed = Math.round((Date.now() - start) / 1000);
    console.log(`  Status: ${status.status}  (${elapsed}s)`);

    if (status.status === "completed") {
      const url = status.outputs.video_url;
      console.log(`  Video ready! Cost: $${status.outputs.cost}`);
      console.log(`  URL: ${url}`);
      return url;
    }
    if (status.status === "failed") {
      throw new Error(`Video generation failed: ${JSON.stringify(status.error)}`);
    }

    await new Promise((r) => setTimeout(r, pollMs));
  }
  throw new Error(`Video job ${jobId} did not complete within ${timeoutMs / 1000}s`);
}

async function basicTextToVideo(): Promise<void> {
  console.log("=== Basic Text-to-Video ===");
  const job = await client.videos.create({
    prompt: "A serene sunset over the ocean with gentle waves",
    model: "minimax/video-01-director",
    width: 1366,
    height: 768,
  });
  console.log(`Job ID: ${job.id}`);
  await waitForVideo(job.id);
}

async function advancedParameters(): Promise<void> {
  console.log("\n=== Advanced Parameters ===");
  const job = await client.videos.create({
    prompt: "A futuristic city at night with neon lights reflecting on wet streets",
    model: "minimax/hailuo-02",
    width: 1366,
    height: 768,
    seconds: 6,
    fps: 30,
    steps: 30,
    guidance_scale: 8.0,
    output_format: "MP4",
    output_quality: 20,
    seed: 42,
    negative_prompt: "blurry, low quality, distorted",
  });
  console.log(`Job ID: ${job.id}`);
  await waitForVideo(job.id);
}

async function imageToVideo(): Promise<void> {
  console.log("\n=== Image-to-Video (Keyframe) ===");
  const job = await client.videos.create({
    prompt: "Smooth camera zoom out revealing a vast landscape",
    model: "minimax/hailuo-02",
    width: 1366,
    height: 768,
    frame_images: [
      {
        input_image:
          "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
        frame: "first",
      },
    ],
  });
  console.log(`Job ID: ${job.id}`);
  await waitForVideo(job.id);
}

async function main(): Promise<void> {
  await basicTextToVideo();
  // Uncomment to run additional examples:
  // await advancedParameters();
  // await imageToVideo();
}

main();
