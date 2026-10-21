# Together AI: Sandboxes

Together code sandbox runs commands and code in isolated VMs built from Docker-image snapshots, for
model-generated code, agent tool calls, data analysis, and RL rollout environments. It ships as its
own package, `together-sandbox` (Python SDK, TypeScript SDK, and CLI), separate from the `together`
SDK, and must be enabled for the organization: if a key that works with the `together` SDK is
rejected here, ask the user to [request access](https://www.together.ai/contact). Long-running
services or GPU workloads go to `domains/dedicated-containers.md` or `domains/gpu-clusters.md`.

> **Code Interpreter is retired.** `POST /tci/execute` and `GET /tci/sessions` return HTTP 404, so
> `client.code_interpreter.execute()` and `client.code_interpreter.sessions.list()`
> (`client.codeInterpreter` in TypeScript) fail, and the next major SDK release removes them. Do not
> use or retry them. Rewrite the code with `together-sandbox` as below; the mapping is in
> [api-reference.md](references/sandboxes/api-reference.md#migrating-from-code-interpreter).

## Workflow

1. Confirm the task needs code *executed*, not only written.
2. Install the package: `pip install together-sandbox` (Python 3.10+) or
   `npm install together-sandbox` (Node.js 18+). It reads `TOGETHER_API_KEY`.
3. Get a snapshot. Reuse one by alias (`snapshots.get_by_alias("my-python@v1")`) before building;
   otherwise create one from a public image or a Dockerfile context with an alias (`namespace@tag`).
   Together builds it remotely, so no local Docker is needed.
4. `sandbox = await sdk.sandboxes.create(snapshot_alias="my-python@v1", ttl=600)`. Creation starts
   the VM and returns a connected sandbox; there is no start step.
5. Write inputs with `sandbox.files.create(path, content)`, run with
   `sandbox.execs.exec("python3", ["/work/main.py"])`, and read `exit_code` and `output` from the
   result. Read result files back with `sandbox.files.read(path)`.
6. `await sandbox.terminate()` in a `finally` block, then confirm nothing you created is still
   running.

## Rules

- **Terminate explicitly.** A sandbox runs until it is terminated or its `ttl` (seconds) elapses.
  `async with` closes the HTTP connection only; it does not terminate the VM. Set a `ttl` as a
  backstop. `together-sandbox sandboxes list` shows what is still running.
- **Termination is permanent.** A sandbox is ephemeral by default, so its filesystem is discarded.
  To keep state, terminate with `snapshot={"aliases": ["my-app@v2"]}` and create a new sandbox from
  that snapshot. The produced snapshot is also aliased `sandbox:<sandbox_id>`.
- **Each exec is a new process.** Files persist across execs in the same sandbox; Python variables
  do not. Code Interpreter's `session_id` reuse becomes one running sandbox plus state in files.
- **Check `exit_code`, not output text.** `output` is stdout and stderr joined in arrival order.
  A nonzero `exit_code` is a failure, and `exec` raises if the stream ends without one.
- **`files.read` returns text.** For a chart or other binary output, base64-encode it in the sandbox,
  print it or write it to a file, and decode it on the client.
- **`TOGETHER_BASE_URL` changes where `together-sandbox` sends requests.** It overrides the sandbox
  management API (default `https://api.bartender.codesandbox.io`). If the environment sets it for the
  `together` SDK, unset it for sandbox code or pass `base_url` (`baseUrl` in TypeScript) explicitly.
- **Do not retry `snapshots.create` blindly.** It is not idempotent, so a retry after a transient
  error can register a duplicate. Look the alias up first.
- Each sandbox gets 1 vCPU and 2 GiB of memory by default. `cpu` takes 0.1 to 16 cores and
  `memory_bytes` takes 1 to 8 GB per CPU.

## Open next

| File | Lines | Contains | Open when |
|---|---|---|---|
| [scripts/sandboxes/run_in_sandbox.py](scripts/sandboxes/run_in_sandbox.py) (.ts) | 117 | reuse or build a snapshot, create a sandbox with a TTL, write a file, run Python, read the result, terminate | running code remotely |
| [references/sandboxes/api-reference.md](references/sandboxes/api-reference.md) | 215 | install, env vars, snapshots, sandbox create/connect/list/terminate, execs, files, states, errors, CLI, Code Interpreter migration | a parameter, state, error, or CLI question, or porting Code Interpreter code |

## Docs

- [Together code sandbox](https://docs.together.ai/docs/together-code-sandbox)
- [Python SDK reference](https://github.com/togethercomputer/together-sandbox/blob/main/docs/python-sdk.md)
- [TypeScript SDK reference](https://github.com/togethercomputer/together-sandbox/blob/main/docs/typescript-sdk.md)
- [CLI reference](https://github.com/togethercomputer/together-sandbox/blob/main/docs/cli.md)
