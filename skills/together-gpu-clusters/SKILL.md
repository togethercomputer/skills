---
name: together-gpu-clusters
description: Provision on-demand and reserved GPU clusters (Instant Clusters) on Together AI with H100, H200, B200, L40, and RTX-6000 hardware. Supports Kubernetes and Slurm orchestration, autoscaling, shared storage volumes, health checks, and user management. Manage via Python SDK, TypeScript SDK, tcloud CLI, Terraform, SkyPilot, or REST API. Use when users need GPU clusters, distributed training, multi-node compute, HPC workloads, or large-scale ML infrastructure.
---

# Together GPU Clusters

## Overview

Provision GPU clusters on Together AI for distributed training, large-scale inference, and HPC
workloads.

- **Hardware**: NVIDIA H100, H200, B200 (SXM), L40 (PCIe), RTX-6000 (PCIe)
- **Cluster types**: On-demand (pay-as-you-go) or Reserved (1-90 day commitment)
- **Orchestration**: Kubernetes or Slurm
- **Management**: Python SDK, TypeScript SDK, tcloud CLI, Terraform, SkyPilot, REST API
- **Networking**: InfiniBand for high-bandwidth inter-node communication
- **Storage**: Shared persistent volumes, local NVMe, NFS /home

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together # for quick install without setting project
```

```shell
# or with pip
pip install together
```

```shell
# TypeScript / JavaScript
npm install together-ai
```

```shell
# Standalone tcloud CLI (alternative to Together CLI)
# Mac (Universal)
curl -LO https://tcloud-cli-downloads.s3.us-west-2.amazonaws.com/releases/latest/tcloud-darwin-universal.tar.gz
tar xzf tcloud-darwin-universal.tar.gz

# Linux (AMD64)
curl -LO https://tcloud-cli-downloads.s3.us-west-2.amazonaws.com/releases/latest/tcloud-linux-amd64.tar.gz
tar xzf tcloud-linux-amd64.tar.gz
```

Set your API key and authenticate:

```shell
export TOGETHER_API_KEY=<your-api-key>

# Together CLI
together auth login

# tcloud (alternative)
tcloud sso login
```

## Workflow

1. Choose hardware, region, and cluster size
2. Create cluster via SDK, CLI, or API
3. Configure orchestration (Kubernetes or Slurm)
4. Attach or create shared storage
5. Run workloads, monitor health
6. Scale up/down as needed
7. Delete when done

## Quick Start

### List Available Regions

```python
from together import Together
client = Together()

regions = client.beta.clusters.list_regions()
for region in regions.regions:
    print(f"{region.name}: {region.supported_instance_types}")
```

```typescript
import Together from "together-ai";
const client = new Together();

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

### Create a Cluster

```python
from together import Together
client = Together()

cluster = client.beta.clusters.create(
    cluster_name="my-training-cluster",
    region="us-central-8",
    gpu_type="H100_SXM",
    num_gpus=8,
    driver_version="CUDA_12_6_560",
    billing_type="ON_DEMAND",
    cluster_type="KUBERNETES",
    # volume_id="existing-volume-id",  # attach existing volume
)
print(cluster.cluster_id)
```

```typescript
import Together from "together-ai";
const client = new Together();

const cluster = await client.beta.clusters.create({
  cluster_name: "my-training-cluster",
  region: "us-central-8",
  gpu_type: "H100_SXM",
  num_gpus: 8,
  driver_version: "CUDA_12_6_560",
  billing_type: "ON_DEMAND",
  cluster_type: "KUBERNETES",
});
console.log(cluster.cluster_id);
```

```shell
curl -X POST \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_name": "my-training-cluster",
    "region": "us-central-8",
    "gpu_type": "H100_SXM",
    "num_gpus": 8,
    "driver_version": "CUDA_12_6_560",
    "billing_type": "ON_DEMAND",
    "cluster_type": "KUBERNETES"
  }' \
  https://api.together.xyz/v1/compute/clusters
```

```shell
# On-demand Kubernetes cluster
together beta clusters create \
  --name my-training-cluster \
  --num-gpus 8 \
  --gpu-type H100_SXM \
  --region us-central-8 \
  --driver-version CUDA_12_6_560 \
  --billing-type ON_DEMAND \
  --cluster-type KUBERNETES

# Reserved Slurm cluster with attached storage
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

### Check Cluster Status

```python
# Retrieve a specific cluster
cluster = client.beta.clusters.retrieve("cluster-id")
print(f"{cluster.cluster_name}: {cluster.status}")

# List all clusters
response = client.beta.clusters.list()
for c in response.clusters:
    print(f"{c.cluster_id}: {c.cluster_name} ({c.status})")
```

```typescript
const cluster = await client.beta.clusters.retrieve("cluster-id");
console.log(cluster.status);

const response = await client.beta.clusters.list();
for (const c of response.clusters) {
  console.log(`${c.cluster_id}: ${c.cluster_name} (${c.status})`);
}
```

```shell
curl -X GET \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.xyz/v1/compute/clusters/${CLUSTER_ID}
```

```shell
together beta clusters retrieve <CLUSTER_ID>
together beta clusters list
```

### Scale a Cluster

GPU count must be a multiple of 8.

```python
cluster = client.beta.clusters.update("cluster-id", num_gpus=16)
print(cluster.num_gpus)
```

```typescript
const cluster = await client.beta.clusters.update("cluster-id", {
  num_gpus: 16,
});
console.log(cluster.num_gpus);
```

```shell
curl -X PUT \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"num_gpus": 16}' \
  https://api.together.xyz/v1/compute/clusters/${CLUSTER_ID}
```

```shell
together beta clusters update <CLUSTER_ID> --num-gpus 16
```

### Get Kubernetes Credentials

```shell
# Write kubeconfig to default location (~/.kube/config)
together beta clusters get-credentials <CLUSTER_ID>

# Write to a specific file
together beta clusters get-credentials <CLUSTER_ID> --file ./kubeconfig.yaml

# Print to stdout
together beta clusters get-credentials <CLUSTER_ID> --file -

# Overwrite existing context and set as default
together beta clusters get-credentials <CLUSTER_ID> \
  --overwrite-existing \
  --set-default-context

# Then use kubectl
export KUBECONFIG=~/.kube/config
kubectl get nodes
```

### Delete a Cluster

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

## Shared Storage

Persistent volumes backed by multi-NIC bare metal paths. Volumes persist independently of
cluster lifecycle and can be attached at cluster creation time.

### Create a Volume

```python
volume = client.beta.clusters.storage.create(
    volume_name="my-shared-data",
    size_tib=2,
    region="us-central-8",
)
print(volume.volume_id)
```

```typescript
const volume = await client.beta.clusters.storage.create({
  volume_name: "my-shared-data",
  size_tib: 2,
  region: "us-central-8",
});
console.log(volume.volume_id);
```

```shell
curl -X POST \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"volume_name": "my-shared-data", "size_tib": 2, "region": "us-central-8"}' \
  https://api.together.xyz/v1/compute/clusters/storage/volumes
```

```shell
together beta clusters storage create \
  --volume-name my-shared-data \
  --size-tib 2 \
  --region us-central-8
```

### List and Retrieve Volumes

```python
# List all volumes
volumes = client.beta.clusters.storage.list()
for v in volumes.volumes:
    print(f"{v.volume_id}: {v.volume_name} ({v.size_tib} TiB, {v.status})")

# Retrieve a specific volume
volume = client.beta.clusters.storage.retrieve("volume-id")
```

```typescript
const volumes = await client.beta.clusters.storage.list();
console.log(volumes);

const volume = await client.beta.clusters.storage.retrieve("volume-id");
console.log(volume);
```

```shell
together beta clusters storage list
together beta clusters storage retrieve <VOLUME_ID>
```

### Resize a Volume

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

### Delete a Volume

Volume must not be attached to any cluster.

```python
client.beta.clusters.storage.delete("volume-id")
```

```typescript
await client.beta.clusters.storage.delete("volume-id");
```

```shell
together beta clusters storage delete <VOLUME_ID>
```

## Kubernetes vs Slurm

**Choose Kubernetes when:**
- Running containerized workloads
- Need auto-scheduling and autoscaling
- Using cloud-native ML frameworks (KubeFlow, Ray)

**Choose Slurm when:**
- Traditional HPC workloads
- Multi-node MPI training
- Familiar with Slurm job scripts
- Need fine-grained resource allocation

You can switch between Kubernetes and Slurm on an existing cluster via the update API.

## Slurm Usage

Slurm clusters provide SSH-accessible login nodes for job submission. Worker nodes are
registered with both Kubernetes and Slurm (Slinky architecture).

```shell
# Access the login node
ssh <username>@slurm-login

# Check node and partition status
sinfo
squeue

# Interactive GPU session
srun --gres=gpu:8 --pty bash

# Submit a batch job
sbatch train.sh

# Cancel a job
scancel <jobid>
```

See [references/cluster-management.md](references/cluster-management.md) for Slurm configuration
details and job script examples.

## Health Checks

Nodes undergo automatic acceptance testing during provisioning:
- DCGM Diag (Level 2) -- GPU compute, memory, and thermal validation
- GPU Burn (5 min) -- stress test for thermal/power issues
- Single-Node NCCL -- GPU-to-GPU communication within a node
- Multi-Node NCCL -- cross-node GPU communication

Nodes that fail are not added to the cluster until repaired. Repair options:
- **Quick Reprovision**: VM recreated on a random physical node (software issues)
- **Migrate to New Host**: New VM on different hardware (hardware failures)

```shell
# Monitor GPU health
nvidia-smi
nvidia-smi -q | grep -i ecc
sudo dmesg | grep -i xid
```

## Autoscaling (Kubernetes)

Kubernetes clusters support autoscaling via the Cluster Autoscaler. Enable during cluster
creation in the UI by toggling autoscaling and setting maximum GPUs.

The autoscaler:
- Scales up when pods are pending due to insufficient resources
- Scales down when nodes are underutilized
- Respects pod disruption budgets

### Targeted Scale-down

```shell
# Kubernetes -- cordon specific nodes before scaling down
kubectl cordon <node_name>

# Slurm -- drain specific nodes
sudo scontrol update NodeName=<node_name> State=drain Reason="scaling down"
```

## User Management

Access is controlled at the project level. All clusters in a project share the same access list.

| Role | Control Plane | Data Plane |
|------|--------------|------------|
| **Admin** | Full write (create/delete/scale clusters and volumes) | Full SSH and kubectl |
| **Member** | Read-only (view only) | SSH and kubectl access |

Manage users via Settings -> GPU Cluster Projects -> View Project -> Add/Remove User.

## Terraform Integration

```hcl
resource "together_gpu_cluster" "training" {
  name              = "my-training-cluster"
  num_gpus          = 8
  instance_type     = "H100-SXM"
  region            = "us-central-8"
  billing_type      = "prepaid"
  reservation_days  = 30
  shared_volume {
    name     = "training-data"
    size_tib = 5
  }
}
```

```shell
terraform init && terraform plan && terraform apply
```

## SkyPilot Integration

```yaml
# sky.yaml
resources:
  accelerators: H100:8
  cloud: kubernetes

setup: |
  pip install torch transformers

run: |
  torchrun --nproc_per_node=8 train.py
```

```shell
sky launch sky.yaml
```

## Key CLI Commands

| `together beta clusters` | `tcloud cluster` | Description |
|--------------------------|-------------------|-------------|
| `clusters create` | `cluster create` | Create a new cluster |
| `clusters list` | `cluster list` | List all clusters |
| `clusters retrieve <ID>` | `cluster get <ID>` | Get cluster details |
| `clusters update <ID>` | `cluster scale <ID>` | Update/scale a cluster |
| `clusters delete <ID>` | `cluster delete <ID>` | Delete a cluster |
| `clusters list-regions` | -- | List regions and GPU types |
| `clusters get-credentials <ID>` | -- | Get K8s kubeconfig |
| `clusters storage create` | -- | Create shared volume |
| `clusters storage list` | -- | List shared volumes |
| `clusters storage retrieve <ID>` | -- | Get volume details |
| `clusters storage delete <ID>` | -- | Delete shared volume |

## Billing

- **Reserved**: Upfront payment, 1-90 days, discounted rates. Non-refundable, non-cancellable.
  Clusters cannot be paused -- charges apply for the full period.
- **On-demand**: Per-GPU-hour billing, no commitment. Can stop/start anytime.
- **Storage**: Pay-per-TiB, billed independently of cluster lifecycle. Persists after cluster
  deletion. Can expand freely; contact support to reduce.
- **Hybrid**: Use reserved for baseline capacity + on-demand for burst workloads.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Cluster stuck provisioning | Check status -- may be WaitingForControlPlaneNodes or RunningAcceptanceTests |
| Pods not scheduling | Verify node status with `kubectl get nodes`, check resource requests |
| GPU not accessible in container | Use CUDA-enabled image (e.g., `pytorch/pytorch`, `nvidia/cuda`) |
| Storage PVC not binding | Confirm volume name matches shared volume, check `kubectl get pvc` |
| Slurm job failures | Run `sinfo` to check partitions, `scontrol show job <jobid>` for details |
| Node health issues | Check `nvidia-smi`, `dmesg | grep xid`, trigger repair via UI |

## Resources

- **CLI reference**: See [references/tcloud-cli.md](references/tcloud-cli.md)
- **API reference**: See [references/api-reference.md](references/api-reference.md)
- **Cluster management**: See [references/cluster-management.md](references/cluster-management.md)
- **Runnable scripts**: See [scripts/](scripts/) for Python and TypeScript examples
- **Official docs**: [GPU Clusters Overview](https://docs.together.ai/docs/gpu-clusters-overview)
- **Quickstart**: [GPU Clusters Quickstart](https://docs.together.ai/docs/gpu-clusters-quickstart)
- **API reference**: [Clusters API](https://docs.together.ai/reference/clusters-create)
- **Pricing**: [Instant GPU Clusters](https://www.together.ai/instant-gpu-clusters)
