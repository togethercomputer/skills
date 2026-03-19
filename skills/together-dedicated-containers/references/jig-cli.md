# Jig CLI Reference

## Installation

```shell
pip install together --upgrade
# or
uv tool install together
```

Jig commands are under `together beta jig`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TOGETHER_API_KEY` | Required | Your Together API key |
| `TOGETHER_DEBUG` | `""` | Enable debug logging (`"1"` or `"true"`) |
| `WARMUP_ENV_NAME` | `TORCHINDUCTOR_CACHE_DIR` | Environment variable for cache location |
| `WARMUP_DEST` | `torch_cache` | Cache directory path in container |

All commands are subcommands of `together beta jig`. Use `--config <path>` to specify a custom config file (default: `pyproject.toml`).

## Build Commands

### jig init

Create a starter `pyproject.toml` with sensible defaults.

```shell
together beta jig init
```

### jig dockerfile

Generate a Dockerfile from your `pyproject.toml` configuration. Useful for debugging the build.

```shell
together beta jig dockerfile
```

### jig build

Build the Docker image locally.

```shell
together beta jig build [flags]
```

| Flag | Description |
|------|-------------|
| `--tag <tag>` | Image tag (default: content-hash) |
| `--warmup` | Pre-generate compile caches after build (requires GPU) |

### jig push

Push the built image to Together's registry at `registry.together.xyz`.

```shell
together beta jig push [flags]
```

| Flag | Description |
|------|-------------|
| `--tag <tag>` | Image tag to push |

## Deployment Commands

### jig deploy

Build, push, and create or update the deployment. Combines `build`, `push`, and deployment creation into one step.

```shell
together beta jig deploy [flags]
```

| Flag | Description |
|------|-------------|
| `--tag <tag>` | Image tag |
| `--warmup` | Pre-generate compile caches (requires GPU) |
| `--build-only` | Build and push only, skip deployment creation |
| `--image <ref>` | Deploy an existing image, skip build and push |

### jig status

Show deployment status and configuration.

```shell
together beta jig status
```

### jig list

List all deployments in your organization.

```shell
together beta jig list
```

### jig logs

Retrieve deployment logs.

```shell
together beta jig logs [flags]
```

| Flag | Description |
|------|-------------|
| `--follow` | Stream logs in real-time |

### jig endpoint

Print the deployment's endpoint URL.

```shell
together beta jig endpoint
```

### jig destroy

Delete the deployment.

```shell
together beta jig destroy
```

## Queue Commands

### jig submit

Submit a job to the deployment's queue.

```shell
together beta jig submit [flags]
```

| Flag | Description |
|------|-------------|
| `--prompt <text>` | Shorthand for `--payload '{"prompt": "..."}'` |
| `--payload <json>` | Full JSON payload |
| `--watch` | Wait for the job to complete and print the result |

Example:

```shell
together beta jig submit --payload '{"prompt": "A cat playing piano"}' --watch
```

### jig job_status

Get the status of a submitted job.

```shell
together beta jig job_status --request-id <id>
```

| Flag | Description |
|------|-------------|
| `--request-id <id>` | The job's request ID (required) |

### jig queue_status

Show queue backlog and worker status.

```shell
together beta jig queue_status
```

## Queue API

### Python (v2 SDK)

```python
from together import Together
client = Together()

# Submit
job = client.beta.jig.queue.submit(model="my-deployment", payload={"prompt": "Hello"}, priority=1)

# Poll status
status = client.beta.jig.queue.retrieve(request_id=job.request_id, model="my-deployment")
```

### TypeScript

```typescript
import Together from "together-ai";
const client = new Together();

// Submit
const job = await client.beta.jig.queue.submit({ model: "my-deployment", payload: { prompt: "Hello" }, priority: 1 });

// Poll status
const status = await client.beta.jig.queue.retrieve({ request_id: job.requestId!, model: "my-deployment" });
```

### cURL

Submit a job:

```shell
curl -X POST "https://api.together.ai/v1/queue/submit" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "my-deployment", "payload": {"prompt": "Hello world"}, "priority": 1}'
```

Poll job status:

```shell
curl "https://api.together.ai/v1/queue/status?model=my-deployment&request_id=req_abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

Cancel a job:

```shell
curl -X POST "https://api.together.ai/v1/queue/cancel" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "my-deployment", "request_id": "req_abc123"}'
```

Queue metrics:

```shell
curl "https://api.together.ai/v1/queue/metrics?model=my-deployment" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

Health check:

```shell
curl https://api.together.ai/v1/deployment-request/my-deployment/health \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### Queue Submit Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Deployment name |
| `payload` | object | Yes | Freeform model input (passed to predict()) |
| `priority` | integer | No | Higher values process first (default: 0) |
| `info` | object | No | Arbitrary metadata stored with the job |

### Queue Status Response

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Job identifier |
| `model` | string | Deployment name |
| `status` | string | `pending`, `running`, `done`, `failed`, `canceled` |
| `outputs` | object | Model output (when done) |
| `info` | object | Job metadata (including emit_info updates) |
| `priority` | integer | Job priority |
| `retries` | integer | Retry count (fails after 3) |
| `created_at` | datetime | Submission time |
| `claimed_at` | datetime | Worker claim time |
| `done_at` | datetime | Completion time |

## Secrets Commands

Secrets are encrypted environment variables injected at runtime.

### jig secrets set

```shell
together beta jig secrets set --name <name> --value <value> [flags]
```

| Flag | Description |
|------|-------------|
| `--name <name>` | Secret name (required) |
| `--value <value>` | Secret value (required) |
| `--description <text>` | Human-readable description |

Example:

```shell
together beta jig secrets set --name HF_TOKEN --value hf_xxxxx --description "Hugging Face token"
```

### jig secrets list

List all secrets for the deployment.

```shell
together beta jig secrets list
```

### jig secrets unset

Remove a secret.

```shell
together beta jig secrets unset <name>
```

## Volumes Commands

Volumes mount read-only data (such as model weights) into your container without baking them into the image.

### jig volumes create

Create a volume and upload files.

```shell
together beta jig volumes create --name <name> --source <path>
```

| Flag | Description |
|------|-------------|
| `--name <name>` | Volume name (required) |
| `--source <path>` | Local directory to upload (required) |

Example:

```shell
together beta jig volumes create --name my-weights --source ./model_weights/
```

### jig volumes update

Update a volume with new files.

```shell
together beta jig volumes update --name <name> --source <path>
```

### jig volumes describe

Show volume details and contents.

```shell
together beta jig volumes describe --name <name>
```

### jig volumes list

List all volumes.

```shell
together beta jig volumes list
```

### jig volumes delete

Delete a volume.

```shell
together beta jig volumes delete --name <name>
```

Mount a volume by adding to your `pyproject.toml`:

```toml
[[tool.jig.volume_mounts]]
name = "my-weights"
mount_path = "/models"
```

## Configuration (pyproject.toml)

Jig reads configuration from your `pyproject.toml` file or a standalone `jig.toml` file. You can also specify a custom config file explicitly:

```shell
together beta jig --config staging_jig.toml deploy
```

This is useful for managing multiple environments (e.g., `staging_jig.toml`, `production_jig.toml`).

### `[tool.jig.image]` -- Build Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `python_version` | string | `"3.11"` | Python version for the container base image |
| `system_packages` | string[] | `[]` | APT packages to install (e.g., `ffmpeg`, `git`, `libgl1`) |
| `environment` | object | `{}` | Build-time + runtime env vars (set as `ENV` directives) |
| `run` | string[] | `[]` | Extra shell commands during build (each becomes a `RUN` instruction) |
| `cmd` | string | `"python app.py"` | Container startup command (Docker `CMD`). Include `--queue` for Sprocket |
| `copy` | string[] | `[]` | Files and directories to include in container |
| `auto_include_git` | bool | `false` | Auto-include git-tracked files (requires clean repo) |

### `[tool.jig.deploy]` -- Runtime Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `description` | string | `""` | Human-readable description |
| `gpu_type` | string | `"h100-80gb"` | `"h100-80gb"` or `"none"` (CPU-only) |
| `gpu_count` | int | `1` | GPUs per replica |
| `cpu` | float | `1.0` | CPU cores per replica (supports fractional, e.g. `0.1`) |
| `memory` | float | `8.0` | Memory in GB (supports fractional, e.g. `0.5`) |
| `storage` | int | `100` | Ephemeral disk in GB |
| `min_replicas` | int | `1` | Min replicas (0 for scale-to-zero) |
| `max_replicas` | int | `1` | Max replicas |
| `port` | int | `8000` | Container listen port |
| `health_check_path` | string | `"/health"` | Health endpoint (must return 200 when ready) |
| `termination_grace_period_seconds` | int | `300` | Shutdown timeout for in-flight jobs |
| `command` | string[] | `null` | Override startup command at deploy time (e.g., `["python", "app.py", "--queue"]`) |

### `[tool.jig.deploy.environment_variables]`

Runtime environment variables injected into your container. For sensitive values, use secrets instead.

```toml
[tool.jig.deploy.environment_variables]
MODEL_PATH = "/models/weights"
TORCH_COMPILE = "1"
LOG_LEVEL = "INFO"
```

### `[tool.jig.autoscaling]`

```toml
[tool.jig.autoscaling]
profile = "QueueBacklogPerWorker"
targetValue = "1.05"
```

The `QueueBacklogPerWorker` profile scales based on queue depth relative to worker count.

Formula: `desired_replicas = queue_depth / targetValue`

| targetValue | Behavior | Example (100 jobs) |
|-------------|----------|-------------------|
| `"1.0"` | Exact match | 100 workers |
| `"1.05"` | 5% underprovisioning (recommended) | 95 workers |
| `"0.9"` | 10% overprovisioning (lower latency) | 111 workers |

### `[[tool.jig.volume_mounts]]`

```toml
[[tool.jig.volume_mounts]]
name = "my-weights"
mount_path = "/models"
```

## Full Example

```toml
[project]
name = "video-generator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["torch>=2.0", "diffusers", "sprocket"]

[tool.jig.image]
python_version = "3.11"
system_packages = ["git", "ffmpeg", "libgl1"]
environment = { TORCH_CUDA_ARCH_LIST = "8.0 9.0" }
run = ["pip install flash-attn --no-build-isolation"]
cmd = "python app.py --queue"
copy = ["app.py", "models/"]

[tool.jig.deploy]
description = "Video generation model"
gpu_type = "h100-80gb"
gpu_count = 2
cpu = 8
memory = 64
min_replicas = 1
max_replicas = 20
port = 8000
health_check_path = "/health"

[tool.jig.deploy.environment_variables]
MODEL_PATH = "/models/weights"
TORCH_COMPILE = "1"

[[tool.jig.volume_mounts]]
name = "my-weights"
mount_path = "/models"

[tool.jig.autoscaling]
profile = "QueueBacklogPerWorker"
targetValue = "1.05"
```

## Container Registry

- **Host:** `registry.together.xyz`
- Private to your organization
- Images referenced by digest for reproducibility
- Authentication handled automatically by Jig CLI

## Debug Mode

```shell
export TOGETHER_DEBUG=1
together beta jig deploy
```
