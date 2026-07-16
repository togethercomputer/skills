# Dedicated model catalog

Together publishes a rolling catalog of models supported for dedicated model inference (DMI). The
canonical list is the [supported-models
page](https://docs.together.ai/docs/dedicated-endpoints/models), which shows each architecture,
its `displayType`, and the instance type of its smallest published [deployment
profile](models-and-configs.md).

The list below is a snapshot for quick reference. Always confirm with `tg beta models public
--product DEDICATED` (v2) or `together models list --type dedicated` (v1) before you commit — the
catalog changes as new architectures land and old ones age out.

## Contents

- [How to list models](#how-to-list-models)
- [Chat and language models](#chat-and-language-models)
- [Image models](#image-models)
- [Transcription models](#transcription-models)
- [Moderation models](#moderation-models)
- [Rerank models](#rerank-models)
- [Fine-tuned and uploaded models](#fine-tuned-and-uploaded-models)

## How to list models

### v2 (default)

```bash
# All models available for dedicated inference (JSON records with deployment profiles)
tg beta models public --product DEDICATED --json

# Filter
tg beta models public --modality TEXT --search qwen
tg beta models public --modality VIDEO

# Configs published for a specific weight
tg beta models configs ml_CbJNwQC2ZqCU2iFT3mrCh
```

Each record includes `id` (`arch_...`), `name` (Hugging Face model ID), `displayName`,
`displayType`, and `deploymentProfiles[]` with the certified model + config pair. See
[models-and-configs.md](models-and-configs.md#list-supported-models) for the response shape.

### v1 (legacy)

```bash
together models list --type dedicated
together models list --json
```

```python
models = client.models.list()  # filter for dedicated eligibility in client-side
```

## Chat and language models

| Model | API ID | Context |
| --- | --- | --- |
| DeepSeek R1-0528 | `deepseek-ai/DeepSeek-R1` | 163,840 |
| DeepSeek R1 Distill Llama 70B | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 131,072 |
| DeepSeek R1 Distill Qwen 14B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 131,072 |
| DeepSeek V3-0324 | `deepseek-ai/DeepSeek-V3` | 131,072 |
| DeepSeek V3.1 | `deepseek-ai/DeepSeek-V3.1` | 131,072 |
| LLaMA-2 70B | `meta-llama/Llama-2-70b-hf` | 4,096 |
| Llama 3.1 405B Instruct | `meta-llama/Llama-3.1-405B-Instruct` | 4,096 |
| Llama 3.2 1B Instruct | `meta-llama/Llama-3.2-1B-Instruct` | 131,072 |
| Llama 3.3 70B Instruct Turbo | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 131,072 |
| Llama 4 Maverick 17Bx128E | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` | 1,048,576 |
| Llama 4 Scout 17Bx16E | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | 1,048,576 |
| Meta Llama 3 70B Instruct Turbo | `meta-llama/Meta-Llama-3-70B-Instruct-Turbo` | 8,192 |
| Meta Llama 3 8B Instruct | `meta-llama/Meta-Llama-3-8B-Instruct` | 8,192 |
| Mistral 7B Instruct v0.1 | `mistralai/Mistral-7B-Instruct-v0.1` | 32,768 |
| Mistral 7B Instruct v0.2 | `mistralai/Mistral-7B-Instruct-v0.2` | 32,768 |
| Mistral 7B Instruct v0.3 | `mistralai/Mistral-7B-Instruct-v0.3` | 32,768 |
| Mixtral-8x7B Instruct v0.1 | `mistralai/Mixtral-8x7B-Instruct-v0.1` | 32,768 |
| OpenAI GPT-OSS 120B | `openai/gpt-oss-120b` | 131,072 |
| OpenAI GPT-OSS 20B | `openai/gpt-oss-20b` | 131,072 |
| Qwen2.5 72B Instruct | `Qwen/Qwen2.5-72B-Instruct` | 32,768 |
| Qwen2.5 72B Instruct Turbo | `Qwen/Qwen2.5-72B-Instruct-Turbo` | 131,072 |
| Qwen2.5 7B Instruct Turbo | `Qwen/Qwen2.5-7B-Instruct-Turbo` | 32,768 |
| Qwen2.5 Coder 32B Instruct | `Qwen/Qwen2.5-Coder-32B-Instruct` | 16,384 |
| Qwen2.5-VL 72B Instruct | `Qwen/Qwen2.5-VL-72B-Instruct` | 32,768 |
| Qwen3 235B A22B FP8 | `Qwen/Qwen3-235B-A22B-fp8-tput` | 40,960 |
| Qwen3 Coder 480B A35B FP8 | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | 262,144 |
| Qwen3 Next 80B A3B | `Qwen/Qwen3-Next-80B-A3B-Instruct` | 262,144 |
| QwQ-32B | `Qwen/QwQ-32B` | 131,072 |
| GLM-4.5 Air FP8 | `zai-org/GLM-4.5-Air-FP8` | 131,072 |

## Image models

| Model | API ID |
| --- | --- |
| FLUX.1 Kontext [max] | `black-forest-labs/FLUX.1-kontext-max` |
| FLUX.1 Kontext [pro] | `black-forest-labs/FLUX.1-kontext-pro` |

## Transcription models

| Model | API ID |
| --- | --- |
| Whisper large-v3 | `openai/whisper-large-v3` |

## Moderation models

| Model | API ID | Context |
| --- | --- | --- |
| Llama Guard 4 12B | `meta-llama/Llama-Guard-4-12B` | 1,048,576 |

## Rerank models

| Model | API ID | Context |
| --- | --- | --- |
| Llama Rank V1 | `Salesforce/Llama-Rank-V1` | 8,192 |

## Fine-tuned and uploaded models

Fine-tuned and uploaded models are also deployable on DMI, subject to two rules:

- **Base architecture must be supported.** An upload can't introduce a new base architecture.
- **File format must match `from_pretrained` layout** — `config.json`, tokenizer files, sharded
  `model-*.safetensors`, and index files. Adapters require `adapter_config.json` and
  `adapter_model.safetensors`.

The v2 upload workflow is `tg beta models create` → `tg beta models upload` (or
`remote-uploads create`) → poll job → `tg beta endpoints deploy`. See
[models-and-configs.md](models-and-configs.md#upload-a-fine-tuned-model) for the walkthrough,
including LoRA adapters and troubleshooting.
