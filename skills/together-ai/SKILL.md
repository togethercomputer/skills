---
name: together-ai
description: "Together AI platform skill covering every product area: chat completions and streaming text generation, tool calling, structured outputs, reasoning models; image generation and editing with FLUX and Kontext; video generation; text-to-speech and speech-to-text; embeddings, reranking, and RAG retrieval; fine-tuning (LoRA, full, DPO, VLM, BYOM); batch inference; LLM-as-a-judge evaluations; code sandboxes; dedicated model inference (tg beta endpoints, deployments, autoscaling, traffic splits, custom model and LoRA uploads); dedicated containers (Sprocket, Jig, queue jobs); GPU clusters (H100, H200, B200, Kubernetes, Slurm); and Kueue quota queueing or Volcano gang scheduling on those clusters. Reach for it whenever the user builds, debugs, deploys, trains, evaluates, or operates anything on Together AI, or mentions the together SDK, the tg or together CLI, api.together.ai, TOGETHER_API_KEY, or a Together-hosted model id. The skill body routes each request to exactly one domain guide before answering."
---

# Together AI

One skill for the whole Together AI platform. This file is a router, not an answer.
Every real answer lives in exactly one domain guide under `domains/`.

## How to use this skill (read this first)

1. Find the user's task in **Routing** below. If two rows look close, read **Disambiguation**.
   If the user pasted an error, symbol, or ID, read **Symptom index** — it is more reliable
   than the prose rows.
2. Open **exactly one** domain guide with the Read tool before writing any code, command,
   or explanation. One guide, fully read, beats three skimmed.
3. Follow that guide. It will point you at `references/AREA/*.md` for depth and
   `scripts/AREA/*` for runnable starting points. Prefer editing a provided script over
   writing a request shape from memory.
4. Only open a second guide when the task genuinely spans two products (see
   **Cross-domain workflows**). Open them in the order given there, not in parallel.

Hard rule: **do not answer a Together AI product question out of this file alone.** This file
deliberately contains no API shapes, no model names, and no parameter lists. If you find
yourself recalling a Together API signature from memory, you skipped step 2.

**Path convention.** Every path in this skill — including paths written inside domain guides —
is relative to the skill root (the directory holding this file). Compose them from the skill
root, not from the directory of the file you are currently reading.

## Setup (applies to every domain)

- **Auth**: every product uses one key, `TOGETHER_API_KEY`, from
  https://api.together.ai/settings/api-keys. Read it from the environment. Never inline a key
  in a script, a command you print, or a file you write.
- **Python SDK**: `uv pip install --upgrade "together>=2.0.0"`, then `client = Together()`
  (picks up `TOGETHER_API_KEY` automatically). Every script in this skill is v2.
- **TypeScript SDK**: `npm install together-ai`, then `new Together()`.
- **CLI**: `uv tool install "together[cli]"` gives you `tg` (and the identical alias
  `together`). `tg` is the primary surface for dedicated model inference, GPU clusters, and
  cluster credentials.
- **Base URLs**: `https://api.together.xyz/v1` for the OpenAI-compatible SDK;
  dedicated-endpoint inference goes to `https://api-inference.together.ai/v1`; management APIs
  are at `https://api.together.ai`.
- **Kubernetes areas** (kueue, volcano) additionally need `kubectl` pointed at a Together
  cluster: `tg beta clusters get-credentials CLUSTER_ID --set-default-context`.

If the user has not set a key yet, say so once and continue; do not invent one or stub it.

## Routing

Open the one guide whose **Open when** matches. Signals are the strongest evidence.

| Open this guide | Open when the user wants to... | Signals |
|---|---|---|
| `domains/chat-completions.md` | generate or stream text, hold a multi-turn chat, call tools, force JSON, use reasoning models, debug a request | `chat.completions.create`, `stream=True`, `tools=`, `tool_choice`, `response_format`, `json_schema`, `finish_reason`, `reasoning_effort`, rate-limit or debug headers |
| `domains/images.md` | make or edit a still image, apply a LoRA style, guide with a reference image | `images.generate`, FLUX, FLUX.2, Kontext, "edit this image", LoRA style, `steps`, `seed`, image dimensions |
| `domains/video.md` | make a video from text or from an image, control keyframes, poll and download a clip | `videos.create`, Veo, Sora, Kling, Seedance, PixVerse, Vidu, first/last frame, "animate this image" |
| `domains/audio.md` | synthesize speech, stream or realtime TTS, transcribe, translate, diarize, timestamp | `audio.speech`, `audio.transcriptions`, `audio.translations`, WebSocket TTS, `BinaryAPIResponse`, diarization, word timestamps, live captions |
| `domains/embeddings.md` | embed text, do semantic search or RAG retrieval, rerank candidates | `embeddings.create`, `rerank`, cosine similarity, vector store, chunking, "retrieve then answer" |
| `domains/fine-tuning.md` | train or adapt a model on their own data | `fine_tuning.jobs.create`, LoRA training, full fine-tune, DPO, preference pairs, VLM tuning, BYOM upload, `training_file`, epochs, checkpoints |
| `domains/batch-inference.md` | run many independent requests offline for less money | `batches.create`, `input_file_id`, JSONL with `custom_id`, `purpose="batch-api"`, "backfill", "label 100k rows", 24-hour window |
| `domains/evaluations.md` | grade, score, classify, or A/B compare model outputs with a judge | `evals.create`, LLM-as-a-judge, classify/score/compare, judge model, eval dataset, `--download-results` |
| `domains/sandboxes.md` | execute Python remotely with session state, run agent-written code, make charts | `code_interpreter.execute`, `session_id`, sandbox, "run this code for me", remote notebook |
| `domains/dedicated-model-inference.md` | host a model on reserved GPUs, autoscale it, split traffic, A/B or shadow it, upload weights or LoRA adapters | `tg beta endpoints`, `client.beta.endpoints`, `ep_`/`dep_`/`cr_`/`ml_`/`abx_`/`exp_` IDs, traffic weight, scale to zero, `DEPLOYMENT_STATE_READY`, deployment profile, "dedicated endpoint" |
| `domains/dedicated-containers.md` | run their own Docker image as an inference worker with a job queue | Sprocket, Jig, `jig deploy`, `pyproject.toml` runtime config, queue submit/poll, custom pipeline in a container |
| `domains/gpu-clusters.md` | rent multi-node GPUs and own the orchestration | `tg beta clusters`, H100/H200/B200, Slurm, Slinky, shared volume, `get-credentials`, reserved vs on-demand, node health, 8-GPU minimum |
| `domains/kueue.md` | queue jobs against a GPU **quota** on their own k8s cluster | Kueue, `ClusterQueue`, `LocalQueue`, `ResourceFlavor`, `kueue.x-k8s.io`, job `suspend`, "share the pool across teams", "admit when quota frees" |
| `domains/volcano.md` | schedule a job's pods **all-or-nothing** on their own k8s cluster | Volcano, `vcjob`, `minAvailable`, gang scheduling, `volcano.sh`, `schedulerName: volcano`, "distributed training must start together" |

If nothing matches, ask one clarifying question naming two candidate guides. Do not guess and
do not answer generically.

## Disambiguation (the pairs that actually get confused)

| If the request is... | Open | Not | Because |
|---|---|---|---|
| a still image, even one to be animated later | `images.md` | `video.md` | animation starts in `video.md` only once a still already exists; "generate then animate" is images first, then video |
| motion, duration, fps, or a clip | `video.md` | `images.md` | video is async job + poll + download; images is a single call |
| "run this Python for me" | `sandboxes.md` | `gpu-clusters.md`, `dedicated-containers.md` | sandboxes = managed short-lived interpreter; clusters = you own nodes; containers = you own the image |
| "serve my own Docker image" | `dedicated-containers.md` | `dedicated-model-inference.md` | DMI serves *models* on Together's runtime; containers serve *your runtime* |
| "host this model on dedicated GPUs" | `dedicated-model-inference.md` | `gpu-clusters.md` | DMI is managed serving with autoscaling; clusters hand you raw nodes and no serving layer |
| "I need GPUs for training / kubectl / Slurm" | `gpu-clusters.md` | `dedicated-model-inference.md` | no model serving involved |
| many prompts, no user waiting | `batch-inference.md` | `chat-completions.md` | batch is JSONL + file upload + poll; chat is per-request |
| many prompts, a user waiting | `chat-completions.md` | `batch-inference.md` | use the async fan-out script in the chat guide |
| "is model A better than model B" | `evaluations.md` | `fine-tuning.md` | measuring, not changing, the model |
| "make the model better at X" | `fine-tuning.md` | `evaluations.md` | changing the model; come back to evals to prove it |
| jobs must wait for **quota** | `kueue.md` | `volcano.md` | Kueue gates admission by quota, leaves the default scheduler in place |
| pods must start **together** | `volcano.md` | `kueue.md` | Volcano replaces the scheduler to gang-schedule |
| "create the cluster first" | `gpu-clusters.md` | `kueue.md`, `volcano.md` | both k8s guides assume a Ready cluster and working `kubectl` |
| embeddings to answer a question | `embeddings.md` first | `chat-completions.md` | retrieval is the plumbing; generation is the hand-off |

## Symptom index (error, symbol, or ID pasted by the user)

| Evidence | Open |
|---|---|
| HTTP 403 `endpoints_v1_create_access_disabled`; `client.endpoints.create` fails; a stopped v1 endpoint will not restart | `domains/dedicated-model-inference.md` (v1 retirement) |
| `routing_error` or 503 against a deployment that shows READY | `domains/dedicated-model-inference.md` (traffic weights) |
| `project_id` required, or resource-name errors on `client.beta.*` | `domains/dedicated-model-inference.md` |
| unexpected GPU bill, "it kept running" | `domains/dedicated-model-inference.md` (no idle auto-stop) or `domains/dedicated-containers.md` |
| 409 "Out of stock" on provisioning | `domains/gpu-clusters.md` (try more regions) |
| "does not exist in the datacenter" on a volume | `domains/gpu-clusters.md` (inline `shared_volume`) |
| `cuda_version` / `nvidia_driver_version` rejected | `domains/gpu-clusters.md` |
| job stuck `suspend: true`, workload not admitted | `domains/kueue.md` |
| pods Pending forever, or partial pod placement on a multi-pod job | `domains/volcano.md` |
| `file_id` rejected, or batch results missing rows by `custom_id` | `domains/batch-inference.md` |
| `stream_to_file` does not exist; base64 `chunk.delta` audio | `domains/audio.md` |
| 80 MB / 1 GB / 4-hour audio limits | `domains/audio.md` |
| 514-token input truncation on embeddings | `domains/embeddings.md` |
| `plt.show()` produced no chart output | `domains/sandboxes.md` |
| `AttributeError` on `create_batch`, `get_batch`, `retrieve_content`, `evaluation.create` | v1 SDK — see **Universal rules**, then the matching guide |

## Universal rules (true in every domain)

- **v2 SDK only.** All Python here requires `together>=2.0.0`; upgrade before debugging
  anything else: `uv pip install --upgrade "together>=2.0.0"`. The v1 names below are gone.
  The `client.beta.*` surface used by dedicated model inference is beta and moves; keep the
  SDK current rather than pinning it old.

  | Operation | v2 (correct) | v1 (gone) |
  |---|---|---|
  | Create batch | `client.batches.create()` | `client.create_batch()` |
  | Get batch | `client.batches.retrieve()` | `client.get_batch()` |
  | Get endpoint | `client.endpoints.retrieve()` | `client.endpoints.get()` |
  | Run code | `client.code_interpreter.execute()` | `client.code_interpreter.run()` |
  | File content | `client.files.content()` | `client.files.retrieve_content()` |
  | Evaluations | `client.evals.create()` | `client.evaluation.create()` |
  | Batch input | `input_file_id=` | `file_id=` |
  | Autoscaling | `autoscaling={"min_replicas": N, "max_replicas": M}` | `min_replicas=N, max_replicas=M` |

- **Async job lifecycle.** Video, batch, evaluations, fine-tuning, container queue jobs, and
  dedicated deployments all follow: submit, get an ID back, poll until a **terminal** state,
  then fetch results. Never sleep a fixed interval and assume success, never treat the first
  non-error response as the result, and always check the failure state, not just the success
  one. Deployments are the slow case: first provisioning can take ~20 minutes.
- **Upload, then keep the file ID.** Batch, evaluations, and fine-tuning all start by
  uploading a file and returning an ID that every later call needs. Capture it in a variable,
  print it, and reuse it — re-uploading creates a second billable file and a second source of
  truth.
- **Reserved capacity bills until someone stops it.** Dedicated deployments, containers, and
  clusters have no automatic idle shutdown. Any workflow you write that creates one must also
  show how to scale it to zero or delete it.
- **Never create billable resources unasked.** If the user asked for a plan or a command,
  print the command and stop.
- **Download promptly.** Generated media and job result files are served from signed URLs
  that expire.

## Cross-domain workflows

Only these combinations warrant opening a second guide. Follow the order.

- **Train, host, prove**: `domains/fine-tuning.md` (train, get the output model) then
  `domains/dedicated-model-inference.md` (deploy it, get the endpoint string) then
  `domains/evaluations.md` (compare tuned vs base with a judge). Fine-tuning success is not
  serving success; serving success is not quality.
- **Retrieve, then answer**: `domains/embeddings.md` (embed corpus and query, retrieve,
  optionally rerank) then `domains/chat-completions.md` (generate the grounded answer). Embed
  the corpus via `domains/batch-inference.md` only when it is large enough to be worth the
  file round-trip.
- **Own the cluster, then schedule it**: `domains/gpu-clusters.md` (provision,
  `get-credentials`) then `domains/volcano.md` for gang scheduling **or** `domains/kueue.md`
  for quota queueing. They are alternatives; do not install both in one walkthrough.
- **Generate, then edit, then animate**: `domains/images.md` (FLUX generate, Kontext edit)
  then `domains/video.md` (image-to-video with the produced still).
- **Measure, change, measure**: `domains/evaluations.md` then `domains/fine-tuning.md` then
  `domains/evaluations.md`.
- **Prototype fast, then scale down cost**: `domains/chat-completions.md` to settle the prompt
  and model, then `domains/batch-inference.md` to run it over the full dataset.

## Official docs

Docs root: https://docs.together.ai. API reference: https://docs.together.ai/reference.
Each domain guide ends with the exact doc pages for its area — prefer those over the root.
