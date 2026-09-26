# TogetherLink Models Reference

TogetherLink is beta and its model list changes. Treat this file as orientation and run
`togetherlink models` (alias `togetherlink list`) for the live list, context limits, Claude tiers, and prices
before pinning or quoting anything.

## Models

| Model | Model ID | Claude Code tier | Context | Capabilities |
|---|---|---|---|---|
| Auto (default) | `auto` | none (default) | 1M | Vision, reasoning. Routes between Together AI models and Opus |
| Kimi K3 | `moonshotai/Kimi-K3` | Opus | 1M | Vision, reasoning |
| GLM 5.3 | `zai-org/GLM-5.3` | Fable | 1M | Reasoning |
| GLM 5.3 Flash | `zai-org/GLM-5.3-Flash` | Sonnet | 1M | Vision, reasoning |
| DeepSeek V4.1 Flash | `deepseek-ai/DeepSeek-V4.1-Flash` | Haiku | 1M | Vision, reasoning |

Prices are per 1M tokens (input, cached input, output) and are shown only by `togetherlink models`. Together AI
models are billed at standard serverless rates; see
[serverless models](https://docs.together.ai/docs/serverless/models).

## Auto Router

`auto` is a virtual model. For each request the gateway classifies the prompt and routes it:

- straightforward requests go to a Together AI model (such as GLM 5.3), billed at serverless rates
- harder requests go to Claude Opus through Anthropic, billed to the Anthropic API key configured for
  TogetherLink

Without an Anthropic key, every request is served by a Together AI model. Setting that key up belongs to
`together-togetherlink-configure`.

## Pinning A Model

```bash
togetherlink --main zai-org/GLM-5.3 claude
togetherlink --main deepseek-ai/DeepSeek-V4.1-Flash codex
```

- `--main` goes before the tool name; `--model` after the tool name is refused.
- `tclaude` and `tcodex` cannot pin a model, because they expand with the tool name first.

## Claude Code Tier Mapping

Inside a Claude Code session, `/model` shows Claude's tiers, and each maps to a Together AI model:

| Claude Code tier | Served by |
|---|---|
| Opus | Kimi K3 |
| Fable | GLM 5.3 |
| Sonnet | GLM 5.3 Flash |
| Haiku | DeepSeek V4.1 Flash |

The same mapping applies anywhere Claude Code picks a tier by alias, such as a subagent configured as `sonnet`
(served by GLM 5.3 Flash) or `haiku` (served by DeepSeek V4.1 Flash). A `model` key in Claude Code's
`settings.json` does not change the session model under TogetherLink; use `--main` or `/model`.

Codex CLI and the desktop apps expose their own model menus, which can differ from Claude Code's tiers.
