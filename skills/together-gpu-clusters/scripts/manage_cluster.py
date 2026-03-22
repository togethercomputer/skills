#!/usr/bin/env python3
"""
Together AI GPU Clusters -- Create, Monitor, Scale, Delete (v2 SDK)

Full lifecycle: list regions, create cluster, wait for ready,
check status, scale, then delete.

Usage:
    python manage_cluster.py list-regions
    python manage_cluster.py create --name my-cluster --region us-central-8 --gpu-type H100_SXM --num-gpus 8 --driver-version CUDA_12_6_560
    python manage_cluster.py demo

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import argparse
import time

from together import Together

client = Together()


def list_regions():
    """List available regions with supported GPUs and drivers."""
    regions = client.beta.clusters.list_regions()
    for region in regions.regions:
        print(f"  {region.name}: GPUs={region.supported_instance_types}, Drivers={region.driver_versions}")
    return regions


def list_clusters() -> list:
    """List all GPU clusters."""
    response = client.beta.clusters.list()
    for cluster in response.clusters:
        print(f"  {cluster.cluster_id}: {cluster.cluster_name} ({cluster.status}, {cluster.num_gpus} GPUs, {cluster.gpu_type})")
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
    print(f"Created cluster: {cluster.cluster_id} (status: {cluster.status})")
    return cluster


def wait_for_ready(cluster_id: str, timeout: int = 1800, poll_interval: int = 30):
    """Poll until cluster reaches Ready state."""
    elapsed = 0
    while elapsed < timeout:
        cluster = client.beta.clusters.retrieve(cluster_id)
        print(f"  Status: {cluster.status} ({elapsed}s)")

        if cluster.status == "Ready":
            return cluster
        if cluster.status in ("Deleting",):
            raise RuntimeError(f"Cluster is being deleted: {cluster_id}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Cluster not ready after {timeout}s")


def scale_cluster(cluster_id: str, num_gpus: int):
    """Scale a cluster to a new GPU count."""
    cluster = client.beta.clusters.update(cluster_id, num_gpus=num_gpus)
    print(f"Scaled cluster {cluster_id} to {num_gpus} GPUs (status: {cluster.status})")
    return cluster


def delete_cluster(cluster_id: str) -> None:
    """Delete a GPU cluster."""
    client.beta.clusters.delete(cluster_id)
    print(f"Deleted cluster: {cluster_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI GPU cluster management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-regions", help="List available regions")
    subparsers.add_parser("list", help="List existing clusters")

    create_parser = subparsers.add_parser("create", help="Create a cluster")
    create_parser.add_argument("--name", required=True, help="Cluster name")
    create_parser.add_argument("--region", required=True, help="Region name")
    create_parser.add_argument("--gpu-type", required=True, help="GPU type")
    create_parser.add_argument("--num-gpus", required=True, type=int, help="GPU count")
    create_parser.add_argument("--driver-version", required=True, help="Driver version")
    create_parser.add_argument("--billing-type", default="ON_DEMAND", help="Billing type")
    create_parser.add_argument("--cluster-type", default="KUBERNETES", help="Cluster type")
    create_parser.add_argument("--volume-id", help="Optional shared storage volume id")

    wait_parser = subparsers.add_parser("wait", help="Wait for a cluster to become ready")
    wait_parser.add_argument("--cluster-id", required=True, help="Cluster id")
    wait_parser.add_argument("--timeout", type=int, default=1800, help="Maximum wait time in seconds")
    wait_parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between polls")

    scale_parser = subparsers.add_parser("scale", help="Scale an existing cluster")
    scale_parser.add_argument("--cluster-id", required=True, help="Cluster id")
    scale_parser.add_argument("--num-gpus", required=True, type=int, help="New GPU count")

    delete_parser = subparsers.add_parser("delete", help="Delete a cluster")
    delete_parser.add_argument("--cluster-id", required=True, help="Cluster id")

    demo_parser = subparsers.add_parser("demo", help="Run the full example flow")
    demo_parser.add_argument("--name", default="my-training-cluster", help="Cluster name")
    demo_parser.add_argument("--region", default="us-central-8", help="Region name")
    demo_parser.add_argument("--gpu-type", default="H100_SXM", help="GPU type")
    demo_parser.add_argument("--num-gpus", type=int, default=8, help="Initial GPU count")
    demo_parser.add_argument("--driver-version", default="CUDA_12_6_560", help="Driver version")
    demo_parser.add_argument("--billing-type", default="ON_DEMAND", help="Billing type")
    demo_parser.add_argument("--cluster-type", default="KUBERNETES", help="Cluster type")
    demo_parser.add_argument("--volume-id", help="Optional shared storage volume id")
    demo_parser.add_argument("--scale-to", type=int, default=16, help="GPU count to scale to after creation")
    demo_parser.add_argument("--timeout", type=int, default=1800, help="Maximum wait time in seconds")
    demo_parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between polls")
    demo_parser.add_argument("--delete", action="store_true", help="Delete the cluster at the end")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "list-regions":
        list_regions()
        return
    if args.command == "list":
        list_clusters()
        return
    if args.command == "create":
        create_cluster(
            name=args.name,
            region=args.region,
            gpu_type=args.gpu_type,
            num_gpus=args.num_gpus,
            driver_version=args.driver_version,
            billing_type=args.billing_type,
            cluster_type=args.cluster_type,
            volume_id=args.volume_id,
        )
        return
    if args.command == "wait":
        wait_for_ready(args.cluster_id, timeout=args.timeout, poll_interval=args.poll_interval)
        return
    if args.command == "scale":
        scale_cluster(args.cluster_id, args.num_gpus)
        return
    if args.command == "delete":
        delete_cluster(args.cluster_id)
        return

    print("Available regions:")
    list_regions()
    print("\nExisting clusters:")
    list_clusters()
    cluster = create_cluster(
        name=args.name,
        region=args.region,
        gpu_type=args.gpu_type,
        num_gpus=args.num_gpus,
        driver_version=args.driver_version,
        billing_type=args.billing_type,
        cluster_type=args.cluster_type,
        volume_id=args.volume_id,
    )
    print("\nWaiting for cluster to be ready...")
    cluster = wait_for_ready(cluster.cluster_id, timeout=args.timeout, poll_interval=args.poll_interval)
    print(f"Cluster ready: {cluster.cluster_name}")
    print(f"\nScaling to {args.scale_to} GPUs...")
    scale_cluster(cluster.cluster_id, args.scale_to)
    wait_for_ready(cluster.cluster_id, timeout=args.timeout, poll_interval=args.poll_interval)
    if args.delete:
        delete_cluster(cluster.cluster_id)


if __name__ == "__main__":
    main()
