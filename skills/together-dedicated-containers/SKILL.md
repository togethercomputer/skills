---
name: together-dedicated-containers
description: "Custom Dockerized inference workers on Together AI's managed GPU infrastructure. Build with Sprocket SDK, configure with Jig CLI, submit async queue jobs, and poll results. Reach for it whenever the user needs container-level control rather than a standard model endpoint or raw cluster."
---

# Together Dedicated Containers

## Overview

Use Dedicated Container Inference when the user needs a custom runtime, not just managed model
hosting.

Core building blocks:

- **Jig CLI** for build and deployment
- **Sprocket SDK** for request handling inside the container
- **Queue API** for async jobs

## When This Skill Wins

- Deploy a custom inference worker
- Bundle custom dependencies or runtime logic into a container
- Use queue-based async processing with progress tracking
- Run a specialized image, video, or multimodal pipeline

## Hand Off To Another Skill

- Use `together-dedicated-endpoints` for standard model hosting without custom containers
- Use `together-gpu-clusters` for full cluster ownership and orchestration control
- Use `together-chat-completions`, `together-images`, or `together-video` when a serverless product already covers the task

## Quick Routing

- **Minimal worker template**
  - Start with [scripts/sprocket_hello_world.py](scripts/sprocket_hello_world.py)
  - Read [references/sprocket-sdk.md](references/sprocket-sdk.md)
- **Build, deploy, logs, queue, and secrets**
  - Read [references/jig-cli.md](references/jig-cli.md)
- **Queue submission and polling**
  - Start with [scripts/queue_client.py](scripts/queue_client.py) or [scripts/queue_client.ts](scripts/queue_client.ts)

## Workflow

1. Confirm that the user truly needs a custom container runtime.
2. Implement the worker with Sprocket's request lifecycle.
3. Configure `pyproject.toml` for image, runtime, autoscaling, and mounts.
4. Deploy with Jig.
5. Submit jobs through the queue API and poll until completion.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Prefer dedicated endpoints over containers unless the runtime or pipeline is genuinely custom.
- Treat the worker contract and `pyproject.toml` as the source of truth for deployment behavior.
- Parameterize deployment name, queue inputs, and resource sizing instead of hardcoding them.
- Queue-based jobs are asynchronous by default; account for polling and result retrieval in client code.

## Resource Map

- **Jig CLI**: [references/jig-cli.md](references/jig-cli.md)
- **Sprocket SDK**: [references/sprocket-sdk.md](references/sprocket-sdk.md)
- **Python queue client**: [scripts/queue_client.py](scripts/queue_client.py)
- **TypeScript queue client**: [scripts/queue_client.ts](scripts/queue_client.ts)
- **Worker template**: [scripts/sprocket_hello_world.py](scripts/sprocket_hello_world.py)

## Official Docs

- [Dedicated Container Inference](https://docs.together.ai/docs/dedicated-container-inference)
- [Containers Quickstart](https://docs.together.ai/docs/containers-quickstart)
- [Deployments API](https://docs.together.ai/reference/deployments-create)
