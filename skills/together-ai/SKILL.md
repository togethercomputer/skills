---
name: together-ai
description: "Together AI platform skill covering every product area: chat completions and streaming text generation, tool calling, structured outputs, reasoning and vision models; image generation and editing with FLUX and Kontext; video generation; text-to-speech and speech-to-text; embeddings, reranking, and RAG retrieval; fine-tuning (LoRA, full, DPO, VLM, BYOM); batch inference; LLM-as-a-judge evaluations; code sandboxes; dedicated model inference (tg beta endpoints, deployments, autoscaling, traffic splits, custom model and LoRA uploads); dedicated containers (Sprocket, Jig, queue jobs); GPU clusters (H100, H200, B200, Kubernetes, Slurm); and Kueue quota queueing or Volcano gang scheduling on those clusters. Reach for it whenever the user builds, debugs, deploys, trains, evaluates, or operates anything on Together AI, or mentions the together SDK, the tg or together CLI, api.together.ai, TOGETHER_API_KEY, or a Together-hosted model id. The skill body routes each request to the matching domain guide."
---

# Together AI

Read the one guide below that matches the task. Each guide covers the common path by itself and
ends with an **Open next** menu saying what every reference and script contains, so you open a file
only when it holds a detail you need. Paths are relative to this skill's directory.

## Setup

- Auth: `TOGETHER_API_KEY` in the environment. Python: `uv pip install --upgrade "together>=2.0.0"`,
  then `client = Together()`. TypeScript: `npm install together-ai`, then `new Together()`.
- CLI: `uv tool install "together[cli]"` gives `tg` (alias `together`), used for dedicated
  inference, clusters, and model discovery.

## Guides

| Guide | Use for |
|---|---|
| `domains/chat-completions.md` | text generation, streaming, multi-turn chat, tool calling, JSON output, reasoning and vision models |
| `domains/images.md` | text-to-image, image editing (Kontext), LoRA styles, reference images |
| `domains/video.md` | text-to-video, image-to-video, keyframes |
| `domains/audio.md` | TTS (REST, streaming, WebSocket), transcription, translation, diarization, realtime STT |
| `domains/embeddings.md` | embeddings, semantic search, RAG retrieval, reranking |
| `domains/batch-inference.md` | large offline jobs at lower cost (JSONL, `batches.create`) |
| `domains/evaluations.md` | LLM-as-a-judge: classify, score, or compare outputs |
| `domains/fine-tuning.md` | LoRA, full, DPO, VLM, function-calling, and reasoning tuning; BYOM upload |
| `domains/sandboxes.md` | remote stateful Python execution, data analysis, charts |
| `domains/dedicated-model-inference.md` | dedicated endpoints (`tg beta endpoints`, `client.beta.endpoints`): deploy, autoscale, traffic split, A/B, shadow, metrics, model/LoRA upload, v1 migration (HTTP 403 `endpoints_v1_create_access_disabled`) |
| `domains/dedicated-containers.md` | your own Docker inference worker: Sprocket, Jig, queue jobs |
| `domains/gpu-clusters.md` | H100/H200/B200 clusters, Kubernetes or Slurm, shared storage, credentials |
| `domains/kueue.md` | quota-gated job queueing on a Together Kubernetes cluster |
| `domains/volcano.md` | all-or-nothing gang scheduling on a Together Kubernetes cluster |

Close calls: a still image is `images`, motion is `video`. Hosting a model is
`dedicated-model-inference`, hosting your own container image is `dedicated-containers`, raw nodes
are `gpu-clusters`. Jobs that wait for quota use `kueue`; pods that must start together use
`volcano`. A task spanning areas (chat + images + audio, or tune, deploy, evaluate) reads each
guide when it reaches that step.

## Rules for every area

- **Model IDs go stale.** IDs in guides and scripts are examples. On `Unable to access
  non-serverless model` or `model_not_available`, do not retry or try other IDs from memory; list
  what is live once and choose from it: `tg beta models public --product serverless --json`
  (Python: `client.beta.models.list_supported(product="PRODUCT_SERVERLESS")`). Each entry lists
  `capabilities` (chat, embedding, rerank, image, video) and `features` (tool calling, structured
  output, reasoning).
- **Do not retry errors that cannot succeed.** 400 non-serverless model, 401, 402
  `insufficient balance` (account-wide; another model will not help), 403, and 404 need a different
  input or a human. Retry only 429 and 5xx, with backoff, a few times, then report.
- **v2 SDK only.** v1 names raise `AttributeError`: `create_batch` is `batches.create`, `get_batch`
  is `batches.retrieve`, `files.retrieve_content` is `files.content`, `evaluation.create` is
  `evals.create`, `code_interpreter.run` is `code_interpreter.execute`, `file_id=` is
  `input_file_id=`.
- **Finish what you start.** Video, batch, evaluations, fine-tuning, queue jobs, and deployments
  are submit, poll to a terminal state, fetch. Do not end your turn while something you started is
  still provisioning, running, or being torn down: wait for the terminal state, or state exactly
  what is pending and the command that checks it.
- **Billable resources.** Dedicated endpoints, containers, and clusters bill until stopped and have
  no idle shutdown. Create them only when asked; delete what you created and confirm it is gone.
- **Report only what you observed.** Every claimed action, duration, count, or split must trace to
  a tool result or API response. Test the configuration you ship, not a test-only override.
