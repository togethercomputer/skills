#!/usr/bin/env -S npx tsx
/**
 * Together AI GPU Clusters -- Create, Monitor, Scale, Delete
 *
 * Full lifecycle: list regions, create cluster, wait for ready,
 * check status, scale, then delete.
 *
 * Usage:
 *   npx tsx manage_cluster.ts
 *
 * Requires:
 *   npm install together-ai
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

async function listRegions(): Promise<void> {
  console.log("=== Available Regions ===");
  const regions = await client.beta.clusters.list_regions();
  for (const r of regions.regions) {
    console.log(`  ${r.name}: GPUs=${JSON.stringify(r.supported_instance_types)}`);
  }
}

async function listClusters(): Promise<void> {
  console.log("\n=== Existing Clusters ===");
  const response = await client.beta.clusters.list();
  for (const c of response.clusters) {
    console.log(`  ${c.cluster_id}: ${c.cluster_name} (${c.status}, ${c.num_gpus} GPUs)`);
  }
}

async function createCluster(
  name: string,
  region: string,
  gpuType: string,
  numGpus: number,
  driverVersion: string,
  billingType: string = "ON_DEMAND",
  clusterType: string = "KUBERNETES",
): Promise<any> {
  const cluster = await client.beta.clusters.create({
    cluster_name: name,
    region,
    gpu_type: gpuType,
    num_gpus: numGpus,
    driver_version: driverVersion,
    billing_type: billingType,
    cluster_type: clusterType,
  });
  console.log(`Created cluster: ${cluster.cluster_id}  (status: ${cluster.status})`);
  return cluster;
}

async function waitForReady(
  clusterId: string,
  timeoutMs: number = 1_800_000,
  pollMs: number = 30_000,
): Promise<any> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const cluster = await client.beta.clusters.retrieve(clusterId);
    const elapsed = Math.round((Date.now() - start) / 1000);
    console.log(`  Status: ${cluster.status}  (${elapsed}s)`);

    if (cluster.status === "Ready") return cluster;
    if (cluster.status === "Deleting") {
      throw new Error(`Cluster is being deleted: ${clusterId}`);
    }

    await new Promise((r) => setTimeout(r, pollMs));
  }
  throw new Error(`Cluster not ready after ${timeoutMs / 1000}s`);
}

async function scaleCluster(clusterId: string, numGpus: number): Promise<any> {
  const cluster = await client.beta.clusters.update({
    cluster_id: clusterId,
    num_gpus: numGpus,
  });
  console.log(`Scaled to ${numGpus} GPUs (status: ${cluster.status})`);
  return cluster;
}

async function deleteCluster(clusterId: string): Promise<void> {
  await client.beta.clusters.delete(clusterId);
  console.log(`Deleted cluster: ${clusterId}`);
}

async function main(): Promise<void> {
  const CLUSTER_NAME = "my-training-cluster";
  const REGION = "us-central-8";
  const GPU_TYPE = "H100_SXM";
  const NUM_GPUS = 8;
  const DRIVER = "CUDA_12_6_560";

  // 1. List available regions
  await listRegions();

  // 2. List existing clusters
  await listClusters();

  // 3. Create a cluster
  const cluster = await createCluster(
    CLUSTER_NAME, REGION, GPU_TYPE, NUM_GPUS, DRIVER,
  );

  // 4. Wait for cluster to be ready
  console.log("\nWaiting for cluster to be ready...");
  const ready = await waitForReady(cluster.cluster_id);
  console.log(`Cluster ready: ${ready.cluster_name}`);

  // 5. Scale up to 16 GPUs
  console.log("\nScaling to 16 GPUs...");
  await scaleCluster(cluster.cluster_id, 16);

  // 6. Wait for scaling to complete
  await waitForReady(cluster.cluster_id);

  // 7. Delete when done (uncomment to delete)
  // await deleteCluster(cluster.cluster_id);
}

main();
