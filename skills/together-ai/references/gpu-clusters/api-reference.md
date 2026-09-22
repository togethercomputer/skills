# GPU Clusters API Reference
## Contents

- [Cluster Endpoints](#cluster-endpoints)
- [Storage Endpoints](#storage-endpoints)
- [Create Cluster](#create-cluster)
- [List Clusters](#list-clusters)
- [Get Cluster](#get-cluster)
- [Update / Scale Cluster](#update-scale-cluster)
- [Delete Cluster](#delete-cluster)
- [List Regions](#list-regions)
- [Create Shared Volume](#create-shared-volume)
- [List Shared Volumes](#list-shared-volumes)
- [Get Shared Volume](#get-shared-volume)
- [Update (Resize) Shared Volume](#update-shared-volume)
- [Delete Shared Volume](#delete-shared-volume)
- [Instance Types](#instance-types)
- [Driver Versions](#driver-versions)
- [Cluster Statuses](#cluster-statuses)
- [Volume Statuses](#volume-statuses)
- [Cluster Response Object](#cluster-response-object)


Base URL: `https://api.together.xyz/v1`

## Cluster Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /compute/clusters` | Create cluster | Provision a new GPU cluster |
| `GET /compute/clusters` | List clusters | List all GPU clusters |
| `GET /compute/clusters/{id}` | Get cluster | Get cluster details |
| `PUT /compute/clusters/{id}` | Update cluster | Scale or change cluster type |
| `DELETE /compute/clusters/{id}` | Delete cluster | Remove a cluster |
| `GET /compute/regions` | List regions | Available regions, GPUs, drivers |

## Storage Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST /compute/clusters/storage/volumes` | Create volume | Create shared storage |
| `GET /compute/clusters/storage/volumes` | List volumes | List all volumes |
| `GET /compute/clusters/storage/volumes/{id}` | Get volume | Get volume details |
| `PUT /compute/clusters/storage/volumes` | Update volume | Resize a volume |
| `DELETE /compute/clusters/storage/volumes/{id}` | Delete volume | Remove a volume |

## Create Cluster

The API requires `cuda_version` and `nvidia_driver_version` as separate fields. The SDK
also accepts a combined `driver_version` string, but the two split fields must be present
for the request to succeed. Pass them via `extra_body` in the SDK or directly in REST.

```python
from together import Together
client = Together()

cluster = client.beta.clusters.create(
    cluster_name="my-gpu-cluster",
    region="us-central-8",
    gpu_type="H100_SXM",
    num_gpus=8,
    driver_version="CUDA_12_6_560",
    billing_type="ON_DEMAND",
    cluster_type="KUBERNETES",
    # volume_id="existing-volume-id",  # optional: attach existing volume
    extra_body={
        "cuda_version": "12.6",
        "nvidia_driver_version": "560",
    },
)
print(cluster.cluster_id)
```

```typescript
import Together from "together-ai";
const client = new Together();

const cluster = await client.beta.clusters.create({
  cluster_name: "my-gpu-cluster",
  region: "us-central-8",
  gpu_type: "H100_SXM",
  num_gpus: 8,
  driver_version: "CUDA_12_6_560",
  billing_type: "ON_DEMAND",
  cluster_type: "KUBERNETES",
  // @ts-expect-error -- required by API but not yet in SDK types
  cuda_version: "12.6",
  nvidia_driver_version: "560",
});
console.log(cluster.cluster_id);
```

```shell
curl -X POST \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_name": "my-gpu-cluster",
    "region": "us-central-8",
    "gpu_type": "H100_SXM",
    "num_gpus": 8,
    "driver_version": "CUDA_12_6_560",
    "cuda_version": "12.6",
    "nvidia_driver_version": "560",
    "billing_type": "ON_DEMAND",
    "cluster_type": "KUBERNETES"
  }' \
  https://api.together.xyz/v1/compute/clusters
```

```shell
together beta clusters create \
  --name my-gpu-cluster \
  --num-gpus 8 \
  --gpu-type H100_SXM \
  --region us-central-8 \
  --driver-version CUDA_12_6_560 \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES
```

### Create Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cluster_name` | string | Yes | Name of the cluster |
| `region` | string | Yes | Region (use `list_regions()` in Python or `listRegions()` in TypeScript to find valid regions) |
| `gpu_type` | string | Yes | GPU type (see Instance Types below) |
| `num_gpus` | integer | Yes | Number of GPUs (must be a multiple of 8) |
| `driver_version` | string | Yes | Combined driver string, e.g. `CUDA_12_6_560` (see Driver Versions below) |
| `cuda_version` | string | Yes | CUDA version, e.g. `"12.6"` |
| `nvidia_driver_version` | string | Yes | NVIDIA driver version, e.g. `"560"` |
| `billing_type` | string | Yes | `ON_DEMAND` or `RESERVED` |
| `cluster_type` | string | No | `KUBERNETES` (default) or `SLURM` |
| `duration_days` | integer | No | Reservation length in days (only with `RESERVED`) |
| `volume_id` | string | No | Existing shared volume ID to attach |
| `shared_volume` | object | No | Inline volume: `{volume_name, size_tib, region}` |

## List Clusters

```python
response = client.beta.clusters.list()
for c in response.clusters:
    print(f"{c.cluster_id}: {c.cluster_name} ({c.status}, {c.num_gpus} GPUs)")
```

```typescript
const response = await client.beta.clusters.list();
for (const c of response.clusters) {
  console.log(`${c.cluster_id}: ${c.cluster_name} (${c.status})`);
}
```

```shell
curl -X GET \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters
```

```shell
together beta clusters list
```

## Get Cluster

```python
cluster = client.beta.clusters.retrieve("cluster-id")
print(f"Status: {cluster.status}, GPUs: {cluster.num_gpus}")
```

```typescript
const cluster = await client.beta.clusters.retrieve("cluster-id");
console.log(cluster);
```

```shell
curl -X GET \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters/${CLUSTER_ID}
```

```shell
together beta clusters retrieve <CLUSTER_ID>
```

## Update / Scale Cluster

```python
cluster = client.beta.clusters.update(
    "cluster-id",
    num_gpus=16,
    cluster_type="KUBERNETES",
)
```

```typescript
const cluster = await client.beta.clusters.update("cluster-id", {
  num_gpus: 16,
  cluster_type: "KUBERNETES",
});
```

```shell
curl -X PUT \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"num_gpus": 16, "cluster_type": "KUBERNETES"}' \
  https://api.together.xyz/v1/compute/clusters/${CLUSTER_ID}
```

```shell
together beta clusters update <CLUSTER_ID> --num-gpus 16
together beta clusters update <CLUSTER_ID> --num-gpus 16 --cluster-type KUBERNETES
```

### Update Request Body

| Field | Type | Description |
|-------|------|-------------|
| `num_gpus` | integer | New GPU count (must be a multiple of 8) |
| `cluster_type` | string | `KUBERNETES` or `SLURM` |

## Delete Cluster

```python
client.beta.clusters.delete("cluster-id")
```

```typescript
await client.beta.clusters.delete("cluster-id");
```

```shell
curl -X DELETE \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters/${CLUSTER_ID}
```

```shell
together beta clusters delete <CLUSTER_ID>
```

## List Regions

```python
regions = client.beta.clusters.list_regions()
for r in regions.regions:
    print(f"{r.name}: {r.supported_instance_types}, drivers: {r.driver_versions}")
```

```typescript
const regions = await client.beta.clusters.listRegions();
console.log(regions);
```

```shell
curl -X GET \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/regions
```

```shell
together beta clusters list-regions
```

## Create Shared Volume

```python
volume = client.beta.clusters.storage.create(
    volume_name="my-shared-volume",
    size_tib=2,
    region="us-central-8",
)
print(volume.volume_id)
```

```typescript
const volume = await client.beta.clusters.storage.create({
  volume_name: "my-shared-volume",
  size_tib: 2,
  region: "us-central-8",
});
console.log(volume.volume_id);
```

```shell
curl -X POST \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"volume_name": "my-shared-volume", "size_tib": 2, "region": "us-central-8"}' \
  https://api.together.xyz/v1/compute/clusters/storage/volumes
```

```shell
together beta clusters storage create \
  --volume-name my-shared-volume \
  --size-tib 2 \
  --region us-central-8
```

### Volume Create Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `volume_name` | string | Yes | Name of the volume |
| `size_tib` | integer | Yes | Size in tebibytes (TiB) |
| `region` | string | Yes | Region name |

## List Shared Volumes

```python
volumes = client.beta.clusters.storage.list()
for v in volumes.volumes:
    print(f"{v.volume_id}: {v.volume_name} ({v.size_tib} TiB, {v.status})")
```

```typescript
const volumes = await client.beta.clusters.storage.list();
console.log(volumes);
```

```shell
curl -X GET \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters/storage/volumes
```

```shell
together beta clusters storage list
```

## Get Shared Volume

```python
volume = client.beta.clusters.storage.retrieve("volume-id")
print(f"{volume.volume_name}: {volume.size_tib} TiB ({volume.status})")
```

```typescript
const volume = await client.beta.clusters.storage.retrieve("volume-id");
console.log(volume);
```

```shell
curl -X GET \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters/storage/volumes/${VOLUME_ID}
```

```shell
together beta clusters storage retrieve <VOLUME_ID>
```

## Update (Resize) Shared Volume

```python
volume = client.beta.clusters.storage.update(
    volume_id="volume-id",
    size_tib=5,
)
```

```typescript
const volume = await client.beta.clusters.storage.update({
  volume_id: "volume-id",
  size_tib: 5,
});
```

```shell
curl -X PUT \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"volume_id": "volume-id", "size_tib": 5}' \
  https://api.together.xyz/v1/compute/clusters/storage/volumes
```

## Delete Shared Volume

Volume must not be attached to any cluster.

```python
client.beta.clusters.storage.delete("volume-id")
```

```typescript
await client.beta.clusters.storage.delete("volume-id");
```

```shell
curl -X DELETE \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters/storage/volumes/${VOLUME_ID}
```

```shell
together beta clusters storage delete <VOLUME_ID>
```

## Instance Types

| CLI Value | GPU | Memory | Notes |
|-----------|-----|--------|-------|
| `H100_SXM` | NVIDIA H100 | 80GB | InfiniBand networking |
| `H100_SXM_INF` | NVIDIA H100 | 80GB | Inference-optimized, lower IB bandwidth |
| `H200_SXM` | NVIDIA H200 | 141GB | InfiniBand networking |
| `B200_SXM` | NVIDIA B200 | 192GB | InfiniBand networking |
| `L40_PCIE` | NVIDIA L40 | 48GB | PCIe |
| `RTX_6000_PCI` | NVIDIA RTX 6000 | 24GB | PCIe |

## Driver Versions

Available CUDA driver versions (check `list_regions()` in Python or `listRegions()` in TypeScript for per-region availability).

The `list_regions()` response returns driver versions as a list of objects:

```json
[
  {"cuda_version": "12.6", "nvidia_driver_version": "560"},
  {"cuda_version": "12.4", "nvidia_driver_version": "550"}
]
```

The combined `driver_version` string follows the pattern `CUDA_{major}_{minor}_{nvidia}`:

| `driver_version` | `cuda_version` | `nvidia_driver_version` |
|-------------------|----------------|--------------------------|
| `CUDA_12_4_550` | `12.4` | `550` |
| `CUDA_12_5_555` | `12.5` | `555` |
| `CUDA_12_6_560` | `12.6` | `560` |
| `CUDA_12_6_565` | `12.6` | `565` |
| `CUDA_12_8_570` | `12.8` | `570` |
| `CUDA_12_9_575` | `12.9` | `575` |

## Cluster Statuses

| Status | Description |
|--------|-------------|
| `Scheduled` | Cluster creation accepted, awaiting resource allocation |
| `WaitingForControlPlaneNodes` | Control plane provisioning |
| `WaitingForDataPlaneNodes` | Worker nodes provisioning |
| `WaitingForSubnet` | Network setup |
| `WaitingForSharedVolume` | Storage provisioning |
| `InstallingDrivers` | CUDA driver installation |
| `RunningAcceptanceTests` | GPU/network health validation |
| `Ready` | Cluster operational |
| `Degraded` | Some nodes unhealthy |
| `Paused` | Cluster paused |
| `OnDemandComputePaused` | On-demand compute paused (credit issue) |
| `Deleting` | Cluster being removed |

## Volume Statuses

| Status | Description |
|--------|-------------|
| `available` | Ready for attachment |
| `bound` | Attached to a cluster |
| `provisioning` | Being created |

## Cluster Response Object

```json
{
  "cluster_id": "abc-123-def-456",
  "cluster_name": "my-gpu-cluster",
  "cluster_type": "KUBERNETES",
  "region": "us-central-8",
  "gpu_type": "H100_SXM",
  "num_gpus": 8,
  "driver_version": "CUDA_12_6_560",
  "duration_hours": 720,
  "status": "Ready",
  "control_plane_nodes": [...],
  "gpu_worker_nodes": [...],
  "volumes": [...],
  "kube_config": "..."
}
```
