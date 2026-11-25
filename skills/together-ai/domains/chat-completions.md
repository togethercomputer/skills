# Together AI: Chat Completions

Serverless, OpenAI-compatible text generation: one call, billed per token. Covers plain and
streaming chat, multi-turn state, tool calling, structured (JSON) output, reasoning models, and
image input to vision models.

Hand-offs: many prompts with no user waiting go to `domains/batch-inference.md`; retrieval goes to
`domains/embeddings.md`; always-on hosting goes to `domains/dedicated-model-inference.md`. For a
production SLA on a stock model, point to
[provisioned throughput](https://docs.together.ai/docs/inference/provisioned-throughput)
(reserved capacity, same API, contact sales).

## Essentials

```python
from together import Together

client = Together()
resp = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Hello"}],
    # stream=True,  -> iterate chunks; text is chunk.choices[0].delta.content
)
print(resp.choices[0].message.content)
```

- Serverless models that support tools and JSON output today include
  `meta-llama/Llama-3.3-70B-Instruct-Turbo`, `zai-org/GLM-5.3-Flash` (reasoning),
  `deepseek-ai/DeepSeek-V4.1-Flash`, and `Qwen/Qwen3.5-9B` (small, also takes images). The catalog
  changes; see the model rule in `SKILL.md`. `Qwen/Qwen3.6-Plus`, `Qwen3.7-Plus`, `Qwen3.7-Max`,
  and `Qwen3.8-Flash` return 403 `third_party_data_sharing_blocked` unless the organization
  enables third-party data sharing.
- Image input: put `{"type": "image_url", "image_url": {"url": ...}}` parts in the user message's
  `content` list and use a vision model (`Qwen/Qwen3.5-9B`,
  `nvidia/NVIDIA-Nemotron-3.5-Super-VL`, `moonshotai/Kimi-K3`; each answered an image request on
  2026-11-18).

## Rules

- Keep the full `messages` history across turns; do not rebuild context from final text only.
- Streams can end with a usage-only chunk whose `choices` list is empty. Check `chunk.choices`
  before reading `chunk.choices[0]`.
- Tool calling is a loop, not one round trip: execute every tool call, append each result as a
  `tool` message, call the model again, and repeat until it answers without tool calls.
- **Ground the final answer in tool results.** When the user asked for an action (create a
  ticket, send an email), do not accept a final answer until that tool has a successful result.
  If the model answers without it, tell it which call is missing and continue the loop. If it
  still has not run, report the task as incomplete rather than repeating the model's claim.
  Seeing the gap in a test run is not enough; change the loop so it recovers.
- Tool schemas: prefer `enum` to free strings, set `"additionalProperties": false`, and add
  `"strict": true` when arguments must match the schema. Tool names cannot contain spaces,
  periods, or dashes. Branch on `finish_reason` (`"tool_calls"` or `"stop"`) and parse
  `function.arguments` as JSON inside a try/except.
- To combine tools with structured output, use two phases: phase 1 sends `tools` with no
  `response_format`; phase 2 sends `response_format` with no `tools`, after the tool results.
- Prefer `json_schema` to looser JSON modes for machine-readable output. Streaming works with
  `response_format`: join the chunks, then parse the full string.
- Reasoning: the trace arrives on `reasoning_content` for most models and on `reasoning` for a few
  (Qwen3.6 Plus, Muse Glimmer 30B, as observed 2026-11-18). Read both, and when you send a prior
  assistant turn back, return the trace unmodified under the key it came on. Thinking-by-default models spend
  `max_tokens` on the trace first, so give them headroom or the answer comes back empty. Use
  reasoning models only when the task benefits; they cost more and are slower.
- Reasoning controls differ per model, and the API returns HTTP 200 for a control the model
  ignores. `reasoning={"enabled": False}` turns thinking off on some models (for example
  DeepSeek V4.1 Flash and Kimi K3). GLM-5.3 and GLM-5.3 Flash keep reasoning under that switch
  but honor `reasoning_effort="low"`. Check the per-model table in
  [reasoning-models.md](references/chat-completions/reasoning-models.md) (Reasoning Controls by
  Model), then confirm the change in `usage.completion_tokens_details.reasoning_tokens`.
- Token usage: reasoning models nest counts OpenAI-style
  (`usage.completion_tokens_details.reasoning_tokens`, `usage.prompt_tokens_details.cached_tokens`)
  but some models return `cached_tokens` flat on `usage`. Read both places. A few models report no
  reasoning count, so compare `completion_tokens` for those.

## Open next

Open a file only for the detail its row names. References over 100 lines start with a
`## Contents` list; read just the section you need.

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/chat-completions/chat_basic.py](scripts/chat-completions/chat_basic.py) (.ts) | 76 | single call, streaming, multi-turn | you want a runnable starting point |
| [scripts/chat-completions/tool_call_loop.py](scripts/chat-completions/tool_call_loop.py) (.ts) | 164 | multi-round tool loop with argument-error handling and the required-tool grounding check | building any agent or tool loop |
| [scripts/chat-completions/structured_outputs.py](scripts/chat-completions/structured_outputs.py) (.ts) | 142 | `json_schema` and regex output | output must parse as JSON |
| [scripts/chat-completions/reasoning_models.py](scripts/chat-completions/reasoning_models.py) (.ts) | 162 | reasoning field, effort levels, hybrid on/off toggles | using a reasoning model |
| [scripts/chat-completions/async_parallel.py](scripts/chat-completions/async_parallel.py) | 50 | asyncio fan-out of independent requests | many requests and a user is waiting |
| [scripts/chat-completions/debug_headers.py](scripts/chat-completions/debug_headers.py) (.ts) | 57 | raw response, rate-limit and routing headers | debugging latency, 429s, or routing |
| [references/chat-completions/models.md](references/chat-completions/models.md) | 74 | model picks by use case, context lengths, vision and moderation models | choosing a model (verify it is live) |
| [references/chat-completions/api-parameters.md](references/chat-completions/api-parameters.md) | 481 | every request parameter, message object, OpenAI-SDK compatibility, rate-limit tiers, HTTP status codes | a parameter or status code not covered above |
| [references/chat-completions/function-calling-patterns.md](references/chat-completions/function-calling-patterns.md) | 838 | six calling patterns (parallel, multi-step, ...), `tool_choice`, tools plus structured output, best practices, supported models | a tool pattern the script does not show |
| [references/chat-completions/structured-outputs.md](references/chat-completions/structured-outputs.md) | 538 | the three JSON modes, reasoning plus JSON, streaming JSON, troubleshooting | JSON output fails to parse or validate |
| [references/chat-completions/reasoning-models.md](references/chat-completions/reasoning-models.md) | 543 | reasoning model table, measured per-model control matrix (off switches, `reasoning_effort`, trace field), effort levels, hybrid toggles, output format, token accounting | tuning reasoning depth or cost, or a reasoning setting that seems to do nothing |

## Docs

- [Chat overview](https://docs.together.ai/docs/inference/chat/overview)
- [Serverless models](https://docs.together.ai/docs/serverless/models)
- [Function calling](https://docs.together.ai/docs/inference/function-calling/overview)
- [Structured outputs](https://docs.together.ai/docs/inference/chat/structured-outputs)
- [Reasoning overview](https://docs.together.ai/docs/inference/chat/reasoning)
- [Chat completions API](https://docs.together.ai/reference/chat-completions)
