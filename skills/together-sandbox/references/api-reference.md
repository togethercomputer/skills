# Together Sandbox SDK Reference

## Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Environment Setup](#environment-setup)
- [Snapshots](#snapshots)
- [Sandboxes](#sandboxes)
- [Command Execution](#command-execution)
- [File Operations](#file-operations)
- [Directory Operations](#directory-operations)
- [Lifecycle Management](#lifecycle-management)
- [Retry Configuration](#retry-configuration)
- [Error Handling](#error-handling)
- [Helper: run_exec](#helper-run_exec)

## Installation

```bash
pip install "together-sandbox @ git+https://github.com/togethercomputer/together-sandbox.git#subdirectory=together-sandbox-python"
```

Requires Python 3.10+. The SDK is async-native.

## Authentication

The SDK reads `TOGETHER_API_KEY` from the environment. It handles the two-auth system (management API for sandbox lifecycle, in-sandbox Pint API for exec and files) automatically.

```python
from together_sandbox import TogetherSandbox

# From environment variable (recommended)
sdk = TogetherSandbox()

# Explicit key
sdk = TogetherSandbox(api_key="your-key")

# Custom base URL (default: https://api.bartender.codesandbox.stream)
sdk = TogetherSandbox(base_url="https://custom.api.url")
```

## Environment Setup

Sandboxes require DNS and PATH configuration before most workloads. Run this as your first exec:

```python
exec_item = await sandbox.execs.create("bash", ["-c",
    'echo "nameserver 1.1.1.1" > /etc/resolv.conf && '
    'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
], autorun=True)
# Wait for completion (see Helper: run_exec below)
```

| Issue | Cause | Fix |
|-------|-------|-----|
| "Could not resolve host" | No DNS configured | Write nameservers to `/etc/resolv.conf` |
| "command not found" for pip tools | `/root/.local/bin` not on PATH | Export PATH with that directory |
| "cannot be used with root privileges" | Tool detects uid=0 | `export IS_SANDBOX=1` |

## Snapshots

Snapshots are immutable environment images. Create them from Docker images or Dockerfiles.

### Create from Docker image

```python
from together_sandbox import CreateImageSnapshotParams

result = await sdk.snapshots.create(CreateImageSnapshotParams(
    image="python:3.11-slim",
    alias="python-base",
))
# result.snapshot_id: str
# result.alias: str | None
```

### Create from Dockerfile (remote build)

```python
from together_sandbox import CreateContextSnapshotParams

result = await sdk.snapshots.create(CreateContextSnapshotParams(
    context="./my-app",
    dockerfile="./my-app/Dockerfile",
    alias="my-app@v1",
    on_progress=lambda p: print(f"{p.step}: {p.output}"),
    memory_snapshot=True,  # capture RAM state for instant resume
))
```

Progress steps: `prepare`, `build`, `auth`, `push`, `register`, `alias`.

### Alias, lookup, list, delete

```python
await sdk.snapshots.alias(snapshot_id, "rl-env-v2")

snapshot = await sdk.snapshots.get_by_alias("rl-env-v2")
snapshot = await sdk.snapshots.get_by_id("550e8400-...")

all_snapshots = await sdk.snapshots.list()

await sdk.snapshots.delete_by_id("550e8400-...")
await sdk.snapshots.delete_by_alias("old-env")
```

### Snapshot model fields

The `Snapshot` object returned by `get_by_id()`, `get_by_alias()`, and `list()`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Snapshot identifier |
| `project_id` | str | Project/namespace |
| `byte_size` | int | Size in bytes |
| `protected` | bool | Whether deletion is blocked |
| `optimized` | bool | Whether Nydus-optimized |
| `includes_memory_snapshot` | bool | Whether RAM state is captured |
| `created_at` | datetime | Creation timestamp |
| `optimized_at` | datetime or None | Optimization timestamp |
| `updated_at` | datetime | Last update timestamp |

Note: Snapshots do not carry alias information. Aliases are separate entities. To find which snapshots have aliases, use `get_by_alias()` for known alias names.

## Sandboxes

### Create

```python
sandbox_model = await sdk.sandboxes.create(
    snapshot_alias="python-base",     # or snapshot_id="uuid"
    millicpu=2000,                    # 2 vCPU (default: 1000)
    memory_bytes=4 * 1024**3,         # 4 GB (default: 2 GB)
    disk_bytes=10 * 1024**3,          # 10 GB (default: 10 GB)
    ephemeral=True,                   # auto-delete on stop, cannot hibernate
)
# sandbox_model.id: str
# sandbox_model.status: str ("created")
```

All parameters are keyword-only.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `snapshot_id` | str | None | Snapshot UUID (provide this or `snapshot_alias`) |
| `snapshot_alias` | str | None | Snapshot alias (provide this or `snapshot_id`) |
| `millicpu` | int | 1000 | CPU in millicores (min 250, multiple of 250) |
| `memory_bytes` | int | 2147483648 | Memory in bytes (2 GB) |
| `disk_bytes` | int | 10737418240 | Disk in bytes (10 GB) |
| `ephemeral` | bool | None | Auto-delete on stop, cannot hibernate |
| `id` | str | None | Custom sandbox ID (auto-generated if omitted) |

### Start

```python
sandbox = await sdk.sandboxes.start(sandbox_model.id)
# Returns a connected Sandbox with execs, files, directories, ports
```

`start()` handles: starting the VM, waiting for "running" state, and establishing the Pint connection. The returned `Sandbox` is ready for operations.

Optional parameter: `version_number: int` to start from a previous version.

### Context manager (recommended)

```python
async with TogetherSandbox() as sdk:
    model = await sdk.sandboxes.create(snapshot_alias="python-base", ephemeral=True)
    async with await sdk.sandboxes.start(model.id) as sandbox:
        exec_item = await sandbox.execs.create("bash", ["-c", "python3 -c 'print(42)'"], autorun=True)
        outputs = await sandbox.execs.get_output(exec_item.id)
        for o in outputs:
            print(o.output)
    # sandbox.shutdown() called automatically on exit
```

## Command Execution

Command execution is a two-step process: create the exec, then poll or stream for output. There is no single-call convenience method.

### Step 1: Create an exec

```python
exec_item = await sandbox.execs.create(
    "bash", ["-c", "echo hello && python3 --version"],
    autorun=True,  # start immediately (default behavior)
)
# exec_item.id: str
# exec_item.status: str ("running")
# exec_item.pid: int
# exec_item.exit_code: int (may be 0 initially; check status for completion)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | str | required | Binary to execute |
| `args` | list[str] | required | Arguments list |
| `autorun` | bool | None | Start immediately (defaults to True) |
| `interactive` | bool | None | Interactive mode |
| `pty` | bool | None | Allocate PTY |
| `cwd` | str | None | Working directory |
| `env` | dict[str, str] | None | Environment variables |
| `uid` | int | None | User ID for the process |
| `gid` | int | None | Group ID for the process |

### Step 2a: Poll for output

```python
outputs = await sandbox.execs.get_output(exec_item.id)
# Returns list[ExecStdout]
# Each item has: .type_ ("stdout"/"stderr"), .output (str), .exit_code (int | Unset)
```

`get_output()` is a one-shot call that returns immediately with whatever output has been buffered. If the command hasn't finished, `exit_code` will be `Unset` on all items. Poll until an item has a non-Unset `exit_code`:

```python
import asyncio

outputs = []
while True:
    outputs = await sandbox.execs.get_output(exec_item.id)
    if any(hasattr(o, 'exit_code') and isinstance(o.exit_code, int) for o in outputs):
        break
    await asyncio.sleep(0.5)

full_output = "".join(o.output for o in outputs)
exit_code = next(o.exit_code for o in outputs if isinstance(o.exit_code, int))
```

### Step 2b: Stream output (alternative)

```python
output_text = ""
exit_code = None
async for chunk in sandbox.execs.stream_output(exec_item.id):
    output_text += chunk.get("output", "")
    if chunk.get("exitCode") is not None:  # camelCase in SSE events
        exit_code = chunk["exitCode"]
        break
```

Note: SSE stream events use camelCase keys (`exitCode`, not `exit_code`).

### Other exec operations

```python
execs_list = await sandbox.execs.list()         # list active execs
exec_info = await sandbox.execs.get(exec_id)    # get exec status
await sandbox.execs.send_stdin(exec_id, "input\n")  # send stdin
await sandbox.execs.resize(exec_id, cols=120, rows=40)  # resize PTY
await sandbox.execs.delete(exec_id)             # kill exec
```

### ExecItem fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Exec identifier |
| `command` | str | Command being executed |
| `args` | list[str] | Arguments |
| `status` | str | "running", "stopped", or "finished" |
| `pid` | int | Process ID |
| `interactive` | bool | Whether interactive |
| `pty` | bool | Whether using PTY |
| `exit_code` | int | Exit code (meaningful when status is "finished") |
| `uid` | int or Unset | User ID |
| `gid` | int or Unset | Group ID |

### ExecStdout fields

| Field | Type | Description |
|-------|------|-------------|
| `type_` | ExecStdoutType | "stdout" or "stderr" |
| `output` | str | Output text |
| `sequence` | int | Sequence number |
| `timestamp` | datetime or Unset | Timestamp |
| `exit_code` | int or Unset | Present when process exits |

## File Operations

```python
# Write (string or bytes)
await sandbox.files.create("/tmp/script.py", "print('hello')")
await sandbox.files.create("/tmp/data.bin", b"\x00\x01\x02")

# Read
content = await sandbox.files.read("/tmp/script.py")  # returns str

# Copy and move
await sandbox.files.copy("/tmp/a.py", "/tmp/b.py")
await sandbox.files.move("/tmp/old.py", "/tmp/new.py")

# Delete
await sandbox.files.delete("/tmp/temp.txt")

# File metadata
info = await sandbox.files.stat("/tmp/script.py")  # returns FileInfo

# Watch for changes
async for event in sandbox.files.watch("/src", recursive=True, ignore_patterns=["__pycache__"]):
    print(event)
```

## Directory Operations

```python
files = await sandbox.directories.list("/tmp")  # returns list[FileInfo]
await sandbox.directories.create("/workspace/output")
await sandbox.directories.delete("/old-dir")
```

## Lifecycle Management

### Shutdown (no state preserved)

```python
await sandbox.shutdown()

# Or by ID without a connected sandbox
await sdk.sandboxes.shutdown(sandbox_id)
```

### Hibernate (captures filesystem + memory state as new snapshot)

```python
await sandbox.hibernate()

# Or by ID
await sdk.sandboxes.hibernate(sandbox_id)
```

Ephemeral sandboxes cannot hibernate.

## Retry Configuration

```python
from together_sandbox import TogetherSandbox, RetryConfig

sdk = TogetherSandbox(retry=RetryConfig(
    max_attempts=3,
    on_retry=lambda ctx: print(f"Retry {ctx.attempt}: {ctx.error}"),
))
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | int | 3 | Maximum retry attempts |
| `should_retry` | callable | None | Custom retry predicate (sync or async) |
| `on_retry` | callable | None | Callback on each retry (sync or async) |

`RetryContext` fields: `operation` (str), `attempt` (int), `error` (Exception), `status` (int or None), `delay` (float).

## Error Handling

The SDK raises `RuntimeError` for connection and state issues. The underlying HTTP client raises exceptions for transport failures.

```python
try:
    sandbox = await sdk.sandboxes.start("nonexistent")
except RuntimeError as e:
    print(f"SDK error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

| Exception | When |
|-----------|------|
| `RuntimeError("Sandbox has no agent connection details")` | Sandbox not yet started |
| `RuntimeError("Sandbox has no ID")` | Invalid sandbox state |
| HTTP transport errors | Network failures, timeouts |

## Helper: run_exec

The SDK requires two steps for command execution (create + poll). This helper wraps both into a single call. Use it in your scripts to simplify the code:

```python
import asyncio

async def run_exec(
    sandbox,
    command: str,
    args: list[str] | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    poll_interval: float = 0.5,
) -> tuple[int, str]:
    """Execute a command and wait for completion. Returns (exit_code, output)."""
    if args is None:
        args = ["-c", command]
        command = "bash"

    exec_item = await sandbox.execs.create(
        command, args, autorun=True, cwd=cwd, env=env,
    )

    while True:
        exec_info = await sandbox.execs.get(exec_item.id)
        if exec_info.status == "finished":
            break
        await asyncio.sleep(poll_interval)

    outputs = await sandbox.execs.get_output(exec_item.id)
    full_output = "".join(o.output for o in outputs)
    return exec_info.exit_code, full_output
```

Usage:

```python
exit_code, output = await run_exec(sandbox, "echo hello && python3 --version")
print(f"Exit code: {exit_code}")
print(f"Output: {output}")
```
