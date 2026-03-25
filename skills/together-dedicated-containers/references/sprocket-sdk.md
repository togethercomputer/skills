# Sprocket SDK Reference
## Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Pattern](#core-pattern)
- [`sprocket.Sprocket` Base Class](#sprocketsprocket-base-class)
- [`sprocket.run(sprocket, name, use_torchrun=False)`](#sprocketrun)
- [`sprocket.FileOutput`](#sprocketfileoutput)
- [`sprocket.emit_info(info: dict)`](#sprocketemitinfo)
- [`sprocket.InputOutputProcessor`](#sprocketinputoutputprocessor)
- [HTTP Endpoints (Sprocket exposes)](#http-endpoints)
- [CLI Arguments](#cli-arguments)
- [Environment Variables](#environment-variables)
- [Multi-GPU Pattern](#multi-gpu-pattern)
- [Graceful Shutdown](#graceful-shutdown)


## Overview
Sprocket is the worker framework for Together Dedicated Containers. It handles job receiving, processing, and result reporting.

## Installation

```shell
pip install sprocket --extra-index-url https://pypi.together.ai/
# or with Together's private PyPI in pyproject.toml:
[[tool.uv.index]]
name = "together-pypi"
url = "https://pypi.together.ai/"
```

## Core Pattern

```python
import sprocket

class MyModel(sprocket.Sprocket):
    def setup(self) -> None:
        """Called once at startup. Load models here."""
        self.model = load_model()

    def predict(self, args: dict) -> dict:
        """Called for each job. Process and return results."""
        result = self.model(args["input"])
        return {"output": result}

    def shutdown(self) -> None:
        """Optional. Called on graceful shutdown."""
        pass

if __name__ == "__main__":
    sprocket.run(MyModel(), "my-deployment")
```

## `sprocket.Sprocket` Base Class

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `setup` | `setup(self) -> None` | Called once at startup. Load models and resources. |
| `predict` | `predict(self, args: dict) -> dict` | Called per job. Return results dict. |
| `shutdown` | `shutdown(self) -> None` | Optional. Cleanup on shutdown. |

### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `processor` | `Type[InputOutputProcessor]` | `InputOutputProcessor` | Custom I/O processor |
| `warmup_inputs` | `list[dict]` | `[]` | Inputs for cache warmup |

## `sprocket.run(sprocket, name, use_torchrun=False)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `sprocket` | Sprocket | Your Sprocket instance |
| `name` | str | Deployment name (used for queue routing) |
| `use_torchrun` | bool | Enable multi-GPU mode. Default: False |

## `sprocket.FileOutput`

Wrap local files for automatic upload:

```python
def predict(self, args):
    video.save("output.mp4")
    return {"video": sprocket.FileOutput("output.mp4"), "duration": 10.5}
```

The file is uploaded after `predict()` returns, and the path is replaced with a public URL in the final result.

## `sprocket.emit_info(info: dict)`

Report progress from inside `predict()`:

```python
def predict(self, args):
    for i in range(100):
        frame = generate_frame(i)
        sprocket.emit_info({"progress": (i + 1) / 100, "status": "generating"})
    return {"video": sprocket.FileOutput("output.mp4")}
```

Constraints:
- Must serialize to under 4,096 bytes JSON
- Updates batched and merged (later values overwrite earlier)
- With `use_torchrun=True`, call only from rank 0

## `sprocket.InputOutputProcessor`

Custom I/O processing:

```python
class CustomProcessor(sprocket.InputOutputProcessor):
    def process_input_file(self, resp, dst):
        """Custom download logic (e.g., decompression)."""
        pass

    async def finalize(self, request_id, inputs, outputs):
        """Post-processing after predict(), before FileOutput upload."""
        return outputs
```

## HTTP Endpoints (Sprocket exposes)

| Endpoint | Method | Response |
|----------|--------|---------|
| `/health` | GET | `{"status": "healthy"}` (200) or `{"status": "unhealthy"}` (503) |
| `/metrics` | GET | Prometheus format: `requests_inflight 0.0` |
| `/generate` | POST | Direct HTTP inference (non-queue mode) |

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--queue` | false | Enable queue worker mode |
| `--port` | 8000 | HTTP server port |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TOGETHER_API_KEY` | Required | API key |
| `TOGETHER_API_BASE_URL` | `https://api.together.ai` | API base URL |
| `TERMINATION_GRACE_PERIOD_SECONDS` | 300 | Shutdown + prediction timeout |
| `WORLD_SIZE` | 1 | GPU processes (set by torchrun) |

## Multi-GPU Pattern

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
            save_output("result.mp4")
            return {"video": sprocket.FileOutput("result.mp4")}
        # Other ranks return None

sprocket.run(MultiGPUModel(), "my-model", use_torchrun=True)
```

Config for multi-GPU:
```toml
[tool.jig.deploy]
gpu_type = "h100-80gb"
gpu_count = 2
```

When `use_torchrun=True` is passed to `sprocket.run()`, Sprocket launches torchrun internally. No need to override `cmd`.

## Graceful Shutdown

1. Container receives SIGTERM
2. Sprocket stops accepting new jobs
3. Current job runs to completion
4. `shutdown()` called
5. Container exits
6. Total time: `termination_grace_period_seconds` (default 300s)
