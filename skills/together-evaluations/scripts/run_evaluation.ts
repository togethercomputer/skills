#!/usr/bin/env -S npx tsx
/**
 * Together AI Evaluations — Run Classify, Score, and Compare (TypeScript SDK)
 *
 * Upload an eval dataset, create an evaluation, poll for results, and
 * optionally download the per-row results file. Supports serverless,
 * dedicated, and external judge or target models, plus dataset-column
 * evaluation for pre-generated responses.
 *
 * Usage:
 *   npx tsx run_evaluation.ts --type classify
 *   npx tsx run_evaluation.ts --type score --dataset score_prompts.jsonl --eval-column response
 *   npx tsx run_evaluation.ts --type compare --model-a-column response_a --model-b-column response_b
 *   npx tsx run_evaluation.ts --type classify --eval-model openai/gpt-5 \
 *     --eval-model-source external --eval-external-api-token "$OPENAI_API_KEY"
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import Together from "together-ai";

const client = new Together();

type EvalType = "classify" | "score" | "compare";
type ModelSource = "serverless" | "dedicated" | "external";
type DatasetRow = Record<string, unknown>;

type ScriptArgs = {
  type: EvalType;
  dataset?: string;
  judgeModel: string;
  judgeModelSource: ModelSource;
  judgeSystemTemplate?: string;
  judgeExternalApiToken?: string;
  judgeExternalBaseUrl?: string;
  evalModel: string;
  evalModelSource: ModelSource;
  evalColumn?: string;
  evalSystemTemplate: string;
  inputTemplate: string;
  maxTokens: number;
  temperature: number;
  evalExternalApiToken?: string;
  evalExternalBaseUrl?: string;
  modelA: string;
  modelASource: ModelSource;
  modelAColumn?: string;
  modelAExternalApiToken?: string;
  modelAExternalBaseUrl?: string;
  modelB: string;
  modelBSource: ModelSource;
  modelBColumn?: string;
  modelBExternalApiToken?: string;
  modelBExternalBaseUrl?: string;
  pollInterval: number;
  downloadResults?: string;
};

const JUDGE_MODEL = "deepseek-ai/DeepSeek-V3.1";
const EVAL_MODEL = "Qwen/Qwen3.5-9B";
const DEFAULT_EVAL_SYSTEM_TEMPLATE = "You are a helpful assistant.";
const DEFAULT_INPUT_TEMPLATE = "{{prompt}}";
const DEFAULT_CLASSIFY_TEMPLATE =
  "Classify the following text as positive, negative, or neutral sentiment.";
const DEFAULT_SCORE_TEMPLATE =
  "Rate the quality of the response from 1 to 10, where 1 is very poor and 10 is excellent. Consider accuracy, clarity, and completeness.";
const DEFAULT_COMPARE_TEMPLATE =
  "Please assess which model has smarter and more helpful responses. Consider clarity, accuracy, and usefulness.";

function printHelp(): void {
  console.log(`Together AI evaluations workflow

Flags:
  --type classify|score|compare
  --dataset PATH
  --judge-model MODEL
  --judge-model-source serverless|dedicated|external
  --judge-system-template TEMPLATE
  --judge-external-api-token TOKEN
  --judge-external-base-url URL
  --eval-model MODEL
  --eval-model-source serverless|dedicated|external
  --eval-column COLUMN
  --eval-system-template TEMPLATE
  --input-template TEMPLATE
  --max-tokens N
  --temperature FLOAT
  --eval-external-api-token TOKEN
  --eval-external-base-url URL
  --model-a MODEL
  --model-a-source serverless|dedicated|external
  --model-a-column COLUMN
  --model-a-external-api-token TOKEN
  --model-a-external-base-url URL
  --model-b MODEL
  --model-b-source serverless|dedicated|external
  --model-b-column COLUMN
  --model-b-external-api-token TOKEN
  --model-b-external-base-url URL
  --poll-interval SECONDS
  --download-results PATH`);
}

function parseFlagMap(argv: string[]): Record<string, string> {
  const values: Record<string, string> = {};

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help") {
      printHelp();
      process.exit(0);
    }
    if (!arg.startsWith("--")) {
      throw new Error(`Unexpected argument: ${arg}`);
    }
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      throw new Error(`Missing value for ${arg}`);
    }
    values[arg.slice(2)] = next;
    i += 1;
  }

  return values;
}

function parseEvalType(value: string | undefined): EvalType {
  const next = value ?? "classify";
  if (next === "classify" || next === "score" || next === "compare") {
    return next;
  }
  throw new Error(`Invalid --type value: ${next}`);
}

function parseModelSource(value: string | undefined, flagName: string): ModelSource {
  const next = value ?? "serverless";
  if (next === "serverless" || next === "dedicated" || next === "external") {
    return next;
  }
  throw new Error(`Invalid ${flagName} value: ${next}`);
}

function parseNumber(value: string | undefined, fallback: number, flagName: string): number {
  if (value === undefined) {
    return fallback;
  }
  const next = Number(value);
  if (!Number.isFinite(next)) {
    throw new Error(`Invalid ${flagName} value: ${value}`);
  }
  return next;
}

function parseScriptArgs(): ScriptArgs {
  const flags = parseFlagMap(process.argv.slice(2));
  const type = parseEvalType(flags.type);

  const args: ScriptArgs = {
    type,
    dataset: flags.dataset,
    judgeModel: flags["judge-model"] ?? JUDGE_MODEL,
    judgeModelSource: parseModelSource(flags["judge-model-source"], "--judge-model-source"),
    judgeSystemTemplate: flags["judge-system-template"],
    judgeExternalApiToken: flags["judge-external-api-token"],
    judgeExternalBaseUrl: flags["judge-external-base-url"],
    evalModel: flags["eval-model"] ?? EVAL_MODEL,
    evalModelSource: parseModelSource(flags["eval-model-source"], "--eval-model-source"),
    evalColumn: flags["eval-column"],
    evalSystemTemplate: flags["eval-system-template"] ?? DEFAULT_EVAL_SYSTEM_TEMPLATE,
    inputTemplate: flags["input-template"] ?? DEFAULT_INPUT_TEMPLATE,
    maxTokens: parseNumber(flags["max-tokens"], 512, "--max-tokens"),
    temperature: parseNumber(flags.temperature, 0.7, "--temperature"),
    evalExternalApiToken: flags["eval-external-api-token"],
    evalExternalBaseUrl: flags["eval-external-base-url"],
    modelA: flags["model-a"] ?? "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
    modelASource: parseModelSource(flags["model-a-source"], "--model-a-source"),
    modelAColumn: flags["model-a-column"],
    modelAExternalApiToken: flags["model-a-external-api-token"],
    modelAExternalBaseUrl: flags["model-a-external-base-url"],
    modelB: flags["model-b"] ?? EVAL_MODEL,
    modelBSource: parseModelSource(flags["model-b-source"], "--model-b-source"),
    modelBColumn: flags["model-b-column"],
    modelBExternalApiToken: flags["model-b-external-api-token"],
    modelBExternalBaseUrl: flags["model-b-external-base-url"],
    pollInterval: parseNumber(flags["poll-interval"], 5, "--poll-interval"),
    downloadResults: flags["download-results"],
  };

  if ((args.modelAColumn && !args.modelBColumn) || (args.modelBColumn && !args.modelAColumn)) {
    throw new Error("--model-a-column and --model-b-column must be provided together");
  }
  if (args.type !== "compare" && (args.modelAColumn || args.modelBColumn)) {
    throw new Error("--model-a-column and --model-b-column only apply to --type compare");
  }

  return args;
}

async function uploadDataset(dataset: DatasetRow[]): Promise<string> {
  const dataPath = path.join(os.tmpdir(), `eval_data_${Date.now()}.jsonl`);
  const lines = dataset.map((row) => JSON.stringify(row)).join("\n") + "\n";
  fs.writeFileSync(dataPath, lines, "utf8");

  try {
    const fileResponse = await client.files.upload(dataPath, "eval", false);
    console.log(`Uploaded dataset: ${fileResponse.id}`);
    return fileResponse.id;
  } finally {
    fs.rmSync(dataPath, { force: true });
  }
}

function loadDataset(datasetPath: string | undefined, fallbackRows: DatasetRow[]): DatasetRow[] {
  if (!datasetPath) {
    return fallbackRows;
  }

  return fs
    .readFileSync(datasetPath, "utf8")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as DatasetRow);
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollEvaluation(workflowId: string, pollIntervalSeconds: number): Promise<any> {
  while (true) {
    const result = await client.evals.status(workflowId);
    console.log(`  Status: ${result.status}`);

    if (result.status === "completed") {
      return result;
    }
    if (result.status === "error" || result.status === "user_error") {
      console.error("Evaluation failed");
      return result;
    }

    await sleep(pollIntervalSeconds * 1000);
  }
}

function getResultFileId(result: any): string | undefined {
  return result?.results?.result_file_id;
}

async function downloadResultFile(fileId: string, outputPath: string): Promise<void> {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const response = await client.files.content(fileId);
  const text = await response.text();
  fs.writeFileSync(outputPath, text, "utf8");
  console.log(`Saved result rows to ${outputPath}`);
}

function buildJudgeConfig(args: ScriptArgs, defaultTemplate: string): Record<string, unknown> {
  const config: Record<string, unknown> = {
    model: args.judgeModel,
    model_source: args.judgeModelSource,
    system_template: args.judgeSystemTemplate ?? defaultTemplate,
  };
  if (args.judgeExternalApiToken) {
    config.external_api_token = args.judgeExternalApiToken;
  }
  if (args.judgeExternalBaseUrl) {
    config.external_base_url = args.judgeExternalBaseUrl;
  }
  return config;
}

function buildModelConfig(options: {
  model: string;
  modelSource: ModelSource;
  systemTemplate: string;
  inputTemplate: string;
  maxTokens: number;
  temperature: number;
  externalApiToken?: string;
  externalBaseUrl?: string;
}): Record<string, unknown> {
  const config: Record<string, unknown> = {
    model: options.model,
    model_source: options.modelSource,
    system_template: options.systemTemplate,
    input_template: options.inputTemplate,
    max_tokens: options.maxTokens,
    temperature: options.temperature,
  };
  if (options.externalApiToken) {
    config.external_api_token = options.externalApiToken;
  }
  if (options.externalBaseUrl) {
    config.external_base_url = options.externalBaseUrl;
  }
  return config;
}

function sampleDatasetForArgs(args: ScriptArgs): DatasetRow[] {
  if (args.type === "compare" && args.modelAColumn && args.modelBColumn) {
    return [
      {
        prompt: "Explain the theory of relativity.",
        [args.modelAColumn]: "Relativity explains gravity as the curvature of spacetime.",
        [args.modelBColumn]: "Einstein's theory says mass bends spacetime and changes motion.",
      },
      {
        prompt: "How does photosynthesis work?",
        [args.modelAColumn]: "Plants convert sunlight, water, and carbon dioxide into sugar.",
        [args.modelBColumn]: "Photosynthesis uses light energy to create glucose and oxygen.",
      },
    ];
  }

  if ((args.type === "classify" || args.type === "score") && args.evalColumn) {
    return [
      {
        prompt: "Summarize what artificial intelligence is.",
        [args.evalColumn]:
          "Artificial intelligence is software that performs tasks requiring reasoning or prediction.",
      },
      {
        prompt: "What causes rainbows?",
        [args.evalColumn]:
          "Rainbows form when water droplets refract, reflect, and disperse sunlight.",
      },
    ];
  }

  if (args.type === "classify") {
    return [
      { prompt: "The product arrived on time and works perfectly!" },
      { prompt: "Terrible experience. The item was broken." },
      { prompt: "It's okay, nothing special." },
    ];
  }
  if (args.type === "score") {
    return [
      { prompt: "Explain quantum computing in simple terms." },
      { prompt: "What causes rainbows?" },
      { prompt: "How do vaccines work?" },
    ];
  }
  return [
    { prompt: "Explain the theory of relativity." },
    { prompt: "What is the meaning of life?" },
    { prompt: "How does photosynthesis work?" },
  ];
}

async function maybeDownloadResults(args: ScriptArgs, result: any): Promise<void> {
  const fileId = getResultFileId(result);
  if (fileId) {
    console.log(`  Result file: ${fileId}`);
  }
  if (args.downloadResults && fileId) {
    await downloadResultFile(fileId, args.downloadResults);
  }
}

async function runClassify(args: ScriptArgs, dataset: DatasetRow[]): Promise<void> {
  console.log("\n=== Classify Evaluation ===");
  const fileId = await uploadDataset(dataset);

  const modelToEvaluate =
    args.evalColumn ??
    buildModelConfig({
      model: args.evalModel,
      modelSource: args.evalModelSource,
      systemTemplate: args.evalSystemTemplate,
      inputTemplate: args.inputTemplate,
      maxTokens: args.maxTokens,
      temperature: args.temperature,
      externalApiToken: args.evalExternalApiToken,
      externalBaseUrl: args.evalExternalBaseUrl,
    });

  if (typeof modelToEvaluate === "string") {
    console.log(`Using dataset column for candidate responses: ${modelToEvaluate}`);
  }

  const evaluation = await client.evals.create({
    type: "classify",
    parameters: {
      input_data_file_path: fileId,
      judge: buildJudgeConfig(args, DEFAULT_CLASSIFY_TEMPLATE),
      labels: ["positive", "negative", "neutral"],
      pass_labels: ["positive"],
      model_to_evaluate: modelToEvaluate,
    },
  });
  console.log(`Created evaluation: ${evaluation.workflow_id}`);

  const result = await pollEvaluation(evaluation.workflow_id!, args.pollInterval);
  if (result.results) {
    console.log(`  Label counts: ${JSON.stringify(result.results.label_counts ?? {})}`);
    console.log(`  Pass percentage: ${result.results.pass_percentage}`);
    await maybeDownloadResults(args, result);
  }
}

async function runScore(args: ScriptArgs, dataset: DatasetRow[]): Promise<void> {
  console.log("\n=== Score Evaluation ===");
  const fileId = await uploadDataset(dataset);

  const modelToEvaluate =
    args.evalColumn ??
    buildModelConfig({
      model: args.evalModel,
      modelSource: args.evalModelSource,
      systemTemplate: args.evalSystemTemplate,
      inputTemplate: args.inputTemplate,
      maxTokens: args.maxTokens,
      temperature: args.temperature,
      externalApiToken: args.evalExternalApiToken,
      externalBaseUrl: args.evalExternalBaseUrl,
    });

  if (typeof modelToEvaluate === "string") {
    console.log(`Using dataset column for candidate responses: ${modelToEvaluate}`);
  }

  const evaluation = await client.evals.create({
    type: "score",
    parameters: {
      input_data_file_path: fileId,
      judge: buildJudgeConfig(args, DEFAULT_SCORE_TEMPLATE),
      min_score: 1.0,
      max_score: 10.0,
      pass_threshold: 7.0,
      model_to_evaluate: modelToEvaluate,
    },
  });
  console.log(`Created evaluation: ${evaluation.workflow_id}`);

  const result = await pollEvaluation(evaluation.workflow_id!, args.pollInterval);
  if (result.results?.aggregated_scores) {
    const scores = result.results.aggregated_scores;
    console.log(`  Mean score: ${scores.mean_score}`);
    console.log(`  Std score: ${scores.std_score}`);
    console.log(`  Pass percentage: ${scores.pass_percentage}`);
    await maybeDownloadResults(args, result);
  }
}

async function runCompare(args: ScriptArgs, dataset: DatasetRow[]): Promise<void> {
  console.log("\n=== Compare Evaluation ===");
  const fileId = await uploadDataset(dataset);

  const modelA =
    args.modelAColumn ??
    buildModelConfig({
      model: args.modelA,
      modelSource: args.modelASource,
      systemTemplate: args.evalSystemTemplate,
      inputTemplate: args.inputTemplate,
      maxTokens: args.maxTokens,
      temperature: args.temperature,
      externalApiToken: args.modelAExternalApiToken,
      externalBaseUrl: args.modelAExternalBaseUrl,
    });
  const modelB =
    args.modelBColumn ??
    buildModelConfig({
      model: args.modelB,
      modelSource: args.modelBSource,
      systemTemplate: args.evalSystemTemplate,
      inputTemplate: args.inputTemplate,
      maxTokens: args.maxTokens,
      temperature: args.temperature,
      externalApiToken: args.modelBExternalApiToken,
      externalBaseUrl: args.modelBExternalBaseUrl,
    });

  if (typeof modelA === "string" && typeof modelB === "string") {
    console.log(`Using dataset columns for comparisons: ${modelA} vs ${modelB}`);
  }

  const evaluation = await client.evals.create({
    type: "compare",
    parameters: {
      input_data_file_path: fileId,
      judge: buildJudgeConfig(args, DEFAULT_COMPARE_TEMPLATE),
      model_a: modelA,
      model_b: modelB,
    },
  });
  console.log(`Created evaluation: ${evaluation.workflow_id}`);

  const result = await pollEvaluation(evaluation.workflow_id!, args.pollInterval);
  if (result.results) {
    console.log(`  A wins: ${result.results.A_wins}`);
    console.log(`  B wins: ${result.results.B_wins}`);
    console.log(`  Ties: ${result.results.Ties}`);
    await maybeDownloadResults(args, result);
  }
}

async function main(): Promise<void> {
  const args = parseScriptArgs();
  const dataset = loadDataset(args.dataset, sampleDatasetForArgs(args));

  if (args.type === "classify") {
    await runClassify(args, dataset);
  } else if (args.type === "score") {
    await runScore(args, dataset);
  } else {
    await runCompare(args, dataset);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
