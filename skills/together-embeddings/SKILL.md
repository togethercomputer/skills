---
name: together-embeddings
description: Use this skill for Together AI embedding, retrieval, and reranking workflows: generating dense vectors, building semantic search or RAG pipelines, and using rerank models behind dedicated endpoints. Reach for it whenever the user needs vector representations or retrieval quality improvements rather than direct text generation.
---

# Together Embeddings & Reranking

## Overview

Use this skill for semantic retrieval components:

- create embeddings
- batch embeddings
- build retrieval or RAG pipelines
- rerank retrieved candidates

This skill is for retrieval plumbing, not for the final language-model response itself.

## When This Skill Wins

- Build vector search or semantic similarity features
- Add embedding generation to a data pipeline
- Improve retrieval quality with reranking
- Assemble a retrieval stage before calling a chat model

## Hand Off To Another Skill

- Use `together-chat-completions` for the final answer-generation step
- Use `together-batch-inference` for very large offline embedding backfills
- Use `together-dedicated-endpoints` when reranking requires a dedicated deployment

## Quick Routing

- **Embeddings API usage**
  - Read [references/api-reference.md](references/api-reference.md)
  - Start with [scripts/embed_and_rerank.py](scripts/embed_and_rerank.py) or [scripts/embed_and_rerank.ts](scripts/embed_and_rerank.ts)
- **RAG pipeline composition**
  - Start with [scripts/rag_pipeline.py](scripts/rag_pipeline.py)
- **Model selection and rerank constraints**
  - Read [references/models.md](references/models.md)

## Workflow

1. Confirm that the user needs vectors or retrieval, not direct generation.
2. Choose the embedding model and batch shape.
3. Generate embeddings for corpus and query paths consistently.
4. Retrieve candidates in the user's vector store.
5. Rerank only when the extra latency and endpoint requirement are justified.

## High-Signal Rules

- Keep embeddings and reranking conceptually separate; rerank is a second-stage precision step.
- Reranking in this repo assumes a dedicated endpoint. Do not promise serverless rerank unless the product changes.
- The `rag_pipeline.py` example demonstrates retrieval plus generation; treat generation as a hand-off to chat completions.
- Preserve model consistency across indexing and querying.

## Resource Map

- **API details**: [references/api-reference.md](references/api-reference.md)
- **Model guide**: [references/models.md](references/models.md)
- **Python embeddings example**: [scripts/embed_and_rerank.py](scripts/embed_and_rerank.py)
- **TypeScript embeddings example**: [scripts/embed_and_rerank.ts](scripts/embed_and_rerank.ts)
- **Python RAG pipeline**: [scripts/rag_pipeline.py](scripts/rag_pipeline.py)

## Official Docs

- [Embeddings Overview](https://docs.together.ai/docs/embeddings-overview)
- [Rerank Overview](https://docs.together.ai/docs/rerank-overview)
- [Embeddings API](https://docs.together.ai/reference/embeddings)
- [Rerank API](https://docs.together.ai/reference/rerank)
