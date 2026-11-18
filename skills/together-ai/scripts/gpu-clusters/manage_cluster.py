#!/usr/bin/env python3
"""
Together AI GPU Clusters -- Create, Monitor, Scale, Delete (SDK 3.x)

Full lifecycle: list regions, create cluster, wait for ready,
check status, scale, then delete.

Every cluster needs a shared volume, and the API rejects a create request without one. Pass
--shared-volume-name with --shared-volume-size-tib to create one with the cluster, or --volume-id
to attach an existing one. Deleting a cluster keeps its volume, which keeps billing until you
delete it (see manage_storage.py).

Usage:
    python manage_cluster.py list-regions
    python manage_cluster.py create --name my-cluster --region us-central-8 --gpu-type H100_SXM --num-gpus 8 --driver-version CUDA_12_6_560 --shared-volume-name my-data --shared-volume-size-tib 1
    python manage_cluster.py demo --shared-volume-name my-data --shared-volume-size-tib 1

Requires:
    uv pip install "together>=3"
    export TOGETHER_API_KEY=your_key
"""

import argparse
import time

from together import Together

client = Together()


def list_regions():
    """List available regions with supported GPUs and drivers."""
    regions = client.clusters.list_regions()
    for region in regions.regions:
        print(f"  {region.name}: GPUs={region.supported_instance_types}, Drivers={region.driver_versions}")
    return regions


def list_clusters() -> list:
    """List all GPU clusters."""
    response = client.clusters.list()
    for cluster in response.clusters:
        print(f"  {cluster.cluster_id}: {cluster.cluster_name} ({cluster.status}, {cluster.num_gpus} GPUs, {cluster.gpu_type})")
    return response.clusters


def parse_driver_version(driver_version: str) -> tuple[str, str]:
    """Extract cuda_version and nvidia_driver_version from a combined string.

    Example: "CUDA_12_6_560" -> ("12.6", "560")
    """
    parts = driver_version.removeprefix("CUDA_").split("_")
    cuda_version = f"{parts[0]}.{parts[1]}"
    nvidia_driver = parts[2]
    return cuda_version, nvidia_driver


def volume_kwargs(
    region: str,
    volume_id: str | None = None,
    shared_volume_name: str | None = None,
    shared_volume_size_tib: int | None = None,
) -> dict:
    """Return the volume part of a create request, or raise ValueError.

    Every cluster needs a shared volume: one created with the cluster (``shared_volume``) or an
    existing one (``volume_id``). The API rejects a create request that has neither.
    """
    inline = shared_volume_name is not None or shared_volume_size_tib is not None
    if volume_id and inline:
        raise ValueError(
            "Pass either --volume-id or --shared-volume-name with --shared-volume-size-tib, not both."
        )
    if volume_id:
        return {"volume_id": volume_id}
    if not inline:
        raise ValueError(
            "A cluster needs a shared volume. Pass --shared-volume-name with --shared-volume-size-tib "
            "to create one with the cluster, or --volume-id to attach an existing one."
        )
    if not shared_volume_name or shared_volume_size_tib is None:
        raise ValueError("--shared-volume-name and --shared-volume-size-tib must be passed together.")
    if shared_volume_size_tib < 1:
        raise ValueError("--shared-volume-size-tib must be a whole number of TiB, 1 or more.")
    return {
        "shared_volume": {
            "volume_name": shared_volume_name,
            "size_tib": shared_volume_size_tib,
            "region": region,
        }
    }


def create_cluster(
    name: str,
    region: str,
    gpu_type: str,
    num_gpus: int,
    driver_version: str,
    billing_type: str = "ON_DEMAND",
    cluster_type: str = "KUBERNETES",
    volume_id: str | None = None,
    shared_volume_name: str | None = None,
    shared_volume_size_tib: int | None = None,
):
    """Create a new GPU cluster.

    A shared volume is required. Prefer ``shared_volume_name`` + ``shared_volume_size_tib``
    (inline creation) over ``volume_id`` to avoid datacenter-mismatch errors.
    """
    volume = volume_kwargs(region, volume_id, shared_volume_name, shared_volume_size_tib)
    cuda_ver, nvidia_ver = parse_driver_version(driver_version)
    kwargs: dict = {
        "cluster_name": name,
        "region": region,
        "gpu_type": gpu_type,
        "num_gpus": num_gpus,
        # The API takes the CUDA and driver versions as two fields; there is no driver_version.
        "cuda_version": cuda_ver,
        "nvidia_driver_version": nvidia_ver,
        "billing_type": billing_type,
        "cluster_type": cluster_type,
        **volume,
    }

    cluster = client.clusters.create(**kwargs)
    print(f"Created cluster: {cluster.cluster_id} (status: {cluster.status})")
    return cluster


def wait_for_ready(cluster_id: str, timeout: int = 1800, poll_interval: int = 30):
    """Poll until cluster reaches Ready state."""
    elapsed = 0
    while elapsed < timeout:
        cluster = client.clusters.retrieve(cluster_id)
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
    cluster = client.clusters.update(cluster_id, num_gpus=num_gpus)
    print(f"Scaled cluster {cluster_id} to {num_gpus} GPUs (status: {cluster.status})")
    return cluster


def delete_cluster(cluster_id: str) -> None:
    """Delete a GPU cluster."""
    client.clusters.delete(cluster_id)
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
    create_parser.add_argument("--volume-id", help="Existing volume id to attach (a volume is required; prefer --shared-volume-name)")
    create_parser.add_argument("--shared-volume-name", help="Name of a shared volume to create with the cluster")
    create_parser.add_argument("--shared-volume-size-tib", type=int, help="Size of that volume in whole TiB (1 or more)")

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
    demo_parser.add_argument("--volume-id", help="Existing volume id to attach (a volume is required; prefer --shared-volume-name)")
    demo_parser.add_argument("--shared-volume-name", help="Name of a shared volume to create with the cluster")
    demo_parser.add_argument("--shared-volume-size-tib", type=int, help="Size of that volume in whole TiB (1 or more)")
    demo_parser.add_argument("--scale-to", type=int, default=16, help="GPU count to scale to after creation")
    demo_parser.add_argument("--timeout", type=int, default=1800, help="Maximum wait time in seconds")
    demo_parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between polls")
    demo_parser.add_argument("--delete", action="store_true", help="Delete the cluster at the end")
    args = parser.parse_args()
    if args.command in ("create", "demo"):
        # Fail before any API call: a create request without a volume is rejected.
        try:
            volume_kwargs(args.region, args.volume_id, args.shared_volume_name, args.shared_volume_size_tib)
        except ValueError as error:
            parser.error(str(error))
    return args


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
            shared_volume_name=args.shared_volume_name,
            shared_volume_size_tib=args.shared_volume_size_tib,
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
        shared_volume_name=args.shared_volume_name,
        shared_volume_size_tib=args.shared_volume_size_tib,
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
