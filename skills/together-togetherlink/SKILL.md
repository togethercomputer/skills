---
name: together-togetherlink
description: "Run Claude Code, Codex CLI, Claude Desktop and Cowork, or ChatGPT Desktop on Together AI models through the TogetherLink CLI: launching sessions (togetherlink claude, tclaude, tcodex), pinning a model with --main, the auto router, the Claude tier to model mapping, headless print-mode runs, spend with togetherlink usage, image generation from a session, and launch troubleshooting. Reach for it whenever the user wants to use a coding agent or desktop app with Together AI models via TogetherLink, rather than install or configure TogetherLink or call the Together API from their own code."
---

# Together TogetherLink

## Overview

TogetherLink is Together AI's CLI (beta) that launches an existing coding tool or desktop app against models
hosted by Together AI. Each launch points the tool at TogetherLink's hosted gateway, which serves every request
from a Together AI model or, on the auto router, from Claude Opus through Anthropic. Claude Code and Codex CLI
launches are configured per session, so launching the tool directly restores the usual setup.

Use this skill for:

- launching Claude Code, Codex CLI, Claude Desktop and Cowork, or ChatGPT Desktop through TogetherLink
- choosing between the auto router and a pinned Together AI model
- understanding which model serves each Claude Code tier in `/model`
- headless print-mode runs from scripts, CI, or other agents
- checking spend with `togetherlink usage`
- generating or editing images from a TogetherLink session or the `togetherlink image` command
- diagnosing a launch that picks the wrong model, hangs, or reports the wrong cost

## When This Skill Wins

- "Run Claude Code on GLM 5.3" or "use Kimi K3 in Codex"
- "Which model am I actually on in tclaude?"
- "My headless togetherlink run never returns"
- "How much did my TogetherLink sessions cost this week?"
- "Generate an image from my TogetherLink session"

## Hand Off To Another Skill

Installing TogetherLink, API keys, the desktop integrations, updates, and restoring your normal setup
belong to together-togetherlink-configure; building your own app on the Together API belongs to
together-chat-completions or together-images.

- Use `together-togetherlink-configure` for the install script, PATH, `togetherlink configure`, the Anthropic
  key, turning the Claude Desktop or ChatGPT Desktop integration off or removing it, and updating the CLI
- Use `together-chat-completions` for calling Together AI models from Python, TypeScript, or REST
- Use `together-images` for FLUX, Kontext, or LoRA image generation through the Together SDK or API

## Quick Routing

- **Launch a tool** - see [Launch](#launch) below
- **Pin a model or read the tier mapping** - read [references/models.md](references/models.md), then run
  `togetherlink models` for the live list, context limits, and prices
- **Every command and flag** - read [references/cli-reference.md](references/cli-reference.md)
- **Headless or scripted run** - see [Run Headless](#run-headless)
- **Image generation** - see [Generate Images](#generate-images) and the image section of
  [references/cli-reference.md](references/cli-reference.md)
- **Something looks wrong** - see [Troubleshooting](#troubleshooting)

## Launch

Run `togetherlink` (alias `tlink`) with no arguments for an interactive launcher, or launch a tool directly:

| Command | Shortcut | Launches |
|---|---|---|
| `togetherlink claude` | `tclaude` | Claude Code |
| `togetherlink codex` | `tcodex` | Codex CLI |
| `togetherlink claude-desktop` | `tclaude-desktop` | Claude Desktop, Cowork, and Code (macOS, beta) |
| `togetherlink chatgpt` | none | ChatGPT Desktop on a dedicated profile (macOS, beta) |

Arguments after the tool name pass through to the tool:

```bash
togetherlink claude --continue
togetherlink codex exec "Explain this project"
```

Every session starts with a routing banner such as `togetherlink ▸ Claude Code → Auto router.`; check it to
confirm which route is serving the session. Each session prints a cost summary when it exits.

The Claude Code and Codex CLI launches are per session: the configuration exists only for that process. The
desktop integrations persist until they are switched off; that belongs to `together-togetherlink-configure`.

## Choose A Model

Sessions default to the virtual `auto` model. The gateway classifies each request and sends straightforward
ones to a Together AI model and harder ones to Claude Opus, billed to the Anthropic key configured for
TogetherLink. With no Anthropic key, every request is served by a Together AI model.

To pin one model for the whole session, pass `--main` with the model ID before the tool name:

```bash
togetherlink --main zai-org/GLM-5.3 claude
togetherlink --main moonshotai/Kimi-K3 codex
```

Rules the agent must follow:

- Put `--main` before the tool name. Everything after the tool name goes to the tool.
- TogetherLink refuses `--model` after the tool name (`togetherlink claude --model x` fails with a `--main`
  hint), because harness model aliases do not select gateway routes.
- The shortcuts (`tclaude`, `tcodex`) expand with the tool name first, so they cannot pin a model. Use the full
  `togetherlink --main ID claude` form instead.
- Inside a Claude Code session, `/model` switches tiers, and each tier maps to a Together AI model (Opus runs
  Kimi K3, Fable runs GLM 5.3, Sonnet runs GLM 5.3 Flash, Haiku runs DeepSeek V4.1 Flash). See
  [references/models.md](references/models.md).
- Desktop apps expose their own model menus, which can differ from the terminal tools.

## Run Headless

Print mode works for scripts, CI jobs, and agents driving TogetherLink:

```bash
togetherlink claude -p "Summarize the open TODOs in this repo" --output-format json < /dev/null
togetherlink --main zai-org/GLM-5.3-Flash claude -p "Reply with pong" < /dev/null
```

Always close stdin with `< /dev/null`. A headless process that inherits an open stdin waits for more input and
blocks indefinitely.

## Check Spend

```bash
togetherlink usage --last 7d
```

This shows spend tracked by the gateway across sessions, including image spend (tracked separately from
tokens). Use it, not Claude Code's own cost figure: the `total_cost_usd` field in `--output-format json` output
is computed at Anthropic prices and overstates what Together AI bills for the models TogetherLink serves.
Together AI models are billed at standard serverless rates for the model that served each request.

## Generate Images

Sessions launched through TogetherLink include an image generation skill, so the user can ask the agent
directly:

```text
Generate an image of a red circle on a white background and save it to logo.png
```

Outside a session, or from a script, call the CLI:

```bash
togetherlink image generate --prompt "A red circle on a white background" --out logo.png
togetherlink image edit --image logo.png --prompt "Make the circle blue" --out logo-blue.png
```

TogetherLink picks the image model remotely; the default output path is `output/imagegen/output.png`. Flags are
in [references/cli-reference.md](references/cli-reference.md). For a specific FLUX or Kontext model, LoRAs, or
image generation inside the user's own app, use `together-images` instead.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `--model` rejected | Move the choice before the tool: `togetherlink --main ID claude` |
| `tclaude` ignores the wanted model | Shortcuts cannot pin a model; use `togetherlink --main ID claude` |
| `settings.json` `model` has no effect | TogetherLink sets the session model and wins; use `--main` or `/model` |
| A headless run hangs | Append `< /dev/null` to close stdin |
| JSON output reports a high cost | `total_cost_usd` uses Anthropic prices; read `togetherlink usage` |
| Commits and PRs have no co-author trailer | TogetherLink blanks Claude Code attribution; add one if needed |
| "Claude Code is not installed" | TogetherLink does not install tools; run the install command in the error |
| No API key configured | Hand off to `together-togetherlink-configure` |
| Unsure which route served a session | Read the routing banner at session start, then `togetherlink usage` |

## High-Signal Rules

- TogetherLink is beta: model IDs, tiers, and flags can change. Run `togetherlink models` and `togetherlink --help`
  for live values before hard-coding anything.
- Never pin a model with a tool's own `--model` flag or with a shortcut alias.
- Always end non-interactive runs with `< /dev/null`.
- Report spend from `togetherlink usage`, not from the tool's own cost estimate.
- Do not quote prices from memory; they come from `togetherlink models`.

## Resource Map

- **Command and flag reference**: [references/cli-reference.md](references/cli-reference.md)
- **Models, tier mapping, and routing**: [references/models.md](references/models.md)

## Official Docs

- [TogetherLink](https://docs.together.ai/docs/togetherlink)
- [Serverless models and pricing](https://docs.together.ai/docs/serverless/models)
- [TogetherLink on GitHub](https://github.com/Nutlope/togetherlink) (issues and release history)
