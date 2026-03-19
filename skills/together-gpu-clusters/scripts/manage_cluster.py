#!/usr/bin/env python3
"""
Together AI GPU Clusters -- Create, Monitor, Scale, Delete (v2 SDK)

Full lifecycle: list regions, create cluster, wait for ready,
check status, scale, then delete.

Usage:
    python manage_cluster.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import time
from together import Together

client = Together()


def list_regions():
    """List available regions with supported GPUs and drivers."""
    regions = client.beta.clusters.list_regions()
    for r in regions.regions:
        print(f"  {r.name}: GPUs={r.supported_instance_types}, "
              f"Drivers={r.driver_versions}")
    return regions


def list_clusters():
    """List all GPU clusters."""
    response = client.beta.clusters.list()
    for c in response.clusters:
        print(f"  {c.cluster_id}: {c.cluster_name} "
              f"({c.status}, {c.num_gpus} GPUs, {c.gpu_type})")
    return response.clusters


def create_cluster(
    name: str,
    region: str,
    gpu_type: str,
    num_gpus: int,
    driver_version: str,
    billing_type: str = "ON_DEMAND",
    cluster_type: str = "KUBERNETES",
    volume_id: str | None = None,
):
    """Create a new GPU cluster."""
    kwargs: dict = {
        "cluster_name": name,
        "region": region,
        "gpu_type": gpu_type,
        "num_gpus": num_gpus,
        "driver_version": driver_version,
        "billing_type": billing_type,
        "cluster_type": cluster_type,
    }
    if volume_id:
        kwargs["volume_id"] = volume_id

    cluster = client.beta.clusters.create(**kwargs)
    print(f"Created cluster: {cluster.cluster_id}  (status: {cluster.status})")
    return cluster


def wait_for_ready(cluster_id: str, timeout: int = 1800, poll_interval: int = 30):
    """Poll until cluster reaches Ready state."""
    elapsed = 0
    while elapsed < timeout:
        cluster = client.beta.clusters.retrieve(cluster_id)
        print(f"  Status: {cluster.status}  ({elapsed}s)")

        if cluster.status == "Ready":
            return cluster
        if cluster.status in ("Deleting",):
            raise RuntimeError(f"Cluster is being deleted: {cluster_id}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Cluster not ready after {timeout}s")


def scale_cluster(cluster_id: str, num_gpus: int):
    """Scale a cluster to a new GPU count (must be multiple of 8)."""
    cluster = client.beta.clusters.update(cluster_id, num_gpus=num_gpus)
    print(f"Scaled cluster {cluster_id} to {num_gpus} GPUs (status: {cluster.status})")
    return cluster


def delete_cluster(cluster_id: str):
    """Delete a GPU cluster."""
    client.beta.clusters.delete(cluster_id)
    print(f"Deleted cluster: {cluster_id}")


if __name__ == "__main__":
    CLUSTER_NAME = "my-training-cluster"
    REGION = "us-central-8"
    GPU_TYPE = "H100_SXM"
    NUM_GPUS = 8
    DRIVER = "CUDA_12_6_560"

    # 1. List available regions
    print("Available regions:")
    list_regions()

    # 2. List existing clusters
    print("\nExisting clusters:")
    list_clusters()

    # 3. Create a cluster
    cluster = create_cluster(
        name=CLUSTER_NAME,
        region=REGION,
        gpu_type=GPU_TYPE,
        num_gpus=NUM_GPUS,
        driver_version=DRIVER,
    )

    # 4. Wait for cluster to be ready
    print("\nWaiting for cluster to be ready...")
    cluster = wait_for_ready(cluster.cluster_id)
    print(f"Cluster ready: {cluster.cluster_name}")

    # 5. Scale up to 16 GPUs
    print("\nScaling to 16 GPUs...")
    scale_cluster(cluster.cluster_id, 16)

    # 6. Wait for scaling to complete
    cluster = wait_for_ready(cluster.cluster_id)

    # 7. Delete when done (uncomment to delete)
    # delete_cluster(cluster.cluster_id)
