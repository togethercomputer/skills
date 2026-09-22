# Together AI: Sandboxes

Use Together Sandboxes when the user wants to execute Python remotely in a managed sandbox.

Typical fits:

- stateful Python sessions
- data analysis and chart generation
- agent-generated code execution
- file uploads into a remote runtime

## Use this guide for

- The user wants remote execution rather than local shell execution
- Session state needs to persist across multiple calls
- The result may include display outputs such as charts
- A lightweight managed runtime is enough; no custom infra is required

## Do not use this guide for

- full infrastructure control or larger distributed jobs -> `domains/gpu-clusters.md`
- custom containerized runtime logic -> `domains/dedicated-containers.md`
- if the user only wants generated code, not executed code -> `domains/chat-completions.md`

## Workflow

1. Decide whether the task needs code execution or only code generation.
2. Start a session with `client.code_interpreter.execute()`.
3. Reuse `session_id` when the workflow depends on prior state.
4. Inspect `stdout`, `stderr`, structured outputs, and display outputs separately.
5. List sessions only when the user needs operational visibility or cleanup.

## Open next

- **Remote execution with session reuse**
  - Start with [scripts/sandboxes/execute_with_session.py](scripts/sandboxes/execute_with_session.py) or [scripts/sandboxes/execute_with_session.ts](scripts/sandboxes/execute_with_session.ts)
- **Response schema and session listing**
  - Read [references/sandboxes/api-reference.md](references/sandboxes/api-reference.md)
- **MCP-style access for agent workflows**
  - Read [references/sandboxes/api-reference.md](references/sandboxes/api-reference.md)

## Rules

- Treat `session_id` as part of the workflow state.
- Inspect `response.errors` before assuming a run succeeded.
- `plt.show()` with the Agg backend does not reliably produce `display_data` outputs. To retrieve charts, save the figure to a `BytesIO` buffer with `fig.savefig()`, base64-encode it, and print the encoded string to stdout. Parse it from the `stdout` output on the client side. See the chart example in [scripts/sandboxes/execute_with_session.py](scripts/sandboxes/execute_with_session.py).
- Use remote sandboxes when the user benefits from remote stateful execution, not just because Python is involved.
- If the task outgrows the sandbox model, hand off to GPU clusters or dedicated containers.

## Docs

- [Together Sandboxes](https://docs.together.ai/docs/together-code-interpreter)
- [Sandboxes API](https://docs.together.ai/reference/tci-execute)
