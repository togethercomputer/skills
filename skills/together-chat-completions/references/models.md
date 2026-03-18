# Chat Model Catalog

## Recommended Models by Use Case

| Use Case | Model | API String | Alternatives |
|----------|-------|-----------|-------------|
| Chat (best) | Kimi K2.5 (instant) | `moonshotai/Kimi-K2.5` | `deepseek-ai/DeepSeek-V3.1`, `openai/gpt-oss-120b` |
| Reasoning | Kimi K2.5 (thinking) | `moonshotai/Kimi-K2.5` | `deepseek-ai/DeepSeek-R1` |
| Coding Agents | Kimi K2.5 (thinking) | `moonshotai/Kimi-K2.5` | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8`, `deepseek-ai/DeepSeek-V3.1` |
| Small & Fast | GPT-OSS 20B | `openai/gpt-oss-20b` | `Qwen/Qwen2.5-7B-Instruct-Turbo` |
| Medium General | GPT-OSS 120B | `openai/gpt-oss-120b` | `zai-org/GLM-4.5-Air-FP8` |
| Function Calling | GLM-5 | `zai-org/GLM-5` | `moonshotai/Kimi-K2.5` |
| Vision | Kimi K2.5 | `moonshotai/Kimi-K2.5` | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` |

## Full Chat Model Catalog

| Organization | Model | API String | Context | Quant |
|-------------|-------|-----------|---------|-------|
| Moonshot | Kimi K2.5 | `moonshotai/Kimi-K2.5` | 262,144 | INT4 |
| Qwen | Qwen3.5 397B | `Qwen/Qwen3.5-397B-A17B` | 262,144 | BF16 |
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 128,000 | BF16 |
| Qwen | Qwen3-Coder 480B | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | 256,000 | FP8 |
| Qwen | Qwen3-Coder-Next | `Qwen/Qwen3-Coder-Next-FP8` | 262,144 | FP8 |
| Qwen | Qwen3 235B Instruct | `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` | 262,144 | FP8 |
| Qwen | Qwen3-Next 80B Instruct | `Qwen/Qwen3-Next-80B-A3B-Instruct` | 262,144 | BF16 |
| MiniMax | MiniMax M2.5 | `MiniMaxAI/MiniMax-M2.5` | 228,700 | FP4 |
| DeepSeek | DeepSeek-V3.1 | `deepseek-ai/DeepSeek-V3.1` | 128,000 | FP8 |
| DeepSeek | DeepSeek-R1 | `deepseek-ai/DeepSeek-R1` | 163,839 | FP8 |
| OpenAI | GPT-OSS 120B | `openai/gpt-oss-120b` | 128,000 | MXFP4 |
| OpenAI | GPT-OSS 20B | `openai/gpt-oss-20b` | 128,000 | MXFP4 |
| Z.ai | GLM-5 | `zai-org/GLM-5` | 202,752 | FP4 |
| Z.ai | GLM 4.7 | `zai-org/GLM-4.7` | 202,752 | FP8 |
| Z.ai | GLM 4.5 Air | `zai-org/GLM-4.5-Air-FP8` | 131,072 | FP8 |
| Meta | Llama 4 Maverick | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` | 1,048,576 | FP8 |
| Meta | Llama 3.3 70B Turbo | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 131,072 | FP8 |
| Deep Cogito | Cogito v2.1 671B | `deepcogito/cogito-v2-1-671b` | 32,768 | FP8 |
| Mistral | Mistral Small 24B | `mistralai/Mistral-Small-24B-Instruct-2501` | 32,768 | FP16 |
| Mistral | Mistral 7B v0.2 | `mistralai/Mistral-7B-Instruct-v0.2` | 32,768 | FP16 |
| Google | Gemma 3N E4B | `google/gemma-3n-E4B-it` | 32,768 | FP8 |
| Qwen | Qwen 2.5 7B Turbo | `Qwen/Qwen2.5-7B-Instruct-Turbo` | 32,768 | FP8 |
| Essential AI | Rnj-1 Instruct | `essentialai/rnj-1-instruct` | 32,768 | BF16 |

## Vision Models

| Organization | Model | API String | Context |
|-------------|-------|-----------|---------|
| Moonshot | Kimi K2.5 | `moonshotai/Kimi-K2.5` | 262,144 |
| Meta | Llama 4 Maverick | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` | 524,288 |
| Qwen | Qwen3-VL-8B | `Qwen/Qwen3-VL-8B-Instruct` | 262,100 |

## Moderation Models

| Model | API String | Context |
|-------|-----------|---------|
| Llama Guard 4 (12B) | `meta-llama/Llama-Guard-4-12B` | 1,048,576 |
| Virtue Guard | `VirtueAI/VirtueGuard-Text-Lite` | 32,768 |

## Quantization Types
- **FP16/BF16:** Full precision
- **FP8:** 8-bit floating point (Turbo models)
- **FP4/MXFP4:** 4-bit floating point
- **INT4:** 4-bit integer (Lite models)
