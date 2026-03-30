# AGENTS.md

This repository contains 12 agent skills for the Together AI platform. Each skill is a self-contained directory following the [Agent Skills specification](https://agentskills.io/specification).

## Skill registry

<skills>
- **together-chat-completions**: Real-time and streaming text generation via Together AI's OpenAI-compatible chat/completions API, including multi-turn conversations, tool and function calling, structured JSON outputs, and reasoning models. Reach for it whenever the user wants to build or debug text generation on Together AI, unless they specifically need batch jobs, embeddings, fine-tuning, dedicated endpoints, dedicated containers, or GPU clusters.
- **together-images**: Text-to-image generation and image editing via Together AI, including FLUX and Kontext models, LoRA-based styling, reference-image guidance, and local image downloads. Reach for it whenever the user wants to generate or edit images on Together AI rather than create videos or build text-only chat applications.
- **together-video**: Text-to-video and image-to-video generation via Together AI, including keyframe control, model and dimension selection, asynchronous job polling, and video downloads. Reach for it whenever the user wants motion generation on Together AI rather than still-image generation or text-only inference.
- **together-audio**: Text-to-speech and speech-to-text via Together AI, including REST, streaming, and realtime WebSocket TTS, plus transcription, translation, diarization, timestamps, and live STT. Reach for it whenever the user needs audio in or audio out on Together AI rather than chat generation, image or video creation, or model training.
- **together-embeddings**: Dense vector embeddings, semantic search, RAG pipelines, and reranking via Together AI. Generate embeddings with open-source models and rerank results behind dedicated endpoints. Reach for it whenever the user needs vector representations or retrieval quality improvements rather than direct text generation.
- **together-fine-tuning**: LoRA, full fine-tuning, DPO preference tuning, VLM training, function-calling tuning, reasoning tuning, and BYOM uploads on Together AI. Reach for it whenever the user wants to adapt a model on custom data rather than only run inference, evaluate outputs, or host an existing model.
- **together-batch-inference**: High-volume, asynchronous offline inference at up to 50% lower cost via Together AI's Batch API. Prepare JSONL inputs, upload files, create jobs, poll status, and download outputs. Reach for it whenever the user needs non-interactive bulk inference rather than real-time chat or evaluation jobs.
- **together-evaluations**: LLM-as-a-judge evaluation framework on Together AI. Classify, score, and compare model outputs, select judge models, use external-provider judges or targets, poll results and download reports. Reach for it whenever the user wants to benchmark outputs, grade responses, compare A/B variants, or operationalize automated evaluations.
- **together-sandboxes**: Remote Python execution in managed sandboxes on Together AI with stateful sessions, file uploads, data analysis, chart generation, and notebook-like runs via the Sandboxes API. Reach for it whenever the user wants managed remote Python execution instead of local execution, raw clusters, or full model hosting.
- **together-dedicated-endpoints**: Single-tenant GPU endpoints on Together AI with autoscaling and no rate limits. Deploy fine-tuned or uploaded models, size hardware, and manage endpoint lifecycle. Reach for it whenever the user needs predictable always-on hosting rather than serverless inference, custom containers, or raw clusters.
- **together-dedicated-containers**: Custom Dockerized inference workers on Together AI's managed GPU infrastructure. Build with Sprocket SDK, configure with Jig CLI, submit async queue jobs, and poll results. Reach for it whenever the user needs container-level control rather than a standard model endpoint or raw cluster.
- **together-gpu-clusters**: On-demand and reserved GPU clusters (H100, H200, B200) on Together AI with Kubernetes or Slurm orchestration, shared storage, credential management, and cluster scaling for ML and HPC jobs. Reach for it when the user needs multi-node compute or infrastructure control rather than a managed model endpoint.

</skills>

## Project structure

```
togetherai-skills/
├── AGENTS.md                     # This file — agent instructions
├── README.md                     # Human-facing docs
├── LICENSE                       # MIT
├── quality/
│   └── trigger-evals/            # Skill trigger eval sets
├── scripts/                      # Repo tooling and generators
└── skills/
    └── together-<product>/       # One directory per skill
        ├── SKILL.md              # Required — frontmatter + instructions
        ├── agents/
        │   └── openai.yaml       # Optional — UI metadata for OpenAI/Codex surfaces
        ├── references/           # Optional — detailed reference docs
        │   ├── models.md
        │   ├── api-reference.md
        │   └── ...
        └── scripts/              # Optional — runnable Python examples
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
- Body should stay lean; target under 500 lines and move deep detail into `references/`

### agents/openai.yaml

Every skill in this repo includes `agents/openai.yaml` with:
- `display_name`
- `short_description`
- `default_prompt`

The default prompt must explicitly mention the skill as `$skill-name`.

### References

Markdown files in `references/` are loaded on demand when the agent needs deeper detail. Use these for model lists, full API specs, CLI command references, and data format documentation.

For reference files over ~100 lines, include a short `## Contents` section near the top so agents can route quickly.

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
- Prefer reusable CLIs over hard-coded one-off demos for multi-step or billable workflows
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

### Quality expectations

- Frontmatter descriptions should route by user intent, not read like marketing copy
- `SKILL.md` should tell the agent when to open a specific reference or run a specific script
- Avoid generic folder links such as `See [scripts/](scripts/)`; link to the exact script
- Keep overlapping skills explicit about hand-off boundaries
- Maintain trigger eval sets in `quality/trigger-evals/`

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

And `python scripts/quality_check.py` warns on:
- oversized `SKILL.md` files
- long references without a TOC
- missing `agents/openai.yaml`
- generic `scripts/` links
- unsafe tempfile usage in Python scripts
- missing trigger eval sets

## Adding a new skill

1. Create `skills/together-<product>/SKILL.md` with frontmatter and body
2. Add `references/` files for detailed specs (model tables, API params)
3. Add `scripts/` with runnable Python v2 SDK examples if the skill involves multi-step workflows
4. Create `agents/openai.yaml` with `display_name`, `short_description`, and `default_prompt`
5. Validate with `python scripts/quick_validate.py skills/together-<product>`
6. Run `./scripts/publish.sh` to regenerate AGENTS.md and README.md
7. Update `.claude-plugin/marketplace.json` with the new skill entry

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
