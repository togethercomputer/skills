#!/usr/bin/env python3
"""
Together AI GPU Clusters -- Shared Storage Management (v2 SDK)

Create, list, resize, and delete shared storage volumes for GPU clusters.

Usage:
    python manage_storage.py

Requires:
    pip install together
    export TOGETHER_API_KEY=your_key
"""

from together import Together

client = Together()


def create_volume(name: str, size_tib: int, region: str):
    """Create a new shared storage volume."""
    volume = client.beta.clusters.storage.create(
        volume_name=name,
        size_tib=size_tib,
        region=region,
    )
    print(f"Created volume: {volume.volume_id}  "
          f"({volume.volume_name}, {volume.size_tib} TiB, {volume.status})")
    return volume


def list_volumes():
    """List all shared storage volumes."""
    response = client.beta.clusters.storage.list()
    for v in response.volumes:
        print(f"  {v.volume_id}: {v.volume_name} "
              f"({v.size_tib} TiB, {v.status})")
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
    """Resize a shared storage volume (can only increase)."""
    volume = client.beta.clusters.storage.update(
        volume_id=volume_id,
        size_tib=new_size_tib,
    )
    print(f"Resized volume {volume_id} to {volume.size_tib} TiB")
    return volume


def delete_volume(volume_id: str):
    """Delete a shared storage volume. Must not be attached to any cluster."""
    client.beta.clusters.storage.delete(volume_id)
    print(f"Deleted volume: {volume_id}")


if __name__ == "__main__":
    VOLUME_NAME = "my-training-data"
    REGION = "us-central-8"
    SIZE_TIB = 2

    # 1. Create a volume
    vol = create_volume(VOLUME_NAME, SIZE_TIB, REGION)

    # 2. List all volumes
    print("\nAll volumes:")
    list_volumes()

    # 3. Get volume details
    print(f"\nVolume details:")
    retrieve_volume(vol.volume_id)

    # 4. Resize the volume
    print(f"\nResizing to 5 TiB...")
    resize_volume(vol.volume_id, 5)

    # 5. Delete the volume (uncomment to delete)
    # delete_volume(vol.volume_id)
