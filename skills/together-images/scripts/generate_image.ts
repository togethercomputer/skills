#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operation: post-images-generations
 * Minimal edits: wrapped in main() for script execution.
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const response = await client.images.generate({
    model: "black-forest-labs/FLUX.1-schnell",
    prompt: "A cartoon of an astronaut riding a horse on the moon",
  });

  console.log(response.data[0].url);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
