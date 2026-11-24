# Together AI: GPU Clusters

GPU clusters (H100, H200, B200, B300, and other types; availability varies by region) with
Kubernetes or Slurm, shared storage, and credentials, for distributed training, multi-node
inference, and HPC. Sizes are multiples of 8 GPUs. `ON_DEMAND` bills from creation until you
delete the cluster; `RESERVED` is charged for the full reserved term. Shared storage bills
separately and keeps billing after the cluster is deleted.

This skill uses `tg clusters ...` and `client.clusters`, which work from SDK and CLI 2.40. The
`tg beta clusters` and `client.beta.clusters` aliases were removed in 3.0 (2026-10-22); on an
older SDK, upgrade rather than switching to them.

Hand-offs: serving a model is `domains/dedicated-model-inference.md`; a custom inference container
is `domains/dedicated-containers.md`; short remote Python is `domains/sandboxes.md`; queueing or
gang scheduling on a running cluster is `domains/kueue.md` or `domains/volcano.md`.

## Workflow

1. Decide whether the workload really needs cluster-level control.
2. Choose on-demand vs reserved billing based on run duration and baseline utilization. Add
   preemptible capacity when the workload can checkpoint and tolerate a five-minute reclaim.
3. Choose Kubernetes vs Slurm based on orchestration requirements and team tooling.
4. Select region, GPU type, driver version, and shared storage plan.
5. Provision first, then layer in access credentials, workload deployment, scaling, and health checks.

## Rules

- Prefer managed products unless the user explicitly needs raw infrastructure control.
- Treat storage lifecycle separately from cluster lifecycle; volumes can outlive clusters.
- When creating a cluster with new shared storage, prefer inline `shared_volume` over creating a volume separately and attaching via `volume_id`. Separately created volumes may land in a different datacenter partition than the cluster, causing a "does not exist in the datacenter" error even when the volume shows as available.
- GPU stock-outs (409 "Out of stock") are common. Always call `list_regions()` first and be prepared to try multiple regions.
- The regions response reports supported configurations, not prices or
  guaranteed stock. Never infer the cheapest GPU from response order or
  hardware generation; open the [GPU Cluster pricing table](https://www.together.ai/pricing#gpu-clusters)
  and compare its numeric on-demand rates.
- Standard GPU count (`num_gpus` / `--num-gpus`) is a multiple of 8 and may be `0` for a
  preemptible-only cluster. Preemptible targets (`num_preemptible_gpus` /
  `--num-preemptible-gpus`) are also multiples of 8. At least one of those counts must be greater
  than 0. For an hourly estimate of standard on-demand capacity, multiply the displayed
  per-GPU-hour rate by at least 8.
- Preemptible compute is generally available on Kubernetes and Slurm. Set
  `num_preemptible_gpus` / `--num-preemptible-gpus` (requires a project) to add discounted,
  interruptible nodes, or pass `num_gpus` / `--num-gpus` `0` for a preemptible-only cluster.
  Together can reclaim preemptible nodes after a five-minute drain; the cluster and shared
  volumes stay. On Kubernetes, target interruptible pods with
  `together.ai/compute-class=preemptible` (and keep coordinators on `non-preemptible`). Slurm
  cannot pin jobs away from preemptible nodes; use `--requeue` and shared-storage checkpoints.
- Every create request needs a shared volume, and the API rejects one without it. Pass `--shared-volume-name` with `--shared-volume-size-tib` (CLI 3.2.0+) or `shared_volume` (SDK) to create one with the cluster, or `--volume` / `volume_id` to attach an existing one.
- `ON_DEMAND` has no one-hour duration flag. For a one-hour plan, omit
  `--duration-days`, create the cluster only when authorized, then delete it
  after the intended runtime. If the user requests a command without
  provisioning, print it but do not run it.
- Set the driver with `nvidia_version_id` (`--nvidia-version-id`, a driver version's `id` from `list_regions()`), or with `cuda_version` plus `nvidia_driver_version` from the same entry. A bare pair selects `ubuntu-22.04`, so for an entry with another `os` use its `id` (or add `--os` in the CLI). They are ordinary SDK arguments and CLI flags; there is no `driver_version` argument or `--driver-version` flag.
- Credentials retrieval is part of provisioning. Do not stop at cluster creation if the user needs to run workloads immediately.
- Slurm startup scripts (worker/login init, worker/controller prolog and epilog, extra `slurm.conf`) are **Slinky v1.0 only**. A non-zero exit from a worker prolog or epilog drains the node, and calling Slurm commands (`squeue`, `scontrol`, `sacctmgr`) inside any prolog/epilog can deadlock the scheduler.

## Open next

For read-only questions (regions, GPU types, prices, a command to run later), the 117-line
`pricing-and-discovery.md` is all you need. Open the others only for the detail in their row, and
read just that section; long ones start with `## Contents`.

| File | Lines | Contains | Open when |
|---|---|---|---|
| [references/gpu-clusters/pricing-and-discovery.md](references/gpu-clusters/pricing-and-discovery.md) | 117 | pricing, billing (including preemptible), and stock surfaces, read-only inventory commands, picking the cheapest live option, one-hour on-demand plan with its shared volume | pricing, availability, or a plan without provisioning |
| [scripts/gpu-clusters/manage_cluster.py](scripts/gpu-clusters/manage_cluster.py) (.ts) | 330 | create (requires `--shared-volume-name` with `--shared-volume-size-tib`, or `--volume-id`; takes the driver from the region's list unless you pass `--nvidia-version-id` or `--driver-version`), poll, scale, delete | provisioning or changing a cluster |
| [scripts/gpu-clusters/manage_storage.py](scripts/gpu-clusters/manage_storage.py) | 129 | create, list, resize, delete shared volumes | managing storage on its own |
| [references/gpu-clusters/cli.md](references/gpu-clusters/cli.md) | 365 | `tg` cluster and storage commands, create flags (`--nvidia-version-id`, `--os`, `--num-preemptible-gpus`, shared-volume flags), global flags, instance types, driver versions | a CLI flag or driver version |
| [references/gpu-clusters/api-reference.md](references/gpu-clusters/api-reference.md) | 484 | cluster and storage endpoints, request fields (`num_preemptible_gpus`), regions, instance types | an API field the script does not set |
| [references/gpu-clusters/cluster-management.md](references/gpu-clusters/cluster-management.md) | 602 | architecture, access, Slurm config, GPU containers, scaling, preemptible compute, storage, health checks, users, billing, troubleshooting, Terraform | operating or debugging a running cluster |

## Docs

- [GPU Clusters Overview](https://docs.together.ai/docs/gpu-clusters-overview)
- [GPU Clusters Quickstart](https://docs.together.ai/docs/gpu-clusters-quickstart)
- [Clusters API](https://docs.together.ai/reference/clusters-create)
- [GPU Cluster Pricing](https://www.together.ai/pricing#gpu-clusters) (rates)
- [GPU Clusters Billing](https://docs.together.ai/docs/gpu-clusters-billing) (billing rules)
- [Preemptible compute](https://docs.together.ai/docs/preemptible-compute)
- [Slurm Startup Scripts](https://docs.together.ai/docs/slurm-startup-scripts)
- [Instant GPU Clusters](https://www.together.ai/instant-gpu-clusters)
