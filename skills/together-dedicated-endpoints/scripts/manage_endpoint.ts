#!/usr/bin/env -S npx tsx
/**
 * Together AI Dedicated Endpoints -- Create, Monitor, Use, Stop
 *
 * Full lifecycle: list hardware, create endpoint, wait for ready,
 * run inference, then stop/delete.
 *
 * Usage:
 *   npx tsx manage_endpoint.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function listHardware(model?: string): Promise<void> {
  console.log("=== Available Hardware ===");
  const response = await client.endpoints.list_hardware(
    model ? { model } : undefined,
  );
  for (const hw of response.data) {
    console.log(`  ${hw.id}`);
  }
}

async function listEndpoints(): Promise<void> {
  console.log("\n=== Your Endpoints ===");
  const response = await client.endpoints.list();
  for (const ep of response.data) {
    console.log(`  ${ep.id}: ${ep.model} (${ep.state})`);
  }
}

async function createEndpoint(
  model: string,
  hardware: string,
  minReplicas: number = 1,
  maxReplicas: number = 1,
  displayName?: string,
): Promise<any> {
  const endpoint = await client.endpoints.create({
    model,
    hardware,
    autoscaling: {
      min_replicas: minReplicas,
      max_replicas: maxReplicas,
    },
    ...(displayName && { display_name: displayName }),
  });
  console.log(`Created endpoint: ${endpoint.id}  (state: ${endpoint.state})`);
  console.log(`  Endpoint name (for inference): ${endpoint.name}`);
  return endpoint;
}

async function waitForReady(
  endpointId: string,
  timeoutMs: number = 600_000,
  pollMs: number = 10_000,
): Promise<any> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const endpoint = await client.endpoints.retrieve(endpointId);
    const elapsed = Math.round((Date.now() - start) / 1000);
    console.log(`  State: ${endpoint.state}  (${elapsed}s)`);

    if (endpoint.state === "STARTED") return endpoint;
    if (endpoint.state === "ERROR") {
      throw new Error(`Endpoint entered ERROR state: ${endpointId}`);
    }

    await new Promise((r) => setTimeout(r, pollMs));
  }
  throw new Error(`Endpoint not ready after ${timeoutMs / 1000}s`);
}

async function runInference(endpointName: string, prompt: string): Promise<string> {
  const response = await client.chat.completions.create({
    model: endpointName,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 200,
  });
  const reply = response.choices[0].message.content ?? "";
  console.log(`Response: ${reply}`);
  return reply;
}

async function stopEndpoint(endpointId: string): Promise<void> {
  const endpoint = await client.endpoints.update(endpointId, { state: "STOPPED" });
  console.log(`Stopped endpoint: ${endpoint.id}  (state: ${endpoint.state})`);
}

async function deleteEndpoint(endpointId: string): Promise<void> {
  await client.endpoints.delete(endpointId);
  console.log(`Deleted endpoint: ${endpointId}`);
}

async function main(): Promise<void> {
  const MODEL = "Qwen/Qwen3.5-9B-FP8";
  const HARDWARE = "1x_nvidia_h100_80gb_sxm";

  // 1. List available hardware
  await listHardware(MODEL);

  // 2. List existing endpoints
  await listEndpoints();

  // 3. Create endpoint
  const ep = await createEndpoint(MODEL, HARDWARE, 1, 1, "My Qwen Endpoint");

  // 4. Wait until ready
  const ready = await waitForReady(ep.id);

  // 5. Run inference
  await runInference(ready.name, "What is the capital of France?");

  // 6. Stop endpoint
  await stopEndpoint(ep.id);

  // 7. Delete endpoint (uncomment to permanently remove)
  // await deleteEndpoint(ep.id);
}

main();
