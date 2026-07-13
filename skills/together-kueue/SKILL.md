---
name: together-kueue
description: Install and use the Kueue job-queueing controller on a Together AI Kubernetes GPU cluster to gate jobs on quota. Covers installing Kueue, defining ResourceFlavor, ClusterQueue, and LocalQueue quota, submitting jobs to a queue, and watching quota admit or suspend them. Reach for it when a Together cluster's GPU pool must be shared across teams or workloads by quota, admitting jobs only when capacity is free, rather than letting every job start immediately. Pins Kueue v0.18.3 (API kueue.x-k8s.io/v1beta2).
---

# Kueue on Together GPU clusters

Kueue is a Kubernetes-native job queueing controller. It holds jobs in a queue and admits them only when their quota is free, suspending the rest. Use it to share a fixed GPU pool across teams or workloads without overcommitting it. Unlike Volcano, Kueue does not replace the scheduler; it gates when jobs start by toggling their `suspend` flag.

Public cookbook: https://docs.together.ai/docs/kueue-on-gpu-clusters. Pair this skill with the `together-gpu-clusters` skill, which covers creating the cluster and configuring `kubectl`.

## Preconditions

- A Together Kubernetes GPU cluster in the `Ready` state, with `kubectl` pointed at it (`tg beta clusters get-credentials <cluster_id> --set-default-context`).
- GPU nodes expose `nvidia.com/gpu` (NVIDIA device plugin preinstalled on Together clusters).

## Install

Pin the version. The API group is `kueue.x-k8s.io/v1beta2` in v0.18.x; older examples using `v1beta1` will not apply.

```bash
kubectl apply --server-side -f https://github.com/kubernetes-sigs/kueue/releases/download/v0.18.3/manifests.yaml
kubectl -n kueue-system wait --for=condition=Available deployment/kueue-controller-manager --timeout=240s
```

`--server-side` is required; the bundled CRDs exceed the client-side apply annotation limit. Helm is an alternative: `helm install kueue oci://registry.k8s.io/kueue/charts/kueue --version 0.18.3 --namespace kueue-system --create-namespace`.

## Define quotas

Three objects: `ResourceFlavor` (a node class), `ClusterQueue` (the quota pool), and `LocalQueue` (the namespaced entry point users submit to).

```yaml
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: gpu-flavor
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: gpu-cluster-queue
spec:
  namespaceSelector: {}            # accept jobs from every namespace
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]  # MUST list every resource jobs request
      flavors:
        - name: gpu-flavor         # must match the ResourceFlavor
          resources:
            - name: "cpu"
              nominalQuota: 64
            - name: "memory"
              nominalQuota: 512Gi
            - name: "nvidia.com/gpu"
              nominalQuota: 8       # admit at most 8 GPUs worth of jobs at once
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  namespace: default
  name: gpu-queue
spec:
  clusterQueue: gpu-cluster-queue
```

## Submit a job to a queue

Add the queue-name label and start the job suspended. Kueue flips `suspend` to `false` on admission.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: gpu-job
  namespace: default
  labels:
    kueue.x-k8s.io/queue-name: gpu-queue   # route to the LocalQueue
spec:
  parallelism: 1
  completions: 1
  suspend: true                            # Kueue unsuspends on admission
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: worker
          image: nvidia/cuda:12.4.0-base-ubuntu22.04
          command: ["bash", "-c", "nvidia-smi -L; sleep 180"]
          resources:
            requests:
              cpu: "2"
              memory: "8Gi"
            limits:
              nvidia.com/gpu: 6
```

## Verify

- `kubectl get workloads` shows `ADMITTED True` once the job fits.
- An over-quota job stays `suspend: true` with no pod. This is correct queueing, not a failure. Read the reason:

```bash
WORKLOAD=$(kubectl get workloads -o name | grep <job-name>)
kubectl get "$WORKLOAD" -o jsonpath='{.status.conditions[?(@.type=="QuotaReserved")].message}'
```

- Freeing quota (a running job finishes or is deleted) auto-admits the next queued job. Do not resubmit.

## Rules and gotchas

- Pin the version, and use API `kueue.x-k8s.io/v1beta2` for v0.18.x.
- The ClusterQueue's `coveredResources` MUST include every resource a job requests. A GPU job that also requests CPU and memory is never admitted if the ClusterQueue only covers `nvidia.com/gpu`. This is the most common failure.
- `flavors[].name` must exactly match a `ResourceFlavor` name, or the ClusterQueue admits nothing.
- The `kueue.x-k8s.io/queue-name` label must name a `LocalQueue` in the job's own namespace. A missing or wrong label means the job runs immediately, bypassing quota.
- Volcano and Kueue can coexist: Kueue gates jobs on the default scheduler; Volcano owns pods with `schedulerName: volcano`. Do not point one job at both.

## Reference

- Kueue docs: https://kueue.sigs.k8s.io/docs/
- Installation: https://kueue.sigs.k8s.io/docs/installation/
- Concepts (ResourceFlavor, ClusterQueue, LocalQueue, Workload): https://kueue.sigs.k8s.io/docs/concepts/
- Running jobs (Job, JobSet, RayJob, MPIJob): https://kueue.sigs.k8s.io/docs/tasks/run/jobs/
