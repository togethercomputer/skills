---
name: together-ai
description: "Together AI platform skill covering every product area: chat completions and streaming text generation, tool calling, structured outputs, reasoning and vision models; image generation and editing (FLUX, Kontext); video generation; text-to-speech and speech-to-text; embeddings and reranking; fine-tuning (LoRA, full, DPO, VLM, BYOM); batch inference; LLM-as-a-judge evaluations; code sandboxes; dedicated model inference (tg endpoints, deployments, autoscaling, traffic splits, model and LoRA uploads); dedicated containers (Sprocket, Jig); GPU clusters (Kubernetes, Slurm) with Kueue or Volcano scheduling; and TogetherLink (tlink, tclaude) for running Claude Code, Codex, OpenCode, or desktop apps on Together models. Reach for it whenever the user builds, debugs, deploys, trains, evaluates, or operates anything on Together AI, or mentions the together SDK, the tg CLI, TogetherLink, api.together.ai, TOGETHER_API_KEY, or a Together-hosted model id. The skill body routes each request to the matching domain guide."
---

# Together AI

Read the one guide below that matches the task. Each guide covers the common path by itself and
ends with an **Open next** menu saying what every reference and script contains, so you open a file
only when it holds a detail you need. Paths are relative to this skill's directory.

## Setup

- Auth: `TOGETHER_API_KEY` in the environment. Python: `uv pip install --upgrade "together>=3"`,
  then `client = Together()`. TypeScript: `npm install "together-ai@>=1"`, then `new Together()`. The
  Python SDK and this skill's scripts use only the API key. From CLI 2.41, `tg login` signs in
  through a browser device flow (`--no-browser` prints the URL) and `tg switch` picks a project;
  it is interactive, so ask the user to run it. The CLI also accepts `TOGETHER_API_KEY`.
- CLI: `uv tool install "together[cli]>=3"` gives `tg` (alias `together`), used for dedicated
  inference, clusters, and fine-tuning. If `tg endpoints deploy` is missing, the CLI predates 3.0:
  `uv tool install --force "together[cli]>=3"`. From 2.40, `tg` prints JSON by default when an AI
  agent runs it; pass `--no-json` for tables.
- **SDK 3.x only.** This skill targets Python `together` 3.x, `together-ai` 1.x, and CLI 3.x
  (2026-10-22). Code written for 2.x breaks on them: `client.beta.endpoints`, `.models`, and
  `.clusters` are now `client.endpoints` and so on, and `tg beta endpoints` is `tg endpoints` (only
  `beta jig` stays); `whoami().project_id` is `whoami().project.id`; a custom `base_url` drops its
  trailing `/v1`; video keyframes go inside `media`; and the v1 `endpoints.create(model=,
  hardware=)` and `client.code_interpreter` are gone. See the
  [v3 migration guide](https://docs.together.ai/docs/sdk-v3-migration-guide).

## Guides

| Guide | Use for |
|---|---|
| `domains/chat-completions.md` | text generation, streaming, multi-turn chat, tool calling, JSON output, reasoning and vision models |
| `domains/images.md` | text-to-image, image editing (Kontext), reference images |
| `domains/video.md` | text-to-video, image-to-video, keyframes |
| `domains/audio.md` | TTS (REST, streaming, WebSocket), transcription, translation, diarization, realtime STT |
| `domains/embeddings.md` | embeddings, semantic search, RAG retrieval, reranking (not currently offered; read before building) |
| `domains/batch-inference.md` | large offline jobs at lower cost (JSONL, `batches.create`) |
| `domains/evaluations.md` | LLM-as-a-judge: classify, score, or compare outputs |
| `domains/fine-tuning.md` | LoRA, full, DPO, VLM, function-calling, and reasoning tuning; BYOM upload |
| `domains/sandboxes.md` | running code in isolated remote sandboxes (`together-sandbox`; the old `code_interpreter` API is gone) |
| `domains/dedicated-model-inference.md` | dedicated endpoints (`tg endpoints`, `client.endpoints`): deploy, autoscale, traffic split, A/B, shadow, metrics, model/LoRA upload, v1 migration (HTTP 403 `endpoints_v1_create_access_disabled`) |
| `domains/dedicated-containers.md` | your own Docker inference worker: Sprocket, Jig, queue jobs |
| `domains/gpu-clusters.md` | H100/H200/B200 clusters, Kubernetes or Slurm, shared storage, credentials |
| `domains/kueue.md` | quota-gated job queueing on a Together Kubernetes cluster |
| `domains/volcano.md` | all-or-nothing gang scheduling on a Together Kubernetes cluster |
| `domains/togetherlink.md` | TogetherLink (`tlink`, `tclaude`): run Claude Code, Codex, OpenCode, Pi Code, Claude Desktop, or ChatGPT Desktop on Together models; install, keys, `--main` pinning, headless runs, usage |

Close calls: a still image is `images`, motion is `video`. Hosting a model is
`dedicated-model-inference`, hosting your own container image is `dedicated-containers`, raw nodes
are `gpu-clusters`. Jobs that wait for quota use `kueue`; pods that must start together use
`volcano`. Running an existing coding agent or desktop app on Together models is `togetherlink`;
calling the API from the user's own code is `chat-completions` or `images`. A task spanning areas
(chat + images + audio, or tune, deploy, evaluate) reads each guide when it reaches that step.

## Rules for every area

- **Model IDs go stale.** IDs in guides and scripts are examples, checked 2026-10-07. An error of
  `Unable to access non-serverless model`, `model_not_available`, or `endpoint_not_ready` means the
  model is not served serverless: do not retry it or try other IDs from memory. Choose from the
  [serverless catalog](https://docs.together.ai/docs/serverless/models) and check the
  [deprecations page](https://docs.together.ai/docs/deprecations) for the named replacement; a chat
  request with `max_tokens=1` confirms a model in one call. `client.models.list()` and
  `tg models public` cannot confirm serverless availability: in SDK 3.x the first lists your
  project's own models, and the second lists only a curated subset.
- **Do not retry errors that cannot succeed.** 400 non-serverless model, 401, 402
  `insufficient balance` (account-wide; another model will not help), 403, and 404 need a different
  input or a human. A 403 `third_party_data_sharing_blocked` means the organization must enable
  third-party data sharing for that partner-hosted model (for example FLUX.2 or Qwen Plus). Retry
  only 429 and 5xx, with backoff, a few times, then report.
- **No v1 SDK names.** They raise `AttributeError`: `create_batch` is `batches.create`, `get_batch`
  is `batches.retrieve`, `files.retrieve_content` is `files.content`, `evaluation.create` is
  `evals.create`, `file_id=` is `input_file_id=`.
- **Finish what you start.** Video, batch, evaluations, fine-tuning, queue jobs, and deployments
  are submit, poll to a terminal state, fetch. Do not end your turn while something you started is
  still provisioning, running, or being torn down: wait for the terminal state, or state exactly
  what is pending and the command that checks it.
- **Billable resources.** Dedicated endpoints, containers, and clusters bill while they run. Only a
  dedicated deployment can stop itself, and only if it was given an inactivity timeout; assume
  everything else keeps billing until stopped. Create them only when asked; delete what you
  created and confirm it is gone.
- **Report only what you observed.** Every claimed action, duration, count, or split must trace to
  a tool result or API response. Test the configuration you ship, not a test-only override.
