#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: batch-list, batch-create, batch-get, batch-cancel
 * Minimal edits: wrapped in main() and placeholder IDs retained.
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const batches = await client.batches.list();
  console.log(batches);

  const created = await client.batches.create({
    endpoint: "/v1/chat/completions",
    input_file_id: "file-id",
  });
  console.log(created);

  const retrieved = await client.batches.retrieve("batch-id");
  console.log(retrieved);

  const canceled = await client.batches.cancel("batch-id");
  console.log(canceled);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
