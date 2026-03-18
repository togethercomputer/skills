#!/usr/bin/env -S npx tsx
/**
 * Together AI Evaluations — Run Classify, Score, and Compare (TypeScript SDK)
 *
 * Upload a dataset, create an evaluation, poll for results.
 * Demonstrates all three evaluation types.
 *
 * Usage:
 *     npx tsx run_evaluation.ts
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

const JUDGE_MODEL = "deepseek-ai/DeepSeek-V3.1";
const EVAL_MODEL = "Qwen/Qwen3.5-9B";

async function uploadDataset(
  dataset: Record<string, string>[]
): Promise<string> {
  const dataPath = path.join(os.tmpdir(), `eval_data_${Date.now()}.jsonl`);
  const lines = dataset.map((r) => JSON.stringify(r)).join("\n") + "\n";
  fs.writeFileSync(dataPath, lines);

  const fileResp = await client.files.upload({
    file: fs.createReadStream(dataPath),
    purpose: "eval",
  });
  console.log(`Uploaded dataset: ${fileResp.id}`);
  return fileResp.id;
}

async function pollEvaluation(workflowId: string): Promise<any> {
  while (true) {
    const result = await client.evals.retrieve(workflowId);
    console.log(`  Status: ${result.status}`);

    if (result.status === "completed") {
      return result;
    } else if (result.status === "error" || result.status === "user_error") {
      console.error("Evaluation failed");
      return result;
    }

    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
}

async function runClassify() {
  console.log("\n=== Classify Evaluation ===");

  const dataset = [
    { prompt: "The product arrived on time and works perfectly!" },
    { prompt: "Terrible experience. The item was broken." },
    { prompt: "It's okay, nothing special." },
  ];
  const fileId = await uploadDataset(dataset);

  const evaluation = await client.evals.create({
    type: "classify",
    parameters: {
      input_data_file_path: fileId,
      judge: {
        model: JUDGE_MODEL,
        model_source: "serverless",
        system_template:
          "Classify the following text as positive, negative, or neutral sentiment.",
      },
      labels: ["positive", "negative", "neutral"],
      pass_labels: ["positive"],
      model_to_evaluate: {
        model: EVAL_MODEL,
        model_source: "serverless",
        system_template: "You are a helpful assistant.",
        input_template: "{{prompt}}",
        max_tokens: 512,
        temperature: 0.7,
      },
    },
  });
  console.log(`Created evaluation: ${evaluation.workflow_id}`);

  const result = await pollEvaluation(evaluation.workflow_id!);
  if (result.results) {
    console.log(`  Label counts: ${JSON.stringify(result.results.label_counts)}`);
    console.log(`  Pass percentage: ${result.results.pass_percentage}`);
    if (result.results.result_file_id) {
      console.log(`  Result file: ${result.results.result_file_id}`);
    }
  }
}

async function runScore() {
  console.log("\n=== Score Evaluation ===");

  const dataset = [
    { prompt: "Explain quantum computing in simple terms." },
    { prompt: "What causes rainbows?" },
    { prompt: "How do vaccines work?" },
  ];
  const fileId = await uploadDataset(dataset);

  const evaluation = await client.evals.create({
    type: "score",
    parameters: {
      input_data_file_path: fileId,
      judge: {
        model: JUDGE_MODEL,
        model_source: "serverless",
        system_template:
          "Rate the quality of the response from 1 to 10. Consider accuracy, clarity, and completeness.",
      },
      min_score: 1.0,
      max_score: 10.0,
      pass_threshold: 7.0,
      model_to_evaluate: {
        model: EVAL_MODEL,
        model_source: "serverless",
        system_template: "You are a helpful assistant.",
        input_template: "{{prompt}}",
        max_tokens: 512,
        temperature: 0.7,
      },
    },
  });
  console.log(`Created evaluation: ${evaluation.workflow_id}`);

  const result = await pollEvaluation(evaluation.workflow_id!);
  if (result.results?.aggregated_scores) {
    const scores = result.results.aggregated_scores;
    console.log(`  Mean score: ${scores.mean_score}`);
    console.log(`  Std score: ${scores.std_score}`);
    console.log(`  Pass percentage: ${scores.pass_percentage}`);
  }
}

async function runCompare() {
  console.log("\n=== Compare Evaluation ===");

  const dataset = [
    { prompt: "Explain the theory of relativity." },
    { prompt: "What is the meaning of life?" },
    { prompt: "How does photosynthesis work?" },
  ];
  const fileId = await uploadDataset(dataset);

  const evaluation = await client.evals.create({
    type: "compare",
    parameters: {
      input_data_file_path: fileId,
      judge: {
        model: JUDGE_MODEL,
        model_source: "serverless",
        system_template:
          "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness.",
      },
      model_a: {
        model: "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
        model_source: "serverless",
        system_template: "You are a helpful assistant.",
        input_template: "{{prompt}}",
        max_tokens: 512,
        temperature: 0.7,
      },
      model_b: {
        model: EVAL_MODEL,
        model_source: "serverless",
        system_template: "You are a helpful assistant.",
        input_template: "{{prompt}}",
        max_tokens: 512,
        temperature: 0.7,
      },
    },
  });
  console.log(`Created evaluation: ${evaluation.workflow_id}`);

  const result = await pollEvaluation(evaluation.workflow_id!);
  if (result.results) {
    console.log(`  A wins: ${result.results.A_wins}`);
    console.log(`  B wins: ${result.results.B_wins}`);
    console.log(`  Ties: ${result.results.Ties}`);
  }
}

async function main() {
  await runClassify();
  // await runScore();
  // await runCompare();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
