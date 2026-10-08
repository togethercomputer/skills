# Together AI: Fine-Tuning

Adapt a model on your data: LoRA (default), full fine-tuning, DPO preference tuning, VLM,
function-calling, and reasoning tuning, plus bring-your-own-model uploads. Billed by training
tokens. Serving the result is `domains/dedicated-model-inference.md`; measuring it is
`domains/evaluations.md`.

## Workflow

1. Pick the method that matches the behavior change; prefer LoRA unless there is a reason to pay
   for full fine-tuning.
2. Check the base model supports that method: `tg beta models public --product fine-tuning`.
3. Validate the dataset format before uploading, so bad files fail before you spend tokens.
4. Upload the file and keep its ID, then create the job with method-specific parameters.
5. Poll job state and events until it is terminal; read checkpoints and per-step metrics.
6. Deploying the tuned model is a separate step; a finished job is not a served model.

## Rules

- Use the method-specific script; each method has its own data format and parameters.
- Parameterize dataset paths, model IDs, and suffixes instead of hardcoding a demo dataset.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/fine-tuning/finetune_workflow.py](scripts/fine-tuning/finetune_workflow.py) | 229 | LoRA or full: validate, upload, create, monitor | standard SFT |
| [scripts/fine-tuning/dpo_workflow.py](scripts/fine-tuning/dpo_workflow.py) | 267 | preference-pair data and DPO parameters | DPO |
| [scripts/fine-tuning/function_calling_finetune.py](scripts/fine-tuning/function_calling_finetune.py) | 309 | tool-call training data and job | tuning tool use |
| [scripts/fine-tuning/reasoning_finetune.py](scripts/fine-tuning/reasoning_finetune.py) | 279 | reasoning-trace data and job | tuning reasoning |
| [scripts/fine-tuning/vlm_finetune.py](scripts/fine-tuning/vlm_finetune.py) | 228 | image-text data and VLM job | vision-language tuning |
| [references/fine-tuning/data-formats.md](references/fine-tuning/data-formats.md) | 368 | every dataset format (conversational, instruction, DPO, reasoning, tools, VLM), loss masking, sample weights, validation | preparing or debugging a dataset |
| [references/fine-tuning/supported-models.md](references/fine-tuning/supported-models.md) | 185 | models per method, recommended starting models, BYOM | choosing a base model |
| [references/fine-tuning/deployment.md](references/fine-tuning/deployment.md) | 234 | training parameters, monitoring, continued fine-tuning, deployment options, pricing | tuning hyperparameters or deploying the result |

## Docs

- [Fine-tuning Quickstart](https://docs.together.ai/docs/fine-tuning-quickstart)
- [Data Preparation](https://docs.together.ai/docs/fine-tuning-data-preparation)
- [Fine-tuning Models](https://docs.together.ai/docs/fine-tuning-models)
- [Deploying a Fine-Tuned Model](https://docs.together.ai/docs/deploying-a-fine-tuned-model)
- [Fine-tuning API](https://docs.together.ai/reference/post-fine-tunes)
