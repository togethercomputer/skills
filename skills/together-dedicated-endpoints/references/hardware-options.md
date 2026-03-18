# Dedicated Endpoints Hardware Reference

## Hardware ID Format

`[count]x_nvidia_[gpu_type]_[memory]_[link]`

Example: `2x_nvidia_h100_80gb_sxm`

## GPU Types

| GPU | Memory | Notes |
|-----|--------|-------|
| H100 SXM | 80GB | Highest performance, recommended for production |
| A100 SXM | 80GB | Good balance of cost and performance |
| A100 PCIe | 80GB | Cost-effective option |
| L40 | 48GB | Mid-range option |
| RTX-6000 | 24GB | Entry-level for smaller models |

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
| `1x_nvidia_a100_80gb_sxm` | A100 | 1 | Small models, cost-effective |
| `2x_nvidia_a100_80gb_sxm` | A100 | 2 | Medium models, cost-effective |
| `4x_nvidia_a100_80gb_sxm` | A100 | 4 | Large models, cost-effective |
| `8x_nvidia_a100_80gb_sxm` | A100 | 8 | Very large models, cost-effective |

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
  "pricing": { "cents_per_minute": 6.0 },
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

## GPU Selection Guide

| Need | Recommendation |
|------|---------------|
| Small models (up to 9B) | 1x H100 or 1x A100 |
| Medium models (7-20B) | 1-2x H100/A100 |
| Large models (70B) | 4-8x H100/A100 |
| Very large / MoE models (120B+) | 8x H100 |
| Maximum throughput | 8x H100 + multiple replicas |
| Cost-effective | A100 (lower per-minute cost) |
| Maximum performance | H100 (faster inference) |

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
