#!/usr/bin/env -S npx tsx
/**
 * Together AI Batch Inference — Full Workflow (TypeScript SDK)
 *
 * End-to-end: prepare JSONL → upload → create batch → poll → download results.
 *
 * Usage:
 *     npx tsx batch_workflow.ts
 *
 * Requires:
 *     npm install together-ai
 *     export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const client = new Together();

async function main() {
  // --- 1. Prepare batch input file ---
  const requests = [
    {
      custom_id: "req-1",
      body: {
        model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
        messages: [{ role: "user", content: "What is the capital of France?" }],
        max_tokens: 128,
      },
    },
    {
      custom_id: "req-2",
      body: {
        model: "Qwen/Qwen2.5-7B-Instruct-Turbo",
        messages: [
          {
            role: "user",
            content: "Explain quantum computing in one sentence.",
          },
        ],
        max_tokens: 128,
      },
    },
  ];

  const inputPath = path.join(os.tmpdir(), `batch_input_${Date.now()}.jsonl`);
  const lines = requests.map((r) => JSON.stringify(r)).join("\n") + "\n";
  fs.writeFileSync(inputPath, lines);
  console.log(`Wrote ${requests.length} requests to ${inputPath}`);

  // --- 2. Upload input file ---
  const fileResp = await client.files.upload(inputPath, "batch-api", false);
  const fileId = fileResp.id;
  console.log(`Uploaded file: ${fileId}`);

  // --- 3. Create batch job ---
  const response = await client.batches.create({
    input_file_id: fileId,
    endpoint: "/v1/chat/completions",
  });
  const batchId = response.job?.id;
  if (!batchId) {
    throw new Error("Batch create response did not include a job id.");
  }
  console.log(`Created batch: ${batchId}`);

  // --- 4. Poll for completion ---
  let batch: any;
  while (true) {
    batch = await client.batches.retrieve(batchId);
    console.log(
      `  Status: ${batch.status} | Progress: ${(batch.progress ?? 0).toFixed(0)}%`
    );

    if (batch.status === "COMPLETED") {
      break;
    } else if (["FAILED", "EXPIRED", "CANCELLED"].includes(batch.status)) {
      console.error(`Batch ended with status: ${batch.status}`);
      if (batch.error) console.error(`Error: ${batch.error}`);
      process.exit(1);
    }

    await new Promise((resolve) => setTimeout(resolve, 10_000));
  }

  // --- 5. Download results ---
  if (batch.output_file_id) {
    const resp = await client.files.content(batch.output_file_id);
    const text = await resp.text();
    const outputPath = "batch_results.jsonl";
    fs.writeFileSync(outputPath, text);
    console.log(`\nResults saved to ${outputPath}`);

    for (const line of text.trim().split("\n")) {
      const result = JSON.parse(line);
      const customId = result.custom_id ?? "?";
      const content =
        result.response?.body?.choices?.[0]?.message?.content ?? "";
      console.log(`  [${customId}] ${content.slice(0, 100)}`);
    }
  }

  // --- 6. Check for errors ---
  if (batch.error_file_id) {
    const errResp = await client.files.content(batch.error_file_id);
    const errText = await errResp.text();
    const errorPath = "batch_errors.jsonl";
    fs.writeFileSync(errorPath, errText);
    console.log(`Errors saved to ${errorPath}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
