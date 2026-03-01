#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: createVideo, retrieveVideo
 * Minimal edits: wrapped in main() and reuse created id for retrieve.
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const createResponse = await client.videos.create({
    model: "together/video-model",
    prompt: "A cartoon of an astronaut riding a horse on the moon",
  });

  console.log(createResponse.id);

  const retrieveResponse = await client.videos.retrieve(createResponse.id);
  console.log(retrieveResponse.status);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
