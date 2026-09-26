# TogetherLink CLI Reference

Covers the commands for launching and using TogetherLink. Flags drift during the beta; confirm with
`togetherlink --help` and `togetherlink image --help`. Install, `configure`, updates, and switching the desktop
integrations off or removing them belong to `together-togetherlink-configure`.

## Contents

- [Command Shape](#command-shape)
- [Launch Commands](#launch-commands)
- [Global Flags](#global-flags)
- [Information Commands](#information-commands)
- [Image Commands](#image-commands)
- [Headless Pattern](#headless-pattern)

## Command Shape

```text
togetherlink [global flags] TOOL [arguments passed through to the tool]
```

Global flags must come before the tool name. Everything after the tool name is passed to the tool unchanged,
except `--model`, which TogetherLink refuses and answers with a `--main` hint.

## Launch Commands

| Command | Alias | What it does |
|---|---|---|
| `togetherlink` | `tlink` | Interactive launcher: pick Claude Code, Claude Desktop, ChatGPT Desktop, or Codex |
| `togetherlink claude [args]` | `tclaude` | Launch Claude Code for one session |
| `togetherlink codex [args]` | `tcodex` | Launch Codex CLI for one session |
| `togetherlink claude-desktop` | `tclaude-desktop` | Claude Desktop, Cowork, and Code on TogetherLink (macOS, beta) |
| `togetherlink chatgpt` | none | ChatGPT Desktop on the `~/.codex-togetherlink` profile (macOS, beta) |

The desktop integrations persist until switched off; their profiles and the off and reset commands belong to
`together-togetherlink-configure`.

Examples:

```bash
togetherlink claude
togetherlink claude -p "hello" < /dev/null
togetherlink codex exec "Explain this project"
```

## Global Flags

| Flag | Purpose |
|---|---|
| `--main MODEL_ID` | Pin the session to one model instead of `auto`, for example `--main zai-org/GLM-5.3` |
| `--api-key KEY` | Override the stored Together API key for one run (see `together-togetherlink-configure`) |

```bash
togetherlink --main moonshotai/Kimi-K3 claude
```

## Information Commands

| Command | Output |
|---|---|
| `togetherlink models` | Models, IDs, Claude tier, context, and per-1M-token prices (alias `togetherlink list`) |
| `togetherlink usage --last 7d` | Spend tracked by the cloud gateway across sessions, tokens and images |
| `togetherlink --help` | All commands for the installed version |

`togetherlink usage` takes a `--last` window, for example `--last 1d` or `--last 7d`.

## Image Commands

TogetherLink uses the configured Together API key and selects the image model remotely.

```text
togetherlink image generate --prompt TEXT [--quality auto|draft|standard|best] [--seed INT] [--out PATH]
                            [--force] [--json]
togetherlink image edit --image PATH [--image PATH ...] --prompt TEXT [--quality auto|draft|standard|best]
                        [--seed INT] [--out PATH] [--force] [--json]
```

| Flag | Meaning |
|---|---|
| `--prompt` | Text prompt (required) |
| `--image` | Input image for `edit`; repeat for several references |
| `--quality` | `auto` (default), `draft`, `standard`, or `best` |
| `--seed` | Integer seed for repeatable output |
| `--out` | Output path; default `output/imagegen/output.png` |
| `--force` | Overwrite an existing output file |
| `--json` | Machine-readable result |

```bash
togetherlink image generate --prompt "Isometric server rack, flat colors" --quality best --out rack.png
togetherlink image edit --image rack.png --prompt "Add a blue status light" --out rack-v2.png --force
```

Image spend is reported by `togetherlink usage`, separately from token spend.

## Headless Pattern

```bash
togetherlink claude -p "TASK" --output-format json < /dev/null
togetherlink --main zai-org/GLM-5.3-Flash claude -p "TASK" < /dev/null
togetherlink codex exec "TASK" < /dev/null
```

- Always close stdin with `< /dev/null`; an inherited open stdin blocks the run indefinitely.
- In Claude Code's JSON output, `total_cost_usd` is computed at Anthropic prices; use `togetherlink usage`.
