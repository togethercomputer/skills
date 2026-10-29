# Chat Model Catalog

Snapshot of the serverless catalog as of 2026-10-26. Serverless availability changes often; a
model that drops off returns `Unable to access non-serverless model` or HTTP 400
`model_not_available`. To confirm a chat model, send one request with `max_tokens=1`; check the
[deprecations page](https://docs.together.ai/docs/deprecations) for retired models and their
replacements. `client.models.list()` and `tg beta models public` cannot confirm serverless
availability.

Recently removed from serverless, with Together's suggested replacements:
`meta-llama/Llama-3.3-70B-Instruct-Turbo` (2026-10-22, use `meta-models/Muse-Glimmer-30B`),
`deepseek-ai/DeepSeek-V4-Flash-0731` (2026-10-22, use `deepseek-ai/DeepSeek-V4.1-Flash`),
`openai/gpt-oss-20b` (2026-09-15, use `Qwen/Qwen3.5-9B`), and `google/gemma-4-31B-it`
(2026-09-15, use `zai-org/GLM-5.3-Flash`).

Qwen3.6 Plus, Qwen3.7 Plus, Qwen3.7 Max, and Qwen3.8 Flash return 403
`third_party_data_sharing_blocked` unless the organization enables third-party data sharing.

Most of these models think before answering by default and spend `max_tokens` on the trace
first. When the output budget is small, pass `reasoning={"enabled": False}` on hybrid models.

Source pages: [Serverless models](https://docs.together.ai/docs/serverless/models) and
[Recommended models](https://docs.together.ai/docs/inference/recommended-models).

## Recommended Models by Use Case

| Use Case | Model | API String | Alternatives |
|----------|-------|-----------|-------------|
| Chat | Kimi K3 | `moonshotai/Kimi-K3` | `zai-org/GLM-5.3`, `Qwen/Qwen3.8-2.4T-A95B` |
| Reasoning | Kimi K3 | `moonshotai/Kimi-K3` | `deepseek-ai/DeepSeek-V4-Pro-0813`, `zai-org/GLM-5.3` |
| Coding agents | GLM-5.3 | `zai-org/GLM-5.3` | `moonshotai/Kimi-K3`, `deepseek-ai/DeepSeek-V4.1-Flash` |
| Small and fast | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | `Qwen/Qwen3.8-Flash` |
| Mid-size general | DeepSeek V4.1 Flash | `deepseek-ai/DeepSeek-V4.1-Flash` | `zai-org/GLM-5.3-Flash` |
| Function calling | GLM-5.3 Flash | `zai-org/GLM-5.3-Flash` | `deepseek-ai/DeepSeek-V4.1-Flash` |

The recommended-models page still names `deepseek-ai/DeepSeek-V4-Flash-0731` as an alternative;
it left serverless on 2026-10-22, so this table uses its replacement. No chat model currently
gets the batch discount (see the batch inference guide).

Kimi K3 thinks by default (`reasoning_effort="max"`) and returns its trace on
`reasoning_content`; give it generous `max_tokens`, or pass `reasoning={"enabled": False}` for
quick turns.

## Full Serverless Chat Catalog

Prices are USD per 1M tokens (input / output). Tools and JSON mean function calling and
structured outputs are supported.

| Organization | Model | API String | Context | Price in / out | Tools | JSON |
|-------------|-------|-----------|---------|---------------|-------|------|
| Moonshot | Kimi K3 | `moonshotai/Kimi-K3` | 1,048,576 | 3.00 / 15.00 | Yes | Yes |
| Z.ai | GLM-5.3 | `zai-org/GLM-5.3` | 1,048,575 | 1.40 / 4.40 | Yes | Yes |
| Z.ai | GLM-5.3 Flash | `zai-org/GLM-5.3-Flash` | 1,048,575 | 0.15 / 0.50 | Yes | Yes |
| Z.ai | GLM-5.2 | `zai-org/GLM-5.2` | 1,048,575 | 1.40 / 4.40 | Yes | Yes |
| DeepSeek | DeepSeek V4 Pro 0813 | `deepseek-ai/DeepSeek-V4-Pro-0813` | 1,048,576 | 1.32 / 3.96 | Yes | Yes |
| DeepSeek | DeepSeek V4.1 Flash | `deepseek-ai/DeepSeek-V4.1-Flash` | 1,000,000 | 0.30 / 1.20 | Yes | Yes |
| DeepSeek | DeepSeek V4.1 Flash 1017 | `deepseek-ai/DeepSeek-V4.1-Flash-1017` | 1,000,000 | 0.30 / 1.20 | Yes | Yes |
| Thinking Machines | Inkling | `thinkingmachines/Inkling` | 524,288 | 1.00 / 4.05 | Yes | Yes |
| MiniMax | MiniMax M3 | `MiniMaxAI/MiniMax-M3` | 524,288 | 0.30 / 1.20 | Yes | Yes |
| MiniMax | MiniMax M3.1 Flash | `MiniMaxAI/MiniMax-M3.1-Flash` | 1,048,576 | 0.15 / 0.60 | Yes | Yes |
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 262,144 | 0.17 / 0.25 | Yes | Yes |
| OpenAI | GPT-OSS 120B | `openai/gpt-oss-120b` | 131,072 | 0.15 / 0.60 | Yes | Yes |
| Meta | Muse Glimmer 30B | `meta-models/Muse-Glimmer-30B` | 131,072 | 0.35 / 1.50 | Yes | Yes |
| Meta | Muse Spark Open 816B A42B | `meta-models/Muse-Spark-Open-816B-A42B` | 1,048,576 | 1.25 / 4.25 | Yes | Yes |
| NVIDIA | Nemotron 3.5 Super VL | `nvidia/NVIDIA-Nemotron-3.5-Super-VL` | 262,144 | 0.15 / 0.50 | Yes | Yes |
| Reflection | Beam 1.0 501B A23B | `reflection/Beam-1.0-501B-A23B` | 1,048,576 | 0.40 / 1.20 | Yes | Yes |
| Qwen | Qwen3.8 2.4T A95B | `Qwen/Qwen3.8-2.4T-A95B` | - | 2.00 / 6.00 | Yes | Yes |
| Qwen | Qwen3.7 Max | `Qwen/Qwen3.7-Max` | - | 2.50 / 7.50 | Yes | Yes |
| Qwen | Qwen3.7 Plus | `Qwen/Qwen3.7-Plus` | 1,000,000 | 0.32 / 1.28 | Yes | Yes |
| Qwen | Qwen3.6 Plus | `Qwen/Qwen3.6-Plus` | 1,000,000 | 0.50 / 3.00 | Yes | Yes |
| Qwen | Qwen3.8 Flash | `Qwen/Qwen3.8-Flash` | 1,000,000 | 0.15 / 0.47 | Yes | Yes |
| Prism ML | Ternary Bonsai 27B | `Prism-ML/Ternary-Bonsai-27B` | 262,144 | free | Yes | Yes |
| Together AI | Tev1 4B Experimental | `together/Tev1-4B-experimental` | 32,768 | 0.042 / free | - | - |

## Vision Models (serverless)

| Organization | Model | API String | Context |
|-------------|-------|-----------|---------|
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 262,144 |
| MiniMax | MiniMax M3 | `MiniMaxAI/MiniMax-M3` | 524,288 |
| Moonshot | Kimi K3 | `moonshotai/Kimi-K3` | 1,048,576 |
| NVIDIA | Nemotron 3.5 Super VL | `nvidia/NVIDIA-Nemotron-3.5-Super-VL` | 262,144 |

Start with `Qwen/Qwen3.5-9B` unless the task needs a larger model.

## Moderation Models

No moderation model is served serverless, and none is listed in the dedicated deployment catalog
(checked 2026-10-07).
