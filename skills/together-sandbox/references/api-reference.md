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

# Custom base URL
sdk = TogetherSandbox(base_url="https://custom.api.url")
```

## Environment Setup

Sandboxes require DNS and PATH configuration before most workloads. Run this as your first exec:

```python
await sandbox.execs.exec("bash", ["-c",
    'echo "nameserver 1.1.1.1" > /etc/resolv.conf && '
    'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
])

await sandbox.execs.exec("bash", ["-c",
    'export PATH="/root/.local/bin:/usr/local/bin:/usr/local/sbin:$PATH"'
])
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
# Returns a connected Sandbox with exec, files, directories, ports
```

`start()` handles: starting the VM, waiting for "running" state, and establishing the Pint connection. The returned `Sandbox` is ready for operations.

### Context manager (recommended)

```python
async with TogetherSandbox() as sdk:
    model = await sdk.sandboxes.create(snapshot_alias="python-base", ephemeral=True)
    async with await sdk.sandboxes.start(model.id) as sandbox:
        result = await sandbox.execs.exec("bash", ["-c", "python3 -c 'print(42)'"])
        print(result["output"])
    # sandbox.shutdown() called automatically
```

## Command Execution

### Simple exec (blocks until complete)

```python
result = await sandbox.execs.exec("bash", ["-c", "echo hello && python3 --version"])
# result["exit_code"]: int
# result["output"]: str
```

### Exec with options

```python
result = await sandbox.execs.exec(
    "python3", ["script.py"],
    cwd="/workspace",
    env={"DEBUG": "1"},
    user="1000:1000",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | str | required | Binary to execute |
| `args` | list[str] | required | Arguments list |
| `cwd` | str | None | Working directory |
| `env` | dict[str, str] | None | Environment variables |
| `user` | str | None | UID:GID (default: 1000:1000) |
| `pty` | bool | None | Allocate PTY |

### Non-blocking exec with streaming

```python
exec_item = await sandbox.execs.create("bash", ["-c", "long-command"], autostart=True)

async for chunk in sandbox.execs.stream_output(exec_item.id):
    print(chunk.get("output", ""), end="")
    if chunk.get("exitCode") is not None:
        break
```

### Poll output (alternative to streaming)

```python
output = await sandbox.execs.get_output(exec_item.id)
# output["exit_code"]: int | None (None if still running)
# output["output"]: str
```

### Other exec operations

```python
execs = await sandbox.execs.list()
exec_info = await sandbox.execs.get(exec_id)
await sandbox.execs.send_stdin(exec_id, "input text\n")
await sandbox.execs.resize(exec_id, cols=120, rows=40)
await sandbox.execs.delete(exec_id)
```

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
info = await sandbox.files.stat("/tmp/script.py")

# Watch for changes
async for event in sandbox.files.watch("/src", recursive=True, ignore_patterns=["__pycache__"]):
    print(event)
```

## Directory Operations

```python
files = await sandbox.directories.list("/tmp")
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
| `should_retry` | callable | None | Custom retry predicate |
| `on_retry` | callable | None | Callback on each retry |

## Error Handling

```python
from together_sandbox import HttpError

try:
    sandbox = await sdk.sandboxes.start("nonexistent")
except HttpError as e:
    print(f"HTTP {e.status}: {e}")
except RuntimeError as e:
    print(f"Runtime error: {e}")
```

| Exception | When |
|-----------|------|
| `HttpError` (status 404) | Sandbox or snapshot not found |
| `HttpError` (status 500) | Infrastructure error (transient, retry) |
| `RuntimeError` | Sandbox has no agent connection details (not yet started) |
