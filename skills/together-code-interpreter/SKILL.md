---
name: together-code-interpreter
description: Use this skill for Together AI Code Interpreter workflows: remote Python execution, session reuse, file uploads, data analysis, plots, and stateful notebook-like runs through the TCI API. Reach for it whenever the user wants managed remote Python execution on Together AI instead of local execution, raw clusters, or full model hosting.
---

# Together Code Interpreter

## Overview

Use Together Code Interpreter when the user wants to execute Python remotely in a managed sandbox.

Typical fits:

- stateful Python sessions
- data analysis and chart generation
- agent-generated code execution
- file uploads into a remote runtime

## When This Skill Wins

- The user wants remote execution rather than local shell execution
- Session state needs to persist across multiple calls
- The result may include display outputs such as charts
- A lightweight managed runtime is enough; no custom infra is required

## Hand Off To Another Skill

- Use `together-gpu-clusters` for full infrastructure control or larger distributed jobs
- Use `together-dedicated-containers` for custom containerized runtime logic
- Use `together-chat-completions` if the user only wants generated code, not executed code

## Quick Routing

- **Remote execution with session reuse**
  - Start with [scripts/execute_with_session.py](scripts/execute_with_session.py) or [scripts/execute_with_session.ts](scripts/execute_with_session.ts)
- **Response schema and session listing**
  - Read [references/api-reference.md](references/api-reference.md)
- **MCP-style access for agent workflows**
  - Read [references/api-reference.md](references/api-reference.md)

## Workflow

1. Decide whether the task needs code execution or only code generation.
2. Start a session with `client.code_interpreter.execute()`.
3. Reuse `session_id` when the workflow depends on prior state.
4. Inspect `stdout`, `stderr`, structured outputs, and display outputs separately.
5. List sessions only when the user needs operational visibility or cleanup.

## High-Signal Rules

- Treat `session_id` as part of the workflow state.
- Inspect `response.errors` before assuming a run succeeded.
- Use this skill when the user benefits from remote stateful execution, not just because Python is involved.
- If the task outgrows the sandbox model, hand off to GPU clusters or dedicated containers.

## Resource Map

- **API reference**: [references/api-reference.md](references/api-reference.md)
- **Alternative access patterns**: [references/api-reference.md](references/api-reference.md)
- **Python workflow**: [scripts/execute_with_session.py](scripts/execute_with_session.py)
- **TypeScript workflow**: [scripts/execute_with_session.ts](scripts/execute_with_session.ts)

## Official Docs

- [Together Code Interpreter](https://docs.together.ai/docs/together-code-interpreter)
- [TCI API](https://docs.together.ai/reference/tci-execute)
