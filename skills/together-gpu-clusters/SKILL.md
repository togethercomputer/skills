---
name: together-gpu-clusters
description: "Use this skill for Together AI GPU clusters and raw infrastructure workflows: provisioning on-demand or reserved clusters, choosing Kubernetes vs Slurm, attaching shared storage, scaling, getting credentials, and operating cluster-backed ML or HPC jobs. Reach for it when the user needs multi-node compute or infrastructure control rather than a managed model endpoint."
---

# Together GPU Clusters

## Overview

Use Together AI GPU clusters when the user needs infrastructure control instead of a managed
inference product.

Typical fits:

- distributed training
- multi-node inference
- HPC or Slurm workloads
- custom Kubernetes jobs
- attached shared storage and cluster lifecycle management

## When This Skill Wins

- Provision a cluster and manage it over time
- Choose between on-demand and reserved capacity
- Choose Kubernetes or Slurm as the orchestration layer
- Manage shared volumes and credentials
- Scale up, scale down, or troubleshoot node health

## Hand Off To Another Skill

- Use `together-dedicated-endpoints` for managed single-model hosting
- Use `together-dedicated-containers` for containerized inference without owning the full cluster
- Use `together-sandboxes` for short-lived remote Python execution
- Use `together-fine-tuning` for managed training jobs instead of raw cluster operations

## Quick Routing

- **Cluster creation, scaling, credentials, deletion**
  - Start with [scripts/manage_cluster.py](scripts/manage_cluster.py) or [scripts/manage_cluster.ts](scripts/manage_cluster.ts)
  - Read [references/api-reference.md](references/api-reference.md)
- **Shared storage lifecycle**
  - Use [scripts/manage_storage.py](scripts/manage_storage.py)
  - Read [references/api-reference.md](references/api-reference.md)
- **Kubernetes vs Slurm operations**
  - Read [references/cluster-management.md](references/cluster-management.md)
- **Troubleshooting node health, PVCs, or scheduling**
  - Read [references/cluster-management.md](references/cluster-management.md)
- **tcloud CLI workflows**
  - Read [references/tcloud-cli.md](references/tcloud-cli.md)

## Workflow

1. Decide whether the workload really needs cluster-level control.
2. Choose on-demand vs reserved billing based on run duration and baseline utilization.
3. Choose Kubernetes vs Slurm based on orchestration requirements and team tooling.
4. Select region, GPU type, driver version, and shared storage plan.
5. Provision first, then layer in access credentials, workload deployment, scaling, and health checks.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Prefer managed products unless the user explicitly needs raw infrastructure control.
- Treat storage lifecycle separately from cluster lifecycle; volumes can outlive clusters.
- When creating a cluster with new shared storage, prefer inline `shared_volume` over creating a volume separately and attaching via `volume_id`. Separately created volumes may land in a different datacenter partition than the cluster, causing a "does not exist in the datacenter" error even when the volume shows as available.
- GPU stock-outs (409 "Out of stock") are common. Always call `list_regions()` first and be prepared to try multiple regions.
- The API requires `cuda_version` and `nvidia_driver_version` as separate fields in addition to the combined `driver_version` string. Pass them via `extra_body` in the Python SDK.
- Credentials retrieval is part of provisioning. Do not stop at cluster creation if the user needs to run workloads immediately.
- Slurm and Kubernetes operational patterns differ materially; read the cluster-management reference before improvising.
- For repeated cluster operations, start from the scripts instead of rebuilding request shapes.

## Resource Map

- **Cluster API reference**: [references/api-reference.md](references/api-reference.md)
- **Operational guide**: [references/cluster-management.md](references/cluster-management.md)
- **Operational troubleshooting**: [references/cluster-management.md](references/cluster-management.md)
- **CLI guide**: [references/tcloud-cli.md](references/tcloud-cli.md)
- **Python cluster management**: [scripts/manage_cluster.py](scripts/manage_cluster.py)
- **TypeScript cluster management**: [scripts/manage_cluster.ts](scripts/manage_cluster.ts)
- **Python storage management**: [scripts/manage_storage.py](scripts/manage_storage.py)

## Official Docs

- [GPU Clusters Overview](https://docs.together.ai/docs/gpu-clusters-overview)
- [GPU Clusters Quickstart](https://docs.together.ai/docs/gpu-clusters-quickstart)
- [Clusters API](https://docs.together.ai/reference/clusters-create)
- [Instant GPU Clusters](https://www.together.ai/instant-gpu-clusters)
