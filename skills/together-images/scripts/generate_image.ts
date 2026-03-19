#!/usr/bin/env -S npx tsx
/**
 * Together AI Image Generation -- Text-to-Image, Editing, FLUX.2
 *
 * Generate images from text, edit with Kontext, use FLUX.2 features.
 *
 * Usage:
 *   npx tsx generate_image.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function basicGeneration(): Promise<void> {
  console.log("=== Basic Generation (FLUX.1 Schnell) ===");
  const response = await client.images.generate({
    model: "black-forest-labs/FLUX.1-schnell",
    prompt: "A serene mountain landscape at sunset with a lake reflection",
    steps: 4,
  });
  console.log(`  Image URL: ${response.data[0].url}`);
}

async function flux2Generation(): Promise<void> {
  console.log("\n=== FLUX.2 Pro ===");
  const response = await client.images.generate({
    model: "black-forest-labs/FLUX.2-pro",
    prompt: "A mountain landscape at sunset with golden light reflecting on a calm lake",
    width: 1024,
    height: 768,
    prompt_upsampling: true,
    output_format: "png",
  });
  console.log(`  Image URL: ${response.data[0].url}`);
}

async function kontextEditing(): Promise<void> {
  console.log("\n=== Kontext Image Editing ===");
  const response = await client.images.generate({
    model: "black-forest-labs/FLUX.1-kontext-pro",
    prompt: "Transform this into a watercolor painting",
    image_url: "https://cdn.pixabay.com/photo/2020/05/20/08/27/cat-5195431_1280.jpg",
    width: 1024,
    height: 768,
    steps: 28,
  });
  console.log(`  Edited image: ${response.data[0].url}`);
}

async function multipleVariations(): Promise<void> {
  console.log("\n=== Multiple Variations ===");
  const response = await client.images.generate({
    model: "black-forest-labs/FLUX.1-schnell",
    prompt: "A cute robot assistant helping in a modern office",
    n: 4,
    steps: 4,
  });
  for (let i = 0; i < response.data.length; i++) {
    console.log(`  Variation ${i + 1}: ${response.data[i].url}`);
  }
}

async function base64Response(): Promise<void> {
  console.log("\n=== Base64 Response ===");
  const response = await client.images.generate({
    model: "black-forest-labs/FLUX.1-schnell",
    prompt: "A cat in outer space",
    response_format: "base64",
  });
  const data = response.data[0].b64_json ?? "";
  console.log(`  Base64 length: ${data.length} chars`);
}

async function main(): Promise<void> {
  await basicGeneration();
  await flux2Generation();
  await kontextEditing();
  await multipleVariations();
  await base64Response();
}

main();
