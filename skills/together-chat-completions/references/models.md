# Chat Model Catalog

## Recommended Models by Use Case

| Use Case | Model | API String | Alternatives |
|----------|-------|-----------|-------------|
| Chat (best) | Kimi K2.6 | `moonshotai/Kimi-K2.6` | `MiniMaxAI/MiniMax-M2.7`, `openai/gpt-oss-120b` |
| Reasoning | DeepSeek-V4-Pro | `deepseek-ai/DeepSeek-V4-Pro` | `moonshotai/Kimi-K2.6`, `Qwen/Qwen3.6-Plus` |
| Coding Agents | GLM-5.1 | `zai-org/GLM-5.1` | `moonshotai/Kimi-K2.6`, `deepseek-ai/DeepSeek-V4-Pro`, `MiniMaxAI/MiniMax-M2.7` |
| Small & Fast | GPT-OSS 20B | `openai/gpt-oss-20b` | `Qwen/Qwen2.5-7B-Instruct-Turbo`, `google/gemma-3n-E4B-it` |
| Medium General | GPT-OSS 120B | `openai/gpt-oss-120b` | `zai-org/GLM-5` |
| Function Calling | GLM-5.1 | `zai-org/GLM-5.1` | `moonshotai/Kimi-K2.6`, `MiniMaxAI/MiniMax-M2.7` |
| Vision | Qwen3.5 397B | `Qwen/Qwen3.5-397B-A17B` | `Qwen/Qwen3.5-9B`, `google/gemma-4-31B-it` |

## Full Chat Model Catalog

| Organization | Model | API String | Context | Quant |
|-------------|-------|-----------|---------|-------|
| MiniMax | MiniMax M2.7 | `MiniMaxAI/MiniMax-M2.7` | 202,752 | FP4 |
| Qwen | Qwen3.7 Max | `Qwen/Qwen3.7-Max` | - | - |
| Qwen | Qwen3.5 397B A17B | `Qwen/Qwen3.5-397B-A17B` | 262,144 | BF16 |
| Qwen | Qwen3.6 Plus | `Qwen/Qwen3.6-Plus` | 1,000,000 | - |
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 262,144 | FP8 |
| Qwen | Qwen3 235B Instruct | `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` | 262,144 | FP8 |
| Moonshot | Kimi K2.6 | `moonshotai/Kimi-K2.6` | 262,144 | FP4 |
| DeepSeek | DeepSeek-V4-Pro | `deepseek-ai/DeepSeek-V4-Pro` | 512,000 | FP4 |
| NVIDIA | Nemotron 3 Ultra 550B A55B | `nvidia/nemotron-3-ultra-550b-a55b` | 512,300 | NVFP4 |
| OpenAI | GPT-OSS 120B | `openai/gpt-oss-120b` | 128,000 | MXFP4 |
| OpenAI | GPT-OSS 20B | `openai/gpt-oss-20b` | 128,000 | MXFP4 |
| Z.ai | GLM-5.1 | `zai-org/GLM-5.1` | 202,752 | FP4 |
| Z.ai | GLM-5 | `zai-org/GLM-5` | 202,752 | FP4 |
| Meta | Llama 3.3 70B Turbo | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 131,072 | FP8 |
| Meta | Llama 3 8B Lite | `meta-llama/Meta-Llama-3-8B-Instruct-Lite` | 8,192 | - |
| Deep Cogito | Cogito v2.1 671B | `deepcogito/cogito-v2-1-671b` | 163,840 | - |
| Google | Gemma 4 31B IT | `google/gemma-4-31B-it` | 262,144 | FP8 |
| Google | Gemma 3N E4B | `google/gemma-3n-E4B-it` | 32,768 | FP8 |
| Liquid AI | LFM2-24B-A2B | `LiquidAI/LFM2-24B-A2B` | 32,768 | - |
| Qwen | Qwen 2.5 7B Turbo | `Qwen/Qwen2.5-7B-Instruct-Turbo` | 32,768 | FP8 |
| Essential AI | Rnj-1 Instruct | `essentialai/rnj-1-instruct` | 32,768 | BF16 |

## Vision Models

| Organization | Model | API String | Context |
|-------------|-------|-----------|---------|
| Qwen | Qwen3.5 397B A17B | `Qwen/Qwen3.5-397B-A17B` | 262,144 |
| Qwen | Qwen3.5 9B | `Qwen/Qwen3.5-9B` | 262,144 |
| Google | Gemma 4 31B IT | `google/gemma-4-31B-it` | 262,144 |

## Moderation Models

| Model | API String | Context |
|-------|-----------|---------|
| Llama Guard 4 (12B) | `meta-llama/Llama-Guard-4-12B` | 1,048,576 |

## Quantization Types
- **FP16/BF16:** Full precision
- **FP8:** 8-bit floating point (Turbo models)
- **FP4/MXFP4:** 4-bit floating point
