---
name: together-evaluations
description: Use this skill for Together AI LLM-as-a-judge workflows: classify, score, and compare evaluations; judge model selection; external-provider judges or targets; and result polling or downloads. Reach for it whenever the user wants to benchmark outputs, grade model responses, compare A/B variants, or operationalize automated evaluations on Together AI.
---

# Together AI Evaluations

## Overview

Use Together AI evaluations when the user wants a managed LLM-as-a-judge workflow rather than an
ad hoc prompt loop.

Core evaluation types:

- **Classify**: assign outputs to labels
- **Score**: grade outputs on a numeric scale
- **Compare**: compare two candidate outputs with bias controls

This skill also covers external providers used as judges or targets when the workflow still runs
through Together AI's evaluation system.

## When This Skill Wins

- Benchmark prompt variants, models, or product responses
- Grade quality, safety, policy compliance, or task success
- Run A/B comparisons between model outputs
- Build repeatable evaluation jobs with uploaded datasets
- Pull results programmatically after asynchronous execution

## Hand Off To Another Skill

- Use `together-chat-completions` for one-off inference or manual judge prompts
- Use `together-batch-inference` for bulk offline generation rather than evaluation
- Use `together-fine-tuning` when the user wants to improve the model instead of just measure it
- Use `together-dedicated-endpoints` only if the evaluation target itself is a dedicated endpoint

## Quick Routing

- **Classify / Score / Compare job setup**
  - Start with [scripts/run_evaluation.py](scripts/run_evaluation.py) or [scripts/run_evaluation.ts](scripts/run_evaluation.ts)
  - Read [references/api-reference.md](references/api-reference.md) for exact request shapes
- **Dataset formatting**
  - Read the dataset sections in [references/api-reference.md](references/api-reference.md)
- **External providers as judge or target**
  - Read the model-source and provider sections in [references/api-reference.md](references/api-reference.md)
- **Polling, listing, or downloading results**
  - Use the retrieval endpoints documented in [references/api-reference.md](references/api-reference.md)

## Workflow

1. Identify whether the user needs classify, score, or compare.
2. Define the dataset schema before writing code.
3. Upload the dataset as an eval file and keep the returned file ID.
4. Configure judge and target models explicitly, especially when mixing providers.
5. Poll status until completion, then download the result file for analysis.

## High-Signal Rules

- The current SDK examples in this repo use `check=False` for eval uploads because local file validation can misclassify eval datasets.
- Treat dataset schema as part of the product contract; inconsistent fields cause downstream confusion.
- Compare evaluations are best when both candidate responses are already present in the dataset.
- Keep judge configuration explicit. Hidden defaults make benchmark interpretation harder.
- Use Together AI's managed evaluation job instead of rebuilding a manual judge loop when repeatability matters.

## Resource Map

- **Full API reference**: [references/api-reference.md](references/api-reference.md)
- **Python workflow**: [scripts/run_evaluation.py](scripts/run_evaluation.py)
- **TypeScript workflow**: [scripts/run_evaluation.ts](scripts/run_evaluation.ts)

## Official Docs

- [AI Evaluations](https://docs.together.ai/docs/ai-evaluations)
- [Evaluations API](https://docs.together.ai/reference/create-evaluation)
