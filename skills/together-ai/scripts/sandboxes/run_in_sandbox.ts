#!/usr/bin/env -S npx tsx
/**
 * Together AI Code Sandbox — Run Code in an Isolated Sandbox (together-sandbox SDK)
 *
 * Reuse or build a snapshot, create a sandbox with a TTL backstop, write input
 * files and a script into it, run the script, read its result file back, and
 * terminate. This replaces the retired Code Interpreter (client.codeInterpreter).
 *
 * Usage:
 *     npx tsx run_in_sandbox.ts
 *     npx tsx run_in_sandbox.ts my-python@v1 python:3.12-slim
 *
 * Requires:
 *     npm install together-sandbox   # Node.js 18+; must be enabled for your organization
 *     export TOGETHER_API_KEY=your_key
 *     # together-sandbox reads TOGETHER_BASE_URL as its own API host: unset it if
 *     # it is set for the together-ai SDK.
 */

import { HttpError, TogetherSandbox } from "together-sandbox";

const SNAPSHOT_ALIAS = process.argv[2] ?? "skills-python@v1";
const IMAGE = process.argv[3] ?? "python:3.12-slim";
const TTL_SECONDS = 600;

const SALES_CSV = "month,revenue\nJan,100\nFeb,150\nMar,130\n";

// Runs inside the sandbox. Standard library only, so a stock Python image works.
const ANALYSIS_SCRIPT = `import csv, json, statistics

with open("/tmp/sales.csv") as f:
    rows = list(csv.DictReader(f))
revenue = [float(row["revenue"]) for row in rows]
summary = {"months": len(rows), "total": sum(revenue), "mean": statistics.mean(revenue)}
with open("/tmp/summary.json", "w") as f:
    json.dump(summary, f)
print(f"Analyzed {len(rows)} months")
`;

const sdk = new TogetherSandbox({ apiKey: process.env.TOGETHER_API_KEY! });

async function ensureSnapshot(alias: string, image: string): Promise<void> {
  try {
    const snapshot = await sdk.snapshots.getByAlias(alias);
    console.log(`Reusing snapshot ${snapshot.id} (${alias})`);
    return;
  } catch (e) {
    if (!(e instanceof HttpError && e.status === 404)) throw e;
  }

  // Not idempotent: a blind retry can register a duplicate snapshot.
  console.log(`Building snapshot ${alias} from ${image}...`);
  const result = await sdk.snapshots.create({
    image,
    alias,
    onProgress: (event) => console.log(`  [${event.step}] ${event.output}`),
  });
  console.log(`Created snapshot ${result.snapshotId}`);
}

async function main() {
  await ensureSnapshot(SNAPSHOT_ALIAS, IMAGE);

  const sandbox = await sdk.sandboxes.create({
    snapshotAlias: SNAPSHOT_ALIAS,
    ttl: TTL_SECONDS,
  });
  console.log(
    `Sandbox ${sandbox.id} is running (auto-terminates after ${TTL_SECONDS}s)`,
  );

  try {
    await sandbox.files.create("/tmp/sales.csv", SALES_CSV);
    await sandbox.files.create("/tmp/analyze.py", ANALYSIS_SCRIPT);

    const result = await sandbox.execs.exec("python3", ["/tmp/analyze.py"]);
    console.log(`exitCode=${result.exitCode}`);
    console.log(result.output);
    if (result.exitCode !== 0) {
      throw new Error("Sandbox script failed; see output above");
    }

    // Files persist across execs in one sandbox; Python variables do not.
    const summary = JSON.parse(await sandbox.files.read("/tmp/summary.json"));
    console.log("Summary:", summary);
  } finally {
    await sandbox.terminate();
    console.log(`Terminated sandbox ${sandbox.id}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
