# Together AI: Chat Completions

Use Together AI's serverless chat/completions API for interactive inference: basic and streaming text generation, multi-turn chat, tool and function calling, structured outputs, and reasoning models.

- basic text generation
- streaming responses
- multi-turn chat state
- tool and function calling
- structured outputs
- reasoning-capable models

Treat this guide as the default entry point for Together AI text generation unless the task is
clearly offline batch processing, vector retrieval, model training, or infrastructure management.

## Use this guide for

- Build a chatbot, assistant, or text-generation endpoint on Together AI
- Add streaming output to a real-time user experience
- Implement tool calling or function-calling loops
- Constrain model output to JSON or a regex-defined shape
- Choose between standard chat models and reasoning models
- Debug request parameters, model behavior, or response shapes

## Do not use this guide for

- large offline runs, backfills, or lower-cost asynchronous jobs -> `domains/batch-inference.md`
- vector search, semantic retrieval, or reranking -> `domains/embeddings.md`
- when the user wants to train or adapt a model -> `domains/fine-tuning.md`
- when the user needs always-on single-tenant hosting -> `domains/dedicated-model-inference.md`
- or `domains/gpu-clusters.md` for custom infrastructure -> `domains/dedicated-containers.md`
- For production stock-model workloads that need a defined SLA (committed throughput and reliability) without managing hardware, point users to Together's [provisioned throughput](https://docs.together.ai/docs/inference/provisioned-throughput) tier (reserved PTU capacity, one-month minimum term, contact sales; uses the same chat/completions API surface)

## Workflow

1. Confirm that the workload is interactive serverless inference rather than batch, retrieval, or training.
2. Pick the smallest model that satisfies latency, quality, and context requirements.
3. Decide whether the job needs plain text, tools, structured output, or reasoning.
4. Start from the matching script instead of re-deriving request shapes from scratch.
5. Pull deeper details from the relevant reference file only when needed.

## Open next

- **Basic chat, streaming, or multi-turn state**
  - Start with [references/chat-completions/api-parameters.md](references/chat-completions/api-parameters.md)
  - Use [scripts/chat-completions/chat_basic.py](scripts/chat-completions/chat_basic.py) or [scripts/chat-completions/chat_basic.ts](scripts/chat-completions/chat_basic.ts)
- **OpenAI SDK migration, rate limits, or debug headers**
  - Read [references/chat-completions/api-parameters.md](references/chat-completions/api-parameters.md)
  - Use [scripts/chat-completions/debug_headers.py](scripts/chat-completions/debug_headers.py) or [scripts/chat-completions/debug_headers.ts](scripts/chat-completions/debug_headers.ts)
- **Parallel async requests**
  - Use [scripts/chat-completions/async_parallel.py](scripts/chat-completions/async_parallel.py)
- **Tool calling or function calling**
  - Read [references/chat-completions/function-calling-patterns.md](references/chat-completions/function-calling-patterns.md)
  - Start from [scripts/chat-completions/tool_call_loop.py](scripts/chat-completions/tool_call_loop.py) or [scripts/chat-completions/tool_call_loop.ts](scripts/chat-completions/tool_call_loop.ts)
- **Designing tools, schemas, or tool_choice for reliability**
  - Read the "Best Practices" section in [references/chat-completions/function-calling-patterns.md](references/chat-completions/function-calling-patterns.md)
- **Structured outputs**
  - Read [references/chat-completions/structured-outputs.md](references/chat-completions/structured-outputs.md)
  - Start from [scripts/chat-completions/structured_outputs.py](scripts/chat-completions/structured_outputs.py) or [scripts/chat-completions/structured_outputs.ts](scripts/chat-completions/structured_outputs.ts)
- **Reasoning models or thinking-mode toggles**
  - Read [references/chat-completions/reasoning-models.md](references/chat-completions/reasoning-models.md)
  - Start from [scripts/chat-completions/reasoning_models.py](scripts/chat-completions/reasoning_models.py) or [scripts/chat-completions/reasoning_models.ts](scripts/chat-completions/reasoning_models.ts)
- **Combining tools + structured output, or tools + streaming**
  - Read the "Combining Tool Calls with Structured Output" section in
    [references/chat-completions/function-calling-patterns.md](references/chat-completions/function-calling-patterns.md)
  - Read the "Streaming Structured Output" section in
    [references/chat-completions/structured-outputs.md](references/chat-completions/structured-outputs.md)
- **Model selection, context length, or pricing-aware choices**
  - Read [references/chat-completions/models.md](references/chat-completions/models.md)

### Scripts in this area

- [scripts/chat-completions/chat_basic.py](scripts/chat-completions/chat_basic.py) and [scripts/chat-completions/chat_basic.ts](scripts/chat-completions/chat_basic.ts): basic chat, streaming, and multi-turn state
- [scripts/chat-completions/debug_headers.py](scripts/chat-completions/debug_headers.py) and [scripts/chat-completions/debug_headers.ts](scripts/chat-completions/debug_headers.ts): raw-response inspection for routing, latency, and rate-limit headers
- [scripts/chat-completions/async_parallel.py](scripts/chat-completions/async_parallel.py): async Python fan-out for independent requests
- [scripts/chat-completions/tool_call_loop.py](scripts/chat-completions/tool_call_loop.py) and [scripts/chat-completions/tool_call_loop.ts](scripts/chat-completions/tool_call_loop.ts): full tool-call loop
- [scripts/chat-completions/structured_outputs.py](scripts/chat-completions/structured_outputs.py) and [scripts/chat-completions/structured_outputs.ts](scripts/chat-completions/structured_outputs.ts): schema-guided and regex outputs
- [scripts/chat-completions/reasoning_models.py](scripts/chat-completions/reasoning_models.py) and [scripts/chat-completions/reasoning_models.ts](scripts/chat-completions/reasoning_models.ts): reasoning fields, effort, and hybrid toggles

## Rules

- Use `client.chat.completions.create()` for Python and `client.chat.completions.create()` for TypeScript.
- Preserve full `messages` history for multi-turn conversations; do not rebuild context from final text only.
- For tools, implement the full loop: model tool call -> execute tool -> append tool result -> second model call.
- For tool definitions, prefer `enum` over free-form strings, set `"additionalProperties": false`, and add `"strict": true` on the function definition when you need argument generation to conform to the schema.
- Tool names must not contain spaces, periods, or dashes. Branch on `finish_reason` (`"tool_calls"` vs `"stop"`) instead of assuming a tool was called, and parse `function.arguments` as JSON inside a try/except.
- Prefer `json_schema` over looser JSON modes when the user needs stable machine-readable output.
- Use reasoning models only when the task benefits from deeper deliberation; otherwise prefer cheaper standard models.
- Preserved thinking uses the `reasoning` key on both output and input (the field is symmetric). When you pass a prior assistant turn back to the API, include `"reasoning": ...` on the assistant message; `reasoning_content` is still accepted on input for backward compatibility but prefer `reasoning` in new code.
- Reasoning models nest extra token counts OpenAI-style (`usage.completion_tokens_details.reasoning_tokens`, `usage.prompt_tokens_details.cached_tokens`), but some non-reasoning models return `cached_tokens` flat at the top of `usage`. Read both locations defensively — clients that only check one shape will silently return `0`. See [references/chat-completions/reasoning-models.md](references/chat-completions/reasoning-models.md) for the defensive-read pattern.
- To combine tool calling with structured output, use a two-phase approach: Phase 1 sends `tools` (no `response_format`), Phase 2 sends `response_format` (no `tools`) after tool results are appended.
- Streaming works with `response_format`; accumulate chunks and parse the final concatenated string as JSON.
- If the user needs many independent requests, combine it with `async_parallel.py` or hand off to batch inference.

## Docs

- [Chat Overview](https://docs.together.ai/docs/chat-overview)
- [Inference Parameters](https://docs.together.ai/docs/inference-parameters)
- [Serverless Models](https://docs.together.ai/docs/serverless-models)
- [Function Calling](https://docs.together.ai/docs/function-calling)
- [JSON Mode](https://docs.together.ai/docs/json-mode)
- [Reasoning Overview](https://docs.together.ai/docs/reasoning-overview)
- [Chat Completions API](https://docs.together.ai/reference/chat-completions)
