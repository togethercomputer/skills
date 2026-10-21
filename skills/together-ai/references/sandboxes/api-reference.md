# Code Sandbox SDK Reference
## Contents

- [Install and configure](#install-and-configure)
- [Snapshots](#snapshots)
- [Sandboxes](#sandboxes)
- [Run commands](#run-commands)
- [Files and directories](#files-and-directories)
- [Sandbox states](#sandbox-states)
- [Errors and retries](#errors-and-retries)
- [CLI](#cli)
- [Migrating from Code Interpreter](#migrating-from-code-interpreter)
- [Full reference](#full-reference)

Checked against `together-sandbox` 4.1.1 (Python and TypeScript). The package is separate from the
`together` SDK and must be enabled for the organization.

## Install and configure

```bash
pip install together-sandbox        # Python 3.10+
npm install together-sandbox        # Node.js 18+
curl -fsSL https://raw.githubusercontent.com/togethercomputer/together-sandbox/main/install.sh | bash  # CLI
```

| Variable | Description |
|---|---|
| `TOGETHER_API_KEY` | Required. Also accepted as `api_key` (Python) or `apiKey` (TypeScript). |
| `TOGETHER_BASE_URL` | Overrides the sandbox management API, default `https://api.bartender.codesandbox.io`. The `together` SDK reads the same variable, so unset it for sandbox code when it points at a Together inference host. |

The Python SDK is async. Use it as `async with TogetherSandbox() as sdk:` inside `asyncio.run()`.
Leaving the block closes HTTP connections and does not terminate sandboxes.

## Snapshots

A snapshot is an immutable disk image that sandboxes boot from. Build one from a public image or a
Docker build context; Together's remote builder does the work, so no local Docker is needed.
Address it by ID or by a mutable alias, `tag` or `namespace@tag`.

```python
from together_sandbox import CreateContextSnapshotParams, CreateImageSnapshotParams

result = await sdk.snapshots.create(
    CreateImageSnapshotParams(image="python:3.12-slim", alias="my-python@v1")
)
result = await sdk.snapshots.create(
    CreateContextSnapshotParams(context="./my-app", alias="my-app@v1", cache_key="my-app")
)
print(result.snapshot_id, result.alias)
```

```typescript
const result = await sdk.snapshots.create({
  image: "python:3.12-slim",
  alias: "my-python@v1",
});
console.log(result.snapshotId, result.alias);
```

| Parameter | Applies to | Description |
|---|---|---|
| `image` | image | Docker image reference, such as `python:3.12-slim`. |
| `context` | context | Path to the build context. Uses its `Dockerfile` unless `dockerfile` is set. |
| `dockerfile` | context | Path to another Dockerfile. |
| `cache_key` / `cacheKey` | context | Stable key so repeated builds share a layer cache. Without one, every build is cold. |
| `alias` | both | `namespace@tag`. |
| `ttl` | context | Seconds before the snapshot retires itself. |
| `on_progress` / `onProgress` | both | Callback receiving `step` (`prepare`, `build`, `auth`, `push`, `register`, `alias`) and `output`. |

Other calls (Python names; TypeScript uses camelCase): `get_by_alias(alias)` and `get_by_id(id)`
return metadata or raise `HttpError` 404; `alias(snapshot_id, alias)` points an alias at a snapshot;
`list(limit=, cursor=, exclude_retired=, tags=)` returns an async-iterable `Page`;
`retire_by_id(id)` (TypeScript `retire(id)`) stops new sandboxes from using it.

`snapshots.create` is not idempotent. Look the alias up before building, and exclude it from custom
retry rules.

## Sandboxes

```python
sandbox = await sdk.sandboxes.create(snapshot_alias="my-python@v1", ttl=600, tags={"task": "demo"})
print(sandbox.id)
await sandbox.terminate()
```

```typescript
const sandbox = await sdk.sandboxes.create({ snapshotAlias: "my-python@v1", ttl: 600 });
await sandbox.terminate();
```

| Parameter (Python / TypeScript) | Default | Description |
|---|---|---|
| `snapshot_id` / `snapshotId` | none | Snapshot to boot. Pass this or the alias. |
| `snapshot_alias` / `snapshotAlias` | none | Alias to boot, such as `my-python@v1` or `sandbox:<id>`. |
| `cpu` | `1.0` | Cores, 0.1 to 16. |
| `memory_bytes` / `memoryBytes` | 2 GiB | 1 to 8 GB per CPU. |
| `ttl` | none | Seconds after creation before the sandbox terminates itself. |
| `tags` | none | Key/value labels, filterable in `list`. IDs are platform UUIDs, so name things with tags. |
| `termination_policy` / `terminationPolicy` | ephemeral | `{"snapshot": {"aliases": [...], "memory": bool, "ttl": int, "tags": {...}}}` to snapshot on termination. |

`create` starts the VM and returns a connected sandbox. Other calls on `sdk.sandboxes`:

- `connect(sandbox_id)`: reattach to a running sandbox and get `.files`, `.execs`, and the rest.
- `get(sandbox_id)`: metadata only (`status`, `status_reason`); no in-VM namespaces.
- `list(limit=, cursor=, statuses=, snapshot_id=, tags=)`: async-iterable `Page`.
- `terminate(sandbox_id, snapshot=...)`: terminate by ID without a connected sandbox.

`sandbox.terminate()` uses the stored termination policy. Pass
`snapshot={"aliases": ["my-app@v2"]}` to keep the filesystem, add `"memory": True` to resume running
processes later, or pass `snapshot=None` (TypeScript `null`) for a teardown with no snapshot. A
terminated sandbox cannot restart: create a new one from the snapshot it produced, which is aliased
`sandbox:<sandbox_id>`.

## Run commands

`execs.exec(command, args, cwd=, env=, user=, pty=)` runs to completion. Python returns a dict with
`exit_code` and `output`; TypeScript returns `{ exitCode, output }`. `output` is stdout and stderr
joined in arrival order. It raises if the stream ends without an exit code, for example when the
sandbox shuts down mid-run. Commands run as `1000:1000` unless `user` is set.

```python
result = await sandbox.execs.exec("python3", ["-c", "print(6 * 7)"])
if result["exit_code"] != 0:
    raise RuntimeError(result["output"])
```

For long-running processes, start one with `execs.create(command, args, autostart=True)`, then read
it with `execs.stream_output(id)` (SSE) or poll `execs.get_output(id)`, whose `exit_code` stays
`None` until the process exits. `execs.send_stdin(id, data)` writes to stdin, `execs.list()` shows
active execs, and `execs.delete(id)` removes one.

Each exec is a new process. To carry state between steps, write it to files in the sandbox or run
the whole job as one script.

## Files and directories

| Call | Description |
|---|---|
| `files.create(path, content)` | Create or overwrite. `content` is `str` (UTF-8) or `bytes`. |
| `files.read(path)` | Returns text. Base64-encode binary output in the sandbox and decode it on the client. |
| `files.delete`, `files.move`, `files.copy`, `files.stat` | Usual file operations; `stat` returns size, type, and modified time. |
| `files.watch(path, recursive=, ignore_patterns=)` | Async iterator of filesystem events. |
| `directories.list`, `directories.create`, `directories.delete` | Directory operations. |
| `ports.list()` | Open ports in the sandbox. |

## Sandbox states

`starting` → `running` → `terminating` → `terminated`. `create` and `terminate` block until the
sandbox settles. A sandbox that cannot start ends in `failed_to_start` (`status_reason`
`out_of_capacity` or `internal_error`). A crashed sandbox goes to `recovering`, then back to
`running` (`restored`) or to `unrecovered`. Termination reasons include `termination_requested`,
`autoterminated` (TTL), `crashed`, `oom_killed`, `evicted`, `node_lost`, and `cluster_lost`.

## Errors and retries

Every failure raises `HttpError`, which subclasses `RuntimeError` in Python and `Error` in
TypeScript. `status` is the HTTP code, or `0` when the request never reached the server.

```python
from together_sandbox import HttpError

try:
    snapshot = await sdk.snapshots.get_by_alias("my-python@v1")
except HttpError as e:
    if e.status != 404:
        raise
```

The SDKs retry 408, 429, 500, 502, 503, 504, and transport failures, three attempts in total with
exponential backoff. Pass `RetryConfig(max_attempts=, should_retry=, on_retry=)` to change that.

## CLI

Command groups accept singular or plural names (`sandbox`/`sandboxes`). A leading `@` resolves an
argument as a snapshot alias. Resources the CLI creates are tagged `client=together-sandbox-cli`.

```bash
together-sandbox snapshots create --image python:3.12-slim --alias my-python@v1
together-sandbox sandboxes run @my-python@v1 --rm -- python3 -c "print(6 * 7)"

SANDBOX_ID=$(together-sandbox sandboxes create @my-python@v1 --ttl 600 | awk '{print $3}')
together-sandbox sandbox exec run "$SANDBOX_ID" -- python3 -c "print(6 * 7)"
together-sandbox sandboxes terminate "$SANDBOX_ID"

together-sandbox sandboxes list          # running only; --all for every status
```

`sandboxes create` takes `--cpu`, `--memory-bytes`, `--ttl`, `--tag`, and `--snapshot-on-terminate`
(with `--snapshot-alias`, `--snapshot-memory`, `--snapshot-ttl`). `sandboxes terminate` takes
`--ephemeral` or the same snapshot flags. `snapshots create --ci` prints the bare snapshot ID last.

## Migrating from Code Interpreter

The Code Interpreter API is gone: `/tci/execute` and `/tci/sessions` return HTTP 404.

| Code Interpreter | `together-sandbox` |
|---|---|
| `client.code_interpreter.execute(code=..., language="python")` | `sandbox.execs.exec("python3", ["-c", code])` in a sandbox created from a Python snapshot |
| `session_id` reuse | Keep one sandbox running (`connect(sandbox_id)` to reattach). Files persist between execs; Python variables do not. |
| `files=[{"name", "encoding", "content"}]` | `sandbox.files.create(path, content)` before the exec |
| `outputs` of type `stdout`, `stderr`, `error` | `output` (stdout and stderr joined) and `exit_code` |
| `display_data` with `image/png` | Save the figure, base64-encode it, print or write it, and decode on the client |
| `client.code_interpreter.sessions.list()` | `sdk.sandboxes.list(statuses=["running"])` |
| Preinstalled data-science packages | Whatever the snapshot's image installs. Build one from a Dockerfile with the packages you need. |
| Session expiry after 60 minutes | `ttl` at creation, or terminate explicitly |

## Full reference

The package installs `LLMS.md` and a `docs/` folder next to its code (`together_sandbox/` in Python
site-packages). Online:

- [Python SDK](https://github.com/togethercomputer/together-sandbox/blob/main/docs/python-sdk.md)
- [TypeScript SDK](https://github.com/togethercomputer/together-sandbox/blob/main/docs/typescript-sdk.md)
- [CLI](https://github.com/togethercomputer/together-sandbox/blob/main/docs/cli.md)
- [Sandboxes and snapshots concepts](https://github.com/togethercomputer/together-sandbox/blob/main/docs/sandboxes.md)
