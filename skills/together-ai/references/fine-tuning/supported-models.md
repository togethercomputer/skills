# Fine-tuning Supported Models
## Contents

- [Recommended Starting Models](#recommended-starting-models)
- [LoRA Fine-tuning Models](#lora-fine-tuning-models)
- [Full Fine-tuning](#full-fine-tuning)
- [VLM Fine-tuning](#vlm-fine-tuning)
- [Reasoning Fine-tuning](#reasoning-fine-tuning)
- [Function-calling Fine-tuning](#function-calling-fine-tuning)
- [DPO/Preference Training](#dpopreference-training)
- [Removed Models](#removed-models)
- [BYOM (Bring Your Own Model)](#byom)

Snapshot of the 29 base models in `GET /v1/fine-tunes/models/supported`, checked 2026-10-26. The
catalog changes: `tg fine-tuning model-limits MODEL` confirms a model and returns its limits. To
serve the result on a dedicated endpoint, the base model must also be deployable there
(`tg models configs MODEL`).

## Recommended Starting Models

| Task | Model | API String |
|------|-------|-----------|
| Simple tasks | Qwen3.5 9B | `Qwen/Qwen3.5-9B` |
| Complex domains | Qwen3.5 27B | `Qwen/Qwen3.5-27B` |
| General (English) | Llama 3.1 8B | `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference` |
| Reasoning | Qwen3.5 9B+ | `Qwen/Qwen3.5-9B` (or larger) |
| Vision | Qwen3.5 9B | `Qwen/Qwen3.5-9B` (the same ID takes image data) |

## LoRA Fine-tuning Models

Every model supports LoRA. Context is the maximum sequence length per training example.

### Large Models (70B+ total parameters)

| Organization | Model | API String | Context (SFT) | Context (DPO) |
|-------------|-------|-----------|---------------|---------------|
| DeepSeek | DeepSeek V4 Flash | `deepseek-ai/DeepSeek-V4-Flash` | 131K | 32K |
| DeepSeek | DeepSeek V4 Flash 0731 | `deepseek-ai/DeepSeek-V4-Flash-0731` | 131K | 32K |
| DeepSeek | DeepSeek V3.1 | `deepseek-ai/DeepSeek-V3.1` | 65K | 32K |
| Z.ai | GLM 5.3 | `zai-org/GLM-5.3` | 50K | 25K |
| Z.ai | GLM 5.2 | `zai-org/GLM-5.2` | 50K | 25K |
| Z.ai | GLM 5.1 | `zai-org/GLM-5.1` | 50K | 25K |
| Moonshot | Kimi K2.7 Code | `moonshotai/Kimi-K2.7-Code` | 32K | 16K |
| Moonshot | Kimi K2.6 | `moonshotai/Kimi-K2.6` | 32K | 16K |
| Qwen | Qwen3.5 397B A17B | `Qwen/Qwen3.5-397B-A17B` | 32K | 16K |
| Qwen | Qwen3.5 122B A10B | `Qwen/Qwen3.5-122B-A10B` | 65K | 32K |
| OpenAI | GPT-OSS 120B | `openai/gpt-oss-120b` | 65K | 32K |
| Meta | Llama 4 Maverick | `meta-llama/Llama-4-Maverick-17B-128E-Instruct` | 16K | 24K |
| Meta | Llama 4 Scout | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | 65K | 12K |
| Meta | Llama 3.3 70B | `meta-llama/Llama-3.3-70B-Instruct-Reference` | 24K | 12K |

### Small and Medium Models (under 70B)

| Organization | Model | API String | Context (SFT) | Context (DPO) |
|-------------|-------|-----------|---------------|---------------|
| Qwen | Qwen3.8 27B | `Qwen/Qwen3.8-27B` | 131K | 65K |
| Qwen | Qwen3.6 35B A3B | `Qwen/Qwen3.6-35B-A3B` | 65K | 32K |
| Qwen | Qwen3.6 27B | `Qwen/Qwen3.6-27B` | 131K | 65K |
| Qwen | Qwen3.5 35B A3B | `Qwen/Qwen3.5-35B-A3B` | 65K | 32K |
| Qwen | Qwen3.5 27B | `Qwen/Qwen3.5-27B` | 131K | 65K |
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 65K | 49K |
| Qwen | Qwen3.5 4B | `Qwen/Qwen3.5-4B` | 131K | 65K |
| Google | Gemma 4 31B IT | `google/gemma-4-31B-it` | 49K | 24K |
| Google | Gemma 4 26B A4B IT | `google/gemma-4-26B-A4B-it` | 49K | 24K |
| OpenAI | GPT-OSS 20B | `openai/gpt-oss-20b` | 131K | 65K |
| Meta | Llama 3.1 8B | `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference` | 131K | 65K |
| Mistral | Mixtral 8x7B | `mistralai/Mixtral-8x7B-Instruct-v0.1` | 32K | 16K |

The `-VLM` IDs for Gemma 4 and Llama 4 are listed under [VLM Fine-tuning](#vlm-fine-tuning).
There are no separate long-context (`-32k`, `-131k`) variants any more; use the base ID.

### LoRA rank

If `lora_r` is not set, the job uses the model's default rank, and `lora_alpha` defaults to twice
the rank. Setting `lora_r` above the model's max returns an error.

| Default | Max | Models |
|---------|-----|--------|
| 16 | 16 | Z.ai GLM 5.1, 5.2, 5.3; Moonshot Kimi K2.6, K2.7 Code; DeepSeek V3.1 |
| 64 | 128 | All other models, including DeepSeek V4 Flash |

## Full Fine-tuning

Only these models support full fine-tuning (`lora=False`); all others are LoRA-only.

| Organization | Model | API String | Context (SFT) |
|-------------|-------|-----------|---------------|
| Qwen | Qwen3.8 27B | `Qwen/Qwen3.8-27B` | 131K |
| Qwen | Qwen3.6 27B | `Qwen/Qwen3.6-27B` | 131K |
| Qwen | Qwen3.5 27B | `Qwen/Qwen3.5-27B` | 131K |
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 65K |
| Qwen | Qwen3.5 4B | `Qwen/Qwen3.5-4B` | 131K |
| Google | Gemma 4 31B IT | `google/gemma-4-31B-it` | 49K |
| Google | Gemma 4 31B IT VLM | `google/gemma-4-31B-it-VLM` | 24K |
| Meta | Llama 3.3 70B | `meta-llama/Llama-3.3-70B-Instruct-Reference` | 24K |
| Meta | Llama 3.1 8B | `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference` | 131K |
| Mistral | Mixtral 8x7B | `mistralai/Mixtral-8x7B-Instruct-v0.1` | 32K |

## VLM Fine-tuning

Qwen models take image data under their usual ID; Gemma 4 and Llama 4 need the `-VLM` ID.

| Model | API String | Context (SFT) | Full | LoRA |
|-------|-----------|---------------|------|------|
| Qwen3.8 27B | `Qwen/Qwen3.8-27B` | 131K | Yes | Yes |
| Qwen3.6 27B | `Qwen/Qwen3.6-27B` | 131K | Yes | Yes |
| Qwen3.5 27B | `Qwen/Qwen3.5-27B` | 131K | Yes | Yes |
| Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 65K | Yes | Yes |
| Qwen3.5 4B | `Qwen/Qwen3.5-4B` | 131K | Yes | Yes |
| Gemma 4 31B IT VLM | `google/gemma-4-31B-it-VLM` | 24K | Yes | Yes |
| Llama 4 Maverick VLM | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-VLM` | 16K | No | Yes |
| Llama 4 Scout VLM | `meta-llama/Llama-4-Scout-17B-16E-Instruct-VLM` | 32K | No | Yes |

## Reasoning Fine-tuning

| Organization | Model | API String |
|-------------|-------|-----------|
| Qwen | Qwen3.8 27B | `Qwen/Qwen3.8-27B` |
| Qwen | Qwen3.6 family | `Qwen/Qwen3.6-27B`, `Qwen/Qwen3.6-35B-A3B` |
| Qwen | Qwen3.5 family | `Qwen/Qwen3.5-*` (4B, 9B, 27B, 35B-A3B, 122B-A10B, 397B-A17B) |
| Z.ai | GLM 5.1 - 5.3 | `zai-org/GLM-5.1`, `zai-org/GLM-5.2`, `zai-org/GLM-5.3` |
| DeepSeek | DeepSeek V4 Flash | `deepseek-ai/DeepSeek-V4-Flash`, `deepseek-ai/DeepSeek-V4-Flash-0731` |
| Google | Gemma 4 | `google/gemma-4-31B-it`, `google/gemma-4-31B-it-VLM`, `google/gemma-4-26B-A4B-it` |
| OpenAI | GPT-OSS | `openai/gpt-oss-120b`, `openai/gpt-oss-20b` |

## Function-calling Fine-tuning

Every model above supports tool-call training data except the DeepSeek models (V3.1, V4 Flash)
and Mixtral 8x7B.

## DPO/Preference Training

Every model above supports DPO; see the Context (DPO) column for its limit. Additional parameters:
- `training_method`: `"dpo"`
- `dpo_beta`: 0.05-0.9 (default 0.1)

## Removed Models

Together removed about 100 base models from fine-tuning on 2026-07-29, and jobs that name them
fail. Replacements for the common ones (full list on the
[deprecations page](https://docs.together.ai/docs/deprecations#fine-tuning)):

| Removed | Use instead |
|---------|-------------|
| `Qwen/Qwen3-8B`, `Qwen/Qwen3-VL-8B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`, `nvidia/NVIDIA-Nemotron-Nano-9B-v2` | `Qwen/Qwen3.5-9B` |
| `Qwen/Qwen3-4B`, `Qwen/Qwen2.5-3B-Instruct` | `Qwen/Qwen3.5-4B` |
| `Qwen/Qwen3-14B`, `Qwen/Qwen3-32B`, `Qwen/Qwen2.5-14B-Instruct`, `Qwen/Qwen2.5-32B-Instruct` | `Qwen/Qwen3.5-27B` |
| `Qwen/Qwen3-30B-A3B`, `Qwen/Qwen3-Coder-30B-A3B-Instruct` | `Qwen/Qwen3.6-35B-A3B` |
| `Qwen/Qwen3-235B-A22B`, `Qwen/Qwen3-235B-A22B-Instruct-2507` | `Qwen/Qwen3.5-397B-A17B` |
| `Qwen/Qwen3-Next-80B-A3B-Instruct`, `Qwen/Qwen3-Next-80B-A3B-Thinking` | `Qwen/Qwen3.5-122B-A10B` |
| `moonshotai/Kimi-K2.5`, `Kimi-K2-Thinking`, `Kimi-K2-Instruct-0905`, `Kimi-K2-Instruct`, `Kimi-K2-Base` | `moonshotai/Kimi-K2.6` |
| `zai-org/GLM-5`, `zai-org/GLM-4.7`, `zai-org/GLM-4.6` | `zai-org/GLM-5.1` |
| `deepseek-ai/DeepSeek-R1`, `-R1-0528`, `-V3`, `-V3-0324` (and `-Base` variants) | `deepseek-ai/DeepSeek-V3.1` |
| `meta-llama/Llama-3.2-3B-Instruct`, `Llama-3.2-1B-Instruct`, Llama 3.1 8B `-131k` and base variants | `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference` |
| Llama 3.1 70B, Llama 3.3 70B `-32k`/`-131k`, `Qwen/Qwen2.5-72B-Instruct`, `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | `meta-llama/Llama-3.3-70B-Instruct-Reference` |
| `google/gemma-3-1b-it`, `gemma-3-4b-it`, `gemma-3-12b-it` | `google/gemma-4-26B-A4B-it` |
| `google/gemma-3-27b-it` | `google/gemma-4-31B-it` |
| `google/gemma-3-12b-it-VLM`, `gemma-3-27b-it-VLM` | `google/gemma-4-31B-it-VLM` |
| `mistralai/Mistral-7B-Instruct-v0.2` | `mistralai/Mixtral-8x7B-Instruct-v0.1` |

No direct replacement: Llama 3.1 405B, Qwen3-Coder 480B, Qwen3-VL 32B and 235B. For the smallest
removed models (Qwen3 0.6B and 1.7B, Qwen2.5 1.5B, Gemma 3 270M) the deprecations page suggests
`Qwen/Qwen3.5-0.8B` or `Qwen/Qwen3.5-2B`, but neither is in the catalog; the smallest available
model is `Qwen/Qwen3.5-4B`.

## BYOM (Bring Your Own Model)

Fine-tune a CausalLM model from Hugging Face Hub (under 100B parameters, `.safetensors` weights,
no custom code):

```python
job = client.fine_tuning.create(
    model="Qwen/Qwen3.5-4B",              # Base template (infrastructure config)
    from_hf_model="my-org/my-custom-model",  # Your actual model
    training_file=file_id,
    hf_api_token="hf_xxx",               # Optional, for private repos
)
```

Important: The `model` parameter (base template) should have a similar architecture, size, and
sequence length to the `from_hf_model` for best results.
