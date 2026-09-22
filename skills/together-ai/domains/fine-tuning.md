# Together AI: Fine-Tuning

Use Together AI fine-tuning when the user needs to adapt a model to their own data or behavior.

Supported workflows in this repo:

- LoRA fine-tuning
- full fine-tuning
- DPO preference tuning
- VLM fine-tuning
- function-calling fine-tuning
- reasoning fine-tuning
- BYOM upload paths

## Use this guide for

- Train a model on custom instruction or conversational data
- Improve function-calling reliability with supervised examples
- Train on preferences rather than only demonstrations
- Fine-tune multimodal or reasoning-oriented models
- Deploy a fine-tuned output model later through dedicated endpoints

## Do not use this guide for

- plain inference without training -> `domains/chat-completions.md`
- measure a model before or after tuning -> `domains/evaluations.md`
- host the resulting tuned model -> `domains/dedicated-model-inference.md`
- only when the user needs raw infrastructure rather than managed tuning -> `domains/gpu-clusters.md`

## Workflow

1. Choose the tuning method that matches the desired behavior change.
2. Validate dataset format before spending tokens on training.
3. Upload training data and keep the returned file ID.
4. Create the job with explicit method-specific parameters.
5. Monitor job state, events, checkpoints, and per-step training metrics before handing off to deployment.

## Open next

- **Standard LoRA or full fine-tuning**
  - Start with [scripts/fine-tuning/finetune_workflow.py](scripts/fine-tuning/finetune_workflow.py)
  - Read [references/fine-tuning/data-formats.md](references/fine-tuning/data-formats.md)
- **DPO preference tuning**
  - Start with [scripts/fine-tuning/dpo_workflow.py](scripts/fine-tuning/dpo_workflow.py)
- **Function-calling tuning**
  - Start with [scripts/fine-tuning/function_calling_finetune.py](scripts/fine-tuning/function_calling_finetune.py)
- **Reasoning tuning**
  - Start with [scripts/fine-tuning/reasoning_finetune.py](scripts/fine-tuning/reasoning_finetune.py)
- **VLM tuning**
  - Start with [scripts/fine-tuning/vlm_finetune.py](scripts/fine-tuning/vlm_finetune.py)
- **Model support and deployment options**
  - Read [references/fine-tuning/supported-models.md](references/fine-tuning/supported-models.md)
  - Read [references/fine-tuning/deployment.md](references/fine-tuning/deployment.md)

## Rules

- Prefer LoRA unless the user has a specific reason to pay for full fine-tuning.
- Keep data-format validation close to the upload step so bad files fail early.
- Treat deployment as a separate phase; fine-tuning success does not automatically mean serving success.
- Use the method-specific script instead of overloading one generic workflow for all modes.
- Parameterize dataset paths, model IDs, and suffixes in automation instead of embedding one demo dataset forever.

## Docs

- [Fine-tuning Quickstart](https://docs.together.ai/docs/fine-tuning-quickstart)
- [Data Preparation](https://docs.together.ai/docs/fine-tuning-data-preparation)
- [Fine-tuning Models](https://docs.together.ai/docs/fine-tuning-models)
- [Deploying a Fine-Tuned Model](https://docs.together.ai/docs/deploying-a-fine-tuned-model)
- [Fine-tuning API](https://docs.together.ai/reference/post-fine-tunes)
