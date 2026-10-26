# Together AI: Sandboxes

Run commands and code in isolated remote sandboxes built from Docker-image snapshots, through the
separate `together-sandbox` SDK and CLI, which must be enabled for the organization first. Long
GPU or always-on work goes to `domains/gpu-clusters.md` or `domains/dedicated-containers.md`.

**The code interpreter API is gone.** Checked 2026-10-26: `POST /v1/tci/execute` returns 404,
`client.code_interpreter` is missing from Python `together` 3.0.0 and `client.codeInterpreter`
from `together-ai` 1.0.0, and the API reference no longer lists it. Do not build on it.

## Workflow

1. Confirm the task needs code *executed*, not only written.
2. Confirm the organization has `together-sandbox` access (it is allowlisted; the user requests it
   at https://www.together.ai/contact). Without access, say so and stop.
3. Install `together-sandbox` (Python, TypeScript, or the CLI); it reads `TOGETHER_API_KEY`.
4. Create a snapshot from a Docker image or build context, create a sandbox from it, run commands
   with `sandbox.execs.exec(...)`, and move files with `sandbox.files`.
5. Call `terminate()` when done.

## Rules

- Sandboxes run until terminated unless created with a `ttl` (CLI: `sandboxes run --rm`). Closing
  the async client does not terminate one.
- Termination is permanent and discards the filesystem; snapshot on terminate to keep state.
- This skill has no verified `together-sandbox` examples yet; follow the linked references.

## Docs

- [Code sandbox](https://docs.together.ai/docs/together-code-sandbox): setup, snapshots, lifecycle
- [Python SDK reference](https://github.com/togethercomputer/together-sandbox/blob/main/docs/python-sdk.md)
- [TypeScript SDK reference](https://github.com/togethercomputer/together-sandbox/blob/main/docs/typescript-sdk.md)
- [CLI reference](https://github.com/togethercomputer/together-sandbox/blob/main/docs/cli.md)
