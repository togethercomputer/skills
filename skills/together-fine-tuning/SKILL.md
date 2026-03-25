---
name: together-fine-tuning
description: "Use this skill for Together AI fine-tuning workflows: LoRA or full fine-tuning, DPO preference tuning, VLM training, function-calling tuning, reasoning tuning, and BYOM uploads. Reach for it whenever the user wants to adapt a model on custom data rather than only run inference, evaluate outputs, or host an existing model."
---

# Together Fine-Tuning

## Overview

Use Together AI fine-tuning when the user needs to adapt a model to their own data or behavior.

Supported workflows in this repo:

- LoRA fine-tuning
- full fine-tuning
- DPO preference tuning
- VLM fine-tuning
- function-calling fine-tuning
- reasoning fine-tuning
- BYOM upload paths

## When This Skill Wins

- Train a model on custom instruction or conversational data
- Improve function-calling reliability with supervised examples
- Train on preferences rather than only demonstrations
- Fine-tune multimodal or reasoning-oriented models
- Deploy a fine-tuned output model later through dedicated endpoints

## Hand Off To Another Skill

- Use `together-chat-completions` for plain inference without training
- Use `together-evaluations` to measure a model before or after tuning
- Use `together-dedicated-endpoints` to host the resulting tuned model
- Use `together-gpu-clusters` only when the user needs raw infrastructure rather than managed tuning

## Quick Routing

- **Standard LoRA or full fine-tuning**
  - Start with [scripts/finetune_workflow.py](scripts/finetune_workflow.py)
  - Read [references/data-formats.md](references/data-formats.md)
- **DPO preference tuning**
  - Start with [scripts/dpo_workflow.py](scripts/dpo_workflow.py)
- **Function-calling tuning**
  - Start with [scripts/function_calling_finetune.py](scripts/function_calling_finetune.py)
- **Reasoning tuning**
  - Start with [scripts/reasoning_finetune.py](scripts/reasoning_finetune.py)
- **VLM tuning**
  - Start with [scripts/vlm_finetune.py](scripts/vlm_finetune.py)
- **Model support and deployment options**
  - Read [references/supported-models.md](references/supported-models.md)
  - Read [references/deployment.md](references/deployment.md)

## Workflow

1. Choose the tuning method that matches the desired behavior change.
2. Validate dataset format before spending tokens on training.
3. Upload training data and keep the returned file ID.
4. Create the job with explicit method-specific parameters.
5. Monitor job state, events, and checkpoints before handing off to deployment.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Prefer LoRA unless the user has a specific reason to pay for full fine-tuning.
- Keep data-format validation close to the upload step so bad files fail early.
- Treat deployment as a separate phase; fine-tuning success does not automatically mean serving success.
- Use the method-specific script instead of overloading one generic workflow for all modes.
- Parameterize dataset paths, model IDs, and suffixes in automation instead of embedding one demo dataset forever.

## Resource Map

- **Data formats**: [references/data-formats.md](references/data-formats.md)
- **Supported models**: [references/supported-models.md](references/supported-models.md)
- **Deployment guide**: [references/deployment.md](references/deployment.md)
- **LoRA or full workflow**: [scripts/finetune_workflow.py](scripts/finetune_workflow.py)
- **DPO workflow**: [scripts/dpo_workflow.py](scripts/dpo_workflow.py)
- **Function-calling workflow**: [scripts/function_calling_finetune.py](scripts/function_calling_finetune.py)
- **Reasoning workflow**: [scripts/reasoning_finetune.py](scripts/reasoning_finetune.py)
- **VLM workflow**: [scripts/vlm_finetune.py](scripts/vlm_finetune.py)

## Official Docs

- [Fine-tuning Quickstart](https://docs.together.ai/docs/fine-tuning-quickstart)
- [Data Preparation](https://docs.together.ai/docs/fine-tuning-data-preparation)
- [Fine-tuning Models](https://docs.together.ai/docs/fine-tuning-models)
- [Deploying a Fine-Tuned Model](https://docs.together.ai/docs/deploying-a-fine-tuned-model)
- [Fine-tuning API](https://docs.together.ai/reference/post-fine-tunes)
