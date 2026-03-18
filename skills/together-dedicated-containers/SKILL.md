---
name: together-dedicated-containers
description: Deploy custom Dockerized inference workloads on Together AI's managed GPU infrastructure using Dedicated Container Inference (DCI). Tools include Jig CLI for building/deploying, Sprocket SDK for request handling, Queue API for async job submission, and a private container registry. Use when users need custom model serving, containerized inference, Docker-based GPU workloads, image/video generation pipelines, or workloads beyond standard model endpoints.
---

# Together Dedicated Containers

## Overview

Run custom Dockerized inference workloads on Together's managed GPU infrastructure. You bring the container -- Together handles compute, autoscaling, networking, and observability.

**Components:**
- **Jig CLI**: Build, push, and deploy containers (`together beta jig`)
- **Sprocket SDK**: Python SDK for handling inference requests inside containers
- **Queue API**: Async job submission with priority and progress tracking
- **Container Registry**: `registry.together.xyz` for storing images

## Installation

```shell
# Python (recommended)
uv init  # optional, if starting a new project
uv add together

uv pip install together
```

```shell
# or with pip
pip install together
```

```shell
# TypeScript / JavaScript
npm install together-ai
```

Set your API key:

```shell
export TOGETHER_API_KEY=<your-api-key>
```

## Workflow

1. Write inference code using Sprocket SDK (`setup()` + `predict()`)
2. Configure `pyproject.toml` with build and deploy settings
3. Deploy with `together beta jig deploy` (builds, pushes, and deploys)
4. Submit jobs via the Queue API
5. Poll for results

## Quick Start

### 1. Create Inference Worker

```python
# app.py
import os
import sprocket

class HelloWorld(sprocket.Sprocket):
    def setup(self) -> None:
        self.greeting = "Hello"

    def predict(self, args: dict) -> dict:
        name = args.get("name", "world")
        return {"message": f"{self.greeting}, {name}!"}

if __name__ == "__main__":
    queue_name = os.environ.get("TOGETHER_DEPLOYMENT_NAME", "hello-world")
    sprocket.run(HelloWorld(), queue_name)
```

### 2. Configure Project

```toml
# pyproject.toml
[project]
name = "hello-world"
version = "0.1.0"
dependencies = ["sprocket"]

[[tool.uv.index]]
name = "together-pypi"
url = "https://pypi.together.ai/"

[tool.uv.sources]
sprocket = { index = "together-pypi" }

[tool.jig.image]
python_version = "3.11"
cmd = "python3 app.py --queue"
copy = ["app.py"]

[tool.jig.deploy]
gpu_type = "none"
gpu_count = 0
cpu = 1
memory = 2
storage = 10
port = 8000
min_replicas = 1
max_replicas = 1
```

### 3. Deploy

```shell
together beta jig deploy       # Build, push, and deploy
together beta jig status       # Check deployment status
together beta jig logs --follow  # Stream logs
```

### 4. Submit Jobs

**Python (v2 SDK):**

```python
from together import Together
import time

client = Together()
deployment = "hello-world"

# Submit a job
job = client.beta.queue.submit(
    model=deployment,
    payload={"name": "Together"},
    priority=1,
)
print(f"Job submitted: {job.request_id}")

# Poll for result
while True:
    status = client.beta.queue.retrieve(
        request_id=job.request_id,
        model=deployment,
    )
    if status.status == "done":
        print(f"Result: {status.outputs}")
        break
    elif status.status == "failed":
        print(f"Failed: {status.error}")
        break
    time.sleep(2)
```

**TypeScript:**

```typescript
import Together from "together-ai";

const client = new Together();
const deployment = "hello-world";

// Submit a job
const job = await client.beta.queue.submit({
  model: deployment,
  payload: { name: "Together" },
  priority: 1,
});
console.log(`Job submitted: ${job.requestId}`);

// Poll for result
while (true) {
  const status = await client.beta.queue.retrieve({
    requestId: job.requestId!,
    model: deployment,
  });
  if (status.status === "done") {
    console.log("Result:", status.outputs);
    break;
  } else if (status.status === "failed") {
    console.log("Failed:", status.error);
    break;
  }
  await new Promise((r) => setTimeout(r, 2000));
}
```

**cURL:**

```shell
# Submit job
curl -X POST "https://api.together.ai/v1/queue/submit" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "hello-world", "payload": {"name": "Together"}, "priority": 1}'

# Poll status (use request_id from submit response)
curl "https://api.together.ai/v1/queue/status?model=hello-world&request_id=req_abc123" \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

**CLI:**

```shell
together beta jig submit --payload '{"name": "Together"}' --watch
```

### 5. Health Check

```shell
curl https://api.together.ai/v1/deployment-request/hello-world/health \
  -H "Authorization: Bearer $TOGETHER_API_KEY"
```

### 6. Cleanup

```shell
together beta jig destroy
```

## Sprocket SDK

The SDK provides the `sprocket.Sprocket` base class:

- `setup()`: Called once at startup -- load models, warm up caches
- `predict(args: dict) -> dict`: Called per request -- process input and return output
- `shutdown()`: Optional cleanup on graceful shutdown

### File Upload (FileOutput)

Wrap local file paths for automatic upload to Together storage:

```python
def predict(self, args):
    # ... generate video ...
    return {"video": sprocket.FileOutput("output.mp4"), "duration": 10.5}
```

The file is uploaded after `predict()` returns, and the path is replaced with a public URL.

### Progress Tracking (emit_info)

Report progress from inside `predict()`:

```python
def predict(self, args):
    for i in range(100):
        frame = generate_frame(i)
        sprocket.emit_info({"progress": (i + 1) / 100, "status": "generating"})
    return {"video": sprocket.FileOutput("output.mp4")}
```

Clients poll progress via the queue status endpoint's `info` field.

### Multi-GPU (torchrun)

For multi-GPU workloads, pass `use_torchrun=True`:

```python
class MultiGPUModel(sprocket.Sprocket):
    def setup(self):
        import torch.distributed as dist
        dist.init_process_group()
        torch.cuda.set_device(dist.get_rank())
        self.model = load_model().to("cuda")

    def predict(self, args):
        output = self.model(args["input"])
        if dist.get_rank() == 0:
            return {"video": sprocket.FileOutput("result.mp4")}
        # Non-rank-0 processes return None

sprocket.run(MultiGPUModel(), "my-model", use_torchrun=True)
```

Configure multi-GPU in `pyproject.toml`:

```toml
[tool.jig.deploy]
gpu_type = "h100-80gb"
gpu_count = 2
```

## Queue API

For async workloads, use the Queue API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/queue/submit` | POST | Submit a job with payload and priority |
| `/v1/queue/status` | GET | Poll job status and retrieve outputs |
| `/v1/queue/cancel` | POST | Cancel a pending job |
| `/v1/queue/metrics` | GET | Queue backlog and worker metrics |

**Job status flow:** `pending` -> `running` -> `done` / `failed` / `canceled`

**Priority:** Higher integer values are processed first. FIFO within the same priority.

## Key Jig CLI Commands

All commands are subcommands of `together beta jig`. Use `--config <path>` to specify a custom config file (default: `pyproject.toml`).

### Build and Deploy

| Command | Description |
|---------|-------------|
| `together beta jig init` | Create a starter `pyproject.toml` with defaults |
| `together beta jig build` | Build container image locally |
| `together beta jig build --warmup` | Build and pre-generate compile caches (requires GPU) |
| `together beta jig push` | Push image to `registry.together.xyz` |
| `together beta jig deploy` | Build, push, and create/update deployment |
| `together beta jig deploy --image <ref>` | Deploy an existing image, skip build and push |

### Deployment Management

| Command | Description |
|---------|-------------|
| `together beta jig status` | Show deployment status and configuration |
| `together beta jig list` | List all deployments in your organization |
| `together beta jig logs --follow` | Stream logs in real-time |
| `together beta jig endpoint` | Print the deployment's endpoint URL |
| `together beta jig destroy` | Delete the deployment |

### Queue

| Command | Description |
|---------|-------------|
| `together beta jig submit --payload '<json>'` | Submit a job to the queue |
| `together beta jig submit --prompt '<text>' --watch` | Submit and wait for the result |
| `together beta jig job-status --request-id <id>` | Get the status of a submitted job |
| `together beta jig queue-status` | Show queue backlog and worker status |

### Secrets

| Command | Description |
|---------|-------------|
| `together beta jig secrets set --name <n> --value <v>` | Create or update a secret |
| `together beta jig secrets list` | List all secrets for the deployment |
| `together beta jig secrets unset <name>` | Remove a secret |

### Volumes

| Command | Description |
|---------|-------------|
| `together beta jig volumes create --name <n> --source <path>` | Create a volume and upload files |
| `together beta jig volumes update --name <n> --source <path>` | Update a volume with new files |
| `together beta jig volumes list` | List all volumes |
| `together beta jig volumes delete --name <n>` | Delete a volume |

## Configuration (pyproject.toml)

### `[tool.jig.image]` -- Build Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `python_version` | string | `"3.11"` | Python version |
| `system_packages` | string[] | `[]` | APT packages (e.g., `ffmpeg`, `git`, `libgl1`) |
| `environment` | object | `{}` | Build-time + runtime env vars |
| `run` | string[] | `[]` | Extra shell commands during build |
| `cmd` | string | `"python app.py"` | Startup command. Include `--queue` for Sprocket |
| `copy` | string[] | `[]` | Files/directories to include |
| `auto_include_git` | bool | `false` | Auto-include git-tracked files |

### `[tool.jig.deploy]` -- Runtime Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `gpu_type` | string | `"h100-80gb"` | `"h100-80gb"` or `"none"` (CPU-only) |
| `gpu_count` | int | `1` | GPUs per replica |
| `cpu` | float | `1.0` | CPU cores per replica |
| `memory` | float | `8.0` | Memory in GB |
| `storage` | int | `100` | Ephemeral disk in GB |
| `min_replicas` | int | `1` | Min replicas (0 for scale-to-zero) |
| `max_replicas` | int | `1` | Max replicas |
| `port` | int | `8000` | Container listen port |
| `health_check_path` | string | `"/health"` | Health endpoint |
| `termination_grace_period_seconds` | int | `300` | Shutdown timeout |

### `[tool.jig.autoscaling]`

```toml
[tool.jig.autoscaling]
profile = "QueueBacklogPerWorker"
targetValue = "1.05"
```

Formula: `desired_replicas = queue_depth / targetValue`

### `[[tool.jig.volume_mounts]]`

```toml
[[tool.jig.volume_mounts]]
name = "my-weights"
mount_path = "/models"
```

## Full Example (pyproject.toml)

```toml
[project]
name = "video-generator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["torch>=2.0", "diffusers", "sprocket"]

[[tool.uv.index]]
name = "together-pypi"
url = "https://pypi.together.ai/"

[tool.uv.sources]
sprocket = { index = "together-pypi" }

[tool.jig.image]
python_version = "3.11"
system_packages = ["git", "ffmpeg", "libgl1"]
cmd = "python app.py --queue"
copy = ["app.py"]

[tool.jig.deploy]
gpu_type = "h100-80gb"
gpu_count = 2
cpu = 8
memory = 64
min_replicas = 1
max_replicas = 20
port = 8000

[tool.jig.deploy.environment_variables]
MODEL_PATH = "/models/weights"

[[tool.jig.volume_mounts]]
name = "my-weights"
mount_path = "/models"

[tool.jig.autoscaling]
profile = "QueueBacklogPerWorker"
targetValue = "1.05"
```

## Resources

- **Full Jig CLI reference**: See [references/jig-cli.md](references/jig-cli.md)
- **Sprocket SDK reference**: See [references/sprocket-sdk.md](references/sprocket-sdk.md)
- **Worker template**: See [scripts/sprocket_hello_world.py](scripts/sprocket_hello_world.py) -- minimal Sprocket worker
- **Queue client (Python)**: See [scripts/queue_client.py](scripts/queue_client.py) -- submit, poll, and retrieve results (v2 SDK)
- **Queue client (TypeScript)**: See [scripts/queue_client.ts](scripts/queue_client.ts) -- submit, poll, and retrieve results (TypeScript SDK)
- **Official docs**: [Dedicated Container Inference](https://docs.together.ai/docs/dedicated-container-inference)
- **Official docs**: [Containers Quickstart](https://docs.together.ai/docs/containers-quickstart)
- **Example**: [Image Generation (Flux2)](https://docs.together.ai/docs/dedicated_containers_image)
- **Example**: [Video Generation (Wan 2.1)](https://docs.together.ai/docs/dedicated_containers_video)
- **API reference**: [Deployments API](https://docs.together.ai/reference/deployments-create)
