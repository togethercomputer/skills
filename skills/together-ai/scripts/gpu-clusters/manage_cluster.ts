#!/usr/bin/env -S npx tsx
/**
 * Together AI GPU Clusters -- Create, Monitor, Scale, Delete
 *
 * Full lifecycle: list regions, create cluster, wait for ready,
 * check status, scale, then delete.
 *
 * Every cluster needs a shared volume, and the API rejects a create request without one. Pass
 * --shared-volume-name with --shared-volume-size-tib to create one with the cluster, or --volume-id
 * to attach an existing one. Deleting a cluster keeps its volume, which keeps billing until you
 * delete it.
 *
 * Usage:
 *   npx tsx manage_cluster.ts            # list regions and clusters only
 *   npx tsx manage_cluster.ts --create --shared-volume-name my-data --shared-volume-size-tib 1
 *                                        # create an 8x H100 cluster (billed hourly) and scale it to 16
 *   npx tsx manage_cluster.ts --create --volume-id <VOLUME_ID>
 *
 * Requires:
 *   npm install "together-ai@>=1"
 *   export TOGETHER_API_KEY=your_key
 */

import Together from "together-ai";
import type { ClusterCreateParams } from "together-ai/resources/clusters/clusters";

const client = new Together({
  apiKey: process.env.TOGETHER_API_KEY,
});

type GPUType = ClusterCreateParams["gpu_type"];
// Combined form such as "CUDA_12_6_560"; the API takes cuda_version and nvidia_driver_version.
type DriverVersion = string;
type BillingType = ClusterCreateParams["billing_type"];
type ClusterType = NonNullable<ClusterCreateParams["cluster_type"]>;
// The volume a new cluster uses: one created with the cluster, or an existing one.
type VolumeChoice =
  | { volumeId: string }
  | { sharedVolumeName: string; sharedVolumeSizeTib: number };

/** Read the volume flags, or throw. A create request without a volume is rejected by the API. */
function parseVolumeArgs(argv: string[]): VolumeChoice {
  const value = (flag: string): string | undefined => {
    const i = argv.indexOf(flag);
    if (i < 0) return undefined;
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) throw new Error(`${flag} needs a value.`);
    return next;
  };
  const volumeId = value("--volume-id");
  const name = value("--shared-volume-name");
  const size = value("--shared-volume-size-tib");

  if (volumeId && (name || size)) {
    throw new Error("Pass either --volume-id or --shared-volume-name with --shared-volume-size-tib, not both.");
  }
  if (volumeId) return { volumeId };
  if (!name && !size) {
    throw new Error(
      "A cluster needs a shared volume. Pass --shared-volume-name with --shared-volume-size-tib " +
        "to create one with the cluster, or --volume-id to attach an existing one.",
    );
  }
  if (!name || !size) {
    throw new Error("--shared-volume-name and --shared-volume-size-tib must be passed together.");
  }
  const sizeTib = Number(size);
  if (!Number.isInteger(sizeTib) || sizeTib < 1) {
    throw new Error("--shared-volume-size-tib must be a whole number of TiB, 1 or more.");
  }
  return { sharedVolumeName: name, sharedVolumeSizeTib: sizeTib };
}

async function listRegions(): Promise<void> {
  console.log("=== Available Regions ===");
  const regions = await client.clusters.listRegions();
  for (const r of regions.regions) {
    console.log(`  ${r.name}: GPUs=${JSON.stringify(r.supported_instance_types)}`);
  }
}

async function listClusters(): Promise<void> {
  console.log("\n=== Existing Clusters ===");
  const response = await client.clusters.list();
  for (const c of response.clusters) {
    console.log(`  ${c.cluster_id}: ${c.cluster_name} (${c.status}, ${c.num_gpus} GPUs)`);
  }
}

function parseDriverVersion(driverVersion: string): { cudaVersion: string; nvidiaDriver: string } {
  const parts = driverVersion.replace("CUDA_", "").split("_");
  return { cudaVersion: `${parts[0]}.${parts[1]}`, nvidiaDriver: parts[2] };
}

async function createCluster(
  name: string,
  region: string,
  gpuType: GPUType,
  numGpus: number,
  driverVersion: DriverVersion,
  volume: VolumeChoice,
  billingType: BillingType = "ON_DEMAND",
  clusterType: ClusterType = "KUBERNETES",
): Promise<any> {
  const { cudaVersion, nvidiaDriver } = parseDriverVersion(driverVersion);
  // Prefer a volume created with the cluster: one created separately can land in another
  // datacenter of the region, and attaching it then fails.
  const volumeParams =
    "volumeId" in volume
      ? { volume_id: volume.volumeId }
      : {
          shared_volume: {
            volume_name: volume.sharedVolumeName,
            size_tib: volume.sharedVolumeSizeTib,
            region,
          },
        };
  const cluster = await client.clusters.create({
    cluster_name: name,
    region,
    gpu_type: gpuType,
    num_gpus: numGpus,
    cuda_version: cudaVersion,
    nvidia_driver_version: nvidiaDriver,
    billing_type: billingType,
    cluster_type: clusterType,
    ...volumeParams,
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
    const cluster = await client.clusters.retrieve(clusterId);
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
  const cluster = await client.clusters.update(clusterId, {
    num_gpus: numGpus,
  });
  console.log(`Scaled to ${numGpus} GPUs (status: ${cluster.status})`);
  return cluster;
}

async function deleteCluster(clusterId: string): Promise<void> {
  await client.clusters.delete(clusterId);
  console.log(`Deleted cluster: ${clusterId}`);
}

async function main(): Promise<void> {
  const CLUSTER_NAME = "my-training-cluster";
  const REGION = "us-central-8";
  const GPU_TYPE = "H100_SXM";
  const NUM_GPUS = 8;
  const DRIVER = "CUDA_12_6_560";

  // Check the volume flags before any API call: a create request without a volume is rejected.
  const create = process.argv.includes("--create");
  let volume: VolumeChoice | undefined;
  if (create) {
    try {
      volume = parseVolumeArgs(process.argv.slice(2));
    } catch (error) {
      console.error(`Error: ${(error as Error).message}`);
      process.exit(1);
    }
  }

  // 1. List available regions
  await listRegions();

  // 2. List existing clusters
  await listClusters();

  // Creating a cluster starts hourly GPU billing, so only continue when asked.
  if (!create || !volume) {
    console.log(
      "\nListed only. Pass --create with --shared-volume-name and --shared-volume-size-tib " +
        "(or --volume-id) to create, scale, and keep a cluster (billed hourly).",
    );
    return;
  }

  // 3. Create a cluster
  const cluster = await createCluster(
    CLUSTER_NAME, REGION, GPU_TYPE, NUM_GPUS, DRIVER, volume,
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
