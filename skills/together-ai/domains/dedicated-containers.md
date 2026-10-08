# Together AI: Dedicated Containers

Run your own Docker image as an inference worker on Together GPUs: Sprocket handles the request
lifecycle, Jig builds and deploys, and clients submit async jobs to a queue. Choose this only when
the runtime is genuinely custom; a standard model belongs on
`domains/dedicated-model-inference.md`.

## Workflow

1. Confirm a custom runtime is required.
2. Implement the worker with Sprocket (`setup` once, `predict` per request).
3. Configure image, runtime, autoscaling, and mounts in `pyproject.toml`.
4. Build and deploy with `jig`.
5. Submit jobs to the queue and poll each to completion; tear down the deployment when done.

## Rules

- `pyproject.toml` is the source of truth for deployment behavior.
- Queue jobs are asynchronous; client code must poll and fetch results.
- Deployments bill while running; scale down or delete what you create.
- Parameterize deployment name, inputs, and resource sizing.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/dedicated-containers/sprocket_hello_world.py](scripts/dedicated-containers/sprocket_hello_world.py) | 85 | minimal Sprocket worker | writing a worker |
| [scripts/dedicated-containers/queue_client.py](scripts/dedicated-containers/queue_client.py) (.ts) | 109 | submit a job, poll, fetch the result | calling a deployed worker |
| [references/dedicated-containers/sprocket-sdk.md](references/dedicated-containers/sprocket-sdk.md) | 189 | Sprocket base class, `run`, file outputs, HTTP endpoints, env vars | a worker API detail |
| [references/dedicated-containers/jig-cli.md](references/dedicated-containers/jig-cli.md) | 526 | build, deploy, queue, secrets, volumes commands; `pyproject.toml` schema; full example | deploying or configuring |

## Docs

- [Dedicated Container Inference](https://docs.together.ai/docs/dedicated-container-inference)
- [Containers Quickstart](https://docs.together.ai/docs/containers-quickstart)
- [Deployments API](https://docs.together.ai/reference/deployments-create)
