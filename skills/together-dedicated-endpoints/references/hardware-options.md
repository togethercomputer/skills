# Dedicated Endpoints Hardware Reference
## Contents

- [Hardware ID Format](#hardware-id-format)
- [GPU Types](#gpu-types)
- [Common Configurations](#common-configurations)
- [Hardware Availability Status](#hardware-availability-status)
- [Hardware Response Object](#hardware-response-object)
- [Pricing Model](#pricing-model)
- [GPU Selection Guide](#gpu-selection-guide)
- [Scaling](#scaling)
- [Autoscaling Schema](#autoscaling-schema)


## Hardware ID Format

`[count]x_nvidia_[gpu_type]_[memory]_[link]`

Example: `2x_nvidia_h100_80gb_sxm`

## GPU Types

Currently offered hardware families:

| GPU | Memory | Notes |
|-----|--------|-------|
| H100 SXM | 80GB | Production workhorse, broad model coverage |
| H200 SXM | 140GB | Larger HBM than H100 for memory-bound workloads |
| B200 SXM | 180GB | Highest performance, largest single-GPU memory |

A100, L40, L40S, and RTX 6000 are no longer offered for new dedicated endpoints. The `/v1/hardware`
endpoint may still return deprecated SKUs; treat only H100, H200, and B200 as deployable.

Hardware availability varies by region and demand. Use the API or CLI to get current options:

```python
from together import Together
client = Together()

response = client.endpoints.list_hardware(model="Qwen/Qwen3.5-9B-FP8")
for hw in response.data:
    status = hw.availability.status if hw.availability else "unknown"
    price = hw.pricing.cents_per_minute if hw.pricing else "N/A"
    print(f"  {hw.id}  ({status}, {price}c/min)")
```

```shell
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8 --available
```

## Common Configurations

| Hardware ID | GPU | Count | Typical Use |
|------------|-----|-------|-------------|
| `1x_nvidia_h100_80gb_sxm` | H100 | 1 | Small models (up to ~9B) |
| `2x_nvidia_h100_80gb_sxm` | H100 | 2 | Medium models (7-20B) |
| `4x_nvidia_h100_80gb_sxm` | H100 | 4 | Large models (70B) |
| `8x_nvidia_h100_80gb_sxm` | H100 | 8 | Very large models (120B+, MoE) |
| `1x_nvidia_h200_140gb_sxm` | H200 | 1 | Memory-bound small/medium models |
| `4x_nvidia_h200_140gb_sxm` | H200 | 4 | Large models with bigger KV cache |
| `8x_nvidia_h200_140gb_sxm` | H200 | 8 | Very large or long-context models |
| `1x_nvidia_b200_180gb_sxm` | B200 | 1 | Highest single-GPU performance |
| `8x_nvidia_b200_180gb_sxm` | B200 | 8 | Maximum throughput / largest models |

## Hardware Availability Status

| Status | Meaning |
|--------|---------|
| `available` | Ready for deployment |
| `unavailable` | Currently not available |
| `insufficient` | Some capacity but may be limited |

## Hardware Response Object

```json
{
  "object": "hardware",
  "id": "1x_nvidia_h100_80gb_sxm",
  "pricing": { "cents_per_minute": 10.82 },
  "specs": {
    "gpu_type": "h100",
    "gpu_link": "sxm",
    "gpu_memory": 80,
    "gpu_count": 1
  },
  "availability": { "status": "available" },
  "updated_at": "2025-01-15T14:30:00Z"
}
```

## Pricing Model

- **Billed per minute** while endpoint is running (even when idle)
- **No charge** during spin-up or for failed deployments
- **Stop endpoint** to pause charges
- Price varies by hardware configuration (check `cents_per_minute`)

### Single-GPU on-demand rates

Reference prices for the currently-offered single-GPU SKUs (multiply by GPU count for multi-GPU
configurations of the same family; for the authoritative live rates always call the API or CLI):

| Hardware ID | Cost/hour |
|-------------|-----------|
| `1x_nvidia_h100_80gb_sxm` | $5.40 |
| `1x_nvidia_h200_140gb_sxm` | $6.60 |
| `1x_nvidia_b200_180gb_sxm` | $9.00 |

Multi-GPU hardware IDs share the single-GPU suffix, e.g. four H100s use `4x_nvidia_h100_80gb_sxm`.
Cost scales linearly with the GPU count.

Each running replica bills independently and stops billing as soon as it is scaled down. Run
`together endpoints hardware --model <MODEL_ID>` (or `tg endpoints hardware --model <MODEL_ID>`)
for the per-model list with current per-minute rates.

## GPU Selection Guide

| Need | Recommendation |
|------|---------------|
| Small models (up to 9B) | 1x H100 |
| Medium models (7-20B) | 1-2x H100 |
| Large models (70B) | 4-8x H100 or 4x H200 |
| Very large / MoE models (120B+) | 8x H100, 8x H200, or 8x B200 |
| Maximum throughput | 8x B200 + multiple replicas |
| Cost-effective baseline | H100 (lowest per-hour rate of currently-offered SKUs) |
| Long-context / memory-bound | H200 or B200 (larger HBM) |
| Maximum performance | B200 (newest generation, highest single-GPU speed) |

Fine-tuned and custom-uploaded models may require larger hardware than their base parameter count
suggests. For example, a fine-tuned 8B model may only be eligible for 4x or 8x H100 configs.
Always call `list_hardware(model=...)` to get the authoritative list of eligible hardware before
creating an endpoint:

```python
response = client.endpoints.list_hardware(model="your-username/your-finetuned-model")
for hw in response.data:
    status = hw.availability.status if hw.availability else "unknown"
    print(f"  {hw.id}  ({status})")
```

## Scaling

### Horizontal (Replicas)

- Increases maximum QPS
- Linear cost scaling
- Best for high-concurrency workloads

### Vertical (GPU Count)

- Increases generation speed
- Reduces time-to-first-token
- Best for latency-sensitive workloads

## Autoscaling Schema

```json
{
  "min_replicas": 1,
  "max_replicas": 5
}
```

- `min_replicas`: Always running (even with no traffic)
- `max_replicas`: Maximum under load
