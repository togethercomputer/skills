# CLI Reference for GPU Clusters
## Contents

- [Installation](#installation)
- [Cluster Commands](#cluster-commands)
- [Storage Commands](#storage-commands)
- [Instance Types](#instance-types)
- [Driver Versions](#driver-versions)


The Together GPU Clusters CLI is available in two forms:

- **Together CLI**: `together beta clusters <subcommand>` (included with the Together Python SDK)
- **Standalone tcloud**: `tcloud cluster <subcommand>` (standalone binary)

Both CLIs provide equivalent functionality. This reference uses the `together beta clusters` form.

## Installation

**Together CLI (via pip):**
```shell
uv pip install "together>=2.0.0"
together auth login
```

**tcloud standalone binary:**

Mac (Universal):
```shell
curl -LO https://tcloud-cli-downloads.s3.us-west-2.amazonaws.com/releases/latest/tcloud-darwin-universal.tar.gz
tar xzf tcloud-darwin-universal.tar.gz
```

Linux (AMD64):
```shell
curl -LO https://tcloud-cli-downloads.s3.us-west-2.amazonaws.com/releases/latest/tcloud-linux-amd64.tar.gz
tar xzf tcloud-linux-amd64.tar.gz
```

Authenticate tcloud:
```shell
tcloud sso login
```

## Cluster Commands

### `clusters create`

Create a new GPU cluster.

```shell
together beta clusters create [OPTIONS]
```

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Name of the cluster |
| `--num-gpus` | number | Number of GPUs (must be a multiple of 8) |
| `--gpu-type` | enum | `H100_SXM`, `H200_SXM`, `B200_SXM`, `H100_SXM_INF`, `L40_PCIE`, `RTX_6000_PCI` |
| `--region` | string | Region (use `clusters list-regions` to find valid regions) |
| `--billing-type` | enum | `ON_DEMAND` or `RESERVED` |
| `--duration-days` | number | Reservation length in days (only with `RESERVED` billing) |
| `--driver-version` | enum | CUDA driver version (use `clusters list-regions` for options) |
| `--cluster-type` | enum | `KUBERNETES` or `SLURM` |
| `--volume` | string | Existing storage volume ID to attach |
| `--json` | -- | Output in JSON format |

**Examples:**

```shell
# On-demand Kubernetes cluster with H100s
together beta clusters create \
  --name my-training-cluster \
  --num-gpus 8 \
  --gpu-type H100_SXM \
  --region us-central-8 \
  --driver-version CUDA_12_6_560 \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES

# Reserved Slurm cluster with H200s and attached storage
together beta clusters create \
  --name my-slurm-cluster \
  --num-gpus 16 \
  --gpu-type H200_SXM \
  --region us-central-8 \
  --driver-version CUDA_12_6_560 \
  --billing-type RESERVED \
  --duration-days 30 \
  --cluster-type SLURM \
  --volume <VOLUME_ID>
```

Equivalent tcloud command:
```shell
tcloud cluster create my-training-cluster \
  --num-gpus 8 \
  --instance-type H100-SXM \
  --region us-central-8 \
  --billing-type on_demand \
  --shared-volume-name my-volume \
  --size-tib 1
```

### `clusters list`

List all GPU clusters.

```shell
together beta clusters list
```

### `clusters retrieve`

Get details for a specific cluster.

```shell
together beta clusters retrieve <CLUSTER_ID>
```

### `clusters update`

Update the configuration of an existing cluster (scale GPU count or change cluster type).

```shell
together beta clusters update <CLUSTER_ID> [OPTIONS]
```

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--num-gpus` | number | New GPU count (must be a multiple of 8) |
| `--cluster-type` | enum | `KUBERNETES` or `SLURM` |
| `--json` | -- | Output in JSON format |

**Example:**

```shell
# Scale up to 16 GPUs
together beta clusters update <CLUSTER_ID> --num-gpus 16

# Switch to Slurm
together beta clusters update <CLUSTER_ID> --cluster-type SLURM
```

Equivalent tcloud command:
```shell
tcloud cluster scale <CLUSTER_UUID> --num-gpus 16
```

### `clusters delete`

Delete a GPU cluster.

```shell
together beta clusters delete <CLUSTER_ID>
```

Equivalent tcloud command:
```shell
tcloud cluster delete <CLUSTER_UUID>
```

### `clusters list-regions`

List available regions, supported GPU types, and driver versions.

```shell
together beta clusters list-regions
```

**Example output:**

```json
{
    "regions": [
        {
            "driver_versions": [
                "CUDA_12_6_565",
                "CUDA_12_5_555",
                "CUDA_12_8_570",
                "CUDA_12_9_575",
                "CUDA_12_6_560",
                "CUDA_12_4_550"
            ],
            "name": "us-central-8",
            "supported_instance_types": [
                "H100_SXM",
                "H200_SXM"
            ]
        }
    ]
}
```

### `clusters get-credentials`

Download Kubernetes credentials (kubeconfig) for a cluster.

```shell
together beta clusters get-credentials <CLUSTER_ID> [OPTIONS]
```

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--file` | path or `-` | Path to write kubeconfig. `-` prints to stdout. Default: `~/.kube/config` |
| `--context-name` | string | Name for the kubeconfig context. Default: cluster name |
| `--overwrite-existing` | -- | Overwrite existing kubeconfig entries on conflict |
| `--set-default-context` | -- | Set the new context as default for kubectl |

**Examples:**

```shell
# Write to default kubeconfig location
together beta clusters get-credentials <CLUSTER_ID>

# Write to a specific file
together beta clusters get-credentials <CLUSTER_ID> --file ./kubeconfig.yaml

# Print to stdout
together beta clusters get-credentials <CLUSTER_ID> --file -

# Overwrite and set as default
together beta clusters get-credentials <CLUSTER_ID> \
  --overwrite-existing \
  --set-default-context

# Use the cluster
export KUBECONFIG=~/.kube/config
kubectl get nodes
```

## Storage Commands

Shared storage volumes are persistent, resizable, high-throughput storage backed by multi-NIC
bare metal paths. Volumes persist independently of cluster lifecycle.

### `clusters storage create`

Create a new shared storage volume.

```shell
together beta clusters storage create [OPTIONS]
```

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--volume-name` | string | Name of the storage volume (required) |
| `--size-tib` | number | Size in tebibytes (required) |
| `--region` | string | Region to create the volume in (required) |
| `--json` | -- | Output in JSON format |

**Example:**

```shell
together beta clusters storage create \
  --volume-name my-training-data \
  --size-tib 2 \
  --region us-central-8
```

### `clusters storage list`

List all shared storage volumes.

```shell
together beta clusters storage list
```

### `clusters storage retrieve`

Get details for a specific volume.

```shell
together beta clusters storage retrieve <VOLUME_ID>
```

### `clusters storage delete`

Delete a shared storage volume. The volume must not be attached to any cluster.

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

Available CUDA driver versions (check `clusters list-regions` for per-region availability):

- `CUDA_12_4_550`
- `CUDA_12_5_555`
- `CUDA_12_6_560`
- `CUDA_12_6_565`
- `CUDA_12_8_570`
- `CUDA_12_9_575`
