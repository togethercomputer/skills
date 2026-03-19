#!/usr/bin/env -S npx tsx
/**
 * Together AI Dedicated Containers — Queue Client (TypeScript SDK)
 *
 * Submit jobs, poll for results, and manage queue operations.
 *
 * Usage:
 *     npx tsx queue_client.ts
 *
 * Requires:
 *     npm install together-ai
 *     export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together();

// Change this to your deployment name
const DEPLOYMENT = "hello-world";

async function submitAndPoll(
  payload: Record<string, any>,
  priority: number = 1
): Promise<any> {
  const job = await client.beta.jig.queue.submit({
    model: DEPLOYMENT,
    payload,
    priority,
  });
  const requestId = job.requestId ?? job.request_id;
  console.log(`Submitted job: ${requestId}`);

  while (true) {
    const status: any = await client.beta.jig.queue.retrieve({
      requestId,
      model: DEPLOYMENT,
    });

    let line = `  Status: ${status.status}`;
    if (status.info?.progress !== undefined) {
      line += ` | Progress: ${(status.info.progress * 100).toFixed(0)}%`;
    }
    console.log(line);

    if (status.status === "done") {
      console.log("  Outputs:", JSON.stringify(status.outputs));
      return { status: "done", outputs: status.outputs };
    } else if (status.status === "failed") {
      console.log("  Error:", status.error);
      return { status: "failed", error: status.error };
    } else if (status.status === "canceled") {
      console.log("  Job was canceled");
      return { status: "canceled" };
    }

    await new Promise((r) => setTimeout(r, 2000));
  }
}

async function submitMultiple(
  payloads: Record<string, any>[]
): Promise<string[]> {
  const requestIds: string[] = [];
  for (const payload of payloads) {
    const job = await client.beta.jig.queue.submit({
      model: DEPLOYMENT,
      payload,
    });
    const requestId = job.requestId ?? (job as any).request_id;
    requestIds.push(requestId);
    console.log(`Submitted: ${requestId}`);
  }
  return requestIds;
}

async function checkStatus(requestId: string): Promise<any> {
  const status: any = await client.beta.jig.queue.retrieve({
    requestId,
    model: DEPLOYMENT,
  });
  console.log(`Job ${requestId}: ${status.status}`);
  if (status.status === "done") {
    console.log("  Outputs:", JSON.stringify(status.outputs));
  }
  return { status: status.status, outputs: status.outputs };
}

async function main() {
  // --- Example 1: Submit and wait for result ---
  console.log("=== Submit and poll ===");
  await submitAndPoll({ name: "Together" });
  console.log();

  // --- Example 2: Submit with priority ---
  console.log("=== Priority job ===");
  await submitAndPoll({ name: "Priority User" }, 10);
  console.log();

  // --- Example 3: Submit batch ---
  console.log("=== Batch submit ===");
  const ids = await submitMultiple([
    { name: "Alice" },
    { name: "Bob" },
    { name: "Charlie" },
  ]);
  console.log(`Submitted ${ids.length} jobs`);

  for (const rid of ids) {
    await new Promise((r) => setTimeout(r, 1000));
    await checkStatus(rid);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
