#!/usr/bin/env python3
"""
Together AI GPU Clusters -- Shared Storage Management (v2 SDK)

Create, list, resize, and delete shared storage volumes for GPU clusters.

Usage:
    python manage_storage.py list
    python manage_storage.py create --name my-training-data --size-tib 2 --region us-central-8
    python manage_storage.py demo

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

import argparse

from together import Together

client = Together()


def create_volume(name: str, size_tib: int, region: str):
    """Create a new shared storage volume."""
    volume = client.beta.clusters.storage.create(
        volume_name=name,
        size_tib=size_tib,
        region=region,
    )
    print(f"Created volume: {volume.volume_id} ({volume.volume_name}, {volume.size_tib} TiB, {volume.status})")
    return volume


def list_volumes() -> list:
    """List all shared storage volumes."""
    response = client.beta.clusters.storage.list()
    for volume in response.volumes:
        print(f"  {volume.volume_id}: {volume.volume_name} ({volume.size_tib} TiB, {volume.status})")
    return response.volumes


def retrieve_volume(volume_id: str):
    """Get details for a specific volume."""
    volume = client.beta.clusters.storage.retrieve(volume_id)
    print(f"Volume: {volume.volume_name}")
    print(f"  ID: {volume.volume_id}")
    print(f"  Size: {volume.size_tib} TiB")
    print(f"  Status: {volume.status}")
    return volume


def resize_volume(volume_id: str, new_size_tib: int):
    """Resize a shared storage volume."""
    volume = client.beta.clusters.storage.update(
        volume_id=volume_id,
        size_tib=new_size_tib,
    )
    print(f"Resized volume {volume_id} to {volume.size_tib} TiB")
    return volume


def delete_volume(volume_id: str) -> None:
    """Delete a shared storage volume."""
    client.beta.clusters.storage.delete(volume_id)
    print(f"Deleted volume: {volume_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Together AI shared storage management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List volumes")

    create_parser = subparsers.add_parser("create", help="Create a volume")
    create_parser.add_argument("--name", required=True, help="Volume name")
    create_parser.add_argument("--size-tib", required=True, type=int, help="Volume size in TiB")
    create_parser.add_argument("--region", required=True, help="Region name")

    retrieve_parser = subparsers.add_parser("get", help="Retrieve a volume")
    retrieve_parser.add_argument("--volume-id", required=True, help="Volume id")

    resize_parser = subparsers.add_parser("resize", help="Resize a volume")
    resize_parser.add_argument("--volume-id", required=True, help="Volume id")
    resize_parser.add_argument("--size-tib", required=True, type=int, help="New size in TiB")

    delete_parser = subparsers.add_parser("delete", help="Delete a volume")
    delete_parser.add_argument("--volume-id", required=True, help="Volume id")

    demo_parser = subparsers.add_parser("demo", help="Run the full example flow")
    demo_parser.add_argument("--name", default="my-training-data", help="Volume name")
    demo_parser.add_argument("--region", default="us-central-8", help="Region name")
    demo_parser.add_argument("--size-tib", type=int, default=2, help="Initial size in TiB")
    demo_parser.add_argument("--resize-to", type=int, default=5, help="New size in TiB")
    demo_parser.add_argument("--delete", action="store_true", help="Delete the volume at the end")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "list":
        list_volumes()
        return
    if args.command == "create":
        create_volume(args.name, args.size_tib, args.region)
        return
    if args.command == "get":
        retrieve_volume(args.volume_id)
        return
    if args.command == "resize":
        resize_volume(args.volume_id, args.size_tib)
        return
    if args.command == "delete":
        delete_volume(args.volume_id)
        return

    volume = create_volume(args.name, args.size_tib, args.region)
    print("\nAll volumes:")
    list_volumes()
    print("\nVolume details:")
    retrieve_volume(volume.volume_id)
    print(f"\nResizing to {args.resize_to} TiB...")
    resize_volume(volume.volume_id, args.resize_to)
    if args.delete:
        delete_volume(volume.volume_id)


if __name__ == "__main__":
    main()
