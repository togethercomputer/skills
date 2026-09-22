# Together AI: GPU Clusters

Use Together AI GPU clusters when the user needs infrastructure control instead of a managed
inference product.

Typical fits:

- distributed training
- multi-node inference
- HPC or Slurm workloads
- custom Kubernetes jobs
- attached shared storage and cluster lifecycle management

## Use this guide for

- Provision a cluster and manage it over time
- Choose between on-demand and reserved capacity
- Choose Kubernetes or Slurm as the orchestration layer
- Manage shared volumes and credentials
- Scale up, scale down, or troubleshoot node health

## Do not use this guide for

- managed single-model hosting -> `domains/dedicated-model-inference.md`
- containerized inference without owning the full cluster -> `domains/dedicated-containers.md`
- short-lived remote Python execution -> `domains/sandboxes.md`
- managed training jobs instead of raw cluster operations -> `domains/fine-tuning.md`

## Workflow

1. Decide whether the workload really needs cluster-level control.
2. Choose on-demand vs reserved billing based on run duration and baseline utilization.
3. Choose Kubernetes vs Slurm based on orchestration requirements and team tooling.
4. Select region, GPU type, driver version, and shared storage plan.
5. Provision first, then layer in access credentials, workload deployment, scaling, and health checks.

## Open next

- **Current regions, instance types, pricing, or a non-creating command plan**
  - Read [references/gpu-clusters/pricing-and-discovery.md](references/gpu-clusters/pricing-and-discovery.md)
  - Query the live regions endpoint, then compare only the matching numeric rates
    on the official pricing table
- **Cluster creation, scaling, credentials, deletion**
  - Start with [scripts/gpu-clusters/manage_cluster.py](scripts/gpu-clusters/manage_cluster.py) or [scripts/gpu-clusters/manage_cluster.ts](scripts/gpu-clusters/manage_cluster.ts)
  - Read [references/gpu-clusters/api-reference.md](references/gpu-clusters/api-reference.md)
- **Shared storage lifecycle**
  - Use [scripts/gpu-clusters/manage_storage.py](scripts/gpu-clusters/manage_storage.py)
  - Read [references/gpu-clusters/api-reference.md](references/gpu-clusters/api-reference.md)
- **Kubernetes vs Slurm operations**
  - Read [references/gpu-clusters/cluster-management.md](references/gpu-clusters/cluster-management.md)
- **Troubleshooting node health, PVCs, or scheduling**
  - Read [references/gpu-clusters/cluster-management.md](references/gpu-clusters/cluster-management.md)
- **Together CLI workflows**
  - Read [references/gpu-clusters/cli.md](references/gpu-clusters/cli.md)

## Rules

- Prefer managed products unless the user explicitly needs raw infrastructure control.
- Treat storage lifecycle separately from cluster lifecycle; volumes can outlive clusters.
- When creating a cluster with new shared storage, prefer inline `shared_volume` over creating a volume separately and attaching via `volume_id`. Separately created volumes may land in a different datacenter partition than the cluster, causing a "does not exist in the datacenter" error even when the volume shows as available.
- GPU stock-outs (409 "Out of stock") are common. Always call `list_regions()` first and be prepared to try multiple regions.
- The regions response reports supported configurations, not prices or
  guaranteed stock. Never infer the cheapest GPU from response order or
  hardware generation; open the [GPU Cluster pricing table](https://www.together.ai/pricing#gpu-clusters)
  and compare its numeric on-demand rates.
- GPU clusters have an 8-GPU minimum. For an hourly estimate, multiply the displayed per-GPU-hour rate by at least 8.
- `ON_DEMAND` has no one-hour duration flag. For a one-hour plan, omit
  `--duration-days`, create the cluster only when authorized, then delete it
  after the intended runtime. If the user requests a command without
  provisioning, print it but do not run it.
- The API requires `cuda_version` and `nvidia_driver_version` as separate fields in addition to the combined `driver_version` string. Pass them via `extra_body` in the Python SDK.
- Credentials retrieval is part of provisioning. Do not stop at cluster creation if the user needs to run workloads immediately.
- Slurm and Kubernetes operational patterns differ materially; read the cluster-management reference before improvising.
- For repeated cluster operations, start from the scripts instead of rebuilding request shapes.
- Slurm startup scripts (worker/login init, worker/controller prolog and epilog, extra `slurm.conf`) are **Slinky v1.0 only**. A non-zero exit from a worker prolog or epilog drains the node, and calling Slurm commands (`squeue`, `scontrol`, `sacctmgr`) inside any prolog/epilog can deadlock the scheduler.

## Docs

- [GPU Clusters Overview](https://docs.together.ai/docs/gpu-clusters-overview)
- [GPU Clusters Quickstart](https://docs.together.ai/docs/gpu-clusters-quickstart)
- [Clusters API](https://docs.together.ai/reference/clusters-create)
- [GPU Cluster Pricing](https://www.together.ai/pricing#gpu-clusters)
- [Slurm Startup Scripts](https://docs.together.ai/docs/slurm-startup-scripts)
- [Instant GPU Clusters](https://www.together.ai/instant-gpu-clusters)
