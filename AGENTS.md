# AGENTS.md

This repository contains a single agent skill, `together-ai`, covering the whole Together AI
platform. It follows the [Agent Skills specification](https://agentskills.io/specification) and is
organised around **progressive disclosure**: triggering the skill costs a small, constant amount of
context no matter how many product areas it covers.

## Architecture

Four levels. Each is opened only when the level above it says to.

| Level | What | Loaded when |
|-------|------|-------------|
| 1 | `SKILL.md` frontmatter `description` | always in context |
| 2 | `SKILL.md` body — the **router** | the skill triggers |
| 3 | `domains/AREA.md` — one guide per product area | the router points there |
| 4 | `references/AREA/*.md`, `scripts/AREA/*` | a domain guide points there |

Every level is sized so an agent can decide what to load next without loading it first. The router
is small (about 70 lines) because every task pays for it: it holds setup, a one-line-per-area guide
table, and the rules that apply everywhere, and nothing product-specific. Each guide covers its
common path on its own and ends with an `## Open next` menu stating every file's size, contents,
and when to open it, so agents skip files they do not need.

This shape comes from a measured regression. An earlier router was about 14k characters and told
agents to read guides "fully" and to prefer scripts over memory; across 13 evaluated tasks, runs
loaded 57% more skill content than with the separate per-product skills, at the same pass rate.
Keep the router lean and the menus precise.

## Domain registry

There are 14 domain guides under `skills/together-ai/domains/`:

<domains>
- **audio.md** (Audio): Text-to-speech (REST, streaming, realtime WebSocket) and speech-to-text (transcription, translation, diarization, timestamps, realtime).
- **batch-inference.md** (Batch Inference): Asynchronous bulk inference over a JSONL file, up to 50% cheaper than real-time, completing within a 24-hour window (small batches usually finish in minutes).
- **chat-completions.md** (Chat Completions): Serverless, OpenAI-compatible text generation: one call, billed per token.
- **dedicated-containers.md** (Dedicated Containers): Run your own Docker image as an inference worker on Together GPUs: Sprocket handles the request lifecycle, Jig builds and deploys, and clients submit async jobs to a queue.
- **dedicated-model-inference.md** (Dedicated Model Inference): Dedicated model inference (DMI) serves a model on reserved single-tenant GPUs.
- **embeddings.md** (Embeddings and Reranking): Dense vectors for semantic search and RAG retrieval, plus reranking as a second-stage precision step.
- **evaluations.md** (Evaluations): Managed LLM-as-a-judge jobs: **classify** outputs into labels, **score** them on a scale, or **compare** two responses.
- **fine-tuning.md** (Fine-Tuning): Adapt a model on your data: LoRA (default), full fine-tuning, DPO preference tuning, VLM, function-calling, and reasoning tuning, plus bring-your-own-model uploads.
- **gpu-clusters.md** (GPU Clusters): On-demand or reserved H100, H200, and B200 clusters with Kubernetes or Slurm, shared storage, and credentials, for distributed training, multi-node inference, and HPC.
- **images.md** (Images): Text-to-image generation and image editing, billed per image (FLUX models also scale with megapixels and steps).
- **kueue.md** (Kueue on Together GPU clusters): Kueue is a Kubernetes-native job queueing controller.
- **sandboxes.md** (Sandboxes): Managed remote Python execution with stateful sessions, for running agent-written code, data analysis, and charts.
- **video.md** (Video): Text-to-video and image-to-video, billed per video.
- **volcano.md** (Volcano on Together GPU clusters): Volcano is a Kubernetes-native batch scheduler.

</domains>

## Skill registry

<skills>
- **together-ai**: Together AI platform skill covering every product area: chat completions and streaming text generation, tool calling, structured outputs, reasoning and vision models; image generation and editing with FLUX and Kontext; video generation; text-to-speech and speech-to-text; embeddings, reranking, and RAG retrieval; fine-tuning (LoRA, full, DPO, VLM, BYOM); batch inference; LLM-as-a-judge evaluations; code sandboxes; dedicated model inference (tg beta endpoints, deployments, autoscaling, traffic splits, custom model and LoRA uploads); dedicated containers (Sprocket, Jig, queue jobs); GPU clusters (H100, H200, B200, Kubernetes, Slurm); and Kueue quota queueing or Volcano gang scheduling on those clusters. Reach for it whenever the user builds, debugs, deploys, trains, evaluates, or operates anything on Together AI, or mentions the together SDK, the tg or together CLI, api.together.ai, TOGETHER_API_KEY, or a Together-hosted model id. The skill body routes each request to the matching domain guide.

</skills>

## Project structure

```
togetherai-skills/
├── AGENTS.md                     # This file — generated, do not hand-edit
├── README.md                     # Human-facing docs
├── LICENSE                       # MIT
├── quality/
│   ├── trigger-evals/            # Does the skill fire at all?
│   └── routing-evals/            # Does it open the RIGHT domain guide?
├── scripts/                      # Repo tooling and generators
└── skills/
    └── together-ai/
        ├── SKILL.md              # Level 2 — the router
        ├── agents/
        │   └── openai.yaml       # UI metadata for OpenAI/Codex surfaces
        ├── domains/              # Level 3 — one guide per product area
        │   ├── chat-completions.md
        │   ├── images.md
        │   └── ...
        ├── references/           # Level 4 — deep docs, one subdir per area
        │   └── AREA/
        │       ├── models.md
        │       └── api-reference.md
        └── scripts/              # Level 4 — runnable examples, one subdir per area
            └── AREA/
                └── workflow.py
```

### Path convention

Every path written inside the skill — in `SKILL.md` and in every `domains/*.md` — is relative to
the **skill root** (`skills/together-ai/`), not to the file containing the link. So a domain guide
links to `references/images/models.md`, never `../references/images/models.md`.
`scripts/quick_validate.py` enforces this for both `SKILL.md` and every domain guide.

## Working with skills

### SKILL.md format

Every skill must have a `SKILL.md` with YAML frontmatter and a Markdown body:

```yaml
---
name: together-ai
description: "One-line description, no angle brackets, max 1024 chars"
---
```

Required frontmatter fields: `name`, `description`.
Optional frontmatter fields: `license`, `allowed-tools`, `metadata`, `compatibility`.

Rules:
- `name` must be kebab-case, max 64 characters
- `description` must NOT contain angle brackets (`<` or `>`)
- The router body stays lean; target under 500 lines. Product detail belongs in
  `domains/`, and deep detail in `references/`

### agents/openai.yaml

The skill includes `agents/openai.yaml` with:
- `display_name`
- `short_description`
- `default_prompt`

The default prompt must explicitly mention the skill as `$together-ai`.

### Domain guides

`domains/AREA.md` is where a product area is actually documented. Each guide follows the same shape:
a lead paragraph (what it is, how it bills, one `Hand-offs:` line to sibling guides), `## Workflow`
(or `## Essentials` with a minimal call), `## Rules`, `## Open next`, and `## Docs`.

`## Open next` is a table with columns `File | Lines | Contains | Open when`. Describe what is
inside each file concretely enough that an agent can tell whether it needs it, and list long
references by the sections they contain. `quality_check.py` warns when a stated line count drifts
more than 25% from the file, so rerun it after editing a script or reference.

The two Kubernetes guides (`kueue.md`, `volcano.md`) are self-contained cookbooks with inline YAML
and no reference or script files. That is intentional — do not force them into the table shape.

### References

Markdown files in `references/AREA/` are loaded on demand when the agent needs deeper detail. Use these for model lists, full API specs, CLI command references, and data format documentation.

For reference files over ~100 lines, include a short `## Contents` section near the top so agents can route quickly.

### Scripts

Files in `scripts/AREA/` are runnable examples demonstrating complete workflows. Python scripts use the **Together Python v2 SDK** (`together>=2.0.0`); several areas also ship TypeScript (`.ts`) equivalents using the `together-ai` npm package.

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
- Keep overlapping domain guides explicit about hand-off boundaries, via
  `## Do not use this guide for`
- Maintain trigger eval sets in `quality/trigger-evals/` and routing eval sets in
  `quality/routing-evals/`

### Markdown style

- Use ATX headings (`##` not underlines)
- Code blocks must specify language (```python, ```bash, ```json)
- Use tables for parameter lists and model comparisons
- Keep lines under 120 characters where practical
- No emojis in SKILL.md files

## Validation

Before committing changes, validate each modified skill:

```bash
python scripts/quick_validate.py skills/together-ai
```

The validator checks:
- YAML frontmatter exists and parses correctly
- `name` is present, kebab-case, max 64 chars
- `description` is present, no angle brackets, max 1024 chars
- No disallowed frontmatter keys
- Referenced files in `references/`, `scripts/`, and `domains/` exist — checked in
  `SKILL.md` and in every `domains/*.md`

And `python scripts/quality_check.py` warns on:
- oversized `SKILL.md` files
- long references without a TOC
- missing `agents/openai.yaml`
- generic `scripts/` links
- unsafe tempfile usage in Python scripts
- missing trigger eval sets
- `Open next` line counts that drift more than 25% from the file

## Adding a new product area

Do **not** create a second skill directory. Add a domain guide instead:

1. Create `skills/together-ai/domains/AREA.md` following the standard guide shape
2. Add `skills/together-ai/references/AREA/` for detailed specs (model tables, API params)
3. Add `skills/together-ai/scripts/AREA/` with runnable v2 SDK examples for multi-step workflows
4. Add a one-line row to the **Guides** table in `SKILL.md`; name the literal symbols, commands, or
   ID prefixes users will mention — they route more reliably than topic words
5. If the new area is easily confused with an existing one, add a clause to the **Close calls**
   paragraph under the table
6. Add cases to `quality/routing-evals/together-ai.json`
7. Validate with `python scripts/quick_validate.py skills/together-ai`
8. Run `./scripts/publish.sh` to regenerate AGENTS.md and README.md

`.claude-plugin/marketplace.json` needs no per-area entry — skills are auto-discovered from the
repo, and it has never enumerated them.

## Modifying the skill

- Read the router (`SKILL.md`) and the relevant domain guide before making changes
- Keep inline examples minimal — move detailed content to `references/AREA/`
- If updating SDK code, ensure it follows v2 patterns (see table above)
- If a model is deprecated, remove it from the model tables in `references/AREA/`
- Test any script changes by reviewing the code (scripts require a Together API key to actually run)

## Common tasks

### Update a model list

Model tables live in `skills/together-ai/references/AREA/models.md` (or similar). Update the table rows. Do not change the table structure unless adding a new column that all rows need.

### Add a new script

1. Create `skills/together-ai/scripts/AREA/descriptive_name.py`
2. Follow the script conventions above (docstring, `__main__`, type hints)
3. Link it from the `## Open next` section of `domains/AREA.md`, using a skill-root-relative path:
   ```
   - Start with [scripts/AREA/name.py](scripts/AREA/name.py)
   ```

### Fix an API pattern

If a Together API changes, update in this order:
1. The relevant `domains/AREA.md` guide
2. The `references/AREA/` docs
3. The `scripts/AREA/` files
4. `SKILL.md` if a universal rule or the v2 SDK table changed
5. `scripts/AGENTS_TEMPLATE.md` if the v2 SDK patterns table needs updating (never hand-edit
   `AGENTS.md`; it is generated)

## Do not

- Add `README.md`, `CHANGELOG.md`, or `INSTALLATION_GUIDE.md` inside the skill directory — the Agent Skills spec forbids extraneous docs within skills
- Create a second `skills/together-*` directory — new product areas are domain guides, not skills
- Write `../references/...` inside a domain guide — all skill paths are skill-root-relative
- Grow the router with product detail; every task pays for every line of it. Put product detail in
  the guide and deep detail in references
- Hardcode a model ID as available without checking the live catalog; IDs in guides, references,
  and scripts are examples, and the scripts' defaults should be on the current serverless list
- Use angle brackets in any `description` frontmatter field
- Use v1 SDK method names in any code
- Add dependencies beyond `together` to scripts without noting it in the docstring
- Create empty `references/`, `scripts/`, or `domains/` directories — only include if they contain files
