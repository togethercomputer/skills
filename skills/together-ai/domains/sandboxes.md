# Together AI: Sandboxes

Managed remote Python execution with stateful sessions, for running agent-written code, data
analysis, and charts. The API namespace is still `client.code_interpreter`. Long-running or GPU
workloads go to `domains/gpu-clusters.md` or `domains/dedicated-containers.md`.

## Workflow

1. Confirm the task needs code *executed*, not only written.
2. `client.code_interpreter.execute(code=..., language="python")`.
3. Pass the returned `session_id` back on later calls to keep variables and files.
4. Read `stdout`, `stderr`, and display outputs separately, and check `response.errors` before
   assuming the run worked.

## Rules

- Treat `session_id` as workflow state; losing it loses the session's variables.
- `plt.show()` does not reliably return a chart. Save the figure to a `BytesIO` with
  `fig.savefig()`, base64-encode it, print it, and decode it from `stdout` on the client.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/sandboxes/execute_with_session.py](scripts/sandboxes/execute_with_session.py) (.ts) | 130 | execute, reuse a session, file upload, chart round-trip | running code remotely |
| [references/sandboxes/api-reference.md](references/sandboxes/api-reference.md) | 276 | execute request and response schema, session listing, preinstalled packages, pricing, MCP access | a response field, package, or limit question |

## Docs

- [Together Sandboxes](https://docs.together.ai/docs/together-code-sandbox)
- [Sandboxes API](https://docs.together.ai/reference/tci-execute)
