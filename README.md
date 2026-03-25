# Together AI Skills for Coding Agents

A collection of 12 agent skills that provide comprehensive knowledge of the [Together AI](https://together.ai) platform — inference, training, embeddings, audio, video, images, function calling, and infrastructure.

Each skill teaches AI coding agents how to use a specific Together AI product, including API patterns, SDK usage (Python and TypeScript), CLI commands, direct API usage, model selection, and best practices. Skills include runnable Python scripts (using the **Together Python v2 SDK**), TypeScript examples, and CLI/API workflow guidance.

Compatible with **Claude Code**, **Cursor**, **Codex**, and **Gemini CLI**.

## What Are Skills?

[Skills](https://agentskills.io/specification) are markdown instruction files that give AI coding agents domain-specific knowledge. When an agent detects that a skill is relevant to your task, it loads the skill's instructions and uses them to write better code.

Each skill contains:

- **`SKILL.md`** — Lean routing guidance for the agent: when to use the skill, when to hand off, and where to look next
- **`references/`** — Detailed reference docs (model lists, API parameters, CLI commands)
- **`scripts/`** — Runnable Python scripts demonstrating complete workflows
- **`agents/openai.yaml`** — Optional UI metadata for OpenAI/Codex surfaces

## Skills Overview

<!-- BEGIN_SKILLS_TABLE -->
| Skill | Description | Scripts |
|-------|-------------|---------|
| **together-chat-completions** | Use this skill for Together AI serverless chat inference: real-time or streaming chat apps, multi-turn conversations,... | `async_parallel.py`, `chat_basic.py`, `debug_headers.py`, `reasoning_models.py`, `structured_outputs.py`, `tool_call_loop.py` |
| **together-images** | Use this skill for Together AI image workflows: text-to-image generation, image editing with Kontext, FLUX model sele... | `generate_image.py`, `kontext_editing.py`, `lora_generation.py` |
| **together-video** | Use this skill for Together AI video workflows: text-to-video generation, image-to-video with keyframe control, model... | `generate_video.py`, `image_to_video.py` |
| **together-audio** | Use this skill for Together AI audio workflows: text-to-speech over REST, streaming, or realtime WebSocket APIs, plus... | `stt_realtime.py`, `stt_transcribe.py`, `tts_generate.py`, `tts_websocket.py` |
| **together-embeddings** | Use this skill for Together AI embedding, retrieval, and reranking workflows: generating dense vectors, building sema... | `embed_and_rerank.py`, `rag_pipeline.py` |
| **together-fine-tuning** | Use this skill for Together AI fine-tuning workflows: LoRA or full fine-tuning, DPO preference tuning, VLM training, ... | `dpo_workflow.py`, `finetune_workflow.py`, `function_calling_finetune.py`, `reasoning_finetune.py`, `vlm_finetune.py` |
| **together-batch-inference** | Use this skill for Together AI Batch API workflows: preparing JSONL inputs, uploading batch files, creating asynchron... | `batch_workflow.py` |
| **together-evaluations** | Use this skill for Together AI LLM-as-a-judge workflows: classify, score, and compare evaluations; judge model select... | `run_evaluation.py` |
| **together-code-interpreter** | Use this skill for Together AI Code Interpreter workflows: remote Python execution, session reuse, file uploads, data... | `execute_with_session.py` |
| **together-dedicated-endpoints** | Use this skill for Together AI dedicated endpoint workflows: selecting dedicated-eligible models, sizing hardware, cr... | `deploy_finetuned.py`, `manage_endpoint.py`, `upload_custom_model.py` |
| **together-dedicated-containers** | Use this skill for Together AI Dedicated Container Inference workflows: building custom Dockerized inference workers,... | `queue_client.py`, `sprocket_hello_world.py` |
| **together-gpu-clusters** | Use this skill for Together AI GPU clusters and raw infrastructure workflows: provisioning on-demand or reserved clus... | `manage_cluster.py`, `manage_storage.py` |
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
uv pip install "together>=2.0.0"
export TOGETHER_API_KEY=your_key

# Run any script directly
python skills/together-images/scripts/generate_image.py
python skills/together-audio/scripts/tts_generate.py
python skills/together-batch-inference/scripts/batch_workflow.py
```

Scripts use the **Together Python v2 SDK** (`together>=2.0.0`) with keyword-only arguments, updated method names, and current response shapes.

## Skill Structure

```
togetherai-skills/
├── quality/
│   └── trigger-evals/         # Skill trigger test sets
├── scripts/                   # Repo tooling, generators, validators
└── skills/
    └── together-<product>/
        ├── SKILL.md           # Core instructions (always loaded on trigger)
        ├── agents/
        │   └── openai.yaml    # OpenAI/Codex interface metadata
        ├── references/        # Detailed docs (loaded when needed)
        │   ├── models.md      # Supported models, IDs, context lengths
        │   ├── api-reference.md
        │   └── ...
        └── scripts/           # Runnable Python examples (v2 SDK)
            └── <workflow>.py
```

### How skills are loaded

1. **Metadata** (YAML frontmatter) — Always available to the agent (~100 words). Used to decide whether to load the skill.
2. **Body** (Markdown) — Loaded when the skill is triggered. It should stay lean and focus on routing, high-signal rules, and the next resource to open.
3. **References** — Loaded on demand when the agent needs deeper detail (model lists, full API specs).
4. **Scripts** — Available as runnable code that the agent can reference or execute directly.
5. **OpenAI metadata** — `agents/openai.yaml` gives OpenAI/Codex surfaces a display name, short description, and default prompt.

## Quality Guardrails

This repo now treats skills as agent artifacts rather than long tutorials:

- `SKILL.md` files are intentionally short and routing-oriented
- Long references include a `## Contents` section near the top
- Each skill has trigger eval examples in `quality/trigger-evals/`
- Multi-step Python workflows are validated for current v2 SDK usage and safer tempfile handling

## SDK Compatibility

> **Version bump:** This repo now requires `together>=2.0.0`. If you are upgrading from v1, see the [migration guide](https://docs.together.ai/docs/v2-migration-guide) for breaking changes in method names, argument styles, and response shapes.

All code examples and scripts target the **Together Python v2 SDK** (`together>=2.0.0`), which uses:

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
- `uv pip install "together>=2.0.0"` (v2 SDK)

## License

MIT
