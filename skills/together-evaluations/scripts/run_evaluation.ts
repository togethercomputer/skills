#!/usr/bin/env -S npx tsx
/**
 * Source: mintlify-docs-main/openapi.yaml x-codeSamples
 * Operations: createEvaluationJob, getEvaluationJobDetails, getEvaluationJobStatusAndResults
 * Minimal edits: wrapped in main() and placeholder IDs retained.
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function main() {
  const created = await client.evals.create({
    type: "classify",
    parameters: {
      judge: {
        model: "meta-llama/Llama-3.1-70B-Instruct-Turbo",
        model_source: "serverless",
        system_template: "You are an expert evaluator...",
      },
      input_data_file_path: "file-abc123",
      labels: ["good", "bad"],
      pass_labels: ["good"],
      model_to_evaluate: "meta-llama/Llama-3.1-8B-Instruct-Turbo",
    },
  });

  console.log(created.workflow_id);

  const details = await client.evals.retrieve("eval_id");
  console.log(details);

  const status = await client.evals.status("eval_id");
  console.log(status.status);
  console.log(status.results);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
