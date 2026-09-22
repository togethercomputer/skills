# Together AI: Embeddings & Reranking

Use Together AI embeddings for dense vector representations, semantic search, RAG retrieval, and reranking -- the plumbing that feeds a generation step, not the generation itself.

- create embeddings
- batch embeddings
- build retrieval or RAG pipelines
- rerank retrieved candidates

This guide is for retrieval plumbing, not for the final language-model response itself.

## Use this guide for

- Build vector search or semantic similarity features
- Add embedding generation to a data pipeline
- Improve retrieval quality with reranking
- Assemble a retrieval stage before calling a chat model

## Do not use this guide for

- the final answer-generation step -> `domains/chat-completions.md`
- very large offline embedding backfills -> `domains/batch-inference.md`
- when reranking requires a dedicated deployment -> `domains/dedicated-model-inference.md`

## Workflow

1. Confirm that the user needs vectors or retrieval, not direct generation.
2. Choose the embedding model and batch shape.
3. Generate embeddings for corpus and query paths consistently.
4. Retrieve candidates. An in-memory cosine-similarity store works for prototyping and small corpora (see `semantic_search.py`). Use a dedicated vector database for production scale.
5. Rerank only when the extra latency and endpoint requirement are justified. When no dedicated rerank endpoint is available, cosine-similarity ranking is a reasonable fallback.

## Open next

- **Embeddings API usage**
  - Read [references/embeddings/api-reference.md](references/embeddings/api-reference.md)
  - Start with [scripts/embeddings/embed_and_rerank.py](scripts/embeddings/embed_and_rerank.py) or [scripts/embeddings/embed_and_rerank.ts](scripts/embeddings/embed_and_rerank.ts)
- **Semantic search (embed, store, query)**
  - Start with [scripts/embeddings/semantic_search.py](scripts/embeddings/semantic_search.py) -- includes an in-memory vector store, cosine-similarity retrieval, and optional rerank
- **RAG pipeline composition**
  - Start with [scripts/embeddings/rag_pipeline.py](scripts/embeddings/rag_pipeline.py)
- **Model selection and rerank constraints**
  - Read [references/embeddings/models.md](references/embeddings/models.md)

## Rules

- Keep embeddings and reranking conceptually separate; rerank is a second-stage precision step.
- Reranking in this repo assumes a dedicated endpoint. Do not promise serverless rerank unless the product changes. When no endpoint is available, fall back to cosine-similarity ranking.
- The embedding model has a 514-token context limit. Chunk longer documents before embedding.
- The `rag_pipeline.py` example demonstrates retrieval plus generation; treat generation as a hand-off to chat completions.
- Preserve model consistency across indexing and querying.

## Docs

- [Embeddings Overview](https://docs.together.ai/docs/embeddings-overview)
- [Rerank Overview](https://docs.together.ai/docs/rerank-overview)
- [Embeddings API](https://docs.together.ai/reference/embeddings)
- [Rerank API](https://docs.together.ai/reference/rerank)
