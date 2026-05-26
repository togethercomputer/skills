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
- **SDK reference (snapshots, sandboxes, exec, files)**
  - Read [references/api-reference.md](references/api-reference.md)
- **RL training patterns (GRPO batch, reward collection, golden images)**
  - Read [references/rl-patterns.md](references/rl-patterns.md)
- **Parallel fan-out for batch evaluation**
  - Start with [scripts/parallel_fanout.py](scripts/parallel_fanout.py)

## Workflow

1. Install the SDK: `pip install "together-sandbox @ git+https://github.com/togethercomputer/together-sandbox.git#subdirectory=together-sandbox-python"`.
2. Create a snapshot from a Docker image or Dockerfile using `sdk.snapshots.create()`.
3. Create a sandbox from the snapshot using `sdk.sandboxes.create()` with CPU, memory, and disk specs.
4. Start the sandbox using `sdk.sandboxes.start()`, which returns a connected `Sandbox` object.
5. Configure DNS inside the sandbox as the first exec (sandboxes have no DNS by default).
6. Execute commands with `sandbox.execs.create()` and poll results with `sandbox.execs.get_output()`. Read/write files with `sandbox.files`.
7. For RL: collect reward files from the sandbox filesystem after test execution.
8. Shut down with `sandbox.shutdown()` or hibernate with `sandbox.hibernate()` to capture state.

## High-Signal Rules

- The SDK is async-native. All methods are `async`. Use `asyncio.run()` or an async context.
- The SDK is not yet on PyPI. Install from GitHub: `pip install "together-sandbox @ git+https://github.com/togethercomputer/together-sandbox.git#subdirectory=together-sandbox-python"`.
- Sandboxes have no DNS by default. Run `echo "nameserver 1.1.1.1" > /etc/resolv.conf` as your first exec or all network calls will fail.
- Tools installed via pip land in `/root/.local/bin`, which is not on PATH. Run `export PATH="/root/.local/bin:$PATH"` before using them.
- Command execution is two-step: `exec_item = await sandbox.execs.create("bash", ["-c", "cmd"], autorun=True)` then poll `await sandbox.execs.get_output(exec_item.id)` for results. There is no single-call `exec()` method.
- `get_output()` returns `list[ExecStdout]`. Each item has `.output` (str) and `.exit_code` (int or Unset). Poll until an item has `exit_code` set to know the command finished.
- `sdk.sandboxes.create()` returns a `SandboxModel` (metadata). `sdk.sandboxes.start()` returns a connected `Sandbox` with exec and file access. These are two separate steps.
- The SDK handles authentication automatically. Set `TOGETHER_API_KEY` and the two-auth system (management API + in-sandbox Pint API) is abstracted away.
- Ephemeral sandboxes (`ephemeral=True`) auto-delete on stop and cannot hibernate. Use for disposable training runs.
- For parallel fan-out, use `asyncio.gather()` to create and start multiple sandboxes concurrently.

## Resource Map

- **API reference**: [references/api-reference.md](references/api-reference.md)
- **RL workflow patterns**: [references/rl-patterns.md](references/rl-patterns.md)
- **Sandbox lifecycle script**: [scripts/sandbox_lifecycle.py](scripts/sandbox_lifecycle.py)
- **Parallel fan-out script**: [scripts/parallel_fanout.py](scripts/parallel_fanout.py)

## Official Docs

- [Together Sandbox SDK](https://github.com/togethercomputer/together-sandbox)
