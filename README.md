# Together AI Skills for Coding Agents

A single agent skill providing comprehensive knowledge of the [Together AI](https://together.ai) platform — inference, training, embeddings, audio, video, images, function calling, and infrastructure.

It uses **progressive disclosure**: one always-loaded description, a compact router, then one of 14 domain guides, then deep references and runnable scripts. Only the parts relevant to your task ever enter the agent's context.

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
| Domain guide | What it covers | Scripts |
|--------------|----------------|---------|
| **audio.md** | Text-to-speech (REST, streaming, realtime WebSocket) and speech-to-text (transcription, translation, diarization, tim... | `stt_realtime.py`, `stt_transcribe.py`, `stt_transcribe.ts`, `tts_generate.py`, `tts_generate.ts`, `tts_websocket.py` |
| **batch-inference.md** | Asynchronous bulk inference over a JSONL file, up to 50% cheaper than real-time, completing within a 24-hour window (... | `batch_workflow.py`, `batch_workflow.ts` |
| **chat-completions.md** | Serverless, OpenAI-compatible text generation: one call, billed per token. | `async_parallel.py`, `chat_basic.py`, `chat_basic.ts`, `debug_headers.py`, `debug_headers.ts`, `reasoning_models.py`, `reasoning_models.ts`, `structured_outputs.py`, `structured_outputs.ts`, `tool_call_loop.py`, `tool_call_loop.ts` |
| **dedicated-containers.md** | Run your own Docker image as an inference worker on Together GPUs: Sprocket handles the request lifecycle, Jig builds... | `queue_client.py`, `queue_client.ts`, `sprocket_hello_world.py` |
| **dedicated-model-inference.md** | Dedicated model inference (DMI) serves a model on reserved single-tenant GPUs. | `deploy_model.py`, `upload_custom_model.py` |
| **embeddings.md** | Dense vectors for semantic search and RAG retrieval, plus reranking as a second-stage precision step. | `embed_and_rerank.py`, `embed_and_rerank.ts`, `rag_pipeline.py`, `semantic_search.py` |
| **evaluations.md** | Managed LLM-as-a-judge jobs: **classify** outputs into labels, **score** them on a scale, or **compare** two responses. | `run_evaluation.py`, `run_evaluation.ts` |
| **fine-tuning.md** | Adapt a model on your data: LoRA (default), full fine-tuning, DPO preference tuning, VLM, function-calling, and reaso... | `dpo_workflow.py`, `finetune_workflow.py`, `function_calling_finetune.py`, `reasoning_finetune.py`, `vlm_finetune.py` |
| **gpu-clusters.md** | On-demand or reserved H100, H200, and B200 clusters with Kubernetes or Slurm, shared storage, and credentials, for di... | `manage_cluster.py`, `manage_cluster.ts`, `manage_storage.py` |
| **images.md** | Text-to-image generation and image editing, billed per image (FLUX models also scale with megapixels and steps). | `generate_image.py`, `generate_image.ts`, `kontext_editing.py`, `lora_generation.py` |
| **kueue.md** | Kueue is a Kubernetes-native job queueing controller. | — |
| **sandboxes.md** | Managed remote Python execution with stateful sessions, for running agent-written code, data analysis, and charts. | `execute_with_session.py`, `execute_with_session.ts` |
| **video.md** | Text-to-video and image-to-video, billed per video. | `generate_video.py`, `generate_video.ts`, `image_to_video.py` |
| **volcano.md** | Volcano is a Kubernetes-native batch scheduler. | — |
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
cp -r skills/together-* your-project/.claude/skills/
# Global availability
cp -r skills/together-* ~/.claude/skills/
```

Marketplace plugin coming soon.

### Cursor

```bash
cp -r skills/together-* your-project/.cursor/skills/
```

Cursor plugin marketplace listing coming soon.

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

The agent routes to the `chat-completions` domain guide for the complete tool call loop pattern, including parallel tool calls and tool_choice options.

**Image generation** — Ask for image workflows:

```
> Generate a FLUX image with Together AI and save it locally as PNG
```

The agent routes to the `images` domain guide to write code with the correct model ID, base64 decoding, and file saving.

**Fine-tuning** — Ask to fine-tune a model:

```
> Fine-tune Llama 3.1 8B on my dataset using Together AI with LoRA
```

The agent routes to the `fine-tuning` domain guide for data format requirements, training parameters, monitoring, and deployment.

### Using the scripts

Each script is a standalone, runnable example. They require the Together Python SDK and an API key:

```bash
uv pip install "together>=2.0.0"
export TOGETHER_API_KEY=your_key

# Run any script directly
python skills/together-ai/scripts/images/generate_image.py
python skills/together-ai/scripts/audio/tts_generate.py
python skills/together-ai/scripts/batch-inference/batch_workflow.py
```

Scripts are grouped by product area under `skills/together-ai/scripts/AREA/`. Python scripts use the **Together Python v2 SDK** (`together>=2.0.0`) with keyword-only arguments, updated method names, and current response shapes; several areas also ship TypeScript equivalents.

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
