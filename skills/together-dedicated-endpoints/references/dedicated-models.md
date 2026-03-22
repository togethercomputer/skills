# Dedicated Endpoints Model Reference
## Contents

- [Chat Models](#chat-models)
- [Image Models](#image-models)
- [Transcription Models](#transcription-models)
- [Moderation Models](#moderation-models)
- [Rerank Models](#rerank-models)
- [Custom and Fine-tuned Models](#custom-and-fine-tuned-models)


Models available for deployment on dedicated endpoints. This list changes frequently -- use
`together models list --type dedicated` for the current catalog.

## Chat Models

| Model | API ID | Context |
|-------|--------|---------|
| DeepSeek R1-0528 | deepseek-ai/DeepSeek-R1 | 163,840 |
| DeepSeek R1 Distill Llama 70B | deepseek-ai/DeepSeek-R1-Distill-Llama-70B | 131,072 |
| DeepSeek R1 Distill Qwen 14B | deepseek-ai/DeepSeek-R1-Distill-Qwen-14B | 131,072 |
| DeepSeek V3-0324 | deepseek-ai/DeepSeek-V3 | 131,072 |
| DeepSeek V3.1 | deepseek-ai/DeepSeek-V3.1 | 131,072 |
| LLaMA-2 70B | meta-llama/Llama-2-70b-hf | 4,096 |
| Llama 3.1 405B Instruct | meta-llama/Llama-3.1-405B-Instruct | 4,096 |
| Llama 3.2 1B Instruct | meta-llama/Llama-3.2-1B-Instruct | 131,072 |
| Llama 3.3 70B Instruct Turbo | meta-llama/Llama-3.3-70B-Instruct-Turbo | 131,072 |
| Llama 4 Maverick 17Bx128E | meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 | 1,048,576 |
| Llama 4 Scout 17Bx16E | meta-llama/Llama-4-Scout-17B-16E-Instruct | 1,048,576 |
| Meta Llama 3 70B Instruct Turbo | meta-llama/Meta-Llama-3-70B-Instruct-Turbo | 8,192 |
| Meta Llama 3 8B Instruct | meta-llama/Meta-Llama-3-8B-Instruct | 8,192 |
| Mistral 7B Instruct v0.1 | mistralai/Mistral-7B-Instruct-v0.1 | 32,768 |
| Mistral 7B Instruct v0.2 | mistralai/Mistral-7B-Instruct-v0.2 | 32,768 |
| Mistral 7B Instruct v0.3 | mistralai/Mistral-7B-Instruct-v0.3 | 32,768 |
| Mixtral-8x7B Instruct v0.1 | mistralai/Mixtral-8x7B-Instruct-v0.1 | 32,768 |
| OpenAI GPT-OSS 120B | openai/gpt-oss-120b | 131,072 |
| OpenAI GPT-OSS 20B | openai/gpt-oss-20b | 131,072 |
| Qwen2.5 72B Instruct | Qwen/Qwen2.5-72B-Instruct | 32,768 |
| Qwen2.5 72B Instruct Turbo | Qwen/Qwen2.5-72B-Instruct-Turbo | 131,072 |
| Qwen2.5 7B Instruct Turbo | Qwen/Qwen2.5-7B-Instruct-Turbo | 32,768 |
| Qwen2.5 Coder 32B Instruct | Qwen/Qwen2.5-Coder-32B-Instruct | 16,384 |
| Qwen2.5-VL 72B Instruct | Qwen/Qwen2.5-VL-72B-Instruct | 32,768 |
| Qwen3 235B A22B FP8 | Qwen/Qwen3-235B-A22B-fp8-tput | 40,960 |
| Qwen3 Coder 480B A35B FP8 | Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8 | 262,144 |
| Qwen3 Next 80B A3B | Qwen/Qwen3-Next-80B-A3B-Instruct | 262,144 |
| QwQ-32B | Qwen/QwQ-32B | 131,072 |
| GLM-4.5 Air FP8 | zai-org/GLM-4.5-Air-FP8 | 131,072 |

## Image Models

| Model | API ID |
|-------|--------|
| FLUX.1 Kontext [max] | black-forest-labs/FLUX.1-kontext-max |
| FLUX.1 Kontext [pro] | black-forest-labs/FLUX.1-kontext-pro |

## Transcription Models

| Model | API ID |
|-------|--------|
| Whisper large-v3 | openai/whisper-large-v3 |

## Moderation Models

| Model | API ID | Context |
|-------|--------|---------|
| Llama Guard 4 12B | meta-llama/Llama-Guard-4-12B | 1,048,576 |

## Rerank Models

| Model | API ID | Context |
|-------|--------|---------|
| Llama Rank V1 | Salesforce/Llama-Rank-V1 | 8,192 |

## Custom and Fine-tuned Models

Custom uploaded models and fine-tuned models can also be deployed on dedicated endpoints.

### Requirements

- **Format**: Hugging Face-compatible (`config.json`, tokenizer files, safetensors)
- **Types**: Text generation and embedding models
- **Scale**: Must fit on a single node (multi-node not supported)
- **Fine-tuned**: Base model must be a supported dedicated endpoint model
- **Sources**: Hugging Face Hub or S3 (`.zip`, `.tar`, `.tar.gz`)

### Upload Custom Model

```python
from together import Together
client = Together()

# From Hugging Face
response = client.models.upload(
    model_name="my-custom-model",
    model_source="https://huggingface.co/your-org/your-model",
    hf_token="hf_...",
)
print(response.data.job_id)

# From S3 (presigned URL, at least 100 min validity)
response = client.models.upload(
    model_name="my-s3-model",
    model_source="https://my-bucket.s3.amazonaws.com/model.tar.gz?...",
)
```

```shell
# From Hugging Face
together models upload \
  --model-name my-custom-model \
  --model-source https://huggingface.co/your-org/your-model \
  --hf-token $HF_TOKEN

# From S3
together models upload \
  --model-name my-s3-model \
  --model-source "$PRESIGNED_URL"
```

### Deploy Custom or Fine-tuned Model

```shell
# Verify model appears
together models list

# Check hardware options
together endpoints hardware --model <model-name>

# Deploy
together endpoints create \
  --model <model-name> \
  --hardware 2x_nvidia_h100_80gb_sxm \
  --display-name "Custom Model Endpoint" \
  --no-speculative-decoding \
  --wait
```

### Deploy Fine-tuned Model

```shell
# Find model output name from fine-tuning job
together fine-tuning list

# Deploy
together endpoints create \
  --model <your-model-output-name> \
  --hardware 4x_nvidia_h100_80gb_sxm \
  --display-name "Fine-tuned Endpoint" \
  --wait
```
