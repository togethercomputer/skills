# Together AI: Batch Inference

Asynchronous bulk inference over a JSONL file, up to 50% cheaper than real-time, with a 24-hour
completion window (batches under 1,000 requests usually finish in minutes; complex or busy models
can occasionally run past 24 hours, so track status rather than wall-clock time). For requests a user is
waiting on, use `domains/chat-completions.md` instead.

## Workflow

1. Write a JSONL file; each line is `{"custom_id": ..., "body": {chat request}}`.
2. Upload it: `client.files.upload(file=path, purpose="batch-api", check=False)`; the server
   validates during `VALIDATING`.
3. `client.batches.create(input_file_id=..., endpoint="/v1/chat/completions")`.
4. Poll `client.batches.retrieve(batch_id)` until `COMPLETED`, `FAILED`, `EXPIRED`, or
   `CANCELLED`.
5. Download the output **and** error files with `client.files.content(id)`; reconcile rows by
   `custom_id`.

## Rules

- `client.batches.create()` returns a wrapper: the batch is `response.job` (`response.job.id`).
  `client.batches.retrieve()` returns the batch directly.
- The 50% discount applies to `meta-llama/Llama-3.3-70B-Instruct-Turbo` and
  `openai/whisper-large-v3` (audio batches use `/v1/audio/transcriptions`); other models run at
  standard rates. Batches can also target a dedicated endpoint, without the discount.
- Keep `custom_id` unique and meaningful; results come back unordered.
- Batch is for independent requests; shared conversation state belongs in chat.
- Always read the error file; failed rows appear only there.
- For classification, set `max_tokens` low (about 4), `temperature` 0, and ask for the label
  only.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/batch-inference/batch_workflow.py](scripts/batch-inference/batch_workflow.py) (.ts) | 170 | build JSONL, upload, create, poll, download, reconcile | running a batch end to end |
| [references/batch-inference/api-reference.md](references/batch-inference/api-reference.md) | 307 | JSONL input and output formats, job object and statuses, discounted and excluded models, limits, error codes, CLI | a format detail, status, limit, or error |

## Docs

- [Batch Inference](https://docs.together.ai/docs/inference/batch/overview)
- [Batch API](https://docs.together.ai/reference/batch-create)
