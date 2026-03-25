---
name: together-chat-completions
description: "Use this skill for Together AI serverless chat inference: real-time or streaming chat apps, multi-turn conversations, tool and function calling, structured JSON outputs, and reasoning-capable models. Reach for it whenever the user wants to build or debug text generation on Together AI's OpenAI-compatible chat/completions API, unless they specifically need batch jobs, embeddings, fine-tuning, dedicated endpoints, dedicated containers, or GPU clusters."
---

# Together Chat Completions

## Overview

Use Together AI's serverless chat/completions API for interactive inference workloads:

- basic text generation
- streaming responses
- multi-turn chat state
- tool and function calling
- structured outputs
- reasoning-capable models

Treat this skill as the default entry point for Together AI text generation unless the task is
clearly offline batch processing, vector retrieval, model training, or infrastructure management.

## When This Skill Wins

- Build a chatbot, assistant, or text-generation endpoint on Together AI
- Add streaming output to a real-time user experience
- Implement tool calling or function-calling loops
- Constrain model output to JSON or a regex-defined shape
- Choose between standard chat models and reasoning models
- Debug request parameters, model behavior, or response shapes

## Hand Off To Another Skill

- Use `together-batch-inference` for large offline runs, backfills, or lower-cost asynchronous jobs
- Use `together-embeddings` for vector search, semantic retrieval, or reranking
- Use `together-fine-tuning` when the user wants to train or adapt a model
- Use `together-dedicated-endpoints` when the user needs always-on single-tenant hosting
- Use `together-dedicated-containers` or `together-gpu-clusters` for custom infrastructure

## Quick Routing

- **Basic chat, streaming, or multi-turn state**
  - Start with [references/api-parameters.md](references/api-parameters.md)
  - Use [scripts/chat_basic.py](scripts/chat_basic.py) or [scripts/chat_basic.ts](scripts/chat_basic.ts)
- **OpenAI SDK migration, rate limits, or debug headers**
  - Read [references/api-parameters.md](references/api-parameters.md)
  - Use [scripts/debug_headers.py](scripts/debug_headers.py) or [scripts/debug_headers.ts](scripts/debug_headers.ts)
- **Parallel async requests**
  - Use [scripts/async_parallel.py](scripts/async_parallel.py)
- **Tool calling or function calling**
  - Read [references/function-calling-patterns.md](references/function-calling-patterns.md)
  - Start from [scripts/tool_call_loop.py](scripts/tool_call_loop.py) or [scripts/tool_call_loop.ts](scripts/tool_call_loop.ts)
- **Structured outputs**
  - Read [references/structured-outputs.md](references/structured-outputs.md)
  - Start from [scripts/structured_outputs.py](scripts/structured_outputs.py) or [scripts/structured_outputs.ts](scripts/structured_outputs.ts)
- **Reasoning models or thinking-mode toggles**
  - Read [references/reasoning-models.md](references/reasoning-models.md)
  - Start from [scripts/reasoning_models.py](scripts/reasoning_models.py) or [scripts/reasoning_models.ts](scripts/reasoning_models.ts)
- **Model selection, context length, or pricing-aware choices**
  - Read [references/models.md](references/models.md)

## Workflow

1. Confirm that the workload is interactive serverless inference rather than batch, retrieval, or training.
2. Pick the smallest model that satisfies latency, quality, and context requirements.
3. Decide whether the job needs plain text, tools, structured output, or reasoning.
4. Start from the matching script instead of re-deriving request shapes from scratch.
5. Pull deeper details from the relevant reference file only when needed.

## High-Signal Rules

- Python scripts require the Together v2 SDK (`together>=2.0.0`). If the user is on an older version, they must upgrade first: `uv pip install --upgrade "together>=2.0.0"`.
- Use `client.chat.completions.create()` for Python and `client.chat.completions.create()` for TypeScript.
- Preserve full `messages` history for multi-turn conversations; do not rebuild context from final text only.
- For tools, implement the full loop: model tool call -> execute tool -> append tool result -> second model call.
- Prefer `json_schema` over looser JSON modes when the user needs stable machine-readable output.
- Use reasoning models only when the task benefits from deeper deliberation; otherwise prefer cheaper standard models.
- If the user needs many independent requests, combine this skill with `async_parallel.py` or hand off to batch inference.

## Resource Map

- **Parameters and response fields**: [references/api-parameters.md](references/api-parameters.md)
- **OpenAI compatibility, rate-limit headers, and debug headers**: [references/api-parameters.md](references/api-parameters.md)
- **Function-calling patterns**: [references/function-calling-patterns.md](references/function-calling-patterns.md)
- **Structured outputs**: [references/structured-outputs.md](references/structured-outputs.md)
- **Reasoning models**: [references/reasoning-models.md](references/reasoning-models.md)
- **Model catalog**: [references/models.md](references/models.md)

## Scripts

- [scripts/chat_basic.py](scripts/chat_basic.py) and [scripts/chat_basic.ts](scripts/chat_basic.ts): basic chat, streaming, and multi-turn state
- [scripts/debug_headers.py](scripts/debug_headers.py) and [scripts/debug_headers.ts](scripts/debug_headers.ts): raw-response inspection for routing, latency, and rate-limit headers
- [scripts/async_parallel.py](scripts/async_parallel.py): async Python fan-out for independent requests
- [scripts/tool_call_loop.py](scripts/tool_call_loop.py) and [scripts/tool_call_loop.ts](scripts/tool_call_loop.ts): full tool-call loop
- [scripts/structured_outputs.py](scripts/structured_outputs.py) and [scripts/structured_outputs.ts](scripts/structured_outputs.ts): schema-guided and regex outputs
- [scripts/reasoning_models.py](scripts/reasoning_models.py) and [scripts/reasoning_models.ts](scripts/reasoning_models.ts): reasoning fields, effort, and hybrid toggles

## Official Docs

- [Chat Overview](https://docs.together.ai/docs/chat-overview)
- [Inference Parameters](https://docs.together.ai/docs/inference-parameters)
- [Serverless Models](https://docs.together.ai/docs/serverless-models)
- [Function Calling](https://docs.together.ai/docs/function-calling)
- [JSON Mode](https://docs.together.ai/docs/json-mode)
- [Reasoning Overview](https://docs.together.ai/docs/reasoning-overview)
- [Chat Completions API](https://docs.together.ai/reference/chat-completions)
