# AGENTS.md

This repository contains 12 agent skills for the Together AI platform. Each skill is a self-contained directory following the [Agent Skills specification](https://agentskills.io/specification).

## Skill registry

<skills>
- **together-chat-completions**: Serverless chat completion inference via Together AI's OpenAI-compatible API. Access 100+ open-source models with pay-per-token pricing. Includes function calling (tool use) with 6 calling patterns, structured outputs (JSON mode, json_schema, regex), and reasoning/thinking models (DeepSeek R1, DeepSeek V3.1, Kimi K2.5, GLM-5, GPT-OSS, Qwen3.5). Use when building chat applications, text generation, multi-turn conversations, function calling, structured JSON outputs, reasoning/chain-of-thought, thinking mode toggle, or any LLM inference task using Together AI.
- **together-images**: Generate and edit images via Together AI's image generation API. Models include FLUX.1 (schnell/dev/pro), FLUX.2, Kontext (image editing with reference images), Seedream, Stable Diffusion, and more. Use when users want to generate images from text, edit existing images, create AI art, use LoRA adapters for custom styles, or work with any image generation task.
- **together-video**: Generate videos from text and image prompts via Together AI. 15+ models including Veo 2/3, Sora 2, Kling 2.1, Hailuo 02, Seedance, PixVerse, Vidu. Supports text-to-video, image-to-video, keyframe control, and reference images. Use when users want to generate videos, create video content, animate images, or work with any video generation task.
- **together-audio**: Text-to-speech (TTS) and speech-to-text (STT) via Together AI. TTS models include Orpheus, Kokoro, Cartesia Sonic with REST, streaming, and WebSocket support. STT models include Whisper, Voxtral, and Parakeet with transcription, translation, diarization, and real-time WebSocket streaming. Use when users need voice synthesis, audio generation, speech recognition, transcription, translation, TTS, STT, or real-time voice applications.
- **together-embeddings**: Generate text embeddings and rerank documents via Together AI. Embedding models include BGE, GTE, E5, UAE families. Reranking via MixedBread reranker. Use when users need text embeddings, vector search, semantic similarity, document reranking, RAG pipeline components, or retrieval-augmented generation.
- **together-fine-tuning**: Fine-tune open-source LLMs on Together AI with LoRA, Full fine-tuning, DPO preference tuning, VLM (vision-language) fine-tuning, reasoning fine-tuning, function calling fine-tuning, and Bring Your Own Model (BYOM). Supports 100+ models including Qwen3, Llama 3/4, DeepSeek, Gemma 3, GLM, Kimi K2.5, Mistral. Use when users want to train, fine-tune, customize, adapt, or specialize language models on custom data.
- **together-batch-inference**: Process large volumes of inference requests asynchronously at up to 50% lower cost via Together AI's Batch API. Supports up to 50K requests per batch, 100MB max file size. Use when users need batch processing, offline inference, bulk data classification, synthetic data generation, or cost-optimized large-scale LLM workloads.
- **together-evaluations**: Evaluate LLM outputs using Together AI's LLM-as-a-Judge framework with Classify, Score, and Compare evaluation types. Supports Together serverless models, dedicated endpoints, and external providers (OpenAI, Anthropic, Google) as both judges and evaluation targets. Use when users want to evaluate model quality, benchmark outputs, compare models A/B, grade responses, detect harmful content, or assess LLM performance.
- **together-code-interpreter**: Execute Python code in a sandboxed environment via Together Code Interpreter (TCI). $0.03 per session, 60-minute lifespan, stateful sessions with pre-installed data science packages. Use when users need to run Python code remotely, execute computations, data analysis, generate plots, RL training environments, or agentic code execution workflows.
- **together-dedicated-endpoints**: Deploy models on dedicated single-tenant GPU endpoints via Together AI for predictable performance, no rate limits, autoscaling, and custom hardware. Supports 179+ models including fine-tuned and custom uploaded models across chat, image, audio, embedding, and moderation categories. Use when users need dedicated inference endpoints, always-on model hosting, production deployments with SLAs, custom or fine-tuned model deployment, or scaling beyond serverless limits.
- **together-dedicated-containers**: Deploy custom Dockerized inference workloads on Together AI's managed GPU infrastructure using Dedicated Container Inference (DCI). Tools include Jig CLI for building/deploying, Sprocket SDK for request handling, Queue API for async job submission, and a private container registry. Use when users need custom model serving, containerized inference, Docker-based GPU workloads, image/video generation pipelines, or workloads beyond standard model endpoints.
- **together-gpu-clusters**: Provision on-demand and reserved GPU clusters (Instant Clusters) on Together AI with H100, H200, B200, L40, and RTX-6000 hardware. Supports Kubernetes and Slurm orchestration, autoscaling, shared storage volumes, health checks, and user management. Manage via Python SDK, TypeScript SDK, tcloud CLI, Terraform, SkyPilot, or REST API. Use when users need GPU clusters, distributed training, multi-node compute, HPC workloads, or large-scale ML infrastructure.

</skills>

## Project structure

```
together-skills/
├── AGENTS.md                     # This file — agent instructions
├── README.md                     # Human-facing docs
├── LICENSE                       # MIT
└── together-<product>/           # One directory per skill
    ├── SKILL.md                  # Required — frontmatter + instructions
    ├── references/               # Optional — detailed reference docs
    │   ├── models.md
    │   ├── api-reference.md
    │   └── ...
    └── scripts/                  # Optional — runnable Python examples
        └── <workflow>.py
```

## Working with skills

### SKILL.md format

Every skill must have a `SKILL.md` with YAML frontmatter and a Markdown body:

```yaml
---
name: together-<product>
description: "One-line description, no angle brackets, max 1024 chars"
---
```

Required frontmatter fields: `name`, `description`.
Optional frontmatter fields: `license`, `allowed-tools`, `metadata`, `compatibility`.

Rules:
- `name` must be kebab-case, max 64 characters
- `description` must NOT contain angle brackets (`<` or `>`)
- Body should be under 5,000 words (progressive disclosure — put details in `references/`)

### References

Markdown files in `references/` are loaded on demand when the agent needs deeper detail. Use these for model lists, full API specs, CLI command references, and data format documentation.

### Scripts

Python files in `scripts/` are runnable examples demonstrating complete workflows. All scripts in this repo use the **Together Python v2 SDK** (`together>=2.0.0`).

## Code conventions

### Python scripts

- Target Python 3.10+
- Use `together` v2 SDK with keyword-only arguments
- Every script must have a module docstring with: description, usage command, and requirements
- Include `if __name__ == "__main__":` block with working examples
- Use type hints (`list[str]`, `str | None`)
- Initialize client at module level: `client = Together()`
- Assume `TOGETHER_API_KEY` is set as an environment variable
- No third-party dependencies beyond `together` unless absolutely necessary (note it in the docstring if so)

### v2 SDK patterns

These are the correct v2 SDK method names. Do NOT use v1 patterns:

| Operation | v2 (correct) | v1 (wrong) |
|-----------|-------------|------------|
| Create batch | `client.batches.create()` | `client.create_batch()` |
| Get batch | `client.batches.retrieve()` | `client.get_batch()` |
| Get endpoint | `client.endpoints.retrieve()` | `client.endpoints.get()` |
| Run code | `client.code_interpreter.execute()` | `client.code_interpreter.run()` |
| File content | `client.files.content()` | `client.files.retrieve_content()` |
| Evaluations | `client.evals.create()` | `client.evaluation.create()` |
| Batch input | `input_file_id=` | `file_id=` |
| Audio files | `with open(path, "rb") as f:` then pass `f` | pass file path string |
| Autoscaling | `autoscaling={"min_replicas": N, "max_replicas": M}` | `min_replicas=N, max_replicas=M` |

### Markdown style

- Use ATX headings (`##` not underlines)
- Code blocks must specify language (```python, ```bash, ```json)
- Use tables for parameter lists and model comparisons
- Keep lines under 120 characters where practical
- No emojis in SKILL.md files

## Validation

Before committing changes, validate each modified skill:

```bash
python scripts/quick_validate.py skills/together-<skill>
```

The validator checks:
- YAML frontmatter exists and parses correctly
- `name` is present, kebab-case, max 64 chars
- `description` is present, no angle brackets, max 1024 chars
- No disallowed frontmatter keys
- Referenced files in `references/` and `scripts/` exist

## Adding a new skill

1. Create `skills/together-<product>/SKILL.md` with frontmatter and body
2. Add `references/` files for detailed specs (model tables, API params)
3. Add `scripts/` with runnable Python v2 SDK examples if the skill involves multi-step workflows
4. Validate with `python scripts/quick_validate.py skills/together-<product>`
5. Run `./scripts/publish.sh` to regenerate AGENTS.md and README.md
6. Update `.claude-plugin/marketplace.json` with the new skill entry

## Modifying existing skills

- Read the full SKILL.md before making changes
- Keep inline examples minimal — move detailed content to `references/`
- If updating SDK code, ensure it follows v2 patterns (see table above)
- If a model is deprecated, remove it from the model tables in `references/`
- Test any script changes by reviewing the code (scripts require a Together API key to actually run)

## Common tasks

### Update a model list

Model tables live in `references/models.md` (or similar) within each skill. Update the table rows. Do not change the table structure unless adding a new column that all rows need.

### Add a new script

1. Create `skills/together-<skill>/scripts/<descriptive_name>.py`
2. Follow the script conventions above (docstring, `__main__`, type hints)
3. Add a reference line to the `## Resources` section of the skill's `SKILL.md`:
   ```
   - **Runnable script**: See [scripts/<name>.py](scripts/<name>.py) — short description (v2 SDK)
   ```

### Fix an API pattern

If a Together API changes, update in this order:
1. The `SKILL.md` inline examples
2. The `references/` docs
3. The `scripts/` files
4. This `AGENTS.md` if the v2 SDK patterns table needs updating

## Do not

- Add `README.md`, `CHANGELOG.md`, or `INSTALLATION_GUIDE.md` inside individual skill directories — the Agent Skills spec forbids extraneous docs within skills
- Use angle brackets in any `description` frontmatter field
- Use v1 SDK method names in any code
- Add dependencies beyond `together` to scripts without noting it in the docstring
- Create empty `references/` or `scripts/` directories — only include if they contain files
