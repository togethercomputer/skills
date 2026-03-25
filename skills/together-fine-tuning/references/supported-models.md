# Fine-tuning Supported Models
## Contents

- [Recommended Starting Models](#recommended-starting-models)
- [LoRA Fine-tuning Models](#lora-fine-tuning-models)
- [Full Fine-tuning](#full-fine-tuning)
- [VLM Fine-tuning](#vlm-fine-tuning)
- [Reasoning Fine-tuning](#reasoning-fine-tuning)
- [DPO/Preference Training](#dpopreference-training)
- [BYOM (Bring Your Own Model)](#byom)


## Recommended Starting Models

| Task | Model | API String |
|------|-------|-----------|
| Simple tasks | Qwen3 8B | `Qwen/Qwen3-8B` |
| Complex domains | Qwen3 32B | `Qwen/Qwen3-32B` |
| General (English) | Llama 3.1 8B | `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference` |
| Reasoning | Qwen3 8B+ | `Qwen/Qwen3-8B` (or larger) |
| Vision | Qwen3-VL-8B | `Qwen/Qwen3-VL-8B-Instruct` |

## LoRA Fine-tuning Models

### Large Models (MoE / 70B+)

| Organization | Model | API String | Context (SFT) |
|-------------|-------|-----------|---------------|
| Moonshot | Kimi K2.5 | `moonshotai/Kimi-K2.5` | 32K |
| Moonshot | Kimi K2 Thinking | `moonshotai/Kimi-K2-Thinking` | 32K |
| Moonshot | Kimi K2 Instruct 0905 | `moonshotai/Kimi-K2-Instruct-0905` | 32K |
| Moonshot | Kimi K2 Base | `moonshotai/Kimi-K2-Base` | 32K |
| Z.ai | GLM-4.7 | `zai-org/GLM-4.7` | 128K |
| Z.ai | GLM-4.6 | `zai-org/GLM-4.6` | 128K |
| OpenAI | GPT-OSS 120B | `openai/gpt-oss-120b` | 16K |
| OpenAI | GPT-OSS 20B | `openai/gpt-oss-20b` | 24K |
| DeepSeek | DeepSeek-R1 | `deepseek-ai/DeepSeek-R1` | 131K |
| DeepSeek | DeepSeek-V3.1 | `deepseek-ai/DeepSeek-V3.1` | 131K |
| DeepSeek | DeepSeek-V3 | `deepseek-ai/DeepSeek-V3` | 131K |
| Qwen | Qwen3 235B A22B | `Qwen/Qwen3-235B-A22B` | 41K |
| Qwen | Qwen3 235B Instruct | `Qwen/Qwen3-235B-A22B-Instruct-2507` | 49K |
| Qwen | Qwen3-Coder 480B | `Qwen/Qwen3-Coder-480B-A35B-Instruct` | 262K |
| Qwen | Qwen3-Coder 30B A3B | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 262K |
| Meta | Llama 4 Maverick | `meta-llama/Llama-4-Maverick-17B-128E-Instruct` | 16K |
| Meta | Llama 4 Scout | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | 65K |
| Meta | Llama 3.3 70B | `meta-llama/Llama-3.3-70B-Instruct-Reference` | 24K |
| Meta | Llama 3.1 70B | `meta-llama/Meta-Llama-3.1-70B-Instruct-Reference` | 24K |
| DeepSeek | R1 Distill Llama 70B | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 24K |
| Qwen | Qwen2.5 72B | `Qwen/Qwen2.5-72B-Instruct` | 24K |

### Medium Models (7B-32B)

| Organization | Model | API String | Context (SFT) |
|-------------|-------|-----------|---------------|
| Qwen | Qwen3 32B | `Qwen/Qwen3-32B` | 41K |
| Qwen | Qwen3 14B | `Qwen/Qwen3-14B` | 41K |
| Qwen | Qwen3 8B | `Qwen/Qwen3-8B` | 41K |
| Qwen | Qwen3-Next 80B A3B | `Qwen/Qwen3-Next-80B-A3B-Instruct` | 16K |
| Qwen | Qwen3 30B A3B | `Qwen/Qwen3-30B-A3B` | 8K |
| Qwen | Qwen2.5 32B Instruct | `Qwen/Qwen2.5-32B-Instruct` | 32K |
| Qwen | Qwen2.5 14B Instruct | `Qwen/Qwen2.5-14B-Instruct` | 32K |
| Qwen | Qwen2.5 7B Instruct | `Qwen/Qwen2.5-7B-Instruct` | 32K |
| Meta | Llama 3.1 8B | `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference` | 131K |
| DeepSeek | R1 Distill Qwen 14B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 65K |
| Google | Gemma 3 27B | `google/gemma-3-27b-it` | 49K |
| Google | Gemma 3 12B | `google/gemma-3-12b-it` | 65K |
| Mistral | Mixtral 8x7B | `mistralai/Mixtral-8x7B-Instruct-v0.1` | 32K |
| Mistral | Mistral 7B v0.2 | `mistralai/Mistral-7B-Instruct-v0.2` | 32K |

### Small Models (<7B)

| Organization | Model | API String | Context (SFT) |
|-------------|-------|-----------|---------------|
| Qwen | Qwen3 4B | `Qwen/Qwen3-4B` | 41K |
| Qwen | Qwen3 1.7B | `Qwen/Qwen3-1.7B` | 41K |
| Qwen | Qwen3 0.6B | `Qwen/Qwen3-0.6B` | 41K |
| Meta | Llama 3.2 3B | `meta-llama/Llama-3.2-3B-Instruct` | 131K |
| Meta | Llama 3.2 1B | `meta-llama/Llama-3.2-1B-Instruct` | 131K |
| Google | Gemma 3 4B | `google/gemma-3-4b-it` | 131K |
| Google | Gemma 3 1B | `google/gemma-3-1b-it` | 32K |
| Google | Gemma 3 270M | `google/gemma-3-270m-it` | 32K |
| Qwen | Qwen2.5 3B | `Qwen/Qwen2.5-3B-Instruct` | 32K |
| Qwen | Qwen2.5 1.5B | `Qwen/Qwen2.5-1.5B-Instruct` | 32K |
| DeepSeek | R1 Distill Qwen 1.5B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 131K |

### Long-context LoRA (32K-131K)

| Model | API String | Max Context |
|-------|-----------|-------------|
| DeepSeek R1 | `deepseek-ai/DeepSeek-R1` | 131K |
| Llama 3.3 70B 131K | `meta-llama/Llama-3.3-70B-131k-Instruct-Reference` | 131K |
| Llama 3.1 8B 131K | `meta-llama/Meta-Llama-3.1-8B-131k-Instruct-Reference` | 131K |
| Llama 3.1 70B 131K | `meta-llama/Meta-Llama-3.1-70B-131k-Instruct-Reference` | 131K |

Note: Long-context fine-tuning of Llama 3.1 models (32K-131K) is only supported using LoRA.

## Full Fine-tuning

Same models as LoRA, but batch sizes are generally smaller. Key full-fine-tuning-only models:

| Organization | Model | API String | Context (SFT) |
|-------------|-------|-----------|---------------|
| DeepSeek | R1 Distill Llama 70B | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 24K |
| DeepSeek | R1 Distill Qwen 14B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 65K |
| DeepSeek | R1 Distill Qwen 1.5B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 131K |
| Qwen | All Qwen3 variants | Various | 32K-41K |
| Google | All Gemma 3 variants | Various | 32K-131K |
| Meta | Llama 3.x variants | Various | 8K-131K |

## VLM Fine-tuning

| Model | API String | Full | LoRA |
|-------|-----------|------|------|
| Qwen3-VL-8B | `Qwen/Qwen3-VL-8B-Instruct` | Yes | Yes |
| Qwen3-VL-30B-A3B | `Qwen/Qwen3-VL-30B-A3B-Instruct` | Yes | Yes |
| Qwen3-VL-235B | `Qwen/Qwen3-VL-235B-A22B-Instruct` | No | Yes |
| Llama 4 Maverick VLM | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-VLM` | No | Yes |
| Llama 4 Scout VLM | `meta-llama/Llama-4-Scout-17B-16E-Instruct-VLM` | No | Yes |
| Gemma 3 4B VLM | `google/gemma-3-4b-it-VLM` | Yes | Yes |
| Gemma 3 12B VLM | `google/gemma-3-12b-it-VLM` | Yes | Yes |
| Gemma 3 27B VLM | `google/gemma-3-27b-it-VLM` | Yes | Yes |

## Reasoning Fine-tuning

| Organization | Model | API String |
|-------------|-------|-----------|
| Qwen | Qwen3 0.6B - 235B | `Qwen/Qwen3-*` (all sizes and base variants) |
| Qwen | Qwen3 32B 16k | `Qwen/Qwen3-32B-16k` |
| Qwen | Qwen3 30B A3B | `Qwen/Qwen3-30B-A3B` (and base) |
| Qwen | Qwen3-Next 80B Thinking | `Qwen/Qwen3-Next-80B-A3B-Thinking` |
| Z.ai | GLM 4.6 | `zai-org/GLM-4.6` |
| Z.ai | GLM 4.7 | `zai-org/GLM-4.7` |

## DPO/Preference Training

Same models as LoRA/Full fine-tuning. Additional parameters:
- `training_method`: `"dpo"`
- `dpo_beta`: 0.05-0.9 (default 0.1)
- DPO context lengths are generally half of SFT context lengths

## BYOM (Bring Your Own Model)

Fine-tune any CausalLM model from HuggingFace Hub:

```python
job = client.fine_tuning.create(
    model="Qwen/Qwen3-4B",               # Base template (infrastructure config)
    from_hf_model="my-org/my-custom-model",  # Your actual model
    training_file=file_id,
    hf_api_token="hf_xxx",               # Optional, for private repos
)
```

Important: The `model` parameter (base template) should have a similar architecture, size, and
sequence length to the `from_hf_model` for best results.

