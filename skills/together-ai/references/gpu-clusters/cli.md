# CLI Reference for GPU Clusters
## Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Cluster Commands](#cluster-commands)
- [Storage Commands](#storage-commands)
- [Instance Types](#instance-types)
- [Driver Versions](#driver-versions)
- [Pricing and billing](#pricing-and-billing)


The Together CLI (`tg`) is the supported command-line interface for managing GPU clusters. It ships with the Together Python SDK and replaces the legacy standalone `tcloud` binary.

`together` is also installed as an alias of `tg`. Examples in this reference use the `tg` form to match the official docs.

## Installation

Install the CLI as a `uv` tool. The `[cli]` extra pulls in CLI-only dependencies without bloating the Python SDK:

```shell
uv tool install "together[cli]>=3"
tg --help
```

Upgrade with:

```shell
uv tool upgrade "together[cli]>=3"
```

For CI/CD, invoke the CLI directly with `uvx` to avoid a separate install step:

```shell
uvx "together[cli]>=3" clusters list
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
tg clusters create [OPTIONS]
```

Every cluster needs at least 8 GPUs, in multiples of 8, and a shared volume. The API rejects a
create request that has no volume, so pass either `--volume` (attach an existing one) or
`--shared-volume-name` with `--shared-volume-size-tib` (create one with the cluster).

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Name of the cluster |
| `--num-gpus` | number | Number of GPUs. At least 8, in multiples of 8. |
| `--gpu-type` | string | `H100_SXM`, `H200_SXM`, `B200_SXM`, `B300_SXM`, `GB200_NVL`, `H100_SXM_INF`, `L40_PCIE`, `RTX_6000_PCI`. Availability varies by region (`clusters list-regions`). |
| `--region` | string | Region (use `clusters list-regions` to find valid regions) |
| `--billing-type` | enum | `ON_DEMAND`, `RESERVED`, or `SCHEDULED_CAPACITY` |
| `--duration-days` | number | Reservation length in days (only with `RESERVED` billing) |
| `--nvidia-version-id` | string | NVIDIA version catalog ID: a driver version's `id` in `clusters list-regions` output. Selects an exact driver, CUDA, and OS combination. Do not combine with the three flags below. |
| `--nvidia-driver-version` | string | NVIDIA driver version (use `clusters list-regions` for options). Pass together with `--cuda-version`. |
| `--cuda-version` | string | CUDA version (use `clusters list-regions` for options). Pass together with `--nvidia-driver-version`. |
| `--os` | string | Operating system for the driver and CUDA pair, for example `ubuntu-24.04`. Requires both version flags. When omitted, the API uses `ubuntu-22.04`. |
| `--cluster-type` | enum | `KUBERNETES` or `SLURM` |
| `--volume` | string | Existing storage volume ID to attach |
| `--shared-volume-name` | string | Name of a shared volume to create with the cluster (CLI 3.2.0+). Requires `--shared-volume-size-tib`. Cannot be combined with `--volume`. |
| `--shared-volume-size-tib` | number | Size of that volume in whole TiB, at least 1 (CLI 3.2.0+). Requires `--shared-volume-name`. |
| `--non-interactive` | -- | Skip interactive prompts. Required in CI. |
| `--json` | -- | Output in JSON format |

In non-interactive mode (`--non-interactive` or `--json`), select the driver one of two ways: pass
`--nvidia-version-id` alone, or pass `--nvidia-driver-version` and `--cuda-version` together,
optionally with `--os`. Both come from the region's `driver_versions` in `clusters list-regions`.

`tg clusters create --help` lists further flags for autoscaling, capacity pools, preemptible GPUs,
scheduled capacity, and Slurm options.

**Examples:**

```shell
# On-demand Kubernetes cluster with H100s and a new 1 TiB shared volume
tg clusters create \
  --name my-training-cluster \
  --num-gpus 8 \
  --gpu-type H100_SXM \
  --region us-central-8 \
  --nvidia-version-id <NVIDIA_VERSION_ID> \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES \
  --shared-volume-name my-training-data \
  --shared-volume-size-tib 1 \
  --non-interactive

# Reserved Slurm cluster with H200s and an existing volume
tg clusters create \
  --name my-slurm-cluster \
  --num-gpus 16 \
  --gpu-type H200_SXM \
  --region us-central-8 \
  --nvidia-driver-version <NVIDIA_DRIVER_VERSION> \
  --cuda-version <CUDA_VERSION> \
  --billing-type RESERVED \
  --duration-days 30 \
  --cluster-type SLURM \
  --volume <VOLUME_ID> \
  --non-interactive
```

Prefer creating the volume with the cluster. A volume created on its own with
`clusters storage create` can land in a different datacenter of the region, and attaching it then
fails with `Shared volume you selected does not exist in the datacenter`.

### `clusters list`

List all GPU clusters.

```shell
tg clusters list
```

### `clusters retrieve`

Get details for a specific cluster.

```shell
tg clusters retrieve [CLUSTER_ID]
```

### `clusters update`

Update the configuration of an existing cluster, for example to scale its GPU count.

```shell
tg clusters update [CLUSTER_ID] [OPTIONS]
```

**Options:**

| Flag | Type | Description |
|------|------|-------------|
| `--num-gpus` | number | New GPU count. At least 8, in multiples of 8. |
| `--cluster-type` | enum | `KUBERNETES` or `SLURM`. Accepted, but the API ignores it on update, so the cluster keeps the type it was created with. |
| `--json` | -- | Output in JSON format |

**Example:**

```shell
# Scale up to 16 GPUs
tg clusters update [CLUSTER_ID] --num-gpus 16
```

### `clusters delete`

Delete a GPU cluster. The command asks for confirmation unless you pass `--force`,
`--non-interactive`, or `--json`. Deleting a cluster does not delete its shared volume, which
keeps billing until you delete it with `clusters storage delete`.

```shell
tg clusters delete [CLUSTER_ID]
```

### `clusters list-regions`

List available regions, supported GPU types, and driver versions. The response has no prices
and does not show stock.

```shell
tg clusters list-regions
```

**Example output** (shape only; run the command for live values):

```json
{
  "regions": [
    {
      "driver_versions": [
        {"id": "<NVIDIA_VERSION_ID>", "cuda_version": "13.0", "nvidia_driver_version": "580", "os": "ubuntu-24.04"},
        {"id": "<NVIDIA_VERSION_ID>", "cuda_version": "13.0", "nvidia_driver_version": "580", "os": "ubuntu-22.04"},
        {"id": "<NVIDIA_VERSION_ID>", "cuda_version": "12.8", "nvidia_driver_version": "570", "os": "ubuntu-22.04"}
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

Pass a driver version's `id` as `--nvidia-version-id`.

### `clusters get-credentials`

Download Kubernetes credentials (kubeconfig) for a cluster.

```shell
tg clusters get-credentials [CLUSTER_ID] [OPTIONS]
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
tg clusters get-credentials [CLUSTER_ID] --set-default-context

# Write to a specific file
tg clusters get-credentials [CLUSTER_ID] --file ./kubeconfig.yaml

# Print to stdout
tg clusters get-credentials [CLUSTER_ID] --file -

# Use the cluster
kubectl get nodes
```

## Storage Commands

Shared storage volumes are persistent, resizable, high-throughput storage backed by multi-NIC
bare metal paths. Volumes persist independently of cluster lifecycle.

### `clusters storage create`

Create a new shared storage volume.

```shell
tg clusters storage create [OPTIONS]
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
tg clusters storage create \
  --volume-name my-training-data \
  --size-tib 2 \
  --region us-central-8
```

### `clusters storage list`

List all shared storage volumes.

```shell
tg clusters storage list
```

### `clusters storage retrieve`

Get details for a specific volume.

```shell
tg clusters storage retrieve [VOLUME_ID]
```

### `clusters storage update`

Grow a volume. Decreasing a volume's size requires contacting Together.

```shell
tg clusters storage update [VOLUME_ID] --size-tib 4
```

### `clusters storage delete`

Delete a shared storage volume. The volume must not be attached to any cluster.

```shell
tg clusters storage delete [VOLUME_ID]
```

## Instance Types

| CLI Value | GPU | Memory | Notes |
|-----------|-----|--------|-------|
| `H100_SXM` | NVIDIA H100 | 80GB | InfiniBand networking |
| `H100_SXM_INF` | NVIDIA H100 | 80GB | Inference-optimized, lower IB bandwidth |
| `H200_SXM` | NVIDIA H200 | 141GB | InfiniBand networking |
| `B200_SXM` | NVIDIA B200 | 192GB | InfiniBand networking |
| `B300_SXM` | NVIDIA B300 | -- | Check `clusters list-regions` for regions |
| `GB200_NVL` | NVIDIA GB200 NVL72 | -- | No public rate. Request capacity from Together. |
| `L40_PCIE` | NVIDIA L40 | 48GB | PCIe |
| `RTX_6000_PCI` | NVIDIA RTX 6000 | 24GB | PCIe |

## Driver Versions

Driver versions are per region and change over time, so read them from `clusters list-regions`
instead of a fixed list. Each entry in a region's `driver_versions` has an `id`, a `cuda_version`,
an `nvidia_driver_version`, and an `os`. Pass the `id` as `--nvidia-version-id`, or pass the
driver and CUDA versions as `--nvidia-driver-version` and `--cuda-version`, adding `--os` for an
OS other than `ubuntu-22.04`.

## Pricing and billing

The CLI and the regions API return no prices. For current per-GPU-hour rates, open the
[GPU cluster pricing table](https://www.together.ai/pricing#gpu-clusters). For how compute and
storage bill, including reserved terms and what happens when credits run out, see
[GPU clusters pricing and billing](https://docs.together.ai/docs/gpu-clusters-billing). The
smallest cluster has 8 GPUs, so its hourly cost is eight times the per-GPU rate.
