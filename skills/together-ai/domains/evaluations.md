# Together AI: Evaluations

Managed LLM-as-a-judge jobs: **classify** outputs into labels, **score** them on a scale, or
**compare** two responses. Use it instead of a hand-written judge loop when results must be
repeatable. To change a model rather than measure it, go to `domains/fine-tuning.md`.

## Workflow

1. Pick classify, score, or compare, and define the dataset columns before writing code.
2. Upload the dataset as an eval file (`check=False`) and keep the file ID.
3. Choose judge and target models explicitly. The evaluation service keeps its **own** serverless
   allowlist, separate from the main catalog; check it live (free):
   `GET https://api.together.xyz/v1/evaluation/model-list?model_source=serverless`. On 2026-10-07
   the live list and the docs table disagreed, so trust the endpoint. Models on both, and callable
   serverless: `openai/gpt-oss-120b` (the docs' example judge),
   `meta-llama/Llama-3.3-70B-Instruct-Turbo`, and `Qwen/Qwen3.5-9B`.
4. `client.evals.create(...)`, poll status until it is terminal, then download the per-row results.

## Rules

- Upload eval files with `check=False`; local validation misreads eval datasets.
- Compare works best when both candidate responses are already columns in the dataset.
- Vision evals need an `image_data_urls` column of base64 data URLs, and a vision-capable model
  and judge.
- Keep judge configuration explicit; hidden defaults make results hard to interpret.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/evaluations/run_evaluation.py](scripts/evaluations/run_evaluation.py) (.ts) | 458 | CLI for classify, score, and compare: upload, create, poll, `--download-results`; flags `--eval-column`, `--model-a-column`, `--model-b-column`, `--judge-model-source external` | running any evaluation |
| [references/evaluations/api-reference.md](references/evaluations/api-reference.md) | 779 | request fields, judge and target config, result schemas, dataset format, image inputs, Jinja2 templates, external providers, retrieval endpoints | a field, template, or provider detail the script does not cover |

## Docs

- [AI Evaluations](https://docs.together.ai/docs/ai-evaluations)
- [Evaluations API](https://docs.together.ai/reference/create-evaluation)
