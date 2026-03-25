---
name: together-dedicated-endpoints
description: Use this skill for Together AI dedicated endpoint workflows: selecting dedicated-eligible models, sizing hardware, creating single-tenant endpoints, deploying fine-tuned or uploaded models, autoscaling, and managing endpoint lifecycle. Reach for it whenever the user needs predictable always-on hosting rather than serverless inference, custom containers, or raw clusters.
---

# Together Dedicated Endpoints

## Overview

Use dedicated endpoints for managed single-tenant model hosting with predictable performance and
no shared serverless pool.

Typical fits:

- production inference with stable latency
- fine-tuned model hosting
- uploaded custom model hosting
- autoscaled model APIs

## When This Skill Wins

- The user needs always-on or single-tenant hosting
- The model is supported for dedicated deployment
- Fine-tuned or uploaded models must be served as endpoints
- Hardware, scaling, or idle-time settings need explicit control

## Hand Off To Another Skill

- Use `together-chat-completions` for serverless chat inference
- Use `together-dedicated-containers` for custom runtimes or nonstandard inference pipelines
- Use `together-gpu-clusters` for raw infrastructure or cluster orchestration

## Quick Routing

- **Create and manage a standard endpoint**
  - Start with [scripts/manage_endpoint.py](scripts/manage_endpoint.py) or [scripts/manage_endpoint.ts](scripts/manage_endpoint.ts)
  - Read [references/api-reference.md](references/api-reference.md)
- **Lifecycle tuning or troubleshooting**
  - Read [references/api-reference.md](references/api-reference.md)
- **Deploy a fine-tuned model**
  - Start with [scripts/deploy_finetuned.py](scripts/deploy_finetuned.py)
  - Read [references/dedicated-models.md](references/dedicated-models.md)
- **Upload and deploy a custom model**
  - Start with [scripts/upload_custom_model.py](scripts/upload_custom_model.py)
  - Read [references/dedicated-models.md](references/dedicated-models.md)
- **Hardware and sizing choices**
  - Read [references/hardware-options.md](references/hardware-options.md)

## Workflow

1. Confirm that the task needs dedicated hosting instead of serverless or containers.
2. Verify model eligibility and inspect available hardware.
3. Create the endpoint with explicit scaling and timeout settings.
4. Wait for readiness before sending inference traffic.
5. Stop or delete the endpoint when the workload no longer needs to run.

## High-Signal Rules

- Model eligibility and hardware availability are gating constraints; check them early.
- Endpoint management uses endpoint IDs, while inference usually uses the endpoint name as `model`.
- Autoscaling, auto-shutdown, prompt caching, and speculative decoding materially affect operations and cost.
- For custom or fine-tuned models, do not skip the intermediate verification steps before deployment.

## Resource Map

- **API reference**: [references/api-reference.md](references/api-reference.md)
- **Operational controls and troubleshooting**: [references/api-reference.md](references/api-reference.md)
- **Dedicated model guide**: [references/dedicated-models.md](references/dedicated-models.md)
- **Hardware guide**: [references/hardware-options.md](references/hardware-options.md)
- **Python endpoint lifecycle**: [scripts/manage_endpoint.py](scripts/manage_endpoint.py)
- **TypeScript endpoint lifecycle**: [scripts/manage_endpoint.ts](scripts/manage_endpoint.ts)
- **Fine-tuned deployment**: [scripts/deploy_finetuned.py](scripts/deploy_finetuned.py)
- **Custom model upload and deployment**: [scripts/upload_custom_model.py](scripts/upload_custom_model.py)

## Official Docs

- [Dedicated Endpoints](https://docs.together.ai/docs/dedicated-inference)
- [Endpoints API](https://docs.together.ai/reference/createendpoint)
- [Upload and Deploy Custom Models](https://docs.together.ai/docs/custom-models)
