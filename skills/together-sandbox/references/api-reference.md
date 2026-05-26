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

# Custom base URL (default: https://api.bartender.codesandbox.stream)
sdk = TogetherSandbox(base_url="https://custom.api.url")
```

## Environment Setup

Sandboxes require DNS and PATH configuration before most workloads. Run this as your first exec:

```python
await sandbox.execs.exec("bash", ["-c",
    'echo "nameserver 1.1.1.1" > /etc/resolv.conf && '
    'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
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

Note: `Snapshot` objects do not carry alias information. Aliases are separate entities. To check if a snapshot has an alias, use `get_by_alias()` for known alias names.

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
        result = await sandbox.execs.exec("bash", ["-c", "python3 -c 'print(42)'"])
        print(result["output"])
    # sandbox connection closed automatically on exit
    # Note: use sdk.sandboxes.shutdown(model.id) for explicit shutdown
```

## Command Execution

### exec (run to completion)

`sandbox.execs.exec()` runs a command, streams output via SSE, waits for the process to exit, and returns the result. This is the primary method for most use cases.

```python
result = await sandbox.execs.exec("bash", ["-c", "echo hello && python3 --version"])
print(f"Exit code: {result['exit_code']}")
print(f"Output: {result['output']}")
```

Returns `{"exit_code": int, "output": str}`. Output is the concatenation of all stdout and stderr chunks.

### exec with options

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
| `user` | str | None | `$USER:$GROUP` (default: 1000:1000) |
| `pty` | bool | None | Allocate PTY |

### Non-blocking exec (create + stream)

For long-running commands where you want incremental output:

```python
exec_item = await sandbox.execs.create("bash", ["-c", "long-command"], autostart=True)

async for chunk in sandbox.execs.stream_output(exec_item.id):
    print(chunk.get("output", ""), end="")
    if chunk.get("exitCode") is not None:  # camelCase in SSE events
        break
```

### Other exec operations

```python
execs_list = await sandbox.execs.list()         # list active execs
exec_info = await sandbox.execs.get(exec_id)    # get exec status
await sandbox.execs.send_stdin(exec_id, "input\n")  # send stdin
await sandbox.execs.resize(exec_id, cols=120, rows=40)  # resize PTY
await sandbox.execs.start(exec_id)              # start a created exec
await sandbox.execs.delete(exec_id)             # kill exec
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
# Via the SDK namespace (recommended for connected sandboxes)
await sdk.sandboxes.shutdown(sandbox.id)

# Via class method (when you only have an ID, no SDK instance)
await Sandbox.shutdown(sandbox_id, api_key="...")
```

### Hibernate (captures filesystem + memory state as new snapshot)

```python
await sdk.sandboxes.hibernate(sandbox.id)

# Via class method
await Sandbox.hibernate(sandbox_id, api_key="...")
```

Ephemeral sandboxes cannot hibernate.

### Close connection (does not stop the sandbox)

```python
await sandbox.close()
```

**Important:** `Sandbox.shutdown()` and `Sandbox.hibernate()` are class methods that take a `sandbox_id` string, not instance methods. To shut down a connected sandbox, use `sdk.sandboxes.shutdown(sandbox.id)`.

## Retry Configuration

```python
from together_sandbox import TogetherSandbox, RetryConfig

sdk = TogetherSandbox(retry=RetryConfig(
    max_attempts=3,
    on_retry=lambda ctx: print(f"Retry {ctx.attempt}: {ctx.error}"),
))
```

## Error Handling

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
| `RuntimeError("exec stream ended without an exit code")` | Sandbox died mid-exec |
| HTTP transport errors | Network failures, timeouts |
