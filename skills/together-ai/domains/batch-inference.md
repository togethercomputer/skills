# Together AI: Batch Inference

Use Together AI's Batch API for large offline workloads where latency is not the primary concern.

Typical fits:

- bulk classification
- synthetic data generation
- dataset transformations
- large summarization or enrichment jobs
- low-cost asynchronous inference

## Use this guide for

- The user has many independent requests to run
- A JSONL request file is acceptable
- Turnaround time can be minutes or hours instead of seconds
- Lower cost matters more than immediate interactivity

## Do not use this guide for

- real-time requests or tool-calling apps -> `domains/chat-completions.md`
- managed LLM-as-a-judge workflows -> `domains/evaluations.md`
- retrieval-specific vector generation -> `domains/embeddings.md`

## Workflow

1. Build a JSONL file where each line contains `custom_id` and `body`.
2. Upload the file with `purpose="batch-api"`.
3. Create the batch with `input_file_id=...` and the target endpoint.
4. Poll until the job is terminal.
5. Download output and error files, then reconcile by `custom_id`.

## Open next

- **End-to-end batch workflow**
  - Start with [scripts/batch-inference/batch_workflow.py](scripts/batch-inference/batch_workflow.py) or [scripts/batch-inference/batch_workflow.ts](scripts/batch-inference/batch_workflow.ts)
- **Request format, status model, and result downloads**
  - Read [references/batch-inference/api-reference.md](references/batch-inference/api-reference.md)
- **Operational guidance and batch sizing**
  - Read [references/batch-inference/api-reference.md](references/batch-inference/api-reference.md)

## Rules

- Use `input_file_id`, not legacy file parameters.
- Keep `custom_id` stable and meaningful so result reconciliation is easy.
- Batch is for independent requests. If the workload depends on shared conversation state, it is probably the wrong tool.
- Always inspect the error file in addition to the success output.
- `client.batches.create()` returns a wrapper; access the batch object via `response.job` (e.g., `response.job.id`). `client.batches.retrieve()` returns the batch object directly.
- For classification or labeling workloads, set `max_tokens` low (e.g., 4), use `temperature: 0`, and constrain the system prompt to return only the label. This minimizes output tokens and cost.
- Small batches (under 1K requests) typically complete in minutes. The 24-hour completion window is a maximum, not typical.

## Docs

- [Batch Inference](https://docs.together.ai/docs/batch-inference)
- [Batch API](https://docs.together.ai/reference/batch-create)
