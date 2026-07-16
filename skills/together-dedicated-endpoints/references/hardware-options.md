# Hardware and pricing

Dedicated model inference bills by the minute per running replica, by hardware. Model, prompt
volume, and request count don't affect the per-replica price — a larger model just needs bigger or
more GPUs.

## Contents

- [Instance type IDs (v2)](#instance-type-ids-v2)
- [Hardware IDs (v1, legacy)](#hardware-ids-v1-legacy)
- [Currently offered GPUs](#currently-offered-gpus)
- [Per-hour pricing](#per-hour-pricing)
- [On-demand vs reserved](#on-demand-vs-reserved)
- [How scaling affects cost](#how-scaling-affects-cost)
- [Instance-type headroom](#instance-type-headroom)
- [GPU selection guide](#gpu-selection-guide)
- [Query hardware programmatically](#query-hardware-programmatically)
- [Deprecated hardware families](#deprecated-hardware-families)

## Instance type IDs (v2)

DMI v2 refers to hardware by **instance type**, identified with a dashed lowercase ID like
`1xnvidia-h100-80gb`. Each instance type has a per-hour price and per-region capacity. A config's
`accelerator_type` + `accelerator_count` selectors map to an instance type; the deployment inherits
it from the config you pick.

Currently listed instance types:

| Instance type | GPU |
| --- | --- |
| `1xnvidia-h100-80gb` | 1x H100 80GB |
| `1xnvidia-h200-141gb` | 1x H200 141GB |
| `1xnvidia-b200-180gb` | 1x B200 180GB |
| `1xnvidia-gb300-280gb` | 1x GB300 280GB |
| `1xnvidia-b300-280gb` | 1x B300 280GB |

Multi-GPU configs use the same GPU model in higher counts and cost proportionally more (see
[Per-hour pricing](#per-hour-pricing)). List every instance type — including multi-GPU variants —
with the public catalog:

```bash
curl -s -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.ai/v2/public/inference-instance-types
```

## Hardware IDs (v1, legacy)

v1 endpoints use the older underscore format, for example `1x_nvidia_h100_80gb_sxm`. These IDs are
returned by `/v1/hardware` and accepted by `together endpoints create --hardware`. Format:

```
[count]x_nvidia_[gpu_type]_[memory]_[link]
```

Example v1 hardware IDs:

| Hardware ID (v1) | GPU | Typical use |
| --- | --- | --- |
| `1x_nvidia_h100_80gb_sxm` | 1x H100 | Small models (up to ~9B) |
| `2x_nvidia_h100_80gb_sxm` | 2x H100 | Medium models (7–20B) |
| `4x_nvidia_h100_80gb_sxm` | 4x H100 | Large models (70B) |
| `8x_nvidia_h100_80gb_sxm` | 8x H100 | Very large models (120B+, MoE) |
| `1x_nvidia_h200_140gb_sxm` | 1x H200 | Memory-bound small/medium |
| `4x_nvidia_h200_140gb_sxm` | 4x H200 | Large + bigger KV cache |
| `8x_nvidia_h200_140gb_sxm` | 8x H200 | Very large / long-context |
| `1x_nvidia_b200_180gb_sxm` | 1x B200 | Highest single-GPU perf |
| `8x_nvidia_b200_180gb_sxm` | 8x B200 | Max throughput / largest models |

v1 hardware IDs and v2 instance type IDs address the same underlying hardware but are not
interchangeable across the two APIs.

## Currently offered GPUs

| GPU family | Memory | Notes |
| --- | --- | --- |
| H100 SXM | 80 GB | Production workhorse; broadest model coverage. |
| H200 SXM | 141 GB | Larger HBM for memory-bound / long-context workloads. |
| B200 SXM | 180 GB | Highest per-GPU performance; largest single-GPU memory. |
| B300 SXM | 280 GB | Next-generation. Contact sales. |
| GB300 | 280 GB | Grace-Blackwell superchip. Contact sales. |

## Per-hour pricing

Public rates from the DMI [pricing page](https://docs.together.ai/docs/dedicated-endpoints/pricing).
Multi-GPU configs of the same family cost proportionally more (a 4-GPU config costs 4x the
single-GPU rate).

| GPU | Instance type (v2) | Cost/hour |
| --- | --- | --- |
| H100 80GB | `1xnvidia-h100-80gb` | $5.49 |
| H200 141GB | `1xnvidia-h200-141gb` | Contact sales |
| B200 180GB | `1xnvidia-b200-180gb` | $8.99 |
| GB300 280GB | `1xnvidia-gb300-280gb` | Contact sales |
| B300 280GB | `1xnvidia-b300-280gb` | Contact sales |

Each running replica bills independently. A deployment running three replicas bills three times
the single-replica rate. Replicas stop billing as soon as they scale down; a deployment at zero
replicas (or stopped) costs nothing.

Prices update over time — for the authoritative live rates always call the
`/v2/public/inference-instance-types` endpoint or the pricing page.

## On-demand vs reserved

- **On-demand** — Per-minute rate for as long as replicas run, no commitment. Capacity scales
  within replica bounds. Best for variable traffic and prototyping.
- **Reserved** — Committed capacity for a set term at a lower effective rate, with guaranteed
  hardware availability. Best for steady production traffic.
  [Contact sales](https://www.together.ai/forms/monthly-reserved) to arrange.

## How scaling affects cost

Billing is proportional to running replicas across all deployments in your project.

- `minReplicas` sets the **floor** on cost. These replicas always run and always bill.
- `maxReplicas` sets the **ceiling** on cost. The deployment never bills for more than this many
  replicas at once.
- Stopped or `0/0` deployments bill nothing. Restarting one costs a
  [cold start](https://docs.together.ai/docs/dedicated-endpoints/concepts#cold-starts) on the first
  request afterward.

**There is no automatic idle shutdown at launch on v2.** v1 endpoints auto-stop after
`inactive_timeout` minutes (default 60); on v2 you must scale to `0/0` to stop billing when the
workload is idle.

### DMI vs serverless break-even (rule of thumb)

- A single H100 replica at $5.49/hr is ~$132/day, or ~$3,950 across a 30-day month if it runs
  continuously.
- Serverless is usually cheaper for low or bursty traffic; DMI is usually cheaper when a replica
  would stay busy most of the day.
- Stopping DMI when idle narrows the gap for spiky traffic. It doesn't help for steady low-volume
  traffic around the clock — serverless wins there.

## Instance-type headroom

Region availability is reported as `headroom`. For each region, `/v2/public/inference-instance-types`
returns how many more replicas currently fit. A headroom value of `N` with the `RELATION_GTE`
relation means at least N units are free; actual availability may be higher. Use it to pick a
region with capacity before you deploy.

## GPU selection guide

| Need | Recommendation |
| --- | --- |
| Small models (≤ 9B) | 1x H100 |
| Medium models (7–20B) | 1–2x H100 |
| Large models (70B) | 4–8x H100 or 4x H200 |
| Very large / MoE models (120B+) | 8x H100, 8x H200, or 8x B200 |
| Maximum throughput | 8x B200 + multiple replicas |
| Cost-effective baseline | H100 (lowest per-hour listed rate) |
| Long-context / memory-bound | H200 or B200 (larger HBM) |
| Maximum single-GPU performance | B200 (or B300 / GB300 for the newest generation) |

Fine-tuned and uploaded models may require larger hardware than their base parameter count
suggests. On v2, always list the profiles published for the specific weight and pick a config from
the list:

```bash
tg beta models configs ml_your_model_id
```

## Query hardware programmatically

### v2

```bash
# All instance types with per-region headroom
curl -s -H "Authorization: Bearer $TOGETHER_API_KEY" \
  https://api.together.ai/v2/public/inference-instance-types

# All configs published for a specific weight
tg beta models configs ml_CbJNwQC2ZqCU2iFT3mrCh

# Every deployment profile in the public catalog (per-architecture)
tg beta models public --product DEDICATED --json
```

### v1 (legacy)

```python
response = client.endpoints.list_hardware(model="Qwen/Qwen3.5-9B-FP8")
for hw in response.data:
    status = hw.availability.status if hw.availability else "unknown"
    price = hw.pricing.cents_per_minute if hw.pricing else "N/A"
    print(f"  {hw.id}  ({status}, {price}c/min)")
```

```bash
together endpoints hardware --model Qwen/Qwen3.5-9B-FP8 --available
```

v1 `Hardware` object:

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

Availability values: `available`, `unavailable`, `insufficient`.

## Deprecated hardware families

A100, L40, L40S, and RTX 6000 are no longer offered for new dedicated endpoints. The v1
`/v1/hardware` endpoint may still return deprecated SKUs; treat only H100, H200, and B200 (plus
the contact-sales-only B300 and GB300) as deployable.
