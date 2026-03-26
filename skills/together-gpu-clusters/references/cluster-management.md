# GPU Cluster Management Reference
## Contents

- [Cluster Architecture](#cluster-architecture)
- [Access Methods](#access-methods)
- [Slurm Configuration](#slurm-configuration)
- [GPU Access in Containers](#gpu-access-in-containers)
- [Scaling](#scaling)
- [Storage](#storage)
- [Health Checks](#health-checks)
- [User Management](#user-management)
- [Billing](#billing)
- [Troubleshooting](#troubleshooting)
- [Terraform](#terraform)


## Cluster Architecture

### Kubernetes Mode
- **Control Plane** -- Manages cluster state, scheduling, API access
- **Worker Nodes** -- GPU-equipped nodes running workloads
- **Networking** -- High-speed InfiniBand for multi-node communication
- **Storage Layer** -- Persistent volumes, local NVMe, shared storage

### Slurm on Kubernetes (Slinky)
- **Slurm Controller** -- Runs as K8s pods, manages job queues
- **Login Nodes** -- SSH-accessible entry points
- **Compute Nodes** -- GPU workers registered with both K8s and Slurm

## Access Methods

### Kubernetes Access

```shell
# Get credentials
together beta clusters get-credentials <CLUSTER_ID>
export KUBECONFIG=$HOME/.kube/config

# Verify
kubectl get nodes
kubectl top nodes
kubectl get pods --all-namespaces
```

### Kubernetes Dashboard

Access the dashboard URL from the cluster UI. Retrieve the admin token:

```shell
kubectl -n kubernetes-dashboard get secret \
  $(kubectl -n kubernetes-dashboard get secret | grep admin-user-token | awk '{print $1}') \
  -o jsonpath='{.data.token}' | base64 -d | pbcopy
```

### SSH Access

SSH keys must be added at `api.together.ai/settings/ssh-key` before cluster creation.

```shell
# Direct SSH to worker nodes
ssh <node-hostname>.cloud.together.ai

# Slurm login node
ssh <username>@slurm-login
```

### Slurm Commands

```shell
sinfo                    # Node and partition status
squeue                   # Job queue
srun --gres=gpu:8 --pty bash  # Interactive GPU session
sbatch script.sh         # Submit batch job
scancel <jobid>          # Cancel job
scontrol show node       # Detailed node info
scontrol show job <jobid>  # Job details
```

## Slurm Configuration

Slurm clusters use four config files managed via a Kubernetes ConfigMap:

- **slurm.conf**: Main cluster configuration (nodes, partitions, scheduling)
- **gres.conf**: GPU and generic resource definitions
- **cgroup.conf**: Control group resource management
- **plugstack.conf**: SPANK plugin configuration

### Partition Configuration

```
PartitionName=gpu Nodes=gpu-nodes State=UP Default=NO MaxTime=24:00:00
PartitionName=cpu Nodes=cpu-nodes State=UP Default=YES
```

### GPU Resource Configuration

```
Name=gpu Type=h100 File=/dev/nvidia[0-7]
```

### Scheduler Tuning

```
SchedulerParameters=batch_sched_delay=10,bf_interval=180,sched_max_job_start=500
```

### Cgroup Settings

```
CgroupPlugin=cgroup/v1
ConstrainCores=yes
ConstrainRAMSpace=yes
```

Changes require restarting the Slurm controller via `kubectl rollout restart` and verifying
with `scontrol` and `sinfo`.

## GPU Access in Containers

GPU devices are exposed by the runtime to all containers, but CUDA support depends on the
container image. Use CUDA-enabled images like `pytorch/pytorch` or `nvidia/cuda`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-workload-pod
spec:
  restartPolicy: Never
  containers:
    - name: pytorch
      image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
      command: ["/bin/bash", "-c", "sleep infinity"]
      resources:
        limits:
          nvidia.com/gpu: 1
      volumeMounts:
        - name: shared-storage
          mountPath: /mnt/shared
  volumes:
    - name: shared-storage
      persistentVolumeClaim:
        claimName: shared-pvc
```

```shell
kubectl apply -f gpu-pod.yaml
kubectl wait --for=condition=Ready pod/gpu-workload-pod
kubectl exec -it gpu-workload-pod -- bash
nvidia-smi
```

## Scaling

### Real-time Scaling

Scale via UI, CLI, or API at any time. GPU count must be a multiple of 8.

```python
from together import Together
client = Together()

cluster = client.beta.clusters.update("cluster-id", num_gpus=16)
```

```shell
together beta clusters update <CLUSTER_ID> --num-gpus 16
```

### Autoscaling (Kubernetes)

Enable autoscaling during cluster creation in the UI. The Kubernetes Cluster Autoscaler:
- Scales up when pods are pending due to insufficient resources
- Scales down when nodes are underutilized
- Respects pod disruption budgets

### Targeted Scale-down

```shell
# Kubernetes -- cordon specific nodes
kubectl cordon <node_name>

# Slurm -- drain specific nodes
sudo scontrol update NodeName=<node_name> State=drain Reason="scaling down"
```

### Combining Capacity

Use reserved for baseline + on-demand for bursts.

## Storage

### Types

1. **Local NVMe** -- High-speed local I/O per node
2. **Shared /home** -- NFS-mounted across nodes (code, configs, logs)
3. **Shared Volumes** -- Multi-NIC, high-throughput persistent storage

### Kubernetes PVCs

**Shared storage (ReadWriteMany):**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-pvc
spec:
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 10Gi
  volumeName: <shared-volume-name>
```

**Local storage (ReadWriteOnce):**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi
  storageClassName: local-storage-class
```

```shell
kubectl apply -f shared-pvc.yaml -n default
kubectl apply -f local-pvc.yaml -n default
kubectl get pvc -A
```

### Pod with Volumes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  restartPolicy: Never
  containers:
    - name: ubuntu
      image: debian:stable-slim
      command: ["/bin/sh", "-c", "sleep infinity"]
      volumeMounts:
        - name: shared-storage
          mountPath: /mnt/shared
        - name: local-storage
          mountPath: /mnt/local
  volumes:
    - name: shared-storage
      persistentVolumeClaim:
        claimName: shared-pvc
    - name: local-storage
      persistentVolumeClaim:
        claimName: local-pvc
```

### Data Upload

```shell
# Small files
kubectl cp LOCAL_FILE POD_NAME:/data/

# Large datasets via S3
# Deploy a data-loader pod with aws-cli
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-loader
spec:
  containers:
    - name: downloader
      image: amazon/aws-cli
      command: ["aws", "s3", "cp", "s3://bucket/data", "/mnt/shared/", "--recursive"]
      volumeMounts:
        - name: shared-storage
          mountPath: /mnt/shared
  volumes:
    - name: shared-storage
      persistentVolumeClaim:
        claimName: shared-pvc
```

## Health Checks

### Automatic Acceptance Testing

During provisioning, nodes undergo automatic tests:
- **DCGM Diag (Level 2)** -- GPU compute, memory, thermal validation
- **GPU Burn (5 min)** -- stress test for thermal/power issues
- **Single-Node NCCL** -- GPU-to-GPU communication within a node
- **Multi-Node NCCL** -- cross-node GPU communication

Nodes showing "Tests Failed" are not added to the cluster until repaired.

### Available Health Check Tests

**GPU Diagnostics:**
- DCGM Diag (levels 1-3): NVIDIA Data Center GPU Manager diagnostics
- GPU Burn: intensive compute stress test

**Network Performance:**
- Single-Node NCCL: intra-node GPU communication
- InfiniBand Write Bandwidth: high-speed interconnect performance

**PCIe Performance:**
- NVBandwidth: CPU-to-GPU, GPU-to-CPU bandwidth, GPU-CPU latency

### Node Repair

- **Quick Reprovision**: VM recreated on a random physical node (for software issues)
- **Migrate to New Host**: New VM on different physical hardware (for hardware failures)

Repair lifecycle: Cordon -> Drain -> Reprovision/Migrate -> Rejoin

### Monitoring Commands

```shell
# Check GPU status
nvidia-smi

# Check for Xid errors
sudo dmesg | grep -i xid

# Check GPU memory errors
nvidia-smi -q | grep -i ecc

# Check temperature and throttling
nvidia-smi -q | grep -E 'Temperature|Throttle'

# Check PCIe link status
nvidia-smi -q | grep -E 'Link Width|Link Speed'

# Check running GPU processes
nvidia-smi pmon

# Kubernetes monitoring
kubectl get nodes
kubectl top nodes
kubectl get pvc

# Slurm monitoring
sinfo
squeue
scontrol show job <jobid>
```

## User Management

### Roles

| Role | Control Plane | Data Plane |
|------|--------------|------------|
| **Admin** | Full write (create/delete/scale clusters and volumes) | Full SSH and kubectl |
| **Member** | Read-only (view only) | SSH and kubectl access |

Only admins can add or remove users. Member permissions for in-cluster operations may vary
based on RBAC configuration.

### Managing Users

1. Navigate to Settings -> GPU Cluster Projects -> View Project
2. Add User (email) or Remove User
3. New users default to Member role; admins can promote afterward

Access is always project-wide -- all clusters in a project share the same access list.

Users require active Together AI accounts before they can be added.

## Billing

### Compute

- **Reserved**: Upfront payment, 1-90 days, discounted. Non-refundable, non-cancellable.
- **On-demand**: Hourly billing, no commitment. Can terminate anytime.
- **Hybrid**: Reserved for baseline + on-demand for burst.

### Storage

- Pay-per-TiB, billed independently of cluster lifecycle
- Persists across cluster creation/deletion
- Can expand freely; contact support to reduce

### Credit Exhaustion

- **Reserved compute**: Runs until end date; overflow capacity decommissioned
- **On-demand compute**: Paused first, then decommissioned if credits not restored
- **Storage**: Access revoked, then data decommissioned

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Cluster stuck provisioning | Check the status for phases like `WaitingForControlPlaneNodes` or `RunningAcceptanceTests` |
| 400 "cuda version and nvidia driver version are required" | Pass `cuda_version` and `nvidia_driver_version` as separate fields alongside `driver_version` |
| 409 "Out of stock" | GPUs unavailable in the requested region. Call `list_regions()` and try another region |
| "Shared volume does not exist in the datacenter" | Volume was created in a different datacenter partition. Use inline `shared_volume` at cluster creation instead of a separate `volume_id` |
| Pods not scheduling | Verify node readiness with `kubectl get nodes` and inspect resource requests and taints |
| GPU not accessible in container | Use a CUDA-enabled image such as `pytorch/pytorch` or `nvidia/cuda` |
| Storage PVC not binding | Confirm the volume name matches the shared volume and inspect `kubectl get pvc` |
| Slurm job failures | Run `sinfo` to inspect partitions and `scontrol show job <jobid>` for details |
| Node health issues | Check `nvidia-smi`, inspect Xid errors in `dmesg`, and trigger repair from the UI if needed |

## Terraform

```hcl
resource "together_gpu_cluster" "training" {
  name              = "training-cluster"
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
