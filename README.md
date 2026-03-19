# Together AI Skills for Coding Agents

A collection of 12 agent skills that provide comprehensive knowledge of the [Together AI](https://together.ai) platform — inference, training, embeddings, audio, video, images, function calling, and infrastructure.

Each skill teaches AI coding agents how to use a specific Together AI product, including API patterns, SDK usage (Python and TypeScript), CLI commands, direct API usage, model selection, and best practices. Skills include runnable Python scripts (using the **Together Python v2 SDK**), TypeScript examples, and CLI/API workflow guidance.

Compatible with **Claude Code**, **Cursor**, **Codex**, and **Gemini CLI**.

## What Are Skills?

[Skills](https://agentskills.io/specification) are markdown instruction files that give AI coding agents domain-specific knowledge. When an agent detects that a skill is relevant to your task, it loads the skill's instructions and uses them to write better code.

Each skill contains:

- **`SKILL.md`** — Core instructions with API patterns, code examples, and best practices
- **`references/`** — Detailed reference docs (model lists, API parameters, CLI commands)
- **`scripts/`** — Runnable Python scripts demonstrating complete workflows

## Skills Overview

<!-- BEGIN_SKILLS_TABLE -->
| Skill | Description | Scripts |
|-------|-------------|---------|
| **together-chat-completions** | Serverless chat completion inference via Together AI's OpenAI-compatible API. | `async_parallel.py`, `chat_basic.py`, `reasoning_models.py`, `structured_outputs.py`, `tool_call_loop.py` |
| **together-images** | Generate and edit images via Together AI's image generation API. | `generate_image.py`, `kontext_editing.py`, `lora_generation.py` |
| **together-video** | Generate videos from text and image prompts via Together AI. | `generate_video.py`, `image_to_video.py` |
| **together-audio** | Text-to-speech (TTS) and speech-to-text (STT) via Together AI. | `stt_transcribe.py`, `tts_generate.py` |
| **together-embeddings** | Generate text embeddings via Together AI using the Multilingual E5 model with 1024-dimension vectors. | `embed_and_rerank.py`, `rag_pipeline.py` |
| **together-fine-tuning** | Fine-tune open-source LLMs on Together AI with LoRA, Full fine-tuning, DPO preference tuning, VLM (vision-language) f... | `dpo_workflow.py`, `finetune_workflow.py`, `function_calling_finetune.py`, `reasoning_finetune.py`, `vlm_finetune.py` |
| **together-batch-inference** | Process large volumes of inference requests asynchronously at up to 50% lower cost via Together AI's Batch API. | `batch_workflow.py` |
| **together-evaluations** | Evaluate LLM outputs using Together AI's LLM-as-a-Judge framework with Classify, Score, and Compare evaluation types. | `run_evaluation.py` |
| **together-code-interpreter** | Execute Python code in a sandboxed environment via Together Code Interpreter (TCI). | `execute_with_session.py` |
| **together-dedicated-endpoints** | Deploy models on dedicated single-tenant GPU endpoints via Together AI for predictable performance, no rate limits, a... | `deploy_finetuned.py`, `manage_endpoint.py`, `upload_custom_model.py` |
| **together-dedicated-containers** | Deploy custom Dockerized inference workloads on Together AI's managed GPU infrastructure using Dedicated Container In... | `queue_client.py`, `sprocket_hello_world.py` |
| **together-gpu-clusters** | Provision on-demand and reserved GPU clusters (Instant Clusters) on Together AI with H100, H200, B200, L40, and RTX-6... | `manage_cluster.py`, `manage_storage.py` |
<!-- END_SKILLS_TABLE -->

## Installation

### Quick Install (Any Agent)

Install all skills at once using [skills.sh](https://skills.sh/):

```bash
npx skills add togethercomputer/skills
```

This works with Claude Code, Cursor, Codex, and other agents that support the [Agent Skills](https://agentskills.io/specification) specification.

### Claude Code

```bash
# Plugin marketplace
/plugin marketplace add togethercomputer/skills

# Or install individual skills
/plugin install together-chat-completions@togethercomputer/skills

# Or copy manually
cp -r skills/together-* your-project/.claude/skills/
# Global availability
cp -r skills/together-* ~/.claude/skills/
```

### Cursor

Install via the Cursor plugin flow using the `.cursor-plugin/` manifests included in this repository.

### Codex

```bash
cp -r skills/together-* your-project/.agents/skills/
```

### Gemini CLI

```bash
gemini extensions install https://github.com/togethercomputer/skills.git --consent
```

### Verify installation

```bash
# Claude Code
ls your-project/.claude/skills/together-*/SKILL.md
# Codex
ls your-project/.agents/skills/together-*/SKILL.md
```

You should see one `SKILL.md` per installed skill.

## Usage

Once installed, skills activate automatically when the agent detects a relevant task. No explicit invocation is needed.

### Examples

**Chat completions** — Ask the agent to build a chat app:

```
> Build a multi-turn chatbot using Together AI with Llama 3.3 70B
```

The agent will use the `together-chat-completions` skill to generate correct v2 SDK code with proper model IDs, parameters, and streaming patterns.

**Function calling** — Ask for tool-using agents:

```
> Create an agent that can check weather and stock prices using Together AI function calling
```

The agent will reference `together-chat-completions` for the complete tool call loop pattern, including parallel tool calls and tool_choice options.

**Image generation** — Ask for image workflows:

```
> Generate a FLUX image with Together AI and save it locally as PNG
```

The agent will use `together-images` to write code with the correct model ID, base64 decoding, and file saving.

**Fine-tuning** — Ask to fine-tune a model:

```
> Fine-tune Llama 3.1 8B on my dataset using Together AI with LoRA
```

The agent will reference `together-fine-tuning` for data format requirements, training parameters, monitoring, and deployment.

### Using the scripts

Each script is a standalone, runnable example. They require the Together Python SDK and an API key:

```bash
pip install together
export TOGETHER_API_KEY=your_key

# Run any script directly
python together-skills/together-images/scripts/generate_image.py
python together-skills/together-audio/scripts/tts_generate.py
python together-skills/together-batch-inference/scripts/batch_workflow.py
```

Scripts use the **Together Python v2 SDK** (`together>=1.0.0`) with keyword-only arguments, updated method names, and current response shapes.

## Skill Structure

```
together-<product>/
├── SKILL.md              # Core instructions (always loaded on trigger)
├── references/           # Detailed docs (loaded when needed)
│   ├── models.md         # Supported models, IDs, context lengths
│   ├── api-reference.md  # Full API parameters and response shapes
│   └── ...
└── scripts/              # Runnable Python examples (v2 SDK)
    └── <workflow>.py     # Complete end-to-end workflow
```

### How skills are loaded

1. **Metadata** (YAML frontmatter) — Always available to the agent (~100 words). Used to decide whether to load the skill.
2. **Body** (Markdown) — Loaded when the skill is triggered. Contains API patterns, code examples, and best practices.
3. **References** — Loaded on demand when the agent needs deeper detail (model lists, full API specs).
4. **Scripts** — Available as runnable code that the agent can reference or execute directly.

## SDK Compatibility

All code examples and scripts target the **Together Python v2 SDK** (`together>=1.0.0`), which uses:

- Keyword-only arguments (not positional)
- `client.batches.create()` / `client.batches.retrieve()` (not `create_batch()` / `get_batch()`)
- `client.endpoints.retrieve()` (not `get()`)
- `client.code_interpreter.execute()` (not `run()`)
- `client.evals.create()` (not `client.evaluation.create()`)
- File objects via context managers (`with open(..., "rb") as f:`)
- Typed parameter classes for evaluations

If you're using the v1 SDK, see the [migration guide](https://docs.together.ai/docs/v2-migration-guide).

## Requirements

- A supported AI coding agent: [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Cursor](https://www.cursor.com), [Codex](https://openai.com/index/introducing-codex/), or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [Together AI API key](https://api.together.ai/settings/api-keys)
- Python 3.10+ (for scripts)
- `pip install together` (v2 SDK, `>=1.0.0`)

## License

MIT
