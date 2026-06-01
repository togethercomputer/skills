---
name: together-sandbox
description: "Isolated gVisor sandboxes for RL training, SFT data generation, and coding agent rollouts on Together AI. Create snapshots from Docker images, run multi-turn bash commands, read and write files, and manage sandbox lifecycle via the together-sandbox Python SDK. Reach for it whenever the user needs isolated container execution for agent environments, reward computation, or parallel code evaluation rather than managed Python notebooks or raw GPU clusters."
---

# Together Sandbox

## Overview

Use Together Sandbox when the user needs isolated container environments for executing untrusted code, running RL training loops, or orchestrating coding agent rollouts.

Typical fits:

- GRPO/RL training with parallel sandbox-based reward computation
- SFT data generation with verified trajectory collection
- Coding agent rollouts (multi-turn bash execution in isolated environments)
- Batch evaluation of code against test suites (SWE-bench, Terminal-Bench)
- Any workflow requiring Docker-image-based environments with file I/O and command execution

## When This Skill Wins

- The user needs isolated container execution from a Docker image, not just a Python notebook
- Sandboxes must survive multi-turn command sequences (1-10 sequential bash commands)
- The workflow requires parallel sandbox fan-out (8-256+ concurrent environments)
- Files need to be uploaded to or downloaded from the sandbox filesystem
- The user references RL training, GRPO, reward computation, verifier environments, or coding agents

## Hand Off To Another Skill

- Use `together-sandboxes` (plural) for managed Python notebook execution via the Code Interpreter API
- Use `together-gpu-clusters` for multi-node GPU compute or distributed training jobs
- Use `together-dedicated-containers` for custom containerized inference workers
- Use `together-fine-tuning` for model training jobs (LoRA, DPO, full fine-tuning)
- Use `together-chat-completions` if the user only needs inference, not code execution

## Quick Routing

- **Create a sandbox and run commands**
  - Start with [scripts/sandbox_lifecycle.py](scripts/sandbox_lifecycle.py)
- **Full SDK API (snapshots, sandboxes, execs, files, retries)**
  - Read the SDK's own docs — see [SDK Reference](#sdk-reference) below
- **RL training patterns (GRPO batch, reward collection, golden images)**
  - Read [references/rl-patterns.md](references/rl-patterns.md)
- **Parallel fan-out for batch evaluation**
  - Start with [scripts/parallel_fanout.py](scripts/parallel_fanout.py)

## Workflow

1. Install the SDK: `pip install together-sandbox` (Python). See [SDK Reference](#sdk-reference) for TypeScript.
2. Create a snapshot from a Docker image or Dockerfile using `sdk.snapshots.create()`.
3. Create a sandbox from the snapshot using `sdk.sandboxes.create()` with CPU, memory, and disk specs.
4. Start the sandbox using `sdk.sandboxes.start()`, which returns a connected `Sandbox` object.
5. Configure DNS inside the sandbox as the first exec (sandboxes have no DNS by default).
6. Run commands with `sandbox.execs.exec("bash", ["-c", cmd])` and read/write files with `sandbox.files`.
7. For RL: collect reward files from the sandbox filesystem after test execution.
8. Shut down or hibernate via the instance (`await sandbox.shutdown()`) or by ID (`await sdk.sandboxes.shutdown(sandbox.id)`).

## High-Signal Rules

- The SDK is async-native. All methods are `async`. Use `asyncio.run()` or an async context.
- Run a command to completion with `sandbox.execs.exec("bash", ["-c", cmd])`, which returns a dict `{"exit_code": int, "output": str}`. For long-running or interactive commands, create the exec with `sandbox.execs.create(...)` and stream with `sandbox.execs.stream_output(id)`. Always wrap shell commands in `bash -c`.
- Sandboxes have no DNS by default. Run `echo "nameserver 1.1.1.1" > /etc/resolv.conf` as your first exec or all network calls will fail.
- Tools installed via pip land in `/root/.local/bin`, which is not on PATH. Run `export PATH="/root/.local/bin:$PATH"` before using them.
- `sdk.sandboxes.create()` returns a `SandboxModel` (metadata). `sdk.sandboxes.start()` returns a connected `Sandbox` with exec and file access. These are two separate steps.
- The SDK handles authentication automatically. Set `TOGETHER_API_KEY` and the two-auth system (management API + in-sandbox agent API) is abstracted away.
- Ephemeral sandboxes (`ephemeral=True`) auto-delete on stop and cannot hibernate. Use for disposable training runs.
- For parallel fan-out, use `asyncio.gather()` to create and start multiple sandboxes concurrently.
- Shut down or hibernate either on the connected instance (`await sandbox.shutdown()` / `await sandbox.hibernate()`) or by ID via the namespace (`await sdk.sandboxes.shutdown(sandbox.id)`). Both forms are valid.

## Resource Map

- **Full SDK API**: see [SDK Reference](#sdk-reference)
- **RL workflow patterns**: [references/rl-patterns.md](references/rl-patterns.md)
- **Sandbox lifecycle script**: [scripts/sandbox_lifecycle.py](scripts/sandbox_lifecycle.py)
- **Parallel fan-out script**: [scripts/parallel_fanout.py](scripts/parallel_fanout.py)

## SDK Reference

The SDK ships its own authoritative, version-matched API docs. **Do not restate the API surface in this skill** — read the SDK docs directly so guidance never drifts from the installed version:

- **Python (primary):** [docs/python-sdk.md](https://github.com/togethercomputer/together-sandbox/blob/main/docs/python-sdk.md)
- **TypeScript:** [docs/typescript-sdk.md](https://github.com/togethercomputer/together-sandbox/blob/main/docs/typescript-sdk.md)
- **CLI:** [docs/cli.md](https://github.com/togethercomputer/together-sandbox/blob/main/docs/cli.md)

### Install

Python (published on PyPI):

```bash
pip install together-sandbox
```

The TypeScript SDK (`@together-sandbox/sdk`) is not yet on npm — until it is published, install from source per the repo instructions: [github.com/togethercomputer/together-sandbox](https://github.com/togethercomputer/together-sandbox).
