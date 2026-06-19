# CLI Reference for GPU Clusters
## Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Cluster Commands](#cluster-commands)
- [Storage Commands](#storage-commands)
- [Instance Types](#instance-types)
- [Driver Versions](#driver-versions)


The Together CLI (`tg`) is the supported command-line interface for managing GPU clusters. It ships with the Together Python SDK and replaces the legacy standalone `tcloud` binary.

`together` is also installed as an alias of `tg`. Examples in this reference use the `tg` form to match the official docs.

## Installation

Install the CLI as a `uv` tool. The `[cli]` extra pulls in CLI-only dependencies without bloating the Python SDK:

```shell
uv tool install "together[cli]"
tg --help
```

Upgrade with:

```shell
uv tool upgrade "together[cli]"
```

For CI/CD, invoke the CLI directly with `uvx` to avoid a separate install step:

```shell
uvx "together[cli]" beta clusters list
```

## Authentication

The CLI authenticates via the `TOGETHER_API_KEY` environment variable. Get a key from [account settings](https://api.together.ai/settings/projects/~first/api-keys):

```shell
export TOGETHER_API_KEY=<your_key>
```

You can also pass `--api-key` per command, but the environment variable is preferred in CI so the token does not appear in process lists or logs. If both are provided, `--api-key` takes precedence.

## Global Flags

Available on every command:

| Flag | Description |
|------|-------------|
| `--json` | Return the response as JSON. Useful for scripting. |
| `--non-interactive` | Disable interactive prompts. Required in CI/CD. |
| `--api-key [string]` | Together API key. Falls back to `TOGETHER_API_KEY`. |
| `--timeout [number]` | Request timeout, in seconds. |
| `--max-retries [number]` | Maximum number of HTTP retries. |
| `--debug` | Enable debug logging. |
| `--help` | Print help for the prefixed command. |

## Cluster Commands

### `clusters create`

Create a new GPU cluster. Run with no flags to launch an interactive prompt that walks through the required fields.

```shell
tg beta clusters create [OPTIONS]
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
| `--nvidia-driver-version` | string | NVIDIA driver version (use `clusters list-regions` for options) |
| `--cuda-version` | string | CUDA version (use `clusters list-regions` for options) |
| `--cluster-type` | enum | `KUBERNETES` or `SLURM` |
| `--volume` | string | Existing storage volume ID to attach |
| `--non-interactive` | -- | Skip interactive prompts. Required in CI. |
| `--json` | -- | Output in JSON format |

**Examples:**

```shell
# On-demand Kubernetes cluster with H100s
tg beta clusters create \
  --name my-training-cluster \
  --num-gpus 8 \
  --gpu-type H100_SXM \
  --region us-central-8 \
  --cuda-version 12.6 \
  --nvidia-driver-version 560 \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES \
  --non-interactive

# Reserved Slurm cluster with H200s and attached storage
tg beta clusters create \
  --name my-slurm-cluster \
  --num-gpus 16 \
  --gpu-type H200_SXM \
  --region us-central-8 \
  --cuda-version 12.6 \
  --nvidia-driver-version 560 \
  --billing-type RESERVED \
  --duration-days 30 \
  --cluster-type SLURM \
  --volume <VOLUME_ID> \
  --non-interactive
```

### `clusters list`

List all GPU clusters.

```shell
tg beta clusters list
```

### `clusters retrieve`

Get details for a specific cluster.

```shell
tg beta clusters retrieve [CLUSTER_ID]
```

### `clusters update`

Update the configuration of an existing cluster (scale GPU count or change cluster type).

```shell
tg beta clusters update [CLUSTER_ID] [OPTIONS]
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
tg beta clusters update [CLUSTER_ID] --num-gpus 16

# Switch to Slurm
tg beta clusters update [CLUSTER_ID] --cluster-type SLURM
```

### `clusters delete`

Delete a GPU cluster.

```shell
tg beta clusters delete [CLUSTER_ID]
```

### `clusters list-regions`

List available regions, supported GPU types, and driver versions.

```shell
tg beta clusters list-regions
```

**Example output:**

```json
{
  "regions": [
    {
      "driver_versions": [
        {"cuda_version": "12.9", "nvidia_driver_version": "575"},
        {"cuda_version": "12.8", "nvidia_driver_version": "570"},
        {"cuda_version": "12.6", "nvidia_driver_version": "560"}
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
tg beta clusters get-credentials [CLUSTER_ID] [OPTIONS]
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
# Merge into ~/.kube/config and switch the default context
tg beta clusters get-credentials [CLUSTER_ID] --set-default-context

# Write to a specific file
tg beta clusters get-credentials [CLUSTER_ID] --file ./kubeconfig.yaml

# Print to stdout
tg beta clusters get-credentials [CLUSTER_ID] --file -

# Use the cluster
kubectl get nodes
```

## Storage Commands

Shared storage volumes are persistent, resizable, high-throughput storage backed by multi-NIC
bare metal paths. Volumes persist independently of cluster lifecycle.

### `clusters storage create`

Create a new shared storage volume.

```shell
tg beta clusters storage create [OPTIONS]
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
tg beta clusters storage create \
  --volume-name my-training-data \
  --size-tib 2 \
  --region us-central-8
```

### `clusters storage list`

List all shared storage volumes.

```shell
tg beta clusters storage list
```

### `clusters storage retrieve`

Get details for a specific volume.

```shell
tg beta clusters storage retrieve [VOLUME_ID]
```

### `clusters storage delete`

Delete a shared storage volume. The volume must not be attached to any cluster.

```shell
tg beta clusters storage delete [VOLUME_ID]
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
