---
name: together-togetherlink-configure
description: "Install, configure, update, and undo TogetherLink, Together AI's CLI for running Claude Code, Codex, Claude Desktop, and ChatGPT Desktop on Together AI models: the install script and PATH, togetherlink configure, TOGETHER_API_KEY and --api-key, the optional Anthropic API key for the auto router, Claude Desktop and ChatGPT Desktop on, off, and reset, togetherlink update, and restoring the normal setup. Reach for it whenever the user is setting TogetherLink up or removing it, rather than launching sessions or choosing models."
---

# Together TogetherLink Configure

## Overview

TogetherLink connects existing coding tools and desktop apps (Claude Code, Codex CLI, Claude Desktop and
Cowork, ChatGPT Desktop) to models hosted by Together AI through TogetherLink's hosted gateway. This skill
covers getting it installed and keyed, turning the desktop integrations on and off, keeping it current, and
going back to the normal setup.

TogetherLink is in beta; commands and behavior may change. Official docs:
https://docs.together.ai/docs/togetherlink

## When This Skill Wins

- Install TogetherLink or fix a missing `togetherlink` command after install
- Save, replace, or override the Together API key
- Add or skip the Anthropic API key used by the auto router
- Enable, disable, or reset the Claude Desktop or ChatGPT Desktop integration
- Update TogetherLink
- Stop using TogetherLink and restore the normal tool setup

## Hand Off To Another Skill

Launching sessions, choosing models, headless runs, usage, and image generation belong to together-togetherlink.

- Use `together-chat-completions` or `together-images` when the user is calling the Together API from their
  own code rather than running a coding tool through TogetherLink

## Requirements

- A Together AI API key: https://api.together.ai/settings/projects/~current/api-keys
- The coding tool or desktop app to use, already installed. TogetherLink does not install Claude Code,
  Codex, or the desktop apps.
- Bash and curl for the installer. On Linux, installing Bun also requires `unzip`.
- macOS for the Claude Desktop and ChatGPT Desktop integrations (beta).
- Optional: an Anthropic API key, used by the auto router for frontier routing.

## Install

```bash
curl -fsSL https://link.together.ai/install | bash
```

- The installer also installs [Bun](https://bun.sh) if it is missing.
- Follow any PATH instructions printed at the end of installation, then open a new shell.
- Confirm the install with `togetherlink --help`; `tlink` is a short alias for the same command.

## Configure API Keys

Save the Together API key interactively:

```bash
togetherlink configure
```

- TogetherLink validates the key before saving it.
- It then optionally asks for an Anthropic API key. With one, the auto router sends difficult requests to
  Claude Opus, billed to the Anthropic account behind that key. Skip it and every request is served by a
  Together AI model.
- `configure` stores keys locally in `~/.togetherlink/config.json`.
- Running `togetherlink` with no key configured also prompts for one from the launcher.

Use the environment instead of saving a key (nothing is written to the config file):

```bash
export TOGETHER_API_KEY="your_together_api_key"
```

Override the stored key for a single run by passing `--api-key` before the tool name:

```bash
togetherlink --api-key "$OTHER_TOGETHER_KEY" claude
```

Flags placed after the tool name are passed through to the tool, so `--api-key` must come first.

For scripts and CI, prefer exporting `TOGETHER_API_KEY` from the environment's secret store over running
the interactive `configure` step.

## Desktop Integrations (macOS, Beta)

Both desktop integrations keep a TogetherLink-owned profile separate from the normal one. Desktop profiles
store the Together API key locally.

### Claude Desktop and Cowork

| Command | Effect |
|---|---|
| `togetherlink claude-desktop` | Configure Claude Desktop, Cowork, and Code to use Together AI models |
| `togetherlink claude-desktop off` | Switch back to official Claude; keep the TogetherLink profile for later |
| `togetherlink claude-desktop reset` | Remove the TogetherLink profile and its imported copies |

- `tclaude-desktop` is a shortcut for `togetherlink claude-desktop`.
- If Claude is running, TogetherLink asks before quitting and restarting it.
- `reset` asks for confirmation. Pass `--yes` in scripts to confirm and allow quitting and reopening a
  running app without further prompts.

### ChatGPT Desktop

| Command | Effect |
|---|---|
| `togetherlink chatgpt` | Launch ChatGPT Desktop on the dedicated profile at `~/.codex-togetherlink` |
| `togetherlink chatgpt off` | Relaunch ChatGPT Desktop on the normal profile |
| `togetherlink chatgpt reset` | Delete the dedicated profile, including its local tasks and settings |

- TogetherLink reads but never rewrites the normal `~/.codex` home.
- Native web search is disabled in the TogetherLink profile.
- `reset` asks for confirmation; `--yes` confirms in scripts. `togetherlink chatgpt restore` does the same
  as `reset`.

## Update

TogetherLink periodically checks for updates. To update manually:

```bash
togetherlink update
```

## Restore the Normal Setup

- **Claude Code and Codex CLI:** stop using `togetherlink`, `tclaude`, or `tcodex` and launch the tool
  directly (`claude`, `codex`). These tools receive launch-specific configuration per session only.
- **Claude Desktop:** run `togetherlink claude-desktop off`, or `reset` to also remove the profile.
- **ChatGPT Desktop:** run `togetherlink chatgpt off`, or `reset` to also delete the dedicated profile.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `togetherlink: command not found` after install | Apply the installer's PATH instructions; open a new shell |
| No API key configured | Run `togetherlink configure` or export `TOGETHER_API_KEY` |
| Key rejected during `configure` | Check the key at the Together API keys page and paste it again |
| Auto router never uses Claude Opus | No Anthropic API key is configured; rerun `togetherlink configure` and add one |
| Desktop app still on TogetherLink models | Run the matching `off` command |

Report bugs or feedback at https://github.com/Nutlope/togetherlink/issues.
