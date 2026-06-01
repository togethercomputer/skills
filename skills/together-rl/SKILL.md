---
name: together-rl
description: "GRPO and policy-gradient reinforcement-learning post-training on Together AI via low-level training sessions: create a session, sample token-level rollouts, score them, and apply forward_backward plus optim_step. Pairs the RL training API with the together-sandbox SDK to compute rewards by executing model-generated code in isolated sandboxes (run a test suite; pass/fail becomes the reward). Reach for it whenever the user wants to train a model with reinforcement learning, run a GRPO loop, or compute verifiable code-execution rewards rather than managed supervised fine-tuning or plain inference."
---

# Together RL

## Overview

Use Together RL when the user wants to post-train a model with reinforcement learning — driving the
training loop themselves through low-level training sessions rather than submitting a managed job.

Typical fits:

- GRPO / policy-gradient post-training with a custom reward
- Coding or agentic RL where the reward comes from **executing** the model's output (run tests, check exit code)
- Verifiable-reward RL (math, code, tool use) with token-level sampling and advantages
- Multi-turn rollout training where each rollout is scored out-of-band

## When This Skill Wins

- The user wants to run the GRPO loop directly: sample → score → `forward_backward` → `optim_step`
- The reward requires running untrusted, model-generated code (so it must execute in a sandbox)
- The user references GRPO, RL fine-tuning, policy gradients, advantages, reward functions, or verifiers
- Token-level control is needed (logprobs, advantages, loss masks) rather than a managed dataset job

## Hand Off To Another Skill

- Use `together-sandbox` for the sandbox API itself — this skill calls it to execute reward code, but the
  snapshot/sandbox/exec surface lives there
- Use `together-fine-tuning` for managed supervised fine-tuning, LoRA, or DPO jobs (no hand-written loop)
- Use `together-chat-completions` if the user only needs inference, not training
- Use `together-evaluations` to score a model with an LLM judge rather than a programmatic reward

## Quick Routing

- **Run a GRPO loop with code-execution rewards**
  - Start with [scripts/grpo_sandbox_reward.py](scripts/grpo_sandbox_reward.py)
- **Training-session lifecycle, the three operations, and the GRPO sample schema**
  - Read [references/grpo-loop.md](references/grpo-loop.md)
- **Compute rewards by running code in a sandbox (the integration)**
  - Read [references/sandbox-rewards.md](references/sandbox-rewards.md)

## Workflow

1. Create a training session with `client.beta.rl.sessions.create(base_model=...)` and wait for status
   `TRAINING_SESSION_STATUS_RUNNING`.
2. For each step, sample a group of rollouts per prompt with `client.beta.rl.training.sample(...)`
   (`num_samples` = group size); each call returns an async **operation** you poll to completion.
3. Decode the sampled token sequences and **compute rewards out-of-band** — for code tasks, hand off to
   `together-sandbox`: run each candidate's test suite in an isolated sandbox, `exit 0` → reward `1.0`.
4. Compute GRPO advantages: `advantage = reward − mean(group_rewards)` (center within each prompt's group).
5. Assemble GRPO samples and call `client.beta.rl.training.forward_backward(...)` with `LOSS_TYPE_GRPO`.
6. Apply `client.beta.rl.training.optim_step(session_id, learning_rate=...)`.
7. Repeat; always `client.beta.rl.sessions.stop(session_id)` in a `finally`.

## High-Signal Rules

- **RL calls return operations, not results.** `sample` / `forward_backward` / `optim_step` each return an
  operation handle — poll it (status `TRAINING_OPERATION_STATUS_*`) until complete before using the output.
- **Rewards are computed out-of-band, never inside the RL call.** Sampling returns tokens + logprobs; you
  score them yourself and feed advantages back in `forward_backward`.
- **The RL SDK is synchronous; the sandbox SDK is async.** Bridge them with a single `asyncio.run(...)` per
  batch that fans out sandboxes with `asyncio.gather` (one sandbox per candidate), then return rewards into
  the sync loop. Do not create a sandbox per token or per RL call.
- **Center advantages within the group.** GRPO subtracts the per-prompt group-mean reward as the baseline;
  a group where every sample gets the same reward contributes zero gradient.
- **GRPO sample schema** (see [references/grpo-loop.md](references/grpo-loop.md)): `model_input.chunks[].
  encoded_text.tokens`, and `loss_inputs.{loss_mask, target_tokens, grpo_inputs.{advantages,
  generator_logprobs}}`. Mask the prompt tokens out of the loss; only response tokens carry advantage.
- **Pre-build the reward environment as a sandbox snapshot.** Bake the task harness, dependencies, and
  tests into a snapshot once, then create ephemeral sandboxes from it per rollout — don't `pip install`
  inside every rollout.

## Status

The RL training API (`client.beta.rl`) is in **beta** and is **not yet in the public `together` package**
(public `together` exposes `beta.clusters` / `beta.jig` only). It also requires a service-specific
`base_url`. This skill targets the public SDK surface; the reward half (`together-sandbox`) is usable today.
Until the public RL release ships, install the preview SDK per the RL API docs and pass the RL `base_url`
explicitly.

## Resource Map

- **GRPO loop mechanics**: [references/grpo-loop.md](references/grpo-loop.md)
- **Sandbox reward integration**: [references/sandbox-rewards.md](references/sandbox-rewards.md)
- **End-to-end script**: [scripts/grpo_sandbox_reward.py](scripts/grpo_sandbox_reward.py)
- **Sandbox API** (hand-off): the `together-sandbox` skill

## Official Docs

- Together RL training API — `/rl/training-sessions` (create, `:forward-backward`, `:optim-step`, `:stop`)
- [Together Sandbox SDK](https://github.com/togethercomputer/together-sandbox/blob/main/docs/python-sdk.md)
- Reference loop: [rl-cookbook/grpo_train.py](https://github.com/togethercomputer/rl-cookbook/blob/main/grpo_train.py)
