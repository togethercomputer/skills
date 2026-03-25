---
name: together-batch-inference
description: "Use this skill for Together AI Batch API workflows: preparing JSONL inputs, uploading batch files, creating asynchronous jobs, polling status, downloading outputs, and optimizing large offline inference runs for lower cost. Reach for it whenever the user needs high-volume, non-interactive inference rather than real-time chat or evaluation jobs."
---

# Together Batch Inference

## Overview

Use Together AI's Batch API for large offline workloads where latency is not the primary concern.

Typical fits:

- bulk classification
- synthetic data generation
- dataset transformations
- large summarization or enrichment jobs
- low-cost asynchronous inference

## When This Skill Wins

- The user has many independent requests to run
- A JSONL request file is acceptable
- Turnaround time can be minutes or hours instead of seconds
- Lower cost matters more than immediate interactivity

## Hand Off To Another Skill

- Use `together-chat-completions` for real-time requests or tool-calling apps
- Use `together-evaluations` for managed LLM-as-a-judge workflows
- Use `together-embeddings` for retrieval-specific vector generation

## Quick Routing

- **End-to-end batch workflow**
  - Start with [scripts/batch_workflow.py](scripts/batch_workflow.py) or [scripts/batch_workflow.ts](scripts/batch_workflow.ts)
- **Request format, status model, and result downloads**
  - Read [references/api-reference.md](references/api-reference.md)
- **Operational guidance and batch sizing**
  - Read [references/api-reference.md](references/api-reference.md)

## Workflow

1. Build a JSONL file where each line contains `custom_id` and `body`.
2. Upload the file with `purpose="batch-api"`.
3. Create the batch with `input_file_id=...` and the target endpoint.
4. Poll until the job is terminal.
5. Download output and error files, then reconcile by `custom_id`.

## High-Signal Rules

- Use `input_file_id`, not legacy file parameters.
- Keep `custom_id` stable and meaningful so result reconciliation is easy.
- Batch is for independent requests. If the workload depends on shared conversation state, it is probably the wrong tool.
- Always inspect the error file in addition to the success output.

## Resource Map

- **API reference and operational guidance**: [references/api-reference.md](references/api-reference.md)
- **Python workflow**: [scripts/batch_workflow.py](scripts/batch_workflow.py)
- **TypeScript workflow**: [scripts/batch_workflow.ts](scripts/batch_workflow.ts)

## Official Docs

- [Batch Inference](https://docs.together.ai/docs/batch-inference)
- [Batch API](https://docs.together.ai/reference/batch-create)
