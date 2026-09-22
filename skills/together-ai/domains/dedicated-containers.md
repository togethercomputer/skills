# Together AI: Dedicated Containers

Use Dedicated Container Inference when the user needs a custom runtime, not just managed model
hosting.

Core building blocks:

- **Jig CLI** for build and deployment
- **Sprocket SDK** for request handling inside the container
- **Queue API** for async jobs

## Use this guide for

- Deploy a custom inference worker
- Bundle custom dependencies or runtime logic into a container
- Use queue-based async processing with progress tracking
- Run a specialized image, video, or multimodal pipeline

## Do not use this guide for

- standard model hosting without custom containers -> `domains/dedicated-model-inference.md`
- full cluster ownership and orchestration control -> `domains/gpu-clusters.md`
- `domains/chat-completions.md`, `domains/images.md`, or `domains/video.md` when a serverless product already covers the task

## Workflow

1. Confirm that the user truly needs a custom container runtime.
2. Implement the worker with Sprocket's request lifecycle.
3. Configure `pyproject.toml` for image, runtime, autoscaling, and mounts.
4. Deploy with Jig.
5. Submit jobs through the queue API and poll until completion.

## Open next

- **Minimal worker template**
  - Start with [scripts/dedicated-containers/sprocket_hello_world.py](scripts/dedicated-containers/sprocket_hello_world.py)
  - Read [references/dedicated-containers/sprocket-sdk.md](references/dedicated-containers/sprocket-sdk.md)
- **Build, deploy, logs, queue, and secrets**
  - Read [references/dedicated-containers/jig-cli.md](references/dedicated-containers/jig-cli.md)
- **Queue submission and polling**
  - Start with [scripts/dedicated-containers/queue_client.py](scripts/dedicated-containers/queue_client.py) or [scripts/dedicated-containers/queue_client.ts](scripts/dedicated-containers/queue_client.ts)

## Rules

- Prefer dedicated endpoints over containers unless the runtime or pipeline is genuinely custom.
- Treat the worker contract and `pyproject.toml` as the source of truth for deployment behavior.
- Parameterize deployment name, queue inputs, and resource sizing instead of hardcoding them.
- Queue-based jobs are asynchronous by default; account for polling and result retrieval in client code.

## Docs

- [Dedicated Container Inference](https://docs.together.ai/docs/dedicated-container-inference)
- [Containers Quickstart](https://docs.together.ai/docs/containers-quickstart)
- [Deployments API](https://docs.together.ai/reference/deployments-create)
