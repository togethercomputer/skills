---
name: together-volcano
description: Install and use the Volcano batch scheduler on a Together AI Kubernetes GPU cluster for gang scheduling. Covers installing Volcano, creating queues, submitting all-or-nothing gang-scheduled jobs (vcjobs), and verifying placement. Reach for it when a job on a Together cluster needs its pods scheduled all-at-once or not at all, such as distributed multi-node training, rather than per-pod best-effort scheduling. Pins Volcano v1.15.0.
---

# Volcano on Together GPU clusters

Volcano is a Kubernetes-native batch scheduler. Its key property is gang scheduling: a group of pods is placed all-at-once or not at all, so distributed training never starts with only some workers running. Use it when a job needs N pods to run together or not at all.

Public cookbook: https://docs.together.ai/docs/volcano-on-gpu-clusters. Pair this skill with the `together-gpu-clusters` skill, which covers creating the cluster and configuring `kubectl`.

## Preconditions

- A Together Kubernetes GPU cluster in the `Ready` state, with `kubectl` pointed at it (`tg beta clusters get-credentials <cluster_id> --set-default-context`).
- GPU nodes expose `nvidia.com/gpu`; the NVIDIA device plugin is preinstalled on Together clusters. Confirm with:

```bash
kubectl get nodes -o custom-columns='NODE:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
```

## Install

Pin the version. Do not use `master`.

```bash
kubectl apply -f https://raw.githubusercontent.com/volcano-sh/volcano/v1.15.0/installer/volcano-development.yaml
kubectl -n volcano-system wait --for=condition=Available deployment --all --timeout=180s
```

A `default` queue is created automatically (`kubectl get queue`). Helm is an alternative: `helm repo add volcano-sh https://volcano-sh.github.io/helm-charts && helm install volcano volcano-sh/volcano -n volcano-system --create-namespace`.

## Create a queue

A queue caps and weights the resources a set of jobs can use.

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata:
  name: research
spec:
  reclaimable: true          # give idle capacity back to other queues
  weight: 1                  # relative share under contention
  capability:                # hard ceiling for this queue
    nvidia.com/gpu: 8
```

## Run a gang-scheduled job

The gang guarantee comes from `minAvailable` on a Volcano `Job` (`vcjob`). Set `schedulerName: volcano` and a `queue`.

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: gpu-gang
spec:
  minAvailable: 4            # schedule all 4 pods together or none
  schedulerName: volcano
  queue: research
  policies:
    - event: PodEvicted
      action: RestartJob     # restart the whole gang if a pod is evicted
  tasks:
    - replicas: 4
      name: worker
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: worker
              image: nvidia/cuda:12.4.0-base-ubuntu22.04
              command: ["bash", "-c", "nvidia-smi -L; sleep 300"]
              resources:
                limits:
                  nvidia.com/gpu: 2   # 4 x 2 = 8 GPUs
```

## Verify

- `kubectl get vcjob <name>` should show `STATUS Running` and `RUNNINGS` equal to `minAvailable`.
- `kubectl get podgroup` shows the gang; a `Running` phase means the whole group is placed.
- A gang that cannot fit stays `Inqueue` with **zero** pods running (all-or-nothing). This is the signal Volcano is working, not a failure. Never "fix" it by lowering `minAvailable` below the job's real parallelism.

## Rules and gotchas

- Always pin the Volcano version in the install URL.
- `schedulerName: volcano` must be on the pod template (on a `vcjob` it goes under `spec`). Without it, the default scheduler grabs the pods and there is no gang guarantee.
- A job whose total request exceeds the queue's `capability` is rejected. Raise the cap or split the job.
- To gang-schedule non-vcjob workloads (for example MPIJobs from the preinstalled MPI Operator), set `schedulerName: volcano` and attach a `PodGroup`. See https://volcano.sh/en/docs/podgroup/.
- Volcano and Kueue can coexist on one cluster: Volcano owns pods with `schedulerName: volcano`; Kueue admits jobs on the default scheduler. Pick one per workload; do not point a single job at both.

## Reference

- Volcano docs: https://volcano.sh/en/docs/
- Installation: https://volcano.sh/en/docs/installation/
- Gang scheduling: https://volcano.sh/en/docs/gang_scheduling/
- Queue: https://volcano.sh/en/docs/queue/
- vcjob: https://volcano.sh/en/docs/vcjob/
